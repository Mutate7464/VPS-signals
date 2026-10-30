"""WI-016 step 6 action-synthesis tests.

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
    SHORTLIST_COLUMNS,
    build_shortlist,
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


# --------------------------------------------------------------------------- #
# Cost-aware decision rule
# --------------------------------------------------------------------------- #
def test_expected_edge_bps_is_symmetric_at_a_coin_flip():
    flat = expected_edge_bps(0.5, close=100.0, atr=3.0, k=1.5)
    assert flat["gross_bps"] == pytest.approx(0.0, abs=1e-9)
    assert flat["net_bps"] == pytest.approx(-COST_BPS)
    # p=0.7, k=1.5, ATR/close=0.03 -> (0.4)*(0.045)*1e4 = 180 bps gross
    good = expected_edge_bps(0.7, close=100.0, atr=3.0, k=1.5)
    assert good["gross_bps"] == pytest.approx(180.0, rel=1e-6)
    assert good["net_bps"] == pytest.approx(160.0, rel=1e-6)


def test_expected_edge_bps_nan_on_invalid_geometry():
    bad = expected_edge_bps(float("nan"), close=100.0, atr=3.0, k=1.5)
    assert np.isnan(bad["net_bps"])
    assert np.isnan(expected_edge_bps(0.6, close=0.0, atr=3.0, k=1.5)["net_bps"])


def test_decide_action_abstains_by_default():
    # undefined probability -> NO_TRADE with a named reason
    d = decide_action(float("nan"), close=100.0, atr=3.0, k=1.5)
    assert d["decision"] == "NO_TRADE" and d["abstain_reason"] == "undefined" and d["size"] == 0.0
    # below the coin-flip floor -> NO_TRADE
    d = decide_action(0.4, close=100.0, atr=3.0, k=1.5)
    assert d["decision"] == "NO_TRADE" and d["abstain_reason"] == "p_below_min"
    # confident but the edge does not clear the cost band -> NO_TRADE
    d = decide_action(0.51, close=100.0, atr=0.01, k=1.5)
    assert d["decision"] == "NO_TRADE" and d["abstain_reason"] == "net_edge_nonpositive"
    assert d["size"] == 0.0


def test_decide_action_trades_when_edge_clears_cost():
    d = decide_action(0.7, close=100.0, atr=3.0, k=1.5, cost_bps=COST_BPS)
    assert d["decision"] == "TRADE" and d["abstain_reason"] == "ok"
    assert d["net_bps"] > 0.0
    assert d["size"] == pytest.approx(0.4)
    assert d["barrier_upper"] == pytest.approx(104.5)
    assert d["barrier_lower"] == pytest.approx(95.5)


def test_cost_band_can_flip_a_marginal_trade_to_no_trade():
    kwargs = dict(close=100.0, atr=0.5, k=1.5)   # 75 bps barrier distance, gross 15 bps
    cheap = decide_action(0.6, cost_bps=10.0, **kwargs)
    dear = decide_action(0.6, cost_bps=200.0, **kwargs)
    assert cheap["decision"] == "TRADE"
    assert dear["decision"] == "NO_TRADE" and dear["abstain_reason"] == "net_edge_nonpositive"


def test_size_from_meta_is_bounded_and_monotone():
    assert size_from_meta(0.4) == 0.0
    assert size_from_meta(0.5) == 0.0
    assert size_from_meta(1.0) == 1.0
    assert size_from_meta(float("nan")) == 0.0
    assert size_from_meta(0.6) < size_from_meta(0.8)


# --------------------------------------------------------------------------- #
# Shortlist artifact
# --------------------------------------------------------------------------- #
def test_build_shortlist_top_decile_only_with_exact_schema():
    panel = _panel()
    frame, info = build_shortlist(panel, _meta_result(), "CAD")
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
    frame, _info = build_shortlist(panel, _meta_result(), "CAD")
    path = write_shortlist_parquet(frame, "CAD", out_dir=tmp_path)
    assert path.exists()
    loaded = pd.read_parquet(path)
    assert list(loaded.columns) == list(SHORTLIST_COLUMNS)
    assert len(loaded) == len(frame)
    # writing the shortlist never creates a frozen WI-014 artifact.
    assert not list(tmp_path.glob("wi014_*"))


def test_shortlist_carries_entry_exit_size_and_abstain_fields():
    panel = _panel()
    frame, _info = build_shortlist(panel, _meta_result(), "CAD")
    row = frame.iloc[0]
    assert row["entry_close"] > 0
    k, h = target_grid(row["target"])
    assert row["barrier_upper"] == pytest.approx(row["entry_close"] + k * row["atr"], rel=1e-5)
    assert row["barrier_lower"] == pytest.approx(row["entry_close"] - k * row["atr"], rel=1e-5)
    assert row["time_stop_bars"] == h
    assert row["cost_bps"] == pytest.approx(COST_BPS)
    assert row["net_bps"] == pytest.approx(row["expected_gross_bps"] - COST_BPS, rel=1e-4)


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
