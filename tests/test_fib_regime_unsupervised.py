"""WI-027b tests — synthetic data only (no data/, no reports/, no full-universe job).

Covers: GMM fit reproducibility (fixed seed), soft probabilities summing to 1.0 within the
float32 tolerance (1e-6), state-ordering stability across random_state values via Hungarian
matching on component means, and fold5 isolation VERDICT detection (PASS)."""
import os
import sys

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                'scripts'))
from fib_regime_unsupervised import (FEATURES, N_COMPS, fit_gmm, fold5_states, gmm_states,
                                     gmm_verdict, state_edge_table)


def synth_daily(n_calib=90, n_eval=20, seed=0):
    """Synthetic daily frame (market/date + FEATURES): 3 well-separated feature clusters
    cycling by row; n_calib CALIB dates (< 2022-05-02) then n_eval post-CALIB dates."""
    rng = np.random.RandomState(seed)
    centers = np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                        [4.0, 4.0, 1.0, 1.0, 1.0, 1.0],
                        [-4.0, -4.0, -1.0, -1.0, -1.0, -1.0]])
    dates = ([d.strftime('%Y-%m-%d') for d in pd.date_range('2021-01-04', periods=n_calib)]
             + [d.strftime('%Y-%m-%d') for d in pd.date_range('2022-06-01', periods=n_eval)])
    x = np.vstack([centers[i % 3] + 0.05 * rng.randn(6) for i in range(n_calib + n_eval)])
    df = pd.DataFrame(x, columns=FEATURES).astype('float32')
    df.insert(0, 'date', dates)
    df.insert(0, 'market', ['CAD'] * len(df))
    return df


def test_gmm_fit_reproducible():
    """Same seed + same data -> identical component means and predict_proba."""
    rng = np.random.RandomState(42)
    x = rng.randn(60, 3)
    a, b = fit_gmm(x, 3), fit_gmm(x, 3)
    assert a.means_.shape == (3, 3) and b.means_.shape == (3, 3)
    assert np.array_equal(a.means_, b.means_)
    assert np.array_equal(a.predict_proba(x), b.predict_proba(x))


def test_soft_probs_sum_to_one():
    """predict_proba rows sum to 1.0 within the float32 tolerance (1e-6)."""
    rng = np.random.RandomState(0)
    x = rng.randn(40, 2)
    assert np.allclose(fit_gmm(x, 3).predict_proba(x).sum(axis=1), 1.0, atol=1e-6)
    d = gmm_states(synth_daily())
    for k in N_COMPS:
        cols = ['gmm%d_s%d_prob' % (k, j) for j in range(k)]
        assert d[cols].dtypes.eq('float32').all()
        p = d[cols].to_numpy('float32')
        assert np.allclose(p.sum(axis=1), 1.0, atol=1e-6)
        assert set(d['gmm%d_label' % k].dropna().astype(int)) <= set(range(k))


def test_state_ordering_stable():
    """Different random_state values: component order may permute, but Hungarian matching
    on the component means recovers the same cluster assignments for every element."""
    rng = np.random.RandomState(7)
    centers = np.array([[0.0, 0.0], [8.0, 0.0], [0.0, 8.0]])
    x = np.vstack([c + 0.3 * rng.randn(30, 2) for c in centers])
    m0, m1 = fit_gmm(x, 3, random_state=0), fit_gmm(x, 3, random_state=1)
    cost = np.linalg.norm(m0.means_[:, None] - m1.means_[None], axis=2)
    rows, cols = linear_sum_assignment(cost)                 # Hungarian match on the means
    mapping = {int(j): int(i) for i, j in zip(rows, cols)}   # m1 component -> m0 component
    l0, l1 = m0.predict(x), m1.predict(x)
    assert (np.array([mapping[int(v)] for v in l1]) == l0).mean() >= 0.98
    assert np.allclose(m0.means_[rows], m1.means_[cols], atol=0.1)


def test_fold5_isolation_pass():
    """Synthetic daily frame where fold5 bottoms concentrate in one failing GMM state while
    another state is fold-stable -> VERDICT detection returns PASS."""
    n_a, n_b = 80, 20                                    # stable state | failing fold5 state
    dates = [d.strftime('%Y-%m-%d') for d in pd.date_range('2010-01-04', periods=n_a + n_b)]
    daily = pd.DataFrame({'market': ['CAD'] * (n_a + n_b), 'date': dates,
                          'gmm3_label': [0] * n_a + [1] * n_b})
    ev = pd.DataFrame({'type': ['bottom'] * (n_a + n_b), 'market': ['CAD'] * (n_a + n_b),
                       'date': dates, 'screen_bottom': [True] * (n_a + n_b),
                       'fwd_mfe_pct': [20.0] * (n_a + n_b),
                       'fwd_ret_pct': [0.02] * n_a + [-0.05] * n_b,
                       'grade': ['med'] * (n_a + n_b)})
    edge = state_edge_table(ev, daily, 'gmm3_label', ['s0', 's1', 's2'])
    pooled = edge[edge['market'] == 'ALL'].set_index('state')
    assert pooled.loc['s0', 'n_folds_pos'] == 5           # fold-stable: all 5 folds positive
    assert pooled.loc['s1', 'n_folds_pos'] == 0          # the failing state
    d0, d1, f5c = fold5_states(ev, daily, 'gmm3_label')
    assert f5c == {'s1': n_b}                             # fold5 isolated in the failing state
    assert gmm_verdict([edge], [f5c]) == 'PASS'
