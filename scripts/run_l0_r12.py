"""D-026 Phase 1 — L0 R12 reference-grid driver (PM-owned analysis script).

Runs the six net-new L0 feature blocks (WI-052..057) on the R12 reference grid
per D-026 ruling 2/3 (vol_expand quarantined -> reference targets = b_hold +
L1-1 xsec_vol_rank_bin):

  2 targets x horizons {8, 13, 21} x lightgbm x 2 markets = 12 cells per block,
  ONE BH-FDR family per block (m = 12, alpha = 0.05).

Test statistic: fold-paired OOF AUC delta against the baseline panel (249-col
panel without the six blocks). Per-cell p-value = two-sided paired t-test over
the 5 fold deltas (df = 4) — the plan's fold-paired statistic; no 5-seed
placebo (a placebo on the delta would cost ~20 core-h; flag for admin if the
paired-t read-out should be replaced). Precision@k lift is reported as a
predictive diagnostic only (D-023; no economic claim).

Single burst, checkpointed per cell (`--resume <ckpt_dir>`), budget-gated.
Footer reports START_UTC / core-h / END_UTC / NEXT_ALLOWED_RUN_UTC.

CLI:
    uv run python scripts/run_l0_r12.py --market ALL
    uv run python scripts/run_l0_r12.py --market ALL --resume /tmp/l0_r12_ckpt
    L0R12_SMOKE=3 uv run python scripts/run_l0_r12.py --out /tmp/l0r12_smoke
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo root -> `src` importable

from src.swing_bsh import binary_features_ext as ext
from src.swing_bsh import binary_grid, binary_labels, binary_train, learner_ext, train
from src.swing_bsh import targets_ext as tg
from src.swing_bsh.precision_diag import precision_at_k
from src.xgb_trainer import PurgedWalkForwardSplit

BASE_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = BASE_DIR / "reports"
CACHE_DIR = Path("/tmp/l0_r12")
R12_HORIZONS: tuple[int, ...] = (8, 13, 21)
LEARNER = "lightgbm"
TARGETS: tuple[str, ...] = ("b_hold", "xsec_vol_rank_bin")
PRUNE_RHO = 0.3
N_SPLITS = binary_grid.N_SPLITS
CORE_HOUR_CAP = 2.5
KS = (10, 25, 50, 100)

BLOCKS: dict[str, tuple[str, ...]] = {
    "L0-1_swing_structure": ("swing_leg_len_", "swing_leg_dur_", "swing_depth_atr_prev"),
    "L0-2_realized_asymmetry": ("semivar_", "rv_skew_"),
    "L0-3_regime_age": ("regime_",),
    "L0-4_jump_intensity": ("jump_",),
    "L0-5_universe_dispersion": ("disp_",),
    "L0-6_effort_result": ("effort_",),
}
"""Block name -> column prefixes (WI-052..057 contracts); a block's delta cols
are every candidate feature matching one of its prefixes."""


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _pinned_variant(market: str) -> str:
    return ext.variant_name(tg.PINNED_EVENT[market], "full", 0.8)


# --------------------------------------------------------------------------- #
# Panel + labels
# --------------------------------------------------------------------------- #
def _cache_paths(market: str) -> tuple[Path, Path]:
    return CACHE_DIR / f"l0r12_panel_{market}.parquet", CACHE_DIR / f"l0r12_labels_{market}.npz"


def load_market(market: str, *, limit: int | None = None, allow_fixture: bool = False,
                use_cache: bool = True):
    """`(panel, b_hold labels by h, xsec labels by h)` for one market.

    b_hold: three-binary labels on the pinned variant from the ext panel build.
    xsec_vol_rank_bin: date-level universe ranks (same pass contract as
    tg.build_targets_panel: symbol-sequential, row-aligned to the panel).
    """
    variant = _pinned_variant(market)
    pp, lp = _cache_paths(market)
    if use_cache and limit is None and pp.exists() and lp.exists():
        panel = pd.read_parquet(pp)
        blob = np.load(lp)
        b_hold = {int(h): blob[f"b_hold|{h}"] for h in R12_HORIZONS}
        xsec = {int(h): blob[f"xsec|{h}"] for h in R12_HORIZONS}
        return panel, b_hold, xsec

    event = tg.PINNED_EVENT[market]
    panel, blabels = ext.build_variant_panel(
        market, allow_fixture=allow_fixture, max_symbols=limit,
        variants=[(variant, event, "full", 0.8)], horizons=R12_HORIZONS)
    if panel.empty:
        raise RuntimeError(f"no swing events for market={market}")

    # xsec labels: second symbol-sequential pass over the SAME event stream
    # (iter_events mirrors build_variant_panel's event filter).
    xrows: list[tuple] = []
    n_rows = 0
    for symbol, g, idx, states, _atr in tg.iter_events(market, allow_fixture=allow_fixture,
                                                       max_symbols=limit):
        n_rows += int(idx.size)
        high = g["high"].to_numpy("float64")
        low = g["low"].to_numpy("float64")
        xrows.append((symbol, g["close"].to_numpy("float64"),
                      ext._entry_bars(high, low, idx, states == "at_bottom"),
                      g["date"].to_numpy()))
    if n_rows != len(panel):
        raise RuntimeError(f"label/panel row mismatch for {market}: {n_rows} != {len(panel)}")
    event = tg.PINNED_EVENT[market]
    closes = {r[0]: r[1] for r in xrows}
    frame = pd.DataFrame({
        "symbol": np.concatenate([[s] * bars[event].size for s, _c, bars, _d in xrows]),
        "bar": np.concatenate([bars[event] for _s, _c, bars, _d in xrows]),
        "date": np.concatenate([dates[bars[event]] for _s, _c, bars, dates in xrows])})
    xsec = {int(h): np.asarray(tg.xsec_vol_rank_bin_labels(frame, closes, int(h)))
            for h in R12_HORIZONS}
    b_hold = {int(h): np.asarray(blabels[(variant, int(h))]["b_hold"]) for h in R12_HORIZONS}

    if use_cache and limit is None:
        pp.parent.mkdir(parents=True, exist_ok=True)
        panel.to_parquet(pp, index=False)
        np.savez_compressed(lp, **{**{f"b_hold|{h}": b_hold[h] for h in R12_HORIZONS},
                                   **{f"xsec|{h}": xsec[h] for h in R12_HORIZONS}})
    return panel, b_hold, xsec


def _features_for(panel: pd.DataFrame, block: str | None) -> tuple[list[str], list[str]]:
    """`(kept, dropped)` rho-pruned feature names for the baseline or one block."""
    cand = ext.candidate_features(panel)
    if block is None:
        feats = [f for f in cand if not any(f.startswith(p) for pre in BLOCKS.values()
                                            for p in pre)]
    else:
        block_cols = [f for f in cand if any(f.startswith(p) for p in BLOCKS[block])]
        # exclude ALL block cols from the base so the delta vs baseline is the
        # block's own contribution (not other blocks' surviving cols)
        base = [f for f in cand if not any(f.startswith(p) for pre in BLOCKS.values()
                                           for p in pre)]
        feats = base + block_cols
    kept, dropped = binary_labels.kept_features(panel, threshold=PRUNE_RHO, features=feats)
    return binary_labels.feature_names(kept), binary_labels.feature_names(dropped)


def _design(panel: pd.DataFrame, kept: list[str]):
    p = train.engineer(panel)
    p["k"] = np.float32(1.0)
    p["horizon"] = np.float32(21.0)
    return train.feature_matrix(p, kept)


# --------------------------------------------------------------------------- #
# Cells
# --------------------------------------------------------------------------- #
def _fold_aucs(X, y, dates, params, splitter, tag) -> tuple[list[float], np.ndarray]:
    """`(per-fold AUCs, pooled OOF predictions)` for one cell."""
    cv = binary_grid.cell_cv(X, y, dates, LEARNER, params, splitter, None, tag)
    _auc, _ic, folds = binary_grid.auc_ic(y, cv["oof"], cv["fold_id"])
    return [float(a) for a in folds], cv["oof"]


def _paired_p(deltas: list[float]) -> tuple[float, float]:
    """Two-sided paired t over fold deltas -> (mean delta, p)."""
    d = np.asarray(deltas, dtype="float64")
    d = d[np.isfinite(d)]
    if d.size < 2 or float(np.std(d, ddof=1)) == 0.0:
        return (float(d.mean()) if d.size else float("nan")), 1.0
    t = float(d.mean()) / (float(np.std(d, ddof=1)) / math.sqrt(d.size))
    return float(d.mean()), float(2.0 * stats.t.sf(abs(t), df=d.size - 1))


def _bh(pvals: list[float], alpha: float = binary_grid.FDR_ALPHA,
        m_total: int | None = None) -> np.ndarray:
    return binary_grid.bh_fdr(pvals, alpha=alpha, m_total=m_total)[0]


def _fmt_lift(v) -> str:
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "n/a"
    return "n/a" if not np.isfinite(v) else f"{v:.3f}x"


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def run(markets: list[str], *, ckpt_dir: Path | None, core_hours: float,
        out_dir: Path, limit: int | None = None, allow_fixture: bool = False,
        blocks: tuple[str, ...] = tuple(BLOCKS)) -> int:
    budget = binary_grid.CoreBudget(core_hours)
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    cfg = train.load_settings()
    params = binary_train.learner_params(cfg)[LEARNER]
    ckpt_path = ckpt_dir / "l0_r12_cells.json"
    cells: dict[str, dict] = (json.loads(ckpt_path.read_text()) if ckpt_path.exists() else {})

    def key(*parts) -> str:
        return "|".join(str(p) for p in parts)

    results: dict[str, list[dict]] = {}
    splitters = {h: PurgedWalkForwardSplit(n_splits=N_SPLITS,
                                           embargo_td=train.embargo_for([h]))
                 for h in R12_HORIZONS}
    grid_share = max(0.0, budget.cap * 3600 * 0.95)  # fits only; no placebo in R12

    for market in markets:
        if budget.left() < binary_grid.PLACEBO_MIN_LEFT:
            print(f"[l0.r12] budget exhausted before market={market}")
            break
        variant = _pinned_variant(market)
        panel, b_hold, xsec = load_market(market, limit=limit, allow_fixture=allow_fixture)
        y_by_target = {"b_hold": b_hold, "xsec_vol_rank_bin": xsec}
        base_kept, _base_drop = _features_for(panel, None)
        Xb, feats_b = _design(panel, base_kept)
        dates = panel["date"].to_numpy()

        # baseline refit (shared across blocks; reused from checkpoint when present)
        base_auc: dict[tuple[str, int], list[float]] = {}
        for tgt in TARGETS:
            for h in R12_HORIZONS:
                k = key("base", market, tgt, h)
                if k in cells:
                    base_auc[(tgt, h)] = cells[k]["fold_auc"]
                    continue
                if budget.spent() > grid_share:
                    print(f"[l0.r12] budget stop at baseline {market} {tgt} h{h}")
                    break
                base_auc[(tgt, h)], oof = _fold_aucs(
                    Xb, y_by_target[tgt][h], dates, params, splitters[h],
                    f"{market}_base_{tgt}_h{h}")
                cells[k] = {"fold_auc": base_auc[(tgt, h)],
                            "prec_base": precision_at_k(y_by_target[tgt][h], oof, (25,))}
                ckpt_path.write_text(json.dumps(cells))

        # per-block delta grids (ADR order: BLOCKS is insertion-ordered L0-1..L0-6)
        for block in blocks:
            if budget.left() < binary_grid.PLACEBO_MIN_LEFT:
                print(f"[l0.r12] budget exhausted before block={block} ({market})")
                break
            blk_kept, blk_drop = _features_for(panel, block)
            Xk, _feats = _design(panel, blk_kept)
            block_cells: list[dict] = []
            for tgt in TARGETS:
                for h in R12_HORIZONS:
                    ck = key(block, market, tgt, h)
                    if ck in cells:
                        block_cells.append(cells[ck])
                        continue
                    if budget.spent() > grid_share:
                        print(f"[l0.r12] budget stop at {block} {market} {tgt} h{h}")
                        break
                    fa, oof = _fold_aucs(Xk, y_by_target[tgt][h], dates, params, splitters[h],
                                         f"{market}_{block}_{tgt}_h{h}")
                    prec = precision_at_k(y_by_target[tgt][h], oof, (25,))
                    prec_base = cells.get(key("base", market, tgt, h), {}).get("prec_base")
                    deltas = [b - a for a, b in zip(base_auc[(tgt, h)], fa)]
                    d_mean, p = _paired_p(deltas)
                    cell = {"block": block, "market": market, "target": tgt, "h": int(h),
                            "learner": LEARNER, "variant": variant,
                            "auc_base_mean": float(np.mean(base_auc[(tgt, h)])),
                            "auc_block_mean": float(np.mean(fa)),
                            "delta": d_mean, "p": p,
                            "prec25": prec, "prec25_base": prec_base,
                            "fold_auc_base": base_auc[(tgt, h)], "fold_auc_block": fa,
                            "n_features": len(blk_kept)}
                    block_cells.append(cell)
                    cells[ck] = cell
                    ckpt_path.write_text(json.dumps(cells))
            if block_cells:
                results.setdefault(block, []).extend(block_cells)

    # BH per block (m = 12 design multiplicity, over the full family)
    m_total = len(TARGETS) * len(R12_HORIZONS) * len(markets)
    summary_rows: list[str] = []
    for block, block_cells in results.items():
        seen: dict[tuple, dict] = {}
        for c in block_cells:
            seen[(c["market"], c["target"], c["h"])] = c
        uniq = list(seen.values())
        surv = _bh([c["p"] for c in uniq], m_total=m_total)
        for c, s in zip(uniq, surv):
            c["fdr"] = bool(s)
        n_surv = int(surv.sum())
        summary_rows.append(f"### {block} — {n_surv}/{m_total} BH-FDR survivors")
        summary_rows.append("")
        summary_rows.append("| market | target | h | base AUC | block AUC | ΔAUC | p | FDR | prec25 lift |")
        summary_rows.append("| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | ---: |")
        for c in sorted(uniq, key=lambda c: -c["delta"]):
            pb = (c.get("prec25_base") or {}).get(25)
            pc = (c.get("prec25") or {}).get(25)
            lift = (pc / pb) if (pb and pc) else float("nan")
            summary_rows.append(
                f"| {c['market']} | `{c['target']}` | {c['h']} | {c['auc_base_mean']:.4f} | "
                f"{c['auc_block_mean']:.4f} | {c['delta']:+.4f} | {c['p']:.3g} | "
                f"{'YES' if c.get('fdr') else ''} | {_fmt_lift(lift)} |")
        summary_rows.append("")

    end = time.time()
    footer = ["", "## Footer", "",
              f"- START_UTC: {START_UTC}", f"- END_UTC: {_now()}",
              f"- core: {budget.spent():.1f}s of {int(core_hours * 3600)}s cap",
              f"- NEXT_ALLOWED_RUN_UTC: "
              f"{(dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%MZ')}"
              f" (burst {'≥' if budget.spent() >= 3600 else '<'} 1 core-h)",
              "- Verdict PROVISIONAL — computed labels are advisory until admin ratification.",
              "- PREDICTIVE DIAGNOSTIC — no economic claim (D-023).", ""]
    report = out_dir / "l0_r12_summary.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(
        ["# D-026 Phase 1 — L0 R12 reference grids (PROVISIONAL)", "",
         f"- Generated (UTC): {_now()}",
         f"- R12: 2 targets (`b_hold`, `xsec_vol_rank_bin`) x horizons "
         f"{R12_HORIZONS} x {LEARNER} x {len(markets)} markets = {m_total} cells per block",
         f"- Test statistic: fold-paired OOF AUC delta vs baseline; paired t (df=4); "
         f"BH alpha={binary_grid.FDR_ALPHA}, m={m_total} per block",
         "", *summary_rows, *footer]) + "\n")
    print(f"[l0.r12] report -> {report}")
    print(f"[l0.r12] EXIT:0 | core={budget.spent():.1f}s | wall={end - t0_global:.0f}s")
    return 0


START_UTC = ""
t0_global = 0.0


def main(argv: list[str] | None = None) -> int:
    global START_UTC, t0_global
    parser = argparse.ArgumentParser(description="D-026 L0 R12 reference grids (PM)")
    parser.add_argument("--market", default="ALL")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--ckpt-dir", default="/tmp/l0_r12_ckpt")
    parser.add_argument("--core-hours", type=float, default=CORE_HOUR_CAP)
    parser.add_argument("--allow-fixture", action="store_true")
    parser.add_argument("--blocks", default=None,
                        help="Comma-separated block names to run (default: all six).")
    args = parser.parse_args(argv)

    smoke = os.environ.get("L0R12_SMOKE", "").strip()
    if args.limit is None and smoke.isdigit():
        args.limit = int(smoke)
    out_dir = Path(args.out) if args.out else REPORTS_DIR
    ckpt_dir = Path(args.ckpt_dir)

    from src.market_cli import cli_markets
    markets = cli_markets(args.market, prog="l0.r12")
    if markets is None:
        return 2
    if smoke:
        markets = markets[:1]
    START_UTC, t0_global = _now(), time.time()
    blocks = (tuple(s.strip() for s in args.blocks.split(",") if s.strip())
              if args.blocks else tuple(BLOCKS))
    with learner_ext.learner_extension_mode(
            variants=tuple(_pinned_variant(m) for m in markets),
            horizons=R12_HORIZONS, binary="b_hold"):
        return run(markets, ckpt_dir=ckpt_dir, core_hours=args.core_hours, out_dir=out_dir,
                   limit=args.limit, allow_fixture=args.allow_fixture, blocks=blocks)


if __name__ == "__main__":
    raise SystemExit(main())
