"""WI-009c Step 2 — continuous-target probabilities, units, fold/calibration leakage.

Locks the acceptance criteria of
`docs/plans/2026-10-25-WI-009c-classifier-route.md` Step 2(b):

* calibration residuals are disjoint from each model's training dates;
* purge/embargo is 20 trading days;
* probabilities are finite and within [0, 1];
* event calculations use the proper units (ATR-dollar up/down vs relative stay);
* overlap is not silently forced into a partition.
"""
import numpy as np
import pandas as pd
import pytest

from src.models.continuous_targets import (
    ATR_PRICE_COLUMN,
    CALIB_FRACTION,
    CONTINUOUS_TARGET,
    EMBARGO_TD,
    INITIAL_TRAIN_FRACTION,
    STAY_RET_MAX,
    UP_MULT,
    calibration_summary,
    composite_score,
    event_probabilities,
    event_thresholds,
    marginal_calibration,
    mirror_check,
    purged_fit_calibration_split,
    purged_fold_plan,
    realized_events,
    residual_quantiles,
)


def _biz_dates(n: int, start: str = "2020-01-01") -> np.ndarray:
    return np.sort(pd.to_datetime(pd.date_range(start, periods=n, freq="B")).to_numpy())


# --------------------------------------------------------------------------- #
# event units
# --------------------------------------------------------------------------- #
def test_route_constants_match_the_fixed_route():
    assert CONTINUOUS_TARGET == "fwd_atr_ret_20"
    assert ATR_PRICE_COLUMN == "atr_pct_20"
    assert UP_MULT == 2.0 and STAY_RET_MAX == 0.05 and EMBARGO_TD == 20


def test_mirror_check_confirms_the_split_policy_is_reused_not_redefined():
    m = mirror_check()
    assert m["calib_fraction_matches_xgb_trainer"] is True
    assert m["initial_train_fraction_matches_xgb_trainer"] is True
    assert m["atr_window_matches_targets"] is True
    assert m["trend_horizon_matches_targets"] is True
    assert CALIB_FRACTION == 0.20 and INITIAL_TRAIN_FRACTION == 0.40


def test_up_and_down_thresholds_are_the_atr_multiple_in_target_units():
    t = event_thresholds(np.zeros(3), np.full(3, 0.02))
    assert np.allclose(t["up"], 2.0) and np.allclose(t["down"], -2.0)


def test_stay_threshold_is_row_specific_and_converts_relative_5pct_into_atr_units():
    t = event_thresholds(np.zeros(3), np.array([0.01, 0.02, 0.05]))
    assert np.allclose(t["stay_abs"], [5.0, 2.5, 1.0])


def test_event_probabilities_reject_unusable_atr_pct():
    with pytest.raises(ValueError):
        event_probabilities(np.zeros(2), np.zeros(5), np.array([0.02, np.nan]))
    with pytest.raises(ValueError):
        event_probabilities(np.zeros(2), np.zeros(5), np.array([0.02, 0.0]))


def test_point_mass_residual_reproduces_the_label_events_exactly():
    """A single zero residual makes the ECDF a point mass: the events become labels."""
    r = np.array([0.0])
    p = event_probabilities(np.array([0.0, 2.0, -2.0, 3.0]), r, np.full(4, 0.02))
    # forecast 0.0 -> neither 2xATR up nor down; within +/-5% (threshold 2.5 ATR)
    assert p["p_up"][0] == 0.0 and p["p_down"][0] == 0.0 and p["p_stay"][0] == 1.0
    # exactly +2.0 is an up event (>= is inclusive, matching src.targets)
    assert p["p_up"][1] == 1.0 and p["p_stay"][1] == 1.0
    assert p["p_down"][2] == 1.0
    assert p["p_up"][3] == 1.0 and p["p_stay"][3] == 0.0


def test_stay_probability_depends_on_the_atr_price_conversion():
    """Same forecast, different ATR/price: 2xATR can sit inside or outside the 5% band."""
    r = np.array([0.0])
    low_atr = event_probabilities(np.array([2.0]), r, np.array([0.02]))
    high_atr = event_probabilities(np.array([2.0]), r, np.array([0.03]))
    assert low_atr["p_stay"][0] == 1.0  # 2xATR = 4% < 5%
    assert high_atr["p_stay"][0] == 0.0  # 2xATR = 6% > 5%


def test_overlap_is_preserved_and_not_forced_into_a_partition():
    r = np.array([0.0])
    p = event_probabilities(np.array([2.0]), r, np.array([0.02]))
    assert p["p_up"][0] == 1.0 and p["p_stay"][0] == 1.0
    assert p["overlap_up_stay"][0] == 1.0
    # the raw +/-5% stay event is NOT 1 - P(up) - P(down)
    assert p["p_stay"][0] != pytest.approx(1.0 - p["p_up"][0] - p["p_down"][0])
    # the exclusive variant does mirror the y_20d_stay label definition
    assert p["p_stay_exclusive"][0] == 0.0


def test_probabilities_are_finite_and_bounded_on_random_input():
    rng = np.random.default_rng(7)
    resid = rng.normal(scale=1.5, size=5000)
    f = rng.normal(scale=1.0, size=4000)
    atr = rng.uniform(0.005, 0.08, size=4000)
    p = event_probabilities(f, resid, atr)
    for k in ("p_up", "p_down", "p_stay", "p_stay_exclusive", "overlap_up_stay", "overlap_down_stay"):
        v = p[k]
        assert np.isfinite(v).all(), k
        assert v.min() >= 0.0 and v.max() <= 1.0, k
    assert (p["p_stay_exclusive"] <= p["p_stay"] + 1e-12).all()


def test_probabilities_are_monotone_in_the_forecast():
    resid = np.linspace(-3.0, 3.0, 201)
    f = np.linspace(-3.0, 3.0, 51)
    p = event_probabilities(f, resid, np.full(f.size, 0.02))
    assert np.all(np.diff(p["p_up"]) >= -1e-12)
    assert np.all(np.diff(p["p_down"]) <= 1e-12)


def test_zero_spread_residual_sample_still_returns_finite_probabilities():
    p = event_probabilities(np.zeros(3), np.zeros(10), np.full(3, 0.02))
    assert np.isfinite(p["p_up"]).all() and p["p_up"].max() == 0.0


def test_empty_or_nonfinite_residual_sample_is_refused():
    with pytest.raises(ValueError):
        event_probabilities(np.zeros(2), np.array([np.nan]), np.full(2, 0.02))


# --------------------------------------------------------------------------- #
# realized events mirror src.targets
# --------------------------------------------------------------------------- #
def test_realized_events_mirror_the_label_definitions():
    y = np.array([3.0, -3.0, 0.0, 1.0])
    atr = np.full(4, 0.02)  # 5% band == 2.5 ATR
    e = realized_events(y, atr)
    assert e["up"].tolist() == [True, False, False, False]
    assert e["down"].tolist() == [False, True, False, False]
    assert e["stay"].tolist() == [False, False, True, True]
    assert e["stay_exclusive"].tolist() == [False, False, True, True]


def test_composite_score_is_p_up_minus_p_down():
    assert np.allclose(composite_score([0.3, 0.1], [0.2, 0.4]), [0.1, -0.3])


# --------------------------------------------------------------------------- #
# fold plan / calibration leakage
# --------------------------------------------------------------------------- #
def test_fit_calibration_split_has_a_20td_purge_gap_and_is_disjoint():
    fit, cal, gap = purged_fit_calibration_split(np.arange(100), calib_fraction=0.20, embargo_td=20)
    assert len(cal) == 20 and gap == 20
    assert set(fit).isdisjoint(set(cal))
    assert fit.max() + gap + 1 == cal.min()
    assert len(fit) + gap + len(cal) == 100


def test_fit_calibration_split_rejects_a_bad_fraction():
    with pytest.raises(ValueError):
        purged_fit_calibration_split(np.arange(50), calib_fraction=1.0)


def test_fold_plan_keeps_calibration_residuals_out_of_the_training_dates():
    """Acceptance: calibration residuals are disjoint from each model's training dates."""
    plan = purged_fold_plan(_biz_dates(400), n_splits=5, embargo_td=EMBARGO_TD)
    viable = [r for r in plan if "skipped" not in r]
    assert len(viable) == 5
    for r in viable:
        fit, cal, val = set(r["fit_pos"]), set(r["cal_pos"]), set(r["val_pos"])
        assert fit.isdisjoint(cal), r["fold"]
        assert fit.isdisjoint(val), r["fold"]
        assert cal.isdisjoint(val), r["fold"]
        assert r["gap_fit_cal"] >= EMBARGO_TD
        assert r["gap_fit_val"] >= EMBARGO_TD
        assert r["gap_cal_val"] >= 0
        assert r["purge_ok"] is True
        # chronological ordering: every fit date precedes every calibration date
        assert r["fit_pos"].max() < r["cal_pos"].min() < r["val_pos"].min()
        assert r["fit_max"] < r["cal_min"] <= r["cal_max"] < r["val_min"]


def test_fold_plan_uses_date_positions_so_validation_never_overlaps_training():
    dates = _biz_dates(300)
    plan = purged_fold_plan(dates, n_splits=3, embargo_td=20)
    for r in plan:
        if "skipped" in r:
            continue
        val_dates = set(dates[r["val_pos"]])
        fit_dates = set(dates[r["fit_pos"]])
        cal_dates = set(dates[r["cal_pos"]])
        assert val_dates.isdisjoint(fit_dates) and val_dates.isdisjoint(cal_dates)


def test_fold_plan_skips_rather_than_leaks_when_the_window_is_too_short():
    plan = purged_fold_plan(_biz_dates(60), n_splits=5, embargo_td=20)
    # early folds have no room for a 20td purge plus a calibration block
    assert any("skipped" in r for r in plan)
    assert all(r["purge_ok"] for r in plan if "skipped" not in r)


# --------------------------------------------------------------------------- #
# calibration diagnostics
# --------------------------------------------------------------------------- #
def test_calibration_summary_is_exact_for_a_perfect_forecast():
    z = np.array([0.0, 1.0, 0.0, 1.0, 1.0])
    s = calibration_summary(z, z)
    assert s["n"] == 5 and s["bias"] == pytest.approx(0.0)
    assert s["brier"] == pytest.approx(0.0)


def test_marginal_calibration_reports_all_three_events_and_the_overlap_mass():
    y = np.array([3.0, -3.0, 0.0, 0.5])
    atr = np.full(4, 0.02)
    pred = {
        "p_up": np.array([1.0, 0.0, 0.0, 0.0]),
        "p_down": np.array([0.0, 1.0, 0.0, 0.0]),
        "p_stay": np.array([1.0, 1.0, 1.0, 1.0]),
        "p_stay_exclusive": np.array([0.0, 0.0, 1.0, 1.0]),
        "overlap_up_stay": np.array([1.0, 0.0, 0.0, 0.0]),
        "overlap_down_stay": np.array([0.0, 1.0, 0.0, 0.0]),
    }
    out = marginal_calibration(pred, y, atr)
    assert out["up"]["realized_rate"] == pytest.approx(0.25)
    assert out["down"]["realized_rate"] == pytest.approx(0.25)
    assert out["stay"]["realized_rate"] == pytest.approx(0.5)
    assert out["stay_exclusive"]["realized_rate"] == pytest.approx(0.5)
    # P(up)+P(down)+P(stay) = (1+1+4)/4 = 1.5 — above 1, because overlap is preserved
    assert out["masses"]["mean_sum_up_down_stay"] == pytest.approx(1.5)
    assert out["masses"]["mean_overlap_up_stay"] == pytest.approx(0.25)


def test_residual_quantiles_summarise_the_ecdf_shape():
    q = residual_quantiles(np.linspace(-1.0, 1.0, 101))
    assert q["n"] == 101
    assert q["q50"] == pytest.approx(0.0, abs=1e-9)
    assert q["q05"] < q["q50"] < q["q95"]
