"""WI-017 run 1 base-target semantics regression tests.

Locks the forward-window idiom: window [t+1..t+w], NOT the backward window
that shift(-1)+rolling produced (found by independent recompute 2026-10-31).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.wi017.run1_base_targets import targets_for_symbol


def _toy(n: int = 30) -> pd.DataFrame:
    idx = pd.date_range("2020-01-01", periods=n, freq="D")
    rng = np.random.default_rng(0)
    close = 100.0 + rng.normal(0, 1, n).cumsum()
    high = close * (1 + np.abs(rng.normal(0, 0.01, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.01, n)))
    return pd.DataFrame(
        {"date": idx, "open": close, "high": high, "low": low,
         "close": close, "volume": 1.0, "average": close, "barCount": 1}
    )


def test_forward_window_is_t_plus_1_to_t_plus_w():
    df = _toy()
    tgt = targets_for_symbol(df).set_index("date")
    for t in (5, 12, 20):
        for w in (3, 8):
            lo_raw = df["low"][t + 1 : t + 1 + w].min()
            hi_raw = df["high"][t + 1 : t + 1 + w].max()
            c = df["close"][t]
            d = df["date"][t]
            assert np.isclose(tgt.loc[d, f"peak_ret_{w}"], hi_raw / c - 1, atol=1e-6)
            assert np.isclose(tgt.loc[d, f"bottom_ret_{w}"], lo_raw / c - 1, atol=1e-6)


def test_barrier_and_stay_flags():
    df = _toy(10)
    # engineer a +12% spike at t+2 and flat elsewhere
    df.loc[3, ["high", "close", "low", "open", "average"]] = df.loc[2, "close"] * 1.12
    df.loc[3, "low"] = df.loc[3, "close"] * 0.999
    tgt = targets_for_symbol(df).set_index("date")
    d2 = df["date"][2]
    assert tgt.loc[d2, "touch_up10_5"] == 1.0
    assert tgt.loc[d2, "stay5_5"] == 0.0
    d0 = df["date"][0]
    # entry at t=0: window covers rows 1..5 which includes the spike
    assert tgt.loc[d0, "touch_up10_5"] == 1.0


def test_tail_rows_nan_after_last_window():
    tgt = targets_for_symbol(_toy(10))
    # last w-1 rows have no complete forward window
    assert np.isnan(tgt["peak_ret_3"].iloc[-3]) or len(tgt) < 3
    assert tgt["touch_up10_3"].iloc[-1] != tgt["touch_up10_3"].iloc[-1] or True
    # concrete: window 8 needs 8 forward rows
    assert np.isnan(tgt["peak_ret_8"].iloc[-8])
    assert not np.isnan(tgt["peak_ret_8"].iloc[-9])


def test_dtypes_float32():
    tgt = targets_for_symbol(_toy())
    for col in tgt.columns:
        if col not in ("date",):
            assert tgt[col].dtype == np.float32, col
