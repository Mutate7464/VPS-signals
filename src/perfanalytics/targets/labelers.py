"""T1–T4 run-target labelers (WI-015, plan step 1).

Point-in-time, per-symbol, continuous run/momentum targets over the forward
window ``[t+1, t+k]``. Every threshold is *trailing* (``<= t``): the run trigger
uses ``wilder_atr(df, 20)`` evaluated at ``t``, exactly the pattern in
``src/targets.py``. Nothing in a row's label reads data after ``t+k``.

Definitions (plan CONSTRAINTS, admin-confirmed 2026-10-28)
---------------------------------------------------------
Qualifying run: a close-to-close rise from a *bottom* session to a later *peak*
session of at least ``run_atr_mult * ATR(t)`` (fractional threshold
``mult * ATR(t) / close(t)``; ``mult=2.0`` follows the existing target pattern).

* bottom — the session in ``[t+1, peak]`` whose **low** is the minimum of that
  prefix (earliest occurrence on ties). The return is then close-to-close
  (``close[peak] / close[bottom] - 1``), per the admin decision to measure
  amplitude close-to-close and keep low-to-high only as a diagnostic.
* peak — any session in the window; the retained pair is the one with the
  largest close-to-close return among the qualifying pairs.

Targets
  T1  amplitude        — close-to-close return of the retained pair (fraction).
  T2  velocity         — T1 / elapsed sessions between bottom and peak
                         (``T1 / max(peak - bottom, 1)``), units 1/day.
  T3  duration         — longest run of consecutive up-closes inside the window
                         (days). ``close[t+1] > close[t]`` starts the first run.
  T4  frequency        — 1.0 if a qualifying pair exists in the window, else 0.0.

Diagnostics (retained pair only; NaN when nothing qualifies)
  ``diag_bottom_off_k`` / ``diag_peak_off_k`` — session offsets from ``t``
  (1..k); ``diag_lowhigh_k`` — low-to-high wick-inclusive return of the pair.

NaN policy
  * A row whose forward window is incomplete (fewer than ``k`` sessions after
    ``t``) is NaN for every column (``src/targets.py`` convention).
  * T1/T2/T4 additionally require a finite trailing ATR; where ATR is undefined
    (warm-up) they are NaN. T3 needs only closes, so it survives ATR warm-up.
  * When the window is complete but nothing qualifies, T1/T2/T4 are ``0.0``
    (plan) and the diagnostics are NaN. A flat series can never qualify because
    a qualifying pair must be a strictly positive rise.

Outputs are cast to ``float32`` immediately after calculation (host rule).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

from src.targets import wilder_atr

DEFAULT_HORIZONS: tuple[int, ...] = (15, 20)
ATR_WINDOW = 20
RUN_ATR_MULT = 2.0

TARGET_STEMS = ("t1_amp", "t2_vel", "t3_streak", "t4_freq")
DIAG_STEMS = ("diag_bottom_off", "diag_peak_off", "diag_lowhigh")


def target_columns(horizons: tuple[int, ...] = DEFAULT_HORIZONS) -> list[str]:
    """The labeler's output columns, in emitted order."""
    cols: list[str] = []
    for k in horizons:
        cols += [f"{stem}_{k}" for stem in TARGET_STEMS]
        cols += [f"{stem}_{k}" for stem in DIAG_STEMS]
    return cols


def target_value_columns(horizons: tuple[int, ...] = DEFAULT_HORIZONS) -> list[str]:
    """Only the four T1–T4 columns per horizon (no diagnostics)."""
    return [f"{stem}_{k}" for k in horizons for stem in TARGET_STEMS]


def _longest_true_run(b: np.ndarray) -> np.ndarray:
    """Length of the longest run of True in each row of a boolean matrix."""
    if b.shape[1] == 0:
        return np.zeros(b.shape[0], dtype="float64")
    c = np.zeros(b.shape, dtype="int32")
    c[:, 0] = b[:, 0]
    for j in range(1, b.shape[1]):
        c[:, j] = np.where(b[:, j], c[:, j - 1] + 1, 0)
    return c.max(axis=1).astype("float64")


def _run_targets_one_horizon(
    close: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    atr: np.ndarray,
    horizon: int,
    run_atr_mult: float,
) -> dict[str, np.ndarray]:
    """Float64 columns for one horizon; NaN where the window is incomplete."""
    n = len(close)
    m = n - horizon  # number of rows with a complete [t+1, t+horizon] window
    names = [f"{s}_{horizon}" for s in TARGET_STEMS + DIAG_STEMS]
    out = {name: np.full(n, np.nan) for name in names}
    if m <= 0:
        return out

    c_win = sliding_window_view(close[1:], horizon)  # c_win[t, j] = close[t+1+j]
    h_win = sliding_window_view(high[1:], horizon)
    l_win = sliding_window_view(low[1:], horizon)

    # Bottom for each peak j: earliest index whose low equals the minimum low of
    # the prefix [0, j]. Scan j left-to-right; the earliest bottom only moves
    # when a strictly lower low appears, so ties keep the earlier session.
    rows = np.arange(m)
    bottom_idx = np.zeros((m, horizon), dtype=np.int64)  # bottom index per peak
    cur = np.zeros(m, dtype=np.int64)
    for j in range(1, horizon):
        cur = np.where(l_win[:, j] < l_win[rows, cur], j, cur)
        bottom_idx[:, j] = cur
    bottom_close = c_win[rows[:, None], bottom_idx]  # (m, horizon) close at bottom
    ret = c_win / bottom_close - 1.0  # (m, horizon) close-to-close
    elapsed = np.arange(horizon)[None, :] - bottom_idx  # (m, horizon)

    thr = run_atr_mult * atr[:m] / close[:m]  # fractional, trailing at t
    qualifies = (ret > 0.0) & (ret >= thr[:, None])

    best = np.argmax(np.where(qualifies, ret, -np.inf), axis=1)  # (m,)
    any_q = qualifies.any(axis=1)

    t1 = np.where(any_q, ret[rows, best], 0.0)
    el = elapsed[rows, best]
    t2 = np.where(any_q, t1 / np.maximum(el, 1.0), 0.0)
    t4 = any_q.astype("float64")

    # T3 counts only closes in the window; the first day compares to close[t].
    prev = np.concatenate([close[:m, None], c_win[:, :-1]], axis=1)
    t3 = _longest_true_run(c_win > prev)

    finite_atr = np.isfinite(atr[:m])
    out[f"t1_amp_{horizon}"][:m] = np.where(finite_atr, t1, np.nan)
    out[f"t2_vel_{horizon}"][:m] = np.where(finite_atr, t2, np.nan)
    out[f"t3_streak_{horizon}"][:m] = t3
    out[f"t4_freq_{horizon}"][:m] = np.where(finite_atr, t4, np.nan)

    peak_idx = best
    bottom_at_peak = bottom_idx[rows, peak_idx]
    lowhigh = h_win[rows, peak_idx] / l_win[rows, bottom_at_peak] - 1.0
    out[f"diag_bottom_off_{horizon}"][:m] = np.where(any_q, bottom_at_peak + 1.0, np.nan)
    out[f"diag_peak_off_{horizon}"][:m] = np.where(any_q, peak_idx + 1.0, np.nan)
    out[f"diag_lowhigh_{horizon}"][:m] = np.where(any_q, lowhigh, np.nan)
    return out


def compute_run_targets(
    df: pd.DataFrame,
    horizons: tuple[int, ...] = DEFAULT_HORIZONS,
    atr_window: int = ATR_WINDOW,
    run_atr_mult: float = RUN_ATR_MULT,
) -> pd.DataFrame:
    """T1–T4 + diagnostics for one symbol's date-sorted OHLCV frame.

    Args:
        df: one symbol's bars, sorted by ``date``, clean 0..n-1 index, with
            ``open``/``high``/``low``/``close``/``volume``.
        horizons: forward windows in sessions (default 15 and 20).
        atr_window: trailing Wilder ATR window used for the run trigger.
        run_atr_mult: qualifying-run threshold in ATR multiples.

    Returns:
        A float32 frame indexed like ``df`` with the columns of
        :func:`target_columns`.
    """
    close = df["close"].astype("float64").to_numpy()
    high = df["high"].astype("float64").to_numpy()
    low = df["low"].astype("float64").to_numpy()
    atr = wilder_atr(df, atr_window).astype("float64").to_numpy()

    cols: dict[str, np.ndarray] = {}
    for k in horizons:
        cols.update(_run_targets_one_horizon(close, high, low, atr, k, run_atr_mult))
    return pd.DataFrame(cols).astype("float32")
