"""WI-042 — rerun the four modern L2 overlays (WI-037/033/030/028) under the D-024 harness (L2).

One protocol (`src/l2_overlay/harness.py`, WI-041) applied to four questions; probabilities come
from the WI-040 library manifest (fold pickles, fold-consistent OOF at the frozen at-bottom
entries), never a bespoke refit. Layer 2 only: a decision/edge, never an AUC claim (D-023).
Cell = question x score source x regime conditioning; every tested cell shares ONE BH-FDR family.

| question | frozen baseline | score source (ref h) | score form |
|---|---|---|---|
| WI-037 `wi037` | frozen fib entry + `t15_s10_d39_close` exit | `b_hold` h13 (its original cell) | keep = 1 - p |
| WI-033 `wi033` | same frozen rule | `b_hold` h21 (its gate geometry) | keep = 1 - p |
| WI-030 `wi030` | frozen exit cell `t15_s10_d39_close` | `b_hold` h34 (nearest the 39-day stop) | keep = 1 - p |
| WI-028 `wi028` | frozen immediate k=0 entry | `b_hold` h5 (the k<=5 entry offsets) | keep = 1 - p |

The 3-class HOLD class maps onto `b_hold`; the exit / entry-window questions are ported as selection
claims against the frozen pricing (the harness scores the events the frozen rule prices) and `keep =
1 - p` because the harness takes an event iff score >= tau while `b_hold` is the rare class. WI-027
regime labels condition cells; a CALIB-fit elastic-net logistic stack over the multi-horizon
`b_hold` vector (frozen before EVAL, target = the question's own label) is one more score source in
the same family. Learners are never re-trained.

    uv run python -m src.l2_overlay.rerun_modern
    L2_SMOKE=5 uv run python -m src.l2_overlay.rerun_modern --out /tmp/l2_rerun_modern_smoke
"""
from __future__ import annotations

import argparse, datetime as dt, json, os, pickle, time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.l2_overlay import harness as H
from src.swing_bsh import binary_features_ext as ext, binary_grid, train
from src.swing_bsh.hold_filter_gate import baseline_returns
from src.swing_bsh.hold_regime_audit import design_matrix, load_regime_labels
from src.swing_bsh.library_audit import MANIFEST_DIR, MANIFEST_NAME
from src.xgb_trainer import PurgedWalkForwardSplit

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR, DEFAULT_SMOKE_DIR = BASE_DIR / "reports" / "l2", "/tmp/l2_rerun_modern_smoke"
REPORT_NAME, JSON_NAME = "rerun_modern.md", "rerun_modern.json"
PANEL_CACHE, BASELINE_DIR, MANIFEST_PATH = "/tmp/wi036", "/tmp/wi035", MANIFEST_DIR / MANIFEST_NAME
FAMILY_ID = "wi042_modern_l2_rerun"           # never pooled with WI-043's family
SCORE_FORM = "keep=1-p"                       # every question is ported in keep-score form
VARIANT, LEARNER, BINARY = ext.variant_name("exact", "full", 0.8), "xgboost", "b_hold"
HORIZONS: tuple[int, ...] = (5, 8, 13, 21, 34, 55, 89)
FDR_ALPHA, CAP_SEC, COST_BPS = 0.05, 3600.0, 25.0
CALIB_END, EVAL_START = H.CALIB_END, H.EVAL_START
MANIFEST_COLS = ["pickle_path", "market", "learner", "variant", "binary", "h", "fold"]
FROZEN = "frozen_fib_w28entry_w30exit_t15_s10_d39_close"
QUESTIONS: tuple[dict, ...] = (
    dict(name="wi037", title="b_hold veto on frozen fib entries", baseline=f"wi037_{FROZEN}", ref_h=13),
    dict(name="wi033", title="3-class swing-conditioned overlay (HOLD <-> b_hold)", baseline=f"wi033_{FROZEN}", ref_h=21),
    dict(name="wi030", title="learned exit chooser vs the frozen exit cell", baseline=f"wi030_{FROZEN}", ref_h=34),
    dict(name="wi028", title="entry-window chooser (k=0 vs k=3/k=5)", baseline=f"wi028_{FROZEN}", ref_h=5),
)
BASELINES = {q["name"]: q["baseline"] for q in QUESTIONS}

def bh_fdr(pvals, alpha: float = FDR_ALPHA):
    """Benjamini-Hochberg step-up q-values (NaN-free input) + the family rejection mask."""
    p = np.asarray(pvals, dtype="float64")
    if p.size == 0:
        return p, np.zeros(0, dtype=bool)
    order, n = np.argsort(p), p.size
    q = np.minimum.accumulate((p[order] * n / np.arange(1, n + 1))[::-1])[::-1].clip(0.0, 1.0)
    out = np.empty(n)
    out[order] = q
    return out, out < float(alpha)

def market_oof(panel, X, manifest, market) -> tuple[dict, np.ndarray]:
    """Fold-consistent OOF P(b_hold) per manifest horizon + the market's validation-block ids."""
    fid = np.full(len(panel), -1, dtype="int16")
    split = PurgedWalkForwardSplit(n_splits=binary_grid.N_SPLITS,
                                   embargo_td=train.embargo_for([max(HORIZONS)]))
    for k, (_tr, va) in enumerate(split.split(panel["date"].to_numpy())):
        fid[va] = k
    probs: dict[int, np.ndarray] = {}
    for h in HORIZONS:
        rows = manifest[(manifest["market"] == market) & (manifest["h"] == float(h))]
        p = np.full(len(panel), np.nan, dtype="float64")
        for _, r in rows.iterrows():
            sel = fid == int(r["fold"])
            if sel.any():
                with open(BASE_DIR / str(r["pickle_path"]), "rb") as fh:
                    blob = pickle.load(fh)
                q = np.asarray((blob["model"] if isinstance(blob, dict) else blob)
                               .predict_proba(X[sel]), dtype="float64")
                p[sel] = q[:, 1] if q.ndim == 2 else q.ravel()
        if np.isfinite(p).any():
            probs[int(h)] = p
    return probs, fid

def prepare_market(market, *, manifest, cache_dir=PANEL_CACHE, baseline_dir=BASELINE_DIR,
                   limit=None, **_) -> dict:
    """Frozen at-bottom entries + fold-consistent multi-horizon `b_hold` OOF (cache, else build)."""
    keys = [(VARIANT, int(h)) for h in HORIZONS]
    panel, labels = ext.load_variant_panel(cache_dir, market, keys)
    if panel is None or not labels:
        panel, labels = ext.build_variant_panel(market, variants=[(VARIANT, "exact", "full", 0.8)],
                                                horizons=HORIZONS, max_symbols=limit)
    if panel is None or panel.empty:
        raise RuntimeError(f"no swing events for market={market}")
    X, feats = design_matrix(panel)
    sym, dates = panel["symbol"].astype(str), pd.to_datetime(panel["date"])
    frame = pd.DataFrame({"pos": np.arange(len(panel)), "symbol": sym, "date": dates,
                          "state": panel["state"].astype(str)})
    frame = frame[frame["state"] == "at_bottom"]
    if limit is not None:      # smoke: the first N symbols only (symbol-sequential)
        frame = frame[frame["symbol"].isin(list(pd.unique(sym))[: int(limit)])]
    frame = frame.merge(baseline_returns(market, baseline_dir), on=["symbol", "date"], how="inner")
    frame = frame.sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)
    probs, fid = market_oof(panel, X, manifest, market)
    keep = fid[frame["pos"].to_numpy()] >= 0        # OOF rows only (fold pickles score their block)
    pos = frame["pos"].to_numpy()[keep]
    reg = load_regime_labels()
    regime = pd.DataFrame({"date": dates.to_numpy()[pos]}).merge(
        reg[reg["market"] == market][["date", "regime"]], on="date", how="left")["regime"]
    out = {"market": market, "dates": dates.to_numpy()[pos], "fold": fid[pos].astype(int),
           "ret": frame["r_frozen"].to_numpy("float64")[keep],
           "regime": regime.astype(object).to_numpy(),
           "probs": {int(h): p[pos].astype("float32") for h, p in probs.items()},
           "labels": {int(h): np.asarray(labels[(VARIANT, int(h))][BINARY], dtype="int8")[pos]
                      for h in HORIZONS if (VARIANT, int(h)) in labels}}
    out["notes"] = {"n_events": int(pos.size), "n_features": int(len(feats)),
                    "horizons": sorted(out["probs"]),
                    "partial_horizons": sorted(h for h, p in out["probs"].items()
                                               if not np.isfinite(p).all()),
                    "n_no_regime": int(pd.isna(out["regime"]).sum())}
    return out

def stack_scores(pr: dict, h: int, calib: np.ndarray, seed: int = 7):
    """CALIB-fit saga elastic-net logistic over the multi-horizon vector, frozen before EVAL.

    Imputation/scaling are fitted on CALIB rows only (causal); `saga` on <=7 columns does not fan
    out, so no `n_jobs` is passed (repo law: never `n_jobs=-1`).
    """
    y = pr["labels"].get(int(h))
    if y is None:
        return None
    F = np.column_stack([pr["probs"][k] for k in pr["notes"]["horizons"]]).astype("float64")
    F = F[:, np.isfinite(F[np.asarray(calib, dtype=bool)]).any(axis=0)]
    if F.shape[1] == 0 or int(calib.sum()) < H.MIN_CALIB_EVENTS or np.unique(y[calib]).size < 2:
        return None
    pipe = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()),
                     ("clf", LogisticRegression(solver="saga", l1_ratio=0.5, C=1.0, max_iter=1000,
                                                random_state=seed))])
    pipe.fit(F[calib], y[calib])
    return pipe.predict_proba(F)[:, 1].astype("float32")

def _cell(q: dict, source: str, cond: str, **kw) -> dict:
    """Blank cell record (INERT until the harness returns something else)."""
    row = {"question": q["name"], "title": q["title"], "baseline": q["baseline"],
           "ref_h": int(q["ref_h"]), "source": source, "conditioning": cond,
           "cell": f"{q['name']}|{source}|{cond}", "verdict": "INERT", "tau": float("nan"),
           "calib_edge": float("nan"), "eval_edge": float("nan"), "placebo_z": float("nan"),
           "p_value": float("nan"), "q_value": float("nan"), "n_calib": 0, "n_eval": 0,
           "n_selected": 0, "folds": [], "reason": ""}
    row.update(kw)
    return row

def run_question(pr: dict, q: dict, *, smoke: bool = False,
                 seeds: int = H.N_PLACEBO_SEEDS) -> list[dict]:
    """Every (score source x regime conditioning) cell of one question, in keep-score form."""
    calib, ev = pr["dates"] < np.datetime64(CALIB_END), pr["dates"] >= np.datetime64(EVAL_START)
    events = pd.DataFrame({"ret": pr["ret"], "fold": pr["fold"]})
    regs = sorted({str(v) for v in np.asarray(pr["regime"], dtype=object)[calib]
                   if isinstance(v, str) and v})
    out: list[dict] = []
    for source in ("raw", "stack"):
        p = pr["probs"].get(int(q["ref_h"])) if source == "raw" else stack_scores(pr, q["ref_h"], calib)
        if p is None:
            why = (f"no WI-040 library cell for {VARIANT}/{BINARY}/h{q['ref_h']}" if source == "raw"
                   else f"stack unfit for {BINARY}/h{q['ref_h']} (labels or CALIB rows missing)")
            out.append(_cell(q, source, "all", n_calib=int(calib.sum()), reason=f"INERT: {why}"))
            continue
        score, finite = 1.0 - np.asarray(p, dtype="float64"), np.isfinite(p)
        for cond in ("all", *regs):
            hit = np.full(len(score), True) if cond == "all" else (pr["regime"] == cond)
            m_c, m_e, n_c, n_e = finite & calib & hit, finite & ev & hit, 0, 0
            n_c, n_e = int(m_c.sum()), int(m_e.sum())
            ok, reason = H.feasible(score[m_c], H.TAU_GRID)
            if not ok:
                out.append(_cell(q, source, cond, n_calib=n_c, n_eval=n_e, reason=reason))
                continue
            if smoke:    # D-024 §2: a partial-universe run stops at the precheck, never EVAL
                out.append(_cell(q, source, cond, verdict="PRECHECK-OK", n_calib=n_c, n_eval=n_e,
                                 reason="precheck ok; EVAL withheld (smoke)"))
                continue
            res = H.run_overlay(f"{q['name']}|{source}|{cond}", q["baseline"], score, events,
                                H.TAU_GRID, m_c, m_e, n_seeds=seeds,
                                seed0=H.QUESTION_SEEDS.get(q["name"], H.PLACEBO_SEED0))
            out.append(_cell(q, source, cond, n_calib=n_c, n_eval=n_e, verdict=res.verdict,
                             tau=res.tau, calib_edge=res.calib_edge, eval_edge=res.eval_edge,
                             placebo_z=res.placebo_z, n_selected=res.n_selected, folds=res.folds,
                             reason=res.inert_reason))
    return out

def run_markets(markets=("USD", "CAD"), *, smoke=False, limit=None, manifest=None,
                manifest_path=MANIFEST_PATH, cache_dir=PANEL_CACHE, baseline_dir=BASELINE_DIR,
                seeds=H.N_PLACEBO_SEEDS, alpha=FDR_ALPHA, loader=prepare_market, cap_sec=CAP_SEC) -> dict:
    """Run the four questions per market, BH-correct ONE family, return the report payload.

    `loader(market, *, manifest, cache_dir, baseline_dir, limit)` returns one prepared market and
    `manifest` (a DataFrame) overrides the WI-040 parquet — both seams exist for synthetic tests.
    """
    t0 = time.time()
    mf = pd.read_parquet(manifest_path) if manifest is None else manifest
    mf = mf[(mf["learner"] == LEARNER) & (mf["variant"] == VARIANT)
            & (mf["binary"] == BINARY)][MANIFEST_COLS]
    blocks, cells = {}, []
    for market in markets:
        pr = loader(market, manifest=mf, cache_dir=cache_dir, baseline_dir=baseline_dir, limit=limit)
        rows: list[dict] = []
        for q in QUESTIONS:
            rows += ([_cell(q, "raw", "(all cells)", reason="SKIPPED: core-hour cap reached")]
                     if time.time() - t0 > float(cap_sec) else run_question(pr, q, smoke=smoke, seeds=seeds))
        blocks[market], cells = {"notes": pr["notes"], "cells": rows}, cells + rows
    tested = [r for r in cells if np.isfinite(r["placebo_z"])]
    ps = [float(norm.sf(float(r["placebo_z"]))) for r in tested]
    qvals, _rejected = bh_fdr(ps, alpha)
    for r, p, q in zip(tested, ps, qvals):
        r["p_value"], r["q_value"] = p, float(q)
        r["verdict"] = (r["verdict"] if r["verdict"] in ("INERT", "REJECT")
                        else "ADOPT" if float(q) < float(alpha) else "INCONCLUSIVE")
    return {"family": FAMILY_ID, "fdr_alpha": float(alpha), "smoke": bool(smoke),
            "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "manifest": str(manifest_path), "manifest_rows": int(len(mf)), "baselines": BASELINES,
            "horizons": list(HORIZONS), "questions": [dict(q) for q in QUESTIONS],
            "markets": blocks, "cells": cells, "costs_bps": COST_BPS,
            "family_size": int(len(tested)), "runtime_sec": round(time.time() - t0, 1),
            "verdict_counts": {v: sum(1 for r in cells if r["verdict"] == v)
                               for v in sorted({r["verdict"] for r in cells})},
            "closure": {q["name"]: sorted({r["verdict"] for r in cells if r["question"] == q["name"]})
                        for q in QUESTIONS}}

def _fmt(x, spec: str = "{:.4f}") -> str:
    return "n/a" if not np.isfinite(float(x)) else spec.format(float(x))

CELL_HEAD = ("| cell | verdict | tau | CALIB edge | EVAL edge | folds | placebo z | p | q | n_calib "
             "| n_eval | note |",
             "| :--- | :---: | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | ---: | :--- |")
FAM_HEAD = ("| cell | verdict | CALIB edge | EVAL edge | placebo z | p | q |",
            "| :--- | :---: | ---: | ---: | ---: | ---: | ---: |")

def _md_cell(r: dict, smoke: bool) -> str:
    """One cell row (folds render as `fold:edge` pairs; INERT reasons are quoted)."""
    folds = ", ".join(f"{f['fold']}:{_fmt(f['edge'], '{:+.4f}')}" for f in r["folds"]) or "—"
    note = r["reason"] or ("EVAL withheld (smoke)" if smoke else "—")
    return (f"| `{r['cell']}` | **{r['verdict']}** | {_fmt(r['tau'], '{:.2f}')} | "
            f"{_fmt(r['calib_edge'], '{:+.5f}')} | {_fmt(r['eval_edge'], '{:+.5f}')} | {folds} | "
            f"{_fmt(r['placebo_z'], '{:+.2f}')} | {_fmt(r['p_value'], '{:.3g}')} | "
            f"{_fmt(r['q_value'], '{:.3g}')} | {r['n_calib']:,} | {r['n_eval']:,} | {note} |")

def write_report(s: dict, path) -> Path:
    """`reports/l2/rerun_modern.md` — per question cells, then the single BH-FDR family."""
    lines = ["# WI-042 — modern L2 rerun under the D-024 harness (Layer 2)", "",
             f"- {s['generated']} · BH-FDR family `{s['family']}` ({s['family_size']} tested cells, "
             f"alpha {s['fdr_alpha']}) — never pooled with WI-043's; counts {s['verdict_counts']} · "
             f"runtime {s['runtime_sec']}s",
             "- Harness `src/l2_overlay/harness.py` (WI-041): INERT precheck on CALIB, tau from CALIB "
             "edge only, one-shot EVAL, 5-seed placebo. **PROVISIONAL** until the admin ratifies the "
             "verdicts (WORKFLOW); a REJECT closes that question under D-024 §2",
             f"- Inputs: `{Path(s['manifest']).name}` ({s['manifest_rows']} `{LEARNER}`/`{BINARY}`/"
             f"`{VARIANT}` fold pickles) -> fold-consistent OOF at the frozen at-bottom entries; "
             f"horizons {s['horizons']}; baseline = frozen fib-rule return ({s['costs_bps']:.0f} bps "
             "inside `r_frozen`); stack = CALIB elastic-net logistic over the horizon vector", ""]
    if s["smoke"]:
        lines += ["> **Smoke run** (L2_SMOKE): a partial universe stops at the feasibility precheck — "
                  "no cell scores the one-shot EVAL window.", ""]
    for market, blk in s["markets"].items():
        n = blk["notes"]
        lines += [f"## {market} — {n['n_events']:,} at-bottom entries, {n['n_features']} design "
                  f"columns, horizons {n['horizons']} (partial {n['partial_horizons'] or 'none'}), "
                  f"{n['n_no_regime']:,} rows without a WI-027 regime label", ""]
        for q in QUESTIONS:
            lines += [f"### {q['name']} — {q['title']}", "",
                      f"`{q['baseline']}`; score `1 - p(b_hold h{q['ref_h']})`; sources raw + stack",
                      "", *CELL_HEAD]
            lines += [_md_cell(r, s["smoke"]) for r in blk["cells"] if r["question"] == q["name"]] + [""]
    fam = sorted((r for r in s["cells"] if np.isfinite(r["p_value"])), key=lambda r: r["p_value"])
    lines += ["## BH-FDR family (every tested cell)", "", *FAM_HEAD]
    lines += ([f"| `{r['cell']}` | {r['verdict']} | {_fmt(r['calib_edge'], '{:+.5f}')} | "
               f"{_fmt(r['eval_edge'], '{:+.5f}')} | {_fmt(r['placebo_z'], '{:+.2f}')} | "
               f"{_fmt(r['p_value'], '{:.3g}')} | {_fmt(r['q_value'], '{:.3g}')} |" for r in fam]
              or ["| — | _no cell reached a verdict (all INERT / smoke precheck only)_ | | | | | |"])
    lines += ["", "## Closure and deviations", "",
              "- INERT cells are honest nulls (no feasible operating point in the pre-registered tau "
              "grid) and carry no p-value, hence no family membership; the family is every cell that "
              "reached a verdict across the four questions, both sources and every conditioning level.",
              f"- Per-question verdict sets: {s['closure']} — nothing is adopted, promoted or closed "
              "from a computed verdict alone; no learner refit (the WI-040 pickles score their own OOF "
              "block), no shortlist, no deployment, no live trading.", ""]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return path

def write_json(s: dict, path) -> Path:
    """`reports/l2/rerun_modern.json` — the same payload, machine-readable."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(s, indent=1, sort_keys=True, default=str) + "\n")
    return path

def main(argv=None) -> int:
    """CLI: full run -> `reports/l2`; `L2_SMOKE=5 --out /tmp/...` -> precheck-only report."""
    ap = argparse.ArgumentParser(description="WI-042 modern-L2 rerun (D-024 §2 harness)")
    for flag, kw in (("--market", dict(default="ALL", help="USD | CAD | ALL")),
                     ("--limit", dict(type=int, default=None, help="Max symbols per market (smoke).")),
                     ("--out", dict(default=None, help="Report dir (smoke defaults to /tmp).")),
                     ("--manifest", dict(default=str(MANIFEST_PATH))),
                     ("--cache-dir", dict(default=PANEL_CACHE)),
                     ("--baseline-dir", dict(default=BASELINE_DIR)),
                     ("--seeds", dict(type=int, default=H.N_PLACEBO_SEEDS)),
                     ("--fdr-alpha", dict(type=float, default=FDR_ALPHA))):
        ap.add_argument(flag, **kw)
    a = ap.parse_args(argv)
    smoke = os.environ.get("L2_SMOKE", "").strip()
    a.limit = int(smoke) if a.limit is None and smoke.isdigit() else a.limit
    markets = [m for m in ("USD", "CAD") if a.market in ("ALL", m)]
    if not markets:
        print("[wi042.rerun] --market must be USD, CAD or ALL")
        return 2
    out = Path(a.out or (DEFAULT_SMOKE_DIR if a.limit is not None else REPORTS_DIR))
    s = run_markets(markets, smoke=a.limit is not None, limit=a.limit, manifest_path=Path(a.manifest),
                    cache_dir=a.cache_dir, baseline_dir=a.baseline_dir, seeds=a.seeds,
                    alpha=a.fdr_alpha)
    rep, js = write_report(s, out / REPORT_NAME), write_json(s, out / JSON_NAME)
    print(f"[wi042.rerun] family={s['family']} cells={len(s['cells'])} tested={s['family_size']} "
          f"verdicts={s['verdict_counts']} runtime={s['runtime_sec']}s")
    print(f"[wi042.rerun] {'smoke (EVAL withheld)' if s['smoke'] else 'run'} -> {rep} | EXIT:0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
