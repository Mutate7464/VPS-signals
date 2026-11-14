"""WI-036 — target-variant grid tests (D-022 §3c).

Synthetic only: no reads under `data/` or `reports/`. Verify:
`uv run pytest tests/test_swing_bsh_binary_grid.py -q`
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.swing_bsh import binary_features_ext as ext
from src.swing_bsh import binary_grid, binary_train
from src.swing_bsh.binary_labels import BINARY_COLUMNS, feature_names


# --------------------------------------------------------------------------- #
# Grid constants match the WI-036 spec
# --------------------------------------------------------------------------- #
def test_grid_constants_match_the_spec():
    assert binary_grid.LEARNERS == ("xgboost", "logistic_l2", "hist_gbm", "mlp_torch")
    assert binary_grid.TAU_P_GRID == (0.40, 0.50, 0.60, 0.70)
    assert binary_grid.TAU_S_GRID == (0.20, 0.30, 0.40, 0.50)
    assert binary_grid.PRUNE_RHO == 0.3
    assert binary_grid.N_PLACEBO_SEEDS == 5
    assert binary_grid.CORE_HOUR_CAP == 2.5
    assert ext.HORIZONS == (5, 8, 13, 21, 34, 55, 89, 144, 233)
    assert ext.K_GRID == (1.0, 0.8)
    assert ext.EVENT_MODES == ("exact", "tol2") and ext.WINDOW_MODES == ("full", "mid60")
    names = [v[0] for v in ext.variant_grid()]
    assert len(names) == 8 and len(set(names)) == 8
    assert {"exact_full_k1.0", "tol2_mid60_k0.8"} <= set(names)
    assert binary_grid.MODEL_DIR.name == "wi036" and "models" in binary_grid.MODEL_DIR.parts
    assert binary_grid.REPORT_NAME == "wi036_summary.md"


def test_core_budget_guard_and_bh_fdr_prefix():
    b = binary_grid.CoreBudget(0.0)
    assert b.exhausted() and b.left() <= 0.0
    p = [0.001, 0.02, 0.5, np.nan, 0.9, 0.0005]
    surv, _thr = binary_grid.bh_fdr(p, alpha=0.05)
    assert surv.tolist() == [True, True, False, False, False, True]
    assert not binary_grid.bh_fdr([0.5, 0.6, np.nan], alpha=0.05)[0].any()


# --------------------------------------------------------------------------- #
# Target variants = first-touch on the moved entry bar / window
# --------------------------------------------------------------------------- #
def _toy_series():
    close = np.full(10, 10.0)
    atr = np.ones(10)
    high = np.full(10, 10.5)
    low = np.full(10, 9.5)
    low[3] = 8.5      # shoulder extreme one bar after the detected bottom
    high[4] = 11.5    # profit touch only from bar 4 onwards
    return high, low, close, atr


def test_variant_labels_follow_the_moved_entry_bar_and_window():
    high, low, close, atr = _toy_series()
    lab = ext.first_touch_labels(high, low, close, atr, np.array([2]), np.array(["at_bottom"]),
                                 ext.variant_grid(), ext.HORIZONS)
    exact_full = lab[("exact_full_k1.0", 21)]
    # entry at the detected bar t=2: the bar-3 low (8.5) hits the stop first
    assert (exact_full["b_stop"][0], exact_full["b_profit"][0], exact_full["b_hold"][0]) == (1, 0, 0)
    # entry at the +/-2 shoulder extreme (bar 3): the bar-4 high (11.5) hits profit first
    tol2_full = lab[("tol2_full_k1.0", 21)]
    assert (tol2_full["b_profit"][0], tol2_full["b_stop"][0]) == (1, 0)
    # mid60 h=21 -> window [t+5, t+16]: no touch survives -> HOLD
    assert lab[("exact_mid60_k1.0", 21)]["b_hold"][0] == 1
    assert lab[("tol2_mid60_k0.8", 21)]["b_hold"][0] == 1
    # every (variant, horizon) cell yields a mutually exclusive decomposition
    for key, targets in lab.items():
        assert sum(int(targets[b][0]) for b in BINARY_COLUMNS) == 1, key


def test_feature_expansion_is_causal_and_leakage_free():
    n = 60
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"date": pd.date_range("2020-01-01", periods=n),
                       "open": rng.uniform(9, 11, n), "high": rng.uniform(10, 12, n),
                       "low": rng.uniform(8, 10, n), "close": rng.uniform(9, 11, n),
                       "volume": rng.uniform(1e5, 1e6, n), "average": rng.uniform(9, 11, n),
                       "barCount": rng.uniform(1e3, 1e4, n)})
    raw = ext._ext_raw_features(df)
    assert {"volume_z_21", "volume_z_55", "volume_trend_21", "vwap_dist",
            "bar_count_z_55", "bar_count_trend_21"} <= set(raw.columns)
    # trailing only: the first 20 rows cannot know a 21-bar rolling mean
    assert np.isnan(raw["volume_z_21"].iloc[19]) and np.isfinite(raw["volume_z_21"].iloc[20])
    banned = ["b_profit", "r_frozen", "fwd_ret_5"]
    names = ext.candidate_features(pd.DataFrame({c: [0.0] for c in banned}))
    assert not any(n.startswith(("b_", "r_", "fwd")) for n in names)
    assert feature_names(["mom_5"] + banned) == ["mom_5"]
    assert set(BINARY_COLUMNS).isdisjoint(names)


# --------------------------------------------------------------------------- #
# Driver calls the WI-035 pipeline functions (monkeypatched, synthetic)
# --------------------------------------------------------------------------- #
class _StubModel:
    method = "isotonic"
    best_iter = -1

    def predict_proba(self, X):
        return np.full(len(X), 0.5)

    def best_iteration(self):
        return -1


def _toy_panel(n=80):
    dates = pd.date_range("2016-01-04", periods=n, freq="B")
    rng = np.random.default_rng(1)
    panel = pd.DataFrame({
        "symbol": ["AAA"] * n, "date": dates,
        "state": ["at_bottom" if i % 2 else "at_top" for i in range(n)],
        "close": rng.uniform(9, 11, n).astype("float32"),
        "atr": np.full(n, 0.5, dtype="float32"),
        "adx_21": rng.uniform(0, 50, n).astype("float32"),
        "rsi_14": rng.uniform(0, 100, n).astype("float32"),
    })
    keys = [(name, h) for name, _, _, _ in ext.variant_grid() for h in ext.HORIZONS]
    labels = {}
    for key in keys:
        y = (rng.random(n) > 0.5).astype("int8")
        labels[key] = {b: y.copy() for b in BINARY_COLUMNS}
    return panel, labels


def test_run_market_scores_every_cell_and_pickles_fold_models(tmp_path, monkeypatch):
    panel, labels = _toy_panel()
    monkeypatch.setattr(ext, "build_variant_panel", lambda *a, **k: (panel, labels))
    monkeypatch.setattr(binary_grid, "fit_learner", lambda *a, **k: _StubModel())
    monkeypatch.setattr(binary_grid, "placebo_auc",
                        lambda *a, **k: {"z": 1.0, "p": 0.1, "n_seeds": 5})
    cfg = {"modeling": {"xgb_params": {"n_estimators": 5}}}
    res = binary_grid.run_market("USD", cfg, model_dir=tmp_path, learners=("xgboost",),
                                 cache_dir=None, budget=binary_grid.CoreBudget(10.0))
    assert len(res["cells"]) == 8 * 9 * 3  # 8 variants x 9 horizons x 3 binaries x 1 learner
    assert all(not f.startswith(("b_", "r_", "fwd")) for f in res["features"])
    assert not any(f in res["features"] for f in BINARY_COLUMNS)
    saved = sorted(p.name for p in tmp_path.glob("*.pkl"))
    assert saved and all(name.startswith("USD_xgboost_") and "_h" in name for name in saved)
    ranked = binary_grid.rank_variants(res["cells"])
    assert ranked.empty or set(ranked["variant"]) <= {v[0] for v in ext.variant_grid()}


def test_torch_mlp_learner_returns_probabilities():
    rng = np.random.default_rng(0)
    X = rng.standard_normal((120, 4)).astype("float32")
    y = (X[:, 0] > 0).astype("int8")
    m = binary_grid.fit_learner("mlp_torch", {}, X[:80], y[:80], X[80:], y[80:])
    assert m is not None and m.method in ("isotonic", "sigmoid")
    p = m.predict_proba(X)
    assert p.shape == (120,) and np.all((p >= 0.0) & (p <= 1.0))


def test_variant_grid_names_are_filename_safe(tmp_path):
    for name, _e, _w, _k in ext.variant_grid():
        tag = f"USD_xgboost_{name}_b_profit_h21"
        binary_grid._pickle(_StubModel(), tmp_path, tag, 0)
        assert (tmp_path / f"{tag}_f0.pkl").exists()
