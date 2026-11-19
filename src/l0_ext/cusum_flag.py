"""L0 extension: causal CUSUM structural-break flag (WI-075).

Predictive-only license (D-023 layer 1): this module computes causal break
flags/statistics, never trading or economic metrics.

Definition (fixed threshold ``threshold``, fixed-width window ``WINDOW``, slack
``SLACK``):
  * ``r_t = close_t / close_{t-1} - 1`` (causal: bars ``t`` and ``t-1`` only);
  * ``sigma_t`` = trailing rolling std of ``r`` over ``WINDOW`` bars
    (``min_periods=WINDOW``);
  * ``z_t = r_t / sigma_t`` (a zero-variance window contributes no evidence, so
    ``z_t = 0`` there; NaN during the warmup window);
  * two-sided tabular CUSUM on ``z``, reset at fixed-width block boundaries
    (blocks of ``WINDOW`` bars): ``A_t = cumsum(z) - SLACK * t`` and
    ``cusum_stat_t = max(up_t, dn_t)`` with ``up_t = A_t - min(0, A_{s..t-1})``
    and ``dn_t`` the same on ``-z`` (``s`` = block start);
  * ``cusum_flag_t = 1`` if a break (``cusum_stat > threshold``) was detected at
    some bar ``s <= t`` inside the current block, else 0.

Strictly causal: bar ``t`` uses bars ``t`` and earlier only, so flags are never
revised by later bars. Window edges propagate NaN (``cusum_stat``), and the
partial block that overlaps the warmup is NaN as well.

Prereg family id: ``l0-cusum``. Repo invariants honoured: symbol-sequential
reads, float32 immediately after calculation, chunked concat (no all-ticker
uncompressed frame), n_jobs=2 (this module is single-process).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

WINDOW = 20
SLACK = 0.5
N_JOBS = 2  # declared, unused: work is symbol-sequential I/O bound
RAW_ROOT = Path("data/raw_ohlcv")
OUT_ROOT = Path("data/features/l0_ext")
CHUNK_SYMBOLS = 50
VALUE_COLS = ["cusum_flag", "cusum_stat"]
SCHEMA = pa.schema(
    [
        ("symbol", pa.string()),
        ("date", pa.date32()),
        ("cusum_flag", pa.int8()),
        ("cusum_stat", pa.float32()),
    ]
)


def _cusum_one(
    d: pd.DataFrame, threshold: float, window: int, slack: float
) -> pd.DataFrame:
    """Trailing CUSUM for one symbol, sorted by date, index reset."""
    d = d.sort_values("date").reset_index(drop=True)
    n = len(d)
    close = d["close"].astype("float64")
    r = close.pct_change()
    sigma = r.rolling(window, min_periods=window).std()
    warm = sigma.isna().to_numpy()
    z = (r / sigma).where(sigma > 0, 0.0)
    zn = z.to_numpy(dtype="float64", copy=True)
    zn[warm] = np.nan

    stat = np.full(n, np.nan, dtype="float64")
    flag = np.zeros(n, dtype="int8")
    start = int(np.argmax(~warm)) if (~warm).any() else n
    bs = ((start + window - 1) // window) * window  # next clean block boundary
    if bs < n:
        seg = zn[bs:]
        m = seg.size
        i = np.arange(m, dtype="float64")
        blk = np.arange(m) // window
        starts = np.flatnonzero(np.r_[True, np.diff(blk) != 0])

        def _up(s: np.ndarray) -> np.ndarray:
            a = np.cumsum(s) - slack * i
            cand = np.empty(m, dtype="float64")
            cand[0] = 0.0
            cand[1:] = a[:-1]
            cand[starts] = 0.0  # block baseline: CUSUM resets to 0
            return a - pd.Series(cand).groupby(blk).cummin().to_numpy()

        stat[bs:] = np.maximum(_up(seg), _up(-seg))
        exc = stat[bs:] > threshold
        flag[bs:] = pd.Series(exc).groupby(blk).cummax().to_numpy().astype("int8")

    return pd.DataFrame(
        {
            "date": d["date"].to_numpy(),
            "cusum_flag": flag,
            "cusum_stat": stat.astype("float32"),
        }
    )


def compute_cusum_flag(lf: pd.DataFrame, threshold: float = 2.0) -> pd.DataFrame:
    """Return causal ``cusum_flag`` (int8) / ``cusum_stat`` (float32).

    Accepts a single symbol or a frame carrying a ``symbol`` column (grouped,
    never crossed across symbols). Index is reset before concat (RISKS R-08).
    """
    if "symbol" in lf.columns:
        parts = [
            _cusum_one(g, threshold, WINDOW, SLACK).assign(symbol=g["symbol"].iloc[0])
            for _, g in lf.groupby("symbol", sort=False)
        ]
        out = pd.concat(parts, ignore_index=True)[["symbol", "date", *VALUE_COLS]]
    else:
        out = _cusum_one(lf, threshold, WINDOW, SLACK)[["date", *VALUE_COLS]]
    return out.reset_index(drop=True)


def write_cusum_flag(df: pd.DataFrame, path: Path) -> Path:
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
    threshold: float = 2.0,
) -> tuple[Path, int]:
    """Symbol-sequential build of ``cusum_flag_{market}.parquet``."""
    files = sorted((Path(root) / f"market={market}").glob("symbol=*.parquet"))
    if limit is not None:
        files = files[:limit]
    if not files:
        raise FileNotFoundError(f"no raw_ohlcv files for market={market} under {root}")
    parts: list[pd.DataFrame] = []
    buf: list[pd.DataFrame] = []
    for f in files:
        sym = f.name[len("symbol=") : -len(".parquet")]
        raw = pq.read_table(f, columns=["date", "close"]).to_pandas()
        buf.append(compute_cusum_flag(raw, threshold=threshold).assign(symbol=sym))
        if len(buf) >= CHUNK_SYMBOLS:
            parts.append(pd.concat(buf, ignore_index=True))
            buf = []
    if buf:
        parts.append(pd.concat(buf, ignore_index=True))
    out = pd.concat(parts, ignore_index=True).reset_index(drop=True)
    path = write_cusum_flag(out, Path(out_dir) / f"cusum_flag_{market}.parquet")
    return path, len(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build CUSUM break flags (WI-075)")
    ap.add_argument("--market", default="USD", choices=["USD", "CAD"])
    ap.add_argument("--out", default=str(OUT_ROOT))
    ap.add_argument("--limit", type=int, default=None, help="first N symbols (dry run)")
    ap.add_argument("--threshold", type=float, default=2.0)
    args = ap.parse_args(argv)
    path, rows = build(args.market, out_dir=args.out, limit=args.limit, threshold=args.threshold)
    print(f"WI-075 cusum_flag {args.market}: {rows} rows -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
