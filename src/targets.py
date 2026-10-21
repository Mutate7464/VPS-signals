"""Point-in-time target labeler (Sprint 2).

Computes four forward binary regime labels evaluated strictly over the forward
horizon [t+1, t+k]. The ATR_20 used inside the thresholds is a *trailing*
(<= t) quantity, so the labels never use future data to construct their own
thresholds — they only observe the forward price path they are meant to predict.

  Y_15d_High : 15-day local peak / exhaustion inflection (sell/trim).
  Y_15d_Low  : 15-day durable floor or V-bottom spring (buy).
  Y_20d_Up   : 20-day sustained upward trend (OLS slope > 0, R^2 >= 0.60).
  Y_20d_Down : 20-day sustained downward trend (OLS slope < 0, R^2 >= 0.60).

Output columns are float64 with NaN where the forward window is incomplete
(the trailing k rows); the dataset builder drops those rows and casts to int8.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

ATR_WINDOW = 20
HIGH_HORIZON = 15
LOW_HORIZON = 15
SPRING_MIN_HORIZON = 10
TREND_HORIZON = 20
TREND_MIN_R2 = 0.60
TREND_ATR_MULT = 2.0

TARGET_COLUMNS = ["y_15d_high", "y_15d_low", "y_20d_up", "y_20d_down"]


def wilder_atr(df: pd.DataFrame, window: int = ATR_WINDOW) -> pd.Series:
    """Wilder-smoothed Average True Range (trailing, causal)."""
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1.0 / window, min_periods=window, adjust=False).mean()


def _forward_roll(arr: np.ndarray, horizon: int, agg: str) -> np.ndarray:
    """Aggregate over the forward window [t+1 .. t+horizon], aligned to index t."""
    a = np.asarray(arr, dtype="float64")
    n = len(a)
    out = np.full(n, np.nan)
    if n <= horizon:
        return out
    sw = sliding_window_view(a, horizon + 1)  # sw[t] = a[t .. t+horizon]
    fwd = sw[:, 1:]  # fwd[t] = a[t+1 .. t+horizon]
    if agg == "max":
        res = fwd.max(axis=1)
    elif agg == "min":
        res = fwd.min(axis=1)
    elif agg == "last":
        res = fwd[:, -1]
    else:
        raise ValueError(f"unknown agg: {agg}")
    out[: len(res)] = res
    return out


def _ols_forward_slope_r2(log_close: np.ndarray, horizon: int):
    """OLS slope + R^2 of log prices over the forward window [t+1 .. t+horizon].

    Fully vectorized via least-squares closed form on sliding windows.
    """
    a = np.asarray(log_close, dtype="float64")
    n = len(a)
    slope = np.full(n, np.nan)
    r2 = np.full(n, np.nan)
    if n <= horizon:
        return slope, r2

    sw = sliding_window_view(a, horizon + 1)
    y = sw[:, 1:]  # (m, horizon) forward log prices
    x = np.arange(1, horizon + 1, dtype="float64")
    xc = x - x.mean()
    denom = float((xc ** 2).sum())

    ybar = y.mean(axis=1)
    yc = y - ybar[:, None]
    s = (yc @ xc) / denom  # sum((x-xbar)(y-ybar)) / sum((x-xbar)^2)

    yhat = ybar[:, None] + s[:, None] * xc[None, :]
    sse = ((y - yhat) ** 2).sum(axis=1)
    sst = (yc ** 2).sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = 1.0 - sse / sst
    r = np.where(sst == 0.0, np.nan, r)

    slope[: len(s)] = s
    r2[: len(r)] = r
    return slope, r2


def compute_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Return the four forward labels as float64 (NaN where undefined).

    Assumes `df` is sorted by date with a clean 0..n-1 index.
    """
    close = df["close"].astype("float64").to_numpy()
    high = df["high"].astype("float64").to_numpy()
    low = df["low"].astype("float64").to_numpy()
    atr = wilder_atr(df).astype("float64").to_numpy()

    fwd_high_15 = _forward_roll(high, HIGH_HORIZON, "max")
    fwd_close_15 = _forward_roll(close, HIGH_HORIZON, "last")
    fwd_low_15 = _forward_roll(low, LOW_HORIZON, "min")
    fwd_close_high_15 = _forward_roll(close, LOW_HORIZON, "max")
    fwd_low_10 = _forward_roll(low, SPRING_MIN_HORIZON, "min")
    fwd_close_20 = _forward_roll(close, TREND_HORIZON, "last")

    # Y_15d_High: rally to a peak then stall/reverse, OR immediate top rejection.
    cond1 = (fwd_high_15 >= close + 2.0 * atr) & (fwd_close_15 <= fwd_high_15 - 1.25 * atr)
    cond2 = (fwd_high_15 <= close + 0.35 * atr) & (fwd_close_15 <= close - 1.5 * atr)
    y_high = cond1 | cond2

    # Y_15d_Low: durable 15-day floor bounce, OR V-bottom spring reversal.
    cond1 = (fwd_low_15 >= close - 0.5 * atr) & (fwd_close_high_15 >= close + 2.0 * atr)
    cond2 = (fwd_low_10 <= close - 1.5 * atr) & (fwd_close_15 >= fwd_low_10 + 2.0 * atr)
    y_low = cond1 | cond2

    # Y_20d_Up / Y_20d_Down: ATR-adjusted forward return + trend slope + R^2.
    slope, r2 = _ols_forward_slope_r2(np.log(close), TREND_HORIZON)
    fwd_ret = fwd_close_20 - close
    y_up = (fwd_ret >= TREND_ATR_MULT * atr) & (slope > 0.0) & (r2 >= TREND_MIN_R2)
    y_down = (fwd_ret <= -TREND_ATR_MULT * atr) & (slope < 0.0) & (r2 >= TREND_MIN_R2)

    # Mask rows where the forward window is incomplete -> NaN (undefined).
    valid_15 = ~np.isnan(fwd_close_15)
    valid_20 = ~np.isnan(fwd_close_20)

    return pd.DataFrame(
        {
            "y_15d_high": np.where(valid_15, y_high.astype("float64"), np.nan),
            "y_15d_low": np.where(valid_15, y_low.astype("float64"), np.nan),
            "y_20d_up": np.where(valid_20, y_up.astype("float64"), np.nan),
            "y_20d_down": np.where(valid_20, y_down.astype("float64"), np.nan),
        }
    )
