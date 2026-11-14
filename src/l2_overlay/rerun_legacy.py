r"""WI-043 — rerun the three legacy L2 questions (WI-012/018/011) under the D-024 harness (L2).

One protocol (`harness.py`, WI-041), three ports onto the modern event base (WI-040 library OOF at
the frozen at-bottom entries, WI-027 regimes, multi-horizon `b_hold`); no bespoke refit, no AUC
selection, EVAL read once after the tau freeze (D-023 layers). Ports, declared before running:

* `wi012` **cross-market**: tau tuned on the USD CALIB edge, then judged on CAD events only. Its
  decision bar is h5 — the entry-gate horizon, and the only USD library horizon whose `b_hold` mass
  spans the pre-registered tau grid (h13/h34 have no operating point and are recorded as INERT).
* `wi018` **cost overlay**: the selected edge pays one extra 25 bps round trip (WI-018's `|IC|*1000
  - 25 bps > 0` rule); USD only, its own scope (D-018 Q2).
* `wi011` **condition-first**: the condition must be a *trigger*, so the WI-011 cadence envelope
  (100-400 firings/yr on CALIB) is an extra INERT gate, and the edge pays the same 25 bps.

The cost is a constant shift of the edge, so the CALIB argmax tau is unchanged (tests pin this) and
the placebo z stays gross. wi012 carries no stack source (a stack is market-local). BH-FDR: the
three questions are ONE family (`wi043_legacy_l2_rerun`), never pooled with WI-042's.

    uv run python -m src.l2_overlay.rerun_legacy
    L2_SMOKE=5 uv run python -m src.l2_overlay.rerun_legacy --out /tmp/l2_rerun_legacy_smoke
"""
from __future__ import annotations

import argparse, datetime as dt, os, time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from src.l2_overlay import harness as H
from src.l2_overlay import rerun_modern as M   # prep/plumbing reused verbatim, never edited

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR, DEFAULT_SMOKE_DIR = BASE_DIR / "reports" / "l2", "/tmp/l2_rerun_legacy_smoke"
REPORT_NAME, JSON_NAME = "rerun_legacy.md", "rerun_legacy.json"
FAMILY_ID = "wi043_legacy_l2_rerun"        # never pooled with WI-042's family
SCORE_FORM, FROZEN, HORIZONS = M.SCORE_FORM, M.FROZEN, M.HORIZONS
COST_BPS, TRADING_DAYS = 25.0, 252.0       # WI-018/WI-011 round trip; WI-011 firings-per-year basis
FIRINGS_MIN, FIRINGS_MAX = 100, 400        # WI-011 Step 6 trigger envelope
FDR_ALPHA, CAP_SEC = 0.05, 5400.0          # WI cap 1.5 core-h; the modern batch took ~30 s
CALIB_END, EVAL_START = H.CALIB_END, H.EVAL_START
QUESTIONS: tuple[dict, ...] = (
    dict(name="wi012", title="cross-market transfer gate (USD-tuned decision, judged on CAD)",
         baseline=f"wi012_{FROZEN}", ref_h=5, judge_markets=("CAD",), tune_market="USD",
         sources=("raw",), cost_bps=0.0, cadence=False),
    dict(name="wi018", title="first-touch h34 cost overlay vs the frozen baseline",
         baseline=f"wi018_{FROZEN}", ref_h=34, judge_markets=("USD",), tune_market=None,
         sources=("raw", "stack"), cost_bps=COST_BPS, cadence=False),
    dict(name="wi011", title="condition-first overlay on the modern event base",
         baseline=f"wi011_{FROZEN}", ref_h=13, judge_markets=("USD", "CAD"), tune_market=None,
         sources=("raw", "stack"), cost_bps=COST_BPS, cadence=True),
)
BASELINES = {q["name"]: q["baseline"] for q in QUESTIONS}
FAMILY = tuple(q["name"] for q in QUESTIONS)   # the BH-FDR family is exactly these three questions


def net_edge(edge, cost_bps: float = COST_BPS) -> float:
    """WI-018 cost rule: the overlay's own turnover pays one round trip on every event it takes."""
    return float(edge) - float(cost_bps) / 1e4 if np.isfinite(float(edge)) else float(edge)


def cadence_ok(dates, selected, mask, min_f: float = FIRINGS_MIN, max_f: float = FIRINGS_MAX):
    """WI-011 trigger envelope on the CALIB window: 100-400 firings/yr, else it is a state."""
    sel = np.asarray(mask, dtype=bool) & np.asarray(selected, dtype=bool)
    if not sel.any():
        return False, "INERT: no selected CALIB event to measure a cadence on"
    years = max(np.unique(np.asarray(dates)[sel]).size / TRADING_DAYS, 1.0 / TRADING_DAYS)
    rate = float(sel.sum()) / years
    if float(min_f) <= rate <= float(max_f):
        return True, ""
    return False, (f"INERT: cadence {rate:,.0f} firings/yr outside the WI-011 envelope "
                   f"{float(min_f):.0f}-{float(max_f):.0f} — a market state, not a trigger")


def _score(pr: dict, q: dict, source: str, calib: np.ndarray):
    """(keep-score `1 - p`, reason): WI-040 library OOF, never a bespoke refit (D-024 §2)."""
    if source == "raw":
        p = pr["probs"].get(int(q["ref_h"]))
        if p is None:
            return None, f"INERT: no WI-040 library cell for {M.VARIANT}/{M.BINARY}/h{q['ref_h']}"
        return 1.0 - np.asarray(p, dtype="float64"), ""
    p = M.stack_scores(pr, q["ref_h"], calib)
    if p is None:
        return None, f"INERT: stack unfit for {M.BINARY}/h{q['ref_h']} (labels or CALIB rows missing)"
    return 1.0 - np.asarray(p, dtype="float64"), ""


def _regimes(pr: dict, calib: np.ndarray) -> list[str]:
    """WI-027 regime labels present in the CALIB window (these cells join the same family)."""
    return sorted({str(v) for v in np.asarray(pr["regime"], dtype=object)[calib]
                   if isinstance(v, str) and v})


def _masks(pr: dict, cond: str, calib, ev, finite):
    """CALIB / EVAL masks for one conditioning level (`all` = every labelled row)."""
    hit = np.ones(len(finite), dtype=bool) if cond == "all" else (pr["regime"] == cond)
    return finite & calib & hit, finite & ev & hit


def _finish(q: dict, source: str, cond: str, market: str, res: H.OverlayResult,
            n_c: int, n_e: int, cost_bps: float) -> dict:
    """One verdict-bearing cell: the cost rule shifts the edges (and fold rows), z stays gross."""
    cal, eva = net_edge(res.calib_edge, cost_bps), net_edge(res.eval_edge, cost_bps)
    folds = ([dict(f, edge=net_edge(f["edge"], cost_bps)) for f in res.folds]
             if cost_bps else res.folds)
    verdict = H.classify(cal, eva, res.placebo_z) if cost_bps else res.verdict
    return M._cell(q, source, cond, market=market, verdict=verdict, tau=res.tau, calib_edge=cal,
                   eval_edge=eva, placebo_z=res.placebo_z, n_calib=n_c, n_eval=n_e,
                   n_selected=res.n_selected, folds=folds, reason=res.inert_reason,
                   cost_bps=float(cost_bps), gross_eval_edge=float(res.eval_edge))


def run_local(pr: dict, q: dict, *, market: str, smoke: bool = False,
              seeds: int = H.N_PLACEBO_SEEDS) -> list[dict]:
    """wi018/wi011: tau tuned on this market's CALIB edge only, then one-shot EVAL on the same market."""
    calib, ev = pr["dates"] < np.datetime64(CALIB_END), pr["dates"] >= np.datetime64(EVAL_START)
    events = pd.DataFrame({"ret": pr["ret"], "fold": pr["fold"]})
    out: list[dict] = []
    for source in q["sources"]:
        score, why = _score(pr, q, source, calib)
        if score is None:
            out.append(M._cell(q, source, "all", market=market, n_calib=int(calib.sum()), reason=why))
            continue
        finite = np.isfinite(score)
        for cond in ("all", *_regimes(pr, calib)):
            m_c, m_e = _masks(pr, cond, calib, ev, finite)
            n_c, n_e = int(m_c.sum()), int(m_e.sum())
            ok, reason = H.feasible(score[m_c], H.TAU_GRID)
            if not ok:
                out.append(M._cell(q, source, cond, market=market, n_calib=n_c, n_eval=n_e, reason=reason))
                continue
            if smoke:      # D-024 §2: a partial-universe run stops at the precheck, never EVAL
                out.append(M._cell(q, source, cond, market=market, verdict="PRECHECK-OK", n_calib=n_c,
                                   n_eval=n_e, reason="precheck ok; EVAL withheld (smoke)"))
                continue
            best, table = H.pick_tau_by_calib_edge(score, pr["ret"], m_c, H.TAU_GRID)
            tau = float(best["tau"])
            if q["cadence"]:   # WI-011: a state that fires on the whole universe is not a trigger
                ok_c, why_c = cadence_ok(pr["dates"], H.selected_mask(score, tau), m_c)
                if not ok_c:
                    out.append(M._cell(q, source, cond, market=market, tau=tau, n_calib=n_c,
                                       n_eval=n_e, n_selected=int(best["n_selected"]), reason=why_c,
                                       cost_bps=float(q["cost_bps"])))
                    continue
            res = H.run_overlay(f"{q['name']}|{source}|{cond}", q["baseline"], score, events,
                                H.TAU_GRID, m_c, m_e, n_seeds=seeds,
                                seed0=H.QUESTION_SEEDS.get(q["name"], H.PLACEBO_SEED0))
            row = _finish(q, source, cond, market, res, n_c, n_e, q["cost_bps"])
            row["tau_table"] = table
            out.append(row)
    return out


def run_cross(tune: dict, judge: dict, q: dict, *, smoke: bool = False,
              seeds: int = H.N_PLACEBO_SEEDS) -> list[dict]:
    """wi012: tau tuned on the USD CALIB edge, then the decision is judged on CAD edges only."""
    market, tmarket = q["judge_markets"][0], q["tune_market"]
    calib, ev = judge["dates"] < np.datetime64(CALIB_END), judge["dates"] >= np.datetime64(EVAL_START)
    calib_t = tune["dates"] < np.datetime64(CALIB_END)
    out: list[dict] = []
    for source in q["sources"]:
        score, why = _score(judge, q, source, calib)
        score_t, why_t = _score(tune, q, source, calib_t)
        if score is None or score_t is None:
            out.append(M._cell(q, source, "all", market=market, n_calib=int(calib.sum()),
                               tuned_on=tmarket, reason=why or why_t))
            continue
        finite, finite_t = np.isfinite(score), np.isfinite(score_t)
        ok_t, reason_t = H.feasible(score_t[finite_t & calib_t], H.TAU_GRID)
        if not ok_t:
            out.append(M._cell(q, source, "all", market=market, n_calib=int(calib.sum()),
                               tuned_on=tmarket, reason=f"{tmarket} tuning universe {reason_t}"))
            continue
        best, table = H.pick_tau_by_calib_edge(score_t, tune["ret"], finite_t & calib_t, H.TAU_GRID)
        tau = float(best["tau"])
        for cond in ("all", *_regimes(judge, calib)):
            m_c, m_e = _masks(judge, cond, calib, ev, finite)
            n_c, n_e = int(m_c.sum()), int(m_e.sum())
            ok, reason = H.feasible(score[m_c], H.TAU_GRID)
            if not ok:
                out.append(M._cell(q, source, cond, market=market, tau=tau, n_calib=n_c, n_eval=n_e,
                                   tuned_on=tmarket, reason=reason))
                continue
            if smoke:
                out.append(M._cell(q, source, cond, market=market, verdict="PRECHECK-OK", tau=tau,
                                   n_calib=n_c, n_eval=n_e, tuned_on=tmarket,
                                   reason="precheck ok; EVAL withheld (smoke)"))
                continue
            # judged on CAD only: CAD CALIB edge, one-shot CAD EVAL edge, CAD placebo, CAD folds
            res = H.OverlayResult(name=f"{q['name']}|{source}|{cond}", verdict="REJECT", tau=tau,
                                  calib_edge=H.score_eval(score, judge["ret"], m_c, tau),
                                  eval_edge=H.score_eval(score, judge["ret"], m_e, tau),
                                  folds=H.fold_edges(score, judge["ret"], judge["fold"], tau, m_c | m_e),
                                  placebo_z=H.placebo_z(score, judge["ret"], tau, n_seeds=seeds,
                                                        seed0=H.QUESTION_SEEDS.get(q["name"],
                                                                                  H.PLACEBO_SEED0)),
                                  n_calib=n_c, n_eval=n_e,
                                  n_selected=int(H.selected_mask(score[m_c], tau).sum()),
                                  tau_table=table, baseline=q["baseline"])
            res.verdict = H.classify(res.calib_edge, res.eval_edge, res.placebo_z)
            row = _finish(q, source, cond, market, res, n_c, n_e, 0.0)
            row["tuned_on"], row["tau_table"] = tmarket, table
            out.append(row)
    return out


def run_markets(markets=("USD", "CAD"), *, smoke: bool = False, limit=None, manifest=None,
                manifest_path=M.MANIFEST_PATH, cache_dir=M.PANEL_CACHE, baseline_dir=M.BASELINE_DIR,
                seeds: int = H.N_PLACEBO_SEEDS, alpha: float = FDR_ALPHA, loader=M.prepare_market,
                cap_sec: float = CAP_SEC) -> dict:
    """Prepare each market once, run every question on its judge market, BH-correct ONE family.

    `loader(market, *, manifest, cache_dir, baseline_dir, limit)` returns one prepared market and
    `manifest` (a DataFrame) overrides the WI-040 parquet — both seams exist for synthetic tests.
    """
    t0 = time.time()
    mf = pd.read_parquet(manifest_path) if manifest is None else manifest
    mf = mf[(mf["learner"] == M.LEARNER) & (mf["variant"] == M.VARIANT)
            & (mf["binary"] == M.BINARY)][M.MANIFEST_COLS]
    blocks: dict[str, dict] = {}
    for market in markets:      # USD is prepared first: wi012 tunes there and judges on CAD
        if time.time() - t0 > float(cap_sec):
            break
        blocks[market] = loader(market, manifest=mf, cache_dir=cache_dir,
                                baseline_dir=baseline_dir, limit=limit)
    cells: list[dict] = []
    for q in QUESTIONS:
        for market in q["judge_markets"]:
            missing = [m for m in ([market] + ([q["tune_market"]] if q["tune_market"] else []))
                       if m not in blocks]
            if missing:
                cells.append(M._cell(q, q["sources"][0], "all", market=market,
                                     reason=f"SKIPPED: {'/'.join(missing)} not prepared "
                                            "(core-hour cap / --market)"))
            elif q["tune_market"]:
                cells += run_cross(blocks[q["tune_market"]], blocks[market], q, smoke=smoke, seeds=seeds)
            else:
                cells += run_local(blocks[market], q, market=market, smoke=smoke, seeds=seeds)
    tested = [r for r in cells if np.isfinite(r["placebo_z"])]
    ps = [float(norm.sf(float(r["placebo_z"]))) for r in tested]
    qvals, _rejected = M.bh_fdr(ps, alpha)
    for r, p, qv in zip(tested, ps, qvals):
        r["p_value"], r["q_value"] = p, float(qv)
        r["verdict"] = (r["verdict"] if r["verdict"] in ("INERT", "REJECT")
                        else "ADOPT" if float(qv) < float(alpha) else "INCONCLUSIVE")
    return {"family": FAMILY_ID, "family_questions": len(FAMILY), "fdr_alpha": float(alpha),
            "smoke": bool(smoke),
            "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "manifest": str(manifest_path), "manifest_rows": int(len(mf)), "baselines": BASELINES,
            "horizons": list(HORIZONS), "questions": [dict(q) for q in QUESTIONS],
            "costs_bps": COST_BPS, "firings": [FIRINGS_MIN, FIRINGS_MAX],
            "markets": {m: {"notes": pr["notes"],
                            "cells": [c for c in cells if c.get("market") == m]}
                        for m, pr in blocks.items()},
            "cells": cells, "family_size": int(len(tested)), "runtime_sec": round(time.time() - t0, 1),
            "verdict_counts": {v: sum(1 for r in cells if r["verdict"] == v)
                               for v in sorted({r["verdict"] for r in cells})},
            "closure": {q["name"]: sorted({r["verdict"] for r in cells if r["question"] == q["name"]})
                        for q in QUESTIONS}}


def write_report(s: dict, path) -> Path:
    """`reports/l2/rerun_legacy.md` — per market, per question cells, then the single BH-FDR family."""
    lines = ["# WI-043 — legacy L2 rerun under the D-024 harness (Layer 2)", "",
             f"- {s['generated']} · BH-FDR family `{s['family']}` ({s['family_size']} tested cells, "
             f"alpha {s['fdr_alpha']}) — three questions, never pooled with WI-042's family; counts "
             f"{s['verdict_counts']} · runtime {s['runtime_sec']}s",
             "- Harness `src/l2_overlay/harness.py` (WI-041): INERT precheck on CALIB, tau from CALIB "
             "edge only, one-shot EVAL, 5-seed placebo. **PROVISIONAL** until the admin ratifies the "
             "verdicts (WORKFLOW); a REJECT closes that question under D-024 §2",
             f"- Ports: wi012 = tau tuned on the USD CALIB edge, then judged on CAD edges only; wi018 "
             f"= USD-only (D-018 Q2) and pays one extra {s['costs_bps']:.0f} bps round trip on every "
             f"event it takes; wi011 = that cost plus the WI-011 trigger envelope "
             f"({s['firings'][0]:.0f}-{s['firings'][1]:.0f} firings/yr on CALIB) as an INERT gate",
             f"- Inputs: `{Path(s['manifest']).name}` ({s['manifest_rows']} `{M.LEARNER}`/`{M.BINARY}`/"
             f"`{M.VARIANT}` fold pickles) -> fold-consistent OOF at the frozen at-bottom entries; "
             f"horizons {s['horizons']}; baseline = frozen fib-rule return (25 bps inside `r_frozen`)", ""]
    if s["smoke"]:
        lines += ["> **Smoke run** (L2_SMOKE): a partial universe stops at the feasibility precheck — "
                  "no cell scores the one-shot EVAL window.", ""]
    for market, blk in s["markets"].items():
        n = blk["notes"]
        lines += [f"## {market} — {n['n_events']:,} at-bottom entries, {n['n_features']} design "
                  f"columns, horizons {n['horizons']} (partial {n['partial_horizons'] or 'none'})", ""]
        for q in QUESTIONS:
            if market not in q["judge_markets"]:
                continue
            lines += [f"### {q['name']} — {q['title']}", "",
                      f"`{q['baseline']}`; score `1 - p(b_hold h{q['ref_h']})`; sources "
                      f"{'/'.join(q['sources'])}; judge market {market}"
                      + (f" (tau tuned on {q['tune_market']})" if q["tune_market"] else ""), "",
                      *M.CELL_HEAD]
            lines += [M._md_cell(r, s["smoke"]) for r in blk["cells"]] + [""]
    fam = sorted((r for r in s["cells"] if np.isfinite(r["p_value"])), key=lambda r: r["p_value"])
    lines += ["## BH-FDR family (every tested cell)", "", *M.FAM_HEAD]
    lines += ([f"| `{r['cell']}` | {r['verdict']} | {M._fmt(r['calib_edge'])} | "
               f"{M._fmt(r['eval_edge'])} | {M._fmt(r['placebo_z'], '{:+.2f}')} | "
               f"{M._fmt(r['p_value'], '{:.3g}')} | {M._fmt(r['q_value'], '{:.3g}')} |" for r in fam]
              or ["| — | _no cell reached a verdict (all INERT / smoke precheck only)_ | | | | | |"])
    lines += ["", "## Closure and deviations", "",
              "- INERT cells are honest nulls (no feasible operating point, or a cadence outside the "
              "WI-011 envelope) and carry no p-value, hence no family membership; the family is every "
              "cell that reached a verdict across the three questions.",
              "- Declared port choice: wi012's decision bar is h5 (the entry-gate horizon; the only USD "
              "library horizon whose mass spans the tau grid), fixed on CALIB feasibility before the "
              "CAD EVAL read; wi018 keeps its own h34 first-touch horizon and wi011 its 5-15d h13 bar, "
              "whose INERT outcomes are recorded, not skipped.",
              "- Deviations from WI-042's shape: per-question judge markets (wi012 CAD-only, wi018 "
              "USD-only per D-018 Q2, wi011 both markets), wi012 carries no stack source (a stack is "
              "market-local and cannot be transferred), and the wi018/wi011 edges are net of one extra "
              "25 bps round trip while the placebo z stays gross (a constant shift cannot move a "
              "permutation null; the tau argmax is invariant to it).",
              f"- Per-question verdict sets: {s['closure']} — nothing is adopted, promoted or closed "
              "from a computed verdict alone; no learner refit (the WI-040 pickles score their own OOF "
              "block), no shortlist, no deployment, no live trading.", ""]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return path


write_json = M.write_json   # the WI-042 payload writer, shape-identical


def main(argv=None) -> int:
    """CLI: full run -> `reports/l2`; `L2_SMOKE=5 --out /tmp/...` -> precheck-only report."""
    ap = argparse.ArgumentParser(description="WI-043 legacy-L2 rerun (D-024 §2 harness)")
    for flag, kw in (("--market", dict(default="ALL", help="USD | CAD | ALL")),
                     ("--limit", dict(type=int, default=None, help="Max symbols per market (smoke).")),
                     ("--out", dict(default=None, help="Report dir (smoke defaults to /tmp).")),
                     ("--manifest", dict(default=str(M.MANIFEST_PATH))),
                     ("--cache-dir", dict(default=M.PANEL_CACHE)),
                     ("--baseline-dir", dict(default=M.BASELINE_DIR)),
                     ("--seeds", dict(type=int, default=H.N_PLACEBO_SEEDS)),
                     ("--fdr-alpha", dict(type=float, default=FDR_ALPHA))):
        ap.add_argument(flag, **kw)
    a = ap.parse_args(argv)
    smoke = os.environ.get("L2_SMOKE", "").strip()
    a.limit = int(smoke) if a.limit is None and smoke.isdigit() else a.limit
    markets = tuple(m for m in ("USD", "CAD") if a.market in ("ALL", m))
    if not markets:
        print("[wi043.rerun] --market must be USD, CAD or ALL")
        return 2
    out = Path(a.out or (DEFAULT_SMOKE_DIR if a.limit is not None else REPORTS_DIR))
    s = run_markets(markets, smoke=a.limit is not None, limit=a.limit, manifest_path=Path(a.manifest),
                    cache_dir=a.cache_dir, baseline_dir=a.baseline_dir, seeds=a.seeds, alpha=a.fdr_alpha)
    rep, js = write_report(s, out / REPORT_NAME), write_json(s, out / JSON_NAME)
    print(f"[wi043.rerun] family={s['family']} cells={len(s['cells'])} tested={s['family_size']} "
          f"verdicts={s['verdict_counts']} runtime={s['runtime_sec']}s")
    print(f"[wi043.rerun] {'smoke (EVAL withheld)' if s['smoke'] else 'run'} -> {rep} | EXIT:0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
