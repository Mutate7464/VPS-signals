"""WI-048a — T2 target-family grid driver (`up` / `high_low` / `vol_expand`, D-025).

Thin driver over the WI-035/036 machinery: one family x 6 horizons x 2 learners x
2 markets = 24 cells = ONE BH-FDR family (m=24) per sub-grid. Verdict = pooled OOF
AUC + rank-IC over the 5 purged folds + a 5-seed label-permutation placebo; no tau
grid, no entry rule, no portfolio returns, no EVAL. Variant pinned per market
(`exact_full_k0.8` USD / `tol2_full_k0.8` CAD, WI-048c). Pickles: FDR survivors only.

CLI::

    WI048_SMOKE=5 python -m src.swing_bsh.grid_targets_ext --family up --out /tmp/wi048_smoke
    python -m src.swing_bsh.grid_targets_ext --family up --family-only
    python -m src.swing_bsh.grid_targets_ext --consolidate

Smoke stops at the label-density report (no CV, no pickles, no report/manifest).
Invariants: purged/embargoed CV (`embargo_td=max(20, h)`), CALIB-only selection,
float32, symbol-sequential, `n_jobs=2`, rho prune 0.3.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.swing_bsh import binary_features_ext as ext
from src.swing_bsh import binary_grid, binary_labels, binary_train, learner_ext, library_audit, train
from src.swing_bsh import targets_ext as tg
from src.xgb_trainer import PurgedWalkForwardSplit

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_DIR = BASE_DIR / "data" / "models" / "wi048"
REPORTS_DIR = BASE_DIR / "reports"
SUMMARY_NAME = "t2_targets_ext_summary.md"
FAMILY_REPORT = {"up": "t2_grid_up_summary.md",
                 "high_low": "t2_grid_highlow_summary.md",
                 "vol_expand": "t2_grid_volexpand_summary.md",
                 "vol_expand_fwd": "t2_grid_volexpandfwd_summary.md"}
LEARNERS: tuple[str, ...] = ("xgboost", "lightgbm")
PRUNE_RHO = 0.3
PINNED_K = 0.8
PINNED_VARIANTS: tuple[str, ...] = tuple(ext.variant_name(e, "full", PINNED_K) for e in tg.EVENT_MODES)
"""`exact_full_k0.8` (USD) / `tol2_full_k0.8` (CAD) — the WI-048c variant pinning."""
N_PLACEBO_SEEDS = binary_grid.N_PLACEBO_SEEDS
FDR_ALPHA = binary_grid.FDR_ALPHA
CORE_HOUR_CAP = 2.0
PLACEBO_RESERVE = binary_grid.PLACEBO_RESERVE
DEFAULT_CACHE_DIR, DEFAULT_SMOKE_DIR = "/tmp/wi048", tg.DEFAULT_SMOKE_DIR

__all__ = ["CORE_HOUR_CAP", "FAMILY_REPORT", "LEARNERS", "MODEL_DIR", "PINNED_VARIANTS",
           "SUMMARY_NAME", "apply_fdr", "build_family_report", "consolidate", "load_panel",
           "main", "rank_cells", "run_market", "run_placebo", "save_survivors",
           "write_manifest"]


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fmt(x, spec: str = "{:.4f}") -> str:
    v = float(x)
    return "n/a" if not np.isfinite(v) else spec.format(v)


def _blob_key(key) -> str:
    return "|".join(str(x) for x in key)


def _cache_paths(cache_dir, market: str) -> tuple[Path, Path]:
    d = Path(cache_dir)
    return d / f"wi048_panel_{market}.parquet", d / f"wi048_labels_{market}.npz"


def _design(panel: pd.DataFrame):
    """float32 design matrix over the rho-pruned candidate features (WI-036 recipe)."""
    kept, dropped = binary_labels.kept_features(panel, threshold=PRUNE_RHO,
                                                features=ext.candidate_features(panel))
    kept = binary_labels.feature_names(kept)
    panel = train.engineer(panel)
    panel["k"] = np.float32(1.0)
    panel["horizon"] = np.float32(21.0)
    X, feats = train.feature_matrix(panel, kept)
    return X, feats, kept, dropped


def load_panel(market: str, *, cache_dir=None, limit: int | None = None,
               allow_fixture: bool = False):
    """`(panel, labels)` for one market — cache first, else `targets_ext` (float32)."""
    if cache_dir is not None and limit is None:
        pp, lp = _cache_paths(cache_dir, market)
        if pp.exists() and lp.exists():
            blob = np.load(lp)
            keys = [tg.label_key(f, e, h) for f in tg.FAMILIES
                    for e in tg.EVENT_MODES for h in tg.HORIZONS]
            return pd.read_parquet(pp), {k: blob[_blob_key(k)] for k in keys}
    panel, labels = tg.build_targets_panel(market, allow_fixture=allow_fixture, max_symbols=limit)
    if cache_dir is not None and limit is None and not panel.empty:
        pp, lp = _cache_paths(cache_dir, market)
        pp.parent.mkdir(parents=True, exist_ok=True)
        panel.to_parquet(pp, index=False)
        np.savez_compressed(lp, **{_blob_key(k): v for k, v in labels.items()})
    return panel, labels


# --------------------------------------------------------------------------- #
# Market driver
# --------------------------------------------------------------------------- #
def run_market(family: str, market: str, cfg: dict, *, cache_dir=None, limit=None,
               allow_fixture=False, budget=None, grid_seconds=None,
               learners=LEARNERS) -> dict:
    """Score one family x one market (6 horizons x learners), budget-gated."""
    budget = budget or binary_grid.CoreBudget(CORE_HOUR_CAP)
    panel, labels = load_panel(market, cache_dir=cache_dir, limit=limit,
                               allow_fixture=allow_fixture)
    if panel.empty:
        raise RuntimeError(f"no swing events for market={market}")
    X, feats, kept, dropped = _design(panel)
    dates = panel["date"].to_numpy()
    params = binary_train.learner_params(cfg)
    event = tg.PINNED_EVENT[market]
    variant = ext.variant_name(event, "full", PINNED_K)
    splitters = {h: PurgedWalkForwardSplit(n_splits=binary_grid.N_SPLITS,
                                           embargo_td=train.embargo_for([h]))
                 for h in tg.HORIZONS}
    cells: list[dict] = []
    skipped: list[str] = []
    t_grid = budget.spent()
    if grid_seconds is None:
        grid_seconds = max(0.0, budget.left() * (1.0 - PLACEBO_RESERVE))
    for h in tg.HORIZONS:
        y = labels[tg.label_key(family, event, h)]
        for learner in learners:
            tag = f"{market}_{learner}_{variant}_{family}_h{h}"
            if budget.spent() - t_grid > grid_seconds:
                skipped.append(tag)
                continue
            cv = binary_grid.cell_cv(X, y, dates, learner, params[learner], splitters[h], None, tag)
            auc, ic, folds = binary_grid.auc_ic(y, cv["oof"], cv["fold_id"])
            cells.append({"market": market, "family": family, "variant": variant, "event": event,
                          "window": "full", "k": PINNED_K, "h": int(h), "binary": family,
                          "learner": learner, "tag": tag, "auc": auc, "ic": ic,
                          "fold_auc": folds, "n_oof": int(np.isfinite(cv["oof"]).sum()),
                          "n_pos": int(np.asarray(y).sum()), "z": float("nan"),
                          "p": float("nan"), "models": cv["models"]})
    return {"market": market, "family": family, "variant": variant, "n_rows": int(len(panel)),
            "n_symbols": int(panel["symbol"].nunique()), "features": feats,
            "n_features_pruned": len(kept), "n_features_input": len(kept) + len(dropped),
            "cells": cells, "skipped": skipped, "core_sec": round(budget.spent(), 1),
            "X": X, "labels": labels, "params": params, "dates": dates, "splitters": splitters}


def run_placebo(results: list[dict], budget, seeds: int = N_PLACEBO_SEEDS) -> int:
    """5-seed AUC permutation placebo, most extreme cells first, budget-gated."""
    cells = [(r, c) for r in results for c in r["cells"] if np.isfinite(c["auc"])]
    done = 0
    for r, c in sorted(cells, key=lambda rc: -abs(rc[1]["auc"] - 0.5)):
        if budget.left() < binary_grid.PLACEBO_MIN_LEFT:
            break
        pl = binary_grid.placebo_auc(
            r["X"], r["labels"][tg.label_key(c["family"], c["event"], c["h"])], r["dates"],
            c["learner"], r["params"][c["learner"]], r["splitters"][c["h"]], c["auc"],
            n_seeds=seeds)
        c["z"], c["p"], c["placebo"] = pl["z"], pl["p"], pl
        done += 1
    return done


def apply_fdr(results: list[dict], m_total: int) -> int:
    """BH-FDR over the sub-grid (`m_total` = the full family size, not the scored cells)."""
    cells = [c for r in results for c in r["cells"]]
    surv, _thr = binary_grid.bh_fdr([c["p"] for c in cells], alpha=FDR_ALPHA, m_total=m_total)
    for c, s in zip(cells, surv):
        c["fdr"] = bool(s)
    return int(surv.sum())


def _cell_id(c: dict) -> str:
    return (f"{c['market']}|{c['learner']}|{c['variant']}|{c['binary']}|h{int(c['h'])}")


def save_survivors(results: list[dict], model_dir) -> int:
    """Pickle the fold models of the FDR survivors only (`<tag>_f<fold>.pkl`)."""
    n = 0
    for r in results:
        for c in r["cells"]:
            if not c.get("fdr"):
                continue
            for fold, model in (c.get("models") or {}).items():
                binary_grid._pickle(model, model_dir, c["tag"], fold)
                n += 1
    return n


def write_manifest(cells: list[dict], model_dir) -> Path:
    """`data/models/wi048/manifest.parquet` — WI-040 row schema, survivors only."""
    rows = []
    for c in cells:
        if not c.get("fdr"):
            continue
        for fold in range(binary_grid.N_SPLITS):
            p = Path(model_dir) / f"{c['tag']}_f{fold}.pkl"
            if not p.exists():
                continue
            rows.append({"manifest_id": f"wi048:{p.stem}", "library": "wi048",
                         "pickle_path": str(p.relative_to(BASE_DIR)), "market": c["market"],
                         "learner": c["learner"], "variant": c["variant"], "event": c["event"],
                         "window": c["window"], "k": float(c["k"]), "h": int(c["h"]),
                         "binary": c["binary"], "fold": int(fold), "cell_id": _cell_id(c),
                         "auc": float(c["auc"]), "ic": float(c["ic"])})
    out = Path(model_dir) / "manifest.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=library_audit.MANIFEST_COLS).to_parquet(out, index=False)
    return out


def dump_cells(family: str, results: list[dict], model_dir) -> Path:
    """Per-family cell sidecar (`<family>_cells.json`) — input to `--consolidate`."""
    payload = {"family": family, "generated_utc": _now(),
               "core_sec": max((r["core_sec"] for r in results), default=0.0),
               "skipped": [s for r in results for s in r["skipped"]],
               "cells": [{k: v for k, v in c.items() if k != "models"}
                         for r in results for c in r["cells"]]}
    path = Path(model_dir) / f"{family}_cells.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1, default=str))
    return path


# --------------------------------------------------------------------------- #
# Ranking / reports
# --------------------------------------------------------------------------- #
def rank_cells(cells: list[dict]) -> pd.DataFrame:
    """Cross-market-consistent ranking of `(family, learner, h)` cells (min AUC)."""
    df = pd.DataFrame([{k: v for k, v in c.items() if k not in ("models", "placebo")}
                       for c in cells if np.isfinite(c["auc"])])
    if df.empty:
        return df
    keys = ["family", "learner", "h"]
    usd = df[df["market"] == "USD"].set_index(keys)[["auc", "ic"]]
    cad = df[df["market"] == "CAD"].set_index(keys)[["auc", "ic"]]
    pair = usd.join(cad, lsuffix="_usd", rsuffix="_cad", how="inner").reset_index()
    if pair.empty:
        return pair
    pair["auc_min"] = pair[["auc_usd", "auc_cad"]].min(axis=1)
    pair["ic_min"] = pair[["ic_usd", "ic_cad"]].min(axis=1)
    return pair.sort_values("auc_min", ascending=False).reset_index(drop=True)


def _fdr_table(cells: list[dict]) -> list[str]:
    lines = ["| market | family | learner | h | AUC | z | p |",
             "| :--- | :--- | :--- | ---: | ---: | ---: | ---: |"]
    surv = [c for c in cells if c.get("fdr")]
    if not surv:
        lines.append("| — | no cell survived BH-FDR | | | | | |")
    for c in sorted(surv, key=lambda c: -c["auc"]):
        lines.append(f"| {c['market']} | `{c['family']}` | {c['learner']} | {int(c['h'])} | "
                     f"{_fmt(c['auc'])} | {_fmt(c['z'], '{:+.2f}')} | {_fmt(c['p'], '{:.2e}')} |")
    return lines


def _provenance(cells: list[dict], learners=LEARNERS) -> list[str]:
    return [f"- Learners: {', '.join(learners)}; variant pinned per market "
            f"{tg.PINNED_EVENT} (`*_full_k{PINNED_K:.1f}`); rho prune {PRUNE_RHO}",
            f"- CV: {binary_grid.N_SPLITS}-fold `PurgedWalkForwardSplit(embargo_td=max(20, h))`; "
            f"placebo {N_PLACEBO_SEEDS}-seed label permutation on the AUC; BH-FDR alpha={FDR_ALPHA} "
            f"over m={len(tg.HORIZONS) * len(tuple(learners)) * 2} per family (design multiplicity)",
            f"- Features read at the detection bar only; float32, symbol-sequential, "
            f"`n_jobs={binary_train.N_JOBS}`; core cap {CORE_HOUR_CAP} h",
            f"- Pickles (survivors only): `data/models/wi048/<MKT>_<learner>_<variant>_<family>_"
            f"h<h>_f<fold>.pkl`; manifest `data/models/wi048/manifest.parquet` (WI-040 schema)"]


def build_family_report(family: str, results: list[dict], path: Path,
                        learners=LEARNERS) -> Path:
    """`t2_grid_<family>_summary.md` — cell ranking, FDR survivors, truncation."""
    cells = [c for r in results for c in r["cells"]]
    skipped = [s for r in results for s in r["skipped"]]
    pair = rank_cells(cells)
    cov = ", ".join(f"{r['market']} {r['core_sec']}s" for r in results)
    lines = [f"# WI-048 — T2 grid `{family}` (D-025 tier 2)", "",
             f"- Generated (UTC): {_now()}",
             f"- Grid: `{family}` x {len(tg.HORIZONS)} horizons "
             f"({', '.join(str(h) for h in tg.HORIZONS)}) x {len(tuple(learners))} learners x "
             f"{len(results)} markets; verdict = pooled OOF AUC + rank-IC (no tau grid, no EVAL)",
             *_provenance(cells, learners),
             f"- Coverage: {len(cells)} cells scored, {len(skipped)} truncated by the core budget "
             f"({cov})",
             "", "## 1. Cell ranking — cross-market consistent AUC / rank-IC", "",
             "| rank | learner | h | AUC USD | AUC CAD | min AUC | min IC |",
             "| ---: | :--- | ---: | ---: | ---: | ---: | ---: |"]
    for i, row in pair.iterrows():
        lines.append(f"| {i + 1} | {row['learner']} | {int(row['h'])} | {_fmt(row['auc_usd'])} | "
                     f"{_fmt(row['auc_cad'])} | **{_fmt(row['auc_min'])}** | "
                     f"{_fmt(row['ic_min'], '{:+.4f}')} |")
    if pair.empty:
        lines.append("| — | no cross-market cell pairs completed | | | | | |")
    lines += ["", f"## 2. FDR survivors (BH alpha=0.05, "
                  f"m={len(tg.HORIZONS) * len(tuple(learners)) * len(results)})",
              "", *_fdr_table(cells), "",
              "## Notes / deviations", "",
              "- Pure-signal run: nothing is selected, no portfolio returns, no costs.",
              "- Label definitions live in `src/swing_bsh/targets_ext.py` (one module docstring "
              "per family); the density probe `reports/t2_label_density_probe.md` is the smoke gate.",
              "- Verdict PROVISIONAL until the admin ratifies it in chat.", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return path


def _load_cells(model_dir) -> list[dict]:
    cells: list[dict] = []
    for family in tg.FAMILIES:
        p = Path(model_dir) / f"{family}_cells.json"
        if p.exists():
            cells += json.loads(p.read_text()).get("cells", [])
    return cells


def consolidate(*, model_dir=MODEL_DIR, out_dir=REPORTS_DIR, cache_dir=DEFAULT_CACHE_DIR,
                allow_fixture: bool = False) -> Path:
    """`t2_targets_ext_summary.md` — cross-family ranking, FDR view, winner attribution."""
    cells = _load_cells(model_dir)
    pair = rank_cells(cells)
    learners = tuple(sorted({str(c["learner"]) for c in cells})) or LEARNERS
    lines = ["# WI-048 — T2 cross-family summary (D-025 tier 2, PROVISIONAL)", "",
             f"- Generated (UTC): {_now()}",
             f"- Families: {', '.join(tg.FAMILIES)}; {len(cells)} cells joined from the per-family "
             "sidecars; no new training except the winner-cell attribution refit",
             *_provenance(cells, learners), "",
             "## 1. Target ranking — family x best cell (cross-market min AUC)", "",
             "| rank | family | best cell | AUC USD | AUC CAD | min AUC | min IC | cells |",
             "| ---: | :--- | :--- | ---: | ---: | ---: | ---: | ---: |"]
    rows = []
    for family, g in (pair.groupby("family") if "family" in pair.columns else []):
        b = g.iloc[0]
        rows.append((float(b["auc_min"]), {"family": family, "learner": b["learner"],
                                           "h": int(b["h"]), "auc_usd": b["auc_usd"],
                                           "auc_cad": b["auc_cad"], "auc_min": b["auc_min"],
                                           "ic_min": b["ic_min"], "n": int(len(g))}))
    for i, (_v, r) in enumerate(sorted(rows, key=lambda t: -t[0])):
        lines.append(f"| {i + 1} | `{r['family']}` | {r['learner']}/h{r['h']} | "
                     f"{_fmt(r['auc_usd'])} | {_fmt(r['auc_cad'])} | **{_fmt(r['auc_min'])}** | "
                     f"{_fmt(r['ic_min'], '{:+.4f}')} | {r['n']} |")
    if not rows:
        note = "no cross-market cell pairs on disk" if cells else "no family cells on disk"
        lines.append(f"| — | {note} | | | | | | |")
    lines += ["", f"## 2. FDR survivors (BH alpha=0.05, "
                  f"m={len(tg.HORIZONS) * len(learners) * 2} per family)", "", *_fdr_table(cells),
              "", "## 3. Feature attribution — winning cell", ""]
    attrs = _winner_attribution(pair, model_dir=model_dir, cache_dir=cache_dir,
                                allow_fixture=allow_fixture)
    if attrs:
        lines += [f"Winning cell `{attrs['cell_id']}` (min AUC {_fmt(attrs['auc_min'])}).", "",
                  "- Top TreeSHAP (xgboost, full-panel refit): "
                  + ", ".join(f"`{k}` {v:.3f}" for k, v in attrs["treeshap"].items()),
                  "- Top |linear coefficient| (logistic_l2): "
                  + ", ".join(f"`{k}` {v:+.3f}" for k, v in attrs["linear"])]
    else:
        lines.append("No cross-market winner available for attribution.")
    lines += ["", "## Notes / deviations", "",
              "- Ranking uses the cross-market minimum AUC per `(family, learner, h)` cell; the "
              "library stays Layer-1 (predictive only, D-023).",
              "- Verdict PROVISIONAL — computed labels are advisory until the admin ratifies them.",
              ""]
    path = Path(out_dir) / SUMMARY_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    write_manifest(cells, model_dir)
    return path


def _winner_attribution(pair: pd.DataFrame, *, model_dir, cache_dir, allow_fixture: bool) -> dict:
    """TreeSHAP + linear attribution for the cross-market winner (one panel refit)."""
    if pair.empty:
        return {}
    w = pair.iloc[0]
    market = "USD" if float(w["auc_usd"]) <= float(w["auc_cad"]) else "CAD"
    panel, labels = load_panel(market, cache_dir=cache_dir, allow_fixture=allow_fixture)
    if panel.empty:
        return {}
    X, feats, _kept, _dropped = _design(panel)
    cell = {"variant": ext.variant_name(tg.PINNED_EVENT[market], "full", PINNED_K),
            "h": int(w["h"]), "binary": w["family"]}
    shim = {"X": X, "features": feats, "params": binary_train.learner_params(train.load_settings()),
            "labels": {(cell["variant"], cell["h"]):
                       {w["family"]: labels[tg.label_key(w["family"], tg.PINNED_EVENT[market],
                                                         int(w["h"]))]}}}
    out = binary_grid.attribution(shim, cell)
    return {**out, "cell_id": f"{market}|{w['learner']}|{w['family']}|h{int(w['h'])}",
            "auc_min": float(w["auc_min"])}


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="WI-048 T2 target-family grid (D-025 tier 2)")
    parser.add_argument("--family", default=None, choices=list(tg.FAMILIES))
    parser.add_argument("--family-only", action="store_true", help="Score only --family.")
    parser.add_argument("--consolidate", action="store_true", help="Cross-family summary only.")
    parser.add_argument("--market", default="ALL", help="USD | CAD | ALL (default ALL)")
    parser.add_argument("--limit", type=int, default=None, help="Max symbols per market (smoke).")
    parser.add_argument("--out", default=None, help="Output dir (smoke runs use /tmp).")
    parser.add_argument("--model-dir", default=None)
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR)
    parser.add_argument("--allow-fixture", action="store_true")
    parser.add_argument("--core-hours", type=float, default=CORE_HOUR_CAP)
    parser.add_argument("--placebo-seeds", type=int, default=N_PLACEBO_SEEDS)
    parser.add_argument("--learners", default=",".join(LEARNERS))
    args = parser.parse_args(argv)

    smoke = os.environ.get("WI048_SMOKE", "").strip()
    if args.limit is None and smoke.isdigit():
        args.limit = int(smoke)
    if args.out is None and smoke:
        args.out = DEFAULT_SMOKE_DIR
    model_dir = Path(args.model_dir) if args.model_dir else MODEL_DIR
    out_dir = Path(args.out) if args.out else REPORTS_DIR

    from src.market_cli import cli_markets
    markets = cli_markets(args.market, prog="wi048.grid_targets_ext")
    if markets is None:
        return 2

    if smoke:
        table = tg.probe_table(markets, max_symbols=args.limit, allow_fixture=args.allow_fixture)
        report = tg.build_probe_report(table, out_dir / tg.PROBE_NAME)
        print(f"[wi048.grid] smoke: label density -> {report} | markets={','.join(markets)} "
              f"| cells={len(table)}")
        print("[wi048.grid] EXIT:0 (smoke: no cells scored)")
        return 0

    if args.consolidate:
        path = consolidate(model_dir=model_dir, out_dir=out_dir, cache_dir=Path(args.cache_dir),
                           allow_fixture=args.allow_fixture)
        print(f"[wi048.grid] consolidate -> {path} | manifest -> {Path(model_dir) / 'manifest.parquet'}")
        print("[wi048.grid] EXIT:0")
        return 0

    if args.family:
        families = (args.family,)
    elif args.family_only:
        print("[wi048.grid] --family-only requires --family")
        return 2
    else:
        families = tg.FAMILIES
    learners = tuple(s.strip() for s in args.learners.split(",") if s.strip())
    cfg = train.load_settings()
    budget = binary_grid.CoreBudget(args.core_hours)
    t0 = time.time()
    grid_share = max(0.0, budget.cap * (1.0 - PLACEBO_RESERVE)) / max(len(markets), 1)
    # The lightgbm registry + the pinned-variant narrowing come from WI-044 (imported, never
    # rewritten): inside the mode `binary_train.learner_params`/`_fit_learner` know lightgbm.
    with learner_ext.learner_extension_mode(variants=PINNED_VARIANTS, horizons=tg.HORIZONS,
                                            binary="b_hold"):
        for family in families:
            results = [run_market(family, m, cfg, cache_dir=Path(args.cache_dir), limit=args.limit,
                                  allow_fixture=args.allow_fixture, budget=budget,
                                  grid_seconds=grid_share, learners=learners)
                       for m in markets]
            n_pl = run_placebo(results, budget, seeds=args.placebo_seeds)
            m_total = len(tg.HORIZONS) * len(learners) * len(markets)
            n_surv = apply_fdr(results, m_total=m_total)
            n_pk = save_survivors(results, model_dir)
            cells = [c for r in results for c in r["cells"]]
            write_manifest(cells, model_dir)
            dump_cells(family, results, model_dir)
            report = build_family_report(family, results, out_dir / FAMILY_REPORT[family],
                                         learners=learners)
            print(f"[wi048.grid] {family}: cells={len(cells)} "
                  f"truncated={sum(len(r['skipped']) for r in results)} placebo={n_pl} "
                  f"survivors={n_surv} pickles={n_pk} core={round(budget.spent(), 1)}s -> {report}")
    print(f"[wi048.grid] EXIT:0 | total {round(time.time() - t0, 1)}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
