"""WI-018 step 3 (G2) — the falsification probe for `first_touch_34` conditions.

What G2 asks, once, and what makes "no" credible
------------------------------------------------
Using the **same** within-date cross-sectional states as the G1 atlas, G2 tests
whether any condition's first-touch *direction* rate differs from the
unconditional split **out of sample**:

1. **Folds** — five chronological held-out blocks from `src.wi011.stats.fold_blocks`
   (the WI-011/WI-015 geometry) with embargo `max(20, 34) = 34` sessions, trimmed
   to `val_pos_min..label_end_pos` so a forward label can never straddle a block.
   Only held-out dates ever enter a statistic.
2. **Univariate family** — every state (88 features × 5 quintile + 3 tercile
   bins = 704) × 2 directions (`up`, `dn`) = 1,408 hypotheses. A hypothesis is
   the lift of the condition's per-date class rate over the unconditional
   per-date rate on the same dates.
3. **Conjunctions** — AND-pairs built **only** from states whose univariate
   hypothesis survived BH-FDR (capped at the 50 best, different features, max
   pair count 1,225), tested in both directions and folded into the *same*
   correction family.
4. **Correction** — one `src.wi016.probe.benjamini_hochberg` pass at 5% over the
   complete family (univariate + conjunctions).
5. **Evidence per hypothesis** — mean out-of-fold lift with a 95% margin from the
   WI-015 circular block bootstrap (20-date blocks, 1,000 draws, seed 42), the
   WI-009b same-sign clause (`_same_sign_from_series`, reused), and per-fold
   lifts so a survivor that only works in one block is visible.

**G2 passes** only if at least one condition has a CI excluding zero, passes
BH-FDR 5%, *and* clears the same-sign bar. Survivor density above
`SURVIVOR_DENSITY_RED_FLAG` is reported as a **red flag** (a wall of survivors is
noise or leakage, not a win), and a G2 failure marks G3 skipped.

`first_touch_34` decides everything; `first_touch_24`/`39` are **robustness reads
only** and never enter selection.

CLI::

    python -m src.wi018.probe --market USD
    python -m src.wi018.probe --market USD --check-report reports/wi018/probe_USD.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.wi011.stats import MIN_N, fold_blocks
from src.wi016.probe import _pvalue as normal_pvalue
from src.wi016.probe import _same_sign_from_series
from src.wi016.probe import benjamini_hochberg
from src.wi018 import (
    BINNINGS,
    BOOTSTRAP_BLOCK_DATES,
    BOOTSTRAP_DRAWS,
    BOOTSTRAP_SEED,
    DERIVED_DIR,
    FDR_ALPHA,
    FEATURES_DIR,
    HORIZON,
    MARKET,
    MIN_GROUP_DATES,
    PREFLIGHT_JSON,
    PRIMARY_TARGET,
    PROBE_JSON,
    PROBE_MD,
    PRUNE_RECS,
    REPORTS_DIR,
    SECONDARY_TARGETS,
)
from src.wi018.data_probe import PreflightError, load_keep_columns, require_preflight, symbol_paths
from src.wi018.rates import ci_from_series, date_mean, sums_to_one
from src.wi018.streaming import (
    BINNING_ORDER,
    CLASSES,
    STATE_OFFSET,
    binning_of_code,
    global_dates,
    state_label,
    stream_conjunction_counts,
    stream_state_counts,
)

__all__ = [
    "DIRECTIONS",
    "FLAG",
    "MAX_CONJUNCTION_PAIRS",
    "MIN_NAMES_PER_DATE",
    "N_FOLDS",
    "SD_REL_FLOOR",
    "SURVIVOR_DENSITY_RED_FLAG",
    "TOP_SURVIVOR_STATES",
    "check_probe_report",
    "conjunction_pairs",
    "format_markdown",
    "held_out_positions",
    "hypothesis_stats",
    "main",
    "run_probe",
    "univariate_hypotheses",
]

DIRECTIONS = ("up", "dn")
"""Tested directions; the ordinal target only has up-first / down-first edges."""

DIRECTION_CLASS = {"up": 0, "dn": 1}
"""Index into `src.wi018.streaming.CLASSES` for each tested direction."""

N_FOLDS = 5
INITIAL_TRAIN_FRACTION = 0.40
MIN_NAMES_PER_DATE = 3
"""A date enters a condition's series only with at least this many condition rows."""

TOP_SURVIVOR_STATES = 50
"""Univariate survivors used to build conjunctions (the ADR's ~50 -> ~1,200 pairs)."""

MAX_CONJUNCTION_PAIRS = 1225
"""C(50, 2) — the pre-registered conjunction-family ceiling."""

SURVIVOR_DENSITY_RED_FLAG = 0.10
"""Above this share of surviving hypotheses the probe reports a red flag, not a win."""

MIN_HOLDOUT_DATES = 60
"""Below this many held-out dates the out-of-fold evidence is reported unevaluable."""

# --------------------------------------------------------------------------- #
# Folds
# --------------------------------------------------------------------------- #
def held_out_positions(
    dates: np.ndarray,
    horizon: int = HORIZON,
    n_splits: int = N_FOLDS,
    initial_train_fraction: float = INITIAL_TRAIN_FRACTION,
) -> tuple[np.ndarray, list[dict]]:
    """Held-out date positions and per-fold details (embargo `max(20, horizon)`).

    `fold_blocks` returns each fold's validation positions plus `label_end_pos`,
    the last position whose forward window ends inside the block; those two
    bounds together are the held-out window, so overlapping labels never cross a
    fold boundary.
    """
    dates = np.asarray(dates)
    folds = fold_blocks(dates, horizon=horizon, n_splits=n_splits, initial_train_fraction=initial_train_fraction)
    mask = np.zeros(dates.size, dtype=bool)
    detail = []
    for record in folds:
        lo, hi = int(record["val_pos_min"]), int(record["label_end_pos"])
        if hi < lo:
            continue
        mask[lo : hi + 1] = True
        detail.append(
            {
                "fold": int(record["fold"]),
                "embargo_td": int(record["embargo_td"]),
                "val_pos_min": lo,
                "val_pos_max": int(record["val_pos_max"]),
                "label_end_pos": hi,
                "held_dates": hi - lo + 1,
                "val_min": str(pd.Timestamp(dates[lo]).date()),
                "val_max": str(pd.Timestamp(dates[hi]).date()),
            }
        )
    return mask, detail


# --------------------------------------------------------------------------- #
# Hypothesis statistics
# --------------------------------------------------------------------------- #
SD_REL_FLOOR = 1e-9
"""A lift series with (essentially) no dispersion carries no estimable evidence."""


def _t_stat(series: np.ndarray) -> tuple[float, float]:
    """`(t, p)` for a per-date mean series (date-clustered, normal approximation)."""
    n = series.size
    if n < 3:
        return float("nan"), float("nan")
    mean = float(series.mean())
    sd = float(series.std(ddof=1))
    # A series that is identical on every date must never masquerade as an
    # infinitely significant finding: `std` is only exactly 0 when the mean is
    # exactly representable, so a (near-)constant series is rejected explicitly.
    if not np.isfinite(sd) or float(series.max()) == float(series.min()) or sd <= abs(mean) * SD_REL_FLOOR:
        return float("nan"), float("nan")
    t = float(mean / (sd / np.sqrt(n)))
    return t, normal_pvalue(t, int(n))


def hypothesis_stats(
    counts_cls: np.ndarray,
    totals: np.ndarray,
    unc_cls: np.ndarray,
    unc_tot: np.ndarray,
    held: np.ndarray,
    fold_bounds: list[dict] | None = None,
    min_names: int = MIN_NAMES_PER_DATE,
    min_holdout_dates: int = MIN_HOLDOUT_DATES,
) -> dict:
    """Out-of-fold lift, CI, p-value and same-sign flag for one (condition, direction).

    `counts_cls`/`totals` are the condition's per-date class counts and per-date
    size; `unc_cls`/`unc_tot` the unconditional reference on the same dates. The
    lift series is `rate_cond − rate_unc`; only dates with at least `min_names`
    condition rows and a usable unconditional rate are kept.
    """
    counts_cls = np.asarray(counts_cls, dtype="float64")
    totals = np.asarray(totals, dtype="float64")
    unc_cls = np.asarray(unc_cls, dtype="float64")
    unc_tot = np.asarray(unc_tot, dtype="float64")
    with np.errstate(divide="ignore", invalid="ignore"):
        cond_rate = np.where(totals > 0, counts_cls / np.where(totals > 0, totals, np.nan), np.nan)
        unc_rate = np.where(unc_tot > 0, unc_cls / np.where(unc_tot > 0, unc_tot, np.nan), np.nan)
    lift = cond_rate - unc_rate
    valid = held & (totals >= min_names) & np.isfinite(lift)
    series = lift[valid]
    positions = np.nonzero(valid)[0]
    n = int(counts_cls[valid].sum()) if valid.any() else 0
    n_dates = int(series.size)
    record = {
        "n": n,
        "n_dates": n_dates,
        "held_out_rate": date_mean(cond_rate[valid]) if n_dates else float("nan"),
        "unconditional_rate": date_mean(unc_rate[valid]) if n_dates else float("nan"),
        "lift": float(series.mean()) if n_dates else float("nan"),
        "t": float("nan"),
        "p": float("nan"),
        "margin": float("nan"),
        "ci_low": float("nan"),
        "ci_high": float("nan"),
        "same_sign": False,
        "estimable": False,
        "unevaluable_reason": None,
        "per_fold_lift": [],
        "folds_same_sign": False,
    }
    if n_dates < MIN_GROUP_DATES or n < MIN_N or n_dates < min_holdout_dates:
        reasons = []
        if n_dates < MIN_GROUP_DATES:
            reasons.append(f"n_dates<{MIN_GROUP_DATES}")
        if n < MIN_N:
            reasons.append(f"n<{MIN_N}")
        if n_dates < min_holdout_dates:
            reasons.append(f"n_dates<{min_holdout_dates}")
        record["unevaluable_reason"] = " and ".join(reasons)
        return record
    t, p = _t_stat(series)
    ci = ci_from_series(series, n_draws=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED)
    record.update(
        {
            "t": t,
            "p": p,
            "margin": ci["margin"],
            "ci_low": ci["ci_low"],
            "ci_high": ci["ci_high"],
            "same_sign": bool(_same_sign_from_series(positions, series)),
            "estimable": bool(np.isfinite(p)),
        }
    )
    if not record["estimable"]:
        record["unevaluable_reason"] = "p-value undefined (zero dispersion or too few dates)"
    if fold_bounds:
        per_fold = []
        for fold in fold_bounds:
            lo, hi = fold["val_pos_min"], fold["label_end_pos"]
            mask = (positions >= lo) & (positions <= hi)
            per_fold.append(float(series[mask].mean()) if mask.any() else float("nan"))
        record["per_fold_lift"] = per_fold
        finite = [v for v in per_fold if np.isfinite(v)]
        record["folds_same_sign"] = bool(
            finite and any(v != 0.0 for v in finite) and len({np.sign(v) for v in finite}) == 1
        )
    return record


def _condition_label(feature: str, code: int) -> str:
    return f"{feature}|{state_label(binning_of_code(code), code)}"


def _passes(record: dict) -> bool:
    """The three stated criteria, in one place (BH rejection is added later)."""
    return bool(
        record.get("estimable")
        and record.get("same_sign")
        and np.isfinite(record.get("margin", np.nan))
        and abs(record.get("lift", np.nan)) > record.get("margin", np.nan)
    )


# --------------------------------------------------------------------------- #
# Univariate family
# --------------------------------------------------------------------------- #
def univariate_hypotheses(
    accumulators: dict,
    keep_columns: list[str],
    held: np.ndarray,
    fold_bounds: list[dict] | None = None,
    min_holdout_dates: int = MIN_HOLDOUT_DATES,
) -> list[dict]:
    """All 704 states × 2 directions for **one target's** accumulators, held-out dates only.

    Called once per target: `first_touch_34` decides, `first_touch_24`/`39` are
    scored with the identical code path so their reads are comparable — never as
    selection targets.
    """
    state_counts = accumulators["state_counts"]
    universe = accumulators["universe"].astype("float64")
    unc_tot = universe.sum(axis=0)
    out: list[dict] = []
    for fi, feature in enumerate(keep_columns):
        for binning in BINNING_ORDER:
            for b in range(BINNINGS[binning]):
                code = STATE_OFFSET[binning] + b
                totals = state_counts[fi, code].sum(axis=0).astype("float64")
                for direction in DIRECTIONS:
                    k = DIRECTION_CLASS[direction]
                    record = hypothesis_stats(
                        state_counts[fi, code, k],
                        totals,
                        universe[k],
                        unc_tot,
                        held,
                        fold_bounds=fold_bounds,
                        min_holdout_dates=min_holdout_dates,
                    )
                    record.update(
                        {
                            "kind": "univariate",
                            "condition": _condition_label(feature, code),
                            "feature": feature,
                            "feature_index": int(fi),
                            "binning": binning,
                            "bin": b + 1,
                            "code": int(code),
                            "direction": direction,
                            "state_share": float(totals.sum() / max(unc_tot.sum(), 1.0)),
                            "_index": len(out),
                        }
                    )
                    out.append(record)
    return out


def survivor_states(hypotheses: list[dict], cap: int = TOP_SURVIVOR_STATES) -> list[tuple[int, int]]:
    """`(feature_index, code)` of states whose univariate hypothesis survived BH.

    Ordered by best (smallest) p-value, capped at `cap` — the cap is what keeps
    the conjunction family near the pre-registered ~1,200 pairs.
    """
    best: dict[tuple[int, int], float] = {}
    for h in hypotheses:
        if h["kind"] != "univariate" or not h.get("reject"):
            continue
        key = (int(h["feature_index"]), int(h["code"]))
        p = float(h.get("q", h.get("p", np.nan)))
        if not np.isfinite(p):
            continue
        best[key] = min(best.get(key, np.inf), p)
    ordered = sorted(best.items(), key=lambda kv: (kv[1], kv[0]))
    return [key for key, _p in ordered[:cap]]


def conjunction_pairs(
    states: list[tuple[int, int]],
    features: list[str],
    cap: int = MAX_CONJUNCTION_PAIRS,
) -> list[tuple[int, int, int, int]]:
    """AND-pairs of survivor states from **different** features, capped at `cap`."""
    pairs: list[tuple[int, int, int, int]] = []
    for i, (fi_a, code_a) in enumerate(states):
        for fi_b, code_b in states[i + 1 :]:
            if fi_a == fi_b:
                continue
            pairs.append((fi_a, code_a, fi_b, code_b))
            if len(pairs) >= cap:
                return pairs
    return pairs


def _conjunction_hypotheses(
    pairs: list[tuple[int, int, int, int]],
    joint_by_target: dict,
    universes: dict[str, np.ndarray],
    keep_columns: list[str],
    held: np.ndarray,
    targets: tuple[str, ...],
    fold_bounds: list[dict] | None = None,
    min_holdout_dates: int = MIN_HOLDOUT_DATES,
) -> dict[str, list[dict]]:
    """Hypothesis records for every pair × direction, per target (34 decides).

    `joint_by_target` holds the pair-wise joint counts; `universes` holds each
    target's all-names class counts from the state-count pass, which is the
    unconditional reference a conjunction's lift is measured against.
    """
    out: dict[str, list[dict]] = {}
    for target in targets:
        joint = joint_by_target[target]["joint_counts"]
        universe = np.asarray(universes[target], dtype="float64")
        unc_tot = universe.sum(axis=0)
        records: list[dict] = []
        for pi, (fi_a, code_a, fi_b, code_b) in enumerate(pairs):
            totals = joint[pi].sum(axis=0).astype("float64")
            label = f"{_condition_label(keep_columns[fi_a], code_a)} & {_condition_label(keep_columns[fi_b], code_b)}"
            for direction in DIRECTIONS:
                k = DIRECTION_CLASS[direction]
                record = hypothesis_stats(
                    joint[pi, k], totals, universe[k], unc_tot, held,
                    fold_bounds=fold_bounds, min_holdout_dates=min_holdout_dates,
                )
                record.update(
                    {
                        "kind": "conjunction",
                        "condition": label,
                        "feature": f"{keep_columns[fi_a]} & {keep_columns[fi_b]}",
                        "binning": f"{binning_of_code(code_a)}x{binning_of_code(code_b)}",
                        "bin": None,
                        "code": None,
                        "pair": [int(fi_a), int(code_a), int(fi_b), int(code_b)],
                        "direction": direction,
                    }
                )
                records.append(record)
        out[target] = records
    return out


# --------------------------------------------------------------------------- #
# BH correction + verdict
# --------------------------------------------------------------------------- #
def _apply_bh(hypotheses: list[dict], alpha: float = FDR_ALPHA) -> dict:
    """One BH pass over the complete family; writes `p`/`q`/`reject` in place."""
    pvals = np.array([h.get("p", np.nan) if h.get("estimable") else np.nan for h in hypotheses], dtype="float64")
    reject, qvals = benjamini_hochberg(pvals, alpha)
    for h, r, q in zip(hypotheses, reject, qvals):
        h["reject"] = bool(r)
        h["q"] = float(q) if np.isfinite(q) else None
    return {
        "n_tested": int(np.isfinite(pvals).sum()),
        "n_rejected": int(reject.sum()),
        "min_p": float(np.nanmin(pvals)) if np.isfinite(pvals).any() else None,
        "alpha": float(alpha),
    }


def _robustness(hypothesis: dict, records_by_target: dict[str, list[dict]], index: int) -> dict:
    """Same condition under the secondary targets — reads only, never selection."""
    out = {}
    for target in SECONDARY_TARGETS:
        records = records_by_target.get(target)
        if records is None or index >= len(records):
            continue
        record = records[index]
        out[target] = {
            "lift": record["lift"],
            "ci_low": record["ci_low"],
            "ci_high": record["ci_high"],
            "n": record["n"],
            "n_dates": record["n_dates"],
            "same_sign": record["same_sign"],
            "passes_all_criteria": _passes(record),
            "note": "robustness read only — never an alternate selection target",
        }
    return out


def _unconditional_block(universe: np.ndarray, held: np.ndarray) -> dict:
    counts = np.asarray(universe, dtype="float64")[:, held]
    totals = counts.sum(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        per_date = np.where(totals > 0, counts / np.where(totals > 0, totals, np.nan), np.nan)
    block = {
        "n": int(counts.sum()),
        "n_dates": int(held.sum()),
        "rates": {c: date_mean(per_date[i]) for i, c in enumerate(CLASSES)},
        "pooled": {c: (float(counts[i].sum() / totals.sum()) if totals.sum() else float("nan"))
                   for i, c in enumerate(CLASSES)},
        "ci": {c: ci_from_series(per_date[i], n_draws=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED)
               for i, c in enumerate(CLASSES)},
    }
    return block


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run_probe(
    deriv_dir: Path = DERIVED_DIR,
    feat_dir: Path = FEATURES_DIR,
    prune_path: Path | None = None,
    preflight_path: Path = PREFLIGHT_JSON,
    block_size: int | None = None,
    market: str = MARKET,
    alpha: float = FDR_ALPHA,
    top_states: int = TOP_SURVIVOR_STATES,
    max_pairs: int = MAX_CONJUNCTION_PAIRS,
    min_holdout_dates: int = MIN_HOLDOUT_DATES,
) -> dict:
    """Run G2 end to end and return the report payload (no writes)."""
    if market.upper() != MARKET:
        raise PreflightError(f"WI-018 is USD-only (got {market!r}); CAD is skipped per D-018 Q2")
    preflight = require_preflight(preflight_path, market)
    keep_columns = load_keep_columns(prune_path or PRUNE_RECS)
    derived_paths = symbol_paths(deriv_dir)
    feature_paths = symbol_paths(feat_dir)
    dates = global_dates(deriv_dir)
    targets = (PRIMARY_TARGET, *SECONDARY_TARGETS)

    held, fold_detail = held_out_positions(dates)
    streamed = stream_state_counts(derived_paths, feature_paths, keep_columns, dates, list(targets), block_size=block_size)
    by_target = streamed["by_target"]

    univariate_by_target = {
        target: univariate_hypotheses(
            by_target[target], keep_columns, held, fold_bounds=fold_detail, min_holdout_dates=min_holdout_dates
        )
        for target in targets
    }
    univariate = univariate_by_target[PRIMARY_TARGET]

    # Pair *selection* needs a BH decision on the univariate family, because
    # conjunctions may only be built from "univariate FDR survivors" (plan step 3).
    # The family-wide pass further down then re-decides every hypothesis —
    # including these univariate ones — over the complete family (univariate +
    # conjunctions), which is the pass that governs `reject`/`q` in the report.
    selection = _apply_bh(univariate, alpha)
    states = survivor_states(univariate, cap=top_states)
    pairs = conjunction_pairs(states, keep_columns, cap=max_pairs) if len(states) > 1 else []
    conjunction_by_target: dict[str, list[dict]] = {t: [] for t in targets}
    pair_symbols = None
    if pairs:
        conj_stream = stream_conjunction_counts(
            derived_paths, feature_paths, keep_columns, dates, list(targets), pairs, block_size=block_size
        )
        conjunction_by_target = _conjunction_hypotheses(
            pairs, conj_stream["by_target"], {t: by_target[t]["universe"] for t in targets},
            keep_columns, held, targets, fold_bounds=fold_detail,
            min_holdout_dates=min_holdout_dates,
        )
        pair_symbols = conj_stream["by_target"][PRIMARY_TARGET]["pair_symbols"]

    family = [*univariate, *conjunction_by_target[PRIMARY_TARGET]]
    bh = _apply_bh(family, alpha)
    survivors = [h for h in family if h.get("reject") and _passes(h)]
    survivors.sort(key=lambda h: (h["p"], h["condition"], h["direction"]))
    density = float(len(survivors) / len(family)) if family else float("nan")
    red_flag = bool(np.isfinite(density) and density > SURVIVOR_DENSITY_RED_FLAG)

    # G2's pass clause is mechanical (survivors exist); the *win* is not. A wall of
    # survivors is pre-registered as a red flag rather than a result (plan step 3),
    # so the conditional G3 is invoked only when G2 passes AND is not red-flagged.
    g2_pass = bool(len(survivors) > 0)
    g3_eligible = bool(g2_pass and not red_flag)
    if not g2_pass:
        g3_skip_reason = "no condition cleared the out-of-fold CI, BH-FDR 5% and the same-sign bar"
    elif red_flag:
        g3_skip_reason = (
            f"survivor density {density:.3f} > {SURVIVOR_DENSITY_RED_FLAG}: a wall of survivors is a "
            "noise/leakage red flag, not a win, so G3 is not invoked"
        )
    else:
        g3_skip_reason = None

    # robustness reads + breadth for survivors only (secondary targets never select)
    for hypothesis in survivors:
        if hypothesis["kind"] == "univariate":
            hypothesis["robustness"] = _robustness(hypothesis, univariate_by_target, hypothesis["_index"])
        else:
            index = conjunction_by_target[PRIMARY_TARGET].index(hypothesis)
            hypothesis["robustness"] = _robustness(hypothesis, conjunction_by_target, index)
            if pair_symbols is not None:
                pi = pairs.index(tuple(hypothesis["pair"]))
                hypothesis["breadth"] = {"symbols": int((pair_symbols[pi] > 0).sum())}

    reported = [_public(h) for h in survivors]
    ranked = sorted(family, key=lambda h: (h["p"] if np.isfinite(h.get("p", np.nan)) else np.inf, h["condition"]))[:10]

    report = {
        "step": "WI-018 step 3 (G2) falsification probe",
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
        },
        "config": {
            "features": list(keep_columns),
            "n_features": len(keep_columns),
            "binnings": dict(BINNINGS),
            "directions": list(DIRECTIONS),
            "state_definition": "within-date USD cross-sectional quantiles (identical to G1 atlas)",
            "fdr_alpha": float(alpha),
            "fdr_method": "Benjamini-Hochberg over the complete family (univariate + conjunctions)",
            "n_folds": N_FOLDS,
            "embargo_td": int(max(20, HORIZON)),
            "fold_helper": "src.wi011.stats.fold_blocks",
            "bootstrap": f"circular {BOOTSTRAP_BLOCK_DATES}-date blocks, {BOOTSTRAP_DRAWS} draws, seed {BOOTSTRAP_SEED}",
            "min_names_per_date": MIN_NAMES_PER_DATE,
            "min_group_n": MIN_N,
            "min_holdout_dates": MIN_HOLDOUT_DATES,
            "top_survivor_states": int(top_states),
            "max_conjunction_pairs": int(max_pairs),
            "survivor_density_red_flag": SURVIVOR_DENSITY_RED_FLAG,
            "decision_rule": "CI excludes zero AND BH-FDR reject AND same-sign bar",
            "secondary_targets": list(SECONDARY_TARGETS),
            "secondary_role": "robustness reads only — never selection targets",
        },
        "folds": fold_detail,
        "held_out": {
            "n_dates": int(held.sum()),
            "share_of_dates": float(held.sum() / dates.size),
            "date_min": str(pd.Timestamp(dates[held].min()).date()) if held.any() else None,
            "date_max": str(pd.Timestamp(dates[held].max()).date()) if held.any() else None,
        },
        "unconditional": {
            PRIMARY_TARGET: {
                "held_out": _unconditional_block(by_target[PRIMARY_TARGET]["universe"], held),
                "full_sample": _unconditional_block(by_target[PRIMARY_TARGET]["universe"], np.ones(dates.size, dtype=bool)),
                "wi017_run2_reference": {"up": 0.3756, "dn": 0.2971, "neither": 0.3273},
            }
        },
        "hypotheses": {
            "n_univariate": int(len(univariate)),
            "n_univariate_estimable": int(sum(1 for h in univariate if h["estimable"])),
            "n_survivor_states": int(len(states)),
            "n_conjunction_pairs": int(len(pairs)),
            "n_conjunction": int(len(conjunction_by_target[PRIMARY_TARGET])),
            "univariate_selection_pass": selection,
            "n_total": int(len(family)),
            "n_tested": bh["n_tested"],
            "n_rejected_bh": bh["n_rejected"],
            "min_p": bh["min_p"],
            "n_survivors": int(len(survivors)),
            "survivor_density": density,
            "red_flag": red_flag,
            "red_flag_detail": (
                f"survivor density {density:.3f} > {SURVIVOR_DENSITY_RED_FLAG} — a wall of survivors is a "
                "noise/leakage red flag, not a win"
                if red_flag else None
            ),
        },
        "survivors": reported,
        "closest_to_passing": [_public(h) for h in ranked],
        "g2_pass": g2_pass,
        "red_flag": red_flag,
        "g3_eligible": g3_eligible,
        "g3_skipped": not g3_eligible,
        "g3_skip_reason": g3_skip_reason,
        "verdict": "G2_PASS_WITH_RED_FLAG" if (survivors and red_flag) else ("G2_PASS" if survivors else "G2_FAIL"),
    }
    checks = check_probe_report(report)
    report["checks"] = {k: {"ok": bool(ok), "detail": detail} for k, (ok, detail) in checks.items()}
    return report


def _public(hypothesis: dict) -> dict:
    """Report-facing projection of a hypothesis record (drops internal indices)."""
    keep = (
        "kind", "condition", "feature", "binning", "bin", "direction", "n", "n_dates",
        "held_out_rate", "unconditional_rate", "lift", "t", "p", "q", "margin",
        "ci_low", "ci_high", "same_sign", "estimable", "unevaluable_reason",
        "per_fold_lift", "folds_same_sign", "reject", "state_share", "breadth", "robustness",
    )
    return {k: hypothesis[k] for k in keep if k in hypothesis}


# --------------------------------------------------------------------------- #
# Acceptance self-check
# --------------------------------------------------------------------------- #
def _is_finite_number(value) -> bool:
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def check_probe_report(report: dict) -> dict:
    """Acceptance self-check for a probe report; returns `{name: (ok, detail)}`."""
    checks: dict[str, tuple[bool, str]] = {}
    config = report.get("config", {})
    hypotheses = report.get("hypotheses", {})
    survivors = report.get("survivors", [])

    checks["family_counts_consistent"] = (
        hypotheses.get("n_total") == hypotheses.get("n_univariate", 0) + hypotheses.get("n_conjunction", 0)
        and hypotheses.get("n_univariate", 0) > 0,
        f"total={hypotheses.get('n_total')} vs univariate={hypotheses.get('n_univariate')} "
        f"+ conjunction={hypotheses.get('n_conjunction')}",
    )
    selection = hypotheses.get("univariate_selection_pass") or {}
    checks["conjunctions_built_only_from_univariate_survivors"] = (
        not hypotheses.get("n_conjunction", 0)
        or (
            hypotheses.get("n_survivor_states", 0) >= 2
            and (selection.get("n_rejected") or 0) > 0
        ),
        f"pairs={hypotheses.get('n_conjunction_pairs')} from {hypotheses.get('n_survivor_states')} states; "
        f"univariate BH rejects={selection.get('n_rejected')} at alpha={selection.get('alpha')}",
    )
    checks["fdr_applied_over_whole_family"] = (
        "Benjamini-Hochberg" in str(config.get("fdr_method")) and config.get("fdr_alpha") == FDR_ALPHA,
        f"{config.get('fdr_method')} at alpha={config.get('fdr_alpha')}",
    )
    checks["folds_and_embargo_recorded"] = (
        len(report.get("folds", [])) == N_FOLDS and int(config.get("embargo_td", 0)) == max(20, HORIZON),
        f"{len(report.get('folds', []))} folds, embargo {config.get('embargo_td')} td",
    )
    surviving_ok, survivor_detail = True, f"{len(survivors)} survivors checked"
    for s in survivors:
        reasons = []
        if not s.get("same_sign"):
            reasons.append("same_sign")
        if not s.get("reject"):
            reasons.append("bh_reject")
        if not (_is_finite_number(s.get("margin")) and abs(s.get("lift", 0.0)) > float(s.get("margin"))):
            reasons.append("ci_excludes_zero")
        if not (_is_finite_number(s.get("ci_low")) and _is_finite_number(s.get("ci_high"))):
            reasons.append("finite_ci")
        if reasons:
            surviving_ok = False
            survivor_detail = f"{s.get('condition')}/{s.get('direction')} fails {reasons}"
    checks["every_survivor_passes_all_criteria"] = (surviving_ok, survivor_detail)
    checks["pass_and_gate_flags_consistent"] = (
        bool(report.get("g2_pass")) == bool(survivors)
        and bool(report.get("g3_eligible")) == (bool(survivors) and not bool(report.get("red_flag")))
        and bool(report.get("g3_skipped")) == (not bool(report.get("g3_eligible"))),
        f"g2_pass={report.get('g2_pass')} red_flag={report.get('red_flag')} "
        f"g3_eligible={report.get('g3_eligible')} g3_skipped={report.get('g3_skipped')} "
        f"survivors={len(survivors)}",
    )
    if not report.get("g3_eligible"):
        checks["g3_skip_reason_recorded"] = (
            bool(report.get("g3_skip_reason")),
            str(report.get("g3_skip_reason")),
        )
    checks["density_red_flag_consistent"] = (
        bool(report.get("red_flag"))
        == bool(_is_finite_number(hypotheses.get("survivor_density"))
                and float(hypotheses.get("survivor_density")) > SURVIVOR_DENSITY_RED_FLAG),
        f"density={hypotheses.get('survivor_density')} red_flag={report.get('red_flag')}",
    )
    checks["determinism_config_present"] = (
        config.get("bootstrap") == f"circular {BOOTSTRAP_BLOCK_DATES}-date blocks, {BOOTSTRAP_DRAWS} draws, "
        f"seed {BOOTSTRAP_SEED}",
        str(config.get("bootstrap")),
    )
    robustness_ok = all(
        all(target in s.get("robustness", {}) for target in SECONDARY_TARGETS) for s in survivors
    )
    checks["survivors_carry_secondary_reads_only"] = (
        robustness_ok and str(config.get("secondary_role", "")).startswith("robustness reads only"),
        f"secondary targets {list(SECONDARY_TARGETS)} present for every survivor",
    )
    unconditional = report.get("unconditional", {}).get(PRIMARY_TARGET, {}).get("held_out", {})
    checks["unconditional_reference_present"] = (
        bool(unconditional) and sums_to_one(unconditional.get("rates", {}), 1e-6),
        f"held-out rates={ {k: round(v, 4) for k, v in unconditional.get('rates', {}).items()} }",
    )
    return checks


def summarize_checks(checks: dict) -> str:
    return "\n".join(f"  {'OK  ' if ok else 'FAIL'} {name}: {detail}" for name, (ok, detail) in checks.items())


# --------------------------------------------------------------------------- #
# Markdown
# --------------------------------------------------------------------------- #
def _fmt_pct(value) -> str:
    return "n/a" if not _is_finite_number(value) else f"{float(value):.4f}"


def format_markdown(report: dict) -> str:
    hyp = report["hypotheses"]
    unc = report["unconditional"][PRIMARY_TARGET]["held_out"]
    gate = (
        "survivors qualify for the conditional cost overlay (G3)"
        if report.get("g3_eligible")
        else f"G3 not invoked — {report.get('g3_skip_reason')}"
    )
    lines = [
        f"# WI-018 G2 falsification probe — `{PRIMARY_TARGET}` ({report['market']})",
        "",
        f"Generated {report['generated_utc']}. Verdict **{report['verdict']}** "
        f"({'G3 skipped' if report['g3_skipped'] else 'G3 eligible'}).",
        "",
        f"**G3 gate:** {gate}.",
        "",
        "## Design (frozen before the run)",
        "",
        f"- states: within-date USD cross-sectional quantiles, identical to the G1 atlas "
        f"({report['config']['n_features']} features × 8 states × 2 directions)",
        f"- folds: {report['config']['n_folds']} chronological held-out blocks "
        f"(`{report['config']['fold_helper']}`), embargo {report['config']['embargo_td']} sessions "
        f"(= max(20, horizon {HORIZON})); held-out dates {report['held_out']['n_dates']} "
        f"({report['held_out']['share_of_dates']:.2%})",
        f"- correction: {report['config']['fdr_method']}, alpha {report['config']['fdr_alpha']}",
        f"- evidence: {report['config']['bootstrap']}; decision rule = {report['config']['decision_rule']}",
        f"- conjunctions: AND-pairs of the {hyp['n_survivor_states']} best univariate FDR-surviving states "
        f"(≤{report['config']['top_survivor_states']}), {hyp['n_conjunction_pairs']} pairs, depth ≤ 2",
        "",
        "## Hypothesis family",
        "",
        "| quantity | value |",
        "|---|---|",
        f"| univariate hypotheses | {hyp['n_univariate']} ({hyp['n_univariate_estimable']} estimable) |",
        f"| conjunction hypotheses | {hyp['n_conjunction']} |",
        f"| total family | {hyp['n_total']} ({hyp['n_tested']} tested) |",
        f"| BH rejections at {report['config']['fdr_alpha']} | {hyp['n_rejected_bh']} |",
        f"| univariate BH rejections (pair-selection pass) | "
        f"{(hyp.get('univariate_selection_pass') or {}).get('n_rejected')} |",
        f"| survivors (CI excludes zero + BH + same sign) | **{hyp['n_survivors']}** |",
        f"| survivor density | {_fmt_pct(hyp['survivor_density'])} "
        f"(red flag above {SURVIVOR_DENSITY_RED_FLAG}) |",
        f"| smallest p in the family | {_fmt_pct(hyp['min_p'])} |",
        "",
        f"Red flag: {hyp['red_flag_detail'] or 'not raised.'}",
        "",
        "## Unconditional reference (held-out dates)",
        "",
        "| class | date-mean rate | 95% CI | pooled |",
        "|---|---|---|---|",
    ]
    for cls in CLASSES:
        ci = unc["ci"][cls]
        lines.append(
            f"| {cls} | {_fmt_pct(unc['rates'][cls])} | [{_fmt_pct(ci['ci_low'])}, {_fmt_pct(ci['ci_high'])}] "
            f"| {_fmt_pct(unc['pooled'][cls])} |"
        )
    lines += ["", "## Survivors", ""]
    if report["survivors"]:
        lines += [
            "| condition | dir | n | n_dates | lift | 95% CI | q | same-sign | folds same-sign |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for s in report["survivors"]:
            lines.append(
                f"| {s['condition']} | {s['direction']} | {s['n']} | {s['n_dates']} | {s['lift']:+.4f} | "
                f"[{s['ci_low']:+.4f}, {s['ci_high']:+.4f}] | {_fmt_pct(s['q'])} | {s['same_sign']} | "
                f"{s['folds_same_sign']} |"
            )
    else:
        lines.append("None. No condition cleared all three criteria out of sample.")
    lines += [
        "",
        "## Closest to passing (smallest p, regardless of outcome)",
        "",
        "| condition | dir | n_dates | lift | 95% CI | p | q | same-sign (2 windows) | folds same-sign |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for s in report["closest_to_passing"]:
        lines.append(
            f"| {s['condition']} | {s['direction']} | {s['n_dates']} | {s['lift']:+.4f} | "
            f"[{s['ci_low']:+.4f}, {s['ci_high']:+.4f}] | {_fmt_pct(s['p'])} | {_fmt_pct(s.get('q'))} | "
            f"{s['same_sign']} | {s['folds_same_sign']} |"
        )
    lines += [
        "",
        "Robustness reads at `first_touch_24`/`first_touch_39` are reported for survivors only and are never "
        "selection targets; decisions always use `first_touch_34`.",
        "",
        "## Self-check",
        "",
        "```",
        summarize_checks(check_probe_report(report)),
        "```",
        "",
        "No executable rules and no shortlist are produced by G2.",
        "",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def write_report(report: dict, json_path: Path = PROBE_JSON, md_path: Path = PROBE_MD) -> tuple[Path, Path]:
    json_path = Path(json_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=1, default=str))
    Path(md_path).write_text(format_markdown(report))
    return json_path, Path(md_path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="WI-018 G2 falsification probe (USD)")
    ap.add_argument("--market", default=MARKET)
    ap.add_argument("--check-report", default=None,
                    help="verify an existing probe report against the acceptance criteria instead of running")
    ap.add_argument("--out", default=str(PROBE_JSON))
    ap.add_argument("--md", default=str(PROBE_MD))
    ap.add_argument("--block-size", type=int, default=None)
    ap.add_argument("--alpha", type=float, default=FDR_ALPHA)
    args = ap.parse_args(argv)

    if args.check_report:
        path = Path(args.check_report)
        if not path.is_file():
            print(f"PROBE CHECK FAIL: report missing ({path})")
            return 1
        report = json.loads(path.read_text())
        checks = check_probe_report(report)
        print(f"WI-018 probe report check [{report.get('market')}] verdict={report.get('verdict')}")
        print(summarize_checks(checks))
        ok = all(ok for ok, _ in checks.values())
        print(f"PROBE CHECK {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1

    try:
        report = run_probe(block_size=args.block_size, market=args.market, alpha=args.alpha)
    except PreflightError as exc:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"PROBE FAIL: {exc}")
        return 1
    json_path, md_path = write_report(report, Path(args.out), Path(args.md))
    hyp = report["hypotheses"]
    print(f"WI-018 probe [{report['market']}] verdict={report['verdict']} -> {json_path}, {md_path}")
    print(
        f"  family={hyp['n_total']} (univariate={hyp['n_univariate']}, conjunction={hyp['n_conjunction']}) "
        f"tested={hyp['n_tested']} rejected={hyp['n_rejected_bh']} survivors={hyp['n_survivors']} "
        f"density={_fmt_pct(hyp['survivor_density'])} red_flag={report['red_flag']} "
        f"g3_skipped={report['g3_skipped']}"
    )
    print(summarize_checks(check_probe_report(report)))
    return 0 if all(ok for ok, _ in check_probe_report(report).values()) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
