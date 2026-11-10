"""WI-045 — CALIB->EVAL edge-decay probe on the ratified WI-042 artifacts (Layer-1 diagnostic).

Read-only: the frozen `reports/l2/rerun_modern.json` (WI-042, ratified 2026-11-10) is read once and
never rewritten — no learner re-fitted, no EVAL window scored again, no verdict re-derived. Per
ratified ADOPT cell the probe decomposes the frozen CALIB edge into the three candidate decay
mechanisms — (a) tau-mass retention, (b) fold concentration, (c) cost floor (the frozen 25 bps) —
and ranks them by share of edge decay.

    uv run python -m src.l2_overlay.edge_decay_probe                 # reports/l2/edge_decay_probe.{md,json}
    uv run python -m src.l2_overlay.edge_decay_probe --smoke --out /tmp/l2_edge_decay_probe_smoke

Identities (in `tests/test_edge_decay_probe.py`, on synthetic CALIB-only fixtures): `gross_bps -
cost_bps == net_bps`; `sum(fold contributions) == fold-reconstructed edge` (exact when the tau keeps
a uniform per-fold fraction); `sum(shares) == 1`. The frozen fold table is the harness' `fold_edges`
over the calib|ev mask, so `fold_recon_gap_bps` is reported, not hidden. Layer 1 (D-023/D-025):
no trading claim, no shortlist, no deployment.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import numpy as np

from src.l2_overlay import harness as H

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "reports" / "l2"
INPUT_JSON = REPORTS_DIR / "rerun_modern.json"
OUT_STEM = "edge_decay_probe"
DEFAULT_SMOKE_DIR = "/tmp/l2_edge_decay_probe_smoke"
COST_BPS = 25.0                       # frozen round-trip cost already inside `r_frozen` (WI-042)
MECHANISMS = ("tau-mass", "fold-concentration", "cost-floor")
SMOKE_VERDICT = "ADOPT"               # fixture cells pass through the ratified-cell filter
N_JOBS = 2                            # repo law; nothing here fans out, kept explicit
__all__ = ["load_payload", "adopt_cells", "fold_table", "fold_concentration", "decompose_cell",
           "probe_cells", "family_ranking", "synthetic_record", "synthetic_fixture", "write_reports",
           "main"]


def _fmt(x, spec: str = "{:.4f}") -> str:
    return "n/a" if not np.isfinite(float(x)) else spec.format(float(x))


def _bps(x) -> float:
    """A frozen edge (return units) as basis points, NaN-safe."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return float("nan")
    return v * 1e4 if np.isfinite(v) else float("nan")


def load_payload(path=INPUT_JSON) -> dict:
    """The frozen WI-042 payload (read-only; the file is never written back)."""
    with open(Path(path)) as fh:
        return json.load(fh)


def adopt_cells(payload) -> dict:
    """Every ratified ADOPT cell, market-tagged (the flat `cells` list carries no market column)."""
    out = []
    for market, blk in sorted(payload.get("markets", {}).items()):
        out += [dict(c, market=market) for c in blk.get("cells", []) if c.get("verdict") == "ADOPT"]
    return sorted(out, key=lambda c: (c["market"], c["cell"]))


def fold_table(folds) -> list[dict]:
    """Frozen fold rows with n-weighted contributions in bps (weights sum to 1 by construction)."""
    rows = list(folds or [])
    total = float(sum(int(f["n_events"]) for f in rows)) or 1.0
    out = []
    for f in rows:
        w = int(f["n_events"]) / total
        out.append({"fold": int(f["fold"]), "n_events": int(f["n_events"]),
                    "n_selected": int(f["n_selected"]), "weight": w,
                    "edge_bps": _bps(f["edge"]), "contrib_bps": w * _bps(f["edge"])})
    return out


def fold_concentration(rows) -> tuple[int, float]:
    """(best fold id, share of the positive fold contributions it carries); (-1, 0.0) if none."""
    pos = [r for r in rows if np.isfinite(r["contrib_bps"]) and r["contrib_bps"] > 0.0]
    if not pos:
        return -1, 0.0
    top = max(pos, key=lambda r: r["contrib_bps"])
    return int(top["fold"]), float(top["contrib_bps"] / sum(r["contrib_bps"] for r in pos))


def decompose_cell(cell, *, cost_bps: float = COST_BPS) -> dict:
    """Per-cell decomposition of the frozen CALIB edge: mass retained, fold shares, gross-vs-net."""
    folds, cost_bps = fold_table(cell.get("folds")), float(cost_bps)
    net_bps = _bps(cell.get("calib_edge"))
    gross_bps = net_bps + cost_bps                          # identity: gross - cost == net
    recon_bps = float(sum(f["contrib_bps"] for f in folds))
    top_fold, top_share = fold_concentration(folds)
    n_calib, n_sel = int(cell.get("n_calib") or 0), int(cell.get("n_selected") or 0)
    retained = (n_sel / n_calib) if n_calib else float("nan")
    eval_bps = _bps(cell.get("eval_edge"))
    decay_bps = max(net_bps - eval_bps, 0.0) if np.isfinite(eval_bps) else float("nan")
    weights = {
        "tau-mass": (float(np.clip(1.0 - retained, 0.0, 1.0)) if np.isfinite(retained) else 0.0),
        "fold-concentration": float(np.clip(top_share, 0.0, 1.0)),
        "cost-floor": (float(np.clip(cost_bps / gross_bps, 0.0, 1.0)) if gross_bps > 0.0 else 1.0),
    }
    total = float(sum(weights.values()))
    shares = {m: (weights[m] / total if total > 0.0 else 0.0) for m in MECHANISMS}
    driver = max(MECHANISMS, key=lambda m: (shares[m], -MECHANISMS.index(m)))
    return {"market": str(cell.get("market", "")), "cell": str(cell.get("cell", "")),
            "question": str(cell.get("question", "")), "source": str(cell.get("source", "")),
            "conditioning": str(cell.get("conditioning", "")), "verdict": str(cell.get("verdict", "")),
            "tau": float(cell.get("tau", float("nan"))), "n_calib": n_calib, "n_eval":
            int(cell.get("n_eval") or 0), "n_selected": n_sel, "mass_retained": retained,
            "net_edge_bps": net_bps, "cost_bps": cost_bps, "gross_edge_bps": gross_bps,
            "cost_floor_binds": bool(np.isfinite(net_bps) and net_bps < cost_bps),
            "folds": folds, "fold_recon_bps": recon_bps,
            "fold_recon_gap_bps": recon_bps - net_bps, "top_fold": top_fold, "top_fold_share": top_share,
            "decay_bps": decay_bps, "weights": weights, "shares": shares, "driver": driver}


def probe_cells(payload) -> list[dict]:
    """The probe's whole per-cell pass: ratified ADOPT cells -> decomposed rows."""
    return [decompose_cell(c) for c in adopt_cells(payload)]


def family_ranking(rows) -> dict:
    """Decay-weighted share of edge decay per mechanism + how many cells each mechanism drives."""
    decay = [max(float(r["decay_bps"]), 0.0) if np.isfinite(r["decay_bps"]) else 0.0 for r in rows]
    total = float(sum(decay))
    agg = {m: (float(sum(d * r["shares"][m] for d, r in zip(decay, rows)) / total)
               if total > 0.0 else 0.0) for m in MECHANISMS}
    order = sorted(MECHANISMS, key=lambda m: (-agg[m], MECHANISMS.index(m)))
    wins = {m: int(sum(1 for r in rows if r["driver"] == m)) for m in MECHANISMS}
    line = (f"Mechanism ranking (decay {total:.1f} bps over {len(rows)} ratified ADOPT cells) — "
            + "; ".join(f"{i}. {m} {100.0 * agg[m]:.1f}% ({wins[m]} cells)"
                        for i, m in enumerate(order, 1)))
    return {"order": order, "shares": agg, "cell_wins": wins, "decay_bps": total,
            "n_cells": int(len(rows)), "line": line}


def synthetic_record(name: str, score, ret, fold) -> dict:
    """One CALIB-only cell in the frozen-cell shape — the harness picks tau, no EVAL rows exist."""
    p, r = np.asarray(score, "float32"), np.asarray(ret, "float32")
    f, calib = np.asarray(fold, "int64"), np.ones(len(p), dtype=bool)
    ok, reason = H.feasible(p, H.TAU_GRID)
    if not ok:
        raise ValueError(f"fixture '{name}' is infeasible: {reason}")
    best, _table = H.pick_tau_by_calib_edge(p, r, calib, H.TAU_GRID)
    return {"market": "SYN", "cell": name, "question": "syn", "source": "raw", "conditioning": "all",
            "verdict": SMOKE_VERDICT, "tau": float(best["tau"]), "calib_edge": float(best["calib_edge"]),
            "eval_edge": float("nan"), "n_calib": int(p.size), "n_eval": 0,
            "n_selected": int(best["n_selected"]), "folds": H.fold_edges(p, r, f, float(best["tau"]),
                                                                        calib), "reason": ""}


def synthetic_fixture(seed: int = 11) -> dict:
    """CALIB-only synthetic payload with one archetype per mechanism; no EVAL window is generated."""
    rng = np.random.default_rng(int(seed))
    per, nf = 250, 4
    n = per * nf
    fold = np.repeat(np.arange(nf), per)
    u = rng.random(n)
    rank = (np.argsort(np.argsort(u)) / n).astype("float32")     # (a) narrow mass, strong ranking
    cells = [synthetic_record("syn|raw|mass", (0.05 + 0.06 * rank).astype("float32"),
                              (0.010 * rank + rng.normal(0.0, 0.001, n)).astype("float32"), fold)]
    v = rng.random(n)                                            # (b) edge in fold 2 only
    ret_fold = np.where(fold == 2, 0.05 * (v - 0.5), 0.0) + rng.normal(0.0, 0.002, n)
    cells.append(synthetic_record("syn|raw|fold", v.astype("float32"), ret_fold.astype("float32"), fold))
    w = rng.random(n)                                            # (c) 99% mass kept, ~1 bps edge
    score_c = np.where(w < 0.01, 0.45, 0.55).astype("float32")
    weak = np.where(w < 0.01, -0.004, 0.002) + rng.normal(0.0, 0.0005, n)
    cells.append(synthetic_record("syn|raw|cost", score_c, weak.astype("float32"), fold))
    for c in cells:   # synthetic placeholder so the smoke ranking renders; NO EVAL rows exist
        c["eval_edge"] = 0.25 * c["calib_edge"]
    return {"probe_input": "synthetic:CALIB-only", "smoke": True, "costs_bps": COST_BPS,
            "markets": {"SYN": {"cells": cells}}}


def write_reports(rows, ranking, *, out_dir, input_path=INPUT_JSON, smoke=False) -> tuple:
    """`<out>/edge_decay_probe.md` + `.json` — table for every ADOPT cell, then fold contributions."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    gen = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    label = str(input_path).rsplit("/", 1)[-1]
    payload = {"probe": "wi045_edge_decay_probe", "generated": gen, "smoke": bool(smoke),
               "input": str(input_path), "cost_bps": COST_BPS, "n_cells": int(len(rows)),
               "mechanisms": list(MECHANISMS), "ranking": ranking, "cells": rows}
    tag = "  (smoke / synthetic CALIB-only fixture)" if smoke else ""
    lines = ["# WI-045 — CALIB->EVAL edge-decay probe (frozen WI-042 artifacts, Layer 1)", "",
             f"- Generated (UTC): {gen}{tag}",
             f"- Input: `{label}` read-only — {len(rows)} ratified ADOPT cells; cost floor "
             f"{COST_BPS:.0f} bps is already inside `r_frozen` (WI-042)",
             f"- **{ranking['line']}**",
             "- Layer separation: derived from the frozen artifact only — no learner refit, no EVAL "
             "scoring, no new verdicts (D-023/D-025 Layer 1); verdicts stay PROVISIONAL.", "",
             "| cell | tau | CALIB n | selected | mass kept | net bps | cost | gross bps | decay bps | "
             "top fold (share) | tau-mass | fold-conc | cost-floor | driver |",
             "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | ---: | ---: | "
             "---: | :--- |"]
    lines += [f"| `{r['market']}|{r['cell']}` | {_fmt(r['tau'], '{:.2f}')} | {r['n_calib']:,} | "
              f"{r['n_selected']:,} | {_fmt(r['mass_retained'], '{:.3f}')} | {_fmt(r['net_edge_bps'], '{:+.2f}')} | "
              f"{r['cost_bps']:.0f} | {_fmt(r['gross_edge_bps'], '{:+.2f}')} | "
              f"{_fmt(r['decay_bps'], '{:+.2f}')} | {r['top_fold']} ({_fmt(r['top_fold_share'], '{:.2f}')}) | "
              f"{_fmt(r['shares']['tau-mass'], '{:.2f}')} | {_fmt(r['shares']['fold-concentration'], '{:.2f}')} | "
              f"{_fmt(r['shares']['cost-floor'], '{:.2f}')} | **{r['driver']}** |" for r in rows]
    lines += ["", "## Fold contributions (frozen harness table, n_events-weighted)", "",
              "| cell | fold | events | selected | edge bps | contribution bps |",
              "| :--- | ---: | ---: | ---: | ---: | ---: |"]
    for r in rows:
        lines += [f"| `{r['market']}|{r['cell']}` | {f['fold']} | {f['n_events']:,} | "
                  f"{f['n_selected']:,} | {_fmt(f['edge_bps'], '{:+.3f}')} | "
                  f"{_fmt(f['contrib_bps'], '{:+.4f}')} |" for f in r["folds"]]
    if rows:
        lines += ["", f"- Fold reconstruction `sum(contrib) = {_fmt(rows[0]['fold_recon_bps'], '{:+.3f}')} "
                  "bps`; the frozen table spans calib|ev, so `fold_recon_gap_bps` reports the gap to the "
                  "CALIB edge instead of hiding it.",
                  "- Record-only diagnostic: no shortlist, no deployment, no live trading."]
    else:
        lines += ["", "- no ADOPT cell in the input."]
    md, js = out / f"{OUT_STEM}.md", out / f"{OUT_STEM}.json"
    md.write_text("\n".join(lines) + "\n")
    js.write_text(json.dumps(payload, indent=1, sort_keys=True, default=str) + "\n")
    return md, js


def main(argv=None) -> int:
    """CLI: frozen-artifact run (default) or `--smoke` on the synthetic CALIB-only fixture."""
    ap = argparse.ArgumentParser(description="WI-045 edge-decay probe (frozen WI-042 artifacts, L1)")
    ap.add_argument("--input", default=None, help=f"frozen rerun JSON (default {INPUT_JSON})")
    ap.add_argument("--out", default=None, help="report dir (smoke defaults to /tmp)")
    ap.add_argument("--smoke", action="store_true", help="synthetic CALIB-only fixture to /tmp")
    a = ap.parse_args(argv)
    if a.smoke:
        payload, out, src = synthetic_fixture(), a.out or DEFAULT_SMOKE_DIR, "synthetic:CALIB-only"
    else:
        src = Path(a.input or INPUT_JSON)
        payload, out = load_payload(src), a.out or REPORTS_DIR
    rows = probe_cells(payload)
    ranking = family_ranking(rows)
    md, _js = write_reports(rows, ranking, out_dir=out, input_path=src, smoke=bool(a.smoke))
    print(f"[wi045.probe] {'smoke' if a.smoke else 'run'} cells={len(rows)} | {ranking['line']}")
    print(f"[wi045.probe] -> {md} (+ .json) | EXIT:0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
