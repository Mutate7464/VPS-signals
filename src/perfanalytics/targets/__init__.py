"""Run-target labelers (WI-015). Continuous targets, point-in-time,
strictly forward-looking evaluation windows [t+1, t+k]; thresholds use only
trailing (<= t) data."""

from src.perfanalytics.targets.labelers import (
    ATR_WINDOW,
    DEFAULT_HORIZONS,
    DIAG_STEMS,
    RUN_ATR_MULT,
    TARGET_STEMS,
    compute_run_targets,
    target_columns,
    target_value_columns,
)
from src.perfanalytics.targets.dataset import (
    BOTH_ORDER,
    build_run_targets,
    dataset_dir,
    resolve_markets,
)

__all__ = [
    "ATR_WINDOW",
    "BOTH_ORDER",
    "DEFAULT_HORIZONS",
    "DIAG_STEMS",
    "RUN_ATR_MULT",
    "TARGET_STEMS",
    "build_run_targets",
    "compute_run_targets",
    "dataset_dir",
    "resolve_markets",
    "target_columns",
    "target_value_columns",
]
