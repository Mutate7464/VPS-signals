"""Sprint 4 — Purged walk-forward XGBoost trainer (4 targets x {USD, CAD}).

Per market and target:
  1. Rebuild the point-in-time panel from raw OHLCV (features -> stationarity
     transform -> date-grouped `_cs_pct` ranks), using the Gate 3 catalog's
     whitelist for that target.
  2. 5-fold `PurgedWalkForwardSplit(embargo_td=20)` over unique dates. Inside
     each training fold, the last 20% of dates (again purged by the embargo)
     are held out for early stopping + probability calibration.
  3. `XGBClassifier(tree_method="hist", n_jobs=2)` with per-fold
     `scale_pos_weight`; isotonic calibration, falling back to sigmoid (Platt)
     when the calibration set has < 25 positives (CB-04).
  4. Placebo runs: the same CV on randomly permuted labels (N seeds).
  5. Final model on all labeled dates, saved to `models/{usd|cad}/`; TreeSHAP
     contributions (XGBoost `pred_contribs`) for global importance and the #1
     local driver per ticker at the latest date T.

Outputs:
  data/oof_{MKT}.parquet               out-of-fold + placebo predictions
  data/train_meta_{MKT}.json           fold stats, calibration, SHAP importance
  data/predictions_{MKT}_latest.parquet  latest-date probabilities + SHAP drivers
  models/{mkt}/{target}.pkl            calibrated final models

CLI:
    python -m src.xgb_trainer --market USD --embargo 20 --n-splits 5
"""

from __future__ import annotations

import argparse
import datetime as dt
import gc
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
from sklearn.metrics import average_precision_score
from xgboost import DMatrix, XGBClassifier

from src.feature_engine import compute_features, load_market_frame
from src.stat_metadata import add_cs_percentile, apply_stationarity_transform
from src.state_manager import init_dirs, log_telemetry, update_state
from src.targets import TARGET_COLUMNS, compute_targets, wilder_atr

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = BASE_DIR / "config" / "settings.yaml"
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

N_JOBS = 2  # Hard-pinned for the 2 vCPU VPS; never -1.
INITIAL_TRAIN_FRACTION = 0.40
CALIB_FRACTION = 0.20
CB04_MIN_POSITIVES = 25
N_PLACEBO_SEEDS = 5
EARLY_STOPPING_ROUNDS = 30

TARGET_HORIZON = {"y_15d_high": 15, "y_15d_low": 15, "y_20d_up": 20, "y_20d_down": 20}
# Sign that maps each target onto "realized forward ATR return in the predicted direction".
TARGET_DIRECTION = {"y_15d_high": -1, "y_15d_low": 1, "y_20d_up": 1, "y_20d_down": -1}
PROB_COLUMN = {
    "y_15d_high": "p_15d_high",
    "y_15d_low": "p_15d_low",
    "y_20d_up": "p_20d_up",
    "y_20d_down": "p_20d_down",
}


# --------------------------------------------------------------------------- #
# Purged walk-forward split
# --------------------------------------------------------------------------- #
class PurgedWalkForwardSplit:
    """Expanding-window walk-forward split over unique dates with an embargo.

    The first `initial_train_fraction` of dates is train-only; the remainder is
    cut into `n_splits` contiguous validation blocks. For each block, training
    dates within `embargo_td` trading days of the block start are purged, so
    `max(train_date_pos) + embargo_td < min(val_date_pos)` always holds.
    """

    def __init__(self, n_splits: int = 5, embargo_td: int = 20, initial_train_fraction: float = INITIAL_TRAIN_FRACTION):
        self.n_splits = n_splits
        self.embargo_td = embargo_td
        self.initial_train_fraction = initial_train_fraction

    def split(self, dates):
        dates = np.asarray(pd.to_datetime(pd.Series(dates)).to_numpy())
        uniq = np.unique(dates)
        pos = np.searchsorted(uniq, dates)
        start = int(len(uniq) * self.initial_train_fraction)
        bounds = np.linspace(start, len(uniq), self.n_splits + 1).astype(int)
        for k in range(self.n_splits):
            v0, v1 = bounds[k], bounds[k + 1]
            train_end = v0 - self.embargo_td  # exclusive
            if train_end <= 0 or v1 <= v0:
                continue
            train_idx = np.where(pos < train_end)[0]
            val_idx = np.where((pos >= v0) & (pos < v1))[0]
            yield train_idx, val_idx


def purged_holdout(dates: np.ndarray, idx: np.ndarray, frac: float, embargo_td: int):
    """Split `idx` into (fit, calib): calib = last `frac` of dates, fit purged by the embargo."""
    d = dates[idx]
    uniq = np.unique(d)
    cut = int(len(uniq) * (1.0 - frac))
    pos = np.searchsorted(uniq, d)
    return idx[pos < cut - embargo_td], idx[pos >= cut]


# --------------------------------------------------------------------------- #
# Calibrated model
# --------------------------------------------------------------------------- #
def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


class CalibratedXGB:
    def __init__(self, model: XGBClassifier, calibrator, method: str):
        self.model = model
        self.calibrator = calibrator
        self.method = method

    def raw_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)[:, 1]

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        raw = self.raw_proba(X)
        if self.method == "isotonic":
            return self.calibrator.predict(raw)
        return self.calibrator.predict_proba(_logit(raw).reshape(-1, 1))[:, 1]

    def contribs(self, X: np.ndarray) -> np.ndarray:
        """TreeSHAP contributions on the margin (last column = bias)."""
        best = getattr(self.model, "best_iteration", None)
        it_range = (0, best + 1) if best is not None else (0, 0)
        return self.model.get_booster().predict(DMatrix(X), pred_contribs=True, iteration_range=it_range)


def load_settings() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def xgb_params(cfg: dict) -> dict:
    params = dict(cfg["modeling"]["xgb_params"])
    params["n_jobs"] = N_JOBS
    params["tree_method"] = "hist"
    return params


def fit_calibrated(X_fit, y_fit, X_cal, y_cal, params: dict):
    pos, neg = int(y_fit.sum()), int(len(y_fit) - y_fit.sum())
    cal_pos = int(y_cal.sum())
    if pos == 0 or neg == 0 or cal_pos == 0 or cal_pos == len(y_cal):
        return None
    model = XGBClassifier(
        **params,
        scale_pos_weight=neg / pos,
        eval_metric="logloss",
        early_stopping_rounds=EARLY_STOPPING_ROUNDS,
    )
    model.fit(X_fit, y_fit, eval_set=[(X_cal, y_cal)], verbose=False)
    raw_cal = model.predict_proba(X_cal)[:, 1]

    # CB-04: isotonic needs enough positives; otherwise parametric Platt scaling.
    if cal_pos >= CB04_MIN_POSITIVES:
        calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(raw_cal, y_cal)
        method = "isotonic"
    else:
        calibrator = LogisticRegression().fit(_logit(raw_cal).reshape(-1, 1), y_cal)
        method = "sigmoid"
    return CalibratedXGB(model, calibrator, method)


# --------------------------------------------------------------------------- #
# Panel
# --------------------------------------------------------------------------- #
def load_catalog(market: str) -> dict:
    return json.loads((DATA_DIR / f"metadata_catalog_{market}.json").read_text())


def build_panel(market: str, catalog: dict) -> pd.DataFrame:
    raw = load_market_frame(market)
    parts = []
    for sym, g in raw.groupby("symbol", sort=False):
        g = g.sort_values("date").reset_index(drop=True)
        f = pd.concat([compute_features(g), compute_targets(g)], axis=1)
        close = g["close"].astype("float64").to_numpy()
        atr = wilder_atr(g).astype("float64").to_numpy()
        for h in (15, 20):
            fwd = np.full(len(close), np.nan)
            if len(close) > h:
                fwd[:-h] = close[h:]
            f[f"fwd_atr_ret_{h}"] = ((fwd - close) / (atr + 1e-12)).astype("float32")
        f["close"] = close.astype("float32")
        f["symbol"] = sym
        f["market"] = market
        parts.append(f)
    panel = pd.concat(parts, ignore_index=True)

    surviving = catalog["surviving_features"]
    flagged = [c for c in surviving if catalog["stationarity"].get(c, {}).get("flagged")]
    panel = apply_stationarity_transform(panel, flagged)
    panel = add_cs_percentile(panel, surviving)
    for c in surviving + [f"{c}_cs_pct" for c in surviving]:
        panel[c] = panel[c].astype("float32")
    return panel


def target_features(catalog: dict, target: str) -> list[str]:
    wl = catalog["whitelist_per_target"][target]
    return wl + [f"{c}_cs_pct" for c in wl]


# --------------------------------------------------------------------------- #
# Cross-validation
# --------------------------------------------------------------------------- #
def _safe_ap(y: np.ndarray, p: np.ndarray) -> float:
    if len(y) == 0 or y.min() == y.max():
        return float("nan")
    return float(average_precision_score(y, p))


def run_cv(X: np.ndarray, y: np.ndarray, dates: np.ndarray, params: dict, splitter: PurgedWalkForwardSplit):
    oof = np.full(len(y), np.nan)
    fold_id = np.full(len(y), -1, dtype="int16")
    stats = []
    for k, (tr, va) in enumerate(splitter.split(dates)):
        fit_i, cal_i = purged_holdout(dates, tr, CALIB_FRACTION, splitter.embargo_td)
        if len(fit_i) == 0 or len(cal_i) == 0:
            continue
        m = fit_calibrated(X[fit_i], y[fit_i], X[cal_i], y[cal_i], params)
        if m is None:
            stats.append({"fold": k, "skipped": "single-class fit/calibration set"})
            continue
        oof[va] = m.predict_proba(X[va])
        fold_id[va] = k
        stats.append({
            "fold": k,
            "n_fit": int(len(fit_i)),
            "n_calib": int(len(cal_i)),
            "n_val": int(len(va)),
            "train_pos_rate": float(y[fit_i].mean()),
            "train_pr_auc": _safe_ap(y[fit_i], m.predict_proba(X[fit_i])),
            "val_pr_auc": _safe_ap(y[va], oof[va]),
            "calibration": m.method,
            "best_iteration": int(getattr(m.model, "best_iteration", -1) or -1),
            "max_train_date": str(pd.Timestamp(dates[tr].max()).date()),
            "min_val_date": str(pd.Timestamp(dates[va].min()).date()),
        })
    return oof, fold_id, stats


# --------------------------------------------------------------------------- #
# Market driver
# --------------------------------------------------------------------------- #
def train_market(market: str, cfg: dict, n_splits: int, embargo_td: int) -> dict:
    t0 = time.time()
    catalog = load_catalog(market)
    params = xgb_params(cfg)
    splitter = PurgedWalkForwardSplit(n_splits=n_splits, embargo_td=embargo_td)

    panel = build_panel(market, catalog)
    latest_date = panel["date"].max()
    labeled = panel.dropna(subset=TARGET_COLUMNS).reset_index(drop=True)
    infer = panel[panel["date"] == latest_date].reset_index(drop=True)
    dates = labeled["date"].to_numpy()

    oof = labeled[["date", "symbol", "close", "fwd_atr_ret_15", "fwd_atr_ret_20"]].copy()
    preds = infer[["date", "symbol"]].copy()
    meta = {
        "market": market,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "n_splits": n_splits,
        "embargo_td": embargo_td,
        "n_placebo_seeds": N_PLACEBO_SEEDS,
        "latest_date": str(pd.Timestamp(latest_date).date()),
        "targets": {},
    }

    model_dir = MODELS_DIR / market.lower()
    model_dir.mkdir(parents=True, exist_ok=True)

    for target in TARGET_COLUMNS:
        feats = target_features(catalog, target)
        X = labeled[feats].to_numpy(dtype="float32")
        y = labeled[target].to_numpy().astype("int8")

        # Real out-of-fold predictions.
        p, fold, stats = run_cv(X, y, dates, params, splitter)
        oof[f"y_{target}"] = y
        oof[f"p_{target}"] = p.astype("float32")
        oof[f"fold_{target}"] = fold

        # Placebo: identical pipeline on permuted labels.
        for s in range(N_PLACEBO_SEEDS):
            y_pl = np.random.default_rng(1000 + s).permutation(y)
            p_pl, _, _ = run_cv(X, y_pl, dates, params, splitter)
            oof[f"y_{target}_pl{s}"] = y_pl
            oof[f"p_{target}_pl{s}"] = p_pl.astype("float32")

        # Final model on all labeled dates.
        all_idx = np.arange(len(y))
        fit_i, cal_i = purged_holdout(dates, all_idx, CALIB_FRACTION, embargo_td)
        final = fit_calibrated(X[fit_i], y[fit_i], X[cal_i], y[cal_i], params)

        tmeta = {"features": feats, "folds": stats, "final_model": None}
        if final is not None:
            with open(model_dir / f"{target}.pkl", "wb") as fh:
                pickle.dump({"model": final, "features": feats, "market": market, "target": target}, fh)

            contrib = final.contribs(X)[:, :-1]
            mean_abs = np.abs(contrib).mean(axis=0)
            share = mean_abs / (mean_abs.sum() + 1e-12)
            tmeta["final_model"] = {
                "path": str((model_dir / f"{target}.pkl").relative_to(BASE_DIR)),
                "calibration": final.method,
                "best_iteration": int(getattr(final.model, "best_iteration", -1) or -1),
                "n_fit": int(len(fit_i)),
                "n_calib": int(len(cal_i)),
            }
            tmeta["shap_importance"] = dict(
                sorted(zip(feats, map(float, share)), key=lambda kv: kv[1], reverse=True)
            )

            Xi = infer[feats].to_numpy(dtype="float32")
            preds[PROB_COLUMN[target]] = final.predict_proba(Xi).astype("float32")
            local = final.contribs(Xi)[:, :-1]
            order = np.argsort(-np.abs(local), axis=1)
            preds[f"top_driver_{target}"] = [feats[o[0]] for o in order]
            preds[f"top3_{target}"] = [
                "; ".join(f"{feats[j]}={local[i, j]:+.3f}" for j in o[:3]) for i, o in enumerate(order)
            ]
        else:
            preds[PROB_COLUMN[target]] = np.nan

        meta["targets"][target] = tmeta
        gc.collect()

    preds["exit_urgency"] = preds[["p_15d_high", "p_20d_down"]].max(axis=1)

    oof.to_parquet(DATA_DIR / f"oof_{market}.parquet", index=False)
    preds.to_parquet(DATA_DIR / f"predictions_{market}_latest.parquet", index=False)
    (DATA_DIR / f"train_meta_{market}.json").write_text(json.dumps(meta, indent=2))

    elapsed = time.time() - t0
    log_telemetry(f"xgb_trainer_{market}", "SUCCESS", elapsed, {"rows": int(len(labeled))})
    print(f"[xgb_trainer] {market}: {len(labeled)} labeled rows, 4 targets, "
          f"{N_PLACEBO_SEEDS} placebo seeds, {elapsed:.1f}s")
    return meta


def main() -> int:
    init_dirs()
    cfg = load_settings()
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", choices=["USD", "CAD", "ALL"], default="ALL")
    parser.add_argument("--embargo", type=int, default=cfg["modeling"]["embargo_td"])
    parser.add_argument("--n-splits", type=int, default=cfg["modeling"]["n_splits"])
    args = parser.parse_args()

    markets = ["USD", "CAD"] if args.market == "ALL" else [args.market]
    for mkt in markets:
        train_market(mkt, cfg, args.n_splits, args.embargo)
    update_state("EP-04", "training", {"markets": markets, "embargo_td": args.embargo, "n_splits": args.n_splits})
    return 0


if __name__ == "__main__":
    sys.exit(main())
