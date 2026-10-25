"""WI-009 — within-date pair sampler and rank-IC helpers.

Guards the two properties the brief makes non-negotiable:
  1. pairs are sampled per date and never enumerated exhaustively (O(N^2) ban),
  2. skill is measured as score-based within-date rank-IC, not class-label IC.
"""

import numpy as np
import pandas as pd
import pytest

from src.models.pair_sampler import (
    iter_pair_batches,
    pairwise_win_rate,
    sample_pairs_for_date,
    within_date_rank_ic,
)


def test_sample_pairs_orient_winner_first():
    rng = np.random.default_rng(0)
    n, d, k = 40, 5, 500
    x = rng.normal(size=(n, d)).astype(np.float32)
    fwd = rng.normal(size=n)

    win, los = sample_pairs_for_date(x, fwd, k, rng)

    assert win.size > 0
    assert win.shape == los.shape
    # Every emitted pair must be decided and correctly oriented.
    assert np.all(fwd[win] > fwd[los])
    # Self-pairs are never emitted.
    assert not np.any(win == los)


def test_sample_pairs_drops_ties_and_small_dates():
    rng = np.random.default_rng(1)
    x = np.zeros((5, 3), dtype=np.float32)

    # Identical returns -> no ordering signal -> no pairs.
    win, los = sample_pairs_for_date(x, np.ones(5), 100, rng)
    assert win.size == 0 and los.size == 0

    # A single asset cannot form a pair.
    win, los = sample_pairs_for_date(x[:1], np.array([1.0]), 10, rng)
    assert win.size == 0 and los.size == 0


def _synthetic_panel(n_dates=50, n_symbols=200, d=6, seed=3):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2020-01-01", periods=n_dates, freq="B")
    rows = []
    for dt_ in dates:
        feats = rng.normal(size=(n_symbols, d)).astype(np.float32)
        fwd = (0.9 * feats[:, 0] - 0.7 * feats[:, 1] + 0.3 * rng.normal(size=n_symbols)).astype(np.float32)
        frame = pd.DataFrame(feats, columns=[f"f{i}" for i in range(d)])
        frame["date"] = dt_
        frame["symbol"] = [f"S{j}" for j in range(n_symbols)]
        frame["fwd_atr_ret_15"] = fwd
        rows.append(frame)
    return pd.concat(rows, ignore_index=True)


def test_streamed_pairs_are_bounded_not_exhaustive():
    """Total pairs must track the sampling budget, not the O(N^2) pair space."""
    panel = _synthetic_panel(n_dates=50, n_symbols=200)
    feature_cols = [c for c in panel.columns if c.startswith("f")]
    pairs_per_date = 64
    batch_pairs = 512

    total = 0
    n_batches = 0
    for batch in iter_pair_batches(
        panel,
        feature_cols,
        "fwd_atr_ret_15",
        n_pairs_per_date=pairs_per_date,
        batch_pairs=batch_pairs,
        rng=np.random.default_rng(5),
    ):
        assert batch.x_win.shape == batch.x_los.shape
        assert batch.x_win.shape[1] == len(feature_cols)
        assert batch.x_win.dtype == np.float32
        assert batch.x_win.shape[0] <= batch_pairs
        total += batch.x_win.shape[0]
        n_batches += 1

    n_dates, n_symbols = 50, 200
    exhaustive = n_dates * (n_symbols * (n_symbols - 1) // 2)
    assert n_batches > 0
    # Sampling budget (~50 * 64 = 3200) with stragglers; far below the 995k exhaustive space.
    assert total <= n_dates * pairs_per_date
    assert total < exhaustive / 100


def test_iter_pair_batches_respects_max_dates_and_subset():
    panel = _synthetic_panel(n_dates=20, n_symbols=40, d=3)
    feature_cols = [c for c in panel.columns if c.startswith("f")]
    subset = sorted(panel["date"].unique())[:5]

    batches = list(
        iter_pair_batches(
            panel,
            feature_cols,
            "fwd_atr_ret_15",
            n_pairs_per_date=32,
            batch_pairs=1024,
            rng=np.random.default_rng(2),
            dates=subset,
        )
    )
    assert len(batches) == 1
    assert batches[0].x_win.shape[0] <= 5 * 32

    capped = list(
        iter_pair_batches(
            panel,
            feature_cols,
            "fwd_atr_ret_15",
            n_pairs_per_date=32,
            batch_pairs=1024,
            rng=np.random.default_rng(2),
            max_dates=3,
        )
    )
    assert capped[0].x_win.shape[0] <= 3 * 32


def test_within_date_rank_ic_is_score_based_and_signed():
    panel = _synthetic_panel(n_dates=30, n_symbols=50, d=2, seed=11)
    dates = panel["date"].to_numpy()
    fwd = panel["fwd_atr_ret_15"].to_numpy()

    perfect, t_perfect, n = within_date_rank_ic(fwd.copy(), fwd, dates)
    assert n == 30
    assert perfect == pytest.approx(1.0, abs=1e-9)
    # Zero dispersion across dates -> t is undefined by construction (documented).
    assert np.isnan(t_perfect)

    inverted, _, _ = within_date_rank_ic(-fwd, fwd, dates)
    assert inverted == pytest.approx(-1.0, abs=1e-9)

    rng = np.random.default_rng(4)
    noise, _, _ = within_date_rank_ic(rng.normal(size=len(fwd)), fwd, dates)
    assert abs(noise) < 0.2

    # Non-degenerate case: a noisy-but-informative score must yield a usable t.
    informative = fwd + rng.normal(scale=0.5, size=len(fwd))
    ic, t, n = within_date_rank_ic(informative, fwd, dates)
    assert ic > 0.4
    assert np.isfinite(t)


def test_within_date_rank_ic_never_uses_class_labels():
    """A binary-thresholded score must not be silently treated as continuous.

    Sanity: collapsing to 0/1 labels loses almost all resolution, so its IC
    must be materially different from the continuous score's IC on the same
    data — demonstrating why class-label IC is the wrong metric.
    """
    panel = _synthetic_panel(n_dates=30, n_symbols=60, d=2, seed=21)
    dates = panel["date"].to_numpy()
    fwd = panel["fwd_atr_ret_15"].to_numpy()
    continuous = fwd + 0.1 * np.random.default_rng(0).normal(size=len(fwd))

    ic_cont, _, _ = within_date_rank_ic(continuous, fwd, dates)
    labels = (continuous > np.median(continuous)).astype(float)
    ic_label, _, _ = within_date_rank_ic(labels, fwd, dates)

    assert ic_cont > 0.9
    assert ic_label < ic_cont


def test_pairwise_win_rate_is_rank_consistent():
    dates = np.array(["d1"] * 4 + ["d2"] * 4)
    scores = np.array([3.0, 1.0, 2.0, 0.0, 5.0, 4.0, 6.0, 7.0])

    wr = pairwise_win_rate(scores, dates)

    # d1: scores 3,1,2,0 -> ranks 4,2,3,1 -> win rates 1.0, 1/3, 2/3, 0.0
    assert wr[0] == pytest.approx(1.0)
    assert wr[3] == pytest.approx(0.0)
    assert wr[1] == pytest.approx(1 / 3)
    assert wr[2] == pytest.approx(2 / 3)
    # d2: 7 is the top of its date.
    assert wr[7] == pytest.approx(1.0)

    # Monotone in score within each date.
    for day in ("d1", "d2"):
        m = dates == day
        s, r = scores[m], wr[m]
        order = np.argsort(s)
        assert np.all(np.diff(r[order]) >= 0)