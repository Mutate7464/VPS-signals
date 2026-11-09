"""WI-032 — swing-event sampling + first-touch label tests.

Verify: `uv run pytest tests/swing_bsh/test_probe.py -q`
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.swing_bsh.events import (
    BUY,
    HOLD,
    SELL,
    detect_swings,
    first_touch_label,
    sample_events,
)
from src.swing_bsh.probe import favorable_outcome
from src.targets import wilder_atr


def _flat(n: int = 160) -> pd.DataFrame:
    """Flat series (high 101 / low 99 / close 100) → wilder_atr = 2.0 from index 19."""
    return pd.DataFrame(
        {
            "date": pd.date_range("2016-01-04", periods=n, freq="B"),
            "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1000.0,
        }
    )


# --------------------------------------------------------------------------- #
# First-touch label geometry
# --------------------------------------------------------------------------- #
def test_bottom_profit_touch_first_is_buy():
    df, t = _flat(), 60
    df.loc[t, "low"] = 96.0
    atr = wilder_atr(df).to_numpy()
    df.loc[t + 1, "high"] = df.at[t, "close"] + 1.5 * atr[t] + 1.0
    assert first_touch_label(df, t, "at_bottom", 1.5, 21) == (BUY, 1)


def test_bottom_stop_touch_first_is_sell():
    df, t = _flat(), 60
    df.loc[t, "low"] = 96.0
    atr = wilder_atr(df).to_numpy()
    df.loc[t + 1, "low"] = df.at[t, "close"] - 1.5 * atr[t] - 1.0
    assert first_touch_label(df, t, "at_bottom", 1.5, 21) == (SELL, 1)


def test_top_downside_first_is_sell():
    df, t = _flat(), 60
    df.loc[t, "high"] = 106.0
    atr = wilder_atr(df).to_numpy()
    df.loc[t + 1, "low"] = df.at[t, "close"] - 1.5 * atr[t] - 1.0
    assert first_touch_label(df, t, "at_top", 1.5, 21) == (SELL, 1)


def test_top_upside_first_is_buy():
    df, t = _flat(), 60
    df.loc[t, "high"] = 106.0
    atr = wilder_atr(df).to_numpy()
    df.loc[t + 1, "high"] = df.at[t, "close"] + 1.5 * atr[t] + 1.0
    assert first_touch_label(df, t, "at_top", 1.5, 21) == (BUY, 1)


def test_vertical_touch_is_hold():
    df, t = _flat(), 60
    df.loc[t, "low"] = 96.0  # flat forward path stays inside both barriers
    assert first_touch_label(df, t, "at_bottom", 1.5, 21)[0] == HOLD


def test_undefined_event_is_negative():
    df = _flat(n=40)
    assert first_touch_label(df, 39, "at_bottom", 1.5, 21) == (-1, -1)


# --------------------------------------------------------------------------- #
# Detection + sampling
# --------------------------------------------------------------------------- #
def test_detect_swings_finds_hand_built_extremes():
    n = 120
    low = np.linspace(100.0, 120.0, n)
    low[60] = 90.0
    high = np.linspace(200.0, 180.0, n)
    high[40] = 250.0
    df = pd.DataFrame({"date": pd.date_range("2016-01-04", periods=n, freq="B"),
                       "open": 110.0, "high": high, "low": low, "close": 110.0, "volume": 1.0})
    assert detect_swings(df, window=21, gap=10) == [(40, "at_top"), (60, "at_bottom")]


def test_favorable_outcome_maps_implied_side():
    panel = pd.DataFrame({"state": ["at_bottom", "at_bottom", "at_bottom", "at_top", "at_top", "at_top"],
                          "y": [BUY, SELL, HOLD, SELL, BUY, HOLD]})
    out = favorable_outcome(panel)
    assert out[0] == 1.0 and out[1] == 0.0 and np.isnan(out[2])
    assert out[3] == 1.0 and out[4] == 0.0 and np.isnan(out[5])


def test_sample_events_empty_ticker_returns_empty_frame(monkeypatch):
    import src.swing_bsh.events as ev

    monkeypatch.setattr(ev, "iter_market_symbols", lambda *a, **k: iter(()))
    out = sample_events("USD", 1.5)
    assert out.empty
    assert list(out.columns) == ["symbol", "date", "state", "y", "horizon"]
