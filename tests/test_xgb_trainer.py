"""WI-016 step 1 — horizon-specific embargo regression tests.

The D-016 precondition fix makes the purge embargo per-target
(`max(20, horizon)`) instead of the flat WI-009 20-bar value, for *both* split
paths: the `PurgedWalkForwardSplit` CV folds and every `purged_holdout` call
(CV calibration + the final model's fit/calibration split).

Verify: `uv run pytest tests/test_xgb_trainer.py -k 'embargo or purged_holdout'`
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.xgb_trainer import (
    EMBARGO_FLOOR_TD,
    PurgedWalkForwardSplit,
    horizon_embargo,
    purged_holdout,
    resolve_embargo,
    target_horizon,
)


def _tdates(n: int = 600) -> np.ndarray:
    """`n` unique business-day datetimes (trading-date positions)."""
    return pd.date_range("2010-01-01", periods=n, freq="B").to_numpy()


def _pos_gap(uniq: np.ndarray, earlier: np.ndarray, later: np.ndarray) -> int:
    """Trading-date position gap between the last `earlier` and first `later` date."""
    return int(np.searchsorted(uniq, later.min()) - np.searchsorted(uniq, earlier.max()))


# --------------------------------------------------------------------------- #
# Helper semantics
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "horizon,expected",
    [(3, 20), (8, 20), (15, 20), (20, 20), (55, 55), (144, 144), (233, 233)],
)
def test_horizon_embargo_keeps_floor_and_covers_horizon(horizon, expected):
    assert horizon_embargo(horizon) == expected
    assert horizon_embargo(horizon) >= EMBARGO_FLOOR_TD


def test_target_horizon_maps_and_parses():
    assert target_horizon("y_15d_high") == 15
    assert target_horizon("y_20d_stay") == 20
    # WI-016 fib-ladder names resolve their own horizon by parse.
    assert target_horizon("y_144d_profit") == 144
    assert target_horizon("y_233d_vertical") == 233
    with pytest.raises(KeyError):
        target_horizon("not_a_target")


def test_cli_default_cannot_weaken_but_may_strengthen():
    # Flat default (20) is ignored when the horizon is larger.
    assert resolve_embargo("y_144d_profit", 20) == 144
    assert resolve_embargo("y_233d_profit", 20) == 233
    assert resolve_embargo("y_144d_profit", None) == 144
    # Short targets keep the 20-bar floor.
    assert resolve_embargo("y_15d_high", 20) == 20
    assert resolve_embargo("y_20d_up", 15) == 20
    # An explicit larger CLI/config value may only strengthen.
    assert resolve_embargo("y_15d_high", 50) == 50
    assert resolve_embargo("y_144d_profit", 200) == 200


# --------------------------------------------------------------------------- #
# Split path 1 — PurgedWalkForwardSplit CV folds
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("h", [144, 233])
def test_fold_train_dates_respect_horizon_embargo(h):
    dates = _tdates(600)
    uniq = np.sort(pd.unique(dates))
    splitter = PurgedWalkForwardSplit(n_splits=5, embargo_td=horizon_embargo(h))
    folds = list(splitter.split(dates))
    assert folds, "expected non-empty folds for the fixture"
    for tr, va in folds:
        assert tr.size and va.size
        gap = _pos_gap(uniq, dates[tr], dates[va])
        assert gap > h, f"embargo violated for h={h}: gap={gap}"


@pytest.mark.parametrize("h", [144, 233])
def test_fold_train_dates_respect_cli_default_embargo(h):
    """`--embargo 20` (the CLI default) must not weaken a long-horizon target."""
    dates = _tdates(600)
    uniq = np.sort(pd.unique(dates))
    eff = resolve_embargo(f"y_{h}d_profit", 20)
    splitter = PurgedWalkForwardSplit(n_splits=5, embargo_td=eff)
    for tr, va in splitter.split(dates):
        gap = _pos_gap(uniq, dates[tr], dates[va])
        assert gap > h


# --------------------------------------------------------------------------- #
# Split path 2 — purged_holdout (calibration + final holdout)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("h", [144, 233])
def test_purged_holdout_respects_horizon_embargo(h):
    dates = _tdates(600)
    idx = np.arange(len(dates))
    uniq = np.sort(pd.unique(dates))
    fit_i, cal_i = purged_holdout(dates, idx, 0.20, horizon_embargo(h))
    assert fit_i.size and cal_i.size
    gap = _pos_gap(uniq, dates[fit_i], dates[cal_i])
    assert gap > h, f"calibration holdout embargo violated for h={h}: gap={gap}"


def test_purged_holdout_twenty_bar_floor_unchanged_for_short_targets():
    dates = _tdates(200)
    idx = np.arange(len(dates))
    uniq = np.sort(pd.unique(dates))
    fit_i, cal_i = purged_holdout(dates, idx, 0.20, horizon_embargo(15))
    gap = _pos_gap(uniq, dates[fit_i], dates[cal_i])
    assert gap > 20
