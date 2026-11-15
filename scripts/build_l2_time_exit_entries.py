#!/usr/bin/env python
"""PM-owned WI-068 full-run prep: fib-baseline entry artifacts with pre-registered horizon columns.

WI-068's `time_exit` fails closed on the swing-event caches (`/tmp/wi036` median gap 18d), so the
full CALIB run needs `--entries` parquets that already carry `r_h13` / `r_h55`. This builds them from
the frozen fib baseline (`hold_filter_gate.baseline_returns`: WI-028 at_bottom entry + WI-030
t15_s10_d39_close event exit, 25 bps inside) with the horizon returns taken from the daily OHLC bars
(`data/raw_ohlcv/market=<MKT>/symbol=*.parquet`, business-daily position i+h — the same semantics the
driver's own cache path enforces).

    uv run python scripts/build_l2_time_exit_entries.py

Output: `data/models/l2_time_exit/<MKT>_fib.parquet` (symbol, date, fold=0, r_event=r_frozen,
t_event=39, r_h13, r_h55; CALIB rows only — EVAL never written). No fold structure is invented: the
wi035 fold boundaries are not reconstructable on disk (prep_report coverage gap), so `fold` stays 0
and the driver's fold ceiling is structurally inapplicable on this baseline — recorded, not hidden.

Invariants: n_jobs=2, float32 immediately, symbol-sequential reads, no row >= CALIB_END written.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from src.l2_overlay import harness as H  # noqa: E402
from src.swing_bsh.hold_filter_gate import baseline_returns  # noqa: E402

MARKETS = ("USD", "CAD")
BASELINE_DIR = Path("/tmp/wi035")
OHLC_ROOT = BASE / "data" / "raw_ohlcv"
OUT_DIR = BASE / "data" / "models" / "l2_time_exit"
HORIZONS = (13, 55)          # WI-068 pre-registered, fixed ex ante
T_EVENT = 39                 # WI-030 frozen event exit horizon (t15_s10_d39_close)


def horizon_col(ohlc: pd.DataFrame, dates: pd.Series, h: int) -> np.ndarray:
    """Forward return at the h-th business-daily bar of that symbol (float32; NaN when unavailable)."""
    close = np.asarray(ohlc["close"], dtype="float64")
    pos = {d: i for i, d in enumerate(pd.to_datetime(ohlc["date"]).to_numpy())}
    out = np.full(len(dates), np.nan, dtype="float64")
    for r, dt in enumerate(pd.to_datetime(dates).to_numpy()):
        i = pos.get(dt)
        if i is not None and i + h < close.size:
            out[r] = close[i + h] / close[i] - 1.0
    return out.astype("float32")


def build_market(market: str) -> pd.DataFrame:
    base = baseline_returns(market, BASELINE_DIR)
    base["date"] = pd.to_datetime(base["date"])
    base = base[pd.to_datetime(base["date"]) < pd.Timestamp(H.CALIB_END)].reset_index(drop=True)
    root = OHLC_ROOT / f"market={market}"
    files = sorted(root.glob("symbol=*.parquet"))
    assert files, f"no daily OHLC files under {root}"
    by_sym = {s: g for s, g in base.groupby(base["symbol"].astype(str), sort=True)}
    r_h = {h: np.full(len(base), np.nan, dtype="float32") for h in HORIZONS}
    n_bars = n_miss = 0
    for f in files:
        sym = f.stem.replace("symbol=", "")
        rows = by_sym.get(sym)
        if rows is None:
            continue
        ohlc = pd.read_parquet(f, columns=["date", "close"])
        n_bars += len(ohlc)
        got = {h: horizon_col(ohlc, rows["date"], h) for h in HORIZONS}
        for h in HORIZONS:
            r_h[h][rows.index.to_numpy()] = got[h]
        n_miss += int(pd.isna(got[HORIZONS[0]]).sum())
    out = pd.DataFrame({
        "symbol": base["symbol"].astype(str).to_numpy(),
        "date": base["date"].to_numpy(),
        "fold": np.zeros(len(base), dtype="int64"),
        "r_event": base["r_frozen"].to_numpy("float32"),   # frozen WI-030 event exit, 25 bps inside
        "t_event": np.full(len(base), T_EVENT, dtype="int64"),
    })
    for h in HORIZONS:
        out[f"r_h{h}"] = r_h[h]
    keep = out.dropna(subset=["r_event"] + [f"r_h{h}" for h in HORIZONS]).reset_index(drop=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{market}_fib.parquet"
    keep.to_parquet(path, index=False)
    print(f"{market}: baseline rows {len(base):,}; OHLC {len(files)} symbols / {n_bars:,} bars; "
          f"h{HORIZONS[0]} unavailable on {n_miss:,} rows; complete rows {len(keep):,} -> {path}")
    return keep


def main() -> None:
    for m in MARKETS:
        build_market(m)
    print(f"outputs under {OUT_DIR} (CALIB only, rows >= {H.CALIB_END} never written)")


if __name__ == "__main__":
    main()
