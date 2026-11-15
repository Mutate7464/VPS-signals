"""WI-041/065 — Layer-2 overlay harness (D-024 §2): feasibility → CALIB-only tau → one-shot EVAL
→ 5-seed placebo → per-fold edges → verdict. WI-065 adds the wi040∪wi048 union loader (cell-key
dedup + no-cell-twice assertion), the mandatory fold report, the hashed pre-registration + EVAL lock
and the CALIB-failure stop flag. No learner refit, no EVAL read while tuning, no AUC selection.

    uv run python -m src.l2_overlay.harness --smoke                     # reports/l2_harness_smoke/
    L2_SMOKE=1 uv run python -m src.l2_overlay.harness --question wi037 --out /tmp/l2_smoke
    uv run python -m src.l2_overlay.harness --prepared /tmp/wi042/USD.parquet

A `--prepared` parquet carries `p, ret` (or `r_frozen`), `fold`, `date`: CALIB is `date < --calib-end`, EVAL `date >= --eval-start`.
"""
from __future__ import annotations

import argparse, datetime as dt, hashlib, json, os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from src.l2_overlay.fold_report import (FOLD_CEILING_SHARE, fold_report as build_fold_report,
                                        write_fold_report)
from src.swing_bsh.evaluate import selection_edge

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "reports" / "l2"
DEFAULT_SMOKE_DIR = BASE_DIR / "reports" / "l2_harness_smoke"
DEFAULT_SMOKE_Q = "wi037"
UNION_ROOT = BASE_DIR / "data" / "models"
WI040_MANIFEST, WI048_MANIFEST = UNION_ROOT / "wi040" / "manifest.parquet", UNION_ROOT / "wi048" / "manifest.parquet"
CELL_KEY = ("market", "learner", "variant", "family", "horizon", "fold")  # D-027 §4: family=`binary`, horizon=`h`
CELL_SOURCES = {"family": "binary", "horizon": "h"}   # real manifests carry no family/horizon columns
MISSING_KEY_SENTINEL = "\x00<missing>"                # keying only: never a real manifest value
N_JOBS = 2                      # repo law; nothing here fans out, kept explicit
MIN_CALIB_EVENTS = 200          # D-024 §2 per-cell CALIB event floor
N_PLACEBO_SEEDS = 5             # CB-05 form without refits: probability permutations
PLACEBO_SEED0, PLACEBO_Z_MIN = 7000, 2.0
CALIB_END, EVAL_START = "2022-05-02", "2022-07-01"   # frozen windows (WI-037 lineage)
TAU_GRID: tuple[float, ...] = (0.1, 0.2, 0.3, 0.5, 0.7)
QUESTION_SEEDS = {"wi037": 41, "wi033": 42, "wi030": 43, "wi028": 44, "wi012": 45,
                  "wi018": 46, "wi011": 47}
PREREG_NAME, PREREG_VERSION = "l2_prereg_template.json", 1
MATERIALITY_FLOOR_BPS = 10.0    # D-027 §11.1: ADOPT requires net CALIB edge ≥ 10 bps
MIN_NAMES_PER_DATE = 20         # D-027 §11.3: xsec INERT precheck name floor
XSEC_MIN_CALIB_EVENTS = 200     # D-027 §7: ≥200 CALIB events + a τ span (the D-024 floor)
__all__ = ["OverlayResult", "run_overlay", "classify", "feasible", "pick_tau_by_calib_edge",
           "placebo_z", "score_eval", "fold_edges", "selected_mask", "synthetic_fixture",
           "write_report", "main", "load_union", "assert_no_duplicate_cells", "xsec_inert_precheck",
           "preregistration_template", "prereg_hash", "write_preregistration", "load_preregistration",
           "EvalLockError", "assert_eval_unlocked", "eval_read", "calib_stop"]


@dataclass
class OverlayResult:
    """D-024 §2 overlay outcome — Layer 2 only: a decision/edge, never an AUC claim."""
    name: str
    verdict: str
    tau: float
    calib_edge: float
    eval_edge: float
    folds: list = field(default_factory=list)
    placebo_z: float = float("nan")
    inert_reason: str = ""
    n_calib: int = 0
    n_eval: int = 0
    n_selected: int = 0
    tau_table: list = field(default_factory=list)
    baseline: str = ""
    smoke: bool = False
    fold_report: dict = field(default_factory=dict)   # WI-065 mandatory column (empty only if INERT)


def _fmt(x, spec: str = "{:.4f}") -> str:
    return "n/a" if not np.isfinite(float(x)) else spec.format(float(x))


def selected_mask(probs, tau) -> np.ndarray:
    """Overlay decision rule: take an event iff its overlay probability clears tau."""
    p = np.asarray(probs, dtype="float64")
    return np.isfinite(p) & (p >= float(tau))


def feasible(calib_probs, tau_grid=TAU_GRID, min_events=MIN_CALIB_EVENTS):
    """D-024 §2 precheck: >= `min_events` CALIB events AND the tau range spans the mass."""
    p = np.asarray(calib_probs, dtype="float64")
    p = p[np.isfinite(p)]
    lo, hi = float(min(tau_grid)), float(max(tau_grid))
    if p.size < int(min_events):
        return False, f"INERT: CALIB events {p.size} < floor {int(min_events)}"
    if p.max() < lo:
        return False, f"INERT: mass max {p.max():.4f} below tau range [{lo:.2f}, {hi:.2f}] — no operating point"
    if p.min() >= hi:
        return False, f"INERT: mass min {p.min():.4f} at/above tau range [{lo:.2f}, {hi:.2f}]"
    return True, ""


def xsec_inert_precheck(calib_probs, names_per_date, tau_grid=TAU_GRID, min_events=XSEC_MIN_CALIB_EVENTS,
                        min_names=MIN_NAMES_PER_DATE):
    """D-027 §7 INERT precheck for a *ranking* construction: CALIB floor + τ span + min names/date."""
    ok, reason = feasible(calib_probs, tau_grid, min_events)
    if not ok:
        return False, reason.replace("INERT:", "INERT (xsec):")
    counts = np.asarray(names_per_date, dtype="float64")
    counts = counts[np.isfinite(counts)]
    thin = int((counts < float(min_names)).sum())
    if counts.size == 0 or thin:
        return False, f"INERT (xsec): {thin}/{counts.size} dates below the {int(min_names)}-name floor"
    return True, ""


def pick_tau_by_calib_edge(probs, ret, calib_mask, tau_grid=TAU_GRID):
    """Pick tau by **max CALIB edge** (D-024 §2); EVAL arrays are never passed in."""
    sel = np.asarray(calib_mask, dtype=bool)
    p, r = np.asarray(probs, "float64")[sel], np.asarray(ret, "float64")[sel]
    table = [{"tau": float(t), "n_selected": int(selected_mask(p, t).sum()),
              "calib_edge": selection_edge(selected_mask(p, t), r)} for t in tau_grid]
    ok = [row for row in table if row["n_selected"] >= 1 and np.isfinite(row["calib_edge"])]
    best = (min(ok, key=lambda d: (-d["calib_edge"], -d["n_selected"], d["tau"])) if ok
            else dict(table[0], calib_edge=float("nan")))
    return best, table


def score_eval(probs, ret, mask, tau) -> float:
    """One-shot EVAL scoring with the tau frozen on CALIB — called exactly once."""
    m = np.asarray(mask, dtype=bool)
    if not m.any():
        return float("nan")
    return selection_edge(selected_mask(np.asarray(probs)[m], tau), np.asarray(ret, "float64")[m])


def placebo_z(probs, ret, tau, *, seed0: int = PLACEBO_SEED0, n_seeds: int = N_PLACEBO_SEEDS):
    """CB-05 placebo on the edge: permute probabilities, re-apply the frozen tau (no refit)."""
    p, r = np.asarray(probs, "float64"), np.asarray(ret, "float64")
    ok = np.isfinite(p) & np.isfinite(r)
    p, r = p[ok], r[ok]
    observed = selection_edge(selected_mask(p, tau), r)
    null = [selection_edge(selected_mask(np.random.default_rng(seed0 + s).permutation(p), tau), r)
            for s in range(int(n_seeds))]
    arr = np.asarray([v for v in null if np.isfinite(v)], dtype="float64")
    mean = float(arr.mean()) if arr.size else float("nan")
    sd = float(arr.std(ddof=1)) if arr.size > 1 else float("nan")
    return float((observed - mean) / sd) if np.isfinite(sd) and sd > 0.0 else float("nan")


def classify(calib_edge, eval_edge, placebo_z, z_min: float = PLACEBO_Z_MIN) -> str:
    """ADOPT iff CALIB edge > 0 AND EVAL edge >= 0 AND placebo z >= z_min (D-024 §2)."""
    if not np.isfinite(calib_edge) or float(calib_edge) <= 0.0 \
            or not np.isfinite(eval_edge) or float(eval_edge) < 0.0:
        return "REJECT"
    if not np.isfinite(placebo_z) or float(placebo_z) < float(z_min):
        return "INCONCLUSIVE"
    return "ADOPT"


def fold_edges(probs, ret, folds, tau, mask) -> list[dict]:
    """Per-fold baseline / selected mean / edge rows, folds ascending."""
    p, r = np.asarray(probs, "float64"), np.asarray(ret, "float64")
    f, m = np.asarray(folds, dtype="int64"), np.asarray(mask, dtype=bool)
    rows = []
    for k in sorted({int(v) for v in f[m]}):
        sel = m & (f == k)
        base, kept = r[sel], selected_mask(p[sel], tau)
        rows.append({"fold": k, "n_events": int(sel.sum()), "n_selected": int(kept.sum()),
                     "baseline_mean": float(base.mean()) if base.size else float("nan"),
                     "model_mean": float(base[kept].mean()) if kept.any() else float("nan"),
                     "edge": selection_edge(kept, base)})
    return rows


def _unpack(events, baseline, probs, calib_mask, eval_mask):
    """Per-event returns + fold ids + CALIB/EVAL masks; an explicit baseline array wins."""
    n = len(probs)
    if not isinstance(baseline, str) and baseline is not None:
        ret = np.asarray(baseline, dtype="float64")
    else:
        if "ret" not in events and "r_frozen" not in events:
            raise KeyError("events needs 'ret'/'r_frozen' when baseline is a name")
        ret = np.asarray(events["ret" if "ret" in events else "r_frozen"], "float64")
    folds = np.asarray(events["fold"], "int64") if "fold" in events else np.zeros(n, "int64")
    calib = np.full(n, True) if calib_mask is None else np.asarray(calib_mask, bool)
    ev = np.full(n, False) if eval_mask is None else np.asarray(eval_mask, bool)
    if ret.shape[0] != n or calib.shape[0] != n or ev.shape[0] != n:
        raise ValueError(f"returns/masks must be aligned to the {n} events")
    return ret, folds, calib, ev


def run_overlay(name, baseline, probs, events, tau_grid=TAU_GRID, calib_mask=None, eval_mask=None,
                *, seed0: int = PLACEBO_SEED0, n_seeds: int = N_PLACEBO_SEEDS,
                smoke: bool = False) -> OverlayResult:
    """Run one overlay question end-to-end (D-024 §2); `baseline` is a frozen name or returns."""
    p = np.asarray(probs, dtype="float64")
    ret, folds, calib, ev = _unpack(events, baseline, p, calib_mask, eval_mask)
    grid = tuple(float(t) for t in tau_grid)
    base_name = baseline if isinstance(baseline, str) else "explicit"
    ok, reason = feasible(p[calib], grid)
    if not ok:  # D-024 §2: record INERT before any EVAL burn
        return OverlayResult(name, "INERT", float("nan"), float("nan"), float("nan"), [],
                             float("nan"), reason, int(calib.sum()), int(ev.sum()), 0, [], base_name, smoke)
    best, table = pick_tau_by_calib_edge(p, ret, calib, grid)
    tau, calib_edge = float(best["tau"]), float(best["calib_edge"])
    eval_edge = score_eval(p, ret, ev, tau)                 # the one and only EVAL touch
    z = placebo_z(p, ret, tau, seed0=seed0, n_seeds=n_seeds)
    rows = fold_edges(p, ret, folds, tau, calib | ev)
    return OverlayResult(name, classify(calib_edge, eval_edge, z), tau, calib_edge, eval_edge,
                         rows, z, "", int(calib.sum()), int(ev.sum()), int(best["n_selected"]),
                         table, base_name, smoke, build_fold_report(rows))   # fails closed if empty


def synthetic_fixture(question, n_calib: int = 240, n_eval: int = 120, inert: bool = False) -> dict:
    """Deterministic smoke fixture (no `data/` read, no EVAL burn): toy but trained signal."""
    rng = np.random.default_rng(QUESTION_SEEDS.get(question, 99))
    n = int(n_calib) + int(n_eval)
    probs = rng.random(n).astype("float32")
    ret = (np.where(probs >= 0.7, 0.04, -0.01) + rng.normal(0.0, 0.01, n)).astype("float32")
    if inert:  # mass far below the tau grid
        probs = (probs * 0.01).astype("float32")
    return {"events": pd.DataFrame({"ret": ret, "fold": (np.arange(n) % 5).astype("int64")}),
            "probs": probs, "tau_grid": TAU_GRID, "calib_mask": np.arange(n) < int(n_calib),
            "eval_mask": np.arange(n) >= int(n_calib)}


def write_report(result: OverlayResult, path) -> Path:
    """`reports/l2/<name>.md` (or the `--out` dir in a smoke run): D-024 §2 protocol record."""
    tag = "  (smoke / synthetic fixture)" if result.smoke else ""
    rep = result.fold_report or {}
    fold_line = ("- Fold report: missing (INERT — no operating point)" if not rep else
                 f"- Fold report: max-fold share {_fmt(rep['max_fold_share'])} "
                 f"(ceiling {FOLD_CEILING_SHARE:.0%}, {'pass' if rep['fold_ceiling_ok'] else 'FAIL'}); "
                 f"positive folds {rep['n_positive_folds']}/{rep['n_folds']}")
    lines = [f"# L2 overlay — {result.name} (D-024 §2 harness)", "",
             f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
             f"- Verdict: **{result.verdict}**{tag}  |  baseline `{result.baseline}`",
             f"- CALIB events {result.n_calib:,} (selected {result.n_selected:,}); EVAL events "
             f"{result.n_eval:,}; tau frozen on CALIB only: {_fmt(result.tau)}",
             f"- CALIB edge {_fmt(result.calib_edge)}; EVAL edge {_fmt(result.eval_edge)}; "
             f"placebo z {_fmt(result.placebo_z, '{:+.2f}')}",
             fold_line,
             "- Layer separation: no learner refit, no AUC selection, EVAL read once after freeze."]
    if result.inert_reason:
        lines += ["", f"- {result.inert_reason}"]
    lines += ["", "| tau | selected | CALIB edge |", "| ---: | ---: | ---: |", *[
        f"| {r['tau']:.2f} | {r['n_selected']:,} | {_fmt(r['calib_edge'], '{:+.5f}')} |"
        for r in result.tau_table]]
    lines += ["", "| fold | events | selected | edge |", "| ---: | ---: | ---: | ---: |", *[
        f"| {f['fold']} | {f['n_events']:,} | {f['n_selected']:,} | {_fmt(f['edge'], '{:+.5f}')} |"
        for f in result.folds], "", "Record-only: no shortlist, no deployment, no live trading."]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return path


# ---------------------------------------------------- WI-065: union / pre-registration / gates
def _key_columns(frame: pd.DataFrame) -> dict:
    """Resolve every CELL_KEY column, substituting its documented manifest source when absent.

    Real manifests (wi040/wi048) have no `family`/`horizon`: family lives in `binary`, horizon in `h`.
    A key column that is absent *and* has no source present fails loudly rather than keying on NaN.
    """
    out, missing = {}, []
    for col in CELL_KEY:
        src = col if col in frame.columns else CELL_SOURCES.get(col)
        if src in frame.columns:
            out[col] = frame[src]
        else:
            missing.append(f"{col} (source `{CELL_SOURCES.get(col)}`)" if col in CELL_SOURCES else col)
    if missing:
        raise KeyError(f"manifest missing cell-key columns {missing}")
    return out


def _cell_keys(frame: pd.DataFrame) -> pd.Series:
    """D-027 §4 cell key: market/learner/variant/family/horizon/fold — family←`binary`, horizon←`h`.

    Blank key fields (e.g. the 96 NaN wi040 variants) are keyed through the reserved
    `MISSING_KEY_SENTINEL` so they neither crash the join nor collide with real variant strings.
    """
    cols = _key_columns(frame)
    parts = []
    for col in CELL_KEY:
        s = pd.Series(cols[col])
        parts.append(s.astype(object).where(~s.isna(), MISSING_KEY_SENTINEL).astype(str))
    return pd.concat(parts, axis=1).agg("|".join, axis=1)


def assert_no_duplicate_cells(frame: pd.DataFrame) -> pd.Series:
    """A cell key may enter the union exactly once; a repeated key is a defect (D-027 §4)."""
    key = _cell_keys(frame)
    dupes = key[key.duplicated(keep=False)]
    if not dupes.empty:
        raise ValueError(f"cell key entered twice: {sorted(set(dupes))[:3]} (n={int(dupes.size)})")
    return key


def load_union(paths=(WI040_MANIFEST, WI048_MANIFEST)) -> pd.DataFrame:
    """wi040 ∪ wi048 with cell-key dedup + an assertion that no cell enters twice (no silent drops)."""
    paths = tuple(Path(p) for p in paths)
    frames = [pd.read_parquet(p) for p in paths]
    union = pd.concat(frames, ignore_index=True)
    union["cell_key"] = _cell_keys(union)
    raw = int(len(union))
    per = [{"source": p.parent.name, "rows": int(len(f))} for p, f in zip(paths, frames)]
    union = union.drop_duplicates(subset=["cell_key"], keep="first").reset_index(drop=True)
    assert_no_duplicate_cells(union)
    union.attrs["union_report"] = {"n_raw": raw, "n_union": int(len(union)),
                                   "n_dropped": raw - int(len(union)), "per_source": per}
    return union


def preregistration_template() -> dict:
    """D-027 §7/§11 schema: constructions, params, FDR family list, materiality floor, hash field."""
    return {"schema_version": PREREG_VERSION, "family_id": "l2_rebuild",
            "constructions": ["(b) xsec top-k rank screener + hysteresis (LONG-ONLY first pass)",
                              "(a) fixed time exits h13/h55 + hybrid on identical entries",
                              "(c) vol-target entry-only sizing", "(d) within-market sector pairs"],
            "params": {"tau_grid": list(TAU_GRID), "long_only": True,
                       "min_names_per_date": MIN_NAMES_PER_DATE,
                       "xsec_min_calib_events": XSEC_MIN_CALIB_EVENTS,
                       "calib_end": CALIB_END, "eval_start": EVAL_START},
            "fdr_family": [], "fdr_pooled_with_d024": False,
            "materiality_floor_bps": MATERIALITY_FLOOR_BPS, "fold_ceiling_share": FOLD_CEILING_SHARE,
            "eval_lock_released": False, "hash": ""}


def prereg_hash(payload: dict) -> str:
    """sha256 over the canonical (sorted, compact) payload minus its own hash field."""
    body = {k: v for k, v in payload.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_preregistration(payload: dict, path) -> Path:
    """Write the payload with its computed sha256 `hash` field."""
    p = dict(payload)
    p["hash"] = prereg_hash(p)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(p, indent=2, sort_keys=True) + "\n")
    return path


def load_preregistration(path) -> dict:
    """Load a pre-registration file and verify its sha256; a mismatch is a hard failure."""
    payload = json.loads(Path(path).read_text())
    if payload.get("hash") != prereg_hash(payload):
        raise ValueError(f"pre-registration hash mismatch in {path}")
    return payload


class EvalLockError(RuntimeError):
    """Raised on any attempted EVAL read before the pre-registered lock is released."""


def assert_eval_unlocked(prereg) -> None:
    """D-027 §7: EVAL is unread until the pre-registration says the lock is released."""
    if not isinstance(prereg, dict) or not prereg.get("eval_lock_released"):
        raise EvalLockError("EVAL locked: eval_lock_released is false — no EVAL read is permitted")


def eval_read(load, prereg, *args, **kwargs):
    """Guarded EVAL read: raises EvalLockError before `load` is ever called while the lock holds."""
    assert_eval_unlocked(prereg)
    return load(*args, **kwargs)


def calib_stop(calib_net_edge_bps, fold: dict, *, floor_bps: float = MATERIALITY_FLOOR_BPS) -> dict:
    """D-027 §7/§11 CALIB-failure stop flag: below floor OR a fold-ceiling failure kills the card."""
    reasons = []
    if not np.isfinite(float(calib_net_edge_bps)) or float(calib_net_edge_bps) <= float(floor_bps):
        reasons.append(f"CALIB net edge {_fmt(calib_net_edge_bps)} bps <= materiality floor "
                       f"{float(floor_bps):.1f}")
    if not fold.get("fold_ceiling_ok"):
        reasons.append(f"fold ceiling failed (share {_fmt(fold.get('max_fold_share'))}, "
                       f"positive folds {fold.get('n_positive_folds')}/{fold.get('n_folds')})")
    return {"stop": bool(reasons), "reasons": reasons}


def main(argv=None) -> int:
    """CLI: `--smoke` (synthetic, `reports/l2_harness_smoke/`) or a real run (`--prepared ...`)."""
    ap = argparse.ArgumentParser(description="WI-041/065 L2 overlay harness (D-024 §2)")
    ap.add_argument("--question", default=None, help="overlay question name (report id)")
    ap.add_argument("--out", default=None, help="report dir (smoke defaults to reports/l2_harness_smoke)")
    ap.add_argument("--prepared", default=None, help="prepared parquet: p,ret,fold,date")
    ap.add_argument("--baseline", default="frozen_fib_wi035", help="frozen baseline name")
    ap.add_argument("--calib-end", default=CALIB_END)
    ap.add_argument("--eval-start", default=EVAL_START)
    ap.add_argument("--inert", action="store_true", help="smoke only: force thin mass")
    ap.add_argument("--smoke", action="store_true", help="synthetic smoke run (no data/ read)")
    ap.add_argument("--seeds", type=int, default=N_PLACEBO_SEEDS)
    args = ap.parse_args(argv)
    question = args.question or DEFAULT_SMOKE_Q
    smoke = args.smoke or os.environ.get("L2_SMOKE", "").strip() == "1" or args.prepared is None
    if smoke:
        fx = synthetic_fixture(question, inert=args.inert)
        res = run_overlay(question, args.baseline, fx["probs"], fx["events"], fx["tau_grid"],
                          fx["calib_mask"], fx["eval_mask"], n_seeds=args.seeds, smoke=True)
    else:
        prep = pd.read_parquet(args.prepared)
        dates = pd.to_datetime(prep["date"])
        res = run_overlay(question, args.baseline, prep["p"].to_numpy("float64"), prep,
                          TAU_GRID, (dates < args.calib_end).to_numpy(),
                          (dates >= args.eval_start).to_numpy(), n_seeds=args.seeds)
    out_dir = Path(args.out or (DEFAULT_SMOKE_DIR if smoke else REPORTS_DIR))
    report = write_report(res, out_dir / f"{question}.md")
    print(f"[l2.harness] {res.name}: verdict={res.verdict} tau={_fmt(res.tau)} "
          f"calib={_fmt(res.calib_edge)} eval={_fmt(res.eval_edge)} z={_fmt(res.placebo_z, '{:+.2f}')}")
    if smoke:   # mandatory artifacts, written beside the smoke report (never under data/)
        pre = write_preregistration(preregistration_template(), out_dir / PREREG_NAME)
        folds = write_fold_report(dict(res.fold_report), out_dir / "fold_report.json")
        print(f"[l2.harness] artifacts -> {pre.name}, {folds.name} in {out_dir}")
    print(f"[l2.harness] {'smoke' if smoke else 'run'} report -> {report} | EXIT:0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
