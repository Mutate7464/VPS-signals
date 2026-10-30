"""WI-016 step 6 meta-labeler tests.

Verify: `uv run pytest tests/test_wi016_meta_labeler.py`
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.wi016.meta_labeler import (
    CLEARED_TARGETS,
    PRIMARY_COLUMN,
    build_meta_panel,
    decile_flags,
    embargo_for,
    emit,
    event_frame,
    fold_plan,
    market_cleared,
    meta_cv,
    meta_labeler,
    primary_pct_rank,
    run_market,
    target_grid,
    target_horizon,
)

FEATURES = ["f_signal", "f_noise"]
SMALL_PARAMS = {
    "n_estimators": 25, "max_depth": 2, "learning_rate": 0.1, "n_jobs": 2,
    "tree_method": "hist", "subsample": 0.9, "colsample_bytree": 0.9,
    "min_child_weight": 5, "reg_alpha": 0.0, "reg_lambda": 1.0, "random_state": 42,
}


def _panel(n_dates: int = 200, per_date: int = 40, seed: int = 0, signal: bool = True) -> pd.DataFrame:
    """A synthetic meta-labeler panel: primary, features, barrier labels, geometry."""
    rng = np.random.default_rng(seed)
    dates = np.repeat(pd.date_range("2020-01-01", periods=n_dates, freq="B"), per_date)
    n = n_dates * per_date
    primary = rng.normal(0, 1, n)
    f_signal = rng.normal(0, 1, n)
    f_noise = rng.normal(0, 1, n)

    # The primary drives the profit-touch probability on the long side.
    p = 1.0 / (1.0 + np.exp(-(1.5 * primary + (1.0 * f_signal if signal else 0.0))))
    profit = rng.random(n) < p
    touch = np.where(profit, 1.0, -1.0)
    vertical = rng.random(n) < 0.25  # vertical exits are NOT meta-label events
    touch = np.where(vertical, 0.0, touch)
    undefined = rng.random(n) < 0.05
    touch = np.where(undefined, -9.0, touch)
    label = np.where(vertical, np.sign(rng.normal(size=n)), touch)
    label = np.where(undefined, np.nan, label)

    frame = pd.DataFrame({
        "date": dates,
        "symbol": np.tile([f"S{i:03d}" for i in range(per_date)], n_dates),
        "close": np.float32(100.0),
        "atr": np.float32(3.0),
        PRIMARY_COLUMN: primary.astype("float32"),
        "f_signal": f_signal.astype("float32"),
        "f_noise": f_noise.astype("float32"),
    })
    for target in CLEARED_TARGETS:
        k, h = target_grid(target)
        tag = f"k{int(round(k * 10))}"
        frame[f"tb_label_{tag}_h{h}"] = label.astype("float32")
        frame[f"tb_touch_{tag}_h{h}"] = touch.astype("int8")
    return frame


# --------------------------------------------------------------------------- #
# Event / decile semantics
# --------------------------------------------------------------------------- #
def test_target_grid_and_embargo_for_cleared_targets():
    assert target_grid("tb_label_k15_h144") == (1.5, 144)
    assert target_grid("tb_label_k20_h8") == (2.0, 8)
    assert target_horizon("tb_label_k15_h55") == 55
    # per-horizon embargo = max(20, h)
    assert embargo_for("tb_label_k15_h8") == 20
    assert embargo_for("tb_label_k20_h8") == 20
    assert embargo_for("tb_label_k15_h55") == 55
    assert embargo_for("tb_label_k15_h144") == 144
    with pytest.raises(KeyError):
        target_grid("y_15d_high")


def test_primary_pct_rank_is_within_date():
    dates = np.repeat(pd.date_range("2020-01-01", periods=2), 5)
    values = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 5.0, 4.0, 3.0, 2.0, 1.0])
    pct = primary_pct_rank(values, dates)
    assert np.allclose(pct[:5], np.array([0.2, 0.4, 0.6, 0.8, 1.0]))
    assert np.allclose(pct[5:], np.array([1.0, 0.8, 0.6, 0.4, 0.2]))
    assert np.isnan(primary_pct_rank([np.nan, 1.0], dates[:2])[0])


def test_decile_flags_top_second_outside():
    pct = np.array([0.05, 0.5, 0.85, 0.9, 1.0, np.nan])
    assert decile_flags(pct).tolist() == [-1, -1, 0, 1, 1, -1]


def test_event_frame_keeps_top_two_deciles_resolved_only():
    panel = _panel(n_dates=60, per_date=40)
    events = event_frame(panel, "tb_label_k15_h8", feature_cols=FEATURES)
    # only the two deciles of each date can appear, and both strata are populated.
    assert set(events["decile_flag"].unique()) <= {0, 1}
    assert (events["decile_flag"] == 1).sum() > 0
    assert (events["decile_flag"] == 0).sum() > 0
    # barrier-resolved rows only: vertical / undefined rows are excluded.
    assert len(events) < len(panel)
    assert events["meta_label"].isin([0, 1]).all()
    assert events["meta_label"].dtype == np.int8
    assert events["decile_flag"].dtype == np.int8
    # the primary is always a model feature (point-in-time, known at the event).
    for f in FEATURES + ["close", "atr", PRIMARY_COLUMN]:
        assert events[f].dtype == np.float32, f
    # top-decile rows are a strict subset of the training events.
    top = events[events["decile_flag"] == 1]
    assert len(top) > 0 and len(top) < len(events)


def test_event_frame_meta_label_matches_profit_touch():
    panel = _panel(n_dates=60, per_date=40)
    events = event_frame(panel, "tb_label_k15_h55", feature_cols=FEATURES)
    touch = panel["tb_touch_k15_h55"].to_numpy()
    label = panel["tb_label_k15_h55"].to_numpy()
    pct = primary_pct_rank(panel[PRIMARY_COLUMN].to_numpy(), panel["date"].to_numpy())
    resolved = np.isfinite(label) & ((touch == 1.0) | (touch == -1.0))
    top2 = resolved & (pct >= 0.8)
    # events = every barrier-resolved row inside the top-two deciles; positives = profit touches.
    assert len(events) == int(top2.sum())
    assert events["meta_label"].sum() == int((top2 & (touch == 1.0)).sum())


def test_event_frame_long_side_uses_primary_rank():
    panel = _panel(n_dates=60, per_date=40)
    events = event_frame(panel, "tb_label_k20_h8", feature_cols=FEATURES)
    assert (events["primary_pct"] >= 0.8).all()
    assert (events["primary_pct"] <= 1.0).all()


# --------------------------------------------------------------------------- #
# Leakage-safe folds
# --------------------------------------------------------------------------- #
def test_fold_plan_embargoes_every_fold_by_horizon():
    dates = np.repeat(pd.date_range("2015-01-01", periods=1200, freq="B"), 4)
    for target, expected in (("tb_label_k15_h8", 20), ("tb_label_k15_h55", 55),
                             ("tb_label_k15_h144", 144)):
        plan = fold_plan(dates, target)
        assert plan, target
        for f in plan:
            assert f["embargo_td"] == expected
            assert f["train_val_gap_td"] >= expected
            assert f["fit_calib_gap_td"] >= expected
            assert f["max_train_date"] < f["min_val_date"]
            assert f["max_fit_date"] < f["min_calib_date"]


def test_fold_plan_144_embargo_purges_more_than_20():
    dates = np.repeat(pd.date_range("2015-01-01", periods=1200, freq="B"), 4)
    short = fold_plan(dates, "tb_label_k15_h8")
    long = fold_plan(dates, "tb_label_k15_h144")
    assert all(f["embargo_td"] == 20 for f in short)
    assert all(f["embargo_td"] == 144 for f in long)
    assert long[0]["n_train"] < short[0]["n_train"]
    assert long[0]["n_val"] == short[0]["n_val"]


# --------------------------------------------------------------------------- #
# Meta-model CV
# --------------------------------------------------------------------------- #
def test_meta_cv_returns_oof_placebo_and_strata():
    panel = _panel(n_dates=200, per_date=25)
    events = event_frame(panel, "tb_label_k15_h8", feature_cols=FEATURES)
    res = meta_cv(events, "tb_label_k15_h8", feature_cols=FEATURES,
                  n_splits=2, placebo_seeds=2, params=SMALL_PARAMS)
    assert len(res["oof"]) == len(events)
    finite = res["oof"][np.isfinite(res["oof"])]
    assert finite.size > 0 and ((finite >= 0) & (finite <= 1)).all()
    assert len(res["placebo"]) == 2
    assert set(res["stratified"]) == {"top_decile", "second_decile"}
    assert res["embargo_td"] == 20
    assert res["final_model"] is not None
    assert res["final_calibration"] in {"isotonic", "sigmoid"}
    assert res["fold_plan"][0]["embargo_td"] == 20


def test_meta_cv_uses_horizon_embargo_for_long_target():
    panel = _panel(n_dates=900, per_date=12)
    events = event_frame(panel, "tb_label_k15_h144", feature_cols=FEATURES)
    res = meta_cv(events, "tb_label_k15_h144", feature_cols=FEATURES,
                  n_splits=2, placebo_seeds=1, params=SMALL_PARAMS)
    assert res["embargo_td"] == 144
    assert res["fold_plan"] and all(f["embargo_td"] == 144 for f in res["fold_plan"])


def test_meta_labeler_covers_exactly_the_cleared_targets():
    panel = _panel(n_dates=120, per_date=25)
    result = meta_labeler(panel, "CAD", feature_cols=FEATURES, n_splits=2, placebo_seeds=1)
    assert set(result["targets"]) == set(CLEARED_TARGETS)
    for res in result["targets"].values():
        assert res["embargo_td"] == max(20, res["horizon"])


# --------------------------------------------------------------------------- #
# Gate enforcement
# --------------------------------------------------------------------------- #
def test_market_cleared_reads_the_addendum_verdict(tmp_path):
    assert market_cleared("CAD", tmp_path) is False  # missing report is not a clear
    (tmp_path / "wi016_addendum_probe_CAD.md").write_text(
        "## DECISION @ 20 bps — barrier-resolved labels: **CLEAR**\n")
    assert market_cleared("CAD", tmp_path) is True
    (tmp_path / "wi016_addendum_probe_USD.md").write_text(
        "## DECISION @ 20 bps — barrier-resolved labels: **NOT_CLEAR**\n")
    assert market_cleared("USD", tmp_path) is False


def test_run_market_refuses_uncleared_market_and_writes_nothing(tmp_path):
    # No addendum report in tmp_path (and USD did NOT clear the real one): no
    # panel is built, no metadata, no shortlist, no report.
    res = run_market("USD", out_dir=tmp_path)
    assert res["cleared"] is False
    assert list(tmp_path.iterdir()) == []


def test_emit_writes_shortlist_and_report(tmp_path):
    panel = _panel(n_dates=60, per_date=25)
    res = emit(panel, "CAD", n_splits=2, placebo_seeds=1, out_dir=tmp_path)
    out = tmp_path / "wi016_shortlist_CAD.parquet"
    assert out.exists()
    frame = pd.read_parquet(out)
    assert list(frame.columns) == res["shortlist_meta"]["columns"]
    assert (tmp_path / "wi016_meta_labeler_CAD.md").exists()
    assert not list(tmp_path.glob("wi014_*"))


def test_build_meta_panel_streams_and_casts_float32():
    panel = build_meta_panel("CAD", max_symbols=3)
    assert {"date", "symbol", "market", "close", "atr", PRIMARY_COLUMN} <= set(panel.columns)
    for col in panel.columns:
        if col not in ("date", "symbol", "market"):
            assert panel[col].dtype == np.float32, col
    for target in CLEARED_TARGETS:
        k, h = target_grid(target)
        tag = f"k{int(round(k * 10))}"
        assert f"tb_label_{tag}_h{h}" in panel.columns
        assert f"tb_touch_{tag}_h{h}" in panel.columns
