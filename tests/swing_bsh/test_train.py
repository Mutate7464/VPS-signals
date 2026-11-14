"""WI-033 — swing-conditioned 3-class trainer + ADOPT_LOOSE_4OF5 gate tests.

Synthetic only: no reads under `data/` or `reports/`. Verify:
`uv run pytest tests/swing_bsh/test_train.py -q`
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.swing_bsh import evaluate, train
from src.xgb_trainer import PurgedWalkForwardSplit


def test_embargo_is_max_of_floor_and_horizon():
    assert train.embargo_for([21, 55]) == 55
    assert train.embargo_for([8, 21]) == 21
    assert train.embargo_for([5]) == train.EMBARGO_FLOOR


def test_calibration_method_identity_sigmoid_isotonic():
    assert train.calibration_method(0, 100) == "identity"
    assert train.calibration_method(100, 100) == "identity"
    assert train.calibration_method(24, 100) == "sigmoid"
    assert train.calibration_method(25, 100) == "isotonic"


def test_verdict_math_adopt_reject_inconclusive():
    assert evaluate.verdict(4, 0.01, 3.0) == "ADOPT"
    assert evaluate.verdict(5, 0.01, 3.0) == "ADOPT"
    assert evaluate.verdict(3, 0.01, 3.0) == "REJECT"
    assert evaluate.verdict(4, -0.01, 3.0) == "REJECT"
    assert evaluate.verdict(4, 0.01, 0.5) == "INCONCLUSIVE"
    assert evaluate.verdict(4, 0.01, float("nan")) == "INCONCLUSIVE"


def _gate(n_win: int) -> pd.DataFrame:
    """5-fold gate frame: model beats the baseline in the first `n_win` folds."""
    rows = []
    for f in range(5):
        base, model = 0.01, (0.02 if f < n_win else 0.005)
        rows += [{"fold": f, "r_frozen": base, "p_buy": 0.5, "selected": False} for _ in range(8)]
        rows += [{"fold": f, "r_frozen": model, "p_buy": 0.6, "selected": True} for _ in range(2)]
    return pd.DataFrame(rows)


def test_fold_gate_four_of_five_adopts_three_of_five_rejects():
    four = evaluate.fold_gate(_gate(4))
    assert four["n_folds_pos"] == 4 and four["pooled_edge"] > 0
    assert evaluate.verdict(four["n_folds_pos"], four["pooled_edge"], 3.0) == "ADOPT"
    three = evaluate.fold_gate(_gate(3))
    assert three["n_folds_pos"] == 3
    assert evaluate.verdict(three["n_folds_pos"], three["pooled_edge"], 3.0) == "REJECT"


def test_gate_frame_filters_to_canonical_geometry():
    oof = pd.DataFrame({
        "symbol": ["A"] * 4, "date": pd.to_datetime(["2020-01-01"] * 4),
        "state": ["at_bottom", "at_bottom", "at_bottom", "at_top"],
        "k": [1.5, 2.0, 1.5, 1.5], "horizon": [21, 21, 55, 21], "fold": [0, 0, 0, 0],
        "p_buy": [0.6, 0.6, 0.6, 0.6], "r_frozen": [0.01, 0.01, 0.01, 0.01],
        "pred": [1, 1, 1, 1],
    })
    g = evaluate.gate_frame(oof)
    assert len(g) == 1 and g["pos"].iloc[0] == 0 and bool(g["selected"].iloc[0])


def test_splitter_yields_five_folds():
    dates = np.repeat(pd.date_range("2016-01-04", periods=200, freq="B").to_numpy(), 5)
    folds = list(PurgedWalkForwardSplit(n_splits=5, embargo_td=55).split(dates))
    assert len(folds) == 5
    for tr, va in folds:
        assert dates[tr].max() < dates[va].min()


def test_feature_matrix_excludes_the_frozen_return():
    panel = pd.DataFrame({"state": ["at_bottom"], "f1": [0.1], "state_is_bottom": [1.0],
                          "k": [1.5], "horizon": [21.0], "r_frozen": [0.5]})
    X, feats = train.feature_matrix(panel, ["f1"])
    assert feats == ["f1", "state_is_bottom", "k", "horizon"]
    assert "r_frozen" not in feats and X.shape == (1, 4)


def test_fit_calibrated_multiclass_sigmoid_fallback():
    rng = np.random.default_rng(0)
    n = 90
    X = rng.standard_normal((n, 4)).astype("float32")
    y = np.tile(np.array([0, 1, 2], dtype="int8"), n // 3)
    params = {"n_estimators": 20, "max_depth": 2, "learning_rate": 0.1,
              "n_jobs": 2, "random_state": 0, "tree_method": "hist"}
    m = train.fit_calibrated_multiclass(X[:60], y[:60], X[60:], y[60:], params)
    assert m is not None
    # 10 calibration rows per class < 25 positives -> sigmoid (CB-04 fallback)
    assert m.methods == ["sigmoid", "sigmoid", "sigmoid"]
    proba = m.predict_proba(X[60:])
    assert proba.shape == (30, 3)
    assert np.allclose(proba.sum(axis=1), 1.0)
