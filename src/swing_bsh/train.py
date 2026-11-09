"""WI-033 step 1 — swing-conditioned 3-class buy/sell/hold XGB trainer (D-021).

Trains ``XGBClassifier(objective="multi:softprob", tree_method="hist",
n_jobs=2)`` on the WI-032 swing-event frame (states ``at_bottom``/``at_top``,
``k in {1.5, 2.0}``, vertical barriers ``{21, 55}``) inside the purged
walk-forward harness (``embargo_td = max(20, horizon)``) with per-fold
one-vs-rest isotonic calibration and a sigmoid (Platt) fallback whenever a class
has < 25 calibration positives (CB-04).

The frozen fib-rule baseline (WI-028 at-bottom entry + WI-030 exit
``t15_s10_d39_close``) is priced per at-bottom event during the same
symbol-sequential pass and carried as the **non-feature** column ``r_frozen``;
the ADOPT_LOOSE_4OF5 gate lives in :mod:`src.swing_bsh.evaluate`. This module
never writes a model pickle on its own — :func:`save_model` is called by
``evaluate`` only after an ADOPT verdict (WI-033 DoD).

Invariants: ``n_jobs=2``, float32 immediately after calculation,
symbol-sequential reads, per-fold checkpoint JSON.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gc
import importlib.util
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from xgboost import DMatrix, XGBClassifier

from src.feature_engine import compute_features_wi016, iter_market_symbols, wi016_feature_names
from src.swing_bsh.events import BARRIERS, K_VALUES, detect_swings, label_symbol
from src.swing_bsh.probe import prune_features
from src.targets import wilder_atr
from src.xgb_trainer import PurgedWalkForwardSplit, purged_holdout

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
SCRIPTS_DIR = BASE_DIR / "scripts"
CONFIG_PATH = BASE_DIR / "config" / "settings.yaml"

N_JOBS = 2
N_CLASSES = 3
N_SPLITS = 5
EMBARGO_FLOOR = 20
CALIB_FRACTION = 0.20
CB04_MIN_POSITIVES = 25
EARLY_STOPPING_ROUNDS = 30
MIN_DATE = "2016-01-01"
FROZEN_EXIT = ("t15_s10_d39_close", 0.15, 0.10, 39)
"""WI-030 frozen exit: target +15%, stop -10%, 39-day vertical, close entry."""
GATE_K, GATE_H = 1.5, 21
"""Canonical gate geometry: primary k=1.5 / h=21 swing-event rows (evaluate)."""
ENGINEERED = ("state_is_bottom", "k", "horizon")
NON_FEATURE_COLUMNS = frozenset(
    {"symbol", "date", "state", "y", "horizon", "k", "close", "atr", "r_frozen",
     "fold", "p_hold", "p_buy", "p_sell", "pred"}
)

__all__ = [
    "CALIB_FRACTION", "CB04_MIN_POSITIVES", "ENGINEERED", "FROZEN_EXIT", "GATE_H",
    "GATE_K", "N_CLASSES", "N_SPLITS", "NON_FEATURE_COLUMNS", "CalibratedMulti",
    "build_event_panel", "calibration_method", "embargo_for", "engineer",
    "feature_matrix", "fit_calibrated_multiclass", "load_settings", "run_cv",
    "save_model", "train_market",
]


# --------------------------------------------------------------------------- #
# Frozen baseline simulation (WI-023 geometry, imported not reimplemented)
# --------------------------------------------------------------------------- #
_FROZEN_SIM: object | None = None


def _frozen_simulate():
    """`simulate` from `scripts/fib_trade_labels.py` (WI-023) — imported once."""
    global _FROZEN_SIM
    if _FROZEN_SIM is None:
        spec = importlib.util.spec_from_file_location(
            "wi033_fib_trade_labels", SCRIPTS_DIR / "fib_trade_labels.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _FROZEN_SIM = mod.simulate
    return _FROZEN_SIM


def embargo_for(horizons) -> int:
    """`max(20, horizon)` over the panel's vertical barriers (WI-033 §2)."""
    h = np.asarray(list(horizons), dtype="float64")
    finite = h[np.isfinite(h)]
    return int(max(EMBARGO_FLOOR, int(finite.max()) if finite.size else EMBARGO_FLOOR))


def load_settings() -> dict:
    with open(CONFIG_PATH) as fh:
        return yaml.safe_load(fh)


# --------------------------------------------------------------------------- #
# Event panel (WI-032 frame + frozen-rule return)
# --------------------------------------------------------------------------- #
def build_event_panel(
    market: str,
    k_values=K_VALUES,
    barriers=BARRIERS,
    features=None,
    min_date: str = MIN_DATE,
    allow_fixture: bool = False,
    max_symbols: int | None = None,
    frozen_exit=FROZEN_EXIT,
) -> pd.DataFrame:
    """One market's swing-event panel with features and the frozen-rule return.

    Rows follow the WI-032 `sample_events` schema (``symbol, date, state, y,
    horizon``) plus the event geometry (``k``), the raw ``close``/``atr`` and the
    WI-028+WI-030 baseline return ``r_frozen`` (at-bottom rows only, NaN for
    at-top). `r_frozen` is a forward outcome and is never a model feature.
    Symbol-sequential; every computed column is cast to float32.
    """
    feats = list(features) if features is not None else wi016_feature_names()
    simulate = _frozen_simulate()
    _pid, tgt_pct, stop_pct, max_days = frozen_exit
    parts: list[pd.DataFrame] = []
    for i, (symbol, raw) in enumerate(
        iter_market_symbols(market, min_date=min_date, allow_fixture=allow_fixture)
    ):
        if max_symbols is not None and i >= max_symbols:
            break
        g = raw.sort_values("date").reset_index(drop=True)
        fdf = compute_features_wi016(g)
        keep = fdf[[f for f in feats if f in fdf.columns]].assign(
            date=g["date"].to_numpy(),
            close=g["close"].to_numpy(dtype="float32"),
            atr=wilder_atr(g).to_numpy(dtype="float32"),
        )
        o, h, l, c = (g[x].to_numpy(dtype="float64") for x in ("open", "high", "low", "close"))
        rows = []
        for t, state in detect_swings(g):
            if state != "at_bottom":
                continue
            entry = float(c[t])
            ret, _reason, _days = simulate(
                o, h, l, c, t, entry, tgt_pct, entry * (1.0 - stop_pct), max_days, "close"
            )
            rows.append((g["date"].iat[t], ret))
        frozen = (pd.DataFrame(rows, columns=["date", "r_frozen"])
                  if rows else pd.DataFrame(columns=["date", "r_frozen"]))
        if not frozen.empty:
            frozen["date"] = pd.to_datetime(frozen["date"]).astype("datetime64[ns]")
        for k in k_values:
            lab = label_symbol(g, symbol, k, barriers=barriers)
            if lab.empty:
                continue
            m = lab.merge(keep, on="date", how="inner").merge(frozen, on="date", how="left")
            m["k"] = float(k)
            parts.append(m)
        del g, fdf, keep
        if (i + 1) % 50 == 0:
            gc.collect()
    if not parts:
        return pd.DataFrame()
    panel = pd.concat(parts, ignore_index=True)
    for col in panel.columns:
        if col in ("symbol", "date", "state"):
            continue
        panel[col] = pd.to_numeric(panel[col], errors="coerce").astype("float32")
    return panel


def engineer(panel: pd.DataFrame) -> pd.DataFrame:
    """Add the engineered event columns (implied side + barrier geometry)."""
    out = panel.copy()
    out["state_is_bottom"] = (out["state"].to_numpy() == "at_bottom").astype("float32")
    return out


def feature_matrix(panel: pd.DataFrame, kept) -> tuple[np.ndarray, list[str]]:
    """float32 design matrix over the pruned whitelist + engineered columns."""
    feats = [f for f in kept if f in panel.columns] + list(ENGINEERED)
    return panel[feats].to_numpy(dtype="float32"), feats


# --------------------------------------------------------------------------- #
# Calibration (one-vs-rest, CB-04 fallback)
# --------------------------------------------------------------------------- #
def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def calibration_method(n_pos: int, n_total: int, min_pos: int = CB04_MIN_POSITIVES) -> str:
    """`identity` (degenerate class), `isotonic` (enough positives) or `sigmoid`."""
    if n_pos <= 0 or n_pos >= n_total:
        return "identity"
    return "isotonic" if n_pos >= min_pos else "sigmoid"


class CalibratedMulti:
    """3-class model with per-class one-vs-rest calibrators (rows renormalised)."""

    def __init__(self, model: XGBClassifier, calibrators: list, methods: list[str]):
        self.model = model
        self.calibrators = calibrators
        self.methods = methods

    def raw_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        raw = np.asarray(self.model.predict_proba(X), dtype="float64")
        out = np.empty_like(raw)
        for j in range(raw.shape[1]):
            method, cal = self.methods[j], self.calibrators[j]
            if method == "isotonic" and cal is not None:
                out[:, j] = cal.predict(raw[:, j])
            elif method == "sigmoid" and cal is not None:
                out[:, j] = cal.predict_proba(_logit(raw[:, j]).reshape(-1, 1))[:, 1]
            else:
                out[:, j] = raw[:, j]
        out = np.clip(out, 1e-9, None)
        return out / out.sum(axis=1, keepdims=True)

    def contribs(self, X: np.ndarray) -> np.ndarray:
        """TreeSHAP contributions on the margin (multiclass: (n, (f+1)*classes))."""
        best = getattr(self.model, "best_iteration", None)
        it_range = (0, best + 1) if best is not None else (0, 0)
        return self.model.get_booster().predict(
            DMatrix(X), pred_contribs=True, iteration_range=it_range
        )


def fit_calibrated_multiclass(X_fit, y_fit, X_cal, y_cal, params: dict,
                              min_pos: int = CB04_MIN_POSITIVES) -> CalibratedMulti | None:
    """Fit + calibrate the 3-class XGB; `None` when the fit set is single-class."""
    if len(y_fit) == 0 or len(y_cal) == 0 or len(np.unique(y_fit)) < 2:
        return None
    model = XGBClassifier(
        **params, objective="multi:softprob", num_class=N_CLASSES,
        eval_metric="mlogloss", early_stopping_rounds=EARLY_STOPPING_ROUNDS,
    )
    model.fit(X_fit, y_fit, eval_set=[(X_cal, y_cal)], verbose=False)
    raw = np.asarray(model.predict_proba(X_cal), dtype="float64")
    calibrators, methods = [], []
    for j in range(N_CLASSES):
        yj = (y_cal == j).astype("int8")
        method = calibration_method(int(yj.sum()), len(yj), min_pos)
        methods.append(method)
        if method == "isotonic":
            calibrators.append(IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
                               .fit(raw[:, j], yj))
        elif method == "sigmoid":
            calibrators.append(LogisticRegression().fit(_logit(raw[:, j]).reshape(-1, 1), yj))
        else:
            calibrators.append(None)
    return CalibratedMulti(model, calibrators, methods)


# --------------------------------------------------------------------------- #
# Cross-validation
# --------------------------------------------------------------------------- #
def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str))


def run_cv(X, y, dates, params: dict, splitter: PurgedWalkForwardSplit,
           calib_fraction: float = CALIB_FRACTION, min_pos: int = CB04_MIN_POSITIVES,
           checkpoint_path: Path | None = None, label: str = "cv"):
    """Purged walk-forward CV -> (oof_proba (n,3), fold_id, fold stats)."""
    oof = np.full((len(y), N_CLASSES), np.nan)
    fold_id = np.full(len(y), -1, dtype="int16")
    stats: list[dict] = []
    for k, (tr, va) in enumerate(splitter.split(dates)):
        fit_i, cal_i = purged_holdout(dates, tr, calib_fraction, splitter.embargo_td)
        if len(fit_i) == 0 or len(cal_i) == 0:
            stats.append({"fold": k, "skipped": "empty fit/calibration set"})
            continue
        t0 = time.time()
        m = fit_calibrated_multiclass(X[fit_i], y[fit_i], X[cal_i], y[cal_i], params, min_pos)
        if m is None:
            stats.append({"fold": k, "skipped": "degenerate class set"})
            continue
        oof[va] = m.predict_proba(X[va])
        fold_id[va] = k
        stats.append({
            "fold": k, "n_fit": int(len(fit_i)), "n_calib": int(len(cal_i)),
            "n_val": int(len(va)),
            "class_counts": {int(c): int((y[va] == c).sum()) for c in range(N_CLASSES)},
            "calibration": list(m.methods),
            "best_iteration": int(getattr(m.model, "best_iteration", -1) or -1),
            "max_train_date": str(pd.Timestamp(dates[tr].max()).date()),
            "min_val_date": str(pd.Timestamp(dates[va].min()).date()),
            "wall_sec": round(time.time() - t0, 1),
        })
        if checkpoint_path is not None:
            _write_json(checkpoint_path, {"label": label, "folds": stats})
    return oof, fold_id, stats


# --------------------------------------------------------------------------- #
# Market driver
# --------------------------------------------------------------------------- #
def train_market(market: str, cfg: dict, *, k_values=K_VALUES, barriers=BARRIERS,
                 min_date: str = MIN_DATE, allow_fixture: bool = False,
                 max_symbols: int | None = None, n_splits: int = N_SPLITS,
                 calib_fraction: float = CALIB_FRACTION, min_pos: int = CB04_MIN_POSITIVES,
                 checkpoint_dir: Path = DATA_DIR) -> dict:
    """Build the event panel, run CV + the final fit; return OOF + model in memory."""
    t0 = time.time()
    panel = build_event_panel(market, k_values=k_values, barriers=barriers,
                              min_date=min_date, allow_fixture=allow_fixture,
                              max_symbols=max_symbols)
    if panel.empty:
        raise RuntimeError(f"no swing events for market={market}")
    kept, dropped = prune_features(panel, wi016_feature_names())
    panel = engineer(panel)
    X, feats = feature_matrix(panel, kept)
    y = panel["y"].to_numpy(dtype="int8")
    dates = panel["date"].to_numpy()
    embargo = embargo_for(panel["horizon"].to_numpy())
    params = dict(cfg["modeling"]["xgb_params"])
    params.update({"n_jobs": N_JOBS, "tree_method": "hist"})
    splitter = PurgedWalkForwardSplit(n_splits=n_splits, embargo_td=embargo)

    checkpoint = Path(checkpoint_dir) / f"wi033_checkpoint_{market}.json"
    oof, fold_id, stats = run_cv(X, y, dates, params, splitter, calib_fraction, min_pos,
                                 checkpoint_path=checkpoint, label=f"wi033_{market}")

    all_idx = np.arange(len(y))
    fit_i, cal_i = purged_holdout(dates, all_idx, calib_fraction, embargo)
    final = fit_calibrated_multiclass(X[fit_i], y[fit_i], X[cal_i], y[cal_i], params, min_pos)

    oof_df = panel[["symbol", "date", "state", "k", "horizon", "y", "close", "atr",
                    "r_frozen"]].copy()
    oof_df["fold"] = fold_id
    for j, name in enumerate(("p_hold", "p_buy", "p_sell")):
        oof_df[name] = oof[:, j].astype("float32")
    finite = np.isfinite(oof).all(axis=1)
    oof_df["pred"] = np.where(finite, np.nanargmax(np.where(finite[:, None], oof, -np.inf), axis=1), -1)
    oof_df["pred"] = oof_df["pred"].astype("int8")

    shap_top: dict[str, float] = {}
    if final is not None:
        sub = np.random.default_rng(0).choice(len(X), size=min(20000, len(X)), replace=False)
        # pred_contribs is (n, classes, features + bias) for multi:softprob.
        contrib = np.abs(final.contribs(X[sub]))[:, :, : len(feats)]
        share = contrib.sum(axis=(0, 1))
        share = share / (share.sum() + 1e-12)
        shap_top = dict(sorted(zip(feats, map(float, share)), key=lambda kv: kv[1], reverse=True))

    result = {
        "market": market,
        "n_rows": int(len(y)),
        "n_symbols": int(pd.Series(panel["symbol"]).nunique()),
        "features": feats,
        "n_features_pruned": len(kept),
        "n_features_input": len(wi016_feature_names()),
        "embargo_td": embargo,
        "k_values": [float(k) for k in k_values],
        "barriers": [int(h) for h in barriers],
        "params": params,
        "folds": stats,
        "oof": oof_df,
        "X": X, "y": y, "dates": dates, "splitter": splitter,
        "final_model": final,
        "final_meta": None if final is None else {
            "calibration": list(final.methods),
            "best_iteration": int(getattr(final.model, "best_iteration", -1) or -1),
            "n_fit": int(len(fit_i)), "n_calib": int(len(cal_i)),
        },
        "shap_importance": shap_top,
        "runtime_sec": round(time.time() - t0, 1),
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    del panel
    gc.collect()
    return result


def save_model(result: dict, model_dir: Path = MODELS_DIR / "swing_bsh") -> Path:
    """Pickle the calibrated final model with provenance (call ONLY on ADOPT)."""
    if result.get("final_model") is None:
        raise RuntimeError("no final model to save")
    model_dir.mkdir(parents=True, exist_ok=True)
    path = Path(model_dir) / f"{result['market']}.pkl"
    provenance = {k: result[k] for k in
                  ("market", "n_rows", "n_symbols", "features", "embargo_td",
                   "k_values", "barriers", "generated_utc", "final_meta")}
    provenance["frozen_exit"] = FROZEN_EXIT[0]
    with open(path, "wb") as fh:
        pickle.dump({"model": result["final_model"], "features": result["features"],
                     "provenance": provenance}, fh)
    return path


def main(argv: list[str] | None = None) -> int:
    """Train-only CLI (never writes a model pickle — the gate lives in evaluate)."""
    parser = argparse.ArgumentParser(description="WI-033 swing-conditioned 3-class trainer")
    parser.add_argument("--market", default="CAD")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", default="/tmp/wi033_train")
    parser.add_argument("--allow-fixture", action="store_true")
    args = parser.parse_args(argv)
    cfg = load_settings()
    out = Path(args.out)
    res = train_market(args.market, cfg, allow_fixture=args.allow_fixture,
                       max_symbols=args.limit, checkpoint_dir=out)
    res["oof"].to_parquet(out / f"wi033_oof_{args.market}.parquet", index=False)
    print(f"[wi033.train] {res['market']}: {res['n_rows']} events, {len(res['features'])} features, "
          f"embargo {res['embargo_td']}")
    print(f"[wi033.train] oof -> {out / f'wi033_oof_{args.market}.parquet'} | "
          f"runtime {res['runtime_sec']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
