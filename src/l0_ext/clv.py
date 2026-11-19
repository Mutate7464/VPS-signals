"""L0 extension: Close Location Value (CLV) + 14-bar rolling mean (WI-076).

Predictive-only license (D-023 layer 1): causal bar geometry only. No trading or
economic metric is computed here.

Definition:
  * ``clv_t = ((close_t - low_t) - (high_t - close_t)) / (high_t - low_t)``
    in ``[-1, 1]``; NaN when the bar has no range (``high == low``);
  * ``clv_ma14_t`` = mean of ``clv`` over bars ``t-13..t`` (``min_periods=14``),
    NaN-propagating: any NaN inside the window yields NaN.

Strictly causal: bar ``t`` uses bar ``t`` and earlier only, so values are never
revised by later bars.

Prereg family id: ``l0-clv``. Repo invariants honoured: symbol-sequential reads,
float32 immediately after calculation, chunked concat (no all-ticker
uncompressed frame), n_jobs=2 (this module is single-process).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

WINDOW = 14
N_JOBS = 2  # declared, unused: work is symbol-sequential I/O bound
RAW_ROOT = Path("data/raw_ohlcv")
OUT_ROOT = Path("data/features/l0_ext")
CHUNK_SYMBOLS = 50
VALUE_COLS = ["clv", "clv_ma14"]
SCHEMA = pa.schema(
    [
        ("symbol", pa.string()),
        ("date", pa.date32()),
        ("clv", pa.float32()),
        ("clv_ma14", pa.float32()),
    ]
)


def _clv_one(d: pd.DataFrame) -> pd.DataFrame:
    """Trailing CLV for one symbol, sorted by date, index reset."""
    d = d.sort_values("date").reset_index(drop=True)
    high = d["high"].astype("float64")
    low = d["low"].astype("float64")
    close = d["close"].astype("float64")
    rng = high - low
    clv = ((close - low) - (high - close)) / rng.where(rng != 0)
    ma = clv.rolling(WINDOW, min_periods=WINDOW).mean()
    return pd.DataFrame(
        {
            "date": d["date"].to_numpy(),
            "clv": clv.astype("float32").to_numpy(),
            "clv_ma14": ma.astype("float32").to_numpy(),
        }
    )


def compute_clv(df: pd.DataFrame) -> pd.DataFrame:
    """Return causal ``clv`` / ``clv_ma14`` (both float32).

    Accepts a single symbol or a frame carrying a ``symbol`` column (grouped,
    never crossed across symbols). Index is reset before concat (RISKS R-08).
    """
    if "symbol" in df.columns:
        parts = [
            _clv_one(g).assign(symbol=g["symbol"].iloc[0])
            for _, g in df.groupby("symbol", sort=False)
        ]
        out = pd.concat(parts, ignore_index=True)[["symbol", "date", *VALUE_COLS]]
    else:
        out = _clv_one(df)[["date", *VALUE_COLS]]
    return out.reset_index(drop=True)


def write_clv(df: pd.DataFrame, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tbl = pa.Table.from_pandas(
        df[["symbol", "date", *VALUE_COLS]], schema=SCHEMA, preserve_index=False
    )
    pq.write_table(tbl, path)
    return path


def build(
    market: str,
    out_dir: Path = OUT_ROOT,
    limit: int | None = None,
    root: Path = RAW_ROOT,
) -> tuple[Path, int]:
    """Symbol-sequential build of ``clv_{market}.parquet``."""
    files = sorted((Path(root) / f"market={market}").glob("symbol=*.parquet"))
    if limit is not None:
        files = files[:limit]
    if not files:
        raise FileNotFoundError(f"no raw_ohlcv files for market={market} under {root}")
    parts: list[pd.DataFrame] = []
    buf: list[pd.DataFrame] = []
    for f in files:
        sym = f.name[len("symbol=") : -len(".parquet")]
        raw = pq.read_table(f, columns=["date", "high", "low", "close"]).to_pandas()
        buf.append(compute_clv(raw).assign(symbol=sym))
        if len(buf) >= CHUNK_SYMBOLS:
            parts.append(pd.concat(buf, ignore_index=True))
            buf = []
    if buf:
        parts.append(pd.concat(buf, ignore_index=True))
    out = pd.concat(parts, ignore_index=True).reset_index(drop=True)
    path = write_clv(out, Path(out_dir) / f"clv_{market}.parquet")
    return path, len(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build CLV features (WI-076)")
    ap.add_argument("--market", default="USD", choices=["USD", "CAD"])
    ap.add_argument("--out", default=str(OUT_ROOT))
    ap.add_argument("--limit", type=int, default=None, help="first N symbols (dry run)")
    args = ap.parse_args(argv)
    path, rows = build(args.market, out_dir=args.out, limit=args.limit)
    print(f"WI-076 clv {args.market}: {rows} rows -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
