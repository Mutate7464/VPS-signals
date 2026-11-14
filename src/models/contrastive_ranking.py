"""Contrastive / pairwise ranking model for relative asset ranking (WI-009).

Architecture choice
-------------------
A **shared encoder + scalar scoring tower** ("Siamese with a score head"),
not a two-tower similarity head. Why: ranking requires a *consistent* ordering
across the universe (acceptance criterion 1). A scalar score per asset gives a
transitive order by construction — comparing any two assets is just
`score(x1) - score(x2)` — whereas a similarity head can be non-transitive.
The two arms still share all weights, and the pairwise loss is computed on
`(score(winner) - score(loser))`, so this is a contrastive/pairwise learner.

Guardrails honoured here
------------------------
* CPU only, `torch.set_num_threads(2)` (never `-1`).
* float32 everywhere; `embed_dim <= 64` is enforced.
* Trained on pairs streamed per date by `src.models.pair_sampler`; this module
  never enumerates a pair set itself.
* No future information: the model consumes only whatever trailing feature
  columns it is handed.
* **Input transform.** The 89 CAD features are raw indicator values spanning
  ~11 orders of magnitude (`amihud_5` reaches 1.75e11), so an untransformed
  first layer produces astronomic initial margins and a diverging pairwise loss
  (WI-009b observed mean epoch loss ~9e4). The module therefore carries a
  winsorise+standardise transform as **buffers**, initialised to the identity so
  untrained models and the WI-009 pilot path are numerically unchanged. The
  trainer fits it on **training-fold rows only** (`fit_input_transform`); because
  the buffers live in the state dict, the inference path (`score_numpy`,
  `load_model`, `scripts/rank_assets.py`) needs no changes and stays consistent
  with training.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

MAX_EMBED_DIM = 64
NUM_THREADS = 2
# Winsorisation quantiles of the input transform (train-fold only).
DEFAULT_LO_Q = 0.01
DEFAULT_HI_Q = 0.99
SIGMA_EPS = 1e-6


def configure_torch() -> None:
    """Pin torch to the host budget (2 vCPU / 8 GB, no swap)."""
    torch.set_num_threads(NUM_THREADS)
    try:
        if torch.get_num_interop_threads() != 1:
            torch.set_num_interop_threads(1)
    except RuntimeError:
        # Already initialised by another call site; intra-op threads still pinned.
        pass


class ContrastiveRanker(nn.Module):
    """Shared-encoder scalar scorer trained with a pairwise (rank) objective."""

    def __init__(self, input_dim: int, embed_dim: int = 32, hidden_dim: int | None = None):
        super().__init__()
        if embed_dim > MAX_EMBED_DIM:
            raise ValueError(f"embed_dim must be <= {MAX_EMBED_DIM}, got {embed_dim}")

        configure_torch()
        self.input_dim = int(input_dim)
        self.embed_dim = int(embed_dim)
        hidden = int(hidden_dim or max(embed_dim * 2, 32))

        # Input transform buffers — identity until `fit_input_transform` is
        # called with training-fold rows, so an untrained model scores raw
        # features exactly as before.
        self.register_buffer("input_lo", torch.full((self.input_dim,), float("-inf"), dtype=torch.float32))
        self.register_buffer("input_hi", torch.full((self.input_dim,), float("inf"), dtype=torch.float32))
        self.register_buffer("input_mu", torch.zeros(self.input_dim, dtype=torch.float32))
        self.register_buffer("input_sigma", torch.ones(self.input_dim, dtype=torch.float32))

        self.encoder = nn.Sequential(
            nn.Linear(self.input_dim, hidden, dtype=torch.float32),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden, self.embed_dim, dtype=torch.float32),
            nn.ReLU(),
        )
        self.score_head = nn.Linear(self.embed_dim, 1, dtype=torch.float32)

    # ---- input transform -------------------------------------------------
    def fit_input_transform(
        self,
        x: np.ndarray,
        lo_q: float = DEFAULT_LO_Q,
        hi_q: float = DEFAULT_HI_Q,
    ) -> dict:
        """Fit winsorise + standardise statistics on TRAINING-FOLD rows only.

        Using validation rows here would be a leak, so the caller is responsible
        for passing the train slice (`scripts/train_contrastive.py` does).

        Returns a small dict of the fitted statistics for logging.
        """
        x = np.asarray(x, dtype="float64")
        if x.ndim != 2 or x.shape[1] != self.input_dim:
            raise ValueError(f"expected (n, {self.input_dim}) array, got {x.shape}")
        finite = np.isfinite(x)
        all_finite = bool(finite.all())
        xs = x if all_finite else np.where(finite, x, np.nan)
        qf = np.percentile if all_finite else np.nanpercentile
        with np.errstate(all="ignore"):
            lo = qf(xs, lo_q * 100.0, axis=0) if lo_q > 0 else np.full(self.input_dim, -np.inf)
            hi = qf(xs, hi_q * 100.0, axis=0) if hi_q < 1 else np.full(self.input_dim, np.inf)
            xw = np.clip(xs, lo, hi)
            mu = (np.mean if all_finite else np.nanmean)(xw, axis=0)
            sigma = (np.std if all_finite else np.nanstd)(xw, axis=0)
        lo = np.where(np.isfinite(lo), lo, -np.inf)
        hi = np.where(np.isfinite(hi), hi, np.inf)
        mu = np.where(np.isfinite(mu), mu, 0.0)
        # A constant feature would divide by zero: fall back to identity scaling.
        sigma = np.where(np.isfinite(sigma) & (sigma > SIGMA_EPS), sigma, 1.0)

        n_clipped = int(np.count_nonzero(np.abs(xw - xs)[finite] > 0))
        with torch.no_grad():
            self.input_lo.copy_(torch.from_numpy(lo.astype(np.float32)))
            self.input_hi.copy_(torch.from_numpy(hi.astype(np.float32)))
            self.input_mu.copy_(torch.from_numpy(mu.astype(np.float32)))
            self.input_sigma.copy_(torch.from_numpy(sigma.astype(np.float32)))
        return {
            "lo_q": float(lo_q),
            "hi_q": float(hi_q),
            "n_rows": int(x.shape[0]),
            "n_clipped_values": n_clipped,
            "n_identity_sigma": int(np.count_nonzero(sigma == 1.0)),
        }

    def _transform(self, x: torch.Tensor) -> torch.Tensor:
        x = x.to(torch.float32)
        x = torch.clamp(x, self.input_lo, self.input_hi)
        return (x - self.input_mu) / self.input_sigma

    # ---- shared arm -----------------------------------------------------
    def embed(self, x: torch.Tensor) -> torch.Tensor:
        return self.encoder(self._transform(x))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Scalar score per row: (m, input_dim) -> (m,)."""
        return self.score_head(self.embed(x)).squeeze(-1)

    # ---- pairwise view --------------------------------------------------
    def pairwise_margin(self, x_win: torch.Tensor, x_los: torch.Tensor) -> torch.Tensor:
        """score(winner) - score(loser), the ranking logit. (m,) -> (m,)"""
        return self(x_win) - self(x_los)

    def compare(self, x1: torch.Tensor, x2: torch.Tensor) -> torch.Tensor:
        """P(x1 out-ranks x2) in [0, 1]; consistent because scores are scalar."""
        return torch.sigmoid(self.pairwise_margin(x1, x2))

    # ---- inference ------------------------------------------------------
    @torch.no_grad()
    def score_numpy(self, x: np.ndarray) -> np.ndarray:
        self.eval()
        t = torch.from_numpy(np.ascontiguousarray(x, dtype=np.float32))
        return self(t).cpu().numpy().astype(np.float64)


def ranknet_loss(margin: torch.Tensor) -> torch.Tensor:
    """Logistic pairwise loss: -log sigmoid(score_win - score_los)."""
    return F.softplus(-margin).mean()


def margin_rank_loss(margin: torch.Tensor, margin_value: float = 0.5) -> torch.Tensor:
    """Hinge-style pairwise loss on the score gap."""
    return F.relu(margin_value - margin).mean()


def save_model(model: ContrastiveRanker, path: str | Path, feature_cols: Sequence[str]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": model.state_dict(),
            "input_dim": model.input_dim,
            "embed_dim": model.embed_dim,
            "feature_cols": list(feature_cols),
        },
        path,
    )
    return path


def load_model(path: str | Path) -> tuple[ContrastiveRanker, list[str]]:
    blob = torch.load(Path(path), map_location="cpu", weights_only=False)
    model = ContrastiveRanker(blob["input_dim"], blob["embed_dim"])
    model.load_state_dict(blob["state_dict"])
    model.eval()
    return model, list(blob["feature_cols"])