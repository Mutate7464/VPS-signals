"""WI-052 — L0-1 swing-structure history feature block (D-026 sprint).

Synthetic only: no reads under `data/` or `reports/`. Verify:
`uv run pytest tests/test_l0_swing_structure.py -q`
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.swing_bsh import binary_features_ext as bei

NEW_COLUMNS = ("swing_leg_len_1", "swing_leg_dur_1", "swing_leg_len_3",
               "swing_leg_dur_3", "swing_depth_atr_prev")
SWINGS = [(2, "at_bottom"), (5, "at_top"), (9, "at_bottom"), (12, "at_top")]


def _series(n: int = 20):
    """Flat frame, then pinned swing extremes: 10, 20, 12, 24 (ATR = 2)."""
    high = np.full(n, 15.0)
    low = np.full(n, 11.0)
    close = np.full(n, 14.0)
    low[2], high[5], low[9], high[12] = 10.0, 20.0, 12.0, 24.0
    close[9] = 13.0
    return high, low, close, np.full(n, 2.0)


def _swing_structure(idx, swings=SWINGS, **kw):
    high, low, close, atr = _series()
    return bei._swing_structure(high, low, close, atr,
                                np.asarray(idx, dtype=np.int64), swings, **kw)


# --------------------------------------------------------------------------- #
# Known geometry from the synthetic swings
# --------------------------------------------------------------------------- #
def test_known_leg_geometry():
    row = _swing_structure([12]).iloc[0]
    assert row["swing_leg_len_1"] == np.float32(6.0)   # |24 - 12| / 2
    assert row["swing_leg_dur_1"] == np.float32(3.0)   # bars 12 - 9
    assert row["swing_leg_len_3"] == np.float32(5.0)   # |20 - 10| / 2
    assert row["swing_leg_dur_3"] == np.float32(3.0)   # bars 5 - 2
    assert row["swing_depth_atr_prev"] == np.float32(1.0)  # |close[12]=14 - 12| / 2


def test_detection_swing_is_rank_one_and_prev_is_the_prior_swing():
    row = _swing_structure([9]).iloc[0]
    assert row["swing_leg_len_1"] == np.float32(4.0)       # |12 - 20| / 2
    assert row["swing_leg_dur_1"] == np.float32(4.0)       # bars 9 - 5
    assert row["swing_depth_atr_prev"] == np.float32(3.5)  # |13 - 20| / 2


def test_columns_are_float32_and_dimensionless_prefix_only():
    out = _swing_structure([9, 12])
    assert tuple(out.columns) == NEW_COLUMNS
    assert all(out[c].dtype == np.float32 for c in out.columns)
    assert all(c.startswith(("swing_", "volume_", "vwap_dist", "bar_count_", "bars_since_",
                             "dd_age", "dow", "month", "cs_", "sec_", "srel_", "breadth_"))
               for c in out.columns)


# --------------------------------------------------------------------------- #
# Warmup -> NaN, never a fabricated leg
# --------------------------------------------------------------------------- #
def test_nan_before_enough_history():
    out = _swing_structure([2, 9])
    assert np.isnan(out.iloc[1]["swing_leg_len_3"])       # only 3 swings at/before 9
    assert np.isnan(out.iloc[1]["swing_leg_dur_3"])
    assert np.isfinite(out.iloc[1]["swing_leg_len_1"])
    first = out.iloc[0]                                   # first swing: no prior at all
    assert first[["swing_leg_len_1", "swing_leg_dur_1", "swing_depth_atr_prev"]].isna().all()


# --------------------------------------------------------------------------- #
# Causal: bars strictly after the detection bar are never read
# --------------------------------------------------------------------------- #
def test_future_bars_do_not_change_the_row():
    high, low, close, atr = _series()
    base = bei._swing_structure(high, low, close, atr, np.array([12]), SWINGS).iloc[0]
    loud_h, loud_l, loud_c = high.copy(), low.copy(), close.copy()
    loud_h[13:], loud_l[13:], loud_c[13:] = 999.0, -999.0, 999.0
    after = bei._swing_structure(loud_h, loud_l, loud_c, atr, np.array([12]), SWINGS).iloc[0]
    pd.testing.assert_series_equal(base, after)


# --------------------------------------------------------------------------- #
# Wiring: the block lands in the panel and in candidate_features
# --------------------------------------------------------------------------- #
def _ohlcv(n: int = 400, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    return pd.DataFrame({
        "date": pd.date_range("2015-01-01", periods=n, freq="B"),
        "open": close * (1 + rng.normal(0, 0.002, n)),
        "high": close * (1 + np.abs(rng.normal(0, 0.005, n))),
        "low": close * (1 - np.abs(rng.normal(0, 0.005, n))),
        "close": close,
        "volume": rng.integers(1_000, 10_000, n).astype("float64"),
    })


def test_block_wired_into_panel_and_candidate_features(monkeypatch):
    g = _ohlcv()
    monkeypatch.setattr(bei, "iter_market_symbols", lambda *a, **k: iter([("SYN", g)]))
    panel, _labels = bei.build_variant_panel("USD", max_symbols=1, with_sector=False)
    assert not panel.empty
    for col in NEW_COLUMNS:
        assert col in panel.columns and panel[col].dtype == np.float32
    assert set(NEW_COLUMNS) <= set(bei.candidate_features(panel))
