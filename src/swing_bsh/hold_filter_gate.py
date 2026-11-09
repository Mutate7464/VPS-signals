"""WI-037 — P(hold) trade-suppression filter on the frozen fib rules (D-022 phase 2).

Inference only: the WI-036 winning cell (`exact_full_k0.8` xgboost `b_hold` h13 fold
pickles in `data/models/wi036/`) gives a fold-consistent OOF P(hold) at the frozen
fib-rule at-bottom entries; an entry is VETOED when P(hold) >= tau. tau is tuned on the
CALIB window only and frozen before EVAL. Gate: ADOPT_LOOSE_4OF5 + CB-05 5-seed placebo.

    WI037_SMOKE=5 python -m src.swing_bsh.hold_filter_gate --out /tmp/wi037_smoke
    python -m src.swing_bsh.hold_filter_gate --market ALL
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

from src.swing_bsh import binary_features_ext as ext
from src.swing_bsh import binary_grid, binary_labels, binary_train, evaluate, train
from src.xgb_trainer import PurgedWalkForwardSplit

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "reports"
MODEL_DIR = BASE_DIR / "data" / "models" / "wi036"
ADOPT_DIR = BASE_DIR / "data" / "models" / "wi037"
REPORT_NAME = "wi037_summary.md"
VARIANT, BINARY, HORIZON = ext.variant_name("exact", "full", 0.8), "b_hold", 13
TAU_GRID: tuple[float, ...] = (0.5, 0.6, 0.7, 0.8)
N_SPLITS, N_PLACEBO_SEEDS, PLACEBO_SEED0, MIN_KEEP = 5, 5, 7000, 100
CALIB_END, EVAL_START, CORE_HOUR_CAP = "2022-05-02", "2022-07-01", 0.5


def design_matrix(panel: pd.DataFrame):
    """Re-derive the WI-036 design matrix (rho>0.3 prune -> engineer -> float32)."""
    kept, _dropped = binary_labels.kept_features(panel, threshold=binary_grid.PRUNE_RHO,
                                                 features=ext.candidate_features(panel))
    eng = train.engineer(panel)
    eng["k"], eng["horizon"] = np.float32(1.0), np.float32(21.0)  # cell constants (WI-036 driver)
    X, feats = train.feature_matrix(eng, binary_labels.feature_names(kept))
    if any(binary_labels.is_leakage_column(f) for f in feats):
        raise RuntimeError("label / forward-outcome column leaked into the design matrix")
    return X, feats


def loaded_models(market: str, model_dir: Path = MODEL_DIR) -> dict:
    """The fold pickles of the WI-036 winning cell, keyed by fold index."""
    tag, out = f"{market}_xgboost_{VARIANT}_{BINARY}_h{HORIZON}", {}
    for k in range(N_SPLITS):
        path = Path(model_dir) / f"{tag}_f{k}.pkl"
        if path.exists():
            with open(path, "rb") as fh:
                out[k] = pickle.load(fh)["model"]
    return out


def oof_hold_proba(X, fold_id, models) -> np.ndarray:
    """Fold-consistent OOF P(hold): each fold pickle scores only its own OOF rows."""
    p = np.full(len(fold_id), np.nan, dtype="float64")
    for k, model in models.items():
        rows = np.asarray(fold_id) == k
        if rows.any():
            p[rows] = np.asarray(model.predict_proba(X[rows]), dtype="float64").ravel()
    return p


def keep_mask(p_hold, tau: float) -> np.ndarray:
    """Frozen veto rule: keep an entry iff P(hold) < tau (VETO when P >= tau)."""
    return np.asarray(p_hold, dtype="float64") < float(tau)


def edge_of(ret, kept) -> float:
    """Filtered mean minus the all-entry (baseline) mean (WI-035 statistic, reused)."""
    return binary_train.selection_edge(kept, ret)


def baseline_returns(market: str, baseline_dir=None) -> pd.DataFrame:
    """Frozen fib-rule return per at-bottom entry (WI-028 entry + WI-030 exit, 25 bps inside)."""
    path = Path(baseline_dir or "/tmp/wi035") / f"wi035_panel_{market}.parquet"
    panel = (pd.read_parquet(path, columns=["symbol", "date", "state", "k", "horizon", "r_frozen"])
             if path.exists() else binary_labels.build_binary_panel(
                 market, k_values=(train.GATE_K,), barriers=(train.GATE_H,)))
    sel = ((panel["state"].to_numpy() == "at_bottom")
           & (panel["k"].to_numpy(dtype="float64") == float(train.GATE_K))
           & (panel["horizon"].to_numpy(dtype="float64") == float(train.GATE_H))
           & np.isfinite(panel["r_frozen"].to_numpy(dtype="float64")))
    return pd.DataFrame({"symbol": panel["symbol"].astype(str).to_numpy()[sel],
                         "date": panel["date"].to_numpy()[sel],
                         "r_frozen": panel["r_frozen"].to_numpy(dtype="float64")[sel]})


def tradeable_frame(panel, p_hold, fold_id, baseline, sub=None) -> pd.DataFrame:
    """At-bottom entries carrying OOF P(hold), fold and priced baseline (`pos` = array row)."""
    sub = np.arange(len(panel)) if sub is None else np.asarray(sub)
    meta = pd.DataFrame({"pos": np.arange(sub.size), "fold": np.asarray(fold_id)[sub].astype(int),
                         "symbol": panel["symbol"].astype(str).to_numpy()[sub],
                         "date": panel["date"].to_numpy()[sub],
                         "state": panel["state"].astype(str).to_numpy()[sub],
                         "p_hold": np.asarray(p_hold, dtype="float64")[sub]})
    meta = meta[(meta["state"] == "at_bottom") & (meta["fold"] >= 0)
                & np.isfinite(meta["p_hold"].to_numpy())]
    return meta.reset_index(drop=True).merge(baseline, on=["symbol", "date"], how="inner")


def pick_tau(frame, grid=TAU_GRID, min_keep: int = MIN_KEEP, calib_end: str = CALIB_END) -> dict:
    """tau from CALIB-period entries only (max edge, then most vetoes, then loosest tau)."""
    calib = frame[frame["date"].to_numpy() < np.datetime64(calib_end)]
    ret, p = calib["r_frozen"].to_numpy(dtype="float64"), calib["p_hold"].to_numpy()
    table = [{"tau": float(t), "n_kept": int(keep_mask(p, t).sum()), "edge": edge_of(ret, keep_mask(p, t)),
              "n_vetoed": int((~keep_mask(p, t)).sum())} for t in grid]
    ok = sorted([r for r in table if r["n_kept"] >= int(min_keep) and np.isfinite(r["edge"])],
                key=lambda r: (-r["edge"], -r["n_vetoed"], r["tau"]))
    return {"tau": float((ok[0] if ok else dict(table[0], edge=float("nan")))["tau"]),
            "table": table, "n_calib": int(len(calib))}


def drop_eval(frame: pd.DataFrame) -> pd.DataFrame:
    """Rows strictly before the one-shot EVAL window (dry-run scoring set)."""
    return frame[frame["date"].to_numpy() < np.datetime64(EVAL_START)].reset_index(drop=True)


def frame_stats(frame, tau, kept=None, include_eval: bool = True) -> dict:
    """Kept/vetoed means, edge, veto precision / prevalence, plus the EVAL-window block."""
    ret, y = frame["r_frozen"].to_numpy(dtype="float64"), frame["y_hold"].to_numpy(dtype="float64")
    kept = keep_mask(frame["p_hold"].to_numpy(), tau) if kept is None else np.asarray(kept, bool)
    pos = ((frame["date"].to_numpy() >= np.datetime64(EVAL_START)) if include_eval
           else np.zeros(len(frame), dtype=bool))
    ek = keep_mask(frame["p_hold"].to_numpy()[pos], tau)
    return {"n": int(len(frame)), "n_kept": int(kept.sum()), "n_vetoed": int((~kept).sum()),
            "baseline": float(ret.mean()) if ret.size else float("nan"),
            "filtered": float(ret[kept].mean()) if kept.any() else float("nan"),
            "edge": edge_of(ret, kept),
            "precision": float(y[~kept].mean()) if (~kept).any() else float("nan"),
            "prevalence": float(y.mean()) if y.size else float("nan"),
            "eval_scored": bool(include_eval), "n_eval": int(pos.sum()), "n_eval_kept": int(ek.sum()),
            "eval_baseline": float(ret[pos].mean()) if pos.any() else float("nan"),
            "eval_edge": edge_of(ret[pos], ek)}


def placebo_z(frame, X, y, dates, params, splitter, tau, *, n_seeds: int = N_PLACEBO_SEEDS,
              seed0: int = PLACEBO_SEED0, budget=None) -> dict:
    """CB-05: permute `b_hold` and refit (the only refits), re-applying the frozen tau."""
    ret, pos = frame["r_frozen"].to_numpy(dtype="float64"), frame["pos"].to_numpy(dtype=int)
    observed = edge_of(ret, keep_mask(frame["p_hold"].to_numpy(), tau))
    null: list[float] = []
    seed_sec = None
    for s in range(n_seeds):
        if s and budget is not None and seed_sec is not None and budget.left() < seed_sec * 1.2:
            break
        t0 = time.time()
        y_perm = np.random.default_rng(seed0 + s).permutation(np.asarray(y, dtype="int8"))
        cv = binary_grid.cell_cv(X, y_perm, dates, "xgboost", params["xgboost"], splitter, None,
                                 tag="wi037_placebo")
        null.append(edge_of(ret, keep_mask(np.asarray(cv["oof"])[pos], tau)))
        seed_sec = time.time() - t0
    arr = np.asarray([v for v in null if np.isfinite(v)], dtype="float64")
    mean = float(arr.mean()) if arr.size else float("nan")
    sd = float(arr.std(ddof=1)) if arr.size > 1 else float("nan")
    return {"observed_edge": observed, "null_mean": mean, "null_sd": sd, "n_seeds": int(arr.size),
            "z": float((observed - mean) / sd) if np.isfinite(sd) and sd > 0.0 else float("nan")}


def run_market(market: str, cfg: dict, *, model_dir=MODEL_DIR, cache_dir=None, baseline_dir=None,
               out_dir=REPORTS_DIR, limit=None, placebo_seeds: int = N_PLACEBO_SEEDS, budget=None,
               smoke: bool = False) -> dict:
    """Score one market's P(hold) veto filter against the frozen fib-rule baseline.

    `smoke=True` (dry run) never scores the one-shot EVAL block: EVAL-window rows are
    dropped before the fold gate / placebo, so only the full-universe job touches them.
    """
    t0 = time.time()
    budget = budget or binary_grid.CoreBudget(CORE_HOUR_CAP)
    panel, labels = ((None, None) if cache_dir is None else
                     ext.load_variant_panel(cache_dir, market, [(VARIANT, HORIZON)]))
    if panel is None or not labels:
        panel, labels = ext.build_variant_panel(market, variants=[(VARIANT, "exact", "full", 0.8)],
                                                horizons=(HORIZON,), max_symbols=limit)
    if panel.empty:
        raise RuntimeError(f"no swing events for market={market}")
    X, feats = design_matrix(panel)
    dates = panel["date"].to_numpy()
    splitter = PurgedWalkForwardSplit(n_splits=N_SPLITS, embargo_td=train.embargo_for([HORIZON]))
    fold_id = np.full(len(dates), -1, dtype="int16")
    for k, (_tr, va) in enumerate(splitter.split(dates)):
        fold_id[va] = k
    y = np.asarray(labels[(VARIANT, HORIZON)][BINARY], dtype="int8")
    models = loaded_models(market, model_dir)
    if any(int(getattr(getattr(m, "model", None), "n_features_in_", len(feats))) != len(feats)
           for m in models.values()):
        raise RuntimeError(f"pickle/matrix feature-width mismatch: {len(feats)} columns")
    p_hold = oof_hold_proba(X, fold_id, models)
    symbols = panel["symbol"].astype(str)
    sub = (np.arange(len(panel)) if limit is None else
           np.flatnonzero(symbols.isin(set(pd.unique(symbols)[: int(limit)]))))
    frame = tradeable_frame(panel, p_hold, fold_id, baseline_returns(market, baseline_dir), sub)
    frame["y_hold"] = y[sub][frame["pos"].to_numpy()]
    n_eval_pending = int((frame["date"].to_numpy() >= np.datetime64(EVAL_START)).sum())
    if smoke:  # dry run: never score the one-shot EVAL split
        frame = drop_eval(frame)
    tau = pick_tau(frame)
    kept = keep_mask(frame["p_hold"].to_numpy(), tau["tau"])
    gate = evaluate.fold_gate(pd.DataFrame({
        "fold": frame["fold"].to_numpy(dtype=int), "selected": kept,
        "p_buy": frame["p_hold"].to_numpy(dtype="float64"),
        "r_frozen": frame["r_frozen"].to_numpy(dtype="float64")}))
    pl = (placebo_z(frame, X[sub], y[sub], dates[sub], binary_train.learner_params(cfg), splitter,
                    tau["tau"], n_seeds=placebo_seeds, budget=budget) if placebo_seeds > 0 else
          {"observed_edge": float("nan"), "null_mean": float("nan"), "null_sd": float("nan"),
           "z": float("nan"), "n_seeds": 0})
    verdict = evaluate.verdict(gate["n_folds_pos"], gate["pooled_edge"], pl["z"])
    saved = None
    if verdict == "ADOPT":
        saved = ADOPT_DIR / f"wi037_hold_filter_{market}.pkl"
        saved.parent.mkdir(parents=True, exist_ok=True)
        with open(saved, "wb") as fh:
            pickle.dump({"market": market, "variant": VARIANT, "binary": BINARY,
                         "horizon": HORIZON, "tau": tau["tau"], "folds_won": gate["n_folds_pos"],
                         "pooled_edge": gate["pooled_edge"], "placebo_z": pl["z"]}, fh)
    return {"market": market, "feats": feats, "n_rows": int(len(panel)), "tau": tau,
            "n_oof_folds": int(np.unique(fold_id[np.isfinite(p_hold)]).size), "gate": gate,
            "placebo": pl, "verdict": verdict, "pickle": saved, "smoke": bool(smoke),
            "stats": frame_stats(frame, tau["tau"], kept, include_eval=not smoke),
            "n_eval_pending": n_eval_pending, "embargo_td": int(splitter.embargo_td),
            "core_sec": round(budget.spent(), 1), "runtime_sec": round(time.time() - t0, 1)}


def _fmt(x, spec: str = "{:.4f}") -> str:
    v = float(x)
    return "n/a" if not np.isfinite(v) else spec.format(v)


def build_report(results: list[dict], path: Path) -> Path:
    """`wi037_summary.md` — per market tau table, fold gate, placebo z, verdict."""
    out = ["# WI-037 — P(hold) veto filter on the frozen fib rules (D-022 phase 2)", "",
           f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
           f"- Filter: fold-consistent OOF P(hold) from the WI-036 cell `{VARIANT}`|xgboost|"
           f"`{BINARY}`|h{HORIZON} (`{MODEL_DIR.name}/`); an at-bottom frozen-rule entry is VETOED "
           f"when P(hold) >= tau; tau grid {TAU_GRID} tuned on CALIB entries (date < {CALIB_END}) "
           f"only, frozen before EVAL (date >= {EVAL_START})",
           f"- Baseline: frozen fib rules (WI-028 entry + WI-030 `{train.FROZEN_EXIT[0]}`, "
           f"{evaluate.COST_BPS:.0f} bps inside `r_frozen`); gate: ADOPT iff >= "
           f"{evaluate.FOLD_THRESHOLD}/5 fold wins AND pooled edge > 0 AND CB-05 placebo z >= "
           f"{evaluate.PLACEBO_Z_MIN} ({N_PLACEBO_SEEDS} permuted-label seeds, refit-only arms)", "",
           "| market | entries | kept | vetoed | folds won | pooled baseline | pooled filtered | "
           "pooled edge | placebo z | tau | verdict |",
           "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |"]
    if any(r.get("smoke") for r in results):
        out.insert(5, "- **Smoke run**: EVAL-window splits are excluded from scoring (the one-shot "
                      "EVAL is reserved for the full-universe job).")
    for r in results:
        g, pl, s, t = r["gate"], r["placebo"], r["stats"], r["tau"]
        out += [f"| {r['market']} | {g['n_events']:,} | {g['n_selected']:,} | "
                f"{g['n_events'] - g['n_selected']:,} | {g['n_folds_pos']}/5 | "
                f"{_fmt(g['pooled_baseline'])} | {_fmt(g['pooled_model'])} | {_fmt(g['pooled_edge'])} "
                f"| {_fmt(pl['z'], '{:+.2f}')} | {t['tau']:.2f} | **{r['verdict']}** |", "",
                f"## {r['market']} — VERDICT: **{r['verdict']}**", "",
                f"- {g['n_events']:,} at-bottom OOF entries with a priced frozen return "
                f"({r['n_oof_folds']}/5 fold pickles, embargo {r['embargo_td']} td, "
                f"{r['n_rows']:,} panel rows); tau={t['tau']:.2f} on CALIB ({t['n_calib']:,} "
                "entries): " + "; ".join(
                    f"tau {x['tau']:.2f} kept {x['n_kept']:,}/vetoed {x['n_vetoed']:,} edge "
                    f"{_fmt(x['edge'], '{:+.5f}')}" for x in t["table"]),
                f"- Veto precision {_fmt(s['precision'])} (true `b_hold` among the "
                f"{s['n_vetoed']:,} vetoed) vs prevalence {_fmt(s['prevalence'])}",
                (f"- EVAL window: n={s['n_eval']:,} kept={s['n_eval_kept']:,} baseline "
                 f"{_fmt(s['eval_baseline'])} edge {_fmt(s['eval_edge'])}" if s["eval_scored"] else
                 f"- EVAL window: NOT scored (smoke run; {r['n_eval_pending']:,} entries "
                 "withheld for the one-shot EVAL in the full-universe job)"),
                f"- Placebo (CB-05): observed {_fmt(pl['observed_edge'])} null {_fmt(pl['null_mean'])}"
                f" sd {_fmt(pl['null_sd'])} z {_fmt(pl['z'], '{:+.2f}')} ({pl['n_seeds']}/"
                f"{N_PLACEBO_SEEDS} seeds); runtime {r['runtime_sec']}s core {r['core_sec']}s", "",
                "| fold | entries | kept | vetoed | baseline mean | filtered mean | edge | IC | win |",
                "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |"]
        out += [f"| {f['fold']} | {f['n_events']:,} | {f['n_selected']:,} | "
                f"{f['n_events'] - f['n_selected']:,} | {_fmt(f['baseline_mean'])} | "
                f"{_fmt(f['model_mean'])} | {_fmt(f['edge'])} | {_fmt(f.get('ic'))} | "
                f"{'yes' if f['win'] else 'no'} |" for f in g["folds"]]
        if r.get("pickle"):
            out.append(f"- Filter config pickled -> `{r['pickle']}` (ADOPT only; nothing deployed)")
    out += ["", "## Notes / deviations", "",
            "- Class-prevalence caveat (WI-036): `b_hold` prevalence is a few tenths of a percent, so "
            "the isotonic-calibrated P(hold) rarely clears 0.5 and the tau grid is close to a no-op "
            "veto — the kept/vetoed counts and the veto precision are the informative numbers.",
            "- Baseline = the WI-033 lineage `r_frozen` (WI-028 entry + WI-030 exit, 25 bps inside) "
            "from the cached canonical panel or `binary_labels.build_binary_panel` "
            f"(k={train.GATE_K}, h={train.GATE_H}); inference only (pickles score their own OOF "
            "rows) and the CB-05 placebo arms are the only refits (permuted labels, tau frozen). "
            "Record-only: no shortlist, no deployment, no live trading.", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n")
    return path


def main(argv: list[str] | None = None) -> int:
    """CLI: `--market ALL --limit N --out DIR --placebo-seeds N --cache-dir DIR`."""
    p = argparse.ArgumentParser(description="WI-037 P(hold) veto filter gate (D-022 phase 2)")
    p.add_argument("--market", default="ALL", help="USD | CAD | ALL (default ALL)")
    p.add_argument("--limit", type=int, default=None, help="Max symbols per market (smoke).")
    p.add_argument("--out", default=None, help="Output dir (smoke runs use /tmp).")
    p.add_argument("--placebo-seeds", type=int, default=N_PLACEBO_SEEDS)
    p.add_argument("--cache-dir", default="/tmp/wi036", help="WI-036 panel cache dir.")
    p.add_argument("--baseline-dir", default="/tmp/wi035", help="Canonical panel cache dir.")
    args = p.parse_args(argv)
    smoke = os.environ.get("WI037_SMOKE", "").strip()
    args.limit = int(smoke) if args.limit is None and smoke.isdigit() else args.limit
    args.out = "/tmp/wi037_smoke" if args.out is None and smoke else args.out
    dry_run = args.limit is not None  # limited universe => never touch the one-shot EVAL
    from src.market_cli import cli_markets
    markets = cli_markets(args.market, prog="wi037.hold_filter_gate")
    if markets is None:
        return 2
    out_dir, t0 = (Path(args.out) if args.out else REPORTS_DIR), time.time()
    results = [run_market(m, train.load_settings(), cache_dir=Path(args.cache_dir),
                          baseline_dir=Path(args.baseline_dir), out_dir=out_dir, limit=args.limit,
                          placebo_seeds=args.placebo_seeds, smoke=dry_run,
                          budget=binary_grid.CoreBudget(CORE_HOUR_CAP)) for m in markets]
    report = build_report(results, out_dir / REPORT_NAME)
    for r in results:
        print(f"[wi037.filter] {r['market']}: verdict={r['verdict']} tau={r['tau']['tau']:.2f} "
              f"kept={r['gate']['n_selected']}/{r['gate']['n_events']} "
              f"folds={r['gate']['n_folds_pos']}/5 edge={_fmt(r['gate']['pooled_edge'])} "
              f"z={_fmt(r['placebo']['z'], '{:+.2f}')} core={r['core_sec']}s")
    print(f"[wi037.filter] report -> {report} | total {round(time.time() - t0, 1)}s")
    print("[wi037.filter] EXIT:0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())