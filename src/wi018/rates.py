"""WI-018 rate estimators shared by the G1 atlas and the G2 probe.

Two numbers describe every condition, and they are deliberately different:

* **pooled rate** — row-weighted ("what does a traded day look like");
* **date-mean rate** — equal weight per date, which is the series the WI-015
  circular block bootstrap (20-date blocks, 1,000 draws, seed 42) resamples, so
  it is the rate that carries the margin.

`ci_from_series` is the only place a CI is produced: the margin comes from
`src.perfanalytics.correlation.alignment.block_bootstrap_margin` (imported, not
reimplemented) and the interval is `mean ± margin`. A rate is only reported when
it is estimable — at least `MIN_GROUP_N` rows across at least
`MIN_GROUP_DATES` dated cross-sections (`src.wi011.stats.insufficient`).
"""

from __future__ import annotations

import numpy as np

from src.perfanalytics.correlation.alignment import (
    BLOCK_DATES,
    N_BOOTSTRAP,
    BOOTSTRAP_SEED,
    block_bootstrap_margin,
)
from src.wi011.stats import insufficient
from src.wi018 import MIN_GROUP_DATES, MIN_GROUP_N

__all__ = [
    "BLOCK_DATES",
    "BOOTSTRAP_SEED",
    "N_BOOTSTRAP",
    "RATE_SUM_TOL",
    "ci_from_series",
    "date_mean",
    "pooled_rate",
    "rate_block",
    "sums_to_one",
    "unconditional_block",
]

RATE_SUM_TOL = 1e-6
"""Tolerance for "the three class rates sum to 1" (float64 accumulation)."""


def pooled_rate(counts, totals) -> float:
    """Row-weighted rate `sum(counts)/sum(totals)` (NaN when no rows)."""
    c = float(np.asarray(counts, dtype="float64").sum())
    t = float(np.asarray(totals, dtype="float64").sum())
    return float(c / t) if t > 0.0 else float("nan")


def date_mean(values) -> float:
    """Mean over finite entries of a per-date series (NaN when empty)."""
    v = np.asarray(values, dtype="float64")
    v = v[np.isfinite(v)]
    return float(v.mean()) if v.size else float("nan")


def ci_from_series(series, n_draws: int = N_BOOTSTRAP, seed: int = BOOTSTRAP_SEED) -> dict:
    """`{mean, margin, ci_low, ci_high, n_dates}` from a per-date series.

    The margin is the 95th percentile of |bootstrap mean − observed mean| from
    circular 20-date blocks (`block_bootstrap_margin`), i.e. the half-width of a
    95% interval around the date-mean. An empty series returns NaNs (never a
    fabricated interval).
    """
    v = np.asarray(series, dtype="float64")
    v = v[np.isfinite(v)]
    if v.size == 0:
        return {"mean": float("nan"), "margin": float("nan"), "ci_low": float("nan"),
                "ci_high": float("nan"), "n_dates": 0}
    mean = float(v.mean())
    margin = block_bootstrap_margin(v, block=BLOCK_DATES, n_draws=n_draws, seed=seed) if v.size > 1 else 0.0
    if not np.isfinite(margin):
        margin = float("nan")
    return {"mean": mean, "margin": margin, "ci_low": mean - margin, "ci_high": mean + margin, "n_dates": int(v.size)}


def sums_to_one(rates: dict, tol: float = RATE_SUM_TOL) -> bool:
    """True when the class rates of an estimable condition sum to 1 within `tol`.

    Non-numeric or non-finite entries make the check fail rather than raise: this
    runs on report payloads, where the input may be a hand-edited or truncated
    artifact (the `--check-report` path).
    """
    try:
        values = [float(v) for v in rates.values()]
    except (TypeError, ValueError):
        return False
    if not values or not np.all(np.isfinite(values)):
        return False
    return abs(float(np.sum(values)) - 1.0) <= tol


def rate_block(counts: np.ndarray, totals: np.ndarray, n_rows: int) -> dict:
    """Full rate record for one condition: pooled, date-mean, CI and sufficiency.

    `counts` is `(n_classes, n_dates)` for the condition, `totals` the matching
    per-date denominators (rows eligible for the condition), `n_rows` the pooled
    condition size. Class names come from `src.wi018.streaming.CLASSES`.
    """
    from src.wi018.streaming import CLASSES

    counts = np.asarray(counts, dtype="float64")
    totals = np.asarray(totals, dtype="float64")
    with np.errstate(divide="ignore", invalid="ignore"):
        per_date = np.where(totals > 0, counts / np.where(totals > 0, totals, np.nan), np.nan)
    n_dates = int(np.isfinite(per_date).any(axis=0).sum()) if per_date.size else 0
    record = {
        "n": int(n_rows),
        "n_dates": n_dates,
        "pooled": {c: pooled_rate(counts[i], totals) for i, c in enumerate(CLASSES)},
        "date_mean": {c: date_mean(per_date[i]) for i, c in enumerate(CLASSES)},
        "ci": {c: ci_from_series(per_date[i]) for i, c in enumerate(CLASSES)},
    }
    record["estimable"] = not insufficient(int(n_rows), n_dates)
    if not record["estimable"]:
        reasons = []
        if int(n_rows) < MIN_GROUP_N:
            reasons.append(f"n<{MIN_GROUP_N}")
        if n_dates < MIN_GROUP_DATES:
            reasons.append(f"n_dates<{MIN_GROUP_DATES}")
        record["unevaluable_reason"] = " and ".join(reasons) or "insufficient"
    else:
        record["unevaluable_reason"] = None
    record["rates"] = dict(record["date_mean"])
    record["rate_sum"] = float(np.nansum([record["rates"][c] for c in CLASSES]))
    return record


def unconditional_block(count_array: np.ndarray, totals: np.ndarray, n_rows: int) -> dict:
    """Unconditional (all-names) rate record from per-date class counts."""
    return rate_block(np.asarray(count_array, dtype="float64"), np.asarray(totals, dtype="float64"), n_rows)
