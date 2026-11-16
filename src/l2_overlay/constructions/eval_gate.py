"""WI-071 — one-shot EVAL gate (D-027 §5/§7/§11, Layer 2 trading verdict).

Freeze (hashed pre-registration) → score EVAL **once** per pre-registered family member → BH-FDR
across the **full** family (constructions × markets × signals, never per-construction) → fold report
→ verdict per construction, always tagged PROVISIONAL (AGENTS.md: nothing adopted, promoted or closed
before the admin ratifies in chat).

    uv run python -m src.l2_overlay.constructions.eval_gate --smoke   # /tmp/l2_eval_gate_smoke

Code+tests only (WI-071): the real EVAL read is PM-owned and refused here; smoke uses
`harness.synthetic_fixture` and never reads under `data/`. Reuse (never reimplement)
`harness.preregistration_template/prereg_hash/load_preregistration` and `harness.score_eval`.
"""
from __future__ import annotations

import argparse, datetime as dt, json, math
from pathlib import Path

import numpy as np

from src.l2_overlay import fold_report as foldrep
from src.l2_overlay import harness as H

BASE_DIR = Path(__file__).resolve().parents[3]
EVAL_ROOT = BASE_DIR / "reports" / "l2_eval"      # frozen pre-registration + verdict artifacts
PREREG_PATH, SMOKE_ROOT = EVAL_ROOT / H.PREREG_NAME, Path("/tmp/l2_eval_gate_smoke")
VERDICTS_MD, VERDICTS_JSON, FDR_ALPHA, BPS = "verdicts.md", "verdicts.json", 0.05, 1.0e4
PROVISIONAL_TAG, LABELS = "PROVISIONAL", ("ADOPT", "REJECT", "INCONCLUSIVE")
SMOKE_CONSTRUCTIONS = ("b_xsec_topk", "a_fixed_time_exits")
SMOKE_MARKETS, SMOKE_SIGNALS = ("USD", "CAD"), ("xsec_vol_rank_cont", "b_hold")
__all__ = ["EVAL_ROOT", "PREREG_PATH", "SMOKE_ROOT", "VERDICTS_MD", "VERDICTS_JSON", "FDR_ALPHA",
           "PROVISIONAL_TAG", "LABELS", "BPS", "FamilyDefect", "DoubleScoringError", "entry_key",
           "to_bps", "p_value_from_z", "verify_prereg_hash", "score_eval_once", "reset_ledger",
           "scored_keys", "bh_fdr_across_family", "label_for", "tagged", "gate_report",
           "emit_verdicts", "smoke_family", "run_smoke", "main"]
_SCORED: set[str] = set()          # process-wide one-shot ledger: one EVAL look per family member

class FamilyDefect(ValueError):
    """The pre-registered FDR family is absent, duplicated or incomplete."""

class DoubleScoringError(RuntimeError):
    """A second EVAL score was attempted for the same family member — the look is one-shot."""

def reset_ledger() -> None:                                  # test seam; a real run never resets
    _SCORED.clear()

def scored_keys() -> frozenset:                              # members whose EVAL look is spent
    return frozenset(_SCORED)

def entry_key(construction, market, signal) -> str:          # D-027 §7 family key
    return f"{construction}|{market}|{signal}"

def to_bps(edge) -> float:                                   # decimal edge → bps (floor is bps)
    e = float(edge)
    return e * BPS if np.isfinite(e) else float("nan")

def p_value_from_z(z) -> float:                              # one-sided p (== norm.sf, stdlib)
    return 0.5 * math.erfc(float(z) / math.sqrt(2.0)) if np.isfinite(z) else float("nan")

def smoke_family() -> list[str]:                             # synthetic constructions × markets × signals
    return [entry_key(c, m, s) for c in SMOKE_CONSTRUCTIONS
            for m in SMOKE_MARKETS for s in SMOKE_SIGNALS]

def verify_prereg_hash(path=PREREG_PATH) -> dict:
    """sha256-verified pre-registration (`harness.load_preregistration`) + family sanity.

    A post-freeze edit (hash mismatch), an absent family or a duplicate member refuses the gate.
    """
    payload = H.load_preregistration(path)                       # ValueError on a post-freeze edit
    family = payload.get("fdr_family")
    if not isinstance(family, list) or not family:
        raise FamilyDefect(f"pre-registration {path} lists no FDR family — refusing to score EVAL")
    if len(set(map(str, family))) != len(family):
        raise FamilyDefect("pre-registration FDR family carries duplicate entries")
    return payload

def score_eval_once(key, probs, ret, mask, tau, *, prereg, ledger=None) -> float:
    """The one EVAL touch for `key` — lock-checked, ledger-guarded, harness-scored.

    The key is burned *before* scoring: a failed look is still a look (D-027 §7).
    """
    H.assert_eval_unlocked(prereg)           # refuses while `eval_lock_released` is false
    store = _SCORED if ledger is None else ledger
    if str(key) in store:
        raise DoubleScoringError(f"EVAL already scored for {key!r} — the look is one-shot")
    store.add(str(key))
    return H.score_eval(probs, ret, mask, tau)                   # reuse the harness scorer

def bh_fdr_across_family(pvals: dict, family, *, alpha: float = FDR_ALPHA) -> dict:
    """BH step-up q-values over the WHOLE pre-registered family — never per-construction.

    Every listed member must be declared: an absent key is a defect (no silent drops). An INERT member
    is declared with a non-finite p, still counted in the denominator (conservative) and gets q = NaN —
    the denominator is `len(family)`; only finite p-values are ranked.
    """
    fam = [str(k) for k in family]
    if not fam:
        raise FamilyDefect("empty FDR family — BH-FDR needs the pre-registered grid")
    if len(set(fam)) != len(fam):
        raise FamilyDefect(f"duplicate FDR family entries: {len(fam) - len(set(fam))}")
    for what, keys in (("outside the pre-registered family", set(map(str, pvals)) - set(fam)),
                       ("with no declared EVAL result", set(fam) - set(map(str, pvals)))):
        if keys:
            raise FamilyDefect(f"family members {what}: {sorted(keys)[:3]}")
    p = {k: float(pvals[k]) for k in fam}
    tested = [k for k in fam if np.isfinite(p[k])]
    q = {k: float("nan") for k in fam}
    if tested:                                   # step-up, monotone from the largest p
        order = sorted(tested, key=lambda k: (p[k], k))
        vals = np.asarray([p[k] for k in order], dtype="float64")
        qvals = np.minimum.accumulate((len(fam) * vals / np.arange(1, vals.size + 1))[::-1])[::-1]
        q.update({k: float(v) for k, v in zip(order, qvals.clip(0.0, 1.0))})
    return {"alpha": float(alpha), "family_size": len(fam), "n_tested": len(tested),
            "n_untested": len(fam) - len(tested), "q_values": q,
            "rejected": {k: bool(np.isfinite(q[k]) and q[k] < float(alpha)) for k in fam}}

def label_for(net_edge_bps, fold, q, *, floor_bps: float = H.MATERIALITY_FLOOR_BPS,
              alpha: float = FDR_ALPHA) -> str:
    """D-027 §11: materiality floor + fold ceiling + BH rejection → ADOPT/REJECT/INCONCLUSIVE.
    A missing fold report fails closed (that column is mandatory) and an edge under the floor rejects
    before the q-value is consulted — the "≤1 bp ADOPT" repeat is blocked structurally.
    """
    edge, qv = float(net_edge_bps), float(q)
    if not np.isfinite(edge) or edge < float(floor_bps):
        return "REJECT"
    if not dict(fold or {}).get("fold_ceiling_ok", False):
        return "REJECT"
    return "ADOPT" if np.isfinite(qv) and qv < float(alpha) else "INCONCLUSIVE"

def tagged(label) -> str:                                    # no ratified state exists in this WI
    return f"{str(label).upper()} ({PROVISIONAL_TAG})"

def gate_report(prereg: dict, scored: dict, *, alpha: float = FDR_ALPHA) -> list[dict]:
    """Per pre-registered member: full-family BH q + the PROVISIONAL label.
    `scored[key]` carries construction/market/signal, net_edge_bps (already bps), the fold report and
    the member's p_value (NaN for a declared-INERT member) — full-family q, then the label.
    """
    H.assert_eval_unlocked(prereg)
    family = [str(k) for k in prereg.get("fdr_family") or []]
    bh = bh_fdr_across_family({k: scored[k].get("p_value", float("nan"))
                               for k in family if k in scored}, family, alpha=alpha)
    floor = float(prereg.get("materiality_floor_bps", H.MATERIALITY_FLOOR_BPS))
    rows = []
    for k in family:
        s, q = scored[k], bh["q_values"][k]
        rows.append({"key": k, "construction": str(s.get("construction", k)),
                     "market": str(s.get("market", "")), "signal": str(s.get("signal", "")),
                     "net_edge_bps": float(s.get("net_edge_bps", float("nan"))), "q_value": float(q),
                     "fold_report": dict(s.get("fold_report") or {}),
                     "label": label_for(s.get("net_edge_bps"), s.get("fold_report"), q,
                                        floor_bps=floor, alpha=alpha)})
    return rows

def _fmt(x, spec: str = "{:.4f}") -> str:                    # NaN-tolerant cell formatting
    return "n/a" if not np.isfinite(x) else spec.format(float(x))

def _markdown(payload: dict) -> str:
    lines = ["# L2 EVAL verdicts — one-shot gate (WI-071, D-027 Phase 5)", "",
             f"- Generated (UTC): {payload['generated']} · family `{payload['family_id']}` · fdr alpha "
             f"{payload['fdr_alpha']:.2f} over the FULL pre-registered family "
             f"({payload['family_size']} members, {payload['n_tested']} tested).",
             "- **Every label below is PROVISIONAL** — the admin ratifies in chat before anything is "
             "adopted, promoted or closed (AGENTS.md provisional-verdict rule).", "",
             "| construction | market | signal | net edge bps | fold ceiling | max fold share | BH q "
             "| verdict |", "| --- | --- | --- | ---: | --- | ---: | ---: | --- |"]
    for r in payload["verdicts"]:
        f = dict(r["fold_report"] or {})
        ceiling = "missing" if not f else ("pass" if f.get("fold_ceiling_ok") else "FAIL")
        lines.append(f"| {r['construction']} | {r['market']} | {r['signal']} | "
                     f"{_fmt(r['net_edge_bps'], '{:+.2f}')} | {ceiling} | "
                     f"{_fmt(f.get('max_fold_share', float('nan')))} | {_fmt(r['q_value'])} "
                     f"| **{r['label_tagged']}** |")
    lines += ["", f"- Counts: {payload['verdict_counts']} — all PROVISIONAL.",
              "- Record-only: no shortlist, no deployment, no live trading."]
    return "\n".join(lines) + "\n"

def emit_verdicts(records, out_dir=EVAL_ROOT, *, prereg: dict | None = None) -> dict:
    """Write `verdicts.md` + `verdicts.json`: net edge, fold report, BH q, PROVISIONAL label."""
    for r in records:
        if str(r.get("label", "")).upper() not in LABELS:
            raise ValueError(f"verdict label {r.get('label')!r} not in {LABELS}")
    rows = [{"key": str(r["key"]), "construction": str(r.get("construction", "")),
             "market": str(r.get("market", "")), "signal": str(r.get("signal", "")),
             "net_edge_bps": float(r.get("net_edge_bps", float("nan"))),
             "fold_report": dict(r.get("fold_report") or {}),
             "q_value": float(r.get("q_value", float("nan"))),
             "label": str(r["label"]).upper(), "label_tagged": tagged(r["label"]),
             "status": PROVISIONAL_TAG} for r in records]
    finite = sum(np.isfinite(r["q_value"]) for r in rows)
    payload = {"family_id": str((prereg or {}).get("family_id", "l2_rebuild")),
               "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "layer": "2 (overlay/trading)", "provisional": True, "tag": PROVISIONAL_TAG,
               "ratification": "admin chat ratification required (AGENTS.md provisional-verdict rule)",
               "fdr_alpha": FDR_ALPHA, "n_records": len(rows), "verdicts": rows,
               "family_size": len(rows), "n_tested": int(finite),
               "n_untested": int(len(rows) - finite),
               "verdict_counts": {v: sum(r["label"] == v for r in rows)
                                  for v in LABELS if any(r["label"] == v for r in rows)}}
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path, md_path = out / VERDICTS_JSON, out / VERDICTS_MD
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    md_path.write_text(_markdown(payload))
    return {"md": md_path, "json": json_path, "payload": payload}

def run_smoke(out_dir=SMOKE_ROOT) -> dict:
    """Synthetic end-to-end: frozen prereg → one EVAL score per member → full-family BH → verdicts."""
    out = Path(out_dir)
    prereg = H.preregistration_template()
    prereg.update({"family_id": "l2_rebuild_smoke", "constructions": list(SMOKE_CONSTRUCTIONS),
                   "fdr_family": smoke_family(), "eval_lock_released": True})
    prereg = verify_prereg_hash(H.write_preregistration(prereg, out / H.PREREG_NAME))
    H.assert_eval_unlocked(prereg)             # gate: EVAL stays unread until the lock releases
    reset_ledger()
    seeds, scored = list(H.QUESTION_SEEDS), {}          # one distinct fixture per family member
    for i, key in enumerate(map(str, prereg["fdr_family"])):
        fx = H.synthetic_fixture(seeds[i % len(seeds)], inert=(i == 0))   # first: no operating point
        probs, ret = np.asarray(fx["probs"], "float64"), fx["events"]["ret"].to_numpy("float64")
        best, _table = H.pick_tau_by_calib_edge(probs, ret, fx["calib_mask"], fx["tau_grid"])
        construction, market, signal = key.split("|")
        scored[key] = {"construction": construction, "market": market, "signal": signal,
                       "net_edge_bps": to_bps(score_eval_once(key, probs, ret, fx["eval_mask"],
                                                             best["tau"], prereg=prereg)),
                       "fold_report": foldrep.fold_report(H.fold_edges(
                           probs, ret, fx["events"]["fold"], best["tau"], fx["eval_mask"])),
                       "p_value": p_value_from_z(H.placebo_z(probs, ret, best["tau"]))}
    gathered = gate_report(prereg, scored)
    return {"records": gathered, "paths": emit_verdicts(gathered, out, prereg=prereg),
            "prereg": out / H.PREREG_NAME}

def main(argv=None) -> int:
    """CLI: `--smoke` (synthetic, /tmp) or a refusal for the PM-owned real EVAL run."""
    ap = argparse.ArgumentParser(description="WI-071 one-shot EVAL gate (D-027 §7/§11)")
    ap.add_argument("--prereg", default=PREREG_PATH, help="pre-registration json (hash-verified)")
    ap.add_argument("--out", default=None, help="verdict dir (smoke defaults to /tmp/l2_eval_gate_smoke)")
    ap.add_argument("--smoke", action="store_true", help="synthetic fixtures only (no data/ read)")
    args = ap.parse_args(argv)
    if not args.smoke:
        H.assert_eval_unlocked(verify_prereg_hash(args.prereg))  # hash mismatch refuses here
        print("[l2.eval_gate] REFUSED: the real EVAL scoring run is PM-owned (WI-071 ships code+tests)")
        return 2
    res = run_smoke(args.out or SMOKE_ROOT)
    print(f"[l2.eval_gate] smoke: {len(res['records'])} members, ledger={len(scored_keys())}, "
          f"verdicts -> {res['paths']['md'].parent} ({res['paths']['md'].name}, "
          f"{res['paths']['json'].name}) | every label tagged PROVISIONAL | EXIT:0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
