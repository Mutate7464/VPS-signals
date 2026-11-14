"""WI-058/059 follow-up — regression read-out path in `cell_cv` (D-026 plan §7).

Guards the fix for the silent int8 binarization: `cell_cv(regression=True)` must
keep continuous labels intact and score via `model.predict`; the classifier path
must be unchanged (int8 cast).
"""

import numpy as np
import pandas as pd
import pytest

from src.swing_bsh import binary_grid
from src.xgb_trainer import PurgedWalkForwardSplit


def _synthetic(n=600, seed=7):
    rng = np.random.default_rng(seed)
    # 60 dates x 10 events per date — `_cont_stats` scores per-date ICs
    dates = np.repeat(pd.date_range("2020-01-01", periods=n // 10, freq="D").to_numpy(), 10)
    X = rng.normal(size=(n, 6)).astype("float32")
    y_cont = (X[:, 0] * 0.8 + rng.normal(0, 0.2, n)).astype("float32")
    y_bin = (y_cont > np.median(y_cont)).astype("int8")
    return X, y_cont, y_bin, dates


@pytest.mark.parametrize("learner", ["xgboost", "lightgbm"])
def test_regression_cell_cv_keeps_continuous_labels(learner):
    X, y_cont, _y_bin, dates = _synthetic()
    splitter = PurgedWalkForwardSplit(n_splits=3, embargo_td=5)
    params = binary_grid.binary_train.learner_params(binary_grid.binary_train.train.load_settings())[learner] \
        if learner == "xgboost" else {"n_estimators": 40, "learning_rate": 0.1,
                                      "num_leaves": 8, "n_jobs": 2, "random_state": 7,
                                      "verbose": -1}
    cv = binary_grid.cell_cv(X, y_cont, dates, learner, params, splitter,
                             None, "t_reg", regression=True)
    oof = cv["oof"]
    assert np.isfinite(oof).sum() > 100
    # continuous labels preserved: OOF spread is NOT two-valued
    assert np.unique(np.round(oof[np.isfinite(oof)], 6)).size > 10
    # and the read-out statistic is computable against the UNBINARIZED labels
    from src.swing_bsh import grid_targets_ext
    pooled, _mean, folds, p = grid_targets_ext._cont_stats(y_cont, oof, cv["fold_id"], dates)
    assert np.isfinite(pooled) and abs(pooled) < 1.0 and np.isfinite(p)
    for m in cv["models"].values():
        assert hasattr(m, "predict") and not hasattr(m, "predict_proba")


def test_classifier_path_unchanged_int8():
    X, _y_cont, y_bin, dates = _synthetic()
    splitter = PurgedWalkForwardSplit(n_splits=3, embargo_td=5)
    params = binary_grid.binary_train.learner_params(
        binary_grid.binary_train.train.load_settings())["xgboost"]
    cv = binary_grid.cell_cv(X, y_bin, dates, "xgboost", params, splitter, None, "t_bin")
    oof = cv["oof"]
    assert np.isfinite(oof).sum() > 100
    assert oof[np.isfinite(oof)].min() >= 0.0 and oof[np.isfinite(oof)].max() <= 1.0


def test_regression_rejects_wi044_learners():
    from src.swing_bsh import learner_ext
    X, y_cont, _y, dates = _synthetic(n=200)
    with learner_ext.learner_extension_mode():
        with pytest.raises(ValueError, match="regression read-out not supported"):
            binary_grid.fit_learner("catboost", {}, X[:150], y_cont[:150],
                                    X[150:], y_cont[150:], regression=True)
