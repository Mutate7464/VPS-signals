"""WI-018 step 2 (G1) — the guaranteed descriptive condition atlas for `first_touch_34`.

What G1 delivers, unconditionally
---------------------------------
For **every** pruned feature (88 `keep_columns`) and **both** binnings (quintile
and tercile, D-018 Q1) the atlas reports the conditional distribution of
`first_touch_34` — up-first / down-first / neither — against the unconditional
split, with 95% margins from the WI-015 circular block bootstrap (20-date
blocks, 1,000 draws, seed 42). States are within-date USD cross-sectional
quantiles: "top quintile of `atr_pct_34` today, relative to its peers today".

Honesty rules baked into the artifact:

* every (feature, binning, bin) cell is either estimable or **explicitly marked
  unevaluable** with its reason (`n` or `n_dates` too small) — no silent gaps;
* estimable rates are finite and sum to 1 within tolerance (self-checked);
* a state's cross-sectional breadth is reported (distinct symbols contributing,
  largest single-symbol share) so a 3-name artifact cannot masquerade as a
  condition;
* the three flagged feature families (`atr_pct`, `fib_dist`, `range_pos`) get an
  explicit **target-representativeness** check: the surviving column's
  within-date rank IC against this target as a share of its family's best,
  because the run-5 prune left exactly one window for each of them.

G1 produces no verdict on signal and spends no multiple-testing budget — it is
descriptive. Gating happens in G2 (`src/wi018/probe.py`).

CLI::

    python -m src.wi018.atlas --market USD                        # run + write + self-check
    python -m src.wi018.atlas --market USD --check-report reports/wi018/atlas_USD.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.wi018 import (
    ATLAS_JSON,
    ATLAS_MD,
    BINNINGS,
    DATES_PER_BLOCK,
    DERIVED_DIR,
    FEATURES_DIR,
    MARKET,
    MIN_GROUP_DATES,
    MIN_GROUP_N,
    PREFLIGHT_JSON,
    PRIMARY_TARGET,
    PRUNE_RECS,
    REPORTS_DIR,
)
from src.wi018.data_probe import PreflightError, load_keep_columns, require_preflight, symbol_paths
from src.wi018.rates import RATE_SUM_TOL, rate_block, sums_to_one, unconditional_block
from src.wi018.streaming import (
    BINNING_ORDER,
    CLASSES,
    N_STATES,
    QUANTILES,
    STATE_OFFSET,
    SYMBOL_COLUMN,
    binning_index,
    classify_target,
    date_blocks,
    edges_from_sorted,
    feature_columns,
    feature_families,
    global_dates,
    group_sorted,
    read_block_pairs,
    schema_columns,
    state_codes,
    state_layout,
)

__all__ = [
    "FLAGGED_FAMILIES",
    "assemble_report",
    "check_atlas_report",
    "collect_state_counts",
    "family_representativeness",
    "format_markdown",
    "main",
    "run_atlas",
    "write_report",
]

FLAGGED_FAMILIES = ("atr_pct", "fib_dist", "range_pos")
"""Families left with a single window by the run-5 prune — its stated caveat."""

FAMILY_REPRESENTATIVE_SHARE = 0.90
"""The kept column counts as family-representative at >= 90% of the family's best |IC|."""


# --------------------------------------------------------------------------- #
# Streaming pass: per-date state counts
# --------------------------------------------------------------------------- #
def collect_state_counts(
    derived_paths: dict[str, Path],
    feature_paths: dict[str, Path],
    keep_columns: list[str],
    dates: np.ndarray,
    target: str = PRIMARY_TARGET,
    block_size: int | None = None,
) -> dict:
    """Accumulate per-(feature, state, class, date) counts and breadth diagnostics.

    One symbol-sequential pass over date blocks; only block-sized frames are held.
    Returns numpy accumulators (the caller derives rates and JSON):

    * `state_counts`   `(n_features, N_STATES, 3, n_dates)` int32
    * `feature_totals` `(n_features, n_dates)` int32 — rows with a defined state
    * `universe`       `(3, n_dates)` int32 — all-names class counts
    * `other`          `(n_dates,)` int32 — finite target values outside {+1,0,-1}
    * `state_symbols`  `(n_features, N_STATES, n_symbols)` int32 — breadth
    """
    n_dates = int(dates.size)
    n_features = len(keep_columns)
    symbols = sorted(derived_paths)
    state_counts = np.zeros((n_features, N_STATES, len(CLASSES), n_dates), dtype=np.int32)
    feature_totals = np.zeros((n_features, len(BINNING_ORDER), n_dates), dtype=np.int32)
    universe = np.zeros((len(CLASSES), n_dates), dtype=np.int32)
    other = np.zeros(n_dates, dtype=np.int32)
    state_symbols = np.zeros((n_features, N_STATES, len(symbols)), dtype=np.int32)

    date_index = pd.Index(dates)
    blocks = date_blocks(dates, size=block_size or DATES_PER_BLOCK)
    for block in blocks:
        pair = read_block_pairs(derived_paths, feature_paths, keep_columns, [target], block["lo"], block["hi"])
        if pair is None:
            continue
        feats, tgts = pair
        pos = date_index.get_indexer(feats["date"].to_numpy())
        target_values = tgts[target].to_numpy(dtype="float64")
        classes = classify_target(target_values)
        sym_codes = feats[SYMBOL_COLUMN].to_numpy(dtype="int64")
        del tgts
        for k in range(len(CLASSES)):
            rows = pos[classes == k]
            if rows.size:
                universe[k] += np.bincount(rows, minlength=n_dates)
        # finite target values outside {+1, 0, -1}: counted, never folded in
        unexpected_rows = pos[(classes < 0) & np.isfinite(target_values)]
        if unexpected_rows.size:
            other += np.bincount(unexpected_rows, minlength=n_dates)
        for fi, col in enumerate(keep_columns):
            v = feats[col].to_numpy(dtype="float64")
            xs, starts, sizes = group_sorted(v, pos, n_dates)
            for binning, quantiles in QUANTILES.items():
                min_names = BINNINGS[binning]
                edges = edges_from_sorted(xs, starts, sizes, quantiles, min_names)
                codes = state_codes(v, edges, pos, offset=STATE_OFFSET[binning])
                defined = (codes >= 0) & (classes >= 0)  # usable target so class rates sum to 1
                if not defined.any():
                    continue
                c = codes[defined].astype("int64")
                p = pos[defined]
                feature_totals[fi, binning_index(binning)] += np.bincount(p, minlength=n_dates)
                bucket = p * N_STATES + c
                for k in range(len(CLASSES)):
                    mask = classes[defined] == k
                    if not mask.any():
                        continue
                    per_date = np.bincount(bucket[mask], minlength=n_dates * N_STATES)
                    state_counts[fi, :, k, :] += per_date.reshape(n_dates, N_STATES).T
                sym_bucket = c * len(symbols) + sym_codes[defined]
                state_symbols[fi] += np.bincount(sym_bucket, minlength=N_STATES * len(symbols)).reshape(
                    N_STATES, len(symbols)
                )
        del feats
    return {
        "state_counts": state_counts,
        "feature_totals": feature_totals,
        "universe": universe,
        "other": other,
        "state_symbols": state_symbols,
        "n_dates": n_dates,
        "symbols": symbols,
    }


# --------------------------------------------------------------------------- #
# Report assembly
# --------------------------------------------------------------------------- #
def assemble_report(counts: dict, keep_columns: list[str], dates: np.ndarray, preflight: dict) -> dict:
    """Derive rates/lifts from the accumulators into the JSON payload."""
    universe = counts["universe"]
    totals_universe = universe.sum(axis=0).astype("float64")
    rows_universe = int(totals_universe.sum())
    unconditional = {PRIMARY_TARGET: unconditional_block(universe, totals_universe, rows_universe)}
    base_up = unconditional[PRIMARY_TARGET]["rates"]["up"]
    base_dn = unconditional[PRIMARY_TARGET]["rates"]["dn"]

    features: dict[str, dict] = {}
    for fi, feature in enumerate(keep_columns):
        entry = {"family": feature.rsplit("_", 1)[0], "states": {}}
        for binning, n_bins in BINNINGS.items():
            offset = STATE_OFFSET[binning]
            cells = []
            for b in range(n_bins):
                code = offset + b
                state_dates_counts = counts["state_counts"][fi, code]
                state_rows_per_date = state_dates_counts.sum(axis=0)  # conditional denominator
                cell = rate_block(state_dates_counts, state_rows_per_date, int(state_dates_counts.sum()))
                cell["eligible_rows"] = int(counts["feature_totals"][fi, binning_index(binning)].sum())
                symbol_counts = counts["state_symbols"][fi, code]
                total_symbol_rows = int(symbol_counts.sum())
                cell.update(
                    {
                        "binning": binning,
                        "bin": b + 1,
                        "code": code,
                        "lift": {
                            "up": float(cell["rates"]["up"] - base_up),
                            "dn": float(cell["rates"]["dn"] - base_dn),
                        },
                        "breadth": {
                            "symbols": int((symbol_counts > 0).sum()),
                            "max_symbol_share": (
                                float(symbol_counts.max() / total_symbol_rows) if total_symbol_rows else float("nan")
                            ),
                        },
                    }
                )
                cells.append(cell)
            entry["states"][binning] = cells
        features[feature] = entry

    unexpected_rows = int(counts["other"].sum())
    return {
        "step": "WI-018 step 2 (G1) condition atlas",
        "market": MARKET,
        "scope": "USD only — CAD skipped (D-018 Q2)",
        "generated_utc": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "target": PRIMARY_TARGET,
        "input_provenance": {
            "preflight_report": str(PREFLIGHT_JSON),
            "preflight_verdict": preflight.get("verdict"),
            "symbols": preflight.get("summary", {}).get("symbols"),
            "derived_dir": preflight.get("config", {}).get("derived_dir"),
            "features_dir": preflight.get("config", {}).get("features_dir"),
            "prune_recs": preflight.get("config", {}).get("prune_recs"),
            "target_rows_used": rows_universe,
        },
        "summary": {
            "rows": rows_universe,
            "unexpected_target_rows": unexpected_rows,
            "symbols": len(counts["symbols"]),
            "date_min": str(pd.Timestamp(dates.min()).date()),
            "date_max": str(pd.Timestamp(dates.max()).date()),
            "n_dates": int(dates.size),
        },
        "config": {
            "features": list(keep_columns),
            "n_features": len(keep_columns),
            "binnings": dict(BINNINGS),
            "state_quantiles": {k: list(v) for k, v in QUANTILES.items()},
            "state_layout": [{"binning": b, "bin": i + 1, "code": c} for b, i, c in state_layout()],
            "tie_rule": "code = #{edge < value} — ties go to the upper bin",
            "min_names_per_date": dict(BINNINGS),
            "min_group_n": int(MIN_GROUP_N),
            "min_group_dates": int(MIN_GROUP_DATES),
            "rate_sum_tolerance": RATE_SUM_TOL,
            "bootstrap": "circular 20-date blocks, 1000 draws, seed 42 (block_bootstrap_margin)",
            "folds": "not used in G1 (descriptive); G2 applies fold_blocks with embargo max(20, 34)",
        },
        "unconditional": unconditional,
        "features": features,
        "family_representativeness": {},
        "coverage": {},
        "checks": {},
        "verdict": "PASS",
    }


def _coverage(report: dict) -> dict:
    estimable = unevaluable = 0
    features_without = []
    for feature, entry in report["features"].items():
        has_estimable = False
        for binning in BINNINGS:
            for cell in entry["states"][binning]:
                if cell["estimable"]:
                    estimable += 1
                    has_estimable = True
                else:
                    unevaluable += 1
        if not has_estimable:
            features_without.append(feature)
    total = estimable + unevaluable
    return {
        "cells_total": total,
        "cells_estimable": estimable,
        "cells_unevaluable": unevaluable,
        "unevaluable_share": float(unevaluable / total) if total else float("nan"),
        "features_without_estimable_cells": features_without,
    }


# --------------------------------------------------------------------------- #
# Flagged-family representativeness
# --------------------------------------------------------------------------- #
def family_representativeness(
    derived_paths: dict[str, Path],
    feature_paths: dict[str, Path],
    keep_columns: list[str],
    dates: np.ndarray,
    block_size: int | None = None,
    families: tuple[str, ...] = FLAGGED_FAMILIES,
    target: str = PRIMARY_TARGET,
) -> dict:
    """Is the surviving column of each flagged family representative for THIS target?

    For `atr_pct`, `fib_dist` and `range_pos` the run-5 prune kept exactly one
    window (its stated caveat). This pass scores *every* column of those families
    with the WI-015 estimator (`daily_spearman_ic`, imported — not reimplemented)
    against `first_touch_34` over the whole USD universe, then reports the kept
    column's |mean IC| as a share of the family's best |mean IC|. `representative`
    is True only when that share clears `FAMILY_REPRESENTATIVE_SHARE` **and** the
    kept column carries the family best's sign — a sign-flipped window describes
    the family's signal backwards, which is not representation.
    """
    from src.perfanalytics.correlation.alignment import daily_spearman_ic

    families_map = feature_families(schema_columns(next(iter(feature_paths.values()))))
    series: dict[str, list[np.ndarray]] = {}
    for family in families:
        for col in families_map.get(family, []):
            series.setdefault(col, [])

    blocks = date_blocks(dates, size=block_size or DATES_PER_BLOCK)
    for block in blocks:
        wanted = [col for family in families for col in families_map.get(family, [])]
        if not wanted:
            break
        pair = read_block_pairs(derived_paths, feature_paths, wanted, [target], block["lo"], block["hi"])
        if pair is None:
            continue
        feats, tgts = pair
        feats = feats.drop(columns=[SYMBOL_COLUMN])
        frame = feats.copy()
        frame[target] = tgts[target].to_numpy()
        ics = daily_spearman_ic(frame, [target], wanted)[target]
        for j, col in enumerate(wanted):
            values = ics[:, j]
            values = values[np.isfinite(values)]
            if values.size:
                series[col].append(values)
        del frame, feats, tgts

    out: dict[str, dict] = {}
    for family in families:
        columns = families_map.get(family, [])
        stats = {}
        for col in columns:
            parts = series.get(col, [])
            values = np.concatenate(parts) if parts else np.array([])
            mean_ic = float(values.mean()) if values.size else float("nan")
            stats[col] = {"mean_ic": mean_ic, "abs_ic": abs(mean_ic) if np.isfinite(mean_ic) else float("nan"),
                          "n_dates": int(values.size)}
        finite = {c: s for c, s in stats.items() if np.isfinite(s["abs_ic"])}
        best_col = max(finite, key=lambda c: finite[c]["abs_ic"]) if finite else None
        best_abs = finite[best_col]["abs_ic"] if best_col else float("nan")
        best_sign = float(np.sign(finite[best_col]["mean_ic"])) if best_col else 0.0
        kept = [c for c in columns if c in keep_columns]
        kept_col = kept[0] if kept else None
        kept_abs = stats.get(kept_col, {}).get("abs_ic", float("nan")) if kept_col else float("nan")
        kept_mean = stats.get(kept_col, {}).get("mean_ic", float("nan")) if kept_col else float("nan")
        share = float(kept_abs / best_abs) if (best_col and np.isfinite(best_abs) and best_abs > 0) else float("nan")
        same_sign = bool(
            best_col and np.isfinite(kept_mean) and best_sign != 0.0 and np.sign(kept_mean) == best_sign
        )
        out[family] = {
            "kept_column": kept_col,
            "kept_abs_ic": kept_abs,
            "kept_mean_ic": kept_mean,
            "family_best_column": best_col,
            "family_best_abs_ic": best_abs,
            "retained_share": share,
            "same_sign_as_family_best": same_sign,
            "representative": bool(np.isfinite(share) and share >= FAMILY_REPRESENTATIVE_SHARE and same_sign),
            "n_columns": len(columns),
            "estimator": f"within-date Spearman rank IC vs {target}, all USD dates (pairwise-complete, >=3 names/date)",
            "columns": stats,
        }
    return out


# --------------------------------------------------------------------------- #
# Acceptance self-check
# --------------------------------------------------------------------------- #
def _is_finite_number(value) -> bool:
    """True for a value that is a finite real number (report payloads may hold junk)."""
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def check_atlas_report(report: dict) -> dict:
    """Acceptance self-check for an atlas report; returns `{name: (ok, detail)}`."""
    checks: dict[str, tuple[bool, str]] = {}
    features = report.get("features", {})
    expected = report.get("config", {}).get("features", [])
    checks["all_features_present"] = (
        sorted(features) == sorted(expected) and bool(expected),
        f"{len(features)} reported vs {len(expected)} expected",
    )
    cell_ok, cell_detail = True, ""
    rates_ok, rates_detail = True, ""
    ci_ok, ci_detail = True, ""
    for feature, entry in features.items():
        for binning, n_bins in BINNINGS.items():
            cells = entry.get("states", {}).get(binning, [])
            if len(cells) != n_bins:
                cell_ok, cell_detail = False, f"{feature}/{binning}: {len(cells)} cells != {n_bins}"
                continue
            for cell in cells:
                if cell.get("estimable"):
                    if not sums_to_one(cell.get("rates", {}), RATE_SUM_TOL):
                        rates_ok, rates_detail = False, f"{feature}/{binning}/{cell.get('bin')}: rates do not sum to 1"
                    for cls in CLASSES:
                        ci = cell.get("ci", {}).get(cls, {})
                        if not (_is_finite_number(ci.get("ci_low")) and _is_finite_number(ci.get("ci_high"))):
                            ci_ok, ci_detail = False, f"{feature}/{binning}/{cell.get('bin')}/{cls}: CI missing"
                elif not cell.get("unevaluable_reason"):
                    cell_ok, cell_detail = False, f"{feature}/{binning}/{cell.get('bin')}: unevaluable without reason"
    checks["cells_represented_or_marked"] = (cell_ok, cell_detail or f"{len(features) * 8} cells present")
    checks["estimable_rates_sum_to_one"] = (rates_ok, rates_detail or f"tolerance {RATE_SUM_TOL:g}")
    checks["cis_present"] = (ci_ok, ci_detail or "all estimable cells carry finite 95% bounds")
    fam = report.get("family_representativeness", {})
    fam_ok = bool(fam) and all(name in fam and fam[name].get("representative") in (True, False) for name in FLAGGED_FAMILIES)
    checks["flagged_families_checked"] = (fam_ok, ", ".join(sorted(fam)) or "none")
    unconditional = report.get("unconditional", {}).get(PRIMARY_TARGET, {})
    checks["unconditional_split_present"] = (
        bool(unconditional) and sums_to_one(unconditional.get("rates", {}), RATE_SUM_TOL),
        f"rates={ {k: round(v, 4) for k, v in unconditional.get('rates', {}).items()} }",
    )
    return checks


def summarize_checks(checks: dict) -> str:
    return "\n".join(f"  {'OK  ' if ok else 'FAIL'} {name}: {detail}" for name, (ok, detail) in checks.items())


# --------------------------------------------------------------------------- #
# Markdown
# --------------------------------------------------------------------------- #
def _fmt(value) -> str:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return "n/a"
    return "n/a" if not np.isfinite(f) else f"{f:.4f}"


def format_markdown(report: dict) -> str:
    """Human-readable atlas summary (top states by |lift| per binning)."""
    lines = [
        f"# WI-018 G1 condition atlas — `{PRIMARY_TARGET}` ({report['market']})",
        "",
        f"Generated {report['generated_utc']}. Inputs: {report['summary']['symbols']} symbols, "
        f"{report['summary']['rows']} rows, {report['summary']['date_min']}..{report['summary']['date_max']} "
        f"({report['summary']['n_dates']} dates).",
        "Descriptive only — no pass/fail and no multiple-testing budget is spent in G1.",
        "",
        "## Unconditional split (reference)",
        "",
        "| class | pooled | date-mean | 95% CI |",
        "|---|---|---|---|",
    ]
    unc = report["unconditional"][PRIMARY_TARGET]
    for cls in CLASSES:
        ci = unc["ci"][cls]
        lines.append(
            f"| {cls} | {unc['pooled'][cls]:.4f} | {unc['date_mean'][cls]:.4f} | "
            f"[{ci['ci_low']:.4f}, {ci['ci_high']:.4f}] |"
        )
    lines += [
        "",
        "States are within-date USD cross-sectional quantiles (ties go to the upper bin); "
        f"bootstrap: {report['config']['bootstrap']}.",
        "",
    ]
    for binning in BINNINGS:
        rows = []
        for feature, entry in report["features"].items():
            for cell in entry["states"].get(binning, []):
                if cell.get("estimable"):
                    rows.append((abs(cell["lift"]["up"]) + abs(cell["lift"]["dn"]), feature, cell))
        rows.sort(key=lambda r: r[0], reverse=True)
        lines += [
            f"## Top conditions by |lift| — {binning} (up to 12)",
            "",
            "| feature | bin | n | n_dates | symbols | up rate | up lift | dn rate | dn lift | neither |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
        for _score, feature, cell in rows[:12]:
            lines.append(
                f"| {feature} | {cell['bin']} | {cell['n']} | {cell['n_dates']} | {cell['breadth']['symbols']} | "
                f"{cell['rates']['up']:.4f} | {cell['lift']['up']:+.4f} | "
                f"{cell['rates']['dn']:.4f} | {cell['lift']['dn']:+.4f} | {cell['rates']['neither']:.4f} |"
            )
        if not rows:
            lines.append("| (none estimable) | | | | | | | | | |")
        lines.append("")
    cov = report["coverage"]
    lines += [
        "## Coverage",
        "",
        f"- cells: {cov['cells_total']} total, {cov['cells_estimable']} estimable, "
        f"{cov['cells_unevaluable']} unevaluable ({cov['unevaluable_share']:.3f}).",
        f"- features without any estimable cell: {cov['features_without_estimable_cells'] or 'none'}.",
        f"- rows with a target value outside {{+1, 0, -1}}: {report['summary']['unexpected_target_rows']} "
        "(excluded from every rate, never folded into 'neither').",
        "",
        "## Flagged family representativeness",
        "",
        "| family | kept column | kept \\|IC\\| | family best | best column | share | representative |",
        "|---|---|---|---|---|---|---|",
    ]
    for family in FLAGGED_FAMILIES:
        entry = report["family_representativeness"].get(family, {})
        lines.append(
            f"| {family} | {entry.get('kept_column')} | {_fmt(entry.get('kept_abs_ic'))} | "
            f"{_fmt(entry.get('family_best_abs_ic'))} | {entry.get('family_best_column')} | "
            f"{_fmt(entry.get('retained_share'))} | {entry.get('representative')} |"
        )
    lines += [
        "",
        f"`representative=true` means the surviving column retains at least "
        f"{FAMILY_REPRESENTATIVE_SHARE:.0%} of its family's best |IC| against this target, so its atlas states "
        "are not a prune artifact; `false` means treat that family's conditions as single-window evidence.",
        "",
        "## Self-check",
        "",
        "```",
        summarize_checks(check_atlas_report(report)),
        "```",
        "",
        "No executable rules, no shortlist, no trading integration — G1 is a description.",
        "",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run_atlas(
    deriv_dir: Path = DERIVED_DIR,
    feat_dir: Path = FEATURES_DIR,
    prune_path: Path | None = None,
    preflight_path: Path = PREFLIGHT_JSON,
    block_size: int | None = None,
    market: str = MARKET,
    flagged_families: tuple[str, ...] = FLAGGED_FAMILIES,
) -> dict:
    """Run the G1 atlas end to end and return the report payload."""
    if market.upper() != MARKET:
        raise PreflightError(f"WI-018 is USD-only (got {market!r}); CAD is skipped per D-018 Q2")
    preflight = require_preflight(preflight_path, market)
    keep_columns = load_keep_columns(prune_path or PRUNE_RECS)
    derived_paths = symbol_paths(deriv_dir)
    feature_paths = symbol_paths(feat_dir)
    dates = global_dates(deriv_dir)
    counts = collect_state_counts(derived_paths, feature_paths, keep_columns, dates, block_size=block_size)
    report = assemble_report(counts, keep_columns, dates, preflight)
    report["family_representativeness"] = family_representativeness(
        derived_paths, feature_paths, keep_columns, dates, block_size=block_size, families=flagged_families
    )
    report["coverage"] = _coverage(report)
    checks = check_atlas_report(report)
    report["checks"] = {name: {"ok": bool(ok), "detail": detail} for name, (ok, detail) in checks.items()}
    report["verdict"] = "PASS" if all(ok for ok, _ in checks.values()) else "FAIL"
    return report


def write_report(report: dict, json_path: Path = ATLAS_JSON, md_path: Path = ATLAS_MD) -> tuple[Path, Path]:
    json_path = Path(json_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=1, default=str))
    Path(md_path).write_text(format_markdown(report))
    return json_path, Path(md_path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="WI-018 G1 condition atlas (USD)")
    ap.add_argument("--market", default=MARKET)
    ap.add_argument("--check-report", default=None,
                    help="verify an existing atlas report against the acceptance criteria instead of running")
    ap.add_argument("--out", default=str(ATLAS_JSON))
    ap.add_argument("--md", default=str(ATLAS_MD))
    ap.add_argument("--block-size", type=int, default=None)
    args = ap.parse_args(argv)

    if args.check_report:
        path = Path(args.check_report)
        if not path.is_file():
            print(f"ATLAS CHECK FAIL: report missing ({path})")
            return 1
        report = json.loads(path.read_text())
        checks = check_atlas_report(report)
        print(f"WI-018 atlas report check [{report.get('market')}] verdict={report.get('verdict')}")
        print(summarize_checks(checks))
        ok = all(ok for ok, _ in checks.values())
        print(f"ATLAS CHECK {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1

    try:
        report = run_atlas(block_size=args.block_size, market=args.market)
    except PreflightError as exc:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"ATLAS FAIL: {exc}")
        return 1
    json_path, md_path = write_report(report, Path(args.out), Path(args.md))
    print(f"WI-018 atlas [{report['market']}] verdict={report['verdict']} -> {json_path}, {md_path}")
    print(summarize_checks(check_atlas_report(report)))
    cov = report["coverage"]
    print(
        f"  cells={cov['cells_total']} estimable={cov['cells_estimable']} "
        f"unevaluable={cov['cells_unevaluable']} ({cov['unevaluable_share']:.3f})"
    )
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
