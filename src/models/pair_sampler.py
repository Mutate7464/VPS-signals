"""Within-date streamed pair sampler for contrastive ranking (WI-009).

Design notes
------------
* Pairs are sampled *within a single date*, so a label is a relative
  (cross-sectional) statement: "on date t, asset i out-returned asset j".
  This is the relative space the E5 probe (2026-10-24) identified as the
  correct target definition — never a pooled magnitude target.
* Pairs are generated on the fly and accumulated only up to `batch_pairs`.
  A full O(N^2) pair matrix is never materialised (host guardrail: 2 vCPU /
  8 GB / no swap, n_jobs <= 2).
* Labels come from a *forward* return column. Features fed to the sampler must
  be trailing/point-in-time; the sampler does not verify causality itself.

Evaluation helpers live here too so that training and the E5 baseline both use
the *same* score-based within-date rank-IC definition (never class-label IC).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Sequence

import numpy as np
import pandas as pd

__all__ = [
    "PairBatch",
    "sample_pairs_for_date",
    "iter_pair_batches",
    "within_date_rank_ic",
    "pairwise_win_rate",
]


@dataclass
class PairBatch:
    """A batch of within-date pairs, already oriented winner-first."""

    x_win: np.ndarray  # (m, d) float32
    x_los: np.ndarray  # (m, d) float32
    n_dates: int       # how many distinct dates contributed to this batch


def sample_pairs_for_date(
    x: np.ndarray,
    fwd_ret: np.ndarray,
    n_pairs: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Sample `n_pairs` winner/loser index pairs from one date's cross-section.

    Args:
        x: (n, d) feature matrix for one date. Not indexed within this function,
           only its row count is used to draw indices.
        fwd_ret: (n,) forward returns for the same rows.
        n_pairs: number of pairs to attempt.
        rng: numpy random generator (caller-owned for reproducibility).

    Returns:
        (win_idx, los_idx): index arrays such that fwd_ret[win] > fwd_ret[los].
        Ties and self-pairs are dropped, so the arrays may be shorter than
        `n_pairs` (and empty when the date has < 2 distinct-return assets).
    """
    n = len(fwd_ret)
    if n < 2 or n_pairs <= 0:
        empty = np.empty(0, dtype=np.int64)
        return empty, empty

    i = rng.integers(0, n, size=n_pairs)
    j = rng.integers(0, n, size=n_pairs)

    keep = i != j
    i, j = i[keep], j[keep]
    if i.size == 0:
        return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64)

    ri, rj = fwd_ret[i], fwd_ret[j]
    # Drop ties (and any non-finite return) — they carry no ordering signal.
    decided = np.isfinite(ri) & np.isfinite(rj) & (ri != rj)
    i, j, ri, rj = i[decided], j[decided], ri[decided], rj[decided]
    if i.size == 0:
        return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64)

    i_win = np.where(ri > rj, i, j)
    j_los = np.where(ri > rj, j, i)
    return i_win.astype(np.int64), j_los.astype(np.int64)


def iter_pair_batches(
    panel: pd.DataFrame,
    feature_cols: Sequence[str],
    return_col: str,
    n_pairs_per_date: int,
    batch_pairs: int,
    rng: np.random.Generator,
    max_dates: int | None = None,
    dates: Sequence | None = None,
) -> Iterator[PairBatch]:
    """Stream winner/loser pair batches, date by date.

    Only `batch_pairs` rows are ever held in memory at once; the generator does
    not retain the panel slices it has already emitted.

    Args:
        panel: DataFrame with a `date` column, `feature_cols`, and `return_col`.
            Will not be mutated; sorted internally by date.
        feature_cols: trailing feature columns (float32).
        return_col: forward-return column used to define the ordering.
        n_pairs_per_date: pair attempts drawn per date.
        batch_pairs: emit a batch once this many *usable* pairs accumulate.
        rng: numpy random generator.
        max_dates: optionally limit how many dates are visited (training slices).
        dates: optionally restrict to an explicit set/sequence of dates.

    Yields:
        PairBatch with float32 (m, d) arrays.
    """
    if max_dates is not None and max_dates <= 0:
        return

    df = panel
    if dates is not None:
        df = df[df["date"].isin(set(dates))]
    if not df["date"].is_monotonic_increasing:
        df = df.sort_values("date", kind="stable")

    buf_win: list[np.ndarray] = []
    buf_los: list[np.ndarray] = []
    buf_d: list[np.ndarray] = []  # date label repeated once per buffered pair
    buf_m = 0
    visited = 0

    for date_key, g in df.groupby("date", sort=True):
        if max_dates is not None and visited >= max_dates:
            break
        visited += 1

        x = g[list(feature_cols)].to_numpy(dtype=np.float32, copy=False)
        r = g[return_col].to_numpy(dtype=np.float64, copy=False)
        w_idx, l_idx = sample_pairs_for_date(x, r, n_pairs_per_date, rng)
        if w_idx.size == 0:
            continue

        buf_win.append(x[w_idx])
        buf_los.append(x[l_idx])
        buf_d.append(np.repeat(np.asarray([date_key], dtype="datetime64[ns]"), w_idx.size))
        buf_m += w_idx.size

        while buf_m >= batch_pairs:
            win = np.concatenate(buf_win, axis=0)
            los = np.concatenate(buf_los, axis=0)
            dts = np.concatenate(buf_d, axis=0)
            take = batch_pairs
            # n_dates counts the dates actually represented in the emitted slice
            # (a spliced batch can hold leftovers from an already-counted date).
            yield PairBatch(win[:take], los[:take], int(pd.unique(dts[:take]).size))
            rest_w, rest_l, rest_d = win[take:], los[take:], dts[take:]
            buf_win = [rest_w] if rest_w.size else []
            buf_los = [rest_l] if rest_l.size else []
            buf_d = [rest_d] if rest_d.size else []
            buf_m = rest_w.shape[0]

    if buf_m > 0:
        yield PairBatch(
            np.concatenate(buf_win, axis=0),
            np.concatenate(buf_los, axis=0),
            int(pd.unique(np.concatenate(buf_d, axis=0)).size),
        )


def within_date_rank_ic(
    scores,
    fwd_ret,
    dates,
) -> tuple[float, float, int]:
    """Score-based within-date rank-IC (Spearman), with a t-stat across dates.

    This is the *only* skill metric used for WI-009. Class-label IC is not used:
    the E5 probe showed class-label scoring overstates sign flips.

    Returns:
        (mean_ic, t_stat, n_dates). `t_stat` is NaN when < 3 dates or zero
        dispersion; `mean_ic` is NaN when no date had a usable cross-section.
    """
    frame = pd.DataFrame(
        {
            "s": np.asarray(scores, dtype="float64"),
            "f": np.asarray(fwd_ret, dtype="float64"),
            "d": np.asarray(dates),
        }
    )
    ics: list[float] = []
    for _, g in frame.groupby("d", sort=False):
        if len(g) < 3:
            continue
        rs = g["s"].rank()
        rf = g["f"].rank()
        if rs.std(ddof=0) == 0.0 or rf.std(ddof=0) == 0.0:
            continue
        ics.append(float(np.corrcoef(rs.to_numpy(), rf.to_numpy())[0, 1]))

    if not ics:
        return float("nan"), float("nan"), 0

    arr = np.asarray(ics, dtype="float64")
    mean_ic = float(arr.mean())
    if arr.size > 2 and arr.std(ddof=1) > 0.0:
        t = float(mean_ic / (arr.std(ddof=1) / np.sqrt(arr.size)))
    else:
        t = float("nan")
    return mean_ic, t, int(arr.size)


def pairwise_win_rate(scores: np.ndarray, dates) -> np.ndarray:
    """Per-asset pairwise win rate vs its own date's cross-section.

    With a scalar scoring tower the ordering is transitive, so
    "P(i out-ranks j)" over all j != i is exactly the fraction of same-date
    peers that i out-scores: (rank_asc_i - 1) / (n_t - 1).

    Computed from ranks only — no per-date score matrix is ever built, so the
    O(N^2) prohibition holds unconditionally. Returns an (n,) array aligned to
    the input rows (NaN where the date has < 2 members).
    """
    scores = np.asarray(scores, dtype="float64")
    dates = np.asarray(dates)
    out = np.full(len(scores), np.nan, dtype="float64")
    frame = pd.DataFrame({"s": scores, "d": dates, "i": np.arange(len(scores))})
    for _, g in frame.groupby("d", sort=False):
        n = len(g)
        if n < 2:
            continue
        idx = g["i"].to_numpy()
        ranks = g["s"].rank(method="average").to_numpy()
        out[idx] = (ranks - 1.0) / (n - 1.0)
    return out