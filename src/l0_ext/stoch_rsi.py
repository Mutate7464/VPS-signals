"""L0 extension: causal StochRSI (14,14) (WI-077).

Predictive-only license (D-023 layer 1): causal oscillator geometry only. No
trading or economic metric is computed here.

Definition:
  * ``rsi_t`` = Wilder RSI(14) on ``close``: ``delta_t = close_t - close_{t-1}``,
    ``avg_gain``/``avg_loss`` = EWM(alpha=1/14, adjust=False, min_periods=14) of
    the up/down legs, ``rsi = 100 - 100 / (1 + avg_gain/avg_loss)`` (an all-gain
    window with ``avg_loss == 0`` gives ``rsi = 100``); NaN during the 14-bar
    warmup;
  * ``stochrsi_14_14_t`` = stochastic of ``rsi`` over the last 14 bars:
    ``(rsi_t - min_14) / (max_14 - min_14)`` in ``[0, 1]``; NaN-propagating (any
    NaN inside the window, or a flat window with ``max == min``, yields NaN).

Strictly causal: bar ``t`` uses bar ``t`` and earlier only, so values are never
revised by later bars.

Prereg family id: ``l0-stochrsi``. Repo invariants honoured: symbol-sequential
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

RSI_PERIOD = 14
STOCH_PERIOD = 14
WARMUP = RSI_PERIOD + STOCH_PERIOD - 1  # first bar with a full RSI+stoch window
N_JOBS = 2  # declared, unused: work is symbol-sequential I/O bound
RAW_ROOT = Path("data/raw_ohlcv")
OUT_ROOT = Path("data/features/l0_ext")
CHUNK_SYMBOLS = 50
VALUE_COLS = ["stochrsi_14_14"]
SCHEMA = pa.schema(
    [
        ("symbol", pa.string()),
        ("date", pa.date32()),
        ("stochrsi_14_14", pa.float32()),
    ]
)


def _stochrsi_one(d: pd.DataFrame) -> pd.DataFrame:
    """Trailing StochRSI for one symbol, sorted by date, index reset."""
    d = d.sort_values("date").reset_index(drop=True)
    close = d["close"].astype("float64")
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(
        alpha=1.0 / RSI_PERIOD, adjust=False, min_periods=RSI_PERIOD
    ).mean()
    avg_loss = loss.ewm(
        alpha=1.0 / RSI_PERIOD, adjust=False, min_periods=RSI_PERIOD
    ).mean()
    rs = avg_gain / avg_loss
    rsi = 100.0 - 100.0 / (1.0 + rs)
    rsi = rsi.where(avg_loss != 0.0, 100.0)  # all-gain window -> RSI 100
    lo = rsi.rolling(STOCH_PERIOD, min_periods=STOCH_PERIOD).min()
    hi = rsi.rolling(STOCH_PERIOD, min_periods=STOCH_PERIOD).max()
    rng = hi - lo
    stoch = (rsi - lo) / rng.where(rng != 0.0)
    return pd.DataFrame(
        {
            "date": d["date"].to_numpy(),
            "stochrsi_14_14": stoch.astype("float32").to_numpy(),
        }
    )


def compute_stochrsi(df: pd.DataFrame) -> pd.DataFrame:
    """Return causal ``stochrsi_14_14`` (float32).

    Accepts a single symbol or a frame carrying a ``symbol`` column (grouped,
    never crossed across symbols). Index is reset before concat (RISKS R-08).
    """
    if "symbol" in df.columns:
        parts = [
            _stochrsi_one(g).assign(symbol=g["symbol"].iloc[0])
            for _, g in df.groupby("symbol", sort=False)
        ]
        out = pd.concat(parts, ignore_index=True)[["symbol", "date", *VALUE_COLS]]
    else:
        out = _stochrsi_one(df)[["date", *VALUE_COLS]]
    return out.reset_index(drop=True)


def write_stochrsi(df: pd.DataFrame, path: Path) -> Path:
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
    """Symbol-sequential build of ``stoch_rsi_{market}.parquet``."""
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
        buf.append(compute_stochrsi(raw).assign(symbol=sym))
        if len(buf) >= CHUNK_SYMBOLS:
            parts.append(pd.concat(buf, ignore_index=True))
            buf = []
    if buf:
        parts.append(pd.concat(buf, ignore_index=True))
    out = pd.concat(parts, ignore_index=True).reset_index(drop=True)
    path = write_stochrsi(out, Path(out_dir) / f"stoch_rsi_{market}.parquet")
    return path, len(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build StochRSI features (WI-077)")
    ap.add_argument("--market", default="USD", choices=["USD", "CAD"])
    ap.add_argument("--out", default=str(OUT_ROOT))
    ap.add_argument("--limit", type=int, default=None, help="first N symbols (dry run)")
    args = ap.parse_args(argv)
    path, rows = build(args.market, out_dir=args.out, limit=args.limit)
    print(f"WI-077 stoch_rsi {args.market}: {rows} rows -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
