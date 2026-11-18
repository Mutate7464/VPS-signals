"""WI-067 — regularised L2 stack ranker (D-027 §6): union cells → clusters → CALIB-only stack → WI-066 ranker.

Layer 2 (D-027 §7): pre-cluster correlated cells on CALIB OOF correlation, keep one **logged** representative per
cluster, fit a regularised stack (ridge linear-probability or the saga elastic net) on cluster scores + the WI-064
meta OOF + regime metafeatures — CALIB only, purged CV — then feed the OOF stack score into the WI-066 top-k ranker.
EVAL is never read (WI-071 owns the one-shot). The stack must beat the best single WI-066 signal on CALIB net edge
AND on the fold report, else the card stops with no stack-score artifact.

    uv run python -m src.l2_overlay.constructions.stack_rank --smoke   # synthetic, *_smoke roots
    uv run python -m src.l2_overlay.constructions.stack_rank           # full CALIB run = PM gate

Invariants: n_jobs=2, float32 immediately, chunked reads (`prune.load_cell_matrix`), cluster BEFORE fit, purged CV,
no EVAL read.
"""
from __future__ import annotations

import argparse, datetime as dt
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.l2_overlay import fold_report as foldrep
from src.l2_overlay import harness as H
from src.l2_overlay import prune
from src.l2_overlay.constructions import xsec_rank as xr
from src.l2_overlay.costs import SINGLE_LEG_BPS, bps_to_frac
from src.l2_overlay.prune import FULL_SCALE, MEMORY_CEILING_GB, assert_memory_budget, projected_peak_gb

BASE_DIR = Path(__file__).resolve().parents[3]        # named input/output roots (never CLI args)
META_OOF_ROOT, META_OOF_SMOKE_ROOT = BASE_DIR / "data/models/l2_meta_oof", BASE_DIR / "data/models/l2_meta_oof_smoke"
SCORE_ROOT, SCORE_SMOKE_ROOT = BASE_DIR / "data/models/l2_stack_rank", BASE_DIR / "data/models/l2_stack_rank_smoke"
REPORTS_ROOT, REPORTS_SMOKE_ROOT = BASE_DIR / "reports/l2_stack_rank", BASE_DIR / "reports/l2_stack_rank_smoke"
MARKETS: tuple[str, ...] = ("USD", "CAD")
META_COLUMNS, REGIME_FEATURES = ("date", "symbol", "p_oof", "fold"), ("disp_entropy_39", "vol_regime_spread")
PRUNE_THRESHOLD, N_JOBS, MAX_ITER, TOL = prune.PRUNE_THRESHOLD, 2, 1000, 1e-3
N_SPLITS, EMBARGO_TD, SEED, MIN_FIT_ROWS, L1_RATIO, STACK_KIND = 5, 20, 67, 50, 0.5, "ridge"
SMOKE_DATES, SMOKE_NAMES, SMOKE_CELLS, SMOKE_SEED = 180, 30, 12, 11
__all__ = ["EvalLeak", "StackModel", "assert_calib_only", "assert_memory_budget", "beats_best_single", "best_single",
           "build_design", "fit_stack", "load_market", "load_meta_oof", "main", "projected_peak_gb", "purged_splits",
           "run_market", "stack_guard", "stack_labels", "synthetic_fixture", "tune_stack", "write_calib_report"]


class EvalLeak(RuntimeError):
    """Raised when a row at/after `EVAL_START` reaches a CALIB-only structure."""


def _fmt(x, spec: str = "{:.4f}") -> str:
    return "n/a" if not np.isfinite(float(x)) else spec.format(float(x))


def assert_calib_only(dates, *, eval_start: str = H.EVAL_START) -> int:
    """EVAL lock: an EVAL/undated row reaching a CALIB-only structure is a defect, not a warning."""
    d = pd.to_datetime(pd.Series(np.asarray(dates)))
    bad = int(((d >= pd.Timestamp(eval_start)) | d.isna()).sum())
    if bad:
        raise EvalLeak(f"{bad} EVAL/undated rows reached a CALIB-only structure (eval_start {eval_start})")
    return int(len(d))


def load_meta_oof(market: str, *, smoke: bool = False, root=None) -> pd.DataFrame:
    """WI-064 meta OOF (`*_smoke` variant when `smoke`): date/symbol/p_oof/fold, float32, CALIB only."""
    base = Path(root) if root is not None else (META_OOF_SMOKE_ROOT if smoke else META_OOF_ROOT)
    path = base / f"{market}_oof.parquet"
    if not path.exists():
        raise FileNotFoundError(f"WI-064 meta OOF missing: {path} (the full run is a PM gate)")
    frame = pd.read_parquet(path)
    if [c for c in META_COLUMNS if c not in frame.columns]:
        raise KeyError(f"{path.name} lacks {[c for c in META_COLUMNS if c not in frame.columns]}")
    out = frame.loc[:, list(META_COLUMNS)].copy()
    out[["date", "symbol", "p_oof"]] = out[["date", "symbol", "p_oof"]].assign()   # float32 immediately
    out["date"], out["symbol"] = pd.to_datetime(out["date"]), out["symbol"].astype(str)
    out["p_oof"] = out["p_oof"].astype("float32")
    assert_calib_only(out["date"])
    return out


def load_market(market: str) -> dict:
    """PM-gate full-CALIB inputs: prepared panel + union cell OOF matrix (aligned) + WI-064 meta OOF."""
    panel = xr.load_candidates(market)                    # raises until the PM prepared panel lands
    matrix, log = prune.load_cell_matrix(market)          # chunked float32 reads, every cell logged
    cells = [str(c) for c in matrix.columns if c not in ("date", "symbol")]
    keys = pd.DataFrame({"date": pd.to_datetime(panel["date"]).to_numpy(),
                         "symbol": panel["symbol"].astype(str).to_numpy()})
    aligned = keys.merge(matrix, on=["date", "symbol"], how="left", sort=False)
    if len(aligned) != len(keys):
        raise ValueError("union OOF keys are not unique per (date, symbol)")
    return {"panel": panel, "cells": cells, "matrix": aligned.astype({c: "float32" for c in cells}),
            "meta": load_meta_oof(market), "load_log": log}


def stack_labels(r, *, cost_bps: float = SINGLE_LEG_BPS) -> np.ndarray:
    """Binary L2 meta-label: the trade clears the round trip (a decision, never an AUC claim)."""
    return (np.asarray(r, dtype="float64") > float(bps_to_frac(float(cost_bps)))).astype("float32")


def build_design(panel, matrix, clustering, meta, *, regime=REGIME_FEATURES):
    """Cluster scores (clustered BEFORE the fit) + meta OOF + regime metafeatures → float32 X; y from `r`."""
    X = prune.cluster_scores(matrix, clustering).reset_index(drop=True)
    keys = pd.DataFrame({"pos": np.arange(len(panel)), "symbol": np.asarray(panel["symbol"]).astype(str),
                         "date": pd.to_datetime(pd.Series(np.asarray(panel["date"]))).to_numpy()})
    m = meta.loc[:, ["date", "symbol", "p_oof"]].copy()
    m["date"], m["symbol"] = pd.to_datetime(m["date"]), m["symbol"].astype(str)
    joined = keys.merge(m, on=["date", "symbol"], how="left", sort=False).sort_values("pos", kind="mergesort")
    if len(joined) != len(keys):
        raise ValueError("meta OOF keys are not unique per (date, symbol)")
    X["meta_p_oof"] = joined["p_oof"].to_numpy("float32")
    for col in regime:        # an absent causal column stays NaN for the imputer, never invented
        X[str(col)] = (np.asarray(panel[col], "float32") if col in panel.columns
                       else np.full(len(panel), np.nan, "float32"))
    return X.astype("float32"), stack_labels(panel["r"])


def purged_splits(dates, *, n_splits: int = N_SPLITS, embargo_td: int = EMBARGO_TD):
    """Purged walk-forward fold indices (WI-009 splitter reused so the embargo never drifts)."""
    from src.xgb_trainer import PurgedWalkForwardSplit    # lazy: keeps this module's import light
    return list(PurgedWalkForwardSplit(n_splits=int(n_splits), embargo_td=int(embargo_td)).split(dates))


def _estimator(kind: str, *, seed: int = SEED) -> Pipeline:
    """Impute → standardise → regularised learner, all inside the fold (no preprocessing leakage)."""
    head = [("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]
    if kind == "ridge":                                   # L2 linear-probability score
        return Pipeline([*head, ("rd", Ridge(alpha=1.0, random_state=seed))])
    if kind == "elasticnet":                              # sparse alternative (sklearn ≥ 1.8 form)
        return Pipeline([*head, ("lr", LogisticRegression(l1_ratio=L1_RATIO, C=1.0, solver="saga",
                                                          max_iter=MAX_ITER, tol=TOL, random_state=seed))])
    raise KeyError(f"unknown stack kind {kind!r}; expected 'ridge' or 'elasticnet'")


def _score_fold(model, X, kind: str) -> np.ndarray:
    """Score rows with a fitted pipeline; the elastic net yields a probability, the ridge a score."""
    X = np.asarray(X, dtype="float32")
    return (np.asarray(model.predict_proba(X)[:, 1], "float32") if kind == "elasticnet"
            else np.asarray(model.predict(X), "float32"))


@dataclass
class StackModel:
    """CALIB-only stack: purged-CV OOF scores (for the ranker) + a refit on all CALIB rows (`score`)."""
    feats: list
    kind: str
    model: Pipeline
    oof: np.ndarray
    fold_id: np.ndarray
    n_folds: int

    def score(self, X) -> np.ndarray:
        """Score with the full-CALIB refit; the EVAL one-shot belongs to WI-071."""
        return _score_fold(self.model, X, self.kind)


def fit_stack(X_calib, y_calib, *, dates=None, feats=None, kind: str = STACK_KIND, seed: int = SEED,
              n_splits: int = N_SPLITS, embargo_td: int = EMBARGO_TD) -> StackModel:
    """Fit the regularised stack CALIB-only: purged-CV OOF scores, then a refit on all CALIB rows."""
    X, y = np.asarray(X_calib, "float32"), np.asarray(y_calib, "float32")
    if X.ndim != 2 or X.shape[0] != y.shape[0]:
        raise ValueError(f"X {X.shape} and y {y.shape} are not aligned CALIB rows")
    d = np.arange(X.shape[0])                # positional fallback: contiguous blocks, same embargo
    if dates is not None:
        assert_calib_only(dates)             # EVAL lock: a leaked row kills the fit outright
        d = np.asarray(pd.to_datetime(pd.Series(np.asarray(dates))))
    oof, fold_id, n_folds = np.full(y.shape[0], np.nan, "float32"), np.full(y.shape[0], -1, "int16"), 0
    for k, (tr, va) in enumerate(purged_splits(d, n_splits=n_splits, embargo_td=embargo_td)):
        if tr.size < MIN_FIT_ROWS or va.size == 0:
            continue
        oof[va] = _score_fold(_estimator(kind, seed=seed).fit(X[tr], y[tr]), X[va], kind)
        fold_id[va], n_folds = k, n_folds + 1
    final = _estimator(kind, seed=seed).fit(X, y)         # CALIB refit, still CALIB-only
    return StackModel(list(feats) if feats is not None else [f"x{i}" for i in range(X.shape[1])],
                      kind, final, oof, fold_id, n_folds)


def tune_stack(panel, score, k_grid=xr.K_GRID, band_grid=xr.BAND_GRID, h_grid=xr.HORIZON_GRID) -> dict:
    """Feed the stack score into the WI-066 ranker through its raw-score hook (`b_hold` = raw score).

    `p_b_hold` is dropped so the signal is the score vector itself; the grid, hysteresis, capacity cap and cost
    model are WI-066's own, and `best_single` runs the identical path — the guard compares like for like.
    """
    frame = panel.drop(columns=["p_b_hold"], errors="ignore").assign(b_hold=np.asarray(score, "float32"))
    return {"signal": "stack", **xr.tune_signal(frame, "b_hold", k_grid=k_grid, band_grid=band_grid, h_grid=h_grid)}


def best_single(panel, signals=xr.SIGNALS) -> dict:
    """Best single WI-066 signal on CALIB net edge — the stack's frozen comparison baseline."""
    rows = [{"signal": s, **xr.tune_signal(panel, s)} for s in signals]
    ok = [r for r in rows if np.isfinite(r["net_edge_bps"])]
    return max(ok or rows, key=lambda r: (r["net_edge_bps"], -r["trades_per_week"]))


def _worst_fold(rep: dict) -> float:
    """Lowest finite per-fold net edge (fraction) in a fold report; NaN when no fold is finite."""
    vals = np.asarray([float(v) for v in rep.get("per_fold_net_edge", {}).values()], dtype="float64")
    vals = vals[np.isfinite(vals)]
    return float(vals.min()) if vals.size else float("nan")


def beats_best_single(stack, single) -> dict:
    """D-027 §7 (WI-033 pattern): the stack must win on CALIB net edge AND on the fold report."""
    reasons, s_edge, b_edge = [], float(stack["net_edge_bps"]), float(single["net_edge_bps"])
    s_rep, b_rep = stack["fold_report"], single["fold_report"]
    s_fold, b_fold = _worst_fold(s_rep), _worst_fold(b_rep)
    if not np.isfinite(s_edge) or s_edge <= b_edge:
        reasons.append(f"stack CALIB net edge {_fmt(s_edge, '{:+.1f}')} bps does not beat the best single "
                       f"`{single['signal']}` {_fmt(b_edge, '{:+.1f}')} bps")
    if not s_rep["fold_ceiling_ok"]:
        reasons.append(f"stack fails the fold ceiling (share {_fmt(s_rep['max_fold_share'])}, positive folds "
                       f"{s_rep['n_positive_folds']}/{s_rep['n_folds']})")
    if np.isfinite(s_fold) and np.isfinite(b_fold) and s_fold < b_fold:
        reasons.append(f"stack worst fold {_fmt(1e4 * s_fold, '{:+.1f}')} bps below the best single "
                       f"{_fmt(1e4 * b_fold, '{:+.1f}')} bps")
    return {"beats": not reasons, "reasons": reasons, "stack_net_edge_bps": s_edge, "single_net_edge_bps": b_edge,
            "single_signal": str(single["signal"]), "stack_worst_fold": s_fold, "single_worst_fold": b_fold}


def stack_guard(stack, single, *, floor_bps: float = H.MATERIALITY_FLOOR_BPS) -> dict:
    """Beats-best-single guard + the D-027 §7 CALIB stop: any reason stops the card (no artifact)."""
    guard = beats_best_single(stack, single)
    stop = H.calib_stop(stack["net_edge_bps"], stack["fold_report"], floor_bps=float(floor_bps))
    return {"stop": bool((not guard["beats"]) or stop["stop"]), "reasons": list(stop["reasons"]) + guard["reasons"],
            "beats_best_single": bool(guard["beats"]), "calib_stop": stop, "guard": guard}


def write_calib_report(path, market: str, res: dict, *, smoke: bool = False) -> Path:
    """CALIB card (D-027 §7): pruning log, design, guard vs the best single, fold report, stop flag."""
    cl, stack, single, guard = res["clustering"], res["stack"], res["single"], res["guard"]
    rep, b, now = stack["fold_report"], res["budget"], dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [f"# L2 stack ranker — {market} (D-027 §6 regularised stack)", "", f"- Generated (UTC): {now}",
             "- Scope: CALIB only (cluster → fit → rank; EVAL unread — WI-071)"
             f"{'  (smoke / synthetic)' if smoke else ''}",
             f"- Cells: {res['n_cells']} input, {len(cl.cluster_rep)} clusters at |rho|>{res['prune_threshold']:g} "
             f"(representatives kept and logged; nothing dropped silently)",
             f"- Design: {res['n_rows']:,} CALIB rows x {res['n_features']} features (cluster scores + meta OOF + "
             f"{len(res['regime'])} regime metafeatures: {', '.join(res['regime'])})",
             f"- Fit: {res['kind']}, {res['n_folds']} purged folds, embargo {res['embargo_td']} td; projected peak "
             f"{b['projected_peak_gb']:.2f} GB at {b['n_events']:,} x {b['n_cols']} (ceiling {b['ceiling_gb']:.1f} GB, pass)",
             f"- Ranker window: {res['n_oof_rows']:,}/{res['n_rows']:,} CALIB rows carry a purged-CV OOF score; the "
             f"rest are unranked, never scored in-sample",
             f"- Stack: k={int(stack['k'])}, band={float(stack['band']):g}, horizon={int(stack['horizon'])} "
             f"({int(stack['n_trials'])} trials), {stack['trades_per_week']:.2f} trades/week, turnover f "
             f"{stack['turnover_f']:.4f} -> cost {stack['cost_bps']:.1f} bps; net edge {stack['net_edge_bps']:+.1f} "
             f"bps (gross {stack['gross_edge_bps']:+.1f})",
             f"- Best single: `{single['signal']}` net edge {single['net_edge_bps']:+.1f} bps (k={int(single['k'])}, "
             f"band={float(single['band']):g}, horizon={int(single['horizon'])})",
             f"- Guard beats-best-single: **{'YES' if guard['beats_best_single'] else 'NO'}**",
             f"- Fold report: max-fold share {_fmt(rep['max_fold_share'])} (ceiling {foldrep.FOLD_CEILING_SHARE:.0%}, "
             f"{'pass' if rep['fold_ceiling_ok'] else 'FAIL'}); positive folds {rep['n_positive_folds']}/{rep['n_folds']}",
             f"- Stop flag: **{'STOP' if guard['stop'] else 'CONTINUE'}**"
             + (" — " + "; ".join(guard["reasons"]) if guard["reasons"] else ""),
             f"- Stack-score artifact: {Path(res['artifact']).name if res['artifact'] else 'none (stopped)'}",
             "", "| cell | cluster | representative | kept | reason |", "| --- | ---: | --- | --- | --- |"]
    lines += [f"| {r['cell']} | {r['cluster']} | {r['representative']} | {'yes' if r['kept'] else 'no'} | {r['reason']} |"
              for r in cl.log]
    lines += ["", "Record-only: no shortlist, no deployment, no live trading."]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return path


def synthetic_fixture(market: str = "USD", *, n_dates: int = SMOKE_DATES, n_names: int = SMOKE_NAMES,
                      n_cells: int = SMOKE_CELLS, seed: int = SMOKE_SEED) -> dict:
    """Deterministic smoke panel (no `data/` read, no EVAL rows): driver `z1 + z2`, cells cover `z1` then `z2`.

    The WI-066 single signals see `z1` only, so the stack is expected to beat the best single. Rows are built in
    (date, symbol) order — no sort can misalign a latent array.
    """
    rng, n = np.random.default_rng(seed), int(n_dates) * int(n_names)
    z1, z2 = (rng.normal(0.0, 1.0, n).astype("float32") for _ in range(2))
    cells = {f"cell_{market}_{i:02d}": ((z1 if i < int(n_cells) // 2 else z2) + rng.normal(0.0, 0.6, n)).astype("float32")
             for i in range(int(n_cells))}
    panel = pd.DataFrame({
        "date": np.repeat(pd.date_range("2021-01-04", periods=int(n_dates), freq="B").to_numpy(), int(n_names)),
        "symbol": np.tile(np.array([f"{market}{i:02d}" for i in range(int(n_names))]), int(n_dates)),
        "fold": np.repeat(np.arange(int(n_dates)) % N_SPLITS, int(n_names)).astype("int64"),
        "r": (0.02 * (z1 + z2) + rng.normal(0.0, 0.012, n)).astype("float32"),
        "xsec_vol_rank_cont": (z1 + rng.normal(0.0, 0.7, n)).astype("float32"),
        "move_occur": rng.random(n).astype("float32"),
        "move_dir_up": (z1 + rng.normal(0.0, 0.7, n)).astype("float32"),
        "p_b_hold": (1.0 / (1.0 + np.exp(-z1.astype("float64")))).astype("float32"),
        **cells, **{c: rng.normal(0.0, 1.0, n).astype("float32") for c in REGIME_FEATURES}})
    meta = panel.loc[:, ["date", "symbol", "fold"]].assign(
        p_oof=(1.0 / (1.0 + np.exp(-(z1 + z2).astype("float64")))).astype("float32"))
    return {"panel": panel, "meta": meta, "cells": list(cells), "regime": list(REGIME_FEATURES)}


def run_market(market: str, panel: pd.DataFrame, meta: pd.DataFrame, *, matrix=None, cells=None,
               regime=REGIME_FEATURES, score_root=SCORE_ROOT, report_root=REPORTS_ROOT, smoke: bool = False,
               prune_threshold: float = PRUNE_THRESHOLD, kind: str = STACK_KIND, budget_scale=prune.FULL_SCALE) -> dict:
    """Cluster BEFORE fit → CALIB-only stack → WI-066 ranker → beats-best-single guard → CALIB card."""
    panel = panel.sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)
    assert_calib_only(panel["date"])                 # EVAL lock: the OOF matrix never sees an EVAL row
    cols = [str(c) for c in (cells if cells is not None else [c for c in panel.columns if str(c).startswith("cell_")])]
    grid = panel[cols] if matrix is None else pd.DataFrame(np.asarray(matrix, "float32"), columns=cols)
    budget = prune.assert_memory_budget(*budget_scale)    # smoke-scaled extrapolation of the full run
    pre = xr.rank_scores(panel.assign(xsec_vol_rank_cont=grid.mean(axis=1).to_numpy("float32")),
                         "xsec_vol_rank_cont")            # WI-066 rank transform on the union mean
    ok, reason = H.xsec_inert_precheck(pre, panel.groupby("date")["symbol"].size().to_numpy())
    if not ok:
        print(f"[l2.stack] {market}: {reason}")
        return {"market": market, "verdict": "INERT", "reason": reason, "cells": cols, "artifact": None}
    clustering = prune.cluster_by_correlation(grid, prune_threshold)
    X, y = build_design(panel, grid, clustering, meta, regime=regime)
    model = fit_stack(X, y, dates=panel["date"], feats=list(X.columns), kind=kind)
    # Only rows with a purged-CV OOF score can be ranked (no score ⇒ no decision, never in-sample); the stack and
    # the best single are judged on that same window, so the guard compares like for like.
    scored = np.isfinite(model.oof)
    window = panel[scored].reset_index(drop=True)
    stack, single = tune_stack(window, model.oof[scored]), best_single(window)
    guard = stack_guard(stack, single)
    res = {"market": market, "verdict": "CONTINUE" if not guard["stop"] else "STOP", "smoke": bool(smoke),
           "clustering": clustering, "n_cells": len(cols), "prune_threshold": float(prune_threshold),
           "n_rows": int(len(X)), "n_features": int(X.shape[1]), "kind": kind, "n_folds": int(model.n_folds),
           "n_oof_rows": int(scored.sum()), "embargo_td": EMBARGO_TD, "budget": budget, "regime": list(regime),
           "stack": stack, "single": single, "guard": guard, "artifact": None}
    if not guard["stop"]:                            # a stopped card emits no stack-score artifact
        path = Path(score_root) / f"{market}_stack.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"date": pd.to_datetime(panel["date"]), "symbol": panel["symbol"].astype(str),
                      "fold": np.asarray(panel["fold"], "int64"), "r": np.asarray(panel["r"], "float32"),
                      "stack_score": np.asarray(model.oof, "float32")}).to_parquet(path, index=False)
        res["artifact"] = path
    res["report"] = write_calib_report(Path(report_root) / f"calib_{market}.md", market, res, smoke=smoke)
    print(f"[l2.stack] {market}: {len(clustering.cluster_rep)} clusters/{len(cols)} cells, {len(X):,} CALIB rows, "
          f"stack {stack['net_edge_bps']:+.1f} bps vs best single `{single['signal']}` "
          f"{single['net_edge_bps']:+.1f} bps -> {res['verdict']}")
    return res


def main(argv=None) -> int:
    """CLI: `--smoke` (synthetic, `*_smoke` roots) or the full CALIB run (PM gate, EVAL unread)."""
    ap = argparse.ArgumentParser(description="WI-067 regularised L2 stack ranker (D-027 §6)")
    ap.add_argument("--smoke", action="store_true", help="synthetic run into the *_smoke roots")
    ap.add_argument("--kind", default=STACK_KIND, choices=("ridge", "elasticnet"))
    args = ap.parse_args(argv)
    for i, mk in enumerate(MARKETS):
        if args.smoke:
            fx = synthetic_fixture(mk, seed=SMOKE_SEED + i)
            run_market(mk, fx["panel"], fx["meta"], cells=fx["cells"], regime=fx["regime"], kind=args.kind,
                       score_root=SCORE_SMOKE_ROOT, report_root=REPORTS_SMOKE_ROOT, smoke=True)
        else:
            data = load_market(mk)
            run_market(mk, data["panel"], data["meta"], matrix=data["matrix"][data["cells"]],
                       cells=data["cells"], kind=args.kind)
    if args.smoke:
        print(f"[l2.stack] smoke artifacts -> {REPORTS_SMOKE_ROOT}, {SCORE_SMOKE_ROOT} | EXIT:0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
