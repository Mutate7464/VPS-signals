"""L0 extension: causal Connors RSI (WI-078).

Predictive-only license (D-023 layer 1): a causal oscillator composite only. No
trading or economic metric is computed here.

Definition (all components trailing, bar ``t`` uses bar ``t`` and earlier only):
  * ``rsi_price_t`` = Wilder RSI(3) on ``close``:
    ``delta_t = close_t - close_{t-1}``, ``avg_gain``/``avg_loss`` =
    EWM(alpha=1/3, adjust=False, min_periods=3) of the up/down legs,
    ``rsi = 100 - 100 / (1 + avg_gain/avg_loss)``; a zero ``avg_loss`` window
    (all-gain, or a flat stretch with ``avg_gain == avg_loss == 0``) gives
    ``rsi = 100``; NaN during the 3-bar warmup;
  * ``streak_t`` = signed run length of consecutive closes in the same
    direction: ``+k`` after ``k`` consecutive up closes, ``-k`` after ``k``
    consecutive down closes, ``0`` on an unchanged close; NaN for the first bar;
  * ``rsi_streak_t`` = Wilder RSI(2) of ``streak`` (same EWM/min_periods
    convention; a zero ``avg_loss`` window gives 100);
  * ``pr_t`` = percent rank of the 1-bar return ``close_t/close_{t-1} - 1``
    inside the trailing ``PR_WINDOW``-bar return window: ``100 * (#window
    returns strictly below the current return) / (PR_WINDOW - 1)`` in
    ``[0, 100]``; NaN until a full NaN-free window exists;
  * ``connors_rsi_t`` = ``(rsi_price_t + rsi_streak_t + pr_t) / 3`` —
    NaN-propagating, so the first valid value is bar index ``WARMUP`` (= 252).

Strictly causal: values are never revised by later bars (append-invariance).

Prereg family id: ``l0-crsi``. Repo invariants honoured: symbol-sequential
reads, float32 immediately after calculation, chunked concat (no all-ticker
uncompressed frame), n_jobs=2 (this module is single-process / I/O bound).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

RSI_PRICE = 3
RSI_STREAK = 2
PR_WINDOW = 252
WARMUP = PR_WINDOW  # first bar with a full return window; RSI warmups are shorter
N_JOBS = 2  # declared, unused: work is symbol-sequential I/O bound
RAW_ROOT = Path("data/raw_ohlcv")
OUT_ROOT = Path("data/features/l0_ext")
CHUNK_SYMBOLS = 50
VALUE_COLS = ["connors_rsi"]
SCHEMA = pa.schema(
    [
        ("symbol", pa.string()),
        ("date", pa.date32()),
        ("connors_rsi", pa.float32()),
    ]
)


def _streak(close: np.ndarray) -> np.ndarray:
    """Signed run length of consecutive closes; NaN for the first bar."""
    n = close.size
    out = np.full(n, np.nan, dtype="float64")
    if n < 2:
        return out
    sign = np.sign(np.diff(close.astype("float64")))
    idx = np.arange(sign.size)
    new_run = np.empty(sign.size, dtype=bool)
    new_run[0] = True
    new_run[1:] = sign[1:] != sign[:-1]
    start = np.maximum.accumulate(np.where(new_run, idx, 0))
    out[1:] = (idx - start + 1).astype("float64") * sign  # sign 0 -> streak 0
    return out


def _percent_rank(roc: np.ndarray, window: int) -> np.ndarray:
    """Trailing percent rank (0-100) of the last value of each window."""
    n = roc.size
    out = np.full(n, np.nan, dtype="float64")
    r = roc[1:]  # drop the first bar: its return does not exist
    if r.size < window:
        return out
    w = np.lib.stride_tricks.sliding_window_view(r, window)
    base, cur = w[:, :-1], w[:, -1:]
    cnt = (base < cur).sum(axis=1).astype("float64")
    bad = np.isnan(base).any(axis=1) | np.isnan(cur[:, 0])
    vals = 100.0 * cnt / float(window - 1)  # strict-inequality rank in [0, 100]
    out[window:] = np.where(bad, np.nan, vals)
    return out


def _wilder_rsi(x: pd.Series, period: int) -> pd.Series:
    """Wilder RSI on a trailing series; zero avg_loss window -> 100."""
    delta = x.diff()
    avg_gain = (
        delta.clip(lower=0.0)
        .ewm(alpha=1.0 / period, adjust=False, min_periods=period)
        .mean()
    )
    avg_loss = (
        (-delta).clip(lower=0.0)
        .ewm(alpha=1.0 / period, adjust=False, min_periods=period)
        .mean()
    )
    rsi = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    return rsi.where(avg_loss != 0.0, 100.0)


def _connors_one(d: pd.DataFrame) -> pd.DataFrame:
    """Trailing Connors RSI for one symbol, sorted by date, index reset."""
    d = d.sort_values("date").reset_index(drop=True)
    close = d["close"].astype("float64")
    streak = pd.Series(_streak(close.to_numpy()), index=close.index)
    rsi_price = _wilder_rsi(close, RSI_PRICE)
    rsi_streak = _wilder_rsi(streak, RSI_STREAK)
    pr = pd.Series(
        _percent_rank(close.pct_change().to_numpy(), PR_WINDOW), index=close.index
    )
    crsi = (rsi_price + rsi_streak + pr) / 3.0  # NaN-propagating composite
    return pd.DataFrame(
        {
            "date": d["date"].to_numpy(),
            "connors_rsi": crsi.astype("float32").to_numpy(),
        }
    )


def compute_connors_rsi(lf: pd.DataFrame) -> pd.DataFrame:
    """Return causal ``connors_rsi`` (float32).

    Accepts a single symbol or a frame carrying a ``symbol`` column (grouped,
    never crossed across symbols). Index is reset before concat (RISKS R-08).
    """
    if "symbol" in lf.columns:
        parts = [
            _connors_one(g).assign(symbol=g["symbol"].iloc[0])
            for _, g in lf.groupby("symbol", sort=False)
        ]
        out = pd.concat(parts, ignore_index=True)[["symbol", "date", *VALUE_COLS]]
    else:
        out = _connors_one(lf)[["date", *VALUE_COLS]]
    return out.reset_index(drop=True)


def write_connors_rsi(df: pd.DataFrame, path: Path) -> Path:
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
    """Symbol-sequential build of ``connors_rsi_{market}.parquet``."""
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
        buf.append(compute_connors_rsi(raw).assign(symbol=sym))
        if len(buf) >= CHUNK_SYMBOLS:
            parts.append(pd.concat(buf, ignore_index=True))
            buf = []
    if buf:
        parts.append(pd.concat(buf, ignore_index=True))
    out = pd.concat(parts, ignore_index=True).reset_index(drop=True)
    path = write_connors_rsi(out, Path(out_dir) / f"connors_rsi_{market}.parquet")
    return path, len(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build Connors RSI features (WI-078)")
    ap.add_argument("--market", default="USD", choices=["USD", "CAD"])
    ap.add_argument("--out", default=str(OUT_ROOT))
    ap.add_argument("--limit", type=int, default=None, help="first N symbols (dry run)")
    args = ap.parse_args(argv)
    path, rows = build(args.market, out_dir=args.out, limit=args.limit)
    print(f"WI-078 connors_rsi {args.market}: {rows} rows -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
