# test_e5_baseline_horizon_nans.py — regression for the WI-012 horizon bug
#
# WI-012 (2026-10-26): build_e5_panel dropped NaN rows on fwd_atr_ret_15 only,
# so --horizon 20 left tail rows (last ~20 bars per symbol, incl. delistings)
# with NaN fwd_atr_ret_20 in the panel; per-date Spearman IC on those dates
# returned NaN and the non-NaN-aware mean turned the WHOLE single-factor table
# into NaN on both markets. Fix: dropna covers both forward columns.
#
# Locks: after build_e5_panel, neither fwd_atr_ret_15 nor fwd_atr_ret_20
# contains NaN, and single_factor_ics at BOTH horizons yields finite
# (non-NaN) mean IC + t for every factor on the real-data panel.

import numpy as np
import pytest

from src.factors.e5_baseline import E5_FACTORS, build_e5_panel, single_factor_ics

pytestmark = pytest.mark.filterwarnings("ignore::RuntimeWarning")


def _panel():
    p = build_e5_panel("CAD")
    if len(p) == 0:
        pytest.skip("no raw rows available for CAD e5 panel")
    return p


def test_panel_has_no_nan_forward_returns():
    p = _panel()
    n15 = int(p["fwd_atr_ret_15"].isna().to_numpy().sum())
    n20 = int(p["fwd_atr_ret_20"].isna().to_numpy().sum())
    assert n15 == 0, "fwd_atr_ret_15 NaN rows survived build_e5_panel"
    assert n20 == 0, "fwd_atr_ret_20 NaN rows survived build_e5_panel (WI-012 bug)"


def test_single_factor_ics_finite_at_both_horizons():
    p = _panel()
    for horizon in (15, 20):
        ics = single_factor_ics(p, horizon=horizon)
        assert set(ics) == set(E5_FACTORS)
        for fac, (mean_ic, t, dates) in ics.items():
            assert dates > 0
            assert np.isfinite(mean_ic), f"{fac} mean IC not finite at horizon {horizon}: {mean_ic}"
            assert np.isfinite(t), f"{fac} t not finite at horizon {horizon}: {t}"