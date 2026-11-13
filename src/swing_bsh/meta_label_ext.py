"""WI-062 — L1.5 meta-label (swing-side primary) + seed-averaging companion.

**Layer 1 only (D-023): predictive statistics (OOF AUC / IC + calibration).** No
threshold, no entry rule, no portfolio return, no EV. The decomposed positive class
uses a **fixed product of separately fitted models** — the admin ruled this
**NOT stacking** (D-026).

Primary = the swing side (``at_bottom`` ⇒ long, ``at_top`` ⇒ short); the frozen fib
rule (``r_frozen``) is the second family. The meta label is **1 when the primary
wins**: the primary rule's size-adjusted forward outcome clears the round-trip cost.

Leakage contract (structural): a fold's rows are scored by a meta model fit on
**earlier fold blocks only** (``train_folds ⊂ {0..k-1}``), and the feature matrix is
**detection-bar geometry only**. Primary OOF predictions are accepted as an
alignment input but are **never feature columns** — any column whose name carries the
primary-prediction / label signature is rejected (`feature_names`,
`is_primary_prediction_name`), so no fold can read its own OOF prediction as a feature.

Invariants: ``n_jobs=2``, float32 matrices, ``embargo_td`` floor, symbol-sequential upstream.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier

from src.swing_bsh import train
from src.xgb_trainer import PurgedWalkForwardSplit, purged_holdout

N_JOBS = 2
N_SPLITS = 5
SEED = 42
MIN_TRAIN_ROWS = 30
"""Minimum earlier-fold rows before a meta fold is scored (below: no fold model)."""
MIN_OOF_ROWS = 30
"""Minimum finite OOF rows behind a pooled AUC (mirrors `binary_grid.auc_ic`)."""
DEFAULT_COST = 0.0
"""Round-trip cost charged against the primary's size-adjusted outcome."""
PRIMARY_PRED_RE = r"(?:^|_)(?:p|prob|pred|oof)(?:_|$)"
"""A label / outcome / primary-prediction column must never become a meta feature."""
_PRIMARY_PRED = re.compile(PRIMARY_PRED_RE)
LEAKAGE_PREFIXES: tuple[str, ...] = ("b_", "r_", "fwd")
"""Label / forward-outcome prefixes (`binary_labels.NON_FEATURE_PREFIXES`)."""
NON_FEATURE_COLUMNS = train.NON_FEATURE_COLUMNS
"""Exact raw columns (symbol/date/state/k/horizon/close/atr/y) — never features."""
XGB_META_DEFAULTS = {"n_estimators": 40, "max_depth": 3, "learning_rate": 0.05,
                     "subsample": 0.8, "colsample_bytree": 0.8, "reg_lambda": 1.0}

__all__ = ["DEFAULT_COST", "MIN_OOF_ROWS", "MIN_TRAIN_ROWS", "N_JOBS", "N_SPLITS",
           "PRIMARY_PRED_RE", "SEED", "build_meta_labels", "feature_names", "fit_meta_model",
           "is_primary_prediction_name", "meta_auc", "meta_oof", "primary_sides"]


# --------------------------------------------------------------------------- #
# Labels: positive class = the primary wins
# --------------------------------------------------------------------------- #
def primary_sides(state) -> np.ndarray:
    """Primary swing side in ``{-1, +1}`` (``at_bottom`` long, ``at_top`` short)."""
    s = pd.Series(np.asarray(state).ravel())
    bottom = s.isin(["at_bottom", "long", 1, True]).to_numpy()
    top = s.isin(["at_top", "short", -1, False]).to_numpy()
    return np.where(bottom, 1.0, np.where(top, -1.0, np.nan)).astype("float32")


def build_meta_labels(primary_side, primary_outcome, *, cost: float = DEFAULT_COST) -> np.ndarray:
    """``y_meta = 1`` iff the primary's size-adjusted outcome beats `cost`.

    `primary_outcome` is the primary rule's forward return (`r_frozen` for the frozen
    fib family) read at the detection bar: it is a forward outcome and is **never** a
    feature (label only). Non-finite side / outcome rows return ``-1`` (purge
    sentinel) and are excluded from every fit and every score.
    """
    side = np.asarray(primary_side, dtype="float64").ravel()
    ret = np.asarray(primary_outcome, dtype="float64").ravel()
    if side.shape != ret.shape:
        raise ValueError(f"shape mismatch: side {side.shape} vs outcome {ret.shape}")
    edge = side * ret - float(cost)
    ok = np.isfinite(edge)
    return np.where(ok, (edge > 0.0).astype("int8"), np.int8(-1))


def is_primary_prediction_name(name: str) -> bool:
    """True for label / forward-outcome / primary-prediction columns (feature guard).

    Exact raw columns (``train.NON_FEATURE_COLUMNS``) plus the ``b_`` / ``r_`` / ``fwd``
    leakage prefixes are rejected; the engineered ``state_is_bottom`` is **kept** (the
    side flag, not the raw ``state`` string).
    """
    n = str(name)
    if n in NON_FEATURE_COLUMNS:
        return True
    if any(n.startswith(p) for p in LEAKAGE_PREFIXES):
        return True
    return _PRIMARY_PRED.search(n) is not None


def feature_names(names) -> list[str]:
    """Detection-bar geometry only; every label / OOF column is rejected."""
    return [str(n) for n in names if not is_primary_prediction_name(n)]


# --------------------------------------------------------------------------- #
# Meta model (purged CV; a fold's own block is never in its fit)
# --------------------------------------------------------------------------- #
def _proba(model, X) -> np.ndarray:
    """1-D positive-class probability for both pickle families."""
    p = np.asarray(model.predict_proba(X), dtype="float64")
    return p[:, 1] if p.ndim == 2 else np.asarray(p).ravel()


def _logit(p) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype="float64"), 1e-6, 1.0 - 1e-6)
    return np.log(p / (1.0 - p))


def meta_auc(y_meta, p) -> float:
    """Pooled OOF AUC of the meta probability (NaN below `MIN_OOF_ROWS`)."""
    y = np.asarray(y_meta, dtype="float64").ravel()
    p = np.asarray(p, dtype="float64").ravel()
    m = np.isfinite(p) & np.isfinite(y) & (y >= 0)
    if m.sum() < MIN_OOF_ROWS or len(np.unique(y[m])) < 2:
        return float("nan")
    return float(roc_auc_score(y[m], p[m]))


def _fit_meta(X_fit, y_fit, X_cal, y_cal, params, seed):
    """XGB meta fit with the CB-04 calibrator (single-class calibration block -> identity)."""
    p = {**XGB_META_DEFAULTS, "objective": "binary:logistic", "eval_metric": "logloss",
         "tree_method": "hist", "n_jobs": N_JOBS, "random_state": int(seed)}
    p.update({k: v for k, v in dict(params or {}).items() if k in XGB_META_DEFAULTS})
    model = XGBClassifier(**p).fit(X_fit, y_fit, eval_set=[(X_cal, y_cal)], verbose=False)
    raw = np.asarray(model.predict_proba(X_cal), dtype="float64")[:, 1]
    y_cal = np.asarray(y_cal, dtype="int8")
    method = train.calibration_method(int(y_cal.sum()), len(y_cal))
    if method == "isotonic":
        cal = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(raw, y_cal)
    elif method == "sigmoid":
        cal = LogisticRegression().fit(_logit(raw).reshape(-1, 1), y_cal)
    else:
        cal = None
    return {"model": model, "method": method, "calibrator": cal, "best_iteration": int(
        getattr(model, "best_iteration", -1) or -1)}


def _calibrated(blob, X) -> np.ndarray:
    raw = np.asarray(blob["model"].predict_proba(X), dtype="float64")[:, 1]
    if blob["method"] == "isotonic" and blob["calibrator"] is not None:
        out = blob["calibrator"].predict(raw)
    elif blob["method"] == "sigmoid" and blob["calibrator"] is not None:
        out = blob["calibrator"].predict_proba(_logit(raw).reshape(-1, 1))[:, 1]
    else:
        out = raw
    return np.clip(np.asarray(out, dtype="float64"), 0.0, 1.0)


# --------------------------------------------------------------------------- #
# I/O contract
# --------------------------------------------------------------------------- #
def meta_oof(y_meta, primary_oof, X, dates, *, n_splits: int = N_SPLITS,
             embargo_td: int = train.EMBARGO_FLOOR, params: dict | None = None,
             min_train_rows: int = MIN_TRAIN_ROWS, seed: int = SEED) -> dict:
    """Purged walk-forward **OOF meta probabilities** (a fold's own OOF is never a feature).

    ``primary_oof`` is taken for alignment / diagnostics only and is **excluded from
    the feature matrix**; the meta model is fit on detection-bar geometry alone. Each
    fold is fit on the splitter's *earlier train block only* (embargo-purged via
    ``PurgedWalkForwardSplit``) with a purged inner calibration holdout, so no
    validation row and no row within the embargo ever enters that fold's fit.
    Returns ``{oof, fold_id, auc, folds, n_scored, primary_oof_used_as_feature, feature_guard}``.
    """
    y = np.asarray(y_meta).ravel().astype("int8")
    X = np.asarray(X, dtype="float32")
    dates = np.asarray(pd.to_datetime(pd.Series(np.asarray(dates).ravel())))
    po = np.asarray(primary_oof, dtype="float64").ravel()
    if not (len(y) == len(X) == len(dates) == len(po)):
        raise ValueError("y_meta / X / dates / primary_oof must share one row count")
    valid = (y >= 0) & np.isfinite(po)
    splitter = PurgedWalkForwardSplit(n_splits=int(n_splits), embargo_td=int(embargo_td))
    oof = np.full(len(y), np.nan)
    fold_id = np.full(len(y), -1, dtype="int16")
    folds: list[dict] = []
    for k, (tr, va) in enumerate(splitter.split(dates)):
        va = np.asarray(va)[valid[np.asarray(va)]]
        fit_i, cal_i = purged_holdout(dates, np.asarray(tr)[valid[np.asarray(tr)]],
                                      train.CALIB_FRACTION, splitter.embargo_td)
        if len(fit_i) < int(min_train_rows) or len(cal_i) == 0 or len(va) == 0:
            folds.append({"fold": k, "skipped": "no earlier purged block to fit on",
                          "n_val": int(len(va))})
            continue
        blob = _fit_meta(X[fit_i], y[fit_i], X[cal_i], y[cal_i], params, seed + k)
        oof[va] = _calibrated(blob, X[va])
        fold_id[va] = k
        folds.append({"fold": k, "n_train": int(len(fit_i)), "n_calib": int(len(cal_i)),
                      "n_val": int(len(va)), "pos_train": int(y[fit_i].sum()),
                      "pos_val": int(y[va].sum()), "calibration": blob["method"],
                      "max_train_idx": int(np.asarray(tr).max()) if len(tr) else -1,
                      "min_val_idx": int(np.asarray(va).min()) if len(va) else -1})
    return {"oof": oof, "fold_id": fold_id, "auc": meta_auc(y, oof), "folds": folds,
            "n_scored": int((fold_id >= 0).sum()), "primary_oof_used_as_feature": False,
            "feature_guard": PRIMARY_PRED_RE}


def fit_meta_model(y_meta, X, dates, *, calib_fraction: float = train.CALIB_FRACTION,
                   embargo_td: int = train.EMBARGO_FLOOR, params: dict | None = None,
                   seed: int = SEED) -> dict | None:
    """Final (non-OOF) meta model: fit on the early block, calibrated on the late block."""
    y = np.asarray(y_meta).ravel().astype("int8")
    X = np.asarray(X, dtype="float32")
    dates = np.asarray(pd.to_datetime(pd.Series(np.asarray(dates).ravel())))
    idx = np.flatnonzero(y >= 0)
    fit_i, cal_i = purged_holdout(dates, idx, float(calib_fraction), int(embargo_td))
    if len(fit_i) == 0 or len(cal_i) == 0 or len(np.unique(y[fit_i])) < 2:
        return None
    return _fit_meta(X[fit_i], y[fit_i], X[cal_i], y[cal_i], params, seed)


def predict_meta(blob: dict, X) -> np.ndarray:
    """Positive-class probability from `fit_meta_model` output."""
    return _calibrated(blob, np.asarray(X, dtype="float32"))


if __name__ == "__main__":  # pragma: no cover - smoke only
    print("[wi062.meta] L1.5 meta-label module — Layer 1 predictive only (D-023)")
