"""E5 factor baseline for WI-009, computed on CAD inside this module.

Why this exists
---------------
`scripts/diag_signal.py` is USD-locked (`only --market USD is implemented`), so
the mandatory E5 factor baseline for the CAD dataset cannot be produced by
routing through `--exp e5 --market CAD`. The five factors are therefore defined
here, byte-for-byte as the E5 report defines them, and evaluated with the *same*
score-based within-date rank-IC used to evaluate the contrastive model
(`src.models.pair_sampler.within_date_rank_ic`).

Factor definitions (dimensionless, trailing):
    mom_12_1          close.shift(21) / close.shift(252) - 1
    rev_1m            close / close.shift(21) - 1
    vol_20            20d std (ddof=1) of daily returns
    amihud_20         mean over 20d of |ret| / dollar_volume
    log_dollar_vol_20 mean over 20d of log(dollar_volume)
Target:
    fwd_atr_ret_h     (close.shift(-h) - close) / wilder_atr      (forward)

Note the E5 numbers quoted in the brief (mom_12_1 +5.54, vol_20 -4.72) are USD;
the CAD baseline must be recomputed and may differ. This module writes the CAD
numbers to `reports/wi009_e5_baseline_CAD.md`.

CLI:
    python -m src.factors.e5_baseline --market CAD
    python -m src.factors.e5_baseline --market CAD --horizon 15 --multivariate
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

from src.feature_engine import iter_market_symbols
from src.models.pair_sampler import within_date_rank_ic
from src.targets import wilder_atr

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS = BASE_DIR / "reports"

E5_FACTORS = ["mom_12_1", "rev_1m", "vol_20", "amihud_20", "log_dollar_vol_20"]
# E5 reads from 2015-01-01 so the 252-trading-day mom_12_1 lookback is warmed up
# by 2016-01-01; rows before warmup complete are dropped by the NaN filter below.
E5_WARMUP_MIN_DATE = "2015-01-01"


def build_e5_panel(market: str, min_date: str = E5_WARMUP_MIN_DATE) -> pd.DataFrame:
    """Build the E5 factor + forward-return panel for one market.

    Streams symbols one at a time (no all-ticker uncompressed frame) and keeps
    only the columns this module needs, cast to float32.

    Returns:
        DataFrame with columns [date, symbol, *E5_FACTORS, fwd_atr_ret_15,
        fwd_atr_ret_20], rows with NaN factors dropped.
    """
    parts: list[pd.DataFrame] = []
    for symbol, raw_df in iter_market_symbols(market, min_date=min_date, allow_fixture=False):
        g = raw_df.sort_values("date").reset_index(drop=True)
        if len(g) < 30:
            continue
        close = g["close"].astype("float64")
        ret = close.pct_change()
        dollar_vol = (close * g["volume"].astype("float64")) + 1e-12

        f = pd.DataFrame(
            {
                "date": g["date"],
                "symbol": symbol,
                "mom_12_1": (close.shift(21) / close.shift(252) - 1.0),
                "rev_1m": (close / close.shift(21) - 1.0),
                "vol_20": ret.rolling(20, min_periods=20).std(ddof=1),
                "amihud_20": (ret.abs() / dollar_vol).rolling(20, min_periods=20).mean(),
                "log_dollar_vol_20": np.log(dollar_vol).rolling(20, min_periods=20).mean(),
            }
        )

        close_a = close.to_numpy()
        atr = wilder_atr(g).astype("float64").to_numpy()
        for h in (15, 20):
            fwd = np.full(len(close_a), np.nan)
            if len(close_a) > h:
                fwd[:-h] = close_a[h:]
            f[f"fwd_atr_ret_{h}"] = (fwd - close_a) / (atr + 1e-12)

        for c in E5_FACTORS + ["fwd_atr_ret_15", "fwd_atr_ret_20"]:
            f[c] = f[c].astype("float32")
        parts.append(f)

    if not parts:
        return pd.DataFrame(columns=["date", "symbol"] + E5_FACTORS)

    panel = pd.concat(parts, ignore_index=True)
    panel = panel.dropna(subset=E5_FACTORS + ["fwd_atr_ret_15"])
    return panel.reset_index(drop=True)


def single_factor_ics(panel: pd.DataFrame, horizon: int = 15) -> dict[str, tuple[float, float, int]]:
    """Per-date Spearman rank-IC + t-stat for each of the five factors."""
    target = f"fwd_atr_ret_{horizon}"
    out: dict[str, tuple[float, float, int]] = {}
    for fac in E5_FACTORS:
        out[fac] = within_date_rank_ic(panel[fac].to_numpy(), panel[target].to_numpy(), panel["date"].to_numpy())
    return out


def date_positions(panel_dates) -> np.ndarray:
    """Position of each row's date within the sorted unique date array.

    This is the correct split key. `PurgedWalkForwardSplit` is fed the *sorted
    unique* dates, so the index sets it returns are positions into that array.
    `pd.factorize` codes are NOT positions — they are assigned by order of first
    appearance (i.e. symbol iteration order) — and masking on them pulls
    held-out rows into training on real data (verified: they disagree for 100%
    of CAD rows).
    """
    arr = np.asarray(panel_dates)
    uniq = np.sort(pd.unique(arr))
    return np.searchsorted(uniq, arr)


def multivariate_ic(panel: pd.DataFrame, horizon: int = 15) -> dict[str, tuple[float, float, int]]:
    """Purged walk-forward ridge + logit rank-IC on the five factors.

    The logit is scored with `predict_proba` (the WI-002 one-line fix): scoring
    it with `predict` returns class labels, which overstates the apparent
    magnitude of the effect.
    """
    from sklearn.linear_model import LogisticRegression, Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    from src.xgb_trainer import PurgedWalkForwardSplit

    target = f"fwd_atr_ret_{horizon}"
    x_all = panel[E5_FACTORS].to_numpy(dtype="float32")
    y_cont = panel[target].to_numpy(dtype="float64")
    med = panel.groupby("date")[target].transform("median")
    y_bin = (panel[target] > med).astype("int8").to_numpy()

    dates = panel["date"].to_numpy()
    # Positions, not factorize codes: see `date_positions`.
    uniq = np.sort(pd.unique(dates))
    pos = date_positions(dates)
    splits = list(PurgedWalkForwardSplit(n_splits=5, embargo_td=20).split(uniq))

    results: dict[str, tuple[float, float, int]] = {}
    for name, y, make_model, use_proba in (
        ("ridge", y_cont, lambda: make_pipeline(StandardScaler(), Ridge(alpha=100.0)), False),
        (
            "logit_median_split",
            y_bin,
            lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=500, C=0.1)),
            True,
        ),
    ):
        oof = np.full(len(panel), np.nan)
        for tr_idx, va_idx in splits:
            tr_rows = np.isin(pos, tr_idx)
            va_rows = np.isin(pos, va_idx)
            if not tr_rows.any() or not va_rows.any():
                continue
            m = make_model()
            m.fit(x_all[tr_rows], y[tr_rows])
            if use_proba:
                oof[va_rows] = m.predict_proba(x_all[va_rows])[:, 1]
            else:
                oof[va_rows] = m.predict(x_all[va_rows])
        mask = np.isfinite(oof) & np.isfinite(y_cont)
        results[name] = within_date_rank_ic(oof[mask], y_cont[mask], dates[mask])
    return results


def write_report(market: str, panel: pd.DataFrame, horizon: int, single: dict, multi: dict | None) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / f"wi009_e5_baseline_{market}.md"
    lines = [
        f"# WI-009 — E5 factor baseline ({market})",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Panel: {len(panel):,} rows · {panel['symbol'].nunique()} symbols · "
        f"{panel['date'].nunique()} dates ({panel['date'].min()} → {panel['date'].max()})",
        f"- Metric: score-based within-date Spearman rank-IC vs `fwd_atr_ret_{horizon}` "
        "(never class-label IC). Compiled on CAD inside `src/factors/e5_baseline.py`.",
        "",
        "## Single-factor within-date rank-IC",
        "",
        "| Factor | mean IC | t | dates |",
        "| :--- | ---: | ---: | ---: |",
    ]
    for fac, (ic, t, n) in single.items():
        lines.append(f"| `{fac}` | {ic:+.4f} | {t:+.2f} | {n} |")
    if multi:
        lines += ["", "## Multivariate (purged WF, 20d embargo)", "", "| Model | mean IC | t | dates |", "| :--- | ---: | ---: | ---: |"]
        for name, (ic, t, n) in multi.items():
            lines.append(f"| `{name}` | {ic:+.4f} | {t:+.2f} | {n} |")
        lines += ["", "Logit is scored with `predict_proba` (WI-002 one-line fix)."]
    out.write_text("\n".join(lines) + "\n")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--market", default="CAD")
    ap.add_argument("--horizon", type=int, default=15, choices=[15, 20])
    ap.add_argument("--multivariate", action="store_true", help="Also fit purged-WF ridge/logit.")
    args = ap.parse_args()

    panel = build_e5_panel(args.market)
    if panel.empty:
        print(f"[e5_baseline] {args.market}: no panel rows")
        return 1
    print(f"[e5_baseline] {args.market}: {len(panel):,} rows, {panel['date'].nunique()} dates")

    single = single_factor_ics(panel, args.horizon)
    multi = multivariate_ic(panel, args.horizon) if args.multivariate else None
    out = write_report(args.market, panel, args.horizon, single, multi)
    print(f"[e5_baseline] wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())