"""WI-016 step 3 — unified fib feature grid + admission tests.

Verify: `uv run pytest tests/test_wi016_features.py`
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.feature_engine import (
    WI016_FAST_FIB_MIN8_WINDOWS,
    WI016_FAST_FIB_WINDOWS,
    WI016_SMOOTH_WINDOWS,
    compute_features_wi016,
    wi016_family_windows,
    wi016_feature_names,
)
from src.wi016.admission import (
    admit_features,
    cluster_features,
    load_wi016_config,
    min_events_ok,
    same_sign_ic,
    select_representatives,
)


def _ohlcv(n: int = 300, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    high = close * (1 + np.abs(rng.normal(0, 0.005, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.005, n)))
    open_ = close * (1 + rng.normal(0, 0.002, n))
    return pd.DataFrame(
        {
            "date": pd.date_range("2015-01-01", periods=n, freq="B"),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": rng.integers(1_000, 10_000, n).astype("float64"),
        }
    )


# --------------------------------------------------------------------------- #
# Exact family grids
# --------------------------------------------------------------------------- #
def test_family_grids_are_exact():
    reg = wi016_family_windows()
    smooth = set(WI016_SMOOTH_WINDOWS)
    for fam in (
        "adx", "di_spread", "atr_pct", "bb_pct_b", "bb_width", "obv_zscore",
        "amihud", "yangzhang", "range_pos", "range_width", "donchian_break", "fib_dist",
    ):
        assert set(reg[fam]) == smooth, f"{fam} not on the smooth ladder"

    assert set(reg["kama_er"]) == set(WI016_FAST_FIB_WINDOWS)
    assert set(reg["vwap_zscore"]) == set(WI016_FAST_FIB_WINDOWS)
    # hurst/entropy need >= 8-bar windows.
    for fam in ("hurst", "entropy"):
        assert set(reg[fam]) == set(WI016_FAST_FIB_MIN8_WINDOWS)
        assert min(reg[fam]) >= 8


def test_no_duplicate_window_variants():
    names = wi016_feature_names()
    assert len(names) == len(set(names)), "duplicate column names in the grid"
    # The old classic / fib-scaled / WI-015 ladders must not leak in.
    forbidden_windows = {5, 10, 20, 50, 100, 6, 15, 24, 39, 63, 102, 13, 34}
    smooth_names = [
        n for n in names
        if n.rsplit("_", 1)[0] in set(wi016_family_windows()) and n != "range_pos"
    ]
    for n in smooth_names:
        fam, w = n.rsplit("_", 1)
        if fam in ("adx", "di_spread", "atr_pct", "bb_pct_b", "bb_width", "obv_zscore",
                   "amihud", "yangzhang", "range_pos", "range_width", "donchian_break", "fib_dist"):
            assert int(w) not in forbidden_windows, f"{n} uses a non-smooth window"
    # No `_f`-suffixed fib aliases.
    assert not any(n.endswith(("_f6", "_f15", "_f39", "_f102", "range_pos_f")) for n in names)


def test_grid_matches_computed_columns_and_dtypes():
    feats = compute_features_wi016(_ohlcv())
    cols = set(feats.columns) - {"date"}
    assert cols == set(wi016_feature_names())
    for c in cols:
        assert feats[c].dtype == np.float32, f"{c} is {feats[c].dtype}"


# --------------------------------------------------------------------------- #
# Config: VIF 8.0, relaxed MI, cluster rho, event floor
# --------------------------------------------------------------------------- #
def test_wi016_config_values():
    cfg = load_wi016_config()
    assert cfg["vif_threshold"] == 8.0
    assert cfg["cluster_rho"] == 0.7
    assert cfg["min_labeled_events"] == 500
    assert cfg["smooth_windows"] == list(WI016_SMOOTH_WINDOWS)
    assert cfg["fast_fib_windows"] == list(WI016_FAST_FIB_WINDOWS)
    assert cfg["mi_min_percentile"] < 30  # relaxed vs the Sprint-3 value


# --------------------------------------------------------------------------- #
# Clustering + same-sign-IC representatives
# --------------------------------------------------------------------------- #
def test_cluster_features_groups_correlated_pair():
    corr = pd.DataFrame(
        [[1.0, 0.9, 0.1], [0.9, 1.0, 0.05], [0.1, 0.05, 1.0]],
        index=["f_a", "f_b", "f_c"],
        columns=["f_a", "f_b", "f_c"],
    )
    clusters = cluster_features(corr, rho=0.7)
    assert sorted(len(c) for c in clusters) == [1, 2]
    pair = next(c for c in clusters if len(c) == 2)
    assert pair == ["f_a", "f_b"]


def test_select_representatives_prefers_same_sign_highest_ic():
    clusters = [["f_a", "f_b"], ["f_c"]]
    ic_info = {
        "f_a": {"ic": 0.05, "same_sign": True},
        "f_b": {"ic": 0.10, "same_sign": True},
        "f_c": {"ic": -0.30, "same_sign": False},
    }
    assert select_representatives(clusters, ic_info) == ["f_b", "f_c"]


def test_select_representatives_prefers_same_sign_over_larger_unstable_ic():
    clusters = [["f_a", "f_b"]]
    ic_info = {
        "f_a": {"ic": 0.40, "same_sign": False},  # larger but not same-sign
        "f_b": {"ic": 0.05, "same_sign": True},
    }
    assert select_representatives(clusters, ic_info) == ["f_b"]


# --------------------------------------------------------------------------- #
# Event floor
# --------------------------------------------------------------------------- #
def test_min_events_floor():
    t = np.ones(600)
    assert min_events_ok(np.ones(600), t, 500) is True
    f = np.ones(600)
    f[:250] = np.nan  # 350 labeled events
    assert min_events_ok(f, t, 500) is False


# --------------------------------------------------------------------------- #
# Same-sign IC + end-to-end admission
# --------------------------------------------------------------------------- #
def _panel(n_dates: int = 20, per_date: int = 30, seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = np.repeat(pd.date_range("2020-01-01", periods=n_dates, freq="B"), per_date)
    f_a = rng.normal(0, 1, n_dates * per_date)
    f_b = f_a + rng.normal(0, 0.1, n_dates * per_date)   # > 0.7 correlated with f_a
    f_c = rng.normal(0, 1, n_dates * per_date)           # independent
    target = (0.6 * f_b + rng.normal(0, 1, n_dates * per_date) > 0).astype(float)
    return pd.DataFrame({"date": dates, "f_a": f_a, "f_b": f_b, "f_c": f_c, "target": target})


def test_same_sign_ic_flags_predictive_feature():
    panel = _panel()
    info = same_sign_ic(panel["f_b"].to_numpy(), panel["target"].to_numpy(), panel["date"].to_numpy())
    assert info["ic"] > 0
    assert info["same_sign"] is True
    assert len(info["window_ic"]) == 2


def test_admit_features_one_rep_per_cluster_and_event_floor():
    panel = _panel(n_dates=30, per_date=30)  # 900 rows
    feature_cols = ["f_a", "f_b", "f_c", "f_low"]
    panel["f_low"] = panel["f_c"].copy()
    panel.loc[panel.index[:400], "f_low"] = np.nan  # only 500 labeled events.. adjust below

    result = admit_features(
        panel, panel["target"].to_numpy(), feature_cols,
        dates=panel["date"].to_numpy(), rho=0.7, min_events=500,
    )
    # f_low has 500 events -> exactly at the floor is admitted; drop it harder:
    panel2 = panel.copy()
    panel2.loc[panel2.index[:450], "f_low"] = np.nan  # 450 events < 500
    result2 = admit_features(panel2, panel2["target"].to_numpy(), feature_cols,
                             dates=panel2["date"].to_numpy(), rho=0.7, min_events=500)

    assert "f_low" in result2["dropped_events"]
    assert "f_low" not in result2["admitted"]
    # Exactly one representative per cluster.
    assert len(result2["admitted"]) == len(result2["clusters"])
    for cluster in result2["clusters"]:
        assert sum(1 for m in cluster if m in result2["admitted"]) == 1
    # f_a/f_b are correlated -> one of them, not both.
    assert not ({"f_a", "f_b"} <= set(result2["admitted"]))
