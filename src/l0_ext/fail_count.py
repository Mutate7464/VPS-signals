"""L0 extension: rolling failed-swing-signal count (WI-079).

Predictive-only license (D-023 layer 1): a causal count of recently *resolved*
failed swing signals, never a trading or economic metric.

Definition (fixed parameters, all trailing):
  * swing signal at bar ``t`` = the WI-032 causal geometry, imported and never
    re-implemented: ``detect_swings`` — ``at_bottom`` (``low_t`` is the trailing
    ``SWING_WINDOW``-bar minimum) or ``at_top`` (``high_t`` the maximum), with
    same-side events closer than ``CLUSTER_GAP`` bars collapsed to the first;
  * outcome = first touch of the ``k·ATR`` barriers inside ``[t+1, t+HORIZON]``
    (``ATR_t`` = trailing Wilder ATR, ``src.targets.wilder_atr``): the stop side
    (``close_t - k·ATR`` for ``at_bottom``, ``+k·ATR`` for ``at_top``) touched
    strictly before the profit side is a **failure**; a same-bar tie goes to the
    stop side (pessimistic, D-016); surviving the horizon is not a failure;
  * ``fail_count_t`` = count of failures whose outcome resolved in the last
    ``WINDOW`` bars, i.e. failures are recorded at their resolution bar
    ``t + HORIZON`` — never earlier (lag >= HORIZON, the family's main leakage
    risk). The observation is undefined (NaN) until the outcome of the oldest
    possible signal can be resolved, and windows with any undefined bar stay
    NaN (NaN-propagating, ``min_periods=WINDOW``).

Strictly causal: bar ``t`` uses bars ``t`` and earlier only, so values are never
revised by later bars. Prereg family id: ``l0-failcount``. Repo invariants:
symbol-sequential reads, float32 immediately after calculation, chunked concat
(no all-ticker uncompressed frame), index reset before concat (RISKS R-08),
n_jobs=2 (this module is single-process).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.swing_bsh.events import CLUSTER_GAP, SWING_WINDOW, detect_swings
from src.targets import wilder_atr

WINDOW = 20
HORIZON = 20
K_ATR = 1.5
N_JOBS = 2  # declared, unused: work is symbol-sequential I/O bound
RAW_ROOT = Path("data/raw_ohlcv")
OUT_ROOT = Path("data/features/l0_ext")
CHUNK_SYMBOLS = 50
RAW_COLS = ["date", "high", "low", "close"]


def fail_count_col(window: int = WINDOW) -> str:
    """Output column name for a given rolling ``window``."""
    return f"fail_count_{window}"


def _count_one(
    d: pd.DataFrame, window: int, horizon: int, k_atr: float, swing_window: int, gap: int
) -> pd.DataFrame:
    """Rolling failure count for one symbol, sorted by date, index reset."""
    d = d.sort_values("date").reset_index(drop=True)
    n = len(d)
    warmup = (swing_window - 1) + horizon  # first bar whose outcome can resolve
    mark = np.zeros(n, dtype="float64")
    mark[: min(warmup, n)] = np.nan
    if n > warmup:
        close = d["close"].to_numpy(dtype="float64")
        high = d["high"].to_numpy(dtype="float64")
        low = d["low"].to_numpy(dtype="float64")
        atr = wilder_atr(d).to_numpy(dtype="float64")
        for t, state in detect_swings(d, window=swing_window, gap=gap):
            r = int(t) + horizon
            if r >= n or not np.isfinite(atr[t]):
                continue
            up = close[t] + k_atr * atr[t]
            dn = close[t] - k_atr * atr[t]
            hit_up = np.flatnonzero(high[t + 1 : r + 1] >= up)
            hit_dn = np.flatnonzero(low[t + 1 : r + 1] <= dn)
            off_up = int(hit_up[0]) if hit_up.size else horizon + 1
            off_dn = int(hit_dn[0]) if hit_dn.size else horizon + 1
            if off_up > horizon and off_dn > horizon:
                continue  # survived the horizon -> not a failure
            stop_first = off_dn <= off_up if state == "at_bottom" else off_up <= off_dn
            if stop_first:
                mark[r] += 1.0
    ser = pd.Series(mark).rolling(window, min_periods=window).sum()
    out = pd.DataFrame({"date": d["date"].to_numpy()})
    out[fail_count_col(window)] = ser.to_numpy(dtype="float32")
    return out


def compute_fail_count(
    lf: pd.DataFrame,
    window: int = WINDOW,
    horizon: int = HORIZON,
    k_atr: float = K_ATR,
    swing_window: int = SWING_WINDOW,
    gap: int = CLUSTER_GAP,
) -> pd.DataFrame:
    """Return the causal ``fail_count_<window>`` (float32) per bar.

    Accepts a single symbol or a frame carrying a ``symbol`` column (grouped,
    never crossed across symbols). Index is reset before concat (RISKS R-08).
    """
    col = fail_count_col(window)

    def one(g: pd.DataFrame) -> pd.DataFrame:
        return _count_one(
            g, window, horizon, k_atr, swing_window, gap
        )

    if "symbol" in lf.columns:
        parts = [
            one(g).assign(symbol=g["symbol"].iloc[0])
            for _, g in lf.groupby("symbol", sort=False)
        ]
        out = pd.concat(parts, ignore_index=True)[["symbol", "date", col]]
    else:
        out = one(lf)[["date", col]]
    return out.reset_index(drop=True)


def write_fail_count(df: pd.DataFrame, path: Path, window: int = WINDOW) -> Path:
    """Write the contract schema: symbol str, date date32, count int16 (null = NaN)."""
    col = fail_count_col(window)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    vals = df[col].to_numpy(dtype="float64")
    observed = np.isfinite(vals)
    tbl = pa.table(
        {
            "symbol": pa.array(df["symbol"].to_numpy(), type=pa.string()),
            "date": pa.array(df["date"].to_numpy(), type=pa.date32()),
            col: pa.array(
                np.where(observed, vals, 0.0).astype("int16"),
                type=pa.int16(),
                mask=~observed,
            ),
        }
    )
    pq.write_table(tbl, path)
    return path


def build(
    market: str,
    out_dir: Path = OUT_ROOT,
    limit: int | None = None,
    root: Path = RAW_ROOT,
    window: int = WINDOW,
) -> tuple[Path, int]:
    """Symbol-sequential build of ``fail_count_{market}.parquet``."""
    files = sorted((Path(root) / f"market={market}").glob("symbol=*.parquet"))
    if limit is not None:
        files = files[:limit]
    if not files:
        raise FileNotFoundError(f"no raw_ohlcv files for market={market} under {root}")
    parts: list[pd.DataFrame] = []
    buf: list[pd.DataFrame] = []
    for f in files:
        sym = f.name[len("symbol=") : -len(".parquet")]
        raw = pq.read_table(f, columns=RAW_COLS).to_pandas()
        buf.append(compute_fail_count(raw, window=window).assign(symbol=sym))
        if len(buf) >= CHUNK_SYMBOLS:
            parts.append(pd.concat(buf, ignore_index=True))
            buf = []
    if buf:
        parts.append(pd.concat(buf, ignore_index=True))
    out = pd.concat(parts, ignore_index=True).reset_index(drop=True)
    path = write_fail_count(out, Path(out_dir) / f"fail_count_{market}.parquet", window)
    return path, len(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build rolling failed-swing counts (WI-079)")
    ap.add_argument("--market", default="USD", choices=["USD", "CAD"])
    ap.add_argument("--out", default=str(OUT_ROOT))
    ap.add_argument("--limit", type=int, default=None, help="first N symbols (dry run)")
    ap.add_argument("--window", type=int, default=WINDOW)
    args = ap.parse_args(argv)
    path, rows = build(args.market, out_dir=args.out, limit=args.limit, window=args.window)
    print(f"WI-079 fail_count {args.market}: {rows} rows -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
