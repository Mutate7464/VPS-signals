"""WI-050 — synthetic tests for the precision@k / top-decile diagnostic.

No market data, no training: separated scores, random labels, NaN and empty
paths only.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.swing_bsh.precision_diag import lift_at_k, precision_at_k, top_decile_calibration


def _separated(n: int = 1000, n_pos: int = 100) -> tuple[np.ndarray, np.ndarray]:
    """Exact probabilities: ``p == y`` (positives scored 1.0, rest 0.0)."""
    y = np.zeros(n, dtype="int8")
    y[-n_pos:] = 1
    return y, y.astype("float32")


def test_separated_precision_one_and_monotone_in_k():
    y, p = _separated()
    ks = (10, 25, 50, 100, 500)
    prec = precision_at_k(y, p, ks=ks)
    assert sorted(prec) == list(ks)
    assert prec[10] == 1.0 and prec[100] == 1.0
    assert prec[500] == pytest.approx(0.2)
    vals = [prec[k] for k in ks]
    assert all(a >= b for a, b in zip(vals, vals[1:])), vals
    assert lift_at_k(y, p, 100) == pytest.approx(10.0)


def test_ece_zero_on_exact_probabilities():
    y, p = _separated()
    out = top_decile_calibration(y, p, n_bins=10)
    assert out["ece"] == 0.0
    assert sum(b[4] for b in out["bins"]) == int(y.size)
    for lo, hi, mean_p, frac_pos, n in out["bins"]:
        assert 0.0 <= lo < hi <= 1.0 and n > 0
        assert frac_pos == pytest.approx(mean_p, abs=1e-12)


def test_random_labels_give_precision_near_base_rate():
    rng = np.random.default_rng(0)
    n, k = 20000, 500
    y = (rng.random(n) < 0.05).astype("int8")
    p = rng.random(n).astype("float32")
    base = float(y.mean())
    assert abs(base - 0.05) < 0.01
    assert precision_at_k(y, p, ks=(k,))[k] == pytest.approx(base, abs=0.03)
    assert lift_at_k(y, p, k) == pytest.approx(1.0, abs=0.6)


def test_nan_scores_are_dropped_before_ranking():
    y = np.array([1, 1, 0, 0, 0, 1, 0, 0, 1, 0], dtype="int8")
    p = np.array([0.9, 0.8, np.nan, 0.7, 0.6, 0.5, np.nan, 0.4, 0.3, 0.2], dtype="float32")
    keep = np.isfinite(p)
    assert precision_at_k(y, p, ks=(3,))[3] == pytest.approx(
        precision_at_k(y[keep], p[keep], ks=(3,))[3]
    )
    assert sum(b[4] for b in top_decile_calibration(y, p)["bins"]) == int(keep.sum())


def test_empty_and_all_nan_inputs():
    empty_i = np.array([], dtype="int8")
    empty_f = np.array([], dtype="float32")
    assert precision_at_k(empty_i, empty_f) == {}
    assert np.isnan(lift_at_k(empty_i, empty_f, 10))
    empty_out = top_decile_calibration(empty_i, empty_f)
    assert empty_out["bins"] == [] and np.isnan(empty_out["ece"])
    y = np.ones(5, dtype="int8")
    all_nan_p = np.full(5, np.nan, dtype="float32")
    assert precision_at_k(y, all_nan_p) == {}
    assert top_decile_calibration(y, all_nan_p)["bins"] == []


def test_length_mismatch_and_non_1d_raise():
    with pytest.raises(ValueError):
        precision_at_k(np.zeros(3, dtype="int8"), np.zeros(4, dtype="float32"))
    with pytest.raises(ValueError):
        precision_at_k(np.zeros((2, 2), dtype="int8"), np.zeros((2, 2), dtype="float32"))
