"""WI-016 step 6 action-synthesis tests (decision-rule v2).

Verify: `uv run pytest tests/test_wi016_actions.py`
"""

from __future__ import annotations

import inspect

import numpy as np
import pandas as pd
import pytest

from src.factors.e5_baseline import E5_FACTORS
from src.wi016 import actions
from src.wi016.actions import (
    COST_BPS,
    META_MIN_PROB,
    MIN_RECALL_FOR_FLOOR,
    SENSITIVITY_COSTS,
    SENSITIVITY_SLIPPAGE,
    SHORTLIST_COLUMNS,
    SLIPPAGE_BPS,
    band_sensitivity,
    breakeven_prob,
    build_shortlist,
    calibrate_prob_floor,
    decide_action,
    expected_edge_bps,
    shortlist_path,
    size_from_meta,
    write_shortlist_parquet,
)
from src.wi016.meta_labeler import (
    CLEARED_TARGETS,
    PRIMARY_COLUMN,
    primary_pct_rank,
    target_grid,
)

TOTAL_COST = COST_BPS + SLIPPAGE_BPS


class _FakeModel:
    """Deterministic stand-in for `CalibratedXGB` (first feature = probability)."""

    def __init__(self, offset: float = 0.0):
        self.offset = offset

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return np.clip(X[:, 0].astype("float64") + self.offset, 0.0, 1.0)


def _panel(n_dates: int = 10, per_date: int = 100, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = np.repeat(pd.date_range("2020-01-01", periods=n_dates, freq="B"), per_date)
    n = n_dates * per_date
    frame = pd.DataFrame({
        "date": dates,
        "symbol": np.tile([f"S{i:03d}" for i in range(per_date)], n_dates),
        "close": np.float32(100.0),
        "atr": np.float32(3.0),
        PRIMARY_COLUMN: rng.normal(0, 1, n).astype("float32"),
        "f_signal": rng.random(n).astype("float32"),
    })
    for f in E5_FACTORS:
        frame[f] = rng.normal(0, 1, n).astype("float32")
    return frame


def _meta_result(features=("f_signal",)) -> dict:
    return {
        "market": "CAD",
        "targets": {
            t: {"features": list(features), "final_model": _FakeModel(), "final_calibration": "isotonic",
                "horizon": target_grid(t)[1], "k": target_grid(t)[0]}
            for t in CLEARED_TARGETS
        },
    }


def _well_calibrated_oof(n: int = 4000, seed: int = 7):
    """OOF scores that are exactly calibrated: P(y=1 | p) = p."""
    rng = np.random.default_rng(seed)
    p = rng.uniform(0.0, 1.0, n)
    y = (rng.uniform(size=n) < p).astype("int8")
    return p, y


# --------------------------------------------------------------------------- #
# Cost-aware decision rule v2
# --------------------------------------------------------------------------- #
def test_expected_edge_bps_is_symmetric_at_a_coin_flip():
    flat = expected_edge_bps(0.5, close=100.0, atr=3.0, k=1.5)
    assert flat["gross_bps"] == pytest.approx(0.0, abs=1e-9)
    assert flat["net_bps"] == pytest.approx(-TOTAL_COST)
    # p=0.7, k=1.5, ATR/close=0.03 -> (0.4)*(0.045)*1e4 = 180 bps gross
    good = expected_edge_bps(0.7, close=100.0, atr=3.0, k=1.5)
    assert good["gross_bps"] == pytest.approx(180.0, rel=1e-6)
    assert good["net_bps"] == pytest.approx(180.0 - TOTAL_COST, rel=1e-6)
    assert good["total_cost_bps"] == pytest.approx(TOTAL_COST)


def test_breakeven_prob_zeroes_the_net_edge():
    # denom = 2 * 1.5 * (0.5/100) * 1e4 = 150 bps; p* = 0.5 + 25/150
    p_star = breakeven_prob(COST_BPS, SLIPPAGE_BPS, k=1.5, atr=0.5, close=100.0)
    assert p_star == pytest.approx(0.5 + TOTAL_COST / 150.0)
    at_star = expected_edge_bps(p_star, close=100.0, atr=0.5, k=1.5)
    assert at_star["net_bps"] == pytest.approx(0.0, abs=1e-9)
    assert at_star["p_star"] == pytest.approx(p_star)
    # just above p* the net edge is positive; just below it is negative.
    assert expected_edge_bps(p_star + 0.01, close=100.0, atr=0.5, k=1.5)["net_bps"] > 0.0
    assert expected_edge_bps(p_star - 0.01, close=100.0, atr=0.5, k=1.5)["net_bps"] < 0.0
    # a dearer band raises the breakeven probability.
    assert breakeven_prob(50.0, SLIPPAGE_BPS, 1.5, 0.5, 100.0) > p_star


def test_breakeven_prob_infinite_without_atr():
    assert np.isinf(breakeven_prob(COST_BPS, SLIPPAGE_BPS, 1.5, 0.0, 100.0))
    assert np.isnan(breakeven_prob(COST_BPS, SLIPPAGE_BPS, 1.5, 3.0, 0.0))


def test_expected_edge_bps_nan_on_invalid_geometry():
    bad = expected_edge_bps(float("nan"), close=100.0, atr=3.0, k=1.5)
    assert np.isnan(bad["net_bps"])
    assert np.isnan(expected_edge_bps(0.6, close=0.0, atr=3.0, k=1.5)["net_bps"])


def test_decide_action_abstains_by_default():
    # undefined probability -> NO_TRADE with a named reason
    d = decide_action(float("nan"), close=100.0, atr=3.0, k=1.5)
    assert d["decision"] == "NO_TRADE" and d["abstain_reason"] == "undefined" and d["size"] == 0.0
    # below the calibrated floor (which here is the binding, higher threshold) -> NO_TRADE
    d = decide_action(0.7, close=100.0, atr=3.0, k=1.5, min_prob=0.8)
    assert d["decision"] == "NO_TRADE" and d["abstain_reason"] == "p_below_floor"
    # below breakeven (cost dwarfs a tiny barrier) -> NO_TRADE
    d = decide_action(0.51, close=100.0, atr=0.01, k=1.5)
    assert d["decision"] == "NO_TRADE" and d["abstain_reason"] == "net_edge_nonpositive"
    assert d["size"] == 0.0


def test_decide_action_trades_when_edge_clears_breakeven_and_floor():
    d = decide_action(0.7, close=100.0, atr=3.0, k=1.5, cost_bps=COST_BPS, slippage_bps=SLIPPAGE_BPS)
    assert d["decision"] == "TRADE" and d["abstain_reason"] == "ok"
    assert d["net_bps"] > 0.0
    assert d["p_star"] < 0.7
    assert d["size"] == pytest.approx(0.4)
    assert d["barrier_upper"] == pytest.approx(104.5)
    assert d["barrier_lower"] == pytest.approx(95.5)


def test_cost_and_slippage_band_flip_a_marginal_trade():
    kwargs = dict(close=100.0, atr=0.5, k=1.5, min_prob=0.5)  # 75 bps barrier, gross 15 bps
    cheap = decide_action(0.6, cost_bps=10.0, slippage_bps=0.0, **kwargs)
    dear = decide_action(0.6, cost_bps=200.0, slippage_bps=0.0, **kwargs)
    assert cheap["decision"] == "TRADE"
    assert dear["decision"] == "NO_TRADE" and dear["abstain_reason"] == "net_edge_nonpositive"
    # slippage alone can flip it too, spreading the same breakeven logic.
    low = decide_action(0.6, cost_bps=0.0, slippage_bps=10.0, **kwargs)
    high = decide_action(0.6, cost_bps=0.0, slippage_bps=100.0, **kwargs)
    assert low["decision"] == "TRADE"
    assert high["decision"] == "NO_TRADE" and high["abstain_reason"] == "net_edge_nonpositive"


def test_size_from_meta_is_bounded_and_monotone():
    assert size_from_meta(0.4) == 0.0
    assert size_from_meta(0.5) == 0.0
    assert size_from_meta(1.0) == 1.0
    assert size_from_meta(float("nan")) == 0.0
    assert size_from_meta(0.6) < size_from_meta(0.8)


# --------------------------------------------------------------------------- #
# OOF-calibrated probability floor
# --------------------------------------------------------------------------- #
def test_calibrate_prob_floor_is_recall_guarded_precision_max():
    p, y = _well_calibrated_oof()
    meta = {"targets": {"t": {"oof": p, "oof_label": y, "oof_decile": np.ones(len(p), dtype="int8")}}}
    info = calibrate_prob_floor(meta, min_recall=0.5)
    assert info["source"] == "oof_calibrated"
    assert 0.0 < info["floor"] < 1.0
    # the guard holds, and precision beats the base rate (i.e. it is not the coin flip).
    assert info["recall"] >= 0.5 - 1e-9
    assert info["precision"] > info["pos_rate"]
    assert info["precision"] > 0.5
    assert info["n_events"] == len(p)
    # a stricter recall floor cannot raise the threshold.
    stricter = calibrate_prob_floor(meta, min_recall=0.9)
    assert stricter["floor"] <= info["floor"]
    assert stricter["recall"] >= 0.9 - 1e-9


def test_calibrate_prob_floor_falls_back_without_oof():
    assert calibrate_prob_floor({"targets": {}})["floor"] == META_MIN_PROB
    assert calibrate_prob_floor({"targets": {}})["source"] == "fallback_default"
    assert MIN_RECALL_FOR_FLOOR == 0.5


def test_calibrate_prob_floor_rejects_the_sub_coin_flip_corner():
    # A high-precision cluster of low scores makes the unconstrained precision-max
    # land below 0.5; a probability floor there would be a near-inert (vacuous)
    # filter, so the lower-bound guard must keep the floor at/above the coin flip.
    rng = np.random.default_rng(5)
    oof = np.concatenate([rng.uniform(0.5, 1.0, 1600), rng.uniform(0.2, 0.4, 400)])
    y = np.concatenate([rng.uniform(size=1600) < 0.6, rng.uniform(size=400) < 0.9]).astype("int8")
    meta = {"targets": {"t": {"oof": oof, "oof_label": y, "oof_decile": np.ones(len(oof), dtype="int8")}}}
    bounded = calibrate_prob_floor(meta)
    assert bounded["floor"] >= META_MIN_PROB
    assert bounded["recall"] >= MIN_RECALL_FOR_FLOOR - 1e-9
    unbounded = calibrate_prob_floor(meta, floor_lower_bound=0.0)
    assert unbounded["floor"] < META_MIN_PROB


# --------------------------------------------------------------------------- #
# Band sensitivity
# --------------------------------------------------------------------------- #
def test_band_sensitivity_is_monotone_in_cost_and_slippage():
    rng = np.random.default_rng(3)
    frame = pd.DataFrame({
        "p_meta": rng.uniform(0.3, 0.95, 500).astype("float32"),
        "entry_close": np.float32(100.0),
        "atr": rng.uniform(0.2, 4.0, 500).astype("float32"),
        "k": np.float32(1.5),
        "p_floor": np.float32(0.55),
    })
    cells = band_sensitivity(frame, costs=SENSITIVITY_COSTS, slippages=SENSITIVITY_SLIPPAGE)
    assert len(cells) == len(SENSITIVITY_COSTS) * len(SENSITIVITY_SLIPPAGE)
    for slip in SENSITIVITY_SLIPPAGE:
        shares = [c["trade_share"] for c in cells if c["slippage_bps"] == slip]
        assert shares == sorted(shares, reverse=True)  # more cost -> fewer trades
    for cost in SENSITIVITY_COSTS:
        shares = [c["trade_share"] for c in cells if c["cost_bps"] == cost]
        assert shares == sorted(shares, reverse=True)  # more slippage -> fewer trades
    assert all(c["n_rows"] == 500 for c in cells)


def test_band_sensitivity_empty_frame():
    cells = band_sensitivity(actions._empty_shortlist())
    assert len(cells) == len(SENSITIVITY_COSTS) * len(SENSITIVITY_SLIPPAGE)
    assert all(c["n_trade"] == 0 for c in cells)


# --------------------------------------------------------------------------- #
# Shortlist artifact
# --------------------------------------------------------------------------- #
def test_build_shortlist_top_decile_only_with_exact_schema():
    panel = _panel()
    frame, info = build_shortlist(panel, _meta_result(), "CAD", min_prob=0.5)
    assert list(frame.columns) == list(SHORTLIST_COLUMNS)
    # decisions are evaluated on top-decile events only (~10% of each date).
    expected_per_date = int((primary_pct_rank(panel[PRIMARY_COLUMN].to_numpy(),
                                              panel["date"].to_numpy()) >= 0.9).sum() / panel["date"].nunique())
    assert info["n_rows"] == len(CLEARED_TARGETS) * expected_per_date
    assert (frame["decile_flag"] == 1).all()
    assert (frame["primary_pct"] >= 0.9).all()
    assert frame["scoring_date"].nunique() == 1
    assert frame["scoring_date"].iloc[0] == str(pd.Timestamp(panel["date"].max()).date())
    # WI-014-compatible head: rank, symbol, E5 factors, scoring_date.
    assert list(frame.columns[: len(E5_FACTORS) + 3]) == ["rank", "symbol", *E5_FACTORS, "scoring_date"]
    # rank restarts per target, ordered by meta-probability descending.
    for _target, grp in frame.groupby("target"):
        assert grp["rank"].tolist() == list(range(1, len(grp) + 1))
        assert grp["p_meta"].is_monotonic_decreasing
    assert set(frame["decision"]) <= {"TRADE", "NO_TRADE"}
    assert set(frame["abstain_reason"]) <= set(actions.ABSTAIN_REASONS)
    assert (frame.loc[frame["decision"] == "NO_TRADE", "size"] == 0.0).all()
    assert (frame["time_stop_bars"] > 0).all()
    # rule-v2 columns are present and coherent.
    assert frame["p_floor"].to_numpy() == pytest.approx(0.5, rel=1e-6)
    assert frame["slippage_bps"].to_numpy() == pytest.approx(SLIPPAGE_BPS, rel=1e-6)
    assert np.isfinite(frame["p_star"].to_numpy()).all()
    assert frame["net_bps"].to_numpy() == pytest.approx(
        frame["expected_gross_bps"].to_numpy() - COST_BPS - SLIPPAGE_BPS, rel=1e-4)


def test_build_shortlist_uses_calibrated_floor_when_available():
    panel = _panel()
    meta = _meta_result()
    p, y = _well_calibrated_oof()
    target = CLEARED_TARGETS[0]
    meta["targets"][target]["oof"] = p
    meta["targets"][target]["oof_label"] = y
    meta["targets"][target]["oof_decile"] = np.ones(len(p), dtype="int8")
    frame, info = build_shortlist(panel, meta, "CAD")
    expected = calibrate_prob_floor(meta)["floor"]
    assert info["floor_info"]["source"] == "oof_calibrated"
    assert info["p_floor"] == pytest.approx(expected)
    assert frame["p_floor"].to_numpy() == pytest.approx(expected, rel=1e-6)


def test_build_shortlist_empty_when_no_meta_models():
    panel = _panel()
    frame, info = build_shortlist(panel, {"targets": {}}, "CAD")
    assert frame.empty
    assert info["n_rows"] == 0


def test_shortlist_path_is_new_artifact_and_never_wi014(tmp_path):
    path = shortlist_path("CAD", out_dir=tmp_path)
    assert path.name == "wi016_shortlist_CAD.parquet"
    assert "wi014" not in path.name


def test_write_shortlist_parquet_round_trips_schema(tmp_path):
    panel = _panel()
    frame, _info = build_shortlist(panel, _meta_result(), "CAD", min_prob=0.5)
    path = write_shortlist_parquet(frame, "CAD", out_dir=tmp_path)
    assert path.exists()
    loaded = pd.read_parquet(path)
    assert list(loaded.columns) == list(SHORTLIST_COLUMNS)
    assert len(loaded) == len(frame)
    # writing the shortlist never creates a frozen WI-014 artifact.
    assert not list(tmp_path.glob("wi014_*"))


def test_shortlist_carries_entry_exit_size_and_abstain_fields():
    panel = _panel()
    frame, _info = build_shortlist(panel, _meta_result(), "CAD", min_prob=0.5)
    row = frame.iloc[0]
    assert row["entry_close"] > 0
    k, h = target_grid(row["target"])
    assert row["barrier_upper"] == pytest.approx(row["entry_close"] + k * row["atr"], rel=1e-5)
    assert row["barrier_lower"] == pytest.approx(row["entry_close"] - k * row["atr"], rel=1e-5)
    assert row["time_stop_bars"] == h
    assert row["cost_bps"] == pytest.approx(COST_BPS)
    assert row["slippage_bps"] == pytest.approx(SLIPPAGE_BPS)
    assert row["net_bps"] == pytest.approx(
        row["expected_gross_bps"] - COST_BPS - SLIPPAGE_BPS, rel=1e-4)


# --------------------------------------------------------------------------- #
# Safety surface
# --------------------------------------------------------------------------- #
def test_no_order_execution_surface_exists():
    banned = ("submit", "place_order", "execute", "send_order", "broker", "live_trade")
    names = [n.lower() for n, _ in inspect.getmembers(actions, inspect.isfunction)]
    names += [n.lower() for n, _ in inspect.getmembers(actions, inspect.isclass)]
    assert not [n for n in names if any(b in n for b in banned)]
    src = inspect.getsource(actions)
    assert "to_csv" not in src  # the artifact is a parquet, not an order file
