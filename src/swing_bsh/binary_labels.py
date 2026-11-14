"""WI-035 step 1 — three binary first-touch labels over the WI-032 swing geometry.

`b_profit` = implied-side barrier touched first, `b_stop` = adverse barrier
touched first, `b_hold` = neither barrier touched inside the vertical barrier
(the three labels are a mutually exclusive/exhaustive decomposition of the
WI-032 `y` in {HOLD, BUY, SELL}).

The event geometry (trailing swing extremes + first-touch barriers) is the one
in :mod:`src.swing_bsh.events`, reached through
:func:`src.swing_bsh.train.build_event_panel`; that builder also carries the
frozen fib-rule return `r_frozen` (WI-028 entry + WI-030 exit), which is a
forward outcome and **never** a feature. The ρ>0.4 uniqueness prune (the set
WI-034 would have produced, computed inline per admin direction 2026-11-09)
lives in :func:`kept_features`.

Symbol-sequential reads, float32, `n_jobs=2` upstream.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.feature_engine import wi016_feature_names
from src.swing_bsh import train
from src.swing_bsh.events import BUY, HOLD, SELL
from src.swing_bsh.probe import prune_features

RHO_THRESHOLD = 0.4
"""Inline uniqueness prune (WI-034 was skipped: |Spearman ρ| > 0.4)."""

BINARY_COLUMNS: tuple[str, ...] = ("b_profit", "b_stop", "b_hold")
NON_FEATURE_PREFIXES: tuple[str, ...] = ("b_", "r_", "fwd")

__all__ = [
    "BINARY_COLUMNS", "NON_FEATURE_PREFIXES", "RHO_THRESHOLD", "add_binary_labels",
    "binary_targets", "build_binary_panel", "canonical_mask", "feature_names",
    "is_leakage_column", "kept_features", "load_panel_checkpoint", "rho_prune_report",
    "save_panel_checkpoint",
]


def binary_targets(y, state) -> dict[str, np.ndarray]:
    """Decompose the WI-032 first-touch label into profit/stop/hold binaries.

    `y` is the 3-class label (HOLD/BUY/SELL) and `state` the swing side; the
    implied side is up at `at_bottom` (profit = BUY) and down at `at_top`
    (profit = SELL). Returns int8 arrays that sum to one per row.
    """
    y = np.asarray(y, dtype="int8")
    bottom = np.asarray(state) == "at_bottom"
    profit = np.where(bottom, y == BUY, y == SELL).astype("int8")
    stop = np.where(bottom, y == SELL, y == BUY).astype("int8")
    hold = (y == HOLD).astype("int8")
    return {"b_profit": profit, "b_stop": stop, "b_hold": hold}


def add_binary_labels(panel: pd.DataFrame) -> pd.DataFrame:
    """Return the panel with `b_profit/b_stop/b_hold` (int8) appended."""
    targets = binary_targets(panel["y"].to_numpy(dtype="int8"), panel["state"].to_numpy())
    extra = pd.DataFrame({name: targets[name] for name in BINARY_COLUMNS}, index=panel.index)
    return pd.concat([panel, extra], axis=1)


def canonical_mask(panel: pd.DataFrame, k: float = train.GATE_K, h: int = train.GATE_H) -> np.ndarray:
    """At-bottom gate-geometry rows with a priced frozen baseline (WI-033 §2)."""
    return (
        (panel["state"].to_numpy() == "at_bottom")
        & (panel["k"].to_numpy(dtype="float64") == float(k))
        & (panel["horizon"].to_numpy(dtype="float64") == float(h))
        & np.isfinite(panel["r_frozen"].to_numpy(dtype="float64"))
    )


def is_leakage_column(name: str) -> bool:
    """True for label / forward-outcome columns that must never be features."""
    return name.startswith(NON_FEATURE_PREFIXES)


def feature_names(names) -> list[str]:
    """Drop label / forward-outcome (`b_*`, `r_*`, `fwd*`) columns from a list."""
    return [n for n in names if not is_leakage_column(n)]


def kept_features(panel: pd.DataFrame, threshold: float = RHO_THRESHOLD, features=None):
    """Keep one representative per |Spearman ρ| > `threshold` feature cluster."""
    feats = list(features) if features is not None else wi016_feature_names()
    return prune_features(panel, feats, threshold=threshold)


def build_binary_panel(market: str, *, min_date: str = train.MIN_DATE,
                       allow_fixture: bool = False, max_symbols: int | None = None,
                       k_values=train.K_VALUES, barriers=train.BARRIERS) -> pd.DataFrame:
    """One market's swing-event panel + the three binary labels (symbol-sequential).

    Row schema = the WI-032 `sample_events` schema (`symbol, date, state, y,
    horizon`) + event geometry `k`, raw `close`/`atr`, frozen-rule return
    `r_frozen`, the WI-016 feature grid and `b_profit/b_stop/b_hold`.
    """
    panel = train.build_event_panel(
        market, k_values=k_values, barriers=barriers, min_date=min_date,
        allow_fixture=allow_fixture, max_symbols=max_symbols,
    )
    if panel.empty:
        return panel
    return add_binary_labels(panel)


def rho_prune_report(dropped: dict[str, str], kept: list[str]) -> str:
    """One-line provenance string for the summary (kept/dropped counts)."""
    return f"{len(kept)} kept / {len(kept) + len(dropped)} candidate features (ρ>{RHO_THRESHOLD} prune)"


def panel_checkpoint_path(out_dir, market: str) -> Path:
    """Checkpoint/report path helper shared by the train/eval modules."""
    return Path(out_dir) / f"wi035_panel_{market}.parquet"


def save_panel_checkpoint(panel: pd.DataFrame, out_dir, market: str) -> Path:
    """Cache one market's binary panel (float32 parquet) — mirrors per-market checkpointing."""
    path = panel_checkpoint_path(out_dir, market)
    path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(path, index=False)
    return path


def load_panel_checkpoint(out_dir, market: str) -> pd.DataFrame | None:
    """Load a cached binary panel, or `None` when the checkpoint is absent."""
    path = panel_checkpoint_path(out_dir, market)
    if not path.exists():
        return None
    return pd.read_parquet(path)
