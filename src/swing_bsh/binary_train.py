"""WI-035 step 2 — three separate binary learners + two-threshold selection (D-022 §3).

Per binary label (`b_profit/b_stop/b_hold`) and per learner in the D-022 §3b grid
(`xgboost`, `logistic_l2`, `hist_gbm`, optional `mlp_torch`) the model is fit on
the purged walk-forward training block and calibrated on that fold's purged
calibration block: isotonic per fold, with the CB-04 sigmoid (Platt) fallback
whenever the calibration block holds < 25 positives.

The **learner and the (τ_p, τ_s) threshold pair are selected on the CALIBRATION
blocks only** and then frozen before the evaluation folds are looked at — the
entry rule is the intersection filter `P̂_profit ≥ τ_p AND P̂_stop ≤ τ_s`, never a
renormalisation of the three probabilities.

Invariants: `n_jobs=2`, float32, symbol-sequential reads, per-fold checkpoint.
"""

from __future__ import annotations

import gc
import json
import pickle
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import DMatrix, XGBClassifier

from src.swing_bsh import train
from src.swing_bsh.binary_labels import (
    BINARY_COLUMNS, binary_targets, build_binary_panel, canonical_mask, feature_names,
    kept_features, load_panel_checkpoint, save_panel_checkpoint,
)
from src.xgb_trainer import PurgedWalkForwardSplit, purged_holdout

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_DIR = BASE_DIR / "data" / "models" / "wi035"
"""Admin override 2026-11-09: every fitted model is pickled here, verdict-independent.
`data/models/` is untracked (gitignore) — pickles are for future testing, nothing deployed."""

N_JOBS = 2
N_SPLITS = 5
CALIB_FRACTION = 0.20
CB04_MIN_POSITIVES = 25
EARLY_STOPPING_ROUNDS = 30
LEARNERS: tuple[str, ...] = ("xgboost", "logistic_l2", "hist_gbm")
OPTIONAL_LEARNERS: tuple[str, ...] = ("mlp_torch",)
"""Kept behind `--learners` and off the default grid (1.0 core-hour cap)."""
TAU_P_GRID: tuple[float, ...] = (0.40, 0.50, 0.60, 0.70)
TAU_S_GRID: tuple[float, ...] = (0.20, 0.30, 0.40, 0.50)
MIN_SELECTED = 20
XGB_MAX_ESTIMATORS = 300
HGB_MAX_ITER = 150
SEED = 42

__all__ = [
    "CALIB_FRACTION", "CB04_MIN_POSITIVES", "LEARNERS", "MIN_SELECTED", "MODEL_DIR",
    "N_SPLITS", "TAU_P_GRID", "TAU_S_GRID", "CalibratedBinary", "binary_cv",
    "fit_calibrated_binary", "frozen_selection", "learner_params", "model_filename",
    "placebo_null", "save_binary_model", "select_binary_config", "selection_edge",
    "train_market", "treeshap_shares",
]


def model_filename(market: str, learner: str, binary: str, fold: int | str) -> str:
    """`<MKT>_<learner>_<binary>_f<fold>.pkl` (admin-mandated pickle naming)."""
    return f"{market}_{learner}_{binary}_f{fold}.pkl"


def save_binary_model(model, market: str, learner: str, binary: str, fold: int | str,
                      model_dir: Path | None = MODEL_DIR, features=None) -> Path | None:
    """Pickle one fitted (calibrated) binary model; never raises on a `None` model."""
    if model is None or model_dir is None:
        return None
    path = Path(model_dir) / model_filename(market, learner, binary, fold)
    path.parent.mkdir(parents=True, exist_ok=True)
    provenance = {"market": market, "learner": learner, "binary": binary, "fold": fold,
                  "calibration": getattr(model, "method", None),
                  "features": list(features) if features is not None else None}
    with open(path, "wb") as fh:
        pickle.dump({"model": model, "provenance": provenance}, fh)
    return path


# --------------------------------------------------------------------------- #
# Learners (D-022 §3b grid)
# --------------------------------------------------------------------------- #
def learner_params(cfg: dict) -> dict[str, dict]:
    """Frozen hyper-parameters per learner; xgb inherits `settings.yaml`."""
    xgb = dict(cfg["modeling"]["xgb_params"])
    xgb.update({
        "n_jobs": N_JOBS, "tree_method": "hist", "random_state": SEED,
        "n_estimators": min(int(xgb.get("n_estimators", XGB_MAX_ESTIMATORS)), XGB_MAX_ESTIMATORS),
    })
    return {
        "xgboost": xgb,
        "logistic_l2": {"C": 1.0, "max_iter": 400, "n_jobs": N_JOBS, "random_state": SEED},
        "hist_gbm": {"max_iter": HGB_MAX_ITER, "learning_rate": 0.06, "max_leaf_nodes": 31,
                     "l2_regularization": 1.0, "early_stopping": False, "random_state": SEED},
    }


def _fit_learner(learner: str, params: dict, X_fit, y_fit, X_cal, y_cal):
    """Fit one learner; xgb early-stops on the fold's calibration block."""
    if learner == "xgboost":
        model = XGBClassifier(**params, objective="binary:logistic", eval_metric="logloss",
                              early_stopping_rounds=EARLY_STOPPING_ROUNDS)
        model.fit(X_fit, y_fit, eval_set=[(X_cal, y_cal)], verbose=False)
        return model
    if learner == "logistic_l2":
        model = Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(penalty="l2", solver="lbfgs", **params)),
        ])
        model.fit(X_fit, y_fit)
        return model
    if learner == "hist_gbm":
        model = HistGradientBoostingClassifier(**params)
        model.fit(X_fit, y_fit)
        return model
    raise ValueError(f"unknown learner: {learner}")


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype="float64"), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def dead_columns(X_fit) -> np.ndarray:
    """Columns with no finite value in the fit block.

    `HistGradientBoostingClassifier` cannot bin an all-missing column and the
    logistic pipeline's median imputer would propagate NaN, so the fit block's
    dead columns are pinned to 0.0 (their training-block mean is undefined).
    """
    return ~np.isfinite(np.asarray(X_fit, dtype="float32")).any(axis=0)


def fill_dead_columns(dead: np.ndarray, *blocks):
    """Zero the dead columns of each design block (idempotent; copies on demand)."""
    if not np.asarray(dead, dtype=bool).any():
        return blocks
    out = []
    for block in blocks:
        block = np.array(block, dtype="float32", copy=True)
        block[:, dead] = 0.0
        out.append(block)
    return tuple(out)


class CalibratedBinary:
    """One binary model + its per-fold calibrator (isotonic, else CB-04 sigmoid)."""

    def __init__(self, learner: str, model, method: str, calibrator):
        self.learner, self.model, self.method, self.calibrator = learner, model, method, calibrator

    def raw_proba(self, X) -> np.ndarray:
        return np.asarray(self.model.predict_proba(X), dtype="float64")[:, 1]

    def predict_proba(self, X) -> np.ndarray:
        raw = self.raw_proba(X)
        if self.method == "isotonic" and self.calibrator is not None:
            out = self.calibrator.predict(raw)
        elif self.method == "sigmoid" and self.calibrator is not None:
            out = self.calibrator.predict_proba(_logit(raw).reshape(-1, 1))[:, 1]
        else:
            out = raw
        return np.clip(np.asarray(out, dtype="float64"), 0.0, 1.0)

    def best_iteration(self) -> int:
        return int(getattr(self.model, "best_iteration", -1) or -1)


def fit_regressor(learner: str, params: dict, X_fit, y_fit, X_cal, y_cal):
    """Fit one uncalibrated regressor for the continuous-target families (plan §7).

    No calibration step (isotonic/sigmoid are classifier-only); the purged fold
    split and dead-column handling are identical to the binary path. Supported
    learners: `xgboost` (reg:squarederror, early-stops on the cal block) and
    `lightgbm` (WI-044 registry hyper-parameters, regression objective).
    """
    if len(y_fit) == 0 or len(y_cal) == 0:
        return None
    X_fit, X_cal = fill_dead_columns(dead_columns(X_fit), X_fit, X_cal)
    if learner == "xgboost":
        from xgboost import XGBRegressor
        model = XGBRegressor(**params, objective="reg:squarederror", eval_metric="rmse",
                             early_stopping_rounds=EARLY_STOPPING_ROUNDS)
        model.fit(X_fit, y_fit, eval_set=[(X_cal, y_cal)], verbose=False)
        return model
    if learner == "lightgbm":
        from lightgbm import LGBMRegressor
        from src.swing_bsh import learner_ext
        model = LGBMRegressor(**learner_ext.learner_kwargs(learner, params))
        model.fit(X_fit, y_fit)
        return model
    raise ValueError(f"regression read-out not supported for learner: {learner}")


def fit_calibrated_binary(learner: str, X_fit, y_fit, X_cal, y_cal, params: dict,
                          min_pos: int = CB04_MIN_POSITIVES) -> CalibratedBinary | None:
    """Fit + calibrate one binary model; `None` when the fit set is single-class."""
    if len(y_fit) == 0 or len(y_cal) == 0 or len(np.unique(y_fit)) < 2:
        return None
    X_fit, X_cal = fill_dead_columns(dead_columns(X_fit), X_fit, X_cal)
    model = _fit_learner(learner, params, X_fit, y_fit, X_cal, y_cal)
    raw = model.predict_proba(X_cal)[:, 1].astype("float64")
    y_cal = np.asarray(y_cal, dtype="int8")
    method = train.calibration_method(int(y_cal.sum()), len(y_cal), min_pos)
    if method == "isotonic":
        calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(raw, y_cal)
    elif method == "sigmoid":
        calibrator = LogisticRegression().fit(_logit(raw).reshape(-1, 1), y_cal)
    else:
        calibrator = None
    return CalibratedBinary(learner, model, method, calibrator)


# --------------------------------------------------------------------------- #
# Cross-validation (val-block OOF + calibration-block predictions)
# --------------------------------------------------------------------------- #
def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str))


def binary_cv(X, y, dates, learner: str, params: dict, splitter: PurgedWalkForwardSplit,
              calib_fraction: float = CALIB_FRACTION, min_pos: int = CB04_MIN_POSITIVES,
              checkpoint_path: Path | None = None, label: str = "binary") -> dict:
    """Purged walk-forward CV for one binary: val-block OOF + calibration-block preds."""
    y = np.asarray(y, dtype="int8")
    oof = np.full(len(y), np.nan)
    cal = np.full(len(y), np.nan)
    fold_id = np.full(len(y), -1, dtype="int16")
    cal_mask = np.zeros(len(y), dtype=bool)
    models: dict[int, object] = {}
    stats: list[dict] = []
    for k, (tr, va) in enumerate(splitter.split(dates)):
        fit_i, cal_i = purged_holdout(dates, tr, calib_fraction, splitter.embargo_td)
        if len(fit_i) == 0 or len(cal_i) == 0:
            stats.append({"fold": k, "skipped": "empty fit/calibration set"})
            continue
        t0 = time.time()
        m = fit_calibrated_binary(learner, X[fit_i], y[fit_i], X[cal_i], y[cal_i], params, min_pos)
        if m is None:
            stats.append({"fold": k, "skipped": "degenerate fit set"})
            continue
        oof[va] = m.predict_proba(X[va])
        cal[cal_i] = m.predict_proba(X[cal_i])
        cal_mask[cal_i] = True
        fold_id[va] = k
        models[k] = m
        stats.append({
            "fold": k, "learner": learner, "n_fit": int(len(fit_i)), "n_calib": int(len(cal_i)),
            "n_val": int(len(va)), "pos_fit": int(y[fit_i].sum()), "pos_calib": int(y[cal_i].sum()),
            "calibration": m.method, "best_iteration": m.best_iteration(),
            "max_train_date": str(pd.Timestamp(dates[tr].max()).date()),
            "min_val_date": str(pd.Timestamp(dates[va].min()).date()),
            "wall_sec": round(time.time() - t0, 1),
        })
        if checkpoint_path is not None:
            _write_json(checkpoint_path, {"label": label, "folds": stats})
    return {"oof": oof, "cal": cal, "cal_mask": cal_mask, "fold_id": fold_id,
            "stats": stats, "models": models}


# --------------------------------------------------------------------------- #
# Two-threshold selection, frozen on the calibration blocks
# --------------------------------------------------------------------------- #
def selection_edge(selected, ret) -> float:
    """Mean return of the selected rows minus the all-rows mean (baseline)."""
    selected = np.asarray(selected, dtype=bool)
    ret = np.asarray(ret, dtype="float64")
    if ret.size == 0 or not selected.any():
        return float("nan")
    return float(ret[selected].mean() - ret.mean())


def select_binary_config(cal_probs: dict, ret, tau_p_grid=TAU_P_GRID, tau_s_grid=TAU_S_GRID,
                         min_selected: int = MIN_SELECTED) -> dict:
    """Pick (learner, τ_p, τ_s) maximising the calibration-block selection edge.

    `cal_probs` maps learner -> (P̂_profit, P̂_stop) on the canonical calibration
    rows; `ret` holds the aligned frozen-baseline returns. Deterministic
    tie-break: highest edge, then learner name, then loosest thresholds.
    """
    ret = np.asarray(ret, dtype="float64")
    rows: list[dict] = []
    for learner, (p_profit, p_stop) in cal_probs.items():
        for tau_p in tau_p_grid:
            for tau_s in tau_s_grid:
                sel = (np.asarray(p_profit) >= float(tau_p)) & (np.asarray(p_stop) <= float(tau_s))
                rows.append({
                    "learner": learner, "tau_p": float(tau_p), "tau_s": float(tau_s),
                    "n_selected": int(sel.sum()), "edge": selection_edge(sel, ret),
                })
    ok = [r for r in rows if r["n_selected"] >= min_selected and np.isfinite(r["edge"])]
    ok.sort(key=lambda r: (-r["edge"], r["learner"], r["tau_p"], r["tau_s"]))
    return {"best": ok[0] if ok else None, "table": rows, "n_candidates": len(rows)}


def frozen_selection(cv_profit: dict, cv_stop: dict, tau_p: float, tau_s: float, mask) -> np.ndarray:
    """Frozen two-threshold filter over panel rows flagged by `mask` (intersection only)."""
    mask = np.asarray(mask, dtype=bool)
    sel = np.zeros(mask.shape, dtype=bool)
    sel[mask] = ((np.asarray(cv_profit["oof"])[mask] >= float(tau_p))
                 & (np.asarray(cv_stop["oof"])[mask] <= float(tau_s)))
    return sel


# --------------------------------------------------------------------------- #
# TreeSHAP (xgboost reference fit per binary)
# --------------------------------------------------------------------------- #
def treeshap_shares(model, X: np.ndarray, feats: list[str], n_sample: int = 20000) -> dict:
    """Mean |TreeSHAP| share per feature for a fitted XGBClassifier."""
    sub = np.random.default_rng(0).choice(len(X), size=min(n_sample, len(X)), replace=False)
    best = getattr(model, "best_iteration", None)
    it_range = (0, best + 1) if best is not None else (0, 0)
    contrib = np.abs(model.get_booster().predict(
        DMatrix(X[sub]), pred_contribs=True, iteration_range=it_range))
    share = np.asarray(contrib, dtype="float64")[:, : len(feats)].sum(axis=0)
    share = share / (share.sum() + 1e-12)
    return dict(sorted(zip(feats, map(float, share)), key=lambda kv: kv[1], reverse=True))


# --------------------------------------------------------------------------- #
# Market driver
# --------------------------------------------------------------------------- #
def train_market(market: str, cfg: dict, *, learners=LEARNERS, params: dict | None = None,
                 min_date: str = train.MIN_DATE, allow_fixture: bool = False,
                 max_symbols: int | None = None, min_pos: int = CB04_MIN_POSITIVES,
                 checkpoint_dir: Path | None = None, model_dir: Path | None = MODEL_DIR,
                 cache_dir: Path | None = None) -> dict:
    """Build the binary panel, run the learner grid, freeze the config on the calib blocks.

    Every fitted model (each fold of each learner/binary grid point, plus the xgboost
    reference fit per binary) is pickled under `model_dir` regardless of the later gate
    verdict (admin override 2026-11-09). `cache_dir` caches the market panel parquet.
    """
    t0 = time.time()
    panel = load_panel_checkpoint(cache_dir, market) if (
        cache_dir is not None and max_symbols is None) else None
    if panel is None:
        panel = build_binary_panel(market, min_date=min_date, allow_fixture=allow_fixture,
                                   max_symbols=max_symbols)
        if cache_dir is not None and max_symbols is None and not panel.empty:
            save_panel_checkpoint(panel, cache_dir, market)
    if panel.empty:
        raise RuntimeError(f"no swing events for market={market}")
    kept, dropped = kept_features(panel)
    kept = feature_names(kept)  # no label / forward-outcome column may become a feature
    panel = train.engineer(panel)
    X, feats = train.feature_matrix(panel, kept)
    dates = panel["date"].to_numpy()
    state = panel["state"].to_numpy()
    y3 = panel["y"].to_numpy(dtype="int8")
    ret = panel["r_frozen"].to_numpy(dtype="float64")
    canon = canonical_mask(panel)
    targets = {b: panel[b].to_numpy(dtype="int8") for b in BINARY_COLUMNS}
    embargo = train.embargo_for(panel["horizon"].to_numpy())
    p_all = params or learner_params(cfg)
    splitter = PurgedWalkForwardSplit(n_splits=N_SPLITS, embargo_td=embargo)
    ckpt_dir = Path(checkpoint_dir) if checkpoint_dir is not None else Path("/tmp/wi035")

    cv: dict[tuple[str, str], dict] = {}
    saved: list[str] = []
    for learner in learners:
        for b in BINARY_COLUMNS:
            cv[(learner, b)] = binary_cv(
                X, targets[b], dates, learner, p_all[learner], splitter, min_pos=min_pos,
                checkpoint_path=ckpt_dir / f"wi035_checkpoint_{market}.json",
                label=f"wi035_{market}_{learner}_{b}",
            )
            # Admin override 2026-11-09: keep every fitted fold model, verdict-independent.
            for fold, m in cv[(learner, b)]["models"].items():
                p = save_binary_model(m, market, learner, b, fold, model_dir, feats)
                if p is not None:
                    saved.append(p.name)

    cal_mask = np.ones(len(y3), dtype=bool)
    for key in cv:
        cal_mask &= cv[key]["cal_mask"]
    cal_rows = (canon & cal_mask
                & np.isfinite(cv[(learners[0], "b_profit")]["cal"])
                & np.isfinite(cv[(learners[0], "b_stop")]["cal"]))
    cal_probs = {
        learner: (cv[(learner, "b_profit")]["cal"][cal_rows], cv[(learner, "b_stop")]["cal"][cal_rows])
        for learner in learners
    }
    selection = select_binary_config(cal_probs, ret[cal_rows], min_selected=MIN_SELECTED)

    fit_i, cal_i = purged_holdout(dates, np.arange(len(y3)), CALIB_FRACTION, embargo)
    treeshap: dict[str, dict] = {}
    final_meta: dict[str, dict] = {}
    for b in BINARY_COLUMNS:
        ref = fit_calibrated_binary("xgboost",
                                    X[fit_i], targets[b][fit_i], X[cal_i], targets[b][cal_i],
                                    p_all["xgboost"], min_pos)
        if ref is not None:
            treeshap[b] = dict(list(treeshap_shares(ref.model, X, feats).items())[:10])
            final_meta[b] = {"reference_learner": "xgboost", "calibration": ref.method,
                             "best_iteration": ref.best_iteration(),
                             "n_fit": int(len(fit_i)), "n_calib": int(len(cal_i))}
            p = save_binary_model(ref, market, "xgboost", b, "final", model_dir, feats)
            if p is not None:
                saved.append(p.name)

    result = {
        "market": market, "n_rows": int(len(y3)),
        "n_symbols": int(pd.Series(panel["symbol"]).nunique()),
        "symbol": panel["symbol"].to_numpy(),
        "features": feats, "n_features_pruned": len(kept),
        "n_features_input": len(kept) + len(dropped), "dropped": dropped,
        "embargo_td": embargo, "params": p_all, "learners": list(learners),
        "folds": {f"{k[0]}:{k[1]}": v["stats"] for k, v in cv.items()},
        "cv": cv, "canon_rows": int(canon.sum()), "cal_selection_rows": int(cal_rows.sum()),
        "selection": selection, "treeshap": treeshap, "final_meta": final_meta,
        "X": X, "dates": dates, "state": state, "y3": y3, "ret": ret, "canon": canon,
        "ret_max_abs": float(np.nanmax(np.abs(ret))) if np.isfinite(ret).any() else float("nan"),
        "fold_id": cv[(learners[0], "b_profit")]["fold_id"], "splitter": splitter,
        "model_dir": str(model_dir) if model_dir is not None else None,
        "n_models_saved": len(saved), "models_saved": saved,
        "runtime_sec": round(time.time() - t0, 1),
    }
    _write_json(ckpt_dir / f"wi035_checkpoint_{market}.json",
                {"market": market, "rows": result["n_rows"], "folds": result["folds"],
                 "selection": selection["best"], "n_models_saved": len(saved),
                 "runtime_sec": result["runtime_sec"]})
    del panel
    gc.collect()
    return result


def placebo_null(res: dict, *, learner: str, n_seeds: int = 3, seed0: int = 1000,
                 min_selected: int = MIN_SELECTED, budget=None) -> dict:
    """CB-05 label-permutation placebo on the frozen config (3 seeds by default).

    Each seed permutes the 3-class labels, re-derives the binaries, retrains and
    re-selects the thresholds on the calibration blocks, then measures the
    evaluation-fold selection edge. `budget` (with `.left()` in core-seconds)
    stops the loop before a seed that would overrun the core-hour cap.
    """
    X, dates, splitter = res["X"], res["dates"], res["splitter"]
    val = res["canon"] & (res["fold_id"] >= 0)
    ret_val = res["ret"][val]
    params = res["params"][learner]
    observed = res["observed_edge"]
    null: list[float] = []
    seed_sec: float | None = None
    for s in range(n_seeds):
        if s > 0 and budget is not None and seed_sec is not None and budget.left() < seed_sec * 1.2:
            break
        t0 = time.time()
        y_perm = np.random.default_rng(seed0 + s).permutation(res["y3"])
        targets = binary_targets(y_perm, res["state"])
        cvs = {b: binary_cv(X, targets[b], dates, learner, params, splitter) for b in BINARY_COLUMNS}
        cal_mask = np.ones(len(res["y3"]), dtype=bool)
        for b in BINARY_COLUMNS:
            cal_mask &= cvs[b]["cal_mask"]
        rows = (res["canon"] & cal_mask & np.isfinite(cvs["b_profit"]["cal"])
                & np.isfinite(cvs["b_stop"]["cal"]))
        pick = select_binary_config(
            {learner: (cvs["b_profit"]["cal"][rows], cvs["b_stop"]["cal"][rows])},
            res["ret"][rows], min_selected=min_selected)["best"]
        if pick is not None:
            sel = (((cvs["b_profit"]["oof"][val] >= pick["tau_p"])
                    & (cvs["b_stop"]["oof"][val] <= pick["tau_s"])))
            null.append(selection_edge(sel, ret_val))
        seed_sec = time.time() - t0
    arr = np.asarray([v for v in null if np.isfinite(v)], dtype="float64")
    mean = float(arr.mean()) if arr.size else float("nan")
    sd = float(arr.std(ddof=1)) if arr.size > 1 else float("nan")
    z = float((observed - mean) / sd) if np.isfinite(sd) and sd > 0.0 else float("nan")
    return {"observed_edge": observed, "null_mean": mean, "null_sd": sd,
            "null_edges": [float(v) for v in null], "z": z, "n_seeds": int(arr.size),
            "learner": learner}
