"""Date-cluster bootstrap CIs for View 1 (WI-087) - evidence, never a verdict.

The bootstrap consumes a pre-aggregated ``(date, bin) -> (n, hits)`` table, never
the raw rows: the date count is orders of magnitude below the row count, so the
default ``B=200`` replicates stay inside the 400 ms server-side compute budget
(plan 26-W47 / WI-087 DoD).

The resampling unit is the **date** (a cluster). Rows inside one date share a
market regime and are not independent, so a row-level bootstrap would understate
the interval width. CIs are percentile intervals and are exactly reproducible
from ``(seed, agg, n_bins, b)``.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

AGG_COLUMNS: tuple[str, ...] = ("date", "bin", "n", "hits")
B_DEFAULT = 200
SEED_DEFAULT = 87  # WI-087's fixed seed: one seed per card, CIs reproducible
CONFIDENCE = 0.95
DATE_DTYPE = "datetime64[ns]"


def preaggregate(dates, bins, labels) -> pd.DataFrame:
    """Collapse rows onto ``(date, bin) -> (n, hits)``; NaN-free input expected."""
    frame = pd.DataFrame(
        {
            "date": np.asarray(dates).astype(DATE_DTYPE),
            "bin": np.asarray(bins, dtype="int32"),
            "label": np.asarray(labels, dtype="float64"),
        }
    )
    frame["hits"] = (frame["label"] > 0).astype("int32")
    grouped = frame.groupby(["date", "bin"], observed=True, sort=True).agg(
        n=("hits", "size"), hits=("hits", "sum")
    )
    return grouped.reset_index()[list(AGG_COLUMNS)]


def aggregate_matrix(agg: pd.DataFrame, n_bins: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Dense ``(dates x bins)`` count matrices plus the sorted date axis."""
    dates = np.sort(pd.unique(np.asarray(agg["date"]).astype(DATE_DTYPE)))
    n = np.zeros((len(dates), int(n_bins)), dtype="int64")
    hits = np.zeros_like(n)
    if len(agg):
        rows = pd.Index(dates).get_indexer(np.asarray(agg["date"]).astype(DATE_DTYPE))
        columns = agg["bin"].to_numpy().astype("int64")
        n[rows, columns] = agg["n"].to_numpy()
        hits[rows, columns] = agg["hits"].to_numpy()
    return dates, n, hits


def rate(hits, n) -> np.ndarray:
    """``hits / n`` with empty bins as NaN (the interval is undefined there)."""
    hits = np.asarray(hits, dtype="float64")
    n = np.asarray(n, dtype="float64")
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(n > 0, hits / np.where(n > 0, n, 1.0), np.nan)


def date_cluster_bootstrap(
    agg: pd.DataFrame,
    n_bins: int,
    b: int = B_DEFAULT,
    seed: int = SEED_DEFAULT,
    confidence: float = CONFIDENCE,
) -> dict:
    """Percentile CIs per bin over ``b`` date-cluster resamples (fixed seed)."""
    dates, n, hits = aggregate_matrix(agg, n_bins)
    n_bins, b, n_dates = int(n_bins), int(b), int(len(dates))
    alpha = (1.0 - float(confidence)) / 2.0
    low = np.full(n_bins, np.nan)
    high = np.full(n_bins, np.nan)
    resampled_n = np.zeros((max(b, 0), n_bins), dtype="int64")
    if n_dates and b:
        rng = np.random.default_rng(seed)
        index = rng.integers(0, n_dates, size=(b, n_dates))
        resampled_n = n[index].sum(axis=1)
        rates = rate(hits[index].sum(axis=1), resampled_n)
        keep = resampled_n.sum(axis=0) > 0
        if keep.any():
            with warnings.catch_warnings():  # all-NaN replicate column
                warnings.simplefilter("ignore", RuntimeWarning)
                low[keep] = np.nanpercentile(rates[:, keep], alpha * 100.0, axis=0)
                high[keep] = np.nanpercentile(rates[:, keep], (1.0 - alpha) * 100.0, axis=0)
    return {
        "b": b,
        "seed": int(seed),
        "confidence": float(confidence),
        "resample_unit": "date",
        "n_dates": n_dates,
        "n_resampled_rows": resampled_n,
        "observed": rate(hits.sum(axis=0), n.sum(axis=0)),
        "low": low,
        "high": high,
        "totals_n": n.sum(axis=0),
        "totals_hits": hits.sum(axis=0),
    }


def bin_intervals(
    agg: pd.DataFrame,
    n_bins: int,
    b: int = B_DEFAULT,
    seed: int = SEED_DEFAULT,
    confidence: float = CONFIDENCE,
) -> tuple[list[dict], dict]:
    """Per-bin ``{n, hits, hit_rate, ci_low, ci_high}`` rows plus the CI metadata."""
    result = date_cluster_bootstrap(agg, n_bins, b=b, seed=seed, confidence=confidence)
    rows = [
        {
            "bin": index,
            "n": int(result["totals_n"][index]),
            "hits": int(result["totals_hits"][index]),
            "hit_rate": float(result["observed"][index]),
            "ci_low": float(result["low"][index]),
            "ci_high": float(result["high"][index]),
        }
        for index in range(int(n_bins))
    ]
    meta = {key: result[key] for key in ("b", "seed", "confidence", "resample_unit", "n_dates")}
    return rows, meta
