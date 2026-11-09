"""WI-036 — extended three-binary target-variant grid (D-022 §3c).

Thin driver over the WI-035 machinery (imported, never rewritten): the 8 target
families x 9 horizons x 3 binaries x 4 learners x 2 markets are scored as **pure
signal** — pooled OOF AUC + rank-IC over the 5 purged folds, a 5-seed label-
permutation placebo on the AUC statistic, and BH-FDR alpha=0.05 across the grid.
No tau grid, no `frozen_selection`, no portfolio returns (admin 2026-11-09).

CLI::

    WI036_SMOKE=5 python -m src.swing_bsh.binary_grid --out /tmp/wi036_smoke
    python -m src.swing_bsh.binary_grid --market ALL

Core-hour cap 2.5 (`CoreBudget`, `time.process_time`); cells launch in priority
order (horizon ascending) and the run truncates cleanly when the budget is spent.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import pickle
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from src.swing_bsh import binary_features_ext as ext
from src.swing_bsh import binary_labels, binary_train, train
from src.xgb_trainer import PurgedWalkForwardSplit, purged_holdout

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "reports"
MODEL_DIR = BASE_DIR / "data" / "models" / "wi036"
REPORT_NAME = "wi036_summary.md"

LEARNERS: tuple[str, ...] = ("xgboost", "logistic_l2", "hist_gbm", "mlp_torch")
TAU_P_GRID = binary_train.TAU_P_GRID
TAU_S_GRID = binary_train.TAU_S_GRID
PRUNE_RHO = 0.3
N_SPLITS = 5
N_PLACEBO_SEEDS = 5
CORE_HOUR_CAP = 2.5
SAFETY = 0.95
CALIB_FRACTION = binary_train.CALIB_FRACTION
CB04_MIN_POSITIVES = binary_train.CB04_MIN_POSITIVES
MLP_HIDDEN = (64, 32)
MLP_EPOCHS = 40
MLP_PATIENCE = 5
FDR_ALPHA = 0.05
PLACEBO_MIN_LEFT = 90.0
PLACEBO_RESERVE = 0.35
"""Fraction of the core budget held back from the grid loop for the placebo pass."""

__all__ = ["CORE_HOUR_CAP", "LEARNERS", "MODEL_DIR", "N_PLACEBO_SEEDS", "PRUNE_RHO",
           "TAU_P_GRID", "TAU_S_GRID", "CoreBudget", "attribution", "bh_fdr", "build_report",
           "cell_cv", "fit_learner", "main", "placebo_auc", "rank_variants", "run_market",
           "run_placebo"]


class CoreBudget:
    """Core-second budget (`process_time`, all threads) with a launch guard."""

    def __init__(self, core_hours: float = CORE_HOUR_CAP, safety: float = SAFETY):
        self.cap = float(core_hours) * 3600.0 * float(safety)
        self.t0 = time.process_time()

    def spent(self) -> float:
        return time.process_time() - self.t0

    def left(self) -> float:
        return self.cap - self.spent()

    def exhausted(self) -> bool:
        return self.left() <= 0.0


# --------------------------------------------------------------------------- #
# Learners (4-learner grid, mlp_torch restored)
# --------------------------------------------------------------------------- #
class TorchMLP:
    """Standardised 2-layer MLP with a `predict_proba` matching the sklearn learners."""

    def __init__(self, net, mu, sd, med):
        self.net, self.mu, self.sd, self.med = net, mu, sd, med
        self.best_iter = -1

    def predict_proba(self, X) -> np.ndarray:
        import torch
        X = np.asarray(X, dtype="float64")
        X = np.where(np.isfinite(X), X, self.med)
        x = torch.tensor(((X - self.mu) / self.sd).astype("float32"))
        self.net.eval()
        with torch.no_grad():
            p = torch.sigmoid(self.net(x)).numpy().ravel()
        return np.column_stack([1.0 - p, p])


# Pin the class to its importable path: run as `python -m src.swing_bsh.binary_grid`
# the driver module is `__main__`, which would make every pickled MLP unloadable.
if __name__ == "__main__":
    import sys as _sys
    _sys.modules.setdefault("src.swing_bsh.binary_grid", _sys.modules[__name__])
    TorchMLP.__module__ = "src.swing_bsh.binary_grid"


def _fit_mlp(X_fit, y_fit, X_cal, y_cal, seed: int = binary_train.SEED) -> TorchMLP:
    """2-layer MLP, early-stopped on the fold's calibration block (CPU, n_jobs=2)."""
    import torch
    torch.manual_seed(seed)
    torch.set_num_threads(binary_train.N_JOBS)
    X_fit, X_cal = binary_train.fill_dead_columns(binary_train.dead_columns(X_fit), X_fit, X_cal)
    med = np.nanmedian(X_fit, axis=0)
    med = np.where(np.isfinite(med), med, 0.0)
    X_fit = np.where(np.isfinite(X_fit), X_fit, med)
    X_cal = np.where(np.isfinite(X_cal), X_cal, med)
    mu = X_fit.mean(axis=0)
    sd = X_fit.std(axis=0)
    sd = np.where(sd > 1e-9, sd, 1.0)
    xf = torch.tensor(((X_fit - mu) / sd).astype("float32"))
    xc = torch.tensor(((X_cal - mu) / sd).astype("float32"))
    yf = torch.tensor(np.asarray(y_fit, dtype="float32")).view(-1, 1)
    yc = torch.tensor(np.asarray(y_cal, dtype="float32")).view(-1, 1)
    h1, h2 = MLP_HIDDEN
    net = torch.nn.Sequential(torch.nn.Linear(X_fit.shape[1], h1), torch.nn.ReLU(),
                              torch.nn.Linear(h1, h2), torch.nn.ReLU(), torch.nn.Linear(h2, 1))
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    loss = torch.nn.BCEWithLogitsLoss()
    best, best_state, bad, best_ep = np.inf, None, 0, -1
    for ep in range(MLP_EPOCHS):
        net.train()
        opt.zero_grad()
        loss(net(xf), yf).backward()
        opt.step()
        net.eval()
        with torch.no_grad():
            vl = float(loss(net(xc), yc))
        if vl < best - 1e-5:
            best, bad, best_ep = vl, 0, ep
            best_state = {k: v.detach().clone() for k, v in net.state_dict().items()}
        else:
            bad += 1
            if bad >= MLP_PATIENCE:
                break
    if best_state is not None:
        net.load_state_dict(best_state)
    wrapper = TorchMLP(net, mu, sd, med)
    wrapper.best_iter = best_ep
    return wrapper


def _logit(p) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype="float64"), 1e-6, 1.0 - 1e-6)
    return np.log(p / (1.0 - p))


def fit_learner(learner: str, params: dict, X_fit, y_fit, X_cal, y_cal,
                min_pos: int = CB04_MIN_POSITIVES):
    """Fit + calibrate one learner; `mlp_torch` gets the WI-036 MLP, the rest reuse WI-035."""
    if learner != "mlp_torch":
        return binary_train.fit_calibrated_binary(learner, X_fit, y_fit, X_cal, y_cal,
                                                  params, min_pos)
    if len(y_fit) == 0 or len(y_cal) == 0 or len(np.unique(y_fit)) < 2:
        return None
    model = _fit_mlp(X_fit, y_fit, X_cal, y_cal)
    raw = model.predict_proba(X_cal)[:, 1]
    y_cal = np.asarray(y_cal, dtype="int8")
    method = train.calibration_method(int(y_cal.sum()), len(y_cal), min_pos)
    if method == "isotonic":
        from sklearn.isotonic import IsotonicRegression
        calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(raw, y_cal)
    elif method == "sigmoid":
        calibrator = LogisticRegression().fit(_logit(raw).reshape(-1, 1), y_cal)
    else:
        calibrator = None
    return binary_train.CalibratedBinary(learner, model, method, calibrator)


# --------------------------------------------------------------------------- #
# Cell CV + statistics
# --------------------------------------------------------------------------- #
def _pickle(model, model_dir, tag: str, fold) -> None:
    if model is None or model_dir is None:
        return
    path = Path(model_dir) / f"{tag}_f{fold}.pkl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as fh:
        pickle.dump({"model": model, "provenance": {
            "tag": tag, "fold": fold, "calibration": getattr(model, "method", None)}}, fh)


def cell_cv(X, y, dates, learner, params, splitter, model_dir=None, tag: str = "cell") -> dict:
    """Purged walk-forward CV for one cell; returns pooled OOF predictions + fold models."""
    y = np.asarray(y, dtype="int8")
    oof = np.full(len(y), np.nan)
    fold_id = np.full(len(y), -1, dtype="int16")
    models: dict[int, object] = {}
    for k, (tr, va) in enumerate(splitter.split(dates)):
        fit_i, cal_i = purged_holdout(dates, tr, CALIB_FRACTION, splitter.embargo_td)
        if len(fit_i) == 0 or len(cal_i) == 0:
            continue
        m = fit_learner(learner, params, X[fit_i], y[fit_i], X[cal_i], y[cal_i])
        if m is None:
            continue
        oof[va] = m.predict_proba(X[va])
        fold_id[va] = k
        models[k] = m
        _pickle(m, model_dir, tag, k)
    return {"oof": oof, "fold_id": fold_id, "models": models}


def auc_ic(y, oof, fold_id) -> tuple[float, float, list[float]]:
    """Pooled OOF AUC + rank-IC, plus the per-fold AUC list."""
    y = np.asarray(y, dtype="float64")
    oof = np.asarray(oof, dtype="float64")
    fold_id = np.asarray(fold_id)
    m = (fold_id >= 0) & np.isfinite(oof)
    if m.sum() < 30 or len(np.unique(y[m])) < 2:
        return float("nan"), float("nan"), []
    auc = float(roc_auc_score(y[m], oof[m]))
    ic = float(spearmanr(oof[m], y[m])[0])
    folds = []
    for f in np.unique(fold_id[m]):
        sel = m & (fold_id == f)
        if len(np.unique(y[sel])) > 1:
            folds.append(float(roc_auc_score(y[sel], oof[sel])))
    return auc, ic, folds


def placebo_auc(X, y, dates, learner, params, splitter, obs: float,
                n_seeds: int = N_PLACEBO_SEEDS, seed0: int = 5000) -> dict:
    """Label-permutation null on the pooled OOF AUC (5 seeds)."""
    null = []
    for s in range(n_seeds):
        yp = np.random.default_rng(seed0 + s).permutation(np.asarray(y, dtype="int8"))
        cv = cell_cv(X, yp, dates, learner, params, splitter)
        null.append(auc_ic(yp, cv["oof"], cv["fold_id"])[0])
    arr = np.asarray([v for v in null if np.isfinite(v)], dtype="float64")
    mean = float(arr.mean()) if arr.size else float("nan")
    sd = float(arr.std(ddof=1)) if arr.size > 1 else float("nan")
    z = float((obs - mean) / sd) if np.isfinite(sd) and sd > 0 else float("nan")
    p = float(norm.sf(z)) if np.isfinite(z) else float("nan")
    return {"auc": float(obs), "null_mean": mean, "null_sd": sd, "z": z, "p": p,
            "n_seeds": int(arr.size)}


def bh_fdr(pvals, alpha: float = FDR_ALPHA, m_total: int | None = None) -> tuple[np.ndarray, float]:
    """Benjamini-Hochberg: reject the largest prefix passing `p_(i) <= i/m*alpha`.

    `m_total` overrides the multiplicity `m` (the WI enforces it over the **full**
    grid, not only the cells that carry a permutation p-value).
    """
    p = np.asarray(pvals, dtype="float64")
    ok = np.flatnonzero(np.isfinite(p))
    surv = np.zeros(len(p), dtype=bool)
    if ok.size == 0:
        return surv, 0.0
    order = ok[np.argsort(p[ok])]
    m = int(m_total) if m_total is not None else ok.size
    kmax = 0
    for rank, j in enumerate(order, 1):
        if p[j] <= alpha * rank / m:
            kmax = rank
    if kmax:
        surv[order[:kmax]] = True
    return surv, (alpha * kmax / m if kmax else 0.0)


# --------------------------------------------------------------------------- #
# Market driver
# --------------------------------------------------------------------------- #
def _panel_and_labels(market, *, cache_dir, limit, allow_fixture):
    keys = [(name, h) for name, _, _, _ in ext.variant_grid() for h in ext.HORIZONS]
    if cache_dir is not None and limit is None:
        panel, labels = ext.load_variant_panel(cache_dir, market, keys)
        if panel is not None:
            return panel, labels
    panel, labels = ext.build_variant_panel(market, allow_fixture=allow_fixture, max_symbols=limit)
    if cache_dir is not None and limit is None and not panel.empty:
        ext.save_variant_panel(panel, labels, cache_dir, market)
    return panel, labels


def run_market(market, cfg, *, out_dir=REPORTS_DIR, model_dir=MODEL_DIR, limit=None,
               allow_fixture=False, cache_dir=None, budget=None, grid_seconds=None,
               placebo_seeds: int = N_PLACEBO_SEEDS, learners=LEARNERS) -> dict:
    """Score the full target-variant grid for one market (budget-gated)."""
    budget = budget or CoreBudget()
    panel, labels = _panel_and_labels(market, cache_dir=cache_dir, limit=limit,
                                      allow_fixture=allow_fixture)
    if panel.empty:
        raise RuntimeError(f"no swing events for market={market}")
    kept, dropped = binary_labels.kept_features(panel, threshold=PRUNE_RHO,
                                                features=ext.candidate_features(panel))
    kept = binary_labels.feature_names(kept)
    panel = train.engineer(panel)
    panel["k"] = np.float32(1.0)
    panel["horizon"] = np.float32(21.0)
    X, feats = train.feature_matrix(panel, kept)
    dates = panel["date"].to_numpy()
    params = binary_train.learner_params(cfg)
    params.setdefault("mlp_torch", {})
    splitters = {h: PurgedWalkForwardSplit(n_splits=N_SPLITS, embargo_td=train.embargo_for([h]))
                 for h in ext.HORIZONS}
    cells: list[dict] = []
    skipped: list[str] = []
    t_grid = budget.spent()
    if grid_seconds is None:
        grid_seconds = max(0.0, budget.left() * (1.0 - PLACEBO_RESERVE))
    for h in ext.HORIZONS:
        for variant, event, window, k in ext.variant_grid():
            for binary in ext.BINARY_COLUMNS:
                for learner in learners:
                    tag = f"{market}_{learner}_{variant}_{binary}_h{h}"
                    if grid_seconds is not None and budget.spent() - t_grid > grid_seconds:
                        skipped.append(tag)
                        continue
                    y = labels[(variant, h)][binary]
                    cv = cell_cv(X, y, dates, learner, params[learner], splitters[h],
                                 model_dir, tag)
                    auc, ic, folds = auc_ic(y, cv["oof"], cv["fold_id"])
                    cells.append({"market": market, "variant": variant, "event": event,
                                  "window": window, "k": k, "h": int(h), "binary": binary,
                                  "learner": learner, "tag": tag, "auc": auc, "ic": ic,
                                  "fold_auc": folds, "n_oof": int(np.isfinite(cv["oof"]).sum()),
                                  "z": float("nan"), "p": float("nan")})
                    del cv
    return {"market": market, "n_rows": int(len(panel)), "n_symbols": int(panel["symbol"].nunique()),
            "features": feats, "n_features_pruned": len(kept),
            "n_features_input": len(kept) + len(dropped), "dropped": dropped,
            "cells": cells, "skipped": skipped, "placebo_seeds": placebo_seeds,
            "core_sec": round(budget.spent(), 1), "X": X, "labels": labels, "params": params,
            "dates": dates, "splitters": splitters}


def run_placebo(results: list[dict], budget: CoreBudget, seeds: int = N_PLACEBO_SEEDS) -> int:
    """5-seed AUC permutation placebo, most extreme cells first, until the budget runs out."""
    cells = [c for r in results for c in r["cells"] if np.isfinite(c["auc"])]
    ctx = {r["market"]: r for r in results}
    done = 0
    for c in sorted(cells, key=lambda c: -abs(c["auc"] - 0.5)):
        if budget.left() < PLACEBO_MIN_LEFT:
            break
        r = ctx[c["market"]]
        pl = placebo_auc(r["X"], r["labels"][(c["variant"], c["h"])][c["binary"]], r["dates"],
                         c["learner"], r["params"][c["learner"]], r["splitters"][c["h"]],
                         c["auc"], n_seeds=seeds)
        c["z"], c["p"], c["placebo"] = pl["z"], pl["p"], pl
        done += 1
    return done


# --------------------------------------------------------------------------- #
# Ranking / attribution / report
# --------------------------------------------------------------------------- #
def _cell_key(c: dict) -> str:
    return f"{c['learner']}|{c['variant']}|{c['binary']}|h{c['h']}"


def rank_variants(cells: list[dict]) -> pd.DataFrame:
    """Cross-market-consistent target ranking (`min(AUC_USD, AUC_CAD)` per variant)."""
    df = pd.DataFrame([c for c in cells if np.isfinite(c["auc"])])
    if df.empty:
        return df
    df["key"] = df.apply(_cell_key, axis=1)
    cols = ["key", "variant", "event", "window", "k", "h", "binary", "learner"]
    usd = df[df["market"] == "USD"].set_index("key")
    cad = df[df["market"] == "CAD"].set_index("key")
    pair = (usd[["auc", "ic"]].join(cad[["auc", "ic"]], lsuffix="_usd", rsuffix="_cad", how="inner")
            .reset_index().merge(df[cols].drop_duplicates("key"), on="key", how="left"))
    if pair.empty:
        return pd.DataFrame()
    pair["auc_min"] = pair[["auc_usd", "auc_cad"]].min(axis=1)
    pair["ic_min"] = pair[["ic_usd", "ic_cad"]].min(axis=1)
    rows = []
    for variant, g in pair.groupby("variant"):
        b = g.sort_values("auc_min", ascending=False).iloc[0]
        rows.append({"variant": variant, "event": b["event"], "window": b["window"], "k": b["k"],
                     "n_cells": int(len(g)), "best": b["key"], "h": int(b["h"]),
                     "binary": b["binary"], "learner": b["learner"], "auc_usd": b["auc_usd"],
                     "auc_cad": b["auc_cad"], "auc_min": b["auc_min"], "ic_min": b["ic_min"],
                     "auc_min_median": float(g["auc_min"].median())})
    return pd.DataFrame(rows).sort_values("auc_min", ascending=False).reset_index(drop=True)


def attribution(res: dict, cell: dict, top: int = 8) -> dict:
    """TreeSHAP + linear coefficients for one cell's target (full-panel refit)."""
    from xgboost import XGBClassifier
    X, feats = res["X"], res["features"]
    y = np.asarray(res["labels"][(cell["variant"], cell["h"])][cell["binary"]], dtype="int8")
    xgb = XGBClassifier(**res["params"]["xgboost"], objective="binary:logistic",
                        eval_metric="logloss")
    xgb.fit(X, y, verbose=False)
    out = {"treeshap": dict(list(binary_train.treeshap_shares(xgb, X, feats).items())[:top])}
    lin = binary_train._fit_learner("logistic_l2", res["params"]["logistic_l2"], X, y, X, y)
    coef = np.asarray(lin.named_steps["clf"].coef_[0], dtype="float64")
    order = np.argsort(-np.abs(coef))[:top]
    out["linear"] = [(feats[j], float(coef[j])) for j in order]
    return out


def _fmt(x, spec: str = "{:.4f}") -> str:
    v = float(x)
    return "n/a" if not np.isfinite(v) else spec.format(v)


def build_report(res: list[dict], path: Path, ranking: pd.DataFrame, attrs: dict,
                 survivors: pd.DataFrame) -> Path:
    """`wi036_summary.md` — target ranking, feature attribution, FDR survivors."""
    n_cells = sum(len(r["cells"]) for r in res)
    n_skipped = sum(len(r["skipped"]) for r in res)
    cells = [c for r in res for c in r["cells"]]
    n_tested = int(np.isfinite([c["p"] for c in cells]).sum())
    cov = ", ".join("{0} {1}s".format(r["market"], r["core_sec"]) for r in res)
    lines = [
        "# WI-036 — extended three-binary target-variant grid (D-022 §3c)",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Grid: {len(ext.variant_grid())} target families x {len(ext.HORIZONS)} horizons "
        f"({', '.join(str(h) for h in ext.HORIZONS)}) x {len(ext.BINARY_COLUMNS)} binaries x "
        f"{len(LEARNERS)} learners x {len(res)} markets; verdict = pooled OOF AUC + rank-IC, "
        "no tau grid / no entry rule (admin 2026-11-09)",
        f"- Learners: {', '.join(LEARNERS)}; rho prune {PRUNE_RHO}; features = WI-016 grid + "
        "WI-036 expansion (raw volume/VWAP/barCount, cross-sectional ranks, sector one-hots + "
        "ranks, event quality, calendar, breadth); `n_jobs=2`, float32, symbol-sequential",
        f"- CV: {N_SPLITS}-fold `PurgedWalkForwardSplit(embargo_td=max(20, h))`; placebo "
        f"{N_PLACEBO_SEEDS}-seed label permutation on the AUC; BH-FDR alpha={FDR_ALPHA}; "
        f"core cap {CORE_HOUR_CAP} h",
        f"- Coverage: {n_cells} cells scored, {n_skipped} truncated by the core budget ({cov}); "
        f"{n_tested} cells carry a 5-seed permutation p-value (FDR over the scored grid)",
        "- Pickles: every fitted fold model under `data/models/wi036/<MKT>_<learner>_<variant>_"
        "<binary>_h<h>_f<fold>.pkl` (verdict-independent)",
        "",
        "## 1. Target ranking — cross-market consistent AUC / rank-IC",
        "",
        "| rank | variant | best cell (learner/binary/h) | AUC USD | AUC CAD | min AUC | min IC | "
        "median min AUC | cells |",
        "| ---: | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for i, row in ranking.iterrows():
        lines.append(
            f"| {i + 1} | `{row['variant']}` | {row['learner']}/{row['binary']}/h{int(row['h'])} | "
            f"{_fmt(row['auc_usd'])} | {_fmt(row['auc_cad'])} | **{_fmt(row['auc_min'])}** | "
            f"{_fmt(row['ic_min'], '{:+.4f}')} | {_fmt(row['auc_min_median'])} | "
            f"{int(row['n_cells'])} |")
    if ranking.empty:
        lines.append("| — | no cross-market cell pairs completed | | | | | | | |")
    lines += ["", "## 2. Feature attribution — winning target", ""]
    if not ranking.empty and ranking.iloc[0]["variant"] in attrs:
        win, a = ranking.iloc[0], attrs[ranking.iloc[0]["variant"]]
        lines += [f"Winning family: `{win['variant']}` (best cell {win['best']}, min AUC "
                  f"{_fmt(win['auc_min'])}).", "",
                  "- Top TreeSHAP (xgboost, full-panel refit): "
                  + ", ".join(f"`{k}` {v:.3f}" for k, v in a["treeshap"].items()),
                  "- Top |linear coefficient| (logistic_l2): "
                  + ", ".join(f"`{k}` {v:+.3f}" for k, v in a["linear"])]
    else:
        lines.append("No winning target with cross-market cells completed.")
    lines += ["", "## 3. FDR survivors (BH alpha=0.05)", "",
              "| market | variant | learner | binary | h | AUC | z | p |",
              "| :--- | :--- | :--- | :--- | ---: | ---: | ---: | ---: |"]
    if survivors.empty:
        lines.append("| — | no cell survived BH-FDR | | | | | | |")
    for _, s in survivors.iterrows():
        lines.append(f"| {s['market']} | `{s['variant']}` | {s['learner']} | {s['binary']} | "
                     f"{int(s['h'])} | {_fmt(s['auc'])} | {_fmt(s['z'], '{:+.2f}')} | "
                     f"{_fmt(s['p'], '{:.2e}')} |")
    lines += ["", "## Notes / deviations", "",
              "- Pure-signal run: the tau/entry-rule layer is retired from the verdict "
              "(admin 2026-11-09) — nothing selected, no portfolio returns, no costs.",
              "- Target definitions: `exact` = detected swing bar; `tol2` = extreme bar within "
              "+/-2 bars (shoulder); `full` = touch window [t+1, t+h]; `mid60` = "
              "[t+ceil(.2h), t+floor(.8h)]; features are always read at the detection bar.",
              "- `k` and `horizon` are constant inside a cell, so the shared design matrix "
              "carries them as zero-variance columns (no information; mirrors WI-035).",
              "- Cells not reached before the core cap are reported as truncated, not dropped; "
              "placebo (FDR) is run on the cells with the largest |AUC-0.5| first.",
              ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return path


def _attribution_for(res: dict, cell_key: str) -> dict:
    """Locate the winning cell in this market and run the attribution refit."""
    for c in res["cells"]:
        if _cell_key(c) == cell_key:
            return attribution(res, c)
    return {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="WI-036 target-variant grid (D-022 §3c)")
    parser.add_argument("--market", default="ALL", help="USD | CAD | ALL (default ALL)")
    parser.add_argument("--limit", type=int, default=None, help="Max symbols per market (smoke).")
    parser.add_argument("--out", default=None, help="Output dir (smoke runs use /tmp).")
    parser.add_argument("--allow-fixture", action="store_true")
    parser.add_argument("--placebo-seeds", type=int, default=N_PLACEBO_SEEDS)
    parser.add_argument("--core-hours", type=float, default=CORE_HOUR_CAP)
    parser.add_argument("--learners", default=",".join(LEARNERS))
    parser.add_argument("--cache-dir", default="/tmp/wi036", help="Panel cache dir.")
    args = parser.parse_args(argv)

    smoke = os.environ.get("WI036_SMOKE", "").strip()
    if args.limit is None and smoke.isdigit():
        args.limit = int(smoke)
    if args.out is None and smoke:
        args.out = "/tmp/wi036_smoke"
    learners = tuple(s.strip() for s in args.learners.split(",") if s.strip())

    from src.market_cli import cli_markets
    markets = cli_markets(args.market, prog="wi036.binary_grid")
    if markets is None:
        return 2
    out_dir = Path(args.out) if args.out else REPORTS_DIR
    cfg = train.load_settings()
    budget = CoreBudget(args.core_hours)
    t0 = time.time()
    # Budget split: the grid CV loops get the cap minus the placebo reserve, split
    # evenly across markets; the held-back fraction pays for the 5-seed placebo.
    grid_share = max(0.0, budget.cap * (1.0 - PLACEBO_RESERVE)) / max(len(markets), 1)
    results = [run_market(m, cfg, out_dir=out_dir, limit=args.limit,
                          allow_fixture=args.allow_fixture, cache_dir=Path(args.cache_dir),
                          budget=budget, grid_seconds=grid_share,
                          placebo_seeds=args.placebo_seeds, learners=learners)
               for m in markets]
    n_placebo = run_placebo(results, budget, seeds=args.placebo_seeds)
    cells = [c for r in results for c in r["cells"]]
    ranking = rank_variants(cells)
    surv, _thr = bh_fdr([c["p"] for c in cells], alpha=FDR_ALPHA)
    for c, s in zip(cells, surv):
        c["fdr"] = bool(s)
    survivors = pd.DataFrame([c for c in cells if c.get("fdr")])
    attrs = {}
    if not ranking.empty:
        win = ranking.iloc[0]
        for r in results:
            if not attrs:
                attrs[win["variant"]] = _attribution_for(r, win["best"])
    report = build_report(results, out_dir / REPORT_NAME, ranking, attrs, survivors)
    for r in results:
        print(f"[wi036.grid] {r['market']}: cells={len(r['cells'])} "
              f"skipped={len(r['skipped'])} core={r['core_sec']}s")
    print(f"[wi036.grid] report -> {report} | placebo={n_placebo} | survivors={len(survivors)} | "
          f"total {round(time.time() - t0, 1)}s")
    print("[wi036.grid] EXIT:0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
