"""WI-062 — L1.5 meta-label tests (D-026, Layer 1 predictive only).

Synthetic only: no reads under `data/` or `reports/`.
Run: `uv run pytest tests/test_meta_label_ext.py -q --tb=short --maxfail=1`
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.swing_bsh import meta_label_ext as ml

N, SEED, N_SPLITS = 1200, 7, 3


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.asarray(z, dtype="float64")))


def _panel(n: int = N, seed: int = SEED, permute: bool = False, beta: float = 1.2):
    """Detection-bar features X; latent signal drives BOTH the primary and the meta label.

    ``primary_oof`` tracks the same latent signal with independent noise, so a
    permuted-label run that still finds AUC > 0.5 would prove leakage.
    """
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 3)).astype("float32")
    s = 1.0 * X[:, 0] + 0.7 * X[:, 1]
    y_meta = (_sigmoid(beta * s) > rng.random(n)).astype("int8")
    if permute:
        y_meta = rng.permutation(y_meta).astype("int8")
    primary_oof = np.clip(0.5 + 0.25 * np.tanh(s) + rng.normal(0.0, 0.15, n), 0.0, 1.0)
    dates = pd.to_datetime("2018-01-01") + pd.to_timedelta(np.arange(n) // 3, unit="D")
    return y_meta, primary_oof, X, dates


# --------------------------------------------------------------------------- #
# Labels — positive class = the primary wins
# --------------------------------------------------------------------------- #
def test_primary_sides_map_the_swing_state():
    sides = ml.primary_sides(["at_bottom", "at_top", "at_bottom"])
    assert sides.dtype == np.float32
    assert np.allclose(sides, [1.0, -1.0, 1.0])


def test_build_meta_labels_is_one_only_when_the_primary_wins():
    side = np.array([1.0, 1.0, -1.0, -1.0, np.nan])
    ret = np.array([0.05, -0.05, -0.05, 0.05, 0.10])
    y = ml.build_meta_labels(side, ret)
    assert y.dtype == np.int8
    assert list(y) == [1, 0, 1, 0, -1]           # last row: no side -> purge sentinel
    assert list(ml.build_meta_labels(side, ret, cost=0.06)) == [0, 0, 0, 0, -1]
    with pytest.raises(ValueError):
        ml.build_meta_labels([1.0], [0.1, 0.2])


# --------------------------------------------------------------------------- #
# Feature guard — an OOF / label column can never become a feature
# --------------------------------------------------------------------------- #
def test_feature_guard_rejects_label_and_primary_prediction_columns():
    names = ["ret_1d", "vol_z", "mom_20", "rsi_14", "state_is_bottom",
             "r_frozen", "y", "b_profit", "p_buy", "primary_oof", "p_meta", "pred_hold"]
    kept = ml.feature_names(names)
    assert kept == ["ret_1d", "vol_z", "mom_20", "rsi_14", "state_is_bottom"]
    assert ml.is_primary_prediction_name("primary_oof")
    assert ml.is_primary_prediction_name("p_meta")
    assert ml.is_primary_prediction_name("b_hold")
    assert ml.is_primary_prediction_name("y")           # raw label column
    assert not ml.is_primary_prediction_name("vol_z")   # not a false positive
    assert not ml.is_primary_prediction_name("mom_20")


# --------------------------------------------------------------------------- #
# OOF meta pipeline
# --------------------------------------------------------------------------- #
def test_meta_oof_uses_earlier_folds_and_never_the_fold_s_own_oof():
    y, pof, X, dates = _panel()
    out = ml.meta_oof(y, pof, X, dates, n_splits=N_SPLITS, embargo_td=20)
    assert out["primary_oof_used_as_feature"] is False
    assert np.isfinite(out["oof"][out["fold_id"] >= 0]).all()
    scored = [f for f in out["folds"] if "calibration" in f]
    assert len(scored) >= 2
    for f in scored:
        # every fitting row is an earlier bar than the fold's first validation bar
        assert f["max_train_idx"] < f["min_val_idx"]
    assert scored[0]["fold"] == 0 and scored[0]["n_train"] >= ml.MIN_TRAIN_ROWS
    scored_rows = out["fold_id"][out["fold_id"] >= 0]
    assert (scored_rows >= 0).all() and out["n_scored"] == len(scored_rows)


def test_synthetic_separation_gives_meta_auc_above_one_half():
    y, pof, X, dates = _panel()
    out = ml.meta_oof(y, pof, X, dates, n_splits=N_SPLITS, embargo_td=20)
    assert out["auc"] > 0.60, out["auc"]
    assert out["n_scored"] >= 100


def test_permuted_labels_give_meta_auc_near_one_half():
    y, pof, X, dates = _panel(permute=True)
    out = ml.meta_oof(y, pof, X, dates, n_splits=N_SPLITS, embargo_td=20)
    assert np.isfinite(out["auc"])
    assert abs(out["auc"] - 0.5) < 0.07, out["auc"]    # no-leakage null


def test_permuted_label_auc_is_far_below_the_real_label_auc():
    y_obs, pof, X, dates = _panel()
    y_perm, _, _, _ = _panel(permute=True)
    obs = ml.meta_oof(y_obs, pof, X, dates, n_splits=N_SPLITS, embargo_td=20)["auc"]
    null = ml.meta_oof(y_perm, pof, X, dates, n_splits=N_SPLITS, embargo_td=20)["auc"]
    assert obs - null > 0.10, (obs, null)


# --------------------------------------------------------------------------- #
# Final (non-OOF) model + guards
# --------------------------------------------------------------------------- #
def test_fit_meta_model_returns_a_calibrated_probability():
    y, pof, X, dates = _panel()
    blob = ml.fit_meta_model(y, X, dates, calib_fraction=0.2, embargo_td=20)
    assert blob is not None
    assert blob["method"] in ("isotonic", "sigmoid", "identity")
    p = ml.predict_meta(blob, X)
    assert p.shape == (len(X),) and np.isfinite(p).all() and ((0.0 <= p) & (p <= 1.0)).all()
    assert ml.fit_meta_model(np.zeros(len(y), dtype="int8"), X, dates) is None


def test_meta_oof_rejects_misaligned_inputs():
    y, pof, X, dates = _panel(n=200, seed=3)
    with pytest.raises(ValueError):
        ml.meta_oof(y, pof[:-1], X, dates)
    # non-finite primary OOF rows are never scored
    pof2 = pof.copy()
    pof2[:50] = np.nan
    out = ml.meta_oof(y, pof2, X, dates, n_splits=2, embargo_td=20)
    assert np.isfinite(out["oof"][:50]).sum() == 0


def test_meta_auc_needs_enough_rows_and_both_classes():
    y = np.zeros(10, dtype="int8")
    assert not np.isfinite(ml.meta_auc(y, np.linspace(0, 1, 10)))
    y2 = np.r_[np.zeros(40, dtype="int8"), np.ones(40, dtype="int8")]
    p = np.r_[np.linspace(0, 0.4, 40), np.linspace(0.6, 1.0, 40)]
    assert ml.meta_auc(y2, p) > 0.9
    assert not np.isfinite(ml.meta_auc(np.full(80, -1, dtype="int8"), p))  # purge sentinels only
