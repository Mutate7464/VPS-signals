"""Feature-target alignment diagnostics (WI-015): per-target rank/spearman
association of candidate features, with same-sign skill bar carried from
WI-009b/009c."""

from src.perfanalytics.correlation.alignment import (
    BLOCK_DATES,
    BOOTSTRAP_SEED,
    EMBARGO_TD,
    N_BOOTSTRAP,
    N_SPLITS,
    block_bootstrap_margin,
    daily_spearman_ic,
    fold_val_positions,
    run_alignment,
    target_columns,
    write_reports,
)

__all__ = [
    "BLOCK_DATES",
    "BOOTSTRAP_SEED",
    "EMBARGO_TD",
    "N_BOOTSTRAP",
    "N_SPLITS",
    "block_bootstrap_margin",
    "daily_spearman_ic",
    "fold_val_positions",
    "run_alignment",
    "target_columns",
    "write_reports",
]
