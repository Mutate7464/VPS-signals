"""WI-038 — long-horizon gap fill (h >= 34 cells truncated in WI-036).

Thin driver over :mod:`src.swing_bsh.binary_grid` (**imported, never
re-implemented**): ``HORIZONS`` is overridden in place to ``LONG_HORIZONS`` =
(34, 55, 89, 144, 233), so the WI-036 CV loop, splitter ladder (embargo =
``max(20, h)``) and 5-seed AUC placebo are the *same* code paths. BH-FDR is over
**this** grid alone (m = the full grid, never pooled with WI-036); fold models go
to ``data/models/wi038/``. Long horizons starve late folds by design: the report
carries per-fold counts and FLAGS starved folds instead of silently pooling.

CLI: ``WI038_SMOKE=5 python -m src.swing_bsh.binary_grid_longh --out
/tmp/wi038_smoke`` · ``python -m src.swing_bsh.binary_grid_longh --market ALL``.
Core cap 2.0 h (h=233 dropped first, then 144, recorded); a dry run never scores
the one-shot EVAL window (date >= 2022-07-01) and never writes the real report.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import time
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd

from src.swing_bsh import binary_features_ext as ext
from src.swing_bsh import binary_grid, train
from src.xgb_trainer import PurgedWalkForwardSplit

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "reports"
MODEL_DIR = BASE_DIR / "data" / "models" / "wi038"
REPORT_NAME = "wi038_summary.md"
DEFAULT_SMOKE_DIR = "/tmp/wi038_smoke"
DEFAULT_CACHE_DIR = "/tmp/wi036"  # shared panel/label cache (horizon subset loaded)
LONG_HORIZONS: tuple[int, ...] = (34, 55, 89, 144, 233)
CORE_HOUR_CAP = 2.0
EVAL_START = "2022-07-01"
STARVED_MIN_EVENTS = 30
FOLD_COUNTS: dict[str, dict[int, int]] = {}

__all__ = ["CORE_HOUR_CAP", "LONG_HORIZONS", "MODEL_DIR", "REPORT_NAME", "build_report", "embargo_for", "fold_table", "horizon_splitter", "main", "run_high_h", "resolve_out_dir"]


def embargo_for(h: int) -> int:
    """`max(20, h)` via the shared WI-033 floor (never re-derived in this driver)."""
    return train.embargo_for([h])


def horizon_splitter(h: int, n_splits: int = binary_grid.N_SPLITS) -> PurgedWalkForwardSplit:
    """The WI-036 purged walk-forward splitter for one horizon."""
    return PurgedWalkForwardSplit(n_splits=n_splits, embargo_td=embargo_for(h))


def _counting_cell_cv(orig):
    def _wrapped(*args, **kwargs):
        cv = orig(*args, **kwargs)
        tag = kwargs.get("tag") or (args[7] if len(args) > 7 else "cell")
        fid = np.asarray(cv["fold_id"])
        FOLD_COUNTS[tag] = {int(f): int((fid == f).sum()) for f in np.unique(fid[fid >= 0])}
        return cv
    _wrapped._wi038_wrapped = True
    return _wrapped


def _eval_guarded(orig, cutoff):
    def _wrapped(market, *, cache_dir, limit, allow_fixture):
        panel, labels = orig(market, cache_dir=cache_dir, limit=limit, allow_fixture=allow_fixture)
        if panel is None or panel.empty:
            return panel, labels
        mask = panel["date"].to_numpy() < np.datetime64(cutoff)
        return (panel.loc[mask].reset_index(drop=True),
                {k: {b: v[b][mask] for b in v} for k, v in labels.items()})
    _wrapped._wi038_guarded = True
    return _wrapped


@contextmanager
def high_horizon_mode(horizons=LONG_HORIZONS, dry_run: bool = False, eval_start: str = EVAL_START):
    """Override `ext.HORIZONS`, wrap `cell_cv` for counts, optionally guard EVAL — then restore."""
    orig_h, orig_cv, orig_pl = ext.HORIZONS, binary_grid.cell_cv, binary_grid._panel_and_labels
    ext.HORIZONS = tuple(horizons)
    if not getattr(binary_grid.cell_cv, "_wi038_wrapped", False):
        binary_grid.cell_cv = _counting_cell_cv(orig_cv)
    if dry_run and not getattr(binary_grid._panel_and_labels, "_wi038_guarded", False):
        binary_grid._panel_and_labels = _eval_guarded(orig_pl, eval_start)
    try:
        yield
    finally:
        ext.HORIZONS, binary_grid.cell_cv, binary_grid._panel_and_labels = orig_h, orig_cv, orig_pl
        FOLD_COUNTS.clear()


def run_high_h(cfg, markets, *, learners, horizons, out_dir, model_dir, limit, allow_fixture,
               cache_dir, core_hours, placebo_seeds, dry_run) -> dict:
    """Score the high-horizon cells per market, placebo-gate, rank, BH-FDR (this grid only)."""
    budget = binary_grid.CoreBudget(core_hours)
    grid_share = max(0.0, budget.cap * (1.0 - binary_grid.PLACEBO_RESERVE)) / max(len(markets), 1)
    results = [binary_grid.run_market(m, cfg, out_dir=out_dir, model_dir=model_dir, limit=limit,
                                      allow_fixture=allow_fixture,
                                      cache_dir=Path(cache_dir) if cache_dir else None,
                                      budget=budget, grid_seconds=grid_share,
                                      placebo_seeds=placebo_seeds, learners=learners)
               for m in markets]
    n_placebo = binary_grid.run_placebo(results, budget, seeds=placebo_seeds)
    cells = [c for r in results for c in r["cells"]]
    ranking = binary_grid.rank_variants(cells)
    m_total = (len(ext.variant_grid()) * len(horizons) * len(ext.BINARY_COLUMNS)
               * len(learners) * len(markets))
    surv, _thr = binary_grid.bh_fdr([c["p"] for c in cells], alpha=binary_grid.FDR_ALPHA,
                                    m_total=m_total)
    for c, s in zip(cells, surv):
        c["fdr"] = bool(s)
    return {"results": results, "cells": cells, "ranking": ranking,
            "survivors": pd.DataFrame([c for c in cells if c.get("fdr")]),
            "n_placebo": n_placebo, "m_total": m_total, "dry_run": bool(dry_run),
            "horizons": tuple(int(h) for h in horizons), "learners": tuple(learners),
            "core_hours": float(core_hours), "core_sec": round(budget.spent(), 1)}


def fold_table(cells: list[dict]) -> dict[tuple[str, int], dict[int, int]]:
    """Per (market, h) fold -> scored-event counts (identical for every cell at that (market, h))."""
    seen: dict[tuple[str, int], dict[int, int]] = {}
    for c in cells:
        seen.setdefault((c["market"], int(c["h"])), dict(FOLD_COUNTS.get(c["tag"], {})))
    return seen


def _dropped_horizons(tags: list[str]) -> list[int]:
    return sorted({int(t.rsplit("_h", 1)[-1]) for t in tags if t.rsplit("_h", 1)[-1].isdigit()})


def build_report(out: dict, path: Path) -> Path:
    """`wi038_summary.md` — target ranking, FDR survivors, per-fold counts with starvation flags."""
    res, ranking, survivors, cells = out["results"], out["ranking"], out["survivors"], out["cells"]
    skipped_tags = [t for r in res for t in r["skipped"]]
    dropped = _dropped_horizons(skipped_tags)
    cov = ", ".join(f"{r['market']} {r['core_sec']}s" for r in res)
    L = ["# WI-038 — long-horizon gap fill (h >= 34 cells truncated in WI-036)", "",
         f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
         f"- Grid: {len(ext.variant_grid())} families x {len(out['horizons'])} horizons ({', '.join(map(str, out['horizons']))}) x {len(ext.BINARY_COLUMNS)} binaries x {len(out['learners'])} learners x {len(res)} markets; WI-036 machinery imported unchanged (`HORIZONS` overridden in place, nothing else)",
         f"- CV: {binary_grid.N_SPLITS}-fold `PurgedWalkForwardSplit(embargo_td=max(20, h))`; placebo {binary_grid.N_PLACEBO_SEEDS}-seed label permutation on the AUC; BH-FDR alpha={binary_grid.FDR_ALPHA} over THIS grid only (m={out['m_total']}, not pooled with WI-036); core cap {out['core_hours']} h; `n_jobs=2`, float32, symbol-sequential",
         f"- Coverage: {len(cells)} cells scored, {len(skipped_tags)} truncated by the core budget ({cov}); {out['n_placebo']} cells carry a 5-seed permutation p-value",
         "- Pickles: `data/models/wi038/<MKT>_<learner>_<variant>_<binary>_h<h>_f<fold>.pkl`"]
    if out["dry_run"]:
        L.append(f"- **Smoke/dry run**: one-shot EVAL window (date >= {EVAL_START}) NOT scored, no wi038 pickles written, the real report NOT written.")
    F = binary_grid._fmt
    L += ["", "## 1. Target ranking — cross-market consistent AUC / rank-IC", "",
          "| rank | variant | best cell (learner/binary/h) | AUC USD | AUC CAD | min AUC | min IC | median min AUC | cells |",
          "| ---: | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for i, row in ranking.iterrows():
        L.append(f"| {i + 1} | `{row['variant']}` | {row['learner']}/{row['binary']}/h{int(row['h'])} | {F(row['auc_usd'])} | {F(row['auc_cad'])} | **{F(row['auc_min'])}** | {F(row['ic_min'], '{:+.4f}')} | {F(row['auc_min_median'])} | {int(row['n_cells'])} |")
    if ranking.empty:
        L.append("| — | no cross-market cell pairs completed | | | | | | | |")
    else:
        w = ranking.iloc[0]
        ver = "**consistent**." if "hold" in str(w["binary"]) else "**not** the expected b_hold family."
        L += ["", f"Verdict: winning family `{w['variant']}` (best cell {w['best']}, min AUC {F(w['auc_min'])}); expected the b_hold family again, weaker at long horizons — {ver}"]
    L += ["", "## 2. FDR survivors (BH alpha=0.05, m over this grid)", "",
          "| market | variant | learner | binary | h | AUC | z | p |",
          "| :--- | :--- | :--- | :--- | ---: | ---: | ---: | ---: |"]
    if survivors.empty:
        L.append("| — | no cell survived BH-FDR | | | | | | |")
    for _, s in survivors.iterrows():
        L.append(f"| {s['market']} | `{s['variant']}` | {s['learner']} | {s['binary']} | {int(s['h'])} | {F(s['auc'])} | {F(s['z'], '{:+.2f}')} | {F(s['p'], '{:.2e}')} |")
    L += ["", "## 3. Per-fold event counts — data-starvation flags", "",
          f"Folds with fewer than {STARVED_MIN_EVENTS} scored events are **FLAGGED** (starved); late folds starve by design at long horizons — counts are never pooled across folds.", "",
          "| market | h | fold 0 | fold 1 | fold 2 | fold 3 | fold 4 | starved folds |",
          "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |"]
    table = fold_table(cells)
    for (market, h), counts in sorted(table.items()):
        row = [counts.get(i, 0) for i in range(binary_grid.N_SPLITS)]
        starved = [f"f{i}({c})" for i, c in enumerate(row) if c < STARVED_MIN_EVENTS]
        L.append(f"| {market} | {h} | " + " | ".join(map(str, row)) + " | " + (", ".join(starved) if starved else "none") + " |")
    if not table:
        L.append("| — | no folds scored | | | | | | |")
    dropped_note = f" — horizons {dropped} (h=233 dropped first, then 144)" if dropped else " — none (budget not tight)"
    L += ["", "## 4. Budget / dropped horizons", "",
          f"- Horizons scored (priority order, ascending): {', '.join(map(str, out['horizons']))}",
          f"- Truncated by the {out['core_hours']} h core budget: {len(skipped_tags)} cells{dropped_note}",
          "", "## Notes / deviations", "",
          "- Thin driver: `run_market`/`run_placebo`/`rank_variants`/`bh_fdr` imported and called unchanged; only `ext.HORIZONS` is overridden (restored on exit).",
          "- Pure-signal run: pooled OOF AUC + rank-IC, no tau grid, no entry rule, no returns.",
          "- Targets: `exact` = detected bar; `tol2` = extreme within +/-2 bars; `full` = [t+1, t+h]; `mid60` = [t+ceil(.2h), t+floor(.8h)]; features always read at the detection bar.", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L) + "\n")
    return path


def resolve_out_dir(out, *, dry_run: bool, reports_dir=REPORTS_DIR, smoke_dir=DEFAULT_SMOKE_DIR) -> Path:
    """A dry run never writes the real report under `reports/`."""
    if out is None:
        return Path(smoke_dir) if dry_run else Path(reports_dir)
    out = Path(out)
    if dry_run and out.resolve() == Path(reports_dir).resolve():
        raise ValueError(f"a dry run may not write the real report ({out})")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="WI-038 long-horizon gap fill")
    parser.add_argument("--market", default="ALL", help="USD | CAD | ALL (default ALL)")
    parser.add_argument("--limit", type=int, default=None, help="Max symbols per market (smoke).")
    parser.add_argument("--out", default=None, help="Output dir (smoke runs use /tmp).")
    parser.add_argument("--allow-fixture", action="store_true")
    parser.add_argument("--placebo-seeds", type=int, default=binary_grid.N_PLACEBO_SEEDS)
    parser.add_argument("--core-hours", type=float, default=CORE_HOUR_CAP)
    parser.add_argument("--learners", default=",".join(binary_grid.LEARNERS))
    parser.add_argument("--horizons", default=",".join(str(h) for h in LONG_HORIZONS))
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR, help="Shared panel cache dir.")
    args = parser.parse_args(argv)

    smoke = os.environ.get("WI038_SMOKE", "").strip()
    if args.limit is None and smoke.isdigit():
        args.limit = int(smoke)
    if args.out is None and smoke:
        args.out = DEFAULT_SMOKE_DIR
    dry_run = smoke.isdigit() or args.limit is not None
    horizons = tuple(int(s) for s in args.horizons.split(",") if s.strip())
    learners = tuple(s.strip() for s in args.learners.split(",") if s.strip())

    from src.market_cli import cli_markets
    markets = cli_markets(args.market, prog="wi038.binary_grid_longh")
    if markets is None:
        return 2
    out_dir = resolve_out_dir(args.out, dry_run=dry_run)
    model_dir = None if dry_run else MODEL_DIR  # pickles only on a real run
    cfg = train.load_settings()
    t0 = time.time()
    with high_horizon_mode(horizons, dry_run=dry_run):
        out = run_high_h(cfg, markets, learners=learners, horizons=horizons, out_dir=out_dir,
                         model_dir=model_dir, limit=args.limit, allow_fixture=args.allow_fixture,
                         cache_dir=args.cache_dir, core_hours=args.core_hours,
                         placebo_seeds=args.placebo_seeds, dry_run=dry_run)
        report = build_report(out, out_dir / REPORT_NAME)  # inside: FOLD_COUNTS still populated
    for r in out["results"]:
        print(f"[wi038.grid] {r['market']}: cells={len(r['cells'])} "
              f"skipped={len(r['skipped'])} core={r['core_sec']}s")
    print(f"[wi038.grid] report -> {report} | placebo={out['n_placebo']} | "
          f"survivors={len(out['survivors'])} | total {round(time.time() - t0, 1)}s")
    print("[wi038.grid] EXIT:0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
