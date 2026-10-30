"""WI-016 Step 6 — conditional meta-labeler (cleared barrier targets only).

Design (D-016 Q5, admin-amended 2026-10-30)
------------------------------------------
* **Primary (side):** per-date rank of ``yangzhang_21`` — the best *clean* primary
  in the de-anchored bake-off (`reports/wi016_addendum_bakeoff_CAD.md`); the
  bake-off's data-chosen winner ``tc_rating`` is excluded (static watchlist
  snapshot, no point-in-time history). Events are the **long side** of the
  per-date top decile (q = 0.9).
* **Training expansion (Q5):** the meta-labeler trains on the **top-two deciles**
  (~2x events) and records a per-event ``decile_flag`` (1 = top decile, 0 = second
  decile) for stratified analysis. Shipped decisions and shortlist semantics stay
  **top-decile only**.
* **Targets:** only the four barrier targets the honest-edge addendum cleared at
  the standing 20 bps band (`reports/wi016_addendum_probe_CAD.md`):
  ``tb_label_k15_h8``, ``tb_label_k15_h55``, ``tb_label_k15_h144``,
  ``tb_label_k20_h8``. Barrier-resolved rows only (``tb_touch_*`` in {+1,-1}), so
  the meta-label is *bet P&L > 0* (profit barrier first touch = 1, stop first = 0).
* **Machinery:** the existing ``src.xgb_trainer`` model/calibration path
  (`PurgedWalkForwardSplit`, `purged_holdout`, `fit_calibrated` -> `CalibratedXGB`,
  isotonic/sigmoid per CB-04) with the per-horizon embargo ``max(20, h)``
  everywhere and a five-seed label-permutation placebo.

No order execution exists anywhere in this module or in
``src.wi016.actions``: the output is a research shortlist artifact the human
gate consumes.

CLI::

    python -m src.wi016.meta_labeler --market CAD
    python -m src.wi016.meta_labeler --market CAD --max-symbols 60
"""

from __future__ import annotations

import argparse
import datetime as dt
import gc
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from src.factors.e5_baseline import E5_FACTORS, factor_frame
from src.feature_engine import compute_features_wi016, iter_market_symbols, wi016_feature_names
from src.market_cli import add_market_argument, cli_markets, report_path
from src.targets import wilder_atr
from src.wi016.triple_barrier import (
    TOUCH_PROFIT,
    TOUCH_STOP,
    _k_tag,
    compute_triple_barrier,
)
from src.xgb_trainer import (
    CALIB_FRACTION,
    N_PLACEBO_SEEDS,
    PurgedWalkForwardSplit,
    fit_calibrated,
    horizon_embargo,
    load_settings,
    purged_holdout,
    run_cv,
    xgb_params,
)

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "reports"

CLEARED_TARGETS: tuple[str, ...] = (
    "tb_label_k15_h8",
    "tb_label_k15_h55",
    "tb_label_k15_h144",
    "tb_label_k20_h8",
)
"""Barrier targets the honest-edge addendum cleared at 20 bps (CAD only)."""

CLEARED_GRID: tuple[tuple[float, int], ...] = ((1.5, 8), (1.5, 55), (1.5, 144), (2.0, 8))
"""The ``(k, h)`` pairs behind :data:`CLEARED_TARGETS`."""

PRIMARY_COLUMN = "yangzhang_21"
"""Long-side primary: per-date rank of this column defines the events."""

TOP_DECILE_Q = 0.9
"""Top-decile event threshold (shipped decisions + shortlist)."""

SECOND_DECILE_Q = 0.8
"""Training expansion: the second decile joins training with ``decile_flag = 0``."""

MIN_DATE = "2016-01-01"
PLACEBO_SEED0 = 1000
DEFAULT_META_FEATURES: tuple[str, ...] = tuple(wi016_feature_names()) + tuple(E5_FACTORS)
"""Feature universe = the WI-016 unified grid + E5 (the probe's universe, 116 cols)."""

__all__ = [
    "CLEARED_GRID",
    "CLEARED_TARGETS",
    "DEFAULT_META_FEATURES",
    "MIN_DATE",
    "PLACEBO_SEED0",
    "PRIMARY_COLUMN",
    "SECOND_DECILE_Q",
    "TOP_DECILE_Q",
    "build_meta_panel",
    "decile_flags",
    "embargo_for",
    "emit",
    "event_frame",
    "fold_plan",
    "market_cleared",
    "meta_cv",
    "meta_labeler",
    "primary_pct_rank",
    "run_market",
    "target_grid",
    "target_horizon",
]


# --------------------------------------------------------------------------- #
# Event construction (primary side + decile expansion)
# --------------------------------------------------------------------------- #
def target_grid(target: str) -> tuple[float, int]:
    """``(k, h)`` parsed from a ``tb_label_<k>_h<h>`` column name."""
    m = re.match(r"^tb_label_k(\d+)_h(\d+)$", str(target))
    if not m:
        raise KeyError(f"not a triple-barrier label column: {target!r}")
    return int(m.group(1)) / 10.0, int(m.group(2))


def target_horizon(target: str) -> int:
    """Vertical-barrier horizon ``h`` for a cleared target column."""
    return target_grid(target)[1]


def embargo_for(target: str) -> int:
    """Per-horizon purge embargo ``max(20, h)`` (D-016 precondition fix)."""
    return horizon_embargo(target_horizon(target))


def primary_pct_rank(values, dates) -> np.ndarray:
    """Per-date percentile rank of the primary; non-finite values stay NaN."""
    v = np.asarray(values, dtype="float64")
    s = pd.Series(np.where(np.isfinite(v), v, np.nan))
    return s.groupby(pd.Series(np.asarray(dates))).rank(pct=True).to_numpy(dtype="float64")


def decile_flags(pct, q_hi: float = TOP_DECILE_Q, q_lo: float = SECOND_DECILE_Q) -> np.ndarray:
    """Decile membership: ``1`` top decile, ``0`` second decile, ``-1`` outside.

    The shipped side/decisions are the top decile (``1``); the training expansion
    adds the second decile (``0``) so the model sees ~2x events (D-016 Q5).
    """
    p = np.asarray(pct, dtype="float64")
    flag = np.full(p.shape, -1, dtype="int8")
    finite = np.isfinite(p)
    flag[finite & (p >= q_lo) & (p < q_hi)] = 0
    flag[finite & (p >= q_hi)] = 1
    return flag


def event_frame(
    panel: pd.DataFrame,
    target: str,
    primary: str = PRIMARY_COLUMN,
    feature_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Meta-labeler training events for one barrier target.

    Rows kept: barrier-resolved (``tb_touch_*`` in {+1,-1}) **and** in the
    top-two-decile expansion of the per-date primary rank. Columns: identifiers,
    the primary/decile metadata, ``meta_label`` (1 = profit barrier first touch =
    bet P&L > 0) and the feature matrix. Long side only.
    """
    k, h = target_grid(target)
    tag = _k_tag(k)
    label_col = f"tb_label_{tag}_h{h}"
    touch_col = f"tb_touch_{tag}_h{h}"
    for col in (label_col, touch_col, primary):
        if col not in panel.columns:
            raise KeyError(f"panel is missing {col!r}")

    feats = list(feature_cols) if feature_cols is not None else list(DEFAULT_META_FEATURES)
    feats = [f for f in feats if f in panel.columns]
    # The primary side is point-in-time known at the event, so it is always a
    # model feature (the caller's list is a floor, not a ceiling).
    if primary in panel.columns and primary not in feats:
        feats.append(primary)

    label = panel[label_col].to_numpy(dtype="float64")
    touch = panel[touch_col].to_numpy(dtype="float64")
    resolved = np.isfinite(label) & ((touch == TOUCH_PROFIT) | (touch == TOUCH_STOP))

    pct = primary_pct_rank(panel[primary].to_numpy(), panel["date"].to_numpy())
    flag = decile_flags(pct)
    keep = resolved & (flag >= 0)

    meta = pd.DataFrame({
        "date": panel["date"].to_numpy()[keep],
        "symbol": panel["symbol"].to_numpy()[keep],
        "primary": panel[primary].to_numpy(dtype="float64")[keep],
        "primary_pct": pct[keep],
        "decile_flag": flag[keep],
        "meta_label": (touch[keep] == TOUCH_PROFIT).astype("int8"),
        "target": target,
        "k": np.float32(k),
        "h": np.int16(h),
    })
    geometry = {
        extra: panel[extra].to_numpy(dtype="float32")[keep]
        for extra in ("close", "atr") if extra in panel.columns
    }
    # One concat for the whole feature block (per-column inserts fragment the frame).
    block = pd.DataFrame({f: panel[f].to_numpy(dtype="float32")[keep] for f in feats})
    return pd.concat([meta, pd.DataFrame(geometry), block], axis=1)


# --------------------------------------------------------------------------- #
# Fold geometry (leakage-safe by construction; pure, no fitting)
# --------------------------------------------------------------------------- #
def fold_plan(
    dates,
    target: str,
    n_splits: int = 5,
    initial_train_fraction: float = 0.40,
) -> list[dict]:
    """Purged walk-forward geometry for one target's events.

    Pure date arithmetic on the same primitives the trainer uses, so the
    ``max(20, h)`` embargo is verifiable without fitting anything. Every fold's
    calibration block is additionally purged by the same embargo
    (`purged_holdout`).
    """
    d = np.asarray(pd.to_datetime(pd.Series(dates)).to_numpy())
    embargo = embargo_for(target)
    splitter = PurgedWalkForwardSplit(
        n_splits=n_splits, embargo_td=embargo, initial_train_fraction=initial_train_fraction
    )
    uniq = np.unique(d)
    plan: list[dict] = []
    for k, (tr, va) in enumerate(splitter.split(d)):
        if len(tr) == 0 or len(va) == 0:
            continue
        fit_i, cal_i = purged_holdout(d, tr, CALIB_FRACTION, embargo)
        if len(fit_i) == 0 or len(cal_i) == 0:
            continue
        plan.append({
            "fold": int(k),
            "target": target,
            "horizon": target_horizon(target),
            "embargo_td": embargo,
            "n_train": int(len(tr)),
            "n_fit": int(len(fit_i)),
            "n_calib": int(len(cal_i)),
            "n_val": int(len(va)),
            "max_train_date": str(pd.Timestamp(d[tr].max()).date()),
            "min_val_date": str(pd.Timestamp(d[va].min()).date()),
            "max_fit_date": str(pd.Timestamp(d[fit_i].max()).date()),
            "min_calib_date": str(pd.Timestamp(d[cal_i].min()).date()),
            "train_val_gap_td": int(
                np.searchsorted(uniq, d[va].min()) - np.searchsorted(uniq, d[tr].max())
            ),
            "fit_calib_gap_td": int(
                np.searchsorted(uniq, d[cal_i].min()) - np.searchsorted(uniq, d[fit_i].max())
            ),
        })
    return plan


# --------------------------------------------------------------------------- #
# Meta-model CV (existing xgb_trainer machinery)
# --------------------------------------------------------------------------- #
def _safe_auc(y: np.ndarray, p: np.ndarray) -> float:
    fin = np.isfinite(p)
    if fin.sum() == 0 or len(np.unique(y[fin])) < 2:
        return float("nan")
    return float(roc_auc_score(y[fin], p[fin]))


def _safe_ap(y: np.ndarray, p: np.ndarray) -> float:
    fin = np.isfinite(p)
    if fin.sum() == 0 or len(np.unique(y[fin])) < 2:
        return float("nan")
    return float(average_precision_score(y[fin], p[fin]))


def _nanmean(values) -> float:
    """Mean over the finite members only (NaN when none are finite)."""
    arr = np.asarray([v for v in values if np.isfinite(v)], dtype="float64")
    return float(arr.mean()) if arr.size else float("nan")


def meta_cv(
    events: pd.DataFrame,
    target: str,
    feature_cols: list[str] | None = None,
    n_splits: int = 5,
    placebo_seeds: int = N_PLACEBO_SEEDS,
    params: dict | None = None,
) -> dict:
    """Fit the meta-model per cleared target with purged walk-forward CV.

    Reuses `src.xgb_trainer.run_cv` (per-fold `purged_holdout` + `fit_calibrated`,
    CB-04 isotonic/sigmoid), then runs a label-permutation placebo with the same
    geometry. Returns OOF predictions, per-fold stats, placebo stats, the
    decile-stratified OOF metrics and the final all-data model.
    """
    feats = list(feature_cols) if feature_cols is not None else [
        f for f in DEFAULT_META_FEATURES if f in events.columns
    ]
    if not feats:
        raise ValueError(f"no usable feature columns for {target}")

    X = events[feats].to_numpy(dtype="float32")
    y = events["meta_label"].to_numpy().astype("int8")
    dates = np.asarray(pd.to_datetime(pd.Series(events["date"])).to_numpy())
    embargo = embargo_for(target)

    splitter = PurgedWalkForwardSplit(n_splits=n_splits, embargo_td=embargo)
    oof, fold_id, stats = run_cv(X, y, dates, params or xgb_params(load_settings()), splitter)

    placebo: list[dict] = []
    for s in range(int(placebo_seeds)):
        y_pl = np.random.default_rng(PLACEBO_SEED0 + s).permutation(y)
        p_pl, _fid, _st = run_cv(
            X, y_pl, dates, params or xgb_params(load_settings()), splitter
        )
        placebo.append({
            "seed": PLACEBO_SEED0 + s,
            "oof_ap": _safe_ap(y_pl, p_pl),
            "oof_auc": _safe_auc(y_pl, p_pl),
        })

    flag = events["decile_flag"].to_numpy()
    stratified = {
        "top_decile": {"n": int((flag == 1).sum()), "oof_ap": _safe_ap(y[flag == 1], oof[flag == 1]),
                       "oof_auc": _safe_auc(y[flag == 1], oof[flag == 1])},
        "second_decile": {"n": int((flag == 0).sum()), "oof_ap": _safe_ap(y[flag == 0], oof[flag == 0]),
                          "oof_auc": _safe_auc(y[flag == 0], oof[flag == 0])},
    }

    all_idx = np.arange(len(y))
    fit_i, cal_i = purged_holdout(dates, all_idx, CALIB_FRACTION, embargo)
    final = fit_calibrated(X[fit_i], y[fit_i], X[cal_i], y[cal_i], params or xgb_params(load_settings()))

    return {
        "target": target,
        "horizon": target_horizon(target),
        "k": target_grid(target)[0],
        "embargo_td": embargo,
        "features": feats,
        "n_events": int(len(events)),
        "n_top_decile": int((flag == 1).sum()),
        "pos_rate": float(y.mean()),
        "fold_plan": fold_plan(dates, target, n_splits=n_splits),
        "folds": stats,
        "oof": oof,
        "fold_id": fold_id,
        "oof_ap": _safe_ap(y, oof),
        "oof_auc": _safe_auc(y, oof),
        "placebo": placebo,
        "placebo_mean_ap": _nanmean([r["oof_ap"] for r in placebo]),
        "placebo_mean_auc": _nanmean([r["oof_auc"] for r in placebo]),
        "stratified": stratified,
        "final_model": final,
        "final_calibration": getattr(final, "method", None),
        "n_fit_final": int(len(fit_i)),
        "n_calib_final": int(len(cal_i)),
    }


def meta_labeler(
    panel: pd.DataFrame,
    market: str,
    targets: tuple[str, ...] = CLEARED_TARGETS,
    feature_cols: list[str] | None = None,
    n_splits: int = 5,
    placebo_seeds: int = N_PLACEBO_SEEDS,
) -> dict:
    """Run the meta-labeler for every cleared target on one market panel."""
    results: dict[str, dict] = {}
    for target in targets:
        events = event_frame(panel, target, feature_cols=feature_cols)
        res = meta_cv(events, target, feature_cols=feature_cols,
                      n_splits=n_splits, placebo_seeds=placebo_seeds)
        results[target] = res
        del events
        gc.collect()
    return {"market": market, "targets": results}


# --------------------------------------------------------------------------- #
# Gate: only addendum-cleared markets/targets run
# --------------------------------------------------------------------------- #
def market_cleared(market: str, out_dir: Path = REPORTS_DIR) -> bool:
    """True when the honest-edge addendum's barrier-resolved verdict is CLEAR.

    The addendum report is the gate record; a missing report is *not* a clear.
    """
    p = report_path(out_dir, "wi016_addendum_probe", market)
    if not p.exists():
        return False
    for line in p.read_text().splitlines():
        if "barrier-resolved" in line and "DECISION" in line.upper():
            return "CLEAR" in line.upper() and "NOT_CLEAR" not in line.upper()
    return False


# --------------------------------------------------------------------------- #
# Panel build (streaming, float32, bounded memory)
# --------------------------------------------------------------------------- #
def build_meta_panel(
    market: str,
    min_date: str = MIN_DATE,
    allow_fixture: bool = False,
    max_symbols: int | None = None,
) -> pd.DataFrame:
    """One market's meta-labeler panel: features + E5 + primary + barrier labels.

    Streams symbols one at a time (8 GB / no-swap host); keeps only the unified
    feature grid, E5, the cleared ``(k, h)`` label/touch pairs, ``close``/``atr``
    (for the barrier levels) and identifiers. Every calculated column is cast to
    float32 immediately.
    """
    features = wi016_feature_names()
    horizons = tuple(sorted({h for _k, h in CLEARED_GRID}))
    keep_tb = [
        f"{kind}_{_k_tag(k)}_h{h}"
        for k, h in CLEARED_GRID
        for kind in ("tb_label", "tb_touch")
    ]
    parts: list[pd.DataFrame] = []
    for i, (_sym, raw) in enumerate(iter_market_symbols(market, min_date=min_date, allow_fixture=allow_fixture)):
        if max_symbols is not None and i >= max_symbols:
            break
        g = raw.sort_values("date").reset_index(drop=True)
        feats = compute_features_wi016(g)
        e5 = factor_frame(g)
        tb = compute_triple_barrier(g, horizons=horizons)
        base = pd.DataFrame({
            "date": g["date"], "symbol": g["symbol"], "market": g["market"],
            "close": g["close"].astype("float32"),
            "atr": wilder_atr(g).astype("float32"),
        })
        combined = pd.concat([base, feats[features], e5, tb[keep_tb]], axis=1)
        combined = combined[combined["date"] >= pd.Timestamp(min_date)]
        parts.append(combined)
        del g, feats, e5, tb, combined
        if (i + 1) % 50 == 0:
            gc.collect()
    if not parts:
        raise RuntimeError(f"no meta-labeler panel rows for market={market}")
    panel = pd.concat(parts, ignore_index=True)
    for c in panel.columns:
        if c not in ("date", "symbol", "market"):
            panel[c] = panel[c].astype("float32")
    gc.collect()
    return panel


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def _write_report(result: dict, market: str, shortlist_meta: dict | None,
                  out_dir: Path = REPORTS_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = report_path(out_dir, "wi016_meta_labeler", market)
    n_seeds = len(next(iter(result["targets"].values()))["placebo"]) if result["targets"] else 0
    lines = [
        f"# WI-016 step 6 meta-labeler — {market}",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Primary: `{PRIMARY_COLUMN}` per-date rank, long side, top-decile events (q={TOP_DECILE_Q})",
        f"- Training expansion: top-two deciles (second decile flag = 0); shipped decisions top-decile only",
        f"- Targets: {', '.join(f'`{t}`' for t in result['targets'])}",
        f"- Embargo `max(20, h)` per target; CB-04 isotonic/sigmoid calibration; "
        f"{n_seeds}-seed label-permutation placebo",
        "- Meta-label = bet P&L > 0 (profit barrier first touch = 1, stop first = 0); barrier-resolved rows only.",
        "",
        "## Per-target OOF vs placebo",
        "",
        "| target | h | embargo | events | top-decile | pos rate | OOF AP | OOF AUC | placebo AP | placebo AUC | calibration |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |",
    ]
    for target, r in result["targets"].items():
        lines.append(
            f"| `{target}` | {r['horizon']} | {r['embargo_td']} | {r['n_events']:,} | "
            f"{r['n_top_decile']:,} | {r['pos_rate']:.3f} | {r['oof_ap']:.4f} | {r['oof_auc']:.4f} | "
            f"{r['placebo_mean_ap']:.4f} | {r['placebo_mean_auc']:.4f} | "
            f"{r['final_calibration'] or 'n/a'} |"
        )
    lines += ["", "## Decile-stratified OOF (training expansion)", "",
              "| target | stratum | n | OOF AP | OOF AUC |", "| :--- | :--- | ---: | ---: | ---: |"]
    for target, r in result["targets"].items():
        for name in ("top_decile", "second_decile"):
            s = r["stratified"][name]
            lines.append(f"| `{target}` | {name} | {s['n']:,} | {s['oof_ap']:.4f} | {s['oof_auc']:.4f} |")
    lines += ["", "## Purged walk-forward folds (`embargo_td = max(20, h)`)", "",
              "| target | fold | n_fit | n_calib | n_val | max train date | min val date | gap (td) | val AP | calibration |",
              "| :--- | ---: | ---: | ---: | ---: | :--- | :--- | ---: | ---: | :--- |"]
    for target, r in result["targets"].items():
        for f in r["fold_plan"]:
            stat = next((s for s in r["folds"] if s.get("fold") == f["fold"]), {})
            lines.append(
                f"| `{target}` | {f['fold']} | {f['n_fit']:,} | {f['n_calib']:,} | {f['n_val']:,} | "
                f"{f['max_train_date']} | {f['min_val_date']} | {f['train_val_gap_td']} | "
                f"{stat.get('val_pr_auc', float('nan')):.4f} | {stat.get('calibration', 'skipped')} |"
            )
    if shortlist_meta is not None:
        lines += ["", "## Shortlist artifact", "",
                  f"- Path: `{shortlist_meta['path']}`",
                  f"- Scoring date: {shortlist_meta['scoring_date']}",
                  f"- Rows: {shortlist_meta['n_rows']} ({shortlist_meta['n_trade']} TRADE / "
                  f"{shortlist_meta['n_no_trade']} NO_TRADE at {shortlist_meta['cost_bps']:.0f} bps)",
                  f"- Schema: {', '.join(shortlist_meta['columns'])}",
                  "- NO_TRADE is the default: a row is tradeable only when the calibrated meta-probability "
                  "clears the coin-flip floor and the expected edge exceeds the cost band.",
                  "- No order execution exists; this artifact is research context for the human gate."]

        # Caveats are computed from this run's numbers so they cannot drift stale.
        def _range(values, fmt="{:.4f}", empty="n/a") -> str:
            vals = [v for v in values if np.isfinite(v)]
            return f"{fmt.format(min(vals))}–{fmt.format(max(vals))}" if vals else empty

        n = shortlist_meta["n_rows"]
        trade_share = shortlist_meta["n_trade"] / n if n else float("nan")
        oof_aucs = [r["oof_auc"] for r in result["targets"].values()]
        pl_aucs = [r["placebo_mean_auc"] for r in result["targets"].values()]
        pos_rates = [r["pos_rate"] for r in result["targets"].values()]
        lines += [
            "", "## Caveats (auto-computed — read before the gate)", "",
            f"- **The cost band is not the binding constraint.** {shortlist_meta['n_trade']}/{n} shortlist "
            f"rows clear {shortlist_meta['cost_bps']:.0f} bps (trade share {trade_share:.1%}). The symmetric "
            "barrier payoff ``k·ATR/close`` is typically several percent, so a 20 bps round trip is dwarfed by "
            "the payoff scale: the abstain channel is driven by the probability floor, not the cost overlay.",
            f"- **The OOF edge is thin.** OOF AUC {_range(oof_aucs)} vs placebo {_range(pl_aucs)} "
            f"(≈0.50 = no edge). OOF AP "
            f"{_range([r['oof_ap'] for r in result['targets'].values()])} on base rates "
            f"{_range(pos_rates, '{:.3f}')}, so part of the AP advantage is the base rate itself.",
            "- The meta-label is a first-touch binary; entry is the scoring-date close and the exit is the "
            "barrier or the h-bar time stop. Intra-horizon drift and slippage beyond the flat cost band are "
            "not modelled.",
            "- The cost band is the unconfirmed WI-011 assumption; the addendum showed no verdict flip across "
            "10/20/30 bps, and this run uses the standing 20 bps.",
        ]
    md_path.write_text("\n".join(lines) + "\n")
    return md_path


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def emit(
    panel: pd.DataFrame,
    market: str,
    *,
    n_splits: int = 5,
    placebo_seeds: int = N_PLACEBO_SEEDS,
    cost_bps: float | None = None,
    out_dir: Path = REPORTS_DIR,
) -> dict:
    """Meta-labeler + action synthesis on an in-memory panel (no gate check).

    Called by :func:`run_market` after the addendum gate clears, and directly by
    the tests. Writes the new shortlist parquet and the meta-labeler report.
    """
    from src.wi016.actions import COST_BPS, build_shortlist, write_shortlist_parquet

    cost = COST_BPS if cost_bps is None else float(cost_bps)
    result = meta_labeler(panel, market, n_splits=n_splits, placebo_seeds=placebo_seeds)
    result["cleared"] = True

    shortlist, meta_info = build_shortlist(panel, result, market, cost_bps=cost)
    path = write_shortlist_parquet(shortlist, market, out_dir=out_dir)
    meta_info["path"] = str(path)
    report = _write_report(result, market, meta_info, out_dir=out_dir)
    result["report"] = str(report)
    result["shortlist"] = shortlist
    result["shortlist_meta"] = meta_info
    return result


def run_market(
    market: str,
    *,
    allow_fixture: bool = False,
    max_symbols: int | None = None,
    n_splits: int = 5,
    placebo_seeds: int = N_PLACEBO_SEEDS,
    cost_bps: float | None = None,
    out_dir: Path = REPORTS_DIR,
) -> dict:
    """Build one market's panel and emit the step-6 artifacts — only if cleared.

    The addendum gate is enforced in code: a market whose honest-edge verdict is
    not CLEAR returns immediately and writes nothing (no panel is even built).
    """
    if not market_cleared(market, out_dir):
        return {"market": market, "cleared": False, "targets": {}, "report": None,
                "shortlist": None, "shortlist_meta": None}
    panel = build_meta_panel(market, allow_fixture=allow_fixture, max_symbols=max_symbols)
    return emit(panel, market, n_splits=n_splits, placebo_seeds=placebo_seeds,
                cost_bps=cost_bps, out_dir=out_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="WI-016 step 6 meta-labeler + actions")
    add_market_argument(parser)
    parser.add_argument("--allow-fixture", action="store_true")
    parser.add_argument("--max-symbols", type=int, default=None,
                        help="Debug bound on symbols per market (default: all).")
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--placebo-seeds", type=int, default=N_PLACEBO_SEEDS)
    parser.add_argument("--cost-bps", type=float, default=None)
    args = parser.parse_args(argv)

    markets = cli_markets(args.market, prog="wi016.meta_labeler")
    if markets is None:
        return 2
    for mkt in markets:
        res = run_market(mkt, allow_fixture=args.allow_fixture, max_symbols=args.max_symbols,
                         n_splits=args.n_splits, placebo_seeds=args.placebo_seeds,
                         cost_bps=args.cost_bps)
        if not res.get("cleared"):
            print(f"[wi016.meta_labeler] {mkt}: NOT_CLEAR at the addendum gate — nothing written")
            continue
        print(f"[wi016.meta_labeler] {mkt}: report -> {res['report']}")
        print(f"[wi016.meta_labeler] {mkt}: shortlist -> {res['shortlist_meta']['path']} "
              f"({res['shortlist_meta']['n_rows']} rows, "
              f"{res['shortlist_meta']['n_trade']} TRADE)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
