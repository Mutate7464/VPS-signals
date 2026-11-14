"""WI-035 — three binary swing-event labels (D-022 §3) tests.

Synthetic only: no reads under `data/` or `reports/`. Verify:
`uv run pytest tests/test_swing_bsh_binary_labels.py -q`
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.feature_engine import wi016_feature_names
from src.swing_bsh import train
from src.swing_bsh.binary_labels import (
    BINARY_COLUMNS, RHO_THRESHOLD, add_binary_labels, binary_targets, canonical_mask,
    kept_features,
)
from src.swing_bsh.binary_train import learner_params
from src.swing_bsh.events import BUY, HOLD, SELL


def test_binary_targets_decompose_first_touch_by_side():
    y = np.array([BUY, SELL, HOLD, BUY, SELL, HOLD], dtype="int8")
    state = np.array(["at_bottom"] * 3 + ["at_top"] * 3)
    t = binary_targets(y, state)
    # at_bottom: implied side up -> BUY is profit, SELL is stop; at_top is mirrored.
    assert t["b_profit"].tolist() == [1, 0, 0, 0, 1, 0]
    assert t["b_stop"].tolist() == [0, 1, 0, 1, 0, 0]
    assert t["b_hold"].tolist() == [0, 0, 1, 0, 0, 1]
    assert (t["b_profit"] + t["b_stop"] + t["b_hold"]).tolist() == [1] * 6


def test_add_binary_labels_is_int8_and_mutually_exclusive():
    panel = pd.DataFrame({"y": [BUY, SELL, HOLD], "state": ["at_bottom", "at_bottom", "at_top"]})
    out = add_binary_labels(panel)
    for name in BINARY_COLUMNS:
        assert out[name].dtype == np.dtype("int8")
    assert out[list(BINARY_COLUMNS)].to_numpy().sum(axis=1).tolist() == [1, 1, 1]


def test_canonical_mask_filters_geometry_and_priced_baseline():
    panel = pd.DataFrame({
        "state": ["at_bottom", "at_bottom", "at_top", "at_bottom"],
        "k": [1.5, 2.0, 1.5, 1.5], "horizon": [21, 21, 21, 55],
        "r_frozen": [0.01, 0.01, 0.01, np.nan],
    })
    assert canonical_mask(panel).tolist() == [True, False, False, False]


def test_kept_features_never_expose_labels_or_forward_outcomes():
    rng = np.random.default_rng(1)
    names = wi016_feature_names()
    panel = pd.DataFrame({
        names[0]: rng.standard_normal(4), names[1]: rng.standard_normal(4),
        "r_frozen": [0.1, 0.2, 0.3, 0.4], "fwd_ret": [1.0, 2.0, 3.0, 4.0],
        "b_profit": [1, 0, 1, 0], "b_stop": [0, 1, 0, 1], "b_hold": [0, 0, 0, 0],
        "state": ["at_bottom"] * 4, "k": [1.5] * 4, "horizon": [21.0] * 4,
    })
    kept, dropped = kept_features(panel)
    assert set(kept) <= set(names) and kept
    for banned in ("r_frozen", "fwd_ret", "b_profit", "b_stop", "b_hold"):
        assert banned not in kept
    assert RHO_THRESHOLD == 0.4 and isinstance(dropped, dict)


def test_kept_features_prunes_duplicate_clusters():
    rng = np.random.default_rng(0)
    base = rng.standard_normal(200)
    names = wi016_feature_names()
    panel = pd.DataFrame({names[0]: base, names[1]: base * -1.0, names[2]: rng.standard_normal(200)})
    kept, dropped = kept_features(panel, features=names[:3])
    assert len(kept) == 2 and len(dropped) == 1


def test_learner_params_keep_n_jobs_two_and_cap_xgb():
    cfg = {"modeling": {"xgb_params": {"n_estimators": 400, "max_depth": 4, "n_jobs": 2}}}
    params = learner_params(cfg)
    assert params["xgboost"]["n_estimators"] <= 300
    assert params["xgboost"]["n_jobs"] == 2 and params["xgboost"]["tree_method"] == "hist"
    assert params["hist_gbm"]["max_iter"] > 0 and params["logistic_l2"]["max_iter"] > 0
    assert train.N_SPLITS == 5
