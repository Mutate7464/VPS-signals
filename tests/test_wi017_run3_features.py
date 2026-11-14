"""WI-017 run 3 feature-grid regression tests.

Locks: (1) hurst windows < 12 are all-NaN by the _hurst_rs_vec constructor
(WI-016's shipped hurst_9 shares this wart); (2) WI-017 columns reproduce
compute_features_wi016 exactly on shared family/window combinations.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.feature_engine import _hurst_rs_vec, compute_features_wi016
from src.wi017.run3_feature_grid import COLUMN_ORDER, features_for_symbol


def _toy(n: int = 320) -> pd.DataFrame:
    rng = np.random.default_rng(3)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.02, n)))
    high = close * (1 + np.abs(rng.normal(0, 0.005, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.005, n)))
    return pd.DataFrame(
        {"date": pd.date_range("2020-01-01", periods=n, freq="D"),
         "open": close, "high": high, "low": low, "close": close,
         "volume": np.abs(rng.normal(1e6, 1e5, n)), "average": close, "barCount": 100}
    )


def test_hurst_below_12_all_nan():
    x = _toy()["close"].to_numpy("float64")
    for w in (8, 9):
        assert np.isnan(_hurst_rs_vec(x, w)).all(), f"hurst_{w} must be all-NaN"
    assert np.isfinite(_hurst_rs_vec(x, 13)).any(), "hurst_13 must produce values"
    assert not any(c.startswith("hurst_") and int(c.split("_")[1]) < 12 for c in COLUMN_ORDER)


def test_grid_matches_wi016_on_shared_windows():
    df = _toy()
    wi016 = compute_features_wi016(df)
    mine = features_for_symbol(df)
    shared = [c for c in COLUMN_ORDER if c in wi016.columns]
    assert len(shared) > 50  # meaningful overlap
    bad = []
    for c in shared:
        a = wi016[c].to_numpy("float64")
        b = mine[c].to_numpy("float64")
        if not np.allclose(a, b, atol=1e-6, equal_nan=True):
            bad.append(c)
    assert not bad, bad


def test_point_in_time_all_float32():
    df = _toy(300)
    feats = features_for_symbol(df)
    for c in COLUMN_ORDER:
        assert feats[c].dtype == np.float32, c
    # trailing-only: row t must not change when future rows are perturbed
    f1 = features_for_symbol(df)
    df2 = df.copy()
    df2.loc[250:, ["high", "low", "close"]] *= 1.5
    f2 = features_for_symbol(df2)
    for c in ("adx_13", "range_pos_21", "kama_er_34", "bb_width_55", "entropy_13"):
        a = f1[c].to_numpy("float64")[:200]
        b = f2[c].to_numpy("float64")[:200]
        assert np.allclose(a, b, atol=1e-6, equal_nan=True), c
