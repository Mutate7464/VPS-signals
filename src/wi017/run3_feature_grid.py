"""WI-017 run 3: ALL existing fib-windowed feature families at the FULL grid
(17 windows, 3-233), USD, symbol-sequential + streaming redundancy.

Reuses feature_engine.py's own family implementations (no re-derivation):
  adx, di_spread, atr_pct, bb_pct_b, bb_width, obv_zscore, amihud, yangzhang,
  range_pos, range_width, donchian_break, fib_dist           (smooth, 17 win)
  kama_er, vwap_zscore                                      (fast, 17 win)
  hurst                                                     (13 win: w>=12 —
      _hurst_rs_vec needs window//4>=3 else all-NaN by construction)
  entropy                                                   (15 win: w>=8)

265 columns/symbol. NOTE: WI-016's shipped hurst_9 column is all-NaN by the same
constructor constraint (pre-existing wart, logged in the run-3 report).

Per symbol: compute -> write reports/wi017/features/<SYM>.parquet
-> accumulate streaming second moments (X.T @ X on complete rows only) for the
cross-symbol correlation matrix. Peak RAM: one symbol frame + 266x267 accumulators
(~3 MB float64). No all-ticker frame, no data copies.

Redundancy policy (admin amendment 2026-10-31): report high-|rho| clusters;
pruning decisions DEFERRED until usefulness is measured (run 4 alignment) —
cut only columns that are BOTH highly correlated AND less useful.

Outputs:
  reports/wi017/features/<SYM>.parquet
  reports/wi017/run3_redundancy.json / .md   (corr clusters + coverage stats)
"""
from __future__ import annotations

import glob
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _REPO_ROOT)
from src.wi017 import MARKET, WI017_WINDOWS  # noqa: E402
from src.feature_engine import (  # noqa: E402
    FIB_LEVELS,
    _adx,
    _amihud,
    _efficiency_ratio,
    _hurst_rs_vec,
    _shannon_entropy_vec,
    _vwap_zscore,
    _yang_zhang_vol,
    wilder_atr,
)

RAW_GLOB = "data/raw_ohlcv/market=USD/*.parquet"
QUARANTINE_CSV = "data/dead_letter_tickers.csv"
OUT_DIR = "reports/wi017/features"
SUMMARY_JSON = "reports/wi017/run3_redundancy.json"
SUMMARY_MD = "reports/wi017/run3_redundancy.md"
RHO_HIGH = 0.90  # cluster threshold; informational only (pruning deferred to run 4)

WINDOWS = list(WI017_WINDOWS)
MIN8 = [w for w in WINDOWS if w >= 8]
HURST_MIN = 12  # _hurst_rs_vec: lags = 2..window//4 needs >= 2 entries -> w >= 12
MIN_HURST = [w for w in WINDOWS if w >= HURST_MIN]

COLUMN_ORDER: list[str] = (
    [f"{fam}_{w}" for fam in ("adx", "di_spread", "atr_pct", "bb_pct_b", "bb_width",
                              "obv_zscore", "amihud", "yangzhang", "range_pos",
                              "range_width", "donchian_break", "fib_dist") for w in WINDOWS]
    + [f"kama_er_{w}" for w in WINDOWS]
    + [f"vwap_zscore_{w}" for w in WINDOWS]
    + [f"hurst_{w}" for w in MIN_HURST]
    + [f"entropy_{w}" for w in MIN8]
)


def features_for_symbol(df: pd.DataFrame) -> pd.DataFrame:
    close = df["close"].astype("float64")
    high = df["high"].astype("float64")
    low = df["low"].astype("float64")
    cols: dict[str, pd.Series] = {}

    for w in WINDOWS:
        adx, di = _adx(df, w)
        cols[f"adx_{w}"] = adx.astype("float32")
        cols[f"di_spread_{w}"] = di.astype("float32")
        cols[f"atr_pct_{w}"] = (wilder_atr(df, w) / (close + 1e-12)).astype("float32")
        sma = close.rolling(w, min_periods=w).mean()
        std = close.rolling(w, min_periods=w).std(ddof=1)
        upper, lower = sma + 2.0 * std, sma - 2.0 * std
        cols[f"bb_pct_b_{w}"] = ((close - lower) / (upper - lower + 1e-12)).astype("float32")
        cols[f"bb_width_{w}"] = ((upper - lower) / (sma + 1e-12)).astype("float32")

    obv = (np.sign(close.diff()).fillna(0.0) * df["volume"]).cumsum()
    obv_slope = obv.diff()
    for w in WINDOWS:
        m = obv_slope.rolling(w, min_periods=w).mean()
        s = obv_slope.rolling(w, min_periods=w).std(ddof=1)
        cols[f"obv_zscore_{w}"] = ((obv_slope - m) / (s + 1e-12)).astype("float32")
        cols[f"amihud_{w}"] = _amihud(df, w).astype("float32")
        cols[f"yangzhang_{w}"] = _yang_zhang_vol(df, w).astype("float32")
        # range structure
        hh = high.rolling(w, min_periods=w).max()
        ll = low.rolling(w, min_periods=w).min()
        rng = (hh - ll).astype("float64")
        cols[f"range_pos_{w}"] = ((close - ll) / (rng + 1e-12)).clip(0.0, 1.0).astype("float32")
        cols[f"range_width_{w}"] = (rng / (close + 1e-12)).astype("float32")
        cols[f"donchian_break_{w}"] = (close > hh.shift(1)).astype("float32")
        flat = rng < 1e-9
        dists = (((close - (ll + f * rng)) / (rng + 1e-12)).abs() for f in FIB_LEVELS)
        nearest = np.minimum.reduce([d.to_numpy() for d in dists])
        signed = np.sign((close - (ll + 0.5 * rng)).to_numpy()) * nearest
        cols[f"fib_dist_{w}"] = pd.Series(
            np.where(flat.to_numpy(), 0.0, signed), index=df.index
        ).astype("float32")
        # fast families
        cols[f"kama_er_{w}"] = _efficiency_ratio(close, w).astype("float32")
        cols[f"vwap_zscore_{w}"] = _vwap_zscore(df, w).astype("float32")

    close_arr = close.to_numpy("float64")
    for w in MIN_HURST:
        cols[f"hurst_{w}"] = _hurst_rs_vec(close_arr, w).astype("float32")
    for w in MIN8:
        cols[f"entropy_{w}"] = _shannon_entropy_vec(close_arr, w).astype("float32")

    return pd.DataFrame({"date": df["date"].values, **cols}, index=df.index)


def main() -> int:
    t0 = time.time()
    os.makedirs(OUT_DIR, exist_ok=True)
    try:
        quar = set(pd.read_csv(QUARANTINE_CSV)["symbol"].astype(str))
    except (OSError, KeyError):
        quar = set()
    files = sorted(glob.glob(RAW_GLOB))
    p = len(COLUMN_ORDER)
    s1 = np.zeros(p, "float64")     # column sums
    s2 = np.zeros((p, p), "float64")  # X.T @ X accumulator (complete rows only)
    n_rows_total = 0
    per_symbol_rows: list[tuple[str, int]] = []
    n_symbols = 0
    for f in files:
        sym = os.path.basename(f).replace("symbol=", "").replace(".parquet", "")
        if sym in quar:
            continue
        df = pq.read_table(f).to_pandas().sort_values("date").reset_index(drop=True)
        df = df[df["close"] > 0].reset_index(drop=True)
        if len(df) < 5:
            continue
        feats = features_for_symbol(df)
        pq.write_table(
            pa.Table.from_pandas(feats[["date", *COLUMN_ORDER]], preserve_index=False),
            os.path.join(OUT_DIR, f"{sym}.parquet"),
        )
        X = feats[COLUMN_ORDER].to_numpy("float64")
        good = ~np.isnan(X).any(axis=1)
        Xg = X[good]
        if len(Xg):
            s1 += Xg.sum(axis=0)
            s2 += Xg.T @ Xg
            n_rows_total += len(Xg)
        per_symbol_rows.append((sym, int(len(df))))
        n_symbols += 1
        if n_symbols % 50 == 0:
            print(f"  {n_symbols} symbols, {time.time() - t0:.0f}s", flush=True)
    # correlation from accumulated moments
    mu = s1 / n_rows_total
    cov = (s2 - n_rows_total * np.outer(mu, mu)) / (n_rows_total - 1)
    d = np.sqrt(np.diag(cov))
    with np.errstate(all="ignore"):
        corr = cov / np.outer(d, d)
    np.fill_diagonal(corr, 1.0)
    np.save(os.path.join(OUT_DIR, "_corr_matrix.npy"), corr)
    # high-|rho| clusters (informational; pruning deferred to run 4)
    pairs = []
    for i in range(p):
        for j in range(i + 1, p):
            r = corr[i, j]
            if abs(r) >= RHO_HIGH:
                pairs.append((COLUMN_ORDER[i], COLUMN_ORDER[j], round(float(r), 4)))
    pairs.sort(key=lambda t: -abs(t[2]))
    summary = {
        "market": MARKET,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "symbols": n_symbols,
        "columns": p,
        "complete_rows_used_for_corr": n_rows_total,
        "rho_threshold": RHO_HIGH,
        "n_high_rho_pairs": len(pairs),
        "high_rho_pairs_top40": pairs[:40],
        "pruning": "DEFERRED to run 4 (admin rule: cut only high-rho AND less-useful)",
    }
    with open(SUMMARY_JSON, "w") as fh:
        json.dump(summary, fh, indent=2)
    lines = [
        "# WI-017 run 3 — feature grid, ALL families x full fib windows 3–233 (USD)",
        "",
        f"Generated (UTC): {summary['generated_utc']} · symbols: {n_symbols} · columns: {p}"
        f" · complete rows for corr: {n_rows_total:,}",
        "",
        f"High-|rho| (>= {RHO_HIGH}) pairs: **{len(pairs)}** of {p * (p - 1) // 2:,} possible.",
        "Clusters below are informational. Pruning is DEFERRED to run 4: per admin rule,",
        "a column is cut only when BOTH highly correlated AND less useful (usefulness =",
        "target alignment, measurable only after the alignment matrix).",
        "",
        "| col A | col B | rho |",
        "|---|---|---|",
    ]
    for a, b, r in pairs[:40]:
        lines.append(f"| {a} | {b} | {r} |")
    with open(SUMMARY_MD, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"DONE symbols={n_symbols} cols={p} rows={n_rows_total} "
          f"high_rho_pairs={len(pairs)} elapsed={time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
