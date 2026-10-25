"""Rebuild data/features/targets_{USD,CAD}.parquet with the current TARGET_COLUMNS.

Targets-only rebuild (no feature recompute — Hurst/entropy are the expensive
stage and are untouched). Mirrors `src.feature_engine.main --min-date 2016-01-01`:
`iter_market_symbols` streaming (reads from min_date - 250d warmup, skips
quarantined / < 125-row symbols), per-symbol `compute_targets`, trim rows to
>= min_date, dropna(subset=TARGET_COLUMNS), int8 cast, parquet write.

Guards: writes a stage file, asserts every legacy label column is identical
row-for-row against the existing parquet, then swaps in. Run:
uv run python scripts/rebuild_targets.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.feature_engine import iter_market_symbols  # noqa: E402
from src.targets import TARGET_COLUMNS, compute_targets  # noqa: E402

FEATURES_DIR = ROOT / "data" / "features"
MIN_DATE = "2016-01-01"  # panel default (WI-002 E2 full-universe rerun)


def rebuild(market: str) -> pd.DataFrame:
    min_ts = pd.Timestamp(MIN_DATE)
    parts: list[pd.DataFrame] = []
    for symbol, raw_df in iter_market_symbols(market, min_date=MIN_DATE, allow_fixture=False):
        g = raw_df.reset_index(drop=True)
        t = compute_targets(g)
        t["date"] = g["date"]
        t["symbol"] = symbol
        t["market"] = market
        t = t[t["date"] >= min_ts]
        t = t.dropna(subset=TARGET_COLUMNS)
        if len(t):
            parts.append(t[["date", "symbol", "market"] + TARGET_COLUMNS])
    merged = pd.concat(parts, ignore_index=True)
    for c in TARGET_COLUMNS:
        merged[c] = merged[c].astype("int8")
    return merged


def main() -> int:
    def _d(x):
        return getattr(x, "date", lambda: x)()

    for market in ("USD", "CAD"):
        new = rebuild(market)
        out = FEATURES_DIR / f"targets_{market}.parquet"
        old = pd.read_parquet(out)
        print(
            f"[rebuild_targets] {market}: old {len(old):,} rows "
            f"({_d(old['date'].min())} → {_d(old['date'].max())}), "
            f"new {len(new):,} rows ({_d(new['date'].min())} → {_d(new['date'].max())}), "
            f"cols old={list(old.columns)} new={list(new.columns)}"
        )
        assert len(old) == len(new), f"{market}: row count changed {len(old):,} → {len(new):,}"
        stage = out.with_suffix(".stage.parquet")
        new.to_parquet(stage, index=False)
        for c in ("y_15d_high", "y_15d_low", "y_20d_up", "y_20d_down"):
            assert (old[c].to_numpy() == new[c].to_numpy()).all(), f"{market}:{c} changed!"
        stage.rename(out)
        print(f"[rebuild_targets] {market}: wrote {out} (+y_20d_stay), legacy labels verified identical")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())