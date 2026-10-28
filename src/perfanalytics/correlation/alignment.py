"""Per-target held-out alignment matrix (WI-015, plan step 4).

For every run target T1–T4 at horizons k ∈ {15, 20}, score each enriched
family×window feature against the target and report the ones that clear the
WI-009b-style bar.

Method (plan CONSTRAINTS — all frozen)
-------------------------------------
* Splits: five chronological held-out folds with a 20-session embargo, using the
  E5 machinery shape (`src.xgb_trainer.PurgedWalkForwardSplit`, n_splits=5,
  embargo_td=20). Only held-out (validation-block) rows are ever scored — an
  in-sample number can never reach the report.
* Score: per-date **cross-sectional Spearman rank IC** (Pearson of within-date
  ranks, ≥3 names per date, zero-dispersion dates dropped), then the mean over
  the held-out dates. The same rank-IC estimator as
  `src.models.pair_sampler.within_date_rank_ic`.
* Baseline: the five E5 factors (`src.factors.e5_baseline.factor_frame`) against
  the same target/horizon, through the same folds. The **best** E5 factor by
  |held-out IC| supplies the sign reference.
* Noise margin: per candidate, resample its daily IC series in circular
  contiguous blocks of 20 dates, with replacement, to the original length, 1000
  times, seed 42 (deterministic); margin = 95th percentile of |bootstrap mean −
  observed mean|.
* Pass: candidate sign == baseline sign **and** |observed IC| > margin.

Bounded memory: the market's unique dates are collected once (dates only), then
each fold is assembled symbol-by-symbol and freed before the next fold. No
all-ticker uncompressed feature frame is ever held.

Reports (`reports/perfanalytics/`, market-suffixed):
    alignment_{market}.csv   full candidate matrix (one row per target×horizon×feature)
    alignment_{market}.json  run metadata + the fold date blocks
    alignment_{market}.md    best family×window per target×horizon (+ addendum summary)

CLI:
    python -m src.perfanalytics.correlation.alignment             # BOTH, CAD then USD
    python -m src.perfanalytics.correlation.alignment --market CAD
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

import numpy as np
import pandas as pd

from src.factors.e5_baseline import E5_FACTORS, factor_frame
from src.feature_engine import iter_market_symbols
from src.market_cli import MarketSelectionError, normalize_market
from src.perfanalytics.features.panel import family_of, feature_columns, window_of
from src.perfanalytics.markets import BOTH_ORDER, resolve_markets
from src.perfanalytics.targets.labelers import DEFAULT_HORIZONS, TARGET_STEMS
from src.xgb_trainer import PurgedWalkForwardSplit

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data" / "perfanalytics"
REPORTS = BASE_DIR / "reports" / "perfanalytics"

N_SPLITS = 5
EMBARGO_TD = 20
BLOCK_DATES = 20
N_BOOTSTRAP = 1000
BOOTSTRAP_SEED = 42
MIN_NAMES_PER_DATE = 3

E5_PREFIX = "e5_"
E5_COLS = [f"{E5_PREFIX}{f}" for f in E5_FACTORS]


def target_columns(horizons: tuple[int, ...] = DEFAULT_HORIZONS) -> list[str]:
    """The scored target columns, target-major (T1..T4 × k)."""
    return [f"{stem}_{k}" for k in horizons for stem in TARGET_STEMS]


def target_label(column: str) -> str:
    """`t1_amp_15` -> `T1` (the horizon stays its own column/field)."""
    return column.split("_")[0].upper()


# --------------------------------------------------------------------------- #
# Fold construction
# --------------------------------------------------------------------------- #
def fold_val_positions(
    unique_dates: np.ndarray, n_splits: int = N_SPLITS, embargo_td: int = EMBARGO_TD
) -> list[np.ndarray]:
    """Positions of each held-out (validation-block) date within `unique_dates`.

    Uses the E5 shape (`PurgedWalkForwardSplit`), but returns the validation
    *date positions* — this analysis scores held-out rows only and trains
    nothing, so the purged training index is not needed.
    """
    splitter = PurgedWalkForwardSplit(n_splits=n_splits, embargo_td=embargo_td)
    folds: list[np.ndarray] = []
    for _train_idx, val_idx in splitter.split(np.asarray(unique_dates)):
        folds.append(np.unique(val_idx))
    return folds


# --------------------------------------------------------------------------- #
# Rank IC
# --------------------------------------------------------------------------- #
def _per_date_sums(mat: np.ndarray, starts: np.ndarray) -> np.ndarray:
    """Sum each contiguous date block of a date-sorted matrix (rows per date)."""
    return np.add.reduceat(mat, starts, axis=0)


def daily_spearman_ic(
    frame: pd.DataFrame,
    target_cols: list[str],
    feat_cols: list[str],
) -> dict[str, np.ndarray]:
    """Per-date cross-sectional Spearman IC for every (target, feature) pair.

    Pairwise-complete: each (target, feature) cell is scored on the names whose
    ranks are defined for **both** that date — a NaN in one long-window feature
    cannot silently delete that date for the other candidates (which would make
    the window comparison unfair, since it would strip dates unevenly). A date
    needs >=3 such names and non-zero rank dispersion in both series, the same
    guard as `within_date_rank_ic`.

    Returns `{target_col: ic_matrix}` with shape `(n_dates_in_fold, n_features)`,
    NaN where a date/candidate pair was undefined.
    """
    codes, uniq = pd.factorize(frame["date"].to_numpy(), sort=True)
    n_dates = len(uniq)
    rt = frame.groupby("date", sort=True)[target_cols].rank().to_numpy("float64")
    rf = frame.groupby("date", sort=True)[feat_cols].rank().to_numpy("float64")
    mt, mf = np.isfinite(rt), np.isfinite(rf)
    rt = np.where(mt, rt, 0.0)
    rf = np.where(mf, rf, 0.0)

    order = np.argsort(codes, kind="stable")
    codes_s = codes[order]
    starts = np.flatnonzero(np.r_[True, codes_s[1:] != codes_s[:-1]])
    rt_s, rf_s, mt_s, mf_s = rt[order], rf[order], mt[order], mf[order]

    out: dict[str, np.ndarray] = {}
    for i, t_col in enumerate(target_cols):
        ti = rt_s[:, i]
        ti2 = ti * ti
        both = (mf_s & mt_s[:, [i]]).astype("float64")
        cnt = _per_date_sums(both, starts)
        sx = _per_date_sums(rf_s * both, starts)
        sxx = _per_date_sums(rf_s * rf_s * both, starts)
        sy = _per_date_sums(ti[:, None] * both, starts)
        syy = _per_date_sums(ti2[:, None] * both, starts)
        sxy = _per_date_sums(rf_s * ti[:, None] * both, starts)
        with np.errstate(divide="ignore", invalid="ignore"):
            mx = sx / cnt
            my = sy / cnt
            vx = sxx / cnt - mx * mx
            vy = syy / cnt - my * my
            cov = sxy / cnt - mx * my
            corr = cov / np.sqrt(vx * vy)
        ok = (cnt >= MIN_NAMES_PER_DATE) & (vx > 0.0) & (vy > 0.0)
        out[t_col] = np.where(ok, corr, np.nan)
    return out


def block_bootstrap_margin(
    ic: np.ndarray,
    block: int = BLOCK_DATES,
    n_draws: int = N_BOOTSTRAP,
    seed: int = BOOTSTRAP_SEED,
) -> float:
    """95th percentile of |bootstrap mean − observed mean| (circular blocks)."""
    ic = np.asarray(ic, dtype="float64")
    ic = ic[np.isfinite(ic)]
    d = len(ic)
    if d < 2:
        return float("nan")
    observed = float(ic.mean())
    n_blocks = int(np.ceil(d / block))
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, d, size=(n_draws, n_blocks))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]) % d
    idx = idx.reshape(n_draws, -1)[:, :d]
    means = ic[idx].mean(axis=1)
    return float(np.percentile(np.abs(means - observed), 95.0))


# --------------------------------------------------------------------------- #
# Fold assembly (bounded memory)
# --------------------------------------------------------------------------- #
def _symbol_dates(target_dir: Path) -> list[tuple[str, np.ndarray]]:
    """(symbol, date array) for every file in the target dataset (dates only)."""
    out: list[tuple[str, np.ndarray]] = []
    for path in sorted(target_dir.glob("symbol=*.parquet")):
        symbol = path.stem.split("=", 1)[-1]
        dates = pd.read_parquet(path, columns=["date"])["date"]
        out.append((symbol, _ns(dates)))
    return out


def _ns(values) -> np.ndarray:
    """Parquet restores datetimes at µs resolution; force ns so merges/searchsorted align."""
    return pd.to_datetime(values).to_numpy().astype("datetime64[ns]")


def _fold_frame(
    symbol: str,
    val_pos: np.ndarray,
    raw: pd.DataFrame,
    target_dir: Path,
    feature_dir: Path,
    all_dates: np.ndarray,
) -> pd.DataFrame | None:
    """The held-out rows of one symbol: targets + fib features + E5 factors."""
    tgt = pd.read_parquet(target_dir / f"symbol={symbol}.parquet")
    feat = pd.read_parquet(feature_dir / f"symbol={symbol}.parquet")
    tgt["date"] = _ns(tgt["date"])
    feat["date"] = _ns(feat["date"])
    g = raw.sort_values("date").reset_index(drop=True)
    g["date"] = _ns(g["date"])

    factors = factor_frame(g)
    factors.insert(0, "date", g["date"].to_numpy())
    factors.columns = ["date"] + E5_COLS

    merged = tgt.merge(feat, on=["date", "symbol"], how="inner").merge(factors, on="date", how="inner")
    if merged.empty:
        return None
    pos = np.searchsorted(all_dates, merged["date"].to_numpy())
    keep = np.isin(pos, val_pos)
    return merged.loc[keep].reset_index(drop=True) if keep.any() else None


def run_alignment(
    market: str,
    data_root: Path | None = None,
    reports_dir: Path | None = None,
    symbol_factory: Callable[[], Iterable[tuple[str, pd.DataFrame]]] | None = None,
    horizons: tuple[int, ...] = DEFAULT_HORIZONS,
    feats: list[str] | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Compute the held-out alignment matrix; return (table, metadata).

    `symbol_factory` returns a *fresh* iterator over `(symbol, raw OHLCV)` — one
    call per fold, because the cross-sectional IC needs every symbol's held-out
    rows for that fold. Default reads the real market from `data/raw_ohlcv/`.
    """
    code = normalize_market(market)
    root = DATA_DIR if data_root is None else Path(data_root)
    target_dir = root / f"run_targets_{code}"
    feature_dir = root / f"features_{code}"
    if not target_dir.exists() or not feature_dir.exists():
        raise FileNotFoundError(f"missing target/feature dataset for {code} under {root}")

    t_cols = target_columns(horizons)
    f_cols = list(feats) if feats is not None else feature_columns()
    candidates = list(f_cols)

    sym_dates = _symbol_dates(target_dir)
    all_dates = np.unique(np.concatenate([d for _, d in sym_dates]))
    date_pos = {s: np.searchsorted(all_dates, d) for s, d in sym_dates}
    folds = fold_val_positions(all_dates)

    series: dict[str, dict[str, list[np.ndarray]]] = {
        t: {f: [] for f in candidates + E5_COLS} for t in t_cols
    }
    factory: Callable[[], Iterable[tuple[str, pd.DataFrame]]]
    factory = symbol_factory if symbol_factory is not None else (lambda: iter_market_symbols(code, allow_fixture=False))

    for val_pos in folds:
        parts: list[pd.DataFrame] = []
        for symbol, raw_df in factory():
            dpos = date_pos.get(symbol)
            if dpos is None or not np.isin(dpos, val_pos).any():
                continue
            fold = _fold_frame(symbol, val_pos, raw_df, target_dir, feature_dir, all_dates)
            if fold is not None:
                parts.append(fold)
            del raw_df
        if not parts:
            continue
        # One fold's held-out cross-section, then freed before the next fold —
        # never the whole market's feature frame at once.
        fold_all = pd.concat(parts, ignore_index=True)
        del parts
        ics = daily_spearman_ic(fold_all, t_cols, candidates + E5_COLS)
        for t_col, mat in ics.items():
            for j, f_col in enumerate(candidates + E5_COLS):
                col = mat[:, j]
                good = np.isfinite(col)
                if good.any():
                    series[t_col][f_col].append(col[good])
        del fold_all, ics

    rows: list[dict] = []
    for t_col in t_cols:
        base_series = {f: np.concatenate(series[t_col][f]) for f in E5_COLS if series[t_col][f]}
        base_best = max(base_series, key=lambda f: abs(base_series[f].mean())) if base_series else None
        base_ic = float(base_series[base_best].mean()) if base_best else float("nan")
        for f_col in candidates:
            parts = series[t_col][f_col]
            ic = np.concatenate(parts) if parts else np.array([])
            observed = float(ic.mean()) if ic.size else float("nan")
            margin = block_bootstrap_margin(ic) if ic.size else float("nan")
            sign_match = bool(
                np.isfinite(observed) and np.isfinite(base_ic) and np.sign(observed) == np.sign(base_ic)
            )
            passed = bool(sign_match and np.isfinite(margin) and abs(observed) > margin)
            rows.append(
                {
                    "target": target_label(t_col),
                    "horizon": int(t_col.rsplit("_", 1)[-1]),
                    "family": family_of(f_col),
                    "window": window_of(f_col),
                    "column": f_col,
                    "held_out_ic": observed,
                    "n_dates": int(ic.size),
                    "noise_margin": margin,
                    "baseline_factor": base_best,
                    "baseline_ic": base_ic,
                    "sign_match": sign_match,
                    "pass": passed,
                }
            )

    table = pd.DataFrame(rows)
    meta = {
        "market": code,
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_splits": N_SPLITS,
        "embargo_td": EMBARGO_TD,
        "block_dates": BLOCK_DATES,
        "n_bootstrap": N_BOOTSTRAP,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "min_names_per_date": MIN_NAMES_PER_DATE,
        "targets": t_cols,
        "n_candidates": len(candidates),
        "fold_date_blocks": [
            [str(pd.Timestamp(all_dates[v[0]]).date()), str(pd.Timestamp(all_dates[v[-1]]).date())]
            for v in folds
            if len(v)
        ],
    }
    write_reports(table, meta, reports_dir)
    return table, meta


# --------------------------------------------------------------------------- #
# Reports
# --------------------------------------------------------------------------- #
def _best_per_target(table: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (target, horizon), g in table.groupby(["target", "horizon"], sort=True):
        g = g[np.isfinite(g["held_out_ic"])]
        if g.empty:
            rows.append(
                {"target": target, "horizon": horizon, "family": None, "window": None,
                 "held_out_ic": float("nan"), "noise_margin": float("nan"),
                 "baseline_factor": None, "baseline_ic": float("nan"),
                 "sign_match": False, "pass": False, "n_dates": 0}
            )
            continue
        best = g.loc[g["held_out_ic"].abs().idxmax()]
        rows.append(best.to_dict())
    return pd.DataFrame(rows)


def write_reports(
    table: pd.DataFrame, meta: dict, reports_dir: Path | None = None
) -> dict[str, Path]:
    """Write the market's alignment CSV + JSON + Markdown; return the paths."""
    root = REPORTS if reports_dir is None else Path(reports_dir)
    root.mkdir(parents=True, exist_ok=True)
    market = meta["market"]

    csv_path = root / f"alignment_{market}.csv"
    table.to_csv(csv_path, index=False)

    json_path = root / f"alignment_{market}.json"
    json_path.write_text(json.dumps(meta, indent=2) + "\n")

    best = _best_per_target(table)
    lines = [
        f"# WI-015 — per-target alignment matrix ({market})",
        "",
        f"- Generated (UTC): {meta['generated_utc']}",
        f"- Method: {meta['n_splits']} chronological held-out folds, {meta['embargo_td']}-session embargo; "
        "per-date cross-sectional Spearman IC, mean over held-out dates only.",
        f"- Skill bar: sign must match the best E5 factor for that target/horizon **and** "
        f"|IC| must exceed a {meta['n_bootstrap']}-draw circular block-bootstrap noise margin "
        f"({meta['block_dates']}-date blocks, seed {meta['bootstrap_seed']}).",
        f"- Held-out date blocks: {', '.join(f'{a}→{b}' for a, b in meta['fold_date_blocks'])}",
        f"- Candidates: {meta['n_candidates']} family×window features; E5 five-factor baseline scored the same way.",
        "",
        "## Best family×window per target × horizon",
        "",
        "| Target | Best family | Window | Held-out IC | Noise margin | Baseline factor | Baseline sign | Pass |",
        "| :--- | :--- | ---: | ---: | ---: | :--- | ---: | :--- |",
    ]
    for _, r in best.iterrows():
        family = r["family"] if r["family"] is not None else "—"
        window = f"{int(r['window'])}" if pd.notna(r["window"]) else "—"
        base = r["baseline_factor"] if r["baseline_factor"] is not None else "—"
        lines.append(
            f"| {r['target']}@{int(r['horizon'])} | `{family}` | {window} | {r['held_out_ic']:+.4f} | "
            f"{r['noise_margin']:.4f} | `{base}` | {'+' if r['baseline_ic'] >= 0 else '−'} | "
            f"{'PASS' if r['pass'] else 'fail'} |"
        )
    n_pass = int(table["pass"].sum())
    lines += [
        "",
        f"**Verdict:** {n_pass} of {len(table)} candidate rows clear the same-sign + noise-margin bar "
        f"({best['pass'].sum()} of {len(best)} best-per-target cells). "
        "Prior expectation (WI-009 series): most cells land at noise; a null result is the honest product.",
        "",
        f"Full matrix: `alignment_{market}.csv` · metadata: `alignment_{market}.json`",
    ]
    md_path = root / f"alignment_{market}.md"
    md_path.write_text("\n".join(lines) + "\n")
    return {"csv": csv_path, "json": json_path, "md": md_path}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--market", default=None, metavar="CAD|USD", help="Omit for both (CAD then USD).")
    ap.add_argument("--data-root", default=None, help="Override the dataset root (default data/perfanalytics).")
    ap.add_argument("--reports-dir", default=None, help="Override the report root (default reports/perfanalytics).")
    args = ap.parse_args(argv)

    try:
        markets = resolve_markets(args.market)
    except MarketSelectionError as exc:
        print(f"[perfanalytics.correlation] {exc}", file=sys.stderr)
        return 2

    root = Path(args.data_root) if args.data_root else None
    reports = Path(args.reports_dir) if args.reports_dir else None
    for market in markets:
        table, meta = run_alignment(market, data_root=root, reports_dir=reports)
        passed = int(table["pass"].sum())
        print(
            f"[perfanalytics.correlation] {market}: {len(table)} candidate rows, "
            f"{passed} pass → {reports or REPORTS}/alignment_{market}.csv"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
