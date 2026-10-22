"""Sprint 4 — Model QA & governance suite (Gate 4).

Reads the out-of-fold predictions produced by `src/xgb_trainer.py` and grades
every (market, target) model on the four governance metrics from
`05_MODEL_GOVERNANCE_AND_QA.md`, plus four overfitting/sanity diagnostics.

Metrics (MVP gate thresholds):
  - Precision@K lift over base rate  >= 1.5x   (per-date top-K bucket)
  - Brier Skill Score vs climatology  > 0.05
  - PR-AUC                            > 1.35x positive prior
  - Deflated IC (Spearman)            > 0.04 with t-stat > 2.5

Diagnostics:
  1. Placebo permutation test (CB-05 hard halt).
  2. Train vs validation PR-AUC generalization gap (> 0.15 -> regularize).
  3. Regime stability (Bull / Bear / Sideways by 50d SMA slope of a benchmark).
  4. SHAP dominance (> 35% of total attribution on one feature).

CB-05: if the mean placebo ROC-AUC exceeds 0.52 *and* is statistically
distinguishable from 0.5 (z > 3), model artifacts are deleted, the state
ledger records CRITICAL_LEAKAGE_DETECTED, `state/PDF_BLOCKED` is written so the
PDF compiler refuses to run, and the process exits with code 1.

CLI:
    python -m src.model_qa --market ALL
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from src.state_manager import STATE_FILE, init_dirs, update_state
from src.targets import TARGET_COLUMNS
from src.xgb_trainer import TARGET_DIRECTION, TARGET_HORIZON

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
REPORT_PATH = BASE_DIR / "reports" / "sprint4_model_qa.md"
PDF_BLOCK_FLAG = BASE_DIR / "state" / "PDF_BLOCKED"

PRECISION_K_MAX = 30
PRECISION_K_UNIVERSE_FRACTION = 0.10
LIFT_MIN = 1.5
BSS_MIN = 0.05
PR_AUC_LIFT_MIN = 1.35
IC_MIN = 0.04
IC_T_MIN = 2.5
PLACEBO_AUC_MAX = 0.52
PLACEBO_Z_MIN = 3.0
GEN_GAP_MAX = 0.15
SHAP_DOMINANCE_MAX = 0.35
REGIME_SLOPE_LOOKBACK = 10
REGIME_SLOPE_THRESHOLD = 0.01
BENCHMARK = {"USD": "SPY", "CAD": "XIU"}


# --------------------------------------------------------------------------- #
# Metric helpers
# --------------------------------------------------------------------------- #
def _k_for(n: int) -> int:
    return int(min(PRECISION_K_MAX, max(1, math.floor(n * PRECISION_K_UNIVERSE_FRACTION))))


def precision_at_k(df: pd.DataFrame, pcol: str, ycol: str) -> float:
    """Mean hit rate of the per-date top-K bucket."""
    hits = []
    for _, g in df.groupby("date"):
        k = _k_for(len(g))
        hits.append(g.nlargest(k, pcol)[ycol].mean())
    return float(np.mean(hits)) if hits else float("nan")


def deflated_ic(df: pd.DataFrame, pcol: str, rcol: str, horizon: int) -> tuple[float, float]:
    """Mean per-date Spearman IC and its t-stat deflated by sqrt(horizon) for overlapping labels."""
    ics = []
    for _, g in df.groupby("date"):
        g = g.dropna(subset=[pcol, rcol])
        if len(g) < 3 or g[pcol].nunique() < 2 or g[rcol].nunique() < 2:
            continue
        rho = spearmanr(g[pcol], g[rcol]).statistic
        if np.isfinite(rho):
            ics.append(rho)
    if len(ics) < 2:
        return float("nan"), float("nan")
    ics = np.asarray(ics)
    sd = ics.std(ddof=1)
    t_raw = ics.mean() / (sd / math.sqrt(len(ics))) if sd > 0 else float("nan")
    return float(ics.mean()), float(t_raw / math.sqrt(horizon))


def _auc(y: np.ndarray, p: np.ndarray) -> float:
    if len(y) == 0 or y.min() == y.max():
        return float("nan")
    return float(roc_auc_score(y, p))


def _auc_null_se(y: np.ndarray) -> float:
    """Standard error of ROC-AUC under the null (Hanley-McNeil, AUC=0.5)."""
    n_pos = int(y.sum())
    n_neg = int(len(y) - n_pos)
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    return math.sqrt((n_pos + n_neg + 1) / (12.0 * n_pos * n_neg))


# --------------------------------------------------------------------------- #
# Regimes
# --------------------------------------------------------------------------- #
def regime_series(market: str, oof: pd.DataFrame) -> tuple[pd.Series, str]:
    """Bull/Bear/Sideways per date from the 50d SMA slope of a benchmark.

    Uses SPY / XIU.TO from `data/raw_ohlcv/` when synced, otherwise an
    equal-weight index of the market's own universe as a proxy.
    """
    bench_path = DATA_DIR / "raw_ohlcv" / f"market={market}" / f"symbol={BENCHMARK[market]}.parquet"
    if bench_path.exists():
        b = pd.read_parquet(bench_path)[["date", "close"]].sort_values("date")
        idx = b.set_index(pd.to_datetime(b["date"]))["close"].astype("float64")
        source = f"{BENCHMARK[market]} benchmark"
    else:
        wide = oof.pivot_table(index="date", columns="symbol", values="close")
        rets = wide.pct_change().mean(axis=1).fillna(0.0)
        idx = (1.0 + rets).cumprod()
        source = "equal-weight universe proxy (benchmark not synced)"

    sma = idx.rolling(50, min_periods=20).mean()
    slope = sma / sma.shift(REGIME_SLOPE_LOOKBACK) - 1.0
    regime = pd.Series("Sideways", index=idx.index)
    regime[slope > REGIME_SLOPE_THRESHOLD] = "Bull"
    regime[slope < -REGIME_SLOPE_THRESHOLD] = "Bear"
    regime[slope.isna()] = "Warmup"
    return regime, source


# --------------------------------------------------------------------------- #
# Per-target evaluation
# --------------------------------------------------------------------------- #
def evaluate_target(oof: pd.DataFrame, meta: dict, target: str, regimes: pd.Series) -> dict:
    pcol, ycol, fcol = f"p_{target}", f"y_{target}", f"fold_{target}"
    tmeta = meta["targets"][target]
    folds = [f for f in tmeta["folds"] if "skipped" not in f]

    v = oof[oof[fcol] >= 0].copy()
    res = {"target": target, "n_oof": int(len(v)), "n_folds": len(folds)}
    if v.empty:
        res["error"] = "no out-of-fold predictions (all folds skipped)"
        return res

    y = v[ycol].to_numpy().astype(int)
    p = v[pcol].to_numpy().astype("float64")
    base = float(y.mean())
    res["base_rate"] = base

    # Precision@K lift.
    prec = precision_at_k(v, pcol, ycol)
    res["precision_at_k"] = prec
    res["precision_lift"] = prec / base if base > 0 else float("nan")

    # Brier Skill Score vs per-fold training climatology.
    clim_map = {f["fold"]: f["train_pos_rate"] for f in folds}
    clim = v[fcol].map(clim_map).to_numpy().astype("float64")
    brier = float(brier_score_loss(y, p))
    brier_clim = float(np.mean((clim - y) ** 2))
    res["brier"] = brier
    res["bss"] = 1.0 - brier / brier_clim if brier_clim > 0 else float("nan")

    # ROC-AUC / PR-AUC.
    res["roc_auc"] = _auc(y, p)
    ap = float(average_precision_score(y, p)) if y.min() != y.max() else float("nan")
    res["pr_auc"] = ap
    res["pr_auc_lift"] = ap / base if base > 0 else float("nan")

    # Deflated IC vs realized forward ATR return in the predicted direction.
    h = TARGET_HORIZON[target]
    v["_realized"] = TARGET_DIRECTION[target] * v[f"fwd_atr_ret_{h}"].astype("float64")
    res["ic"], res["ic_t_deflated"] = deflated_ic(v, pcol, "_realized", h)

    # Placebo permutation test (CB-05).
    aucs = []
    for s in range(meta["n_placebo_seeds"]):
        mask = oof[fcol] >= 0
        aucs.append(_auc(oof.loc[mask, f"y_{target}_pl{s}"].to_numpy().astype(int),
                         oof.loc[mask, f"p_{target}_pl{s}"].to_numpy().astype("float64")))
    aucs = [a for a in aucs if np.isfinite(a)]
    pl_mean = float(np.mean(aucs)) if aucs else float("nan")
    se = _auc_null_se(y) / math.sqrt(max(len(aucs), 1))
    pl_z = (pl_mean - 0.5) / se if se and np.isfinite(se) and se > 0 else float("nan")
    res["placebo_auc_mean"] = pl_mean
    res["placebo_auc_seeds"] = aucs
    res["placebo_z"] = pl_z
    res["cb05_triggered"] = bool(np.isfinite(pl_mean) and pl_mean > PLACEBO_AUC_MAX and pl_z > PLACEBO_Z_MIN)

    # Generalization gap.
    gaps = [f["train_pr_auc"] - f["val_pr_auc"] for f in folds
            if np.isfinite(f.get("train_pr_auc", np.nan)) and np.isfinite(f.get("val_pr_auc", np.nan))]
    res["gen_gap"] = float(np.mean(gaps)) if gaps else float("nan")
    res["calibration_methods"] = sorted({f["calibration"] for f in folds})

    # Regime stability.
    v["_regime"] = pd.to_datetime(v["date"]).map(regimes).fillna("Warmup")
    reg = {}
    for name, g in v.groupby("_regime"):
        b = g[ycol].mean()
        pk = precision_at_k(g, pcol, ycol)
        reg[name] = {
            "n_dates": int(g["date"].nunique()),
            "base_rate": float(b),
            "precision_at_k": pk,
            "lift": pk / b if b > 0 else float("nan"),
        }
    res["regimes"] = reg

    # SHAP dominance.
    shap = tmeta.get("shap_importance", {})
    if shap:
        top_feat, top_share = next(iter(shap.items()))
        res["shap_top_feature"] = top_feat
        res["shap_top_share"] = float(top_share)
        res["shap_dominance_flag"] = bool(top_share > SHAP_DOMINANCE_MAX)

    # Gate verdicts.
    res["checks"] = {
        "precision_lift": bool(np.isfinite(res["precision_lift"]) and res["precision_lift"] >= LIFT_MIN),
        "bss": bool(np.isfinite(res["bss"]) and res["bss"] > BSS_MIN),
        "pr_auc_lift": bool(np.isfinite(res["pr_auc_lift"]) and res["pr_auc_lift"] > PR_AUC_LIFT_MIN),
        "ic": bool(np.isfinite(res["ic"]) and res["ic"] > IC_MIN
                   and np.isfinite(res["ic_t_deflated"]) and res["ic_t_deflated"] > IC_T_MIN),
    }
    res["gate_pass"] = all(res["checks"].values()) and not res["cb05_triggered"]
    return res


# --------------------------------------------------------------------------- #
# CB-05 halt
# --------------------------------------------------------------------------- #
def trigger_cb05(market: str, offenders: list[str]) -> None:
    model_dir = MODELS_DIR / market.lower()
    if model_dir.exists():
        shutil.rmtree(model_dir)
        model_dir.mkdir(parents=True, exist_ok=True)
    PDF_BLOCK_FLAG.write_text(
        f"CRITICAL_LEAKAGE_DETECTED {market}: {', '.join(offenders)} "
        f"at {dt.datetime.now(dt.timezone.utc).isoformat()}\n"
    )
    state = json.loads(STATE_FILE.read_text())
    state["last_error"] = f"CRITICAL_LEAKAGE_DETECTED ({market}: {', '.join(offenders)})"
    STATE_FILE.write_text(json.dumps(state, indent=2))


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def _fmt(x, nd=3, pct=False) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "n/a"
    return f"{x:.1%}" if pct else f"{x:.{nd}f}"


def _mark(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def write_report(results: dict, regime_sources: dict, last_meta: dict | None = None) -> None:
    lines = [
        "# Sprint 4 — Model QA & Governance (Gate 4)",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).isoformat()}",
        f"- Validation: 5-fold purged walk-forward, 20-day embargo, `tree_method='hist'`, `n_jobs=2`",
        f"- Precision@K: per-date top-K bucket, K = min({PRECISION_K_MAX}, "
        f"{PRECISION_K_UNIVERSE_FRACTION:.0%} of universe, >= 1)",
        f"- Deflated IC: t-stat divided by sqrt(horizon) to correct for overlapping labels",
        f"- CB-05: placebo ROC-AUC > {PLACEBO_AUC_MAX} **and** z > {PLACEBO_Z_MIN} vs 0.5",
        "",
    ]
    for market, per_target in results.items():
        universe = last_meta.get("universe", {}) if last_meta else {}
        uni_str = (f"- Universe: **{universe.get('n_symbols', '?')} symbols**, "
                   f"{universe.get('n_rows', '?'):,} rows, "
                   f"{universe.get('date_min', '?')} → {universe.get('date_max', '?')}, "
                   f"source=`{universe.get('source', '?')}`")
        lines += [f"## {market}", "", uni_str, "", f"- Regime source: {regime_sources[market]}", "",
                  "### Governance metrics", "",
                  "| Target | Base rate | P@K lift (>=1.5) | BSS (>0.05) | PR-AUC lift (>1.35) | IC / t-defl (>0.04 / >2.5) | ROC-AUC | Gate |",
                  "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: |"]
        for r in per_target:
            if "error" in r:
                lines.append(f"| `{r['target']}` | — | — | — | — | — | — | {r['error']} |")
                continue
            c = r["checks"]
            lines.append(
                f"| `{r['target']}` | {_fmt(r['base_rate'], pct=True)} "
                f"| {_fmt(r['precision_lift'], 2)} {_mark(c['precision_lift'])} "
                f"| {_fmt(r['bss'])} {_mark(c['bss'])} "
                f"| {_fmt(r['pr_auc_lift'], 2)} {_mark(c['pr_auc_lift'])} "
                f"| {_fmt(r['ic'])} / {_fmt(r['ic_t_deflated'], 2)} {_mark(c['ic'])} "
                f"| {_fmt(r['roc_auc'])} | **{_mark(r['gate_pass'])}** |"
            )
        lines += ["", "### Diagnostic 1 — Placebo permutation test (CB-05)", "",
                  "| Target | Mean placebo ROC-AUC | z vs 0.5 | Seeds | CB-05 |",
                  "| :--- | ---: | ---: | :--- | :---: |"]
        for r in per_target:
            if "error" in r:
                continue
            seeds = ", ".join(f"{a:.3f}" for a in r["placebo_auc_seeds"])
            lines.append(
                f"| `{r['target']}` | {_fmt(r['placebo_auc_mean'])} | {_fmt(r['placebo_z'], 2)} "
                f"| {seeds} | {'**HALT**' if r['cb05_triggered'] else 'clear'} |"
            )
        lines += ["", "### Diagnostic 2 — Generalization gap (train PR-AUC − val PR-AUC)", "",
                  "| Target | Mean gap | Calibration | Recommendation |",
                  "| :--- | ---: | :--- | :--- |"]
        for r in per_target:
            if "error" in r:
                continue
            rec = ("tighten: max_depth 4→3, min_child_weight 20→40, colsample_bytree 0.7→0.5"
                   if np.isfinite(r["gen_gap"]) and r["gen_gap"] > GEN_GAP_MAX else "ok")
            lines.append(f"| `{r['target']}` | {_fmt(r['gen_gap'])} | {', '.join(r['calibration_methods'])} | {rec} |")
        lines += ["", "### Diagnostic 3 — Regime stability (P@K by regime)", "",
                  "| Target | Regime | Dates | Base rate | P@K | Lift |",
                  "| :--- | :--- | ---: | ---: | ---: | ---: |"]
        for r in per_target:
            if "error" in r:
                continue
            for name, g in sorted(r["regimes"].items()):
                lines.append(
                    f"| `{r['target']}` | {name} | {g['n_dates']} | {_fmt(g['base_rate'], pct=True)} "
                    f"| {_fmt(g['precision_at_k'], pct=True)} | {_fmt(g['lift'], 2)} |"
                )
        lines += ["", "### Diagnostic 4 — SHAP dominance (> 35% flag)", "",
                  "| Target | Top feature | Share of |SHAP| | Flag |",
                  "| :--- | :--- | ---: | :---: |"]
        for r in per_target:
            if "shap_top_feature" not in r:
                continue
            lines.append(
                f"| `{r['target']}` | `{r['shap_top_feature']}` | {_fmt(r['shap_top_share'], pct=True)} "
                f"| {'**DOMINANT**' if r['shap_dominance_flag'] else 'ok'} |"
            )
        lines.append("")
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n")


def main() -> int:
    init_dirs()
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", choices=["USD", "CAD", "ALL"], default="ALL")
    args = parser.parse_args()
    markets = ["USD", "CAD"] if args.market == "ALL" else [args.market]

    results, sources, halted = {}, {}, {}
    for mkt in markets:
        oof = pd.read_parquet(DATA_DIR / f"oof_{mkt}.parquet")
        meta = json.loads((DATA_DIR / f"train_meta_{mkt}.json").read_text())

        # Universe header: warn if fixture
        universe = meta.get("universe", {})
        source = universe.get("source", "unknown")
        if source == "fixture":
            print(f"[model_qa] FATAL: {mkt} model was trained on FIXTURE data ({universe.get('n_symbols', '?')} tickers). "
                  f"Re-run on real data. Exiting.", file=sys.stderr)
            sys.exit(3)
        n_sym = universe.get("n_symbols", oof["symbol"].nunique())
        k = _k_for(n_sym)
        if k < 5:
            print(f"[model_qa] WARNING: {mkt} K={k} (universe {n_sym} tickers) — P@K may be unstable")

        regimes, sources[mkt] = regime_series(mkt, oof)
        results[mkt] = [evaluate_target(oof, meta, t, regimes) for t in TARGET_COLUMNS]
        offenders = [r["target"] for r in results[mkt] if r.get("cb05_triggered")]
        if offenders:
            halted[mkt] = offenders
            trigger_cb05(mkt, offenders)

    write_report(results, sources, meta if len(markets) == 1 else None)

    summary = {
        mkt: {r["target"]: {"gate_pass": r.get("gate_pass", False),
                             "placebo_auc": r.get("placebo_auc_mean")} for r in rs}
        for mkt, rs in results.items()
    }
    update_state("EP-04", "gate_4", {"summary": summary, "cb05_halted": halted})

    for mkt, rs in results.items():
        for r in rs:
            if "error" in r:
                print(f"[model_qa] {mkt} {r['target']}: {r['error']}")
                continue
            print(f"[model_qa] {mkt} {r['target']}: gate={'PASS' if r['gate_pass'] else 'FAIL'} "
                  f"auc={_fmt(r['roc_auc'])} placebo={_fmt(r['placebo_auc_mean'])}")
    print(f"[model_qa] report -> {REPORT_PATH}")

    if halted:
        print(f"[model_qa] CB-05 HARD HALT: CRITICAL_LEAKAGE_DETECTED {halted}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
