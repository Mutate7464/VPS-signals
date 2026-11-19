"""L1-BIF trailing swing/retracement-level DISTANCE features (WI-081).

Design: ``docs/workflow/designs/D-029-l1-bifurcation.md`` (WI-080 boundary rule).
License: D-023 layer 1 (predictive only) — causal bar geometry only; no trading
or economic metric is computed or exported here.

Definition (strictly causal: bar ``t`` uses bars ``t-window+1..t`` only)
  * ``level_high_t = max(high)`` / ``level_low_t = min(low)`` over the trailing
    swing window (``SWING_WINDOW`` bars), emitted at the CONFIRMATION bar and
    never back-filled onto its pivot bar (WI-080 ``trailing_level``);
  * retracement levels ``low + f * (high - low)`` for ``f`` in {0.5, 0.75};
  * ``atr_t`` = Wilder ATR (``ATR_WINDOW``) over the same causal bars;
  * ``dist_to_swing_hi_atr_t = (level_high_t - close_t) / atr_t`` (positive when
    price sits below the swing high), ``dist_to_swing_lo_atr_t`` mirrored, and
    ``dist_ret{50,75}_atr_t = (close_t - retrace level) / atr_t`` (signed).

NaN-propagating: the first ``window-1`` bars per symbol are NaN; a zero-width
trailing range carries no retracement evidence, so ``dist_ret*`` is NaN there,
never ``0.0``; a zero ATR yields NaN, never ``inf``.

Prereg: this card is the prereg for its own BH-FDR family (``l1-swing-levels``);
its eval job is sized separately and checkpointed. Output columns pass
``assert_boundary`` (D-029): no ``fwd_*`` / ``y_*`` / MFE-MAE / model output.

Repo invariants: symbol-sequential reads, float32 immediately after calculation,
index reset before concat (RISKS R-08), n_jobs=2 (single-process module).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.l1_bif.bif_boundary import assert_boundary, concat_frames, to_float32, trailing_level

SWING_WINDOW = 20
ATR_WINDOW = 20
RETRACE_EXT = 0.75
N_JOBS = 2  # declared, unused: work is symbol-sequential I/O bound
RAW_ROOT = Path("data/raw_ohlcv")
OUT_ROOT = Path("data/features/l0_ext")
CHUNK_SYMBOLS = 50
VALUE_COLS = [
    "dist_to_swing_hi_atr",
    "dist_to_swing_lo_atr",
    "dist_ret50_atr",
    "dist_ret75_atr",
]
SCHEMA = pa.schema(
    [("symbol", pa.string()), ("date", pa.date32())]
    + [(c, pa.float32()) for c in VALUE_COLS]
)


def _wilder_atr(high: pd.Series, low: pd.Series, close: pd.Series,
                window: int = ATR_WINDOW) -> pd.Series:
    """Trailing Wilder ATR (causal, ``min_periods=window``)."""
    if window < 2:
        raise ValueError("atr_window must be >= 2")
    prev = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev).abs(), (low - prev).abs()], axis=1
    ).max(axis=1)
    return tr.ewm(alpha=1.0 / window, min_periods=window, adjust=False).mean()


def _swing_one(d: pd.DataFrame, window: int = SWING_WINDOW,
               atr_window: int = ATR_WINDOW) -> pd.DataFrame:
    """Confirmation-dated level distances for one symbol (index reset, float32)."""
    d = d.sort_values("date").reset_index(drop=True)
    lv = trailing_level(d, window=window, retrace=0.5).reset_index(drop=True)
    high = d["high"].astype("float64")
    low = d["low"].astype("float64")
    close = d["close"].astype("float64")
    lh = lv["level_high"].astype("float64")
    ll = lv["level_low"].astype("float64")
    atr = _wilder_atr(high, low, close, atr_window)
    denom = atr.where(atr > 0)  # zero ATR carries no distance evidence -> NaN
    ret50 = lv["retrace_50"].astype("float64")
    # same NaN pattern as ret50: a zero-width trailing range yields NaN, not 0.0
    ret75 = (ll + RETRACE_EXT * (lh - ll)).where(ret50.notna())
    out = pd.DataFrame(
        {
            "date": d["date"].to_numpy(),
            "dist_to_swing_hi_atr": (lh - close) / denom,
            "dist_to_swing_lo_atr": (close - ll) / denom,
            "dist_ret50_atr": (close - ret50) / denom,
            "dist_ret75_atr": (close - ret75) / denom,
        }
    )
    return to_float32(out).reset_index(drop=True)


def compute_swing_levels(lf: pd.DataFrame, window: int = SWING_WINDOW,
                         atr_window: int = ATR_WINDOW) -> pd.DataFrame:
    """Return the four causal ATR-normalised swing/retracement distances (float32).

    Accepts a single symbol or a frame carrying a ``symbol`` column (grouped,
    never crossed across symbols). Index is reset before concat (RISKS R-08).
    Output columns pass :func:`~src.l1_bif.bif_boundary.assert_boundary`.
    """
    if "symbol" in lf.columns:
        parts = [
            _swing_one(g, window, atr_window).assign(symbol=g["symbol"].iloc[0])
            for _, g in lf.groupby("symbol", sort=False)
        ]
        out = concat_frames(parts)[["symbol", "date", *VALUE_COLS]]
    else:
        out = _swing_one(lf, window, atr_window)[["date", *VALUE_COLS]]
        out = out.reset_index(drop=True)
    assert_boundary(list(out.columns))
    return out.reset_index(drop=True)


def write_swing_levels(df: pd.DataFrame, path: Path) -> Path:
    """Write ``symbol, date(date32), <four float32 distances>`` to parquet."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tbl = pa.Table.from_pandas(
        df[["symbol", "date", *VALUE_COLS]], schema=SCHEMA, preserve_index=False
    )
    pq.write_table(tbl, path)
    return path


def build(market: str, out_dir: Path = OUT_ROOT, limit: int | None = None,
          root: Path = RAW_ROOT, window: int = SWING_WINDOW,
          atr_window: int = ATR_WINDOW) -> tuple[Path, int]:
    """Symbol-sequential build of ``swing_levels_{market}.parquet``."""
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
        buf.append(compute_swing_levels(raw, window, atr_window).assign(symbol=sym))
        if len(buf) >= CHUNK_SYMBOLS:
            parts.append(pd.concat(buf, ignore_index=True))
            buf = []
    if buf:
        parts.append(pd.concat(buf, ignore_index=True))
    out = pd.concat(parts, ignore_index=True).reset_index(drop=True)
    path = write_swing_levels(out, Path(out_dir) / f"swing_levels_{market}.parquet")
    return path, len(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build L1 swing-level distances (WI-081)")
    ap.add_argument("--market", default="USD", choices=["USD", "CAD"])
    ap.add_argument("--out", default=str(OUT_ROOT))
    ap.add_argument("--limit", type=int, default=None, help="first N symbols (dry run)")
    ap.add_argument("--window", type=int, default=SWING_WINDOW)
    ap.add_argument("--atr-window", type=int, default=ATR_WINDOW)
    args = ap.parse_args(argv)
    path, rows = build(args.market, out_dir=args.out, limit=args.limit,
                       window=args.window, atr_window=args.atr_window)
    print(f"WI-081 swing_levels {args.market}: {rows} rows -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
