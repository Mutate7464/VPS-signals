"""WI-035 — two-threshold binary entry gate tests (D-022 §3).

Synthetic only: no reads under `data/` or `reports/`. Verify:
`uv run pytest tests/test_swing_bsh_binary_gate.py -q`
"""

from __future__ import annotations

import pickle

import numpy as np
import pandas as pd

from src.feature_engine import wi016_feature_names
from src.swing_bsh import binary_evaluate, binary_train, train
from src.swing_bsh.binary_labels import BINARY_COLUMNS, feature_names
from src.xgb_trainer import PurgedWalkForwardSplit


# --------------------------------------------------------------------------- #
# Entry rule = intersection filter (never a renormalisation, never a union)
# --------------------------------------------------------------------------- #
def test_frozen_selection_takes_the_intersection_only():
    mask = np.array([True, True, True, True])
    prof = {"oof": np.array([0.60, 0.60, 0.30, 0.90])}
    stop = {"oof": np.array([0.20, 0.90, 0.20, 0.10])}
    sel = binary_train.frozen_selection(prof, stop, 0.50, 0.30, mask)
    assert sel.tolist() == [True, False, False, True]
    # a row failing either leg is out; an out-of-mask row can never be in
    assert not sel[1] and not sel[2]
    offmask = np.array([False, False, False, False])
    assert not binary_train.frozen_selection(prof, stop, 0.0, 1.0, offmask).any()


def test_selection_edge_is_selected_minus_all_rows_mean():
    ret = np.array([0.10, 0.02, 0.02, 0.02])
    assert abs(binary_train.selection_edge([True, False, False, False], ret) - 0.06) < 1e-12
    assert np.isnan(binary_train.selection_edge([False] * 4, ret))


def test_select_binary_config_uses_calibration_edge_and_min_selected_floor():
    rng = np.random.default_rng(0)
    ret = np.concatenate([np.full(40, 0.02), np.full(60, -0.01)])
    # learner A: profit high only on the first 40 (real edge); learner B: noise
    cal_a = (np.concatenate([np.full(40, 0.8), np.full(60, 0.2)]), np.full(100, 0.1))
    cal_b = (rng.uniform(0.3, 0.7, 100), rng.uniform(0.1, 0.5, 100))
    out = binary_train.select_binary_config({"A": cal_a, "B": cal_b}, ret)
    assert out["best"]["learner"] == "A" and out["best"]["n_selected"] == 40
    assert out["best"]["edge"] > 0
    # deterministic tie-break: equal edge -> loosest thresholds (lowest τ_p)
    assert out["best"]["tau_p"] == min(binary_train.TAU_P_GRID)
    assert out["n_candidates"] == 2 * len(binary_train.TAU_P_GRID) * len(binary_train.TAU_S_GRID)
    tight = binary_train.select_binary_config({"A": cal_a, "B": cal_b}, ret, min_selected=99)
    assert tight["best"] is None


# --------------------------------------------------------------------------- #
# Calibration: isotonic per fold, CB-04 sigmoid fallback under 25 positives
# --------------------------------------------------------------------------- #
def _params():
    return {"n_estimators": 12, "max_depth": 2, "learning_rate": 0.2, "n_jobs": 2,
            "random_state": 0, "tree_method": "hist"}


def _binary_xy(n_fit=60, n_cal=120, n_pos=30, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.standard_normal((n_fit + n_cal, 4)).astype("float32")
    y = np.zeros(n_fit + n_cal, dtype="int8")
    y[n_fit + rng.choice(n_cal, size=n_pos, replace=False)] = 1
    y[: n_fit // 2] = 1
    return X[:n_fit], y[:n_fit], X[n_fit:], y[n_fit:]


def test_isotonic_when_positives_clear_the_cb04_floor():
    Xf, yf, Xc, yc = _binary_xy(n_pos=30)
    m = binary_train.fit_calibrated_binary("xgboost", Xf, yf, Xc, yc, _params())
    assert m is not None and m.method == "isotonic"
    p = m.predict_proba(Xc)
    assert p.shape == (len(yc),) and np.all((p >= 0.0) & (p <= 1.0))


def test_sigmoid_fallback_below_25_positives_and_identity_on_degenerate():
    Xf, yf, Xc, yc = _binary_xy(n_pos=10)
    m = binary_train.fit_calibrated_binary("xgboost", Xf, yf, Xc, yc, _params())
    assert m is not None and m.method == "sigmoid"
    assert np.all((m.predict_proba(Xc) >= 0.0) & (m.predict_proba(Xc) <= 1.0))
    # a single-class fit set can never produce a model
    assert binary_train.fit_calibrated_binary("xgboost", Xf, np.zeros(len(yf), "int8"), Xc, yc,
                                             _params()) is None
    assert train.calibration_method(0, 100) == "identity"


# --------------------------------------------------------------------------- #
# Leakage lock — labels / forward outcomes may never become features
# --------------------------------------------------------------------------- #
def test_feature_names_drop_labels_and_forward_columns():
    banned = ["r_frozen", "b_profit", "b_stop", "b_hold", "fwd_ret_5"]
    names = ["mom_5", "k", "horizon"] + banned
    assert feature_names(names) == ["mom_5", "k", "horizon"]
    panel = pd.DataFrame({**{c: [0.1] for c in names}, "state": ["at_bottom"]})
    kept = feature_names(names + list(wi016_feature_names()))
    X, feats = train.feature_matrix(train.engineer(panel), kept)
    assert set(feats) == {"mom_5", "state_is_bottom", "k", "horizon"}
    assert not any(f.startswith(("b_", "r_", "fwd")) for f in feats)
    # the three binaries stay a mutually exclusive decomposition of the 3-class label
    assert set(BINARY_COLUMNS).isdisjoint(feats)


# --------------------------------------------------------------------------- #
# Gate frame + verdict reuse (ADOPT_LOOSE_4OF5 arithmetic, for the record)
# --------------------------------------------------------------------------- #
def _fake_res(learner="xgboost", n=18):
    # fold 0: 6 selected (real edge) + 3 unselected; fold 1: all unselected
    prof = np.array([0.8] * 6 + [0.2] * 3 + [0.2] * 9)
    stop = np.array([0.1] * 6 + [0.4] * 12)
    ret = np.array([0.03] * 6 + [0.0] * 3 + [0.02] * 9)
    return {
        "canon": np.array([True] * n), "fold_id": np.array([0] * 9 + [1] * 9, dtype="int16"),
        "ret": ret, "symbol": np.array(["A"] * n),
        "dates": np.array(pd.date_range("2020-01-01", periods=n).to_numpy()),
        "cv": {(learner, "b_profit"): {"oof": prof}, (learner, "b_stop"): {"oof": stop}},
    }


def test_gate_frame_applies_the_frozen_two_threshold_rule():
    res = _fake_res()
    g = binary_evaluate.gate_frame(res, "xgboost", 0.5, 0.3)
    assert len(g) == 18 and g["selected"].tolist() == [True] * 6 + [False] * 12
    gate = binary_evaluate.evaluate.fold_gate(g)
    assert gate["n_folds_pos"] == 1 and gate["folds"][1]["n_selected"] == 0
    assert gate["folds"][0]["edge"] > 0 and gate["pooled_edge"] > 0
    assert binary_evaluate.evaluate.verdict(gate["n_folds_pos"], gate["pooled_edge"], 3.0) == "REJECT"
    assert binary_evaluate.evaluate.verdict(4, gate["pooled_edge"], 3.0) == "ADOPT"


# --------------------------------------------------------------------------- #
# Admin mandate — every fitted model is pickled, verdict-independent
# --------------------------------------------------------------------------- #
def test_model_filename_contract_for_every_grid_point():
    for mkt in ("USD", "CAD"):
        for learner in binary_train.LEARNERS:
            for b in BINARY_COLUMNS:
                for fold in (0, 4, "final"):
                    name = binary_train.model_filename(mkt, learner, b, fold)
                    assert name == f"{mkt}_{learner}_{b}_f{fold}.pkl"
    assert binary_train.MODEL_DIR.name == "wi035" and "models" in binary_train.MODEL_DIR.parts


def test_save_binary_model_round_trips(tmp_path):
    Xf, yf, Xc, yc = _binary_xy(n_pos=30)
    m = binary_train.fit_calibrated_binary("logistic_l2", Xf, yf, Xc, yc, {})
    path = binary_train.save_binary_model(m, "CAD", "logistic_l2", "b_stop", 3, tmp_path, ["a"])
    assert path.name == "CAD_logistic_l2_b_stop_f3.pkl" and path.exists()
    with open(path, "rb") as fh:
        blob = pickle.load(fh)
    assert blob["provenance"]["binary"] == "b_stop" and blob["provenance"]["fold"] == 3
    assert blob["model"].predict_proba(Xc).shape == (len(yc),)
    assert binary_train.save_binary_model(None, "CAD", "xgboost", "b_hold", 0, tmp_path) is None


def test_binary_cv_collects_one_fitted_model_per_fold():
    rng = np.random.default_rng(1)
    n, dates = 400, np.repeat(pd.date_range("2016-01-04", periods=80, freq="B").to_numpy(), 5)
    X = rng.standard_normal((n, 5)).astype("float32")
    y = (rng.random(n) > 0.5).astype("int8")
    splitter = PurgedWalkForwardSplit(n_splits=2, embargo_td=5)
    out = binary_train.binary_cv(X, y, dates, "logistic_l2", {}, splitter)
    assert len(out["models"]) == out["fold_id"].max() + 1 and out["models"]
    assert np.isfinite(out["oof"]).any()
