"""WI-015 step 1 — T1–T4 run-target labeler tests (synthetic OHLCV)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.perfanalytics.targets import (
    DEFAULT_HORIZONS,
    compute_run_targets,
    target_columns,
)

QUIET = 41  # rows of flat lead-in so the trailing ATR(20) is warm at t >= 40


def _frame(close, low=None, high=None):
    close = np.asarray(close, dtype="float64")
    n = len(close)
    low = close * 0.999 if low is None else np.asarray(low, dtype="float64")
    high = close * 1.001 if high is None else np.asarray(high, dtype="float64")
    return pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=n, freq="B"),
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "volume": 1_000_000.0,
        }
    )


def _run_series(walk: list[float]) -> np.ndarray:
    """Flat 100 for QUIET rows, then `walk` (length becomes QUIET + len(walk))."""
    return np.concatenate([np.full(QUIET, 100.0), np.asarray(walk, dtype="float64")])


def test_columns_and_dtypes():
    out = compute_run_targets(_frame(np.full(80, 100.0)))
    assert list(out.columns) == target_columns()
    assert all(str(d) == "float32" for d in out.dtypes), out.dtypes


def test_incomplete_horizons_are_nan():
    out = compute_run_targets(_frame(_run_series([100.0] * 40)))
    for k in DEFAULT_HORIZONS:
        for col in target_columns():
            if col.endswith(f"_{k}"):
                assert out[col].tail(k).isna().all(), col
        # one row before the truncation is finalised
        assert not out[f"t4_freq_{k}"].iloc[-k - 1 :].isna().all()


def test_flat_series_has_no_run_and_zero_targets():
    out = compute_run_targets(_frame(_run_series([100.0] * 40)))
    t = 40
    for k in DEFAULT_HORIZONS:
        assert out[f"t1_amp_{k}"][t] == 0.0
        assert out[f"t2_vel_{k}"][t] == 0.0
        assert out[f"t3_streak_{k}"][t] == 0.0
        assert out[f"t4_freq_{k}"][t] == 0.0
        assert np.isnan(out[f"diag_bottom_off_{k}"][t])
        assert np.isnan(out[f"diag_peak_off_{k}"][t])
        assert np.isnan(out[f"diag_lowhigh_{k}"][t])


def test_t3_longest_up_streak():
    # 5 consecutive up-closes (100->105) inside the window for t=0.
    close = [100.0] * 5 + [101.0, 102.0, 103.0, 104.0, 105.0] + [100.0] * 20
    out = compute_run_targets(_frame(close))
    assert out["t3_streak_15"][0] == 5.0
    assert out["t3_streak_20"][0] == 5.0

    # A longer streak later in the series (t=40 sees it).
    walk = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0] + [100.0] * 8
    out2 = compute_run_targets(_frame(_run_series(walk)))
    assert out2["t3_streak_15"][40] == 6.0


def test_best_bottom_to_peak_pair_and_velocity():
    walk = [100.0, 98.0, 96.0, 99.0, 102.0, 104.0, 106.0, 104.0, 100.0, 99.0, 97.0, 100.0, 101.0, 102.0, 103.0]
    out = compute_run_targets(_frame(_run_series(walk)))
    t = 40
    expected = 106.0 / 96.0 - 1.0
    assert out["t1_amp_15"][t] == pytest.approx(expected, rel=1e-5)
    assert out["t2_vel_15"][t] == pytest.approx(expected / 4.0, rel=1e-5)
    assert out["t4_freq_15"][t] == 1.0
    assert out["diag_bottom_off_15"][t] == 3.0
    assert out["diag_peak_off_15"][t] == 7.0
    # low-to-high diagnostic uses wicks of the selected pair
    expected_lh = (106.0 * 1.001) / (96.0 * 0.999) - 1.0
    assert out["diag_lowhigh_15"][t] == pytest.approx(expected_lh, rel=1e-5)


def test_no_qualifying_run_sets_zero_and_nan_diagnostics():
    walk = [100.0, 99.0, 98.0, 97.0, 96.0, 95.0, 94.0] + [93.0] * 8
    out = compute_run_targets(_frame(_run_series(walk)))
    t = 40
    assert out["t1_amp_15"][t] == 0.0
    assert out["t2_vel_15"][t] == 0.0
    assert out["t4_freq_15"][t] == 0.0
    assert np.isnan(out["diag_lowhigh_15"][t])
    # T3 still measures the streak: the window only declines, so there is none
    assert out["t3_streak_15"][t] == 0.0


def test_threshold_is_trailing_only():
    """A higher trailing ATR at t must disqualify an otherwise identical run."""
    forward = [100.0, 101.0, 102.0, 103.0, 103.0] + [103.0] * 10

    quiet = _run_series(forward)
    volatile = quiet.copy()
    # inflate only the trailing 20 rows (t <= 39): alternating +/- 5%
    volatile[20:40] = 100.0 * (1.0 + 0.05 * np.array([(-1.0) ** i for i in range(20)]))

    out_q = compute_run_targets(_frame(quiet))
    out_v = compute_run_targets(_frame(volatile))
    assert out_q["t4_freq_15"][40] == 1.0
    assert out_v["t4_freq_15"][40] == 0.0
    assert out_v["t1_amp_15"][40] == 0.0
    # T3 is threshold-free, so the forward path still registers the same streak
    assert out_v["t3_streak_15"][40] == out_q["t3_streak_15"][40] == 3.0


def test_labels_ignore_data_after_t_plus_k():
    walk = [100.0, 98.0, 96.0, 99.0, 102.0, 104.0, 106.0, 104.0, 100.0, 99.0, 97.0, 100.0, 101.0, 102.0, 103.0]
    base = compute_run_targets(_frame(_run_series(walk + [103.0] * 10)))
    # Append 10 wild rows strictly after the longest window (t=40 + k=20 = 60).
    extended = compute_run_targets(_frame(_run_series(walk + [103.0] * 10 + [1000.0] * 10)))
    for k in DEFAULT_HORIZONS:
        for col in target_columns():
            if col.endswith(f"_{k}"):
                assert base[col][40] == pytest.approx(extended[col][40], nan_ok=True, rel=1e-6), col


def test_label_at_t_observes_t_plus_1():
    """Changing only row t+1 must change the label at t (no shift-1 misalignment)."""
    base = compute_run_targets(_frame(_run_series([100.0] + [103.0] * 14)))
    bumped = compute_run_targets(_frame(_run_series([99.0] + [103.0] * 14)))
    t = 40
    assert base["t4_freq_15"][t] == 1.0
    assert bumped["t4_freq_15"][t] == 1.0
    assert bumped["t1_amp_15"][t] > base["t1_amp_15"][t]


def test_atr_warmup_rows_are_nan_for_triggered_targets():
    out = compute_run_targets(_frame(_run_series([100.0] * 40)))
    # Wilder ATR(20) is undefined before row 19 -> no threshold -> NaN for T1/T2/T4
    assert out["t4_freq_15"][:19].isna().all()
    assert out["t1_amp_15"][:19].isna().all()
    assert np.isfinite(out["t3_streak_15"][:19]).all()
