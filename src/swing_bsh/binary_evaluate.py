"""WI-035 step 3 — two-threshold entry gate over the three binary models (D-022 §3).

The **learner and the (τ_p, τ_s) pair are frozen on the calibration blocks** by
:mod:`src.swing_bsh.binary_train`; this module only *reports*: canonical at-bottom
`k=1.5/h=21` rows are taken iff `P̂_profit ≥ τ_p AND P̂_stop ≤ τ_s` (an intersection
filter — the three probabilities are never renormalised), the selected events are
compared fold by fold with the frozen fib-rule baseline (`r_frozen`, WI-028 entry +
WI-030 exit), and the ADOPT_LOOSE_4OF5 gate is computed **for the record**: this run
is confirmatory and expected to document no edge (admin direction 2026-11-09).

Model pickles are written by the trainer for **every** fitted model, independent of
the verdict (admin override 2026-11-09: kept for future testing, nothing deployed, the
shortlist is unchanged). Placebo: CB-05 label permutation, 3 seeds.

CLI::

    WI035_SMOKE=5 python -m src.swing_bsh.binary_evaluate --out /tmp/wi035_smoke
    python -m src.swing_bsh.binary_evaluate --market ALL
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.swing_bsh import binary_train, evaluate, train
from src.swing_bsh.binary_labels import RHO_THRESHOLD

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "reports"
N_PLACEBO_SEEDS = 3
"""Admin waived the full check battery: 3-of-5 CB-05 seeds under a 1.0 core-hour cap."""

PLACEBO_BUDGET_SEC = 420.0
"""Wall-clock safety valve per market: a seed starts only if ≥1.2x its cost still fits."""

SMALL_SELECTION = 200
"""Below this many selected events the pooled edge is flagged as fat-tail dominated (record-only)."""


class WallBudget:
    """Minimal budget object consumed by `binary_train.placebo_null` (`left()` in seconds)."""

    def __init__(self, seconds: float):
        self.deadline = time.time() + float(seconds)

    def left(self) -> float:
        return self.deadline - time.time()


NAN_PLACEBO = {"observed_edge": float("nan"), "null_mean": float("nan"),
               "null_sd": float("nan"), "null_edges": [], "z": float("nan"), "n_seeds": 0}

__all__ = ["N_PLACEBO_SEEDS", "PLACEBO_BUDGET_SEC", "WallBudget", "gate_frame", "run_market",
           "write_summary"]


def gate_frame(res: dict, learner: str, tau_p: float, tau_s: float) -> pd.DataFrame:
    """Canonical at-bottom rows carrying the frozen two-threshold (intersection) selection."""
    prof = np.asarray(res["cv"][(learner, "b_profit")]["oof"], dtype="float64")
    stop = np.asarray(res["cv"][(learner, "b_stop")]["oof"], dtype="float64")
    mask = (res["canon"] & (res["fold_id"] >= 0)
            & np.isfinite(prof) & np.isfinite(stop) & np.isfinite(res["ret"]))
    sel = binary_train.frozen_selection({"oof": prof}, {"oof": stop}, tau_p, tau_s, mask) & mask
    return pd.DataFrame({
        "pos": np.flatnonzero(mask), "symbol": res["symbol"][mask],
        "date": res["dates"][mask], "fold": res["fold_id"][mask].astype(int),
        "p_profit": prof[mask], "p_stop": stop[mask],
        "p_buy": prof[mask],  # `evaluate.fold_gate` computes its rank-IC on `p_buy`
        "r_frozen": res["ret"][mask], "selected": sel[mask],
    })


def run_market(market: str, cfg: dict, *, out_dir: Path = REPORTS_DIR, limit: int | None = None,
               allow_fixture: bool = False, placebo_seeds: int = N_PLACEBO_SEEDS,
               learners=None, model_dir: Path | None = binary_train.MODEL_DIR,
               cache_dir: Path | None = None) -> dict:
    """Train the binary grid for one market, freeze the rule on calib, then gate it."""
    kw = {"learners": learners} if learners is not None else {}
    res = binary_train.train_market(
        market, cfg, allow_fixture=allow_fixture, max_symbols=limit, checkpoint_dir=out_dir,
        model_dir=model_dir, cache_dir=cache_dir, **kw)
    best = res["selection"]["best"]
    if best is None:
        gate = {"folds": [], "n_folds_pos": 0, "pooled_edge": float("nan"),
                "pooled_baseline": float("nan"), "pooled_model": float("nan"),
                "n_events": 0, "n_selected": 0, "pooled_ic": float("nan")}
        return {**res, "gate": gate, "placebo": dict(NAN_PLACEBO), "verdict": "REJECT",
                "rule": None}
    g = gate_frame(res, best["learner"], best["tau_p"], best["tau_s"])
    gate = evaluate.fold_gate(g)
    res["observed_edge"] = gate["pooled_edge"]
    pl = (binary_train.placebo_null(res, learner=best["learner"], n_seeds=placebo_seeds,
                                    budget=WallBudget(PLACEBO_BUDGET_SEC))
          if placebo_seeds > 0 else dict(NAN_PLACEBO))
    verdict = evaluate.verdict(gate["n_folds_pos"], gate["pooled_edge"], pl["z"])
    return {**res, "gate": gate, "placebo": pl, "verdict": verdict, "rule": best}


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def _fmt(x, spec="{:.4f}") -> str:
    v = float(x)
    return "n/a" if not np.isfinite(v) else spec.format(v)


def _shap_line(shap: dict) -> str:
    top = list(shap.items())[:6]
    return ", ".join(f"`{k}` {v:.3f}" for k, v in top) if top else "n/a"


def _rule_str(rule: dict | None) -> str:
    """Human-readable frozen rule, or the explicit no-candidate note."""
    if not rule:
        return "no candidate cleared the calibration edge floor (NaN rule)"
    return (f"`{rule['learner']}` τ_p={rule['tau_p']:.2f} / τ_s={rule['tau_s']:.2f} — "
            f"calib-selected {rule['n_selected']} rows, calib edge {rule['edge']:+.4f}")


def write_summary(results: list[dict], path: Path) -> Path:
    """Write `wi035_summary.md` — fold table, pooled edge, placebo z, TreeSHAP per binary."""
    lines = [
        "# WI-035 — three binary first-touch models + two-threshold entry gate (D-022 §3)",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Learners: {', '.join(binary_train.LEARNERS)} on `b_profit/b_stop/b_hold`; "
        f"`n_jobs=2`, float32, symbol-sequential; per-fold isotonic calibration, sigmoid "
        f"fallback < {binary_train.CB04_MIN_POSITIVES} positives (CB-04)",
        f"- CV: 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, horizon))`; entry rule "
        f"`P̂_profit ≥ τ_p AND P̂_stop ≤ τ_s` (no renormalisation), grid τ_p∈{binary_train.TAU_P_GRID}, "
        f"τ_s∈{binary_train.TAU_S_GRID}, selected on CALIB folds only and frozen before EVAL",
        f"- Gate geometry: at-bottom k={train.GATE_K}, h={train.GATE_H}; baseline frozen fib rules "
        f"(WI-028 + WI-030 `{train.FROZEN_EXIT[0]}`, {evaluate.COST_BPS:.0f} bps); "
        f"placebo CB-05 label permutation ({N_PLACEBO_SEEDS} seeds)",
        f"- Gate (for the record, confirmatory run): ADOPT iff ≥ {evaluate.FOLD_THRESHOLD}/5 folds "
        f"AND pooled edge > 0 AND placebo z ≥ {evaluate.PLACEBO_Z_MIN}",
        "- Model pickles (admin override 2026-11-09): every fitted model saved under "
        "`data/models/wi035/<MKT>_<learner>_<binary>_f<fold>.pkl` regardless of verdict "
        "(kept for future testing; nothing deployed, shortlist unchanged)",
        "",
        "| market | events | selected | folds won | pooled baseline | pooled model | pooled edge "
        "| placebo z | rule | verdict |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :---: |",
    ]
    for r in results:
        gate, pl, rule = r["gate"], r["placebo"], r.get("rule")
        rule_s = ("n/a" if not rule else
                  f"{rule['learner']} τ_p={rule['tau_p']:.2f}/τ_s={rule['tau_s']:.2f}")
        lines.append(
            f"| {r['market']} | {gate['n_events']:,} | {gate['n_selected']:,} | "
            f"{gate['n_folds_pos']}/5 | {_fmt(gate['pooled_baseline'])} | {_fmt(gate['pooled_model'])} | "
            f"{_fmt(gate['pooled_edge'])} | {_fmt(pl['z'], '{:+.2f}')} | {rule_s} | "
            f"**{r['verdict']}** |")
    for r in results:
        gate, pl = r["gate"], r["placebo"]
        lines += ["", f"## {r['market']} — VERDICT: **{r['verdict']}** (confirmatory)", "",
                  f"- Events: {r['n_rows']:,} panel rows · {r['n_symbols']} symbols · "
                  f"{len(r['features'])} features ({r['n_features_pruned']}/{r['n_features_input']} kept, "
                  f"ρ>{RHO_THRESHOLD} prune) · embargo {r['embargo_td']} td · runtime {r['runtime_sec']}s",
                  f"- Rule (frozen on CALIB folds): {_rule_str(r.get('rule'))}",
                  f"- Placebo: observed edge {_fmt(pl['observed_edge'])}, null mean "
                  f"{_fmt(pl['null_mean'])}, sd {_fmt(pl['null_sd'])}, z "
                  f"{_fmt(pl['z'], '{:+.2f}')} ({pl['n_seeds']}/{N_PLACEBO_SEEDS} seeds run"
                  f"{'' if pl['n_seeds'] >= N_PLACEBO_SEEDS else ', budget-truncated'})",
                  f"- Pooled rank-IC (P̂_profit vs frozen return): {_fmt(gate.get('pooled_ic'))}",
                  f"- Pickles: {r['n_models_saved']} saved in `{r['model_dir']}` "
                  f"(all learners × 3 binaries × folds, verdict-independent)",
                  "", "| fold | events | selected | baseline mean | model mean | edge | IC | win |",
                  "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |"]
        for f in gate["folds"]:
            lines.append(
                f"| {f['fold']} | {f['n_events']:,} | {f['n_selected']:,} | "
                f"{_fmt(f['baseline_mean'])} | {_fmt(f['model_mean'])} | {_fmt(f['edge'])} | "
                f"{_fmt(f.get('ic'))} | {'yes' if f['win'] else 'no'} |")
        if 0 < gate["n_selected"] < SMALL_SELECTION:
            lines += ["", f"- ⚠ **Small selected set** ({gate['n_selected']:,} of "
                      f"{gate['n_events']:,} canonical events): the frozen-rule return `r_frozen` is "
                      f"fat-tailed (|max| ≈ {_fmt(r.get('ret_max_abs'), '{:.2f}')}), so the pooled edge "
                      f"can be set by a handful of extreme events while the pooled rank-IC stays near "
                      f"zero ({_fmt(gate.get('pooled_ic'), '{:+.3f}')}). Treat this verdict as "
                      f"record-only — no edge is claimed (admin direction 2026-11-09)."]
        for b in binary_train.BINARY_COLUMNS:
            lines.append(f"- Top TreeSHAP — `{b}`: {_shap_line(r['treeshap'].get(b, {}))}")
    lines += ["", "## Notes / deviations", "",
              "- Confirmatory no-edge run (admin 2026-11-09): the gate arithmetic is reported for "
              "the record; no shortlist, no deployment, no live trading.",
              "- The two-threshold rule is a filter, not a renormalisation: rows are taken on the "
              "intersection `P̂_profit ≥ τ_p AND P̂_stop ≤ τ_s` over canonical at-bottom rows.",
              "- Pickles exist for every grid point (admin override), including folds whose gate "
              "fold lost; they are evaluation artefacts only.",
              ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="WI-035 three-binary two-threshold gate (D-022 §3)")
    parser.add_argument("--market", default="ALL", help="USD | CAD | ALL (default ALL)")
    parser.add_argument("--limit", type=int, default=None, help="Max symbols per market (smoke).")
    parser.add_argument("--out", default=None, help="Output dir (smoke runs use /tmp).")
    parser.add_argument("--allow-fixture", action="store_true")
    parser.add_argument("--placebo-seeds", type=int, default=N_PLACEBO_SEEDS)
    parser.add_argument("--learners", default=",".join(binary_train.LEARNERS))
    parser.add_argument("--cache-dir", default="/tmp/wi035", help="Panel-parquet cache dir.")
    args = parser.parse_args(argv)

    smoke = os.environ.get("WI035_SMOKE", "").strip()
    if args.limit is None and smoke.isdigit():
        args.limit = int(smoke)
    if args.out is None and smoke:
        args.out = "/tmp/wi035_smoke"
    learners = tuple(s.strip() for s in args.learners.split(",") if s.strip())

    from src.market_cli import cli_markets
    markets = cli_markets(args.market, prog="wi035.binary_evaluate")
    if markets is None:
        return 2
    out_dir = Path(args.out) if args.out else REPORTS_DIR
    cfg = train.load_settings()
    t0 = time.time()
    results = [run_market(m, cfg, out_dir=out_dir, limit=args.limit,
                          allow_fixture=args.allow_fixture,
                          placebo_seeds=args.placebo_seeds, learners=learners,
                          cache_dir=Path(args.cache_dir)) for m in markets]
    report = write_summary(results, out_dir / "wi035_summary.md")
    for r in results:
        print(f"[wi035.binary] {r['market']}: verdict={r['verdict']} folds={r['gate']['n_folds_pos']}/5 "
              f"edge={_fmt(r['gate']['pooled_edge'])} z={_fmt(r['placebo']['z'], '{:+.2f}')} "
              f"pickles={r['n_models_saved']} runtime={r['runtime_sec']}s")
    print(f"[wi035.binary] report -> {report} | total {round(time.time() - t0, 1)}s")
    print("[wi035.binary] EXIT:0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
