"""WI-044 — L1 learner extension on the winning ``b_hold`` cells (D-024 §2).

Thin driver over :mod:`src.swing_bsh.binary_grid` (**imported, never re-implemented**): the
WI-036 CV loop, purged walk-forward splitter (embargo ``max(20, h)``), 5-seed AUC placebo and
BH-FDR are the *same* code paths. Inside `learner_extension_mode` two in-place overrides are
installed, then restored: the grid narrows to the two top target variants x h in (13, 21, 34,
55) x `b_hold` x 2 markets, and the learner registry gains exactly six models chosen for
thin-positive event data (LightGBM, CatBoost — CPU limits re-imposed on every fit —,
RandomForest, ExtraTrees, an isotonic-calibrated XGB wrapper, and elastic-net logistic).

BH-FDR over this grid alone (m = 96). Outputs: ``reports/wi044_summary.md``, fold pickles
under ``data/models/wi044/`` and a wi044-scoped library manifest (``library_audit`` scan).
Layer 1 only (D-023): predictive stats, no tau grid, no trading claim. Env note: the VPS has
no system libgomp — the venv's ``sitecustomize.py`` preloads the bundled copy; recreate it
after a ``uv sync`` or the LightGBM import fails.

CLI: ``WI044_SMOKE=5 python -m src.swing_bsh.learner_ext --out /tmp/wi044_smoke`` ·
``python -m src.swing_bsh.learner_ext --market ALL``. Core cap 2.0 h.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib
import os
import time
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.swing_bsh import binary_features_ext as ext
from src.swing_bsh import binary_grid, binary_train, library_audit, train
from src.xgb_trainer import PurgedWalkForwardSplit

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "reports"
MODEL_DIR = BASE_DIR / "data" / "models" / "wi044"
REPORT_NAME = "wi044_summary.md"
DEFAULT_SMOKE_DIR, DEFAULT_CACHE_DIR = "/tmp/wi044_smoke", "/tmp/wi036"
SEED, N_JOBS = binary_train.SEED, binary_train.N_JOBS
NEW_LEARNERS: tuple[str, ...] = ("lightgbm", "catboost", "random_forest", "extra_trees",
                                 "xgboost_isotonic", "elasticnet_logistic")
VARIANTS: tuple[str, ...] = ("exact_full_k0.8", "tol2_full_k0.8")
"""The top-2 WI-036 target families (rank 1 and rank 3 of the frozen report)."""
HORIZONS: tuple[int, ...] = (13, 21, 34, 55)
BINARY, MARKETS = "b_hold", ("USD", "CAD")
N_SPLITS, FDR_ALPHA = binary_grid.N_SPLITS, binary_grid.FDR_ALPHA
CORE_HOUR_CAP, CALIB_CV_FOLDS = 2.0, 3
EL_L1_RATIOS: tuple[float, ...] = (0.1, 0.5, 0.9)
LGBM_PARAMS = {"n_estimators": 300, "learning_rate": 0.05, "num_leaves": 31,
               "min_child_samples": 20, "subsample": 0.8, "subsample_freq": 1,
               "colsample_bytree": 0.8, "reg_lambda": 1.0, "random_state": SEED, "n_jobs": N_JOBS}
CATBOOST_PARAMS = {"iterations": 300, "learning_rate": 0.05, "depth": 6, "l2_leaf_reg": 3.0,
                   "random_seed": SEED, "allow_writing_files": False, "thread_count": N_JOBS}
FOREST_PARAMS = {"n_estimators": 300, "min_samples_leaf": 5, "max_features": "sqrt",
                 "class_weight": "balanced_subsample", "random_state": SEED, "n_jobs": N_JOBS}
XGB_ISO_PARAMS = {"n_estimators": 300, "max_depth": 4, "learning_rate": 0.05, "subsample": 0.8,
                  "colsample_bytree": 0.8, "reg_lambda": 1.0, "tree_method": "hist",
                  "random_state": SEED, "n_jobs": N_JOBS}
EL_PARAMS = {"C": 1.0, "max_iter": 400, "random_state": SEED, "l1_ratios": EL_L1_RATIOS}
DEP_MODULES = {"lightgbm": "lightgbm", "catboost": "catboost", "random_forest": "sklearn.ensemble",
               "extra_trees": "sklearn.ensemble", "xgboost_isotonic": "xgboost",
               "elasticnet_logistic": "sklearn.linear_model"}
_CANONICAL_VARIANTS = tuple(ext.variant_grid())
CALIB_STATS: dict[str, dict] = {}
"""Per-cell OOF calibration diagnostics keyed by tag (recording wrapper; cleared on mode exit)."""

__all__ = ["BINARY", "CALIB_STATS", "CORE_HOUR_CAP", "HORIZONS", "MARKETS", "MODEL_DIR",
           "NEW_LEARNERS", "REPORT_NAME", "VARIANTS", "ElasticNetLogistic", "average_uniqueness",
           "build_report", "calibration_stats", "concurrency", "embargo_for", "fdr_m_total",
           "fit_new_learner", "horizon_splitter", "import_learner_deps", "learner_calibration",
           "learner_kwargs", "learner_extension_mode", "main", "new_learner_params",
           "refresh_manifest", "resolve_out_dir", "run_extension"]


def embargo_for(h: int) -> int:
    """``max(20, h)`` via the shared WI-033 floor (never re-derived here)."""
    return train.embargo_for([h])


# --------------------------------------------------------------------------- #
# WI-061 — average-uniqueness sample weights (method variant, no new cell family)
# --------------------------------------------------------------------------- #
def concurrency(t0, h, n: int) -> np.ndarray:
    """Events spanning each bar in ``[0, n)`` (floor 1 where no event covers it)."""
    conc = np.zeros(int(n), dtype="int64")
    for s, hh in zip(np.asarray(t0, dtype="int64").ravel(), np.asarray(h, dtype="int64").ravel()):
        if hh > 0:
            conc[int(s): int(s) + int(hh)] += 1
    return np.maximum(conc, 1)


def average_uniqueness(t0, h, n: int) -> np.ndarray:
    """Mean ``1/concurrency`` over each event's own ``h``-bar span, in ``(0, 1]``.

    Lopez de Prado average uniqueness: events sharing no bar keep weight ``1.0``,
    ``k`` fully overlapping events get ``1/k``. Reads only the event's forward span
    (causal per event); clipped to ``(0, 1]`` and returned as ``float32[m]``.
    """
    t0 = np.asarray(t0, dtype="int64").ravel()
    h = np.asarray(h, dtype="int64").ravel()
    if t0.size == 0:
        return np.zeros(0, dtype="float32")
    conc = concurrency(t0, h, n)
    out = np.ones(t0.size, dtype="float64")
    for i, (s, hh) in enumerate(zip(t0, h)):
        seg = conc[int(s): int(s) + max(int(hh), 0)]
        if seg.size:
            out[i] = float(np.mean(1.0 / seg))
    return np.clip(out, 1e-12, 1.0).astype("float32")


def horizon_splitter(h: int, n_splits: int = N_SPLITS) -> PurgedWalkForwardSplit:
    """The WI-036 purged walk-forward splitter for one horizon."""
    return PurgedWalkForwardSplit(n_splits=n_splits, embargo_td=embargo_for(h))


def fdr_m_total(learners=NEW_LEARNERS, n_markets: int = len(MARKETS)) -> int:
    """BH multiplicity of this grid: 2 variants x 4 h x 1 binary x 6 learners x 2 markets."""
    return len(VARIANTS) * len(HORIZONS) * len(tuple(learners)) * int(n_markets)


def import_learner_deps(learners=NEW_LEARNERS) -> dict:
    """Import each learner's module; a failure names the env fix, not a raw traceback."""
    out = {}
    for name in learners:
        module = DEP_MODULES.get(name)
        if module is None:
            raise ValueError(f"unknown learner: {name}")
        try:
            out[name] = importlib.import_module(module)
        except Exception as exc:  # pragma: no cover - environment-dependent
            raise RuntimeError(
                f"{name}: cannot import {module} ({exc}); this VPS has no system libgomp — the "
                "venv's site-packages/sitecustomize.py must preload the bundled copy after "
                "`uv sync`") from exc
    return out


# --------------------------------------------------------------------------- #
# Six extension learners (CPU-forced; the WI-035 per-fold calibrator still follows)
# --------------------------------------------------------------------------- #
def new_learner_params(cfg: dict | None = None) -> dict[str, dict]:
    """Frozen params for the six learners; the isotonic wrapper inherits `cfg`'s xgb params."""
    out = {"lightgbm": dict(LGBM_PARAMS), "catboost": dict(CATBOOST_PARAMS),
           "random_forest": dict(FOREST_PARAMS), "extra_trees": dict(FOREST_PARAMS),
           "xgboost_isotonic": dict(XGB_ISO_PARAMS), "elasticnet_logistic": dict(EL_PARAMS)}
    if cfg:
        out["xgboost_isotonic"].update(dict(cfg.get("modeling", {}).get("xgb_params") or {}))
    return out


def learner_kwargs(learner: str, params: dict | None = None) -> dict:
    """Constructor kwargs with the hard CPU limits re-imposed (never trusted from the caller)."""
    p = dict(params or {})
    defaults = {"lightgbm": (LGBM_PARAMS, {"objective": "binary", "verbose": -1}),
                "catboost": (CATBOOST_PARAMS, {"verbose": False, "thread_count": N_JOBS}),
                "random_forest": (FOREST_PARAMS, {}), "extra_trees": (FOREST_PARAMS, {}),
                "xgboost_isotonic": (XGB_ISO_PARAMS, {"objective": "binary:logistic",
                                                      "eval_metric": "logloss"}),
                "elasticnet_logistic": (EL_PARAMS, {"l1_ratios": tuple(
                    p.get("l1_ratios", EL_L1_RATIOS))})}
    if learner not in defaults:
        raise ValueError(f"unknown extension learner: {learner}")
    base, forced = defaults[learner]
    kw = {**base, **p, **forced, "n_jobs": N_JOBS}
    if learner in ("catboost", "elasticnet_logistic"):
        kw.pop("n_jobs")  # CatBoost takes `thread_count`; sklearn >=1.8 ignores n_jobs (saga is serial)
    return kw


class ElasticNetLogistic:
    """Elastic-net logistic + the ``l1_ratio`` picked on the fold's calibration block."""

    def __init__(self, model, l1_ratio: float):
        self.model, self.l1_ratio = model, float(l1_ratio)

    def predict_proba(self, X) -> np.ndarray:
        p = np.asarray(self.model.predict_proba(X), dtype="float64")
        return p if p.ndim == 2 else np.column_stack([1.0 - p, p])


def _fit_elasticnet(kw: dict, X_fit, y_fit, X_cal, y_cal, sample_weight=None) -> ElasticNetLogistic:
    """Fit one saga elastic-net per ``l1_ratio``; keep the lowest calibration-block log-loss."""
    from sklearn.metrics import log_loss
    ratios, best, best_ll, best_r = tuple(kw.pop("l1_ratios")), None, np.inf, float(EL_L1_RATIOS[0])
    for r in ratios:
        pipe = Pipeline([("impute", SimpleImputer(strategy="median")),
                         ("scale", StandardScaler()),
                         ("clf", LogisticRegression(solver="saga", l1_ratio=float(r),
                                                    **kw))]).fit(
            X_fit, y_fit, clf__sample_weight=sample_weight)
        ll = float(log_loss(y_cal, pipe.predict_proba(X_cal)[:, 1], labels=[0, 1]))
        if ll < best_ll:
            best, best_ll, best_r = pipe, ll, float(r)
    return ElasticNetLogistic(best, best_r)


def fit_new_learner(learner: str, params: dict, X_fit, y_fit, X_cal, y_cal, sample_weight=None):
    """Fit one extension learner (uncalibrated output — the WI-035 fold calibrator follows).

    WI-061: an optional ``sample_weight`` array (e.g. :func:`average_uniqueness`) is
    forwarded to the underlying estimator's ``fit``; the default ``None`` keeps the
    unweighted WI-044 path unchanged. Weights touch the fit only, never the fold
    calibration block.
    """
    kw = learner_kwargs(learner, params)
    if learner == "lightgbm":
        from lightgbm import LGBMClassifier
        return LGBMClassifier(**kw).fit(X_fit, y_fit, sample_weight=sample_weight)
    if learner == "catboost":
        from catboost import CatBoostClassifier
        return CatBoostClassifier(**kw).fit(X_fit, y_fit, sample_weight=sample_weight)
    if learner in ("random_forest", "extra_trees"):
        cls = RandomForestClassifier if learner == "random_forest" else ExtraTreesClassifier
        return Pipeline([("impute", SimpleImputer(strategy="median")),
                         ("clf", cls(**kw))]).fit(X_fit, y_fit,
                                                  clf__sample_weight=sample_weight)
    if learner == "xgboost_isotonic":
        from sklearn.calibration import CalibratedClassifierCV
        from xgboost import XGBClassifier
        base = XGBClassifier(**kw)
        n_pos = int(np.asarray(y_fit, dtype="int8").sum())
        folds = min(CALIB_CV_FOLDS, n_pos, len(y_fit) - n_pos)
        if folds < 2:
            # Too thin to split internally: the per-fold WI-035 calibrator still calibrates the
            # base fit — no fabricated inner folds, no silently dropped cell.
            return base.fit(X_fit, y_fit, sample_weight=sample_weight)
        return CalibratedClassifierCV(estimator=base, method="isotonic", cv=folds).fit(
            X_fit, y_fit, sample_weight=sample_weight)
    return _fit_elasticnet(kw, X_fit, y_fit, X_cal, y_cal, sample_weight=sample_weight)


def _extended_fit_learner(orig):
    def _wrapped(learner, params, X_fit, y_fit, X_cal, y_cal):
        if learner in NEW_LEARNERS:
            return fit_new_learner(learner, params, X_fit, y_fit, X_cal, y_cal)
        return orig(learner, params, X_fit, y_fit, X_cal, y_cal)
    _wrapped._wi044_wrapped = True
    return _wrapped


def _extended_learner_params(orig):
    def _wrapped(cfg):
        return {**orig(cfg), **new_learner_params(cfg)}
    _wrapped._wi044_wrapped = True
    return _wrapped


# --------------------------------------------------------------------------- #
# OOF calibration diagnostics + in-place grid/registry override
# --------------------------------------------------------------------------- #
def calibration_stats(y, oof) -> dict:
    """OOF prevalence, mean/max probability and Brier score (the L2 tau-mass precheck)."""
    yy, pp = np.asarray(y, dtype="float64"), np.asarray(oof, dtype="float64")
    ok = np.isfinite(pp)
    if ok.sum() < 30 or len(np.unique(yy[ok])) < 2:
        return {}
    pp, yy = np.clip(pp[ok], 0.0, 1.0), yy[ok]
    return {"n": int(ok.sum()), "prevalence": float(yy.mean()), "mean_p": float(pp.mean()),
            "max_p": float(pp.max()), "brier": float(np.mean((pp - yy) ** 2))}


def _recording_cell_cv(orig):
    def _wrapped(*args, **kwargs):
        cv = orig(*args, **kwargs)
        tag = kwargs.get("tag") or (args[7] if len(args) > 7 else None)
        if tag is not None:
            stats = calibration_stats(kwargs.get("y", args[1] if len(args) > 1 else None),
                                      cv["oof"])
            if stats:
                CALIB_STATS[tag] = {**stats, "learner": kwargs.get("learner", args[3]), "tag": tag}
        return cv
    _wrapped._wi044_wrapped = True
    return _wrapped


@contextmanager
def learner_extension_mode(variants=VARIANTS, horizons=HORIZONS, binary=BINARY):
    """Narrow the target grid + widen the learner registry in place, then restore WI-036 state."""
    keep = (ext.HORIZONS, ext.BINARY_COLUMNS, ext.variant_grid, binary_grid.LEARNERS,
            binary_grid.cell_cv, binary_train._fit_learner, binary_train.learner_params)
    want = set(variants)
    ext.HORIZONS = tuple(int(h) for h in horizons)
    ext.BINARY_COLUMNS = (binary,)
    ext.variant_grid = lambda: [v for v in _CANONICAL_VARIANTS if v[0] in want]
    binary_grid.LEARNERS = tuple(binary_grid.LEARNERS) + tuple(NEW_LEARNERS)
    binary_train._fit_learner = _extended_fit_learner(keep[5])
    binary_train.learner_params = _extended_learner_params(keep[6])
    if not getattr(binary_grid.cell_cv, "_wi044_wrapped", False):
        binary_grid.cell_cv = _recording_cell_cv(keep[4])
    try:
        yield
    finally:
        (ext.HORIZONS, ext.BINARY_COLUMNS, ext.variant_grid, binary_grid.LEARNERS,
         binary_grid.cell_cv, binary_train._fit_learner, binary_train.learner_params) = keep
        CALIB_STATS.clear()


# --------------------------------------------------------------------------- #
# Run, report, manifest
# --------------------------------------------------------------------------- #
def run_extension(cfg, markets, *, learners=NEW_LEARNERS, out_dir=REPORTS_DIR, model_dir=MODEL_DIR,
                  limit=None, allow_fixture=False, cache_dir=DEFAULT_CACHE_DIR,
                  core_hours=CORE_HOUR_CAP, placebo_seeds=binary_grid.N_PLACEBO_SEEDS,
                  dry_run=False) -> dict:
    """Score the extension grid per market, placebo-gate, rank, BH-FDR over this grid alone."""
    budget = binary_grid.CoreBudget(core_hours)
    share = max(0.0, budget.cap * (1.0 - binary_grid.PLACEBO_RESERVE)) / max(len(markets), 1)
    results = [binary_grid.run_market(m, cfg, out_dir=out_dir, model_dir=model_dir, limit=limit,
                                      allow_fixture=allow_fixture,
                                      cache_dir=Path(cache_dir) if cache_dir else None,
                                      budget=budget, grid_seconds=share,
                                      placebo_seeds=placebo_seeds, learners=tuple(learners))
               for m in markets]
    n_placebo = binary_grid.run_placebo(results, budget, seeds=placebo_seeds)
    cells = [c for r in results for c in r["cells"]]
    m_total = fdr_m_total(learners, len(markets))
    surv, _thr = binary_grid.bh_fdr([c["p"] for c in cells], alpha=FDR_ALPHA, m_total=m_total)
    for c, s in zip(cells, surv):
        c["fdr"] = bool(s)
    return {"results": results, "cells": cells, "ranking": binary_grid.rank_variants(cells),
            "survivors": pd.DataFrame([c for c in cells if c.get("fdr")]), "n_placebo": n_placebo,
            "m_total": m_total, "dry_run": bool(dry_run), "learners": tuple(learners),
            "core_hours": float(core_hours), "core_sec": round(budget.spent(), 1),
            "calibration": {k: dict(v) for k, v in CALIB_STATS.items()}}


def learner_calibration(stats: dict) -> pd.DataFrame:
    """Per-learner aggregation of the OOF calibration diagnostics (Brier ascending)."""
    df = pd.DataFrame(list(stats.values()))
    if df.empty:
        return df
    return (df.groupby("learner")
              .agg(cells=("tag", "count"), events=("n", "sum"), prevalence=("prevalence", "mean"),
                   mean_p=("mean_p", "mean"), max_p=("max_p", "max"), brier=("brier", "mean"))
              .reset_index().sort_values("brier").reset_index(drop=True))


def build_report(out: dict, path: Path) -> Path:
    """`wi044_summary.md` — ranking, FDR survivors, per-learner OOF calibration reliability."""
    F, res = binary_grid._fmt, out["results"]
    skipped = [t for r in res for t in r["skipped"]]
    cov = ", ".join(f"{r['market']} {r['core_sec']}s" for r in res)
    L = ["# WI-044 — L1 learner extension on the winning `b_hold` cells (D-024 §2)", "",
         f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
         f"- Grid: {', '.join(VARIANTS)} x h in {HORIZONS} x `{BINARY}` x {len(out['learners'])} "
         f"learners ({', '.join(out['learners'])}) x {len(res)} markets; WI-036 machinery imported "
         "unchanged (variant grid, binary set and learner hooks overridden in place, restored "
         "afterwards)",
         f"- CV: {N_SPLITS}-fold `PurgedWalkForwardSplit(embargo_td=max(20, h))`; placebo "
         f"{binary_grid.N_PLACEBO_SEEDS}-seed permutation on the AUC; BH-FDR alpha={FDR_ALPHA} "
         f"over THIS grid only (m={out['m_total']}); core cap {out['core_hours']} h; float32, "
         f"symbol-sequential, `n_jobs={N_JOBS}` (LightGBM/CatBoost CPU limits re-imposed per fit)",
         f"- Coverage: {len(out['cells'])} cells scored, {len(skipped)} truncated by the core "
         f"budget ({cov}); {out['n_placebo']} cells carry a permutation p-value",
         f"- Pickles: `data/models/wi044/<MKT>_<learner>_<variant>_{BINARY}_h<h>_f<fold>.pkl`; "
         "Layer 1 only (D-023): no tau grid, no entry rule — P(hold) reliability is reported for "
         "the L2 tau-mass precheck and nothing else."]
    if out["dry_run"]:
        L.append("- **Smoke/dry run**: symbol-limited; no wi044 pickles, no real report/manifest.")
    L += ["", "## 1. Target ranking — cross-market consistent AUC / rank-IC", "",
          "| rank | variant | best cell (learner/binary/h) | AUC USD | AUC CAD | min AUC | min IC | "
          "median min AUC | cells |",
          "| ---: | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    L += [f"| {i + 1} | `{r['variant']}` | {r['learner']}/{r['binary']}/h{int(r['h'])} | "
          f"{F(r['auc_usd'])} | {F(r['auc_cad'])} | **{F(r['auc_min'])}** | "
          f"{F(r['ic_min'], '{:+.4f}')} | {F(r['auc_min_median'])} | {int(r['n_cells'])} |"
          for i, r in out["ranking"].iterrows()] or \
        ["| — | no cross-market cell pairs completed | | | | | | | |"]
    L += ["", "## 2. FDR survivors (BH alpha=0.05, m over this grid)", "",
          "| market | variant | learner | binary | h | AUC | z | p |",
          "| :--- | :--- | :--- | :--- | ---: | ---: | ---: | ---: |"]
    L += [f"| {s['market']} | `{s['variant']}` | {s['learner']} | {s['binary']} | {int(s['h'])} | "
          f"{F(s['auc'])} | {F(s['z'], '{:+.2f}')} | {F(s['p'], '{:.2e}')} |"
          for _, s in out["survivors"].iterrows()] or ["| — | no cell survived BH-FDR | | | | | | |"]
    cal = learner_calibration(out["calibration"])
    L += ["", "## 3. Per-learner OOF calibration reliability (Brier, ascending)", "",
          "| learner | cells | events | prevalence | mean p̂ | max p̂ | Brier |",
          "| :--- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    L += [f"| {r['learner']} | {int(r['cells'])} | {int(r['events'])} | {F(r['prevalence'])} | "
          f"{F(r['mean_p'])} | {F(r['max_p'])} | {F(r['brier'])} |"
          for _, r in cal.iterrows()] or ["| — | no cell carried OOF diagnostics | | | | | |"]
    L += ["", "## Notes / deviations", "",
          "- Thin driver: `run_market`/`run_placebo`/`rank_variants`/`bh_fdr`/`_fmt` imported and "
          "called unchanged; only the variant grid, the binary set, the learner registry and the "
          "two learner hooks are overridden in place (restored on exit).",
          f"- `xgboost_isotonic` = the WI-036 winner learner under `CalibratedClassifierCV("
          f"method='isotonic', cv<= {CALIB_CV_FOLDS})`; the inner fold count is capped by the "
          "fold's minority class and falls back to the uncalibrated base when it cannot be split "
          "— the per-fold WI-035 calibrator always follows (nested calibration).",
          f"- `elasticnet_logistic` picks `l1_ratio` from {EL_L1_RATIOS} on the fold's calibration "
          "block by log-loss (saga) — the sparse cross-check on the WI-040 attribution.",
          "- Truncated cells are reported as truncated, never dropped; placebo (FDR) runs on the "
          "largest |AUC-0.5| cells first.", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L) + "\n")
    return path


def refresh_manifest(model_dir=MODEL_DIR) -> Path | None:
    """Scan the wi044 pickles into a wi044-scoped manifest (WI-040 row schema, no pooling)."""
    frame = library_audit.scan_library(dirs=[("wi044", Path(model_dir))])
    if frame.empty:
        return None
    path = Path(model_dir) / "manifest.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)
    return path


def resolve_out_dir(out, *, dry_run: bool, reports_dir=REPORTS_DIR, smoke_dir=DEFAULT_SMOKE_DIR) -> Path:
    """A dry run never writes the real report under `reports/`."""
    if out is None:
        return Path(smoke_dir) if dry_run else Path(reports_dir)
    out = Path(out)
    if dry_run and out.resolve() == Path(reports_dir).resolve():
        raise ValueError(f"a dry run may not write the real report ({out})")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="WI-044 L1 learner extension (D-024 §2)")
    parser.add_argument("--market", default="ALL", help="USD | CAD | ALL (default ALL)")
    parser.add_argument("--limit", type=int, default=None, help="Max symbols per market (smoke).")
    parser.add_argument("--out", default=None, help="Output dir (smoke runs use /tmp).")
    parser.add_argument("--allow-fixture", action="store_true")
    parser.add_argument("--placebo-seeds", type=int, default=binary_grid.N_PLACEBO_SEEDS)
    parser.add_argument("--core-hours", type=float, default=CORE_HOUR_CAP)
    parser.add_argument("--learners", default=",".join(NEW_LEARNERS))
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR, help="Shared WI-036 panel cache.")
    args = parser.parse_args(argv)

    smoke = os.environ.get("WI044_SMOKE", "").strip()
    if args.limit is None and smoke.isdigit():
        args.limit = int(smoke)
    if args.out is None and smoke:
        args.out = DEFAULT_SMOKE_DIR
    dry_run = smoke.isdigit() or args.limit is not None
    learners = tuple(s.strip() for s in args.learners.split(",") if s.strip())

    from src.market_cli import cli_markets
    markets = cli_markets(args.market, prog="wi044.learner_ext")
    if markets is None:
        return 2
    out_dir = resolve_out_dir(args.out, dry_run=dry_run)
    model_dir = None if dry_run else MODEL_DIR  # pickles only on a real run
    cfg = train.load_settings()
    t0 = time.time()
    with learner_extension_mode():
        out = run_extension(cfg, markets, learners=learners, out_dir=out_dir, model_dir=model_dir,
                            limit=args.limit, allow_fixture=args.allow_fixture,
                            cache_dir=Path(args.cache_dir), core_hours=args.core_hours,
                            placebo_seeds=args.placebo_seeds, dry_run=dry_run)
        report = build_report(out, out_dir / REPORT_NAME)
        manifest = None if dry_run else refresh_manifest(MODEL_DIR)
    for r in out["results"]:
        print(f"[wi044.ext] {r['market']}: cells={len(r['cells'])} "
              f"skipped={len(r['skipped'])} core={r['core_sec']}s")
    print(f"[wi044.ext] report -> {report} | manifest -> {manifest} | placebo={out['n_placebo']} | "
          f"survivors={len(out['survivors'])} | total {round(time.time() - t0, 1)}s")
    print("[wi044.ext] EXIT:0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
