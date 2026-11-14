"""WI-028 tests — synthetic data only (no data/ or reports/ reads)."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 '..', 'scripts'))
import fib_entry_window as few  # noqa: E402

COST = 0.0025


def _flat(n=40, base=100.0):
    """40 synthetic bars: flat o/h/l/c around base."""
    o = np.full(n, base)
    h = np.full(n, base + 1.0)
    l = np.full(n, base - 1.0)
    c = np.full(n, base)
    return o, h, l, c


def test_at_bottom_entry():
    o, h, l, c = _flat()
    i = 5
    entry = c[i]                       # 100
    # target 10% -> T = 110; stop 5% -> S = 95; hit on bar 12
    h[12] = 111.0
    ret, reason, days = few.simulate_at(o, h, l, c, i, 0, 0.10, 0.05, 20,
                                        np.zeros(40))
    assert ret == pytest.approx(110.0 / entry - 1 - COST, abs=1e-9)
    assert reason == 'target'
    assert days == 7


def test_delayed_confirmed_entry():
    o, h, l, c = _flat()
    i = 5
    l[i] = 90.0                        # the event low
    o[i] = h[i] = 95.0
    c[i] = 95.0
    # lows hold through [i+1..i+3] -> confirmed k=3, entry = close[8] = 100
    for j in (6, 7, 8):
        l[j] = 90.0 + (j - i)          # 91, 92, 93 — all > 90
    entry = c[8]                       # 100
    # stop 5% -> S = 95; stop hit on bar 15
    l[15] = 94.0
    ret, reason, days = few.simulate_at(o, h, l, c, i, 3, 0.10, 0.05, 20,
                                        np.zeros(40))
    assert ret == pytest.approx(95.0 / entry - 1 - COST, abs=1e-9)
    assert reason == 'stop'
    assert days == 15 - 8


def test_no_confirmation_skips():
    o, h, l, c = _flat()
    i = 5
    l[i] = 96.0                        # event low (above k=0 stop of 95)
    o[i] = h[i] = 97.0
    c[i] = 100.0
    # low breaks on day 2 of the window (bar 7 dips below the event low,
    # but stays above the k=0 stop of 95)
    l[7] = 95.5
    # k=3: no confirmation -> no trade (NaN ret)
    ret_k3, reason_k3, _ = few.simulate_at(o, h, l, c, i, 3, 0.10, 0.05, 20,
                                           np.zeros(40))
    assert np.isnan(ret_k3)
    assert reason_k3 == 'unresolved'
    # k=0: still produces a trade (target hit on bar 12)
    h[12] = 111.0
    ret_k0, reason_k0, _ = few.simulate_at(o, h, l, c, i, 0, 0.10, 0.05, 20,
                                           np.zeros(40))
    assert not np.isnan(ret_k0)
    assert reason_k0 == 'target'


def test_ensemble_mean():
    lab = {'symbol': ['X'] * 4, 'market': ['CAD'] * 4,
           'date': ['2021-01-04'] * 4,
           'policy': ['p1', 'p2', 'p3', 'p4'],
           'ret': np.array([0.01, -0.02, 0.03, 0.06], dtype='float32')}
    df = __import__('pandas').DataFrame(lab)
    ens = few.ensemble_mean(df)
    assert len(ens) == 1
    expected = np.mean(np.array([0.01, -0.02, 0.03, 0.06],
                                 dtype='float32'))
    assert float(ens.iloc[0]['ret']) == pytest.approx(expected,
                                                      rel=1e-6)