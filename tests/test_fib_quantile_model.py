"""WI-025 tests (synthetic only)."""
import importlib.util
import os

import numpy as np
import pandas as pd
import pytest

SPEC = importlib.util.spec_from_file_location(
    'fib_quantile_model',
    os.path.join(os.path.dirname(__file__), '..', 'scripts',
                 'fib_quantile_model.py'))
fq = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fq)


def test_pinball_hand_calc():
    # alpha=0.5, y=[1,3], pred=[2,2]: |d| mean = (1+1)/2 = 0.5
    assert fq.pinball_loss([1.0, 3.0], [2.0, 2.0], 0.5) == pytest.approx(0.5)
    # alpha=0.1, y=2, pred=1: max(0.1*1, -0.9*1)=0.1
    assert fq.pinball_loss([2.0], [1.0], 0.1) == pytest.approx(0.1)
    # alpha=0.9, y=1, pred=2: max(0.9*(-1), -0.1*(-1)) = -0.1 -> 0.1? no: max(-0.9, 0.1)=0.1
    assert fq.pinball_loss([1.0], [2.0], 0.9) == pytest.approx(0.1)
    # asymmetric check alpha=0.1, y=1, pred=2: max(0.1*(-1), -0.9*(-1))=0.9
    assert fq.pinball_loss([1.0], [2.0], 0.1) == pytest.approx(0.9)


def test_sort_removes_crossing():
    pred = np.array([[5.0, 1.0, 3.0], [9.0, 0.0, 4.0]])
    s = fq.sort_quantiles(pred)
    assert (np.diff(s, axis=1) >= 0).all()
    assert s[0].tolist() == [1.0, 3.0, 5.0]
    assert s[1].tolist() == [0.0, 4.0, 9.0]


def test_baseline_global_fallback():
    rng = np.random.default_rng(0)
    n_big, n_small = 30, 5
    sym = ['AAA'] * n_big + ['BBB'] * n_small
    val = list(rng.normal(10, 2, n_big)) + list(rng.normal(50, 2, n_small))
    df = pd.DataFrame({'symbol': sym, 'v': val})
    q = fq.empirical_quantiles(df, 'v')
    # AAA (30 events >= 20): its own quantiles
    a = np.percentile(val[:n_big], [10, 50, 90])
    assert np.allclose(q['AAA'], a, atol=1e-9)
    # BBB (5 events < 20): global CALIB quantiles
    g = np.percentile(val, [10, 50, 90])
    assert np.allclose(q['BBB'], g, atol=1e-9)
    assert not np.allclose(q['BBB'], np.percentile(val[n_big:], [10, 50, 90]),
                           atol=1e-9)