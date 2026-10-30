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
import re
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

from src.feature_engine import compute_features, iter_market_symbols, load_market_frame, load_quarantine
from src.run_logging import (
    MemoryGuardError,
    check_memory,
    log_phase,
    rss_mb,
    setup_logging,
    xgb_callback,
)
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

# WI-009's flat embargo floor (trading days). A per-target embargo never goes
# below this, but grows to cover the label horizon (D-016 precondition fix):
# a forward label spanning `horizon` bars cannot straddle a fold boundary.
EMBARGO_FLOOR_TD = 20

TARGET_HORIZON = {"y_15d_high": 15, "y_15d_low": 15, "y_20d_up": 20, "y_20d_down": 20}
# Sign that maps each target onto "realized forward ATR return in the predicted direction".
TARGET_DIRECTION = {"y_15d_high": -1, "y_15d_low": 1, "y_20d_up": 1, "y_20d_down": -1}
PROB_COLUMN = {
    "y_15d_high": "p_15d_high",
    "y_15d_low": "p_15d_low",
    "y_20d_up": "p_20d_up",
    "y_20d_down": "p_20d_down",
    "y_20d_stay": "p_20d_stay",
}

# exit_urgency = max P(event) over the four *event* targets. y_20d_stay (added
# 2026-10-25) is a do-nothing band, deliberately excluded from this max.
EVENT_PROB_COLUMNS = ("p_15d_high", "p_15d_low", "p_20d_up", "p_20d_down")


# --------------------------------------------------------------------------- #
# Horizon-specific embargo (D-016 precondition fix)
# --------------------------------------------------------------------------- #
def horizon_embargo(horizon: int, floor: int = EMBARGO_FLOOR_TD) -> int:
    """Per-target embargo = `max(floor, horizon)`.

    A forward label spanning `horizon` trading days cannot straddle a fold
    boundary, so the purge must cover at least the label horizon. The WI-009
    flat 20-bar floor is retained for short targets.
    """
    return int(max(int(floor), int(horizon)))


def target_horizon(target: str) -> int:
    """Label horizon for a target column.

    Mapping first (`TARGET_HORIZON`), then a `y_<N>d_*` name parse so targets
    added by future work items (e.g. the WI-016 fib-ladder names) resolve their
    own horizon instead of silently inheriting the flat floor.
    """
    if target in TARGET_HORIZON:
        return int(TARGET_HORIZON[target])
    m = re.match(r"^y_(\d+)d", str(target))
    if m:
        return int(m.group(1))
    raise KeyError(f"no horizon known for target {target!r}")


def resolve_embargo(target: str, cli_embargo: int | None = None) -> int:
    """Effective per-target embargo for `target`.

    An explicit CLI/config value may only *strengthen* the per-target horizon
    embargo — the flat default (20) can never weaken it, so `--embargo 20` on a
    144-bar target still yields 144.
    """
    configured = int(cli_embargo) if cli_embargo is not None else EMBARGO_FLOOR_TD
    return max(configured, horizon_embargo(target_horizon(target)))



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


def _load_persisted_artifacts(market: str) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """Load the persisted Sprint-2 features/targets parquets, or (None, None)."""
    f_path = DATA_DIR / "features" / f"features_{market}.parquet"
    t_path = DATA_DIR / "features" / f"targets_{market}.parquet"
    if not (f_path.exists() and t_path.exists()):
        return None, None
    try:
        f_all = pd.read_parquet(f_path)
        t_all = pd.read_parquet(t_path)
    except Exception:
        return None, None
    return f_all, t_all


def build_panel(
    market: str, catalog: dict, allow_fixture: bool = False, min_date: str | None = None,
    recompute_features: bool = False,
) -> pd.DataFrame:
    """Build the panel using streaming symbol iteration.

    Default path: JOIN the persisted Sprint-2 `features_{mkt}.parquet` /
    `targets_{mkt}.parquet` on (symbol, date) and compute only `close` +
    `fwd_atr_ret_{15,20}` from raw (fast — no rolling.apply). This removes the
    ~4 h full feature recompute measured in the E2 run (plan WI-002 E3–E5,
    Step 3). `--recompute-features` (or fixture runs) falls back to the legacy
    in-loop `compute_features()` path. The persisted parquets must have been
    built with `min_date` <= the trainer's `min_date`.

    Per symbol: keep only *surviving* feature columns plus labels,
    fwd_atr_ret columns and identifiers.  Casts float32 immediately.
    `symbol` is stored as a category column.
    """
    surviving = catalog["surviving_features"]
    flagged = [c for c in surviving if catalog["stationarity"].get(c, {}).get("flagged")]

    use_join = (not recompute_features) and (not allow_fixture)
    f_all = t_all = None
    if use_join:
        f_all, t_all = _load_persisted_artifacts(market)
        if f_all is None or any(c not in f_all.columns for c in surviving):
            use_join = False
            f_all = t_all = None
            print(f"[xgb_trainer] persisted features/targets unavailable or stale for {market}; "
                  "falling back to in-loop feature computation")

    parts: list[pd.DataFrame] = []
    sym_count = 0
    for symbol, raw_df in iter_market_symbols(market, min_date=min_date, allow_fixture=allow_fixture):
        sym_count += 1
        g = raw_df.sort_values("date").reset_index(drop=True)

        close = g["close"].astype("float64").to_numpy()
        atr = wilder_atr(g).astype("float64").to_numpy()
        base = pd.DataFrame({"date": g["date"]})
        for h in (15, 20):
            fwd = np.full(len(close), np.nan)
            if len(close) > h:
                fwd[:-h] = close[h:]
            base[f"fwd_atr_ret_{h}"] = ((fwd - close) / (atr + 1e-12)).astype("float32")
        base["close"] = close.astype("float32")
        base_cols = ["fwd_atr_ret_15", "fwd_atr_ret_20", "close"]

        if use_join:
            f_sub = f_all[f_all["symbol"] == symbol]
            feat_cols_all = [c for c in f_all.columns if c not in ("date", "symbol", "market")]
            f_sub = f_sub[["date"] + feat_cols_all]
            t_sub = t_all[t_all["symbol"] == symbol][["date"] + TARGET_COLUMNS]
            combined = (
                base.merge(f_sub, on="date", how="inner")
                .merge(t_sub, on="date", how="inner")
            )
            combined["symbol"] = symbol
            combined["market"] = market
            if len(combined) < 0.98 * len(f_sub):
                print(f"[xgb_trainer] WARN: {symbol}: join kept {len(combined)}/{len(f_sub)} "
                      "feature rows — persisted parquets may be stale vs min_date")
        else:
            f = compute_features(g)
            # Keep the full feature matrix (E3 ablation masks select subsets later)
            t = compute_targets(g)
            combined = pd.concat([f, t], axis=1)
            combined["symbol"] = symbol
            combined["market"] = market
            for c in base_cols:
                combined[c] = base[c].to_numpy()

        # Trim to min_date (data was read from min_date-250d for warmup)
        if min_date is not None:
            combined = combined[combined["date"] >= pd.Timestamp(min_date)]

        # Drop rows where any target is NaN
        combined = combined.dropna(subset=TARGET_COLUMNS)
        if len(combined) > 0:
            parts.append(combined)

        del g, combined
        if sym_count % 50 == 0:
            gc.collect()

    if f_all is not None:
        del f_all, t_all
        gc.collect()

    if not parts:
        raise RuntimeError(f"No labeled rows for market={market}")

    panel = pd.concat(parts, ignore_index=True)
    del parts
    gc.collect()

    panel = apply_stationarity_transform(panel, [f for f in surviving if f in flagged])
    panel = add_cs_percentile(panel, surviving)

    # Ensure float32 on all feature columns
    for c in surviving + [f"{c}_cs_pct" for c in surviving]:
        if c in panel.columns:
            panel[c] = panel[c].astype("float32")

    # symbol as category (memory-efficient)
    panel["symbol"] = panel["symbol"].astype("category")
    gc.collect()

    return panel


def target_features(
    catalog: dict, target: str, feature_set: str = "full",
    panel_cols: set[str] | None = None,
) -> list[str]:
    """Feature columns for a target under an E3 ablation mask.

    full        — the Gate-3 whitelist for the target (E2-faithful baseline)
    no_static   — whitelist minus ADF-flagged (non-stationary) features
    fib_only    — all Fibonacci-window range features present in the panel
    legacy19    — union of the E2-era whitelists (VIF-5 / MI-30 catalog)
    cs_pct_only — whitelist features, cross-sectional percentile ranks only
    """
    cols = panel_cols if panel_cols is not None else set()
    if target not in catalog["whitelist_per_target"]:
        # y_20d_stay (added 2026-10-25) has no Gate-3 whitelist entry yet — a
        # Sprint-3 metadata pass is WI-009c work. Fall back to the full panel so
        # trainer loops resolve non-empty instead of KeyError (WI-009b lesson:
        # masks must resolve, never silently-empty).
        import logging

        logging.getLogger("xgb_trainer").warning(
            "[xgb_trainer] no Gate-3 whitelist for target '%s' — using all panel features", target
        )
        wl = sorted(cols) if cols else None
        if wl is None:
            raise KeyError(target)  # no panel columns either: genuinely unusable
    else:
        wl = catalog["whitelist_per_target"][target]

    def _existing(names: list[str]) -> list[str]:
        return [f for f in names if cols is None or f in cols]

    if feature_set == "no_static":
        base = [f for f in wl if not catalog["stationarity"].get(f, {}).get("flagged")]
    elif feature_set == "fib_only":
        from src.feature_engine import FIB_FEATURE_NAMES
        base = _existing(FIB_FEATURE_NAMES)
    elif feature_set == "legacy19":
        base = _existing(LEGACY_WHITELIST_UNION)
    elif feature_set == "cs_pct_only":
        base = _existing(wl)
        return [f"{f}_cs_pct" for f in base]
    else:  # full
        base = _existing(wl)
    return base + [f"{f}_cs_pct" for f in base if cols is None or f"{f}_cs_pct" in cols]


LEGACY_WHITELIST_UNION = [
    "adx_100", "adx_20", "adx_5", "amihud_10", "amihud_20", "amihud_50",
    "atr_pct_100", "bb_width_10", "bb_width_5", "entropy_10", "entropy_20",
    "frac_diff_close", "hurst_20", "kama_er_10", "kama_er_100", "kama_er_20",
    "kama_er_5", "kama_er_50", "obv_zscore_50", "rsi_14", "rsi_14_slope_5",
    "vwap_zscore_10", "vwap_zscore_5", "yangzhang_100",
]


# --------------------------------------------------------------------------- #
# Cross-validation
# --------------------------------------------------------------------------- #
def _safe_ap(y: np.ndarray, p: np.ndarray) -> float:
    if len(y) == 0 or y.min() == y.max():
        return float("nan")
    return float(average_precision_score(y, p))


def run_cv(X: np.ndarray, y: np.ndarray, dates: np.ndarray, params: dict,
           splitter: PurgedWalkForwardSplit, logger: logging.Logger | None = None):
    oof = np.full(len(y), np.nan)
    fold_id = np.full(len(y), -1, dtype="int16")
    stats = []
    for k, (tr, va) in enumerate(splitter.split(dates)):
        fit_i, cal_i = purged_holdout(dates, tr, CALIB_FRACTION, splitter.embargo_td)
        if len(fit_i) == 0 or len(cal_i) == 0:
            logger.warning("fold %d: empty fit(%d) or cal(%d) — skipping", k, len(fit_i), len(cal_i)) if logger else None
            continue
        t0 = time.time()
        m = fit_calibrated(X[fit_i], y[fit_i], X[cal_i], y[cal_i], params)
        if m is None:
            stats.append({"fold": k, "skipped": "single-class fit/calibration set"})
            if logger:
                logger.warning("fold %d: skipped (single-class)", k)
            continue
        oof[va] = m.predict_proba(X[va])
        fold_id[va] = k
        fold_stat = {
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
            "wall_sec": round(time.time() - t0, 1),
        }
        if logger:
            logger.info(
                "fold %d: n_fit=%d n_calib=%d n_val=%d pos_rate=%.3f best_iter=%d "
                "train_pr=%.3f val_pr=%.3f cal=%s wall=%.1fs",
                k, fold_stat["n_fit"], fold_stat["n_calib"], fold_stat["n_val"],
                fold_stat["train_pos_rate"], fold_stat["best_iteration"],
                fold_stat["train_pr_auc"], fold_stat["val_pr_auc"],
                fold_stat["calibration"], fold_stat["wall_sec"],
            )
        if fold_stat["best_iteration"] <= 1:
            logger.warning("fold %d: NO_LEARNING best_iteration=%d", k, fold_stat["best_iteration"]) if logger else None
        stats.append(fold_stat)
    return oof, fold_id, stats


# --------------------------------------------------------------------------- #
# Market driver
# --------------------------------------------------------------------------- #
def train_market(
    market: str, cfg: dict, n_splits: int, embargo_td: int,
    placebo_seeds: int = 1, targets: list[str] | None = None,
    allow_fixture: bool = False, min_date: str | None = None,
    min_avail_mb: float = 1000.0, resume: bool = False,
    xgb_verbose: bool = False, recompute_features: bool = False,
    feature_set: str = "full",
) -> dict:
    import logging as _logging_mod

    if xgb_verbose:
        import xgboost as xgbx
        xgbx.set_config(verbosity=2)

    t0_wall = time.time()
    logger, _log_path, _jsonl_path = setup_logging("xgb_trainer", market)
    catalog = load_catalog(market)
    params = xgb_params(cfg)

    target_list = targets if targets else list(TARGET_COLUMNS)
    suffix = "" if feature_set == "full" else f"_{feature_set}"
    # --resume: skip targets already in meta
    if resume:
        meta_path = DATA_DIR / f"train_meta_{market}{suffix}.json"
        if meta_path.exists():
            existing_meta = json.loads(meta_path.read_text())
            done_targets = set(existing_meta.get("targets", {}).keys())
            target_list = [t for t in target_list if t not in done_targets]
            logger.info("resume: done=%s remaining=%s", sorted(done_targets), target_list)

    with log_phase(logger, "build_panel"):
        panel = build_panel(market, catalog, allow_fixture=allow_fixture, min_date=min_date,
                            recompute_features=recompute_features)

    latest_date = panel["date"].max()
    # Slim the panel to the union of E3 ablation masks + bookkeeping columns
    # before training (the full 89-col panel x2 copies contributed to the OOM
    # kill of the first E3 attempt on this 8 GB host).
    from src.feature_engine import FIB_FEATURE_NAMES
    keep_cols = (set(catalog["surviving_features"])
                 | {f"{c}_cs_pct" for c in catalog["surviving_features"]}
                 | set(FIB_FEATURE_NAMES) | set(LEGACY_WHITELIST_UNION)
                 | set(TARGET_COLUMNS)
                 | {"date", "symbol", "market", "close", "fwd_atr_ret_15", "fwd_atr_ret_20"})
    slim = panel[[c for c in panel.columns if c in keep_cols]]
    labeled = slim.dropna(subset=TARGET_COLUMNS).reset_index(drop=True)
    infer = slim[slim["date"] == latest_date].reset_index(drop=True)
    dates = labeled["date"].to_numpy()
    del panel, slim
    gc.collect()

    universe = {
        "n_symbols": int(labeled["symbol"].nunique()),
        "n_rows": int(len(labeled)),
        "date_min": str(pd.Timestamp(labeled["date"].min()).date()),
        "date_max": str(pd.Timestamp(latest_date).date()),
        "source": "fixture" if allow_fixture else "raw_ohlcv",
        "min_date": min_date,
        "quarantined_excluded": len(load_quarantine(market)),
    }
    logger.info("universe: %d symbols, %d labeled rows, %s -> %s, source=%s",
                universe["n_symbols"], universe["n_rows"],
                universe["date_min"], universe["date_max"], universe["source"])

    # Load or initialize meta
    meta_path = DATA_DIR / f"train_meta_{market}{suffix}.json"
    if resume and meta_path.exists():
        meta = json.loads(meta_path.read_text())
    else:
        meta = {
            "market": market,
            "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "n_splits": n_splits,
            "embargo_td": embargo_td,
            "n_placebo_seeds": placebo_seeds,
            "feature_set": feature_set,
            "latest_date": str(pd.Timestamp(latest_date).date()),
            "universe": universe,
            "targets": {},
        }

    # Load or initialize OOF
    oof_path = DATA_DIR / f"oof_{market}{suffix}.parquet"
    preds_path = DATA_DIR / f"predictions_{market}{suffix}_latest.parquet"
    if resume and oof_path.exists():
        oof = pd.read_parquet(oof_path)
        preds = pd.read_parquet(preds_path)
    else:
        oof = labeled[["date", "symbol", "close", "fwd_atr_ret_15", "fwd_atr_ret_20"]].copy()
        preds = infer[["date", "symbol"]].copy()

    model_dir = MODELS_DIR / market.lower()
    model_dir.mkdir(parents=True, exist_ok=True)

    for target in target_list:
        logger.info("=== target: %s ===", target)
        check_memory(logger, min_avail_mb)

        # Per-target embargo: floor at the flat WI-009 value, grow to the label
        # horizon, and never let the CLI/default weaken it (D-016).
        target_embargo_td = resolve_embargo(target, embargo_td)
        splitter = PurgedWalkForwardSplit(n_splits=n_splits, embargo_td=target_embargo_td)
        logger.info("target %s: horizon=%d embargo_td=%d", target, target_horizon(target), target_embargo_td)

        panel_cols = set(labeled.columns)
        feats = target_features(catalog, target, feature_set=feature_set, panel_cols=panel_cols)
        # Ensure features exist in the panel (some may have been dropped)
        feats = [f for f in feats if f in labeled.columns]
        if not feats:
            logger.error("no valid features for target %s", target)
            continue

        X = labeled[feats].to_numpy(dtype="float32")
        y = labeled[target].to_numpy().astype("int8")

        nan_frac = float(np.isnan(X).mean())
        if nan_frac > 0.20:
            logger.warning("X NaN fraction %.1f%% for target %s", nan_frac * 100, target)

        with log_phase(logger, f"cv_{target}"):
            p, fold, stats = run_cv(X, y, dates, params, splitter, logger=logger)

        oof[f"y_{target}"] = y
        oof[f"p_{target}"] = p.astype("float32")
        oof[f"fold_{target}"] = fold

        # Placebo runs
        for s in range(placebo_seeds):
            with log_phase(logger, f"placebo_{target}_s{s}"):
                y_pl = np.random.default_rng(1000 + s).permutation(y)
                p_pl, _, _ = run_cv(X, y_pl, dates, params, splitter, logger=logger)
            oof[f"y_{target}_pl{s}"] = y_pl
            oof[f"p_{target}_pl{s}"] = p_pl.astype("float32")

        # Final model on all labeled dates
        all_idx = np.arange(len(y))
        fit_i, cal_i = purged_holdout(dates, all_idx, CALIB_FRACTION, target_embargo_td)
        final = fit_calibrated(X[fit_i], y[fit_i], X[cal_i], y[cal_i], params)

        tmeta: dict[str, object] = {
            "features": feats,
            "folds": stats,
            "final_model": None,
            "horizon": target_horizon(target),
            "embargo_td": target_embargo_td,
        }
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
            logger.warning("final model failed for %s", target)
            preds[PROB_COLUMN[target]] = np.nan

        meta["targets"][target] = tmeta

        # Checkpoint after each target
        oof.to_parquet(oof_path, index=False)
        preds["exit_urgency"] = (
            preds[[c for c in EVENT_PROB_COLUMNS if c in preds.columns]].max(axis=1)
            if any(c in preds.columns for c in EVENT_PROB_COLUMNS)
            else np.nan
        )
        preds.to_parquet(preds_path, index=False)
        meta_path.write_text(json.dumps(meta, indent=2))
        logger.info("checkpoint saved: %s", target)

        gc.collect()

    elapsed = time.time() - t0_wall
    log_telemetry(f"xgb_trainer_{market}", "SUCCESS", elapsed, {
        "rows": int(len(labeled)), "targets": target_list, "placebo_seeds": placebo_seeds,
    })
    logger.info("[xgb_trainer] %s: %d labeled rows, %d targets, %d placebo seeds, %.1fs",
                market, len(labeled), len(target_list), placebo_seeds, elapsed)
    return meta


def main() -> int:
    init_dirs()
    cfg = load_settings()
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", choices=["USD", "CAD", "ALL"], default="ALL")
    parser.add_argument("--embargo", type=int, default=cfg["modeling"]["embargo_td"])
    parser.add_argument("--n-splits", type=int, default=cfg["modeling"]["n_splits"])
    parser.add_argument("--placebo-seeds", type=int, default=N_PLACEBO_SEEDS)
    parser.add_argument("--targets", default=None, help="Comma-separated target list, e.g. y_15d_high,y_20d_up")
    parser.add_argument("--min-date", default=None, help="Earliest date to use (YYYY-MM-DD)")
    parser.add_argument("--allow-fixture", action="store_true", help="Permit fixture test data fallback")
    parser.add_argument("--min-avail-mb", type=float, default=1000.0, help="Abort if MemAvailable drops below this")
    parser.add_argument("--xgb-verbose", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Skip targets already in train_meta JSON")
    parser.add_argument("--recompute-features", action="store_true",
                        help="Ignore persisted features/targets parquets; recompute in-loop (legacy path)")
    parser.add_argument("--feature-set", default="full",
                        choices=["full", "no_static", "fib_only", "legacy19", "cs_pct_only"],
                        help="E3 ablation mask over the panel columns (default full = Gate-3 whitelist)")
    args = parser.parse_args()
    target_list = [t.strip() for t in args.targets.split(",")] if args.targets else None

    markets = ["USD", "CAD"] if args.market == "ALL" else [args.market]
    for mkt in markets:
        train_market(
            mkt, cfg, args.n_splits, args.embargo,
            placebo_seeds=args.placebo_seeds, targets=target_list,
            allow_fixture=args.allow_fixture, min_date=args.min_date,
            min_avail_mb=args.min_avail_mb, resume=args.resume,
            xgb_verbose=args.xgb_verbose, recompute_features=args.recompute_features,
            feature_set=args.feature_set,
        )
    update_state("EP-04", "training", {"markets": markets, "embargo_td": args.embargo, "n_splits": args.n_splits})
    return 0


if __name__ == "__main__":
    sys.exit(main())
