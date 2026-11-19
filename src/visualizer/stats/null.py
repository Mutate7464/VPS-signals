"""Within-date target-shuffled null for View 1 (WI-087) - evidence, never a verdict.

Under the null the labels are exchangeable **inside a date**: shuffling labels
within a date preserves that date's hit count, so the per-``(date, bin)`` hit
count follows a hypergeometric law. Sampling that law on the pre-aggregated
``(date, bin) -> (n, hits)`` table reproduces a full label shuffle without ever
touching the rows (plan 26-W47: "hypergeometric sampling on the same aggregate").

The joint draw is sequential across bins (the multivariate hypergeometric
marginals are hypergeometric), which keeps every replicate consistent with the
fixed per-date hit counts. Sized for the DoD: ``sims=200`` over a few thousand
dates costs milliseconds.
"""
from __future__ import annotations

import warnings

import numpy as np

from src.visualizer.stats.bootstrap import aggregate_matrix, rate

SIM_DEFAULT = 200
SEED_DEFAULT = 87
CONFIDENCE = 0.95
METHOD = "within-date target shuffle (sequential multivariate hypergeometric on the (date, bin) aggregate)"


def draw_within_date(n: np.ndarray, hits: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """One exact within-date shuffle: per-date hits redistributed over the bins."""
    remaining_total = n.sum(axis=1)
    remaining_hits = hits.sum(axis=1)
    drawn = np.zeros_like(n)
    for column in range(n.shape[1]):
        take = rng.hypergeometric(
            ngood=remaining_hits,
            nbad=remaining_total - remaining_hits,
            nsample=n[:, column],
        )
        drawn[:, column] = take
        remaining_total = remaining_total - n[:, column]
        remaining_hits = remaining_hits - take
    return drawn


def target_shifted_null(
    agg,
    n_bins: int,
    sims: int = SIM_DEFAULT,
    seed: int = SEED_DEFAULT,
    confidence: float = CONFIDENCE,
) -> dict:
    """Null hit rates per bin + the pooled null vs the base rate under MC error."""
    _, n, hits = aggregate_matrix(agg, n_bins)
    n_bins, sims = int(n_bins), int(sims)
    totals_n = n.sum(axis=0)
    totals_hits = hits.sum(axis=0)
    total_rows = int(n.sum())
    base_rate = float(totals_hits.sum() / total_rows) if total_rows else float("nan")
    rng = np.random.default_rng(seed)
    sim_hits = np.zeros((max(sims, 0), n_bins), dtype="int64")
    for index in range(sims):
        sim_hits[index] = draw_within_date(n, hits, rng).sum(axis=0)
    alpha = (1.0 - float(confidence)) / 2.0
    sim_rates = rate(sim_hits, np.broadcast_to(totals_n, sim_hits.shape))
    bin_low = np.full(n_bins, np.nan)
    bin_high = np.full(n_bins, np.nan)
    keep = totals_n > 0
    if sims and keep.any():
        with warnings.catch_warnings():  # all-NaN replicate column
            warnings.simplefilter("ignore", RuntimeWarning)
            bin_low[keep] = np.nanpercentile(sim_rates[:, keep], alpha * 100.0, axis=0)
            bin_high[keep] = np.nanpercentile(sim_rates[:, keep], (1.0 - alpha) * 100.0, axis=0)
    pooled = sim_hits.sum(axis=1) / total_rows if total_rows else np.zeros(sims)
    mean_rate = float(np.mean(pooled)) if sims else float("nan")
    std = float(np.std(pooled, ddof=1)) if sims > 1 else 0.0
    mc_error = std / float(np.sqrt(sims)) if sims > 1 else 0.0
    delta = mean_rate - base_rate
    return {
        "sims": sims,
        "seed": int(seed),
        "confidence": float(confidence),
        "method": METHOD,
        "n_dates": int(n.shape[0]),
        "base_rate": base_rate,
        "mean": mean_rate,
        "std": std,
        "mc_error": mc_error,
        "delta": float(delta),
        "within_mc_error": bool(abs(delta) <= 3.0 * mc_error + 1e-9),
        "n_hits_total": int(hits.sum()),
        "per_date_hits_preserved": int(sim_hits.sum(axis=1).max(initial=0)) == int(hits.sum()) if sims else True,
        "bin_rate": rate(sim_hits.sum(axis=0) if sims else np.zeros(n_bins), totals_n),
        "bin_low": bin_low,
        "bin_high": bin_high,
        "totals_n": totals_n,
    }
