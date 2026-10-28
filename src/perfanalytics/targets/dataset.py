"""Market run-target datasets (WI-015, plan step 2).

Builds `data/perfanalytics/run_targets_{market}/` — a Parquet dataset with one
`symbol=<TICKER>.parquet` file per symbol, written **one symbol at a time** from
the labeler in `labelers.py`. No all-ticker uncompressed frame is ever assembled:
each symbol's bars are labelled, filtered and flushed before the next symbol is
read (`tests/perfanalytics/test_target_dataset.py::test_streams_symbol_by_symbol`
locks this in).

Schema (also written to `data/perfanalytics/run_targets_{market}_schema.json`)

    date    datetime64    session date, t (naive; restored µs-precision on read)
    symbol  string          ticker as it appears in `data/raw_ohlcv/market=*/`
    t1_amp_{k}  float32     best qualifying close-to-close run return in [t+1,t+k]
    t2_vel_{k}  float32     t1 / max(peak-bottom sessions, 1), 1/day
    t3_streak_{k} float32   longest consecutive up-close streak in the window
    t4_freq_{k} float32     1.0 if a qualifying run exists, else 0.0
    diag_bottom_off_{k} float32  bottom session offset from t (1..k), NaN if none
    diag_peak_off_{k}   float32  peak session offset from t (1..k), NaN if none
    diag_lowhigh_{k}    float32  low-to-high return of the retained pair, NaN if none

for k in {15, 20}. Rows whose entire target set is NaN (leading ATR warm-up) are
dropped; NaN inside a retained row means "incomplete forward window" or
"undefined trailing ATR" exactly as documented in `labelers.py`.

CLI:
    python -m src.perfanalytics.targets.dataset                     # BOTH, CAD then USD
    python -m src.perfanalytics.targets.dataset --market CAD
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections.abc import Iterable, Iterator
from pathlib import Path

import pandas as pd

from src.perfanalytics.targets.labelers import (
    ATR_WINDOW,
    DEFAULT_HORIZONS,
    RUN_ATR_MULT,
    DIAG_STEMS,
    compute_run_targets,
    target_columns,
    target_value_columns,
)
from src.feature_engine import iter_market_symbols
from src.market_cli import MarketSelectionError, normalize_market
from src.perfanalytics.markets import BOTH_ORDER, resolve_markets

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data" / "perfanalytics"


def dataset_dir(market: str, base: Path | None = None) -> Path:
    """`data/perfanalytics/run_targets_<MARKET>/` (market-suffixed dataset)."""
    root = DATA_DIR if base is None else Path(base)
    return root / f"run_targets_{normalize_market(market)}"


def _default_symbol_iter(market: str, min_date: str | None) -> Iterator[tuple[str, pd.DataFrame]]:
    return iter_market_symbols(market, min_date=min_date, allow_fixture=False)


def build_run_targets(
    market: str,
    out_dir: Path | None = None,
    min_date: str | None = None,
    symbol_iter: Iterable[tuple[str, pd.DataFrame]] | None = None,
    horizons: tuple[int, ...] = DEFAULT_HORIZONS,
    atr_window: int = ATR_WINDOW,
    run_atr_mult: float = RUN_ATR_MULT,
) -> Path:
    """Write the run-target Parquet dataset for one market; return its directory.

    ``symbol_iter`` is the injection point used by tests; producing code passes
    the real market iterator. Files are written per symbol, so peak memory is one
    symbol's label frame regardless of universe size.
    """
    code = normalize_market(market)
    out = dataset_dir(code, out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for stale in out.glob("symbol=*.parquet"):
        stale.unlink()

    value_cols = target_value_columns(horizons)
    all_cols = ["date", "symbol"] + target_columns(horizons)
    src = symbol_iter if symbol_iter is not None else _default_symbol_iter(code, min_date)

    symbols = 0
    rows = 0
    date_min: pd.Timestamp | None = None
    date_max: pd.Timestamp | None = None
    for symbol, df in src:
        g = df.sort_values("date").reset_index(drop=True)
        labels = compute_run_targets(
            g, horizons=horizons, atr_window=atr_window, run_atr_mult=run_atr_mult
        )
        keep = labels[value_cols].notna().any(axis=1).to_numpy()
        if not keep.any():
            continue
        frame = labels.loc[keep].copy()
        frame.insert(0, "symbol", symbol)
        frame.insert(0, "date", pd.to_datetime(g.loc[keep, "date"]).to_numpy())
        frame = frame[all_cols]
        frame.to_parquet(out / f"symbol={symbol}.parquet", index=False)
        symbols += 1
        rows += len(frame)
        dmin, dmax = frame["date"].min(), frame["date"].max()
        date_min = dmin if date_min is None else min(date_min, dmin)
        date_max = dmax if date_max is None else max(date_max, dmax)

    _write_schema(code, out, horizons, symbols, rows, date_min, date_max, atr_window, run_atr_mult)
    return out


def _relative_to_base(path: Path) -> str:
    """Repo-relative path when inside the repo, else the absolute path (tests/overrides)."""
    try:
        return str(path.relative_to(BASE_DIR))
    except ValueError:
        return str(path)


def _write_schema(
    market: str,
    out: Path,
    horizons: tuple[int, ...],
    symbols: int,
    rows: int,
    date_min: pd.Timestamp | None,
    date_max: pd.Timestamp | None,
    atr_window: int,
    run_atr_mult: float,
) -> Path:
    """Sibling schema/coverage record for the dataset (not inside the dataset dir)."""
    hs = sorted(horizons)
    fields: dict[str, str] = {
        "date": "datetime64 session date t (naive)",
        "symbol": "string ticker",
    }
    for k in hs:
        for stem, doc in (
            ("t1_amp", "best qualifying close-to-close run return over [t+1,t+k]"),
            ("t2_vel", "t1 / max(peak-bottom sessions, 1) (1/day)"),
            ("t3_streak", "longest consecutive up-close streak inside the window"),
            ("t4_freq", "1.0 if a qualifying run exists, else 0.0"),
            (DIAG_STEMS[0], "bottom session offset from t (1..k); NaN if no run"),
            (DIAG_STEMS[1], "peak session offset from t (1..k); NaN if no run"),
            (DIAG_STEMS[2], "low-to-high return of the retained pair; NaN if no run"),
        ):
            fields[f"{stem}_{k}"] = "float32: " + doc
    schema = {
        "market": market,
        "dataset": _relative_to_base(out),
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "horizons": hs,
        "atr_window": atr_window,
        "run_atr_mult": run_atr_mult,
        "rows": rows,
        "symbols": symbols,
        "date_min": None if date_min is None else str(date_min.date()),
        "date_max": None if date_max is None else str(date_max.date()),
        "columns": fields,
    }
    path = out.parent / f"{out.name}_schema.json"
    path.write_text(json.dumps(schema, indent=2) + "\n")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--market", default=None, metavar="CAD|USD", help="Omit for both (CAD then USD).")
    ap.add_argument("--min-date", default=None, help="Drop bars before this date (YYYY-MM-DD).")
    ap.add_argument("--out-dir", default=None, help="Override the dataset root (default data/perfanalytics).")
    args = ap.parse_args(argv)

    try:
        markets = resolve_markets(args.market)
    except MarketSelectionError as exc:
        print(f"[perfanalytics.targets] {exc}", file=sys.stderr)
        return 2

    base = Path(args.out_dir) if args.out_dir else None
    for market in markets:
        out = build_run_targets(market, out_dir=base, min_date=args.min_date)
        print(f"[perfanalytics.targets] {market}: wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
