"""L0 extension: NR4/NR7 narrow-range compression flags (WI-074).

Predictive-only license (D-023 layer 1): this module computes causal 0/1 flags,
never trading or economic metrics.

Strictly causal: bar ``t`` uses bars ``t`` and earlier only (trailing rolling
window). Window edges propagate NaN instead of a spurious 0/1.
Prereg family id: ``l0-nr4nr7``.

Repo invariants honoured: symbol-sequential reads, float32 immediately after
calculation, chunked concat (no all-ticker uncompressed frame), n_jobs=2 (this
module is single-process and needs no parallelism).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

WINDOWS = (4, 7)
N_JOBS = 2  # declared, unused: work is symbol-sequential I/O bound
RAW_ROOT = Path("data/raw_ohlcv")
OUT_ROOT = Path("data/features/l0_ext")
CHUNK_SYMBOLS = 50
FLAG_COLS = ["nr4", "nr7"]
SCHEMA = pa.schema(
    [
        ("symbol", pa.string()),
        ("date", pa.date32()),
        ("nr4", pa.float32()),
        ("nr7", pa.float32()),
    ]
)


def _flags_one(d: pd.DataFrame) -> pd.DataFrame:
    """Trailing NR flags for a single symbol, sorted by date, index reset."""
    d = d.sort_values("date").reset_index(drop=True)
    rng = (d["high"].astype("float32") - d["low"].astype("float32")).astype("float32")
    out = pd.DataFrame({"date": d["date"].to_numpy()})
    for w in WINDOWS:
        mn = rng.rolling(w, min_periods=w).min()
        flag = (rng <= mn).astype("float32")
        flag[mn.isna()] = np.nan
        out[f"nr{w}"] = flag.astype("float32")
    return out.reset_index(drop=True)


def compute_nr_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Return causal ``nr4``/``nr7`` float32 flags (NaN before the window fills).

    Handles a single symbol or a frame carrying a ``symbol`` column (grouped,
    never crossed across symbols). Index is reset before concat (RISKS R-08).
    """
    if "symbol" in df.columns:
        parts = [
            _flags_one(g).assign(symbol=g["symbol"].iloc[0])
            for _, g in df.groupby("symbol", sort=False)
        ]
        out = pd.concat(parts, ignore_index=True)
        out = out[["symbol", "date", *FLAG_COLS]]
    else:
        out = _flags_one(df)[["date", *FLAG_COLS]]
    return out.reset_index(drop=True)


def write_nr_flags(df: pd.DataFrame, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tbl = pa.Table.from_pandas(
        df[["symbol", "date", *FLAG_COLS]], schema=SCHEMA, preserve_index=False
    )
    pq.write_table(tbl, path)
    return path


def build(
    market: str, out_dir: Path = OUT_ROOT, limit: int | None = None, root: Path = RAW_ROOT
) -> tuple[Path, int]:
    """Symbol-sequential build of ``nr_flags_{market}.parquet``."""
    files = sorted((Path(root) / f"market={market}").glob("symbol=*.parquet"))
    if limit is not None:
        files = files[:limit]
    if not files:
        raise FileNotFoundError(f"no raw_ohlcv files for market={market} under {root}")
    parts: list[pd.DataFrame] = []
    buf: list[pd.DataFrame] = []
    for f in files:
        sym = f.name[len("symbol=") : -len(".parquet")]
        raw = pq.read_table(f, columns=["date", "high", "low"]).to_pandas()
        buf.append(compute_nr_flags(raw).assign(symbol=sym))
        if len(buf) >= CHUNK_SYMBOLS:
            parts.append(pd.concat(buf, ignore_index=True))
            buf = []
    if buf:
        parts.append(pd.concat(buf, ignore_index=True))
    out = pd.concat(parts, ignore_index=True).reset_index(drop=True)
    path = write_nr_flags(out, Path(out_dir) / f"nr_flags_{market}.parquet")
    return path, len(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build NR4/NR7 flags (WI-074)")
    ap.add_argument("--market", default="USD", choices=["USD", "CAD"])
    ap.add_argument("--out", default=str(OUT_ROOT))
    ap.add_argument("--limit", type=int, default=None, help="first N symbols (dry run)")
    args = ap.parse_args(argv)
    path, rows = build(args.market, out_dir=args.out, limit=args.limit)
    print(f"WI-074 nr_flags {args.market}: {rows} rows -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
