"""Candidate feature builders for run targets (WI-015): fib-spacing features
and derived momentum/run-condition features."""

from src.perfanalytics.features.panel import (
    FIB_GRID,
    FAMILIES,
    MIN_HURST_WINDOW,
    build_feature_panel,
    compute_fib_features,
    dataset_dir,
    family_of,
    feature_columns,
    window_of,
)

__all__ = [
    "FIB_GRID",
    "FAMILIES",
    "MIN_HURST_WINDOW",
    "build_feature_panel",
    "compute_fib_features",
    "dataset_dir",
    "family_of",
    "feature_columns",
    "window_of",
]
