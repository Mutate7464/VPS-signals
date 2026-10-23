"""Tests: Fibonacci-window range features are XGBoost-compliant (WI-002 E3)."""
import numpy as np
import pandas as pd
import pytest

from src.feature_engine import FIB_WINDOWS, _range_fib_features, compute_features


@pytest.fixture()
def ohlcv() -> pd.DataFrame:
    rng = np.random.default_rng(3)
    n = 260
    close = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.02, n)))
    spread = np.abs(rng.normal(0, 0.01, n)) + 0.005
    df = pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=n, freq="B"),
            "open": close * (1 + rng.normal(0, 0.003, n)),
            "high": close * (1 + spread),
            "low": close * (1 - spread),
            "close": close,
            "volume": rng.integers(1e5, 1e7, n).astype("float64"),
        }
    )
    return df


def test_feature_count_and_names(ohlcv):
    feats = _range_fib_features(ohlcv, ohlcv["close"])
    expected = []
    for w in FIB_WINDOWS:
        expected += [f"range_pos_f{w}", f"range_width_f{w}"]
        if w in (6, 15):
            expected.append(f"donchian_break_f{w}")
    expected += [
        "range_compression_f6_39",
        "range_compression_f15_102",
        "pct_from_high_f102",
        "pct_from_low_f102",
        "fib_dist_f15",
        "fib_dist_f39",
        "fib_dist_f102",
        "gap_z",
    ]
    assert list(feats.columns) == expected
    assert len(expected) == 26


def test_all_float32_no_inf_nan_bounded(ohlcv):
    feats = _range_fib_features(ohlcv, ohlcv["close"])
    for c in feats.columns:
        col = feats[c]
        assert col.dtype == np.float32, c
        arr = col.to_numpy()
        assert np.isinf(arr).sum() == 0, c
        finite = arr[np.isfinite(arr)]
        assert np.isfinite(finite).all()
    # NaN confined to warmup: no NaN after bar `window` for any feature
    for c in feats.columns:
        tail = feats[c].to_numpy()[102:]  # largest fib window
        assert np.isfinite(tail).all(), c
    # ranges
    for w in FIB_WINDOWS:
        pos = feats[f"range_pos_f{w}"].to_numpy()
        assert np.nanmin(pos) >= 0.0 and np.nanmax(pos) <= 1.0
        assert (feats[f"range_width_f{w}"].to_numpy()[np.isfinite(feats[f"range_width_f{w}"].to_numpy())] > 0).all()
        assert set(np.unique(feats[f"donchian_break_f{w}"].dropna().to_numpy())) <= {0.0, 1.0} if w in (6, 15) else True
    for w in (15, 39, 102):
        d = feats[f"fib_dist_f{w}"].to_numpy()
        assert np.nanmax(np.abs(d)) <= 0.5 + 1e-6
    assert (feats["pct_from_high_f102"].to_numpy()[np.isfinite(feats["pct_from_high_f102"].to_numpy())] <= 0).all()
    assert (feats["pct_from_low_f102"].to_numpy()[np.isfinite(feats["pct_from_low_f102"].to_numpy())] >= 0).all()


def test_compute_features_total_count(ohlcv):
    df = ohlcv.copy()
    df.index = range(len(df))
    feats = compute_features(df)
    feature_cols = [c for c in feats.columns if c != "date"]
    assert len(feature_cols) == 89
    assert all(feats[c].dtype == np.float32 for c in feature_cols)


def test_no_lookahead_in_fib_features(ohlcv):
    """Truncating the future must not change past feature values."""
    full = _range_fib_features(ohlcv, ohlcv["close"])
    trunc = _range_fib_features(ohlcv.iloc[:200], ohlcv["close"].iloc[:200])
    for c in full.columns:
        a = full[c].to_numpy()[:150]
        b = trunc[c].to_numpy()[:150]
        mask = np.isfinite(a) & np.isfinite(b)
        assert np.array_equal(a[mask], b[mask]), c
