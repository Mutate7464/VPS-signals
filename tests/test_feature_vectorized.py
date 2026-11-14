"""Tests: vectorized feature kernels equal the reference `.apply()` versions."""
import time

import numpy as np
import pandas as pd
import pytest

from src.feature_engine import (
    FRAC_DIFF_D,
    FRAC_DIFF_WINDOW,
    _frac_diff_fixed,
    _frac_diff_vec,
    _hurst_rs,
    _hurst_rs_vec,
    _shannon_entropy,
    _shannon_entropy_vec,
)


@pytest.fixture(scope="module")
def synthetic_close() -> np.ndarray:
    rng = np.random.default_rng(42)
    # log-normal random walk with regime shifts (so Hurst varies, not a pure trend)
    n = 600
    steps = rng.normal(0.0003, 0.02, n)
    steps[200:300] += 0.004  # trending regime
    steps[400:500] -= 0.003
    close = 100.0 * np.exp(np.cumsum(steps))
    return close


def test_hurst_vec_matches_reference(synthetic_close):
    w = 100
    ref = (
        pd.Series(synthetic_close)
        .rolling(w, min_periods=w)
        .apply(_hurst_rs, raw=True)
        .to_numpy()
    )
    vec = _hurst_rs_vec(synthetic_close, w)
    mask = np.isfinite(ref) & np.isfinite(vec)
    assert mask.sum() > 400
    corr = np.corrcoef(ref[mask], vec[mask])[0, 1]
    assert corr > 0.999
    assert np.nanmax(np.abs(ref[mask] - vec[mask])) < 1e-6
    # NaN pattern matches: NaN before warmup, finite after
    assert np.isnan(vec[: w - 1]).all()


def test_entropy_vec_matches_reference(synthetic_close):
    w = 20
    ref = (
        pd.Series(synthetic_close)
        .rolling(w, min_periods=w)
        .apply(_shannon_entropy, raw=True)
        .to_numpy()
    )
    vec = _shannon_entropy_vec(synthetic_close, w)
    mask = np.isfinite(ref) & np.isfinite(vec)
    assert mask.sum() > 550
    assert np.nanmax(np.abs(ref[mask] - vec[mask])) < 1e-6


def test_frac_diff_vec_matches_reference(synthetic_close):
    ref = (
        _frac_diff_fixed(pd.Series(np.log(synthetic_close)), FRAC_DIFF_D, FRAC_DIFF_WINDOW)
        .to_numpy()
    )
    vec = _frac_diff_vec(np.log(synthetic_close), FRAC_DIFF_D, FRAC_DIFF_WINDOW)
    mask = np.isfinite(ref) & np.isfinite(vec)
    assert mask.sum() > 490
    assert np.nanmax(np.abs(ref[mask] - vec[mask])) < 1e-6


def test_vectorized_speed():
    """10 tickers x ~5y of daily bars: all three kernels < 30 s total."""
    rng = np.random.default_rng(7)
    closes = [100.0 * np.exp(np.cumsum(rng.normal(0, 0.02, 1260))) for _ in range(10)]
    t0 = time.perf_counter()
    for c in closes:
        for w in (20, 50, 100):
            _hurst_rs_vec(c, w)
        _frac_diff_vec(np.log(c), FRAC_DIFF_D, FRAC_DIFF_WINDOW)
        for w in (10, 20):
            _shannon_entropy_vec(c, w)
    elapsed = time.perf_counter() - t0
    assert elapsed < 30.0, f"vectorized kernels took {elapsed:.1f}s for 10 tickers"
