"""WI-009 — synthetic-data validation gate, run before any real-data claim.

A synthetic cross-section with a *known* relative-performance ordering must be
recovered by the contrastive ranker in within-date rank space. If the learner
cannot recover a planted ordering, a null result on CAD would be uninterpretable.
"""

import numpy as np
import pandas as pd
import pytest
import torch

from src.models.contrastive_ranking import (
    MAX_EMBED_DIM,
    ContrastiveRanker,
    configure_torch,
    ranknet_loss,
)
from src.models.pair_sampler import iter_pair_batches, within_date_rank_ic


def _planted_panel(n_dates=40, n_symbols=60, d=6, seed=13, noise=0.3):
    """Cross-sections whose forward return is a planted linear function of features."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2021-01-04", periods=n_dates, freq="B")
    frames = []
    for dt_ in dates:
        feats = rng.normal(size=(n_symbols, d)).astype(np.float32)
        fwd = (1.0 * feats[:, 0] - 0.8 * feats[:, 1] + noise * rng.normal(size=n_symbols)).astype(np.float32)
        f = pd.DataFrame(feats, columns=[f"f{i}" for i in range(d)])
        f["date"] = dt_
        f["symbol"] = [f"S{j}" for j in range(n_symbols)]
        f["fwd_atr_ret_15"] = fwd
        frames.append(f)
    return pd.concat(frames, ignore_index=True)


def _train(panel, feature_cols, dates, epochs=8, embed_dim=8, seed=7, lr=0.01):
    configure_torch()
    torch.manual_seed(seed)
    model = ContrastiveRanker(input_dim=len(feature_cols), embed_dim=embed_dim)
    sub = panel[panel["date"].isin(set(dates))].reset_index(drop=True)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    rng = np.random.default_rng(seed)
    model.train()
    for _ in range(epochs):
        for batch in iter_pair_batches(
            sub, feature_cols, "fwd_atr_ret_15", n_pairs_per_date=200, batch_pairs=512, rng=rng
        ):
            margin = model.pairwise_margin(
                torch.from_numpy(batch.x_win), torch.from_numpy(batch.x_los)
            )
            loss = ranknet_loss(margin)
            opt.zero_grad()
            loss.backward()
            opt.step()
    return model


def test_recovers_planted_relative_ordering():
    panel = _planted_panel()
    feature_cols = [c for c in panel.columns if c.startswith("f")]
    dates = np.sort(panel["date"].unique())
    train_dates, val_dates = dates[:30], dates[30:]

    model = _train(panel, feature_cols, train_dates)

    val = panel[panel["date"].isin(set(val_dates))].reset_index(drop=True)
    scores = model.score_numpy(val[feature_cols].to_numpy(dtype=np.float32))
    ic, t, n = within_date_rank_ic(scores, val["fwd_atr_ret_15"].to_numpy(), val["date"].to_numpy())

    assert n == len(val_dates)
    assert ic > 0.3, f"planted ordering not recovered: val rank-IC={ic:.4f}"
    assert np.isfinite(t)


def test_pairwise_comparison_is_transitive():
    """A scalar score tower must give a consistent (transitive) order."""
    model = ContrastiveRanker(input_dim=5, embed_dim=8)
    model.eval()

    x = torch.from_numpy(np.array(
        [[1.0, 0.0, 0.5, -1.0, 0.2],
         [0.5, 0.1, 0.4, -0.5, 0.1],
         [0.2, 0.2, 0.1, 0.0, -0.3]], dtype=np.float32))

    with torch.no_grad():
        p_ab = float(model.compare(x[0:1], x[1:2]))
        p_bc = float(model.compare(x[1:2], x[2:3]))
        p_ac = float(model.compare(x[0:1], x[2:3]))

    # If a out-ranks b and b out-ranks c, then a must out-rank c.
    if p_ab > 0.5 and p_bc > 0.5:
        assert p_ac > 0.5


def test_embed_dim_guardrail_and_thread_pin():
    with pytest.raises(ValueError):
        ContrastiveRanker(input_dim=4, embed_dim=MAX_EMBED_DIM + 1)

    model = ContrastiveRanker(input_dim=4, embed_dim=MAX_EMBED_DIM)
    assert model.embed_dim <= MAX_EMBED_DIM
    assert torch.get_num_threads() == 2

    # float32 throughout.
    for p in model.parameters():
        assert p.dtype == torch.float32
    out = model(torch.zeros(3, 4, dtype=torch.float32))
    assert out.dtype == torch.float32
    assert out.shape == (3,)