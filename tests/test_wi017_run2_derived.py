"""WI-017 run 2 derived-target semantics regression tests.

Locks: forward window [t+1..t+w], first-touch ordering, velocity sign/denominator.
Windows used must exist in WI017_WINDOWS (13, 34).
"""
from __future__ import annotations

import numpy as np

from src.wi017.run2_derived_targets import derived_for_symbol


def test_up_first_beats_dn():
    close = np.full(40, 100.0)
    high, low = close.copy(), close.copy()
    # entry t=0, window w=13: +10% touch on day 3, -10% touch on day 7
    high[3] = 111.0
    low[7] = 89.0
    res = derived_for_symbol(high, low, close)
    assert res.loc[0, "first_touch_13"] == 1.0
    assert res.loc[0, "days_to_up_13"] == 3.0
    assert res.loc[0, "days_to_dn_13"] == 7.0


def test_dn_first_beats_up():
    close = np.full(40, 100.0)
    high, low = close.copy(), close.copy()
    high[12] = 110.5  # up touch on last day of window
    low[2] = 88.0  # dn touch earlier
    res = derived_for_symbol(high, low, close)
    assert res.loc[0, "first_touch_13"] == -1.0


def test_neither_and_nan_tail():
    close = np.full(40, 100.0)
    high, low = close.copy(), close.copy()
    res = derived_for_symbol(high, low, close)
    assert res.loc[0, "first_touch_13"] == 0.0
    assert np.isnan(res.loc[0, "days_to_up_13"])
    # no complete window for the last 13 entries
    assert np.isnan(res.loc[30, "first_touch_13"])
    assert not np.isnan(res.loc[26, "first_touch_13"])


def test_velocity_sign_and_denominator():
    close = np.full(60, 100.0)
    high, low = close.copy(), close.copy()
    # bottom on day 2, peak on day 8 -> positive (bottom-to-peak), rung/delta=6
    low[2] = 92.0
    high[8] = 107.0
    res = derived_for_symbol(high, low, close)
    assert np.isclose(res.loc[0, "velocity_13"], (107.0 - 92.0) / 100.0 / 6.0, atol=1e-6)
    assert res.loc[0, "rung_13"] > 0
    # peak BEFORE bottom -> negative velocity (fresh arrays)
    high2, low2 = close.copy(), close.copy()
    high2[2] = 107.0
    low2[8] = 92.0
    res2 = derived_for_symbol(high2, low2, close)
    assert np.isclose(res2.loc[0, "velocity_13"], -(107.0 - 92.0) / 100.0 / 6.0, atol=1e-6)
    # peak and bottom same bar -> denominator floors at 1
    high3, low3 = close.copy(), close.copy()
    high3[4] = 107.0
    low3[4] = 92.0
    res3 = derived_for_symbol(high3, low3, close)
    assert np.isclose(res3.loc[0, "velocity_13"], -(107.0 - 92.0) / 100.0, atol=1e-6)


def test_window_excludes_entry_day():
    close = np.full(40, 100.0)
    high, low = close.copy(), close.copy()
    high[0] = 115.0  # spike ON entry day must NOT count as up-touch
    low[0] = 80.0
    res = derived_for_symbol(high, low, close)
    assert res.loc[0, "first_touch_13"] == 0.0
    assert np.isnan(res.loc[0, "days_to_up_13"])
    assert res.loc[1, "first_touch_13"] == 0.0
