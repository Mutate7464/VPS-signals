"""WI-023 tests: simulate() first-touch exit semantics on synthetic 10-bar arrays.

Covered (per WI-023 blueprint): target-first; stop-first; open gap below stop ->
'stop_gap' at the open price; same bar touches both -> 'stop_tie'; neither ->
'time' at close; too few bars -> 'unresolved'; cost deducted exactly 0.0025.
Synthetic data only — no reads of data/ or reports/.
"""
import numpy as np
import pytest

from scripts.fib_trade_labels import simulate


def bars(o=100.0, h=104.0, l=96.0, c=100.0, n=10):
    """Flat 10-bar arrays; defaults never touch T=110 or S=95."""
    return (np.full(n, float(o)), np.full(n, float(h)),
            np.full(n, float(l)), np.full(n, float(c)))


def run(o, h, l, c, **over):
    """simulate() with the standard test policy: entry 100, tgt 10%, stop 95,
    max_days 5, close entry -> T=110, S=95."""
    kw = dict(i=0, entry=100.0, tgt_pct=0.10, stop_px=95.0, max_days=5,
              entry_mode='close')
    kw.update(over)
    return simulate(o, h, l, c, **kw)


def test_target_first():
    o, h, l, c = bars()
    h[1] = 112.0            # bar 1 touches target; stop would only come later
    l[2] = 90.0
    ret, reason, days = run(o, h, l, c)
    assert reason == 'target'
    assert ret == pytest.approx(110.0 / 100.0 - 1 - 0.0025)   # exit AT target
    assert days == 1


def test_stop_first():
    o, h, l, c = bars()
    l[2] = 93.0             # stop touched on bar 2; target would only come later
    h[3] = 120.0
    ret, reason, days = run(o, h, l, c)
    assert reason == 'stop'
    assert ret == pytest.approx(95.0 / 100.0 - 1 - 0.0025)
    assert days == 2


def test_open_gap_below_stop():
    o, h, l, c = bars()
    o[1] = 90.0             # opens below the stop
    ret, reason, days = run(o, h, l, c)
    assert reason == 'stop_gap'
    assert ret == pytest.approx(90.0 / 100.0 - 1 - 0.0025)    # exit at the open
    assert days == 1


def test_same_bar_touches_both_is_stop_tie():
    o, h, l, c = bars()
    l[1] = 93.0
    h[1] = 112.0
    ret, reason, days = run(o, h, l, c)
    assert reason == 'stop_tie'                             # conservative
    assert ret == pytest.approx(95.0 / 100.0 - 1 - 0.0025)  # exits at the stop
    assert days == 1


def test_neither_touched_time_exit_at_close():
    o, h, l, c = bars()
    c[5] = 102.0            # close of bar i+max_days
    ret, reason, days = run(o, h, l, c)
    assert reason == 'time'
    assert ret == pytest.approx(102.0 / 100.0 - 1 - 0.0025)
    assert days == 5


def test_too_few_bars_unresolved():
    o, h, l, c = bars()
    ret, reason, days = run(o, h, l, c, max_days=10)   # i+max_days == len(c)
    assert np.isnan(ret)
    assert reason == 'unresolved'
    assert days == 0
    ret, reason, days = run(o, h, l, c, max_days=9)     # one bar short still ok
    assert reason == 'time'
    assert days == 9


def test_cost_deducted_exactly():
    o, h, l, c = bars()
    c[5] = 100.0            # time exit at entry price -> net = -cost only
    ret, _, _ = run(o, h, l, c)
    assert ret == pytest.approx(-0.0025)
    o, h, l, c = bars()
    h[1] = 111.0            # target hit (exit AT T=110) -> net = raw - 0.0025
    ret, _, _ = run(o, h, l, c)
    assert ret == pytest.approx(0.10 - 0.0025)
