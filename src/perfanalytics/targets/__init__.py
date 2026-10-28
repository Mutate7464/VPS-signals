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

__all__ = [
    "ATR_WINDOW",
    "DEFAULT_HORIZONS",
    "DIAG_STEMS",
    "RUN_ATR_MULT",
    "TARGET_STEMS",
    "compute_run_targets",
    "target_columns",
    "target_value_columns",
]
