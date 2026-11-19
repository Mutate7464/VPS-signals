"""WI-086: join index, global filter bar and the watermarked KPI strip.

Evidence is the real artifacts, no synthetic frames: the CAD market (701,599
feature rows, 1,400 oof rows, 315 target symbols) exercises the unmatched paths.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from dash import dcc

import src.visualizer.join as join_module
from src.visualizer import controls, kpi, state_path
from src.visualizer.controls import SLIDER_WHITELIST
from src.visualizer.loader import VisualizerLoader

MARKET = "CAD"
TARGET = "y_20d_stay"
YEARS = 0.75


@pytest.fixture(scope="module")
def cad(tmp_path_factory):
    state_dir = tmp_path_factory.mktemp("viz_state")
    loader = VisualizerLoader(state_dir=state_dir)
    index = join_module.load_or_build(loader, MARKET, state_dir=state_dir)
    return loader, index, state_dir


@pytest.fixture(scope="module")
def panel(cad):
    """Join-aligned columns for one market, built once (features read in one projection)."""
    loader, index, _ = cad
    features = loader.load_columns(MARKET, list(SLIDER_WHITELIST))
    frame = pd.DataFrame(
        {
            "date": index.frame["date"].to_numpy(),
            "y_20d_stay": index.values(loader, "targets", "y_20d_stay").to_numpy(),
            "y_20d_down": index.values(loader, "targets", "y_20d_down").to_numpy(),
            "fwd_atr_ret_20": index.values(loader, "oof", "fwd_atr_ret_20").to_numpy(),
        }
    )
    for feature in SLIDER_WHITELIST:
        frame[feature] = index.align(features[feature].to_numpy(), "features").to_numpy()
    retained = frame.loc[frame["date"] >= pd.Timestamp("2025-06-01")]
    return frame, retained


def test_join_alignment_matches_a_pandas_reference(cad) -> None:
    loader, index, _ = cad
    frame = index.frame
    features = loader.load_columns(MARKET, ["symbol", "date"], source="features")
    assert len(frame) == index.counts["features_rows"] == len(features)
    np.testing.assert_array_equal(frame["features_pos"].to_numpy(), np.arange(len(frame), dtype="int32"))
    left = pd.DataFrame({"symbol": features["symbol"].astype(str), "date": pd.to_datetime(features["date"])})
    for source, column in (("targets", "targets_pos"), ("oof", "oof_pos")):
        keys = loader.load_columns(MARKET, ["symbol", "date"], source=source)
        right = pd.DataFrame({"symbol": keys["symbol"].astype(str), "date": pd.to_datetime(keys["date"])}).reset_index()
        merged = left.merge(right, on=["symbol", "date"], how="left")
        assert len(merged) == len(frame)
        expected, actual = merged["index"].to_numpy(), frame[column].to_numpy()
        matched = expected == expected
        np.testing.assert_array_equal(actual[matched], expected[matched].astype("int32"))
        assert int((actual < 0).sum()) == int((~matched).sum())
        assert int((actual >= 0).sum()) == index.counts[f"{source}_matched"]
    assert index.counts["targets_unmatched"] == 0 and index.counts["targets_rows_outside_panel"] == 0
    assert index.counts["oof_unmatched"] > 0 and index.counts["oof_rows_outside_panel"] > 0
    assert index.counts["oof_matched"] + index.counts["oof_unmatched"] == index.counts["features_rows"]
    assert index.counts["oof_duplicate_keys"] == 0 and index.counts["market_mismatch_rows"] == 0


def test_join_cache_carries_fingerprints_and_rebuilds_when_stale(cad, monkeypatch) -> None:
    loader, index, state_dir = cad
    assert index.cached is False and index.cache_path == state_dir / "join_CAD.parquet"
    entry = json.loads((state_dir / "manifest.json").read_text(encoding="utf-8"))["joins"]["CAD"]
    assert entry["fingerprints"] == index.fingerprints and entry["counts"] == index.counts
    assert {"features", "targets", "oof"} <= set(entry["fingerprints"])
    assert any(key.startswith("oof_variant:") for key in join_module.source_fingerprints(loader, "USD"))
    again = join_module.load_or_build(loader, MARKET, state_dir=state_dir)
    assert again.cached is True and again.counts["rows"] == index.counts["rows"]
    np.testing.assert_array_equal(again.frame["oof_pos"].to_numpy(), index.frame["oof_pos"].to_numpy())
    stale = dict(index.fingerprints)
    stale["features"] = dict(stale["features"], mtime_ns=stale["features"]["mtime_ns"] + 1)
    monkeypatch.setattr(join_module, "source_fingerprints", lambda *args, **kwargs: stale)
    assert join_module.load_or_build(loader, MARKET, state_dir=state_dir).cached is False
    monkeypatch.undo()
    assert join_module.load_or_build(loader, MARKET, state_dir=state_dir).cached is False
    assert join_module.is_fresh(MARKET, index.fingerprints, state_dir)


def test_kpis_match_a_hand_computed_pandas_reference(panel) -> None:
    frame, retained = panel
    payload = kpi.kpi_strip(retained, TARGET, base_frame=frame, market=MARKET, years=YEARS)
    labels = pd.Series(frame[TARGET], dtype="float64")
    kept = pd.Series(retained[TARGET], dtype="float64")
    returns = pd.Series(retained["fwd_atr_ret_20"], dtype="float64")
    expected = {
        "trades_per_year": len(kept) / YEARS,
        "hit_rate": kept.mean(),
        "lift": kept.mean() / labels.mean(),
        "ev": returns.mean(),
        "profit_factor": returns[returns > 0].sum() / abs(returns[returns < 0].sum()),
        "base_rate": labels.mean(),
        "n_rows": len(kept),
    }
    for name, value in expected.items():
        assert abs(payload["kpis"][name]["value"] - float(value)) <= 1e-6, name
    assert payload["ev_horizon"] == 20 and payload["ev_column"] == "fwd_atr_ret_20"
    assert payload["sign"] == 1.0 and payload["kpis"]["lift"]["value"] > 0.0
    assert payload["kpis"]["lift"]["value"] == pytest.approx(
        payload["kpis"]["hit_rate"]["value"] / payload["kpis"]["base_rate"]["value"], abs=1e-6
    )
    assert payload["kpis"]["trades_per_year"]["value"] == pytest.approx(expected["trades_per_year"], abs=1e-6)


def test_low_down_sign_convention_is_a_config_flag(panel) -> None:
    frame, retained = panel
    raw = kpi.kpi_strip(retained, "y_20d_down", base_frame=frame, years=YEARS, sign_mode="raw")
    flipped = kpi.kpi_strip(retained, "y_20d_down", base_frame=frame, years=YEARS, sign_mode="negate_low_down")
    assert raw["sign"] == 1.0 and flipped["sign"] == -1.0
    assert abs(raw["kpis"]["ev"]["value"] + flipped["kpis"]["ev"]["value"]) <= 1e-6
    assert "Open question" in flipped["notes"][0]
    assert kpi.sign_for("y_20d_up", "negate_low_down") == 1.0 == kpi.sign_for("y_y_20d_up", "negate_low_down")
    assert kpi.horizon_for("y_y_15d_high") == 15 and kpi.ev_column_for("y_15d_low") == "fwd_atr_ret_15"
    with pytest.raises(ValueError):
        kpi.sign_for("y_20d_down", "flip")
    with pytest.raises(ValueError):
        kpi.horizon_for("p_20d_up")


def test_watermark_renders_on_every_kpi(panel) -> None:
    frame, retained = panel
    payload = kpi.kpi_strip(retained, TARGET, base_frame=frame, years=YEARS)
    rows = kpi.render_strip(payload)
    assert [row["label"] for row in rows[:5]] == [name.replace("_", " ") for name in kpi.KPI_ORDER]
    assert len(rows) == len(kpi.KPI_ORDER) + 2
    assert payload["watermark"] == kpi.WATERMARK and "no verdicts" in kpi.WATERMARK
    for row in rows:
        assert row["watermark"] == kpi.WATERMARK and row["units"]
    for entry in payload["kpis"].values():
        assert entry["watermark"] == kpi.WATERMARK and isinstance(entry["value"], (int, float))


def test_filter_spec_roundtrips_through_the_url_query_string(panel) -> None:
    frame, _ = panel
    spec = controls.default_spec(MARKET.lower(), TARGET, ("2016-01-04", "2026-09-22"), controls.slider_bounds(frame))
    search = controls.encode_spec(spec)
    assert search.startswith("spec=") and "%22" in search
    assert controls.decode_spec("?" + search) == spec
    store = controls.build_filter_store(spec)
    assert isinstance(store, dcc.Store) and store.id == controls.STORE_ID and store.data == spec
    assert spec["market"] == MARKET and spec["target"] in controls.TARGET_OPTIONS
    assert set(spec["sliders"]) == set(SLIDER_WHITELIST)
    assert "dcc.Interval" not in Path(controls.__file__).read_text(encoding="utf-8")


def test_spec_rejects_non_whitelisted_features_and_unknown_targets() -> None:
    spec = controls.default_spec(MARKET, TARGET)
    spec["sliders"] = {"close": [0.0, 1.0]}
    with pytest.raises(ValueError, match="whitelist"):
        controls.validate_spec(spec)
    with pytest.raises(ValueError):
        controls.default_spec("JPY")
    with pytest.raises(ValueError):
        controls.encode_spec(controls.default_spec(MARKET, "not_a_target"))
    with pytest.raises(ValueError):
        controls.decode_spec("other=1")
    assert "close" not in SLIDER_WHITELIST and "rsi_14" not in SLIDER_WHITELIST
    assert {"y_20d_stay", "y_15d_low", "y_y_15d_high", "p_y_20d_down"} <= set(controls.TARGET_OPTIONS)


def test_apply_spec_masks_match_a_pandas_reference(panel) -> None:
    frame, _ = panel
    bounds = controls.slider_bounds(frame)
    spec = controls.default_spec(MARKET, TARGET, ("2025-01-01", "2026-09-30"), bounds)
    mask, filtered = controls.apply_spec(frame, spec)
    reference = pd.Series(True, index=frame.index)
    for feature, (low, high) in bounds.items():
        reference &= (frame[feature] >= low) & (frame[feature] <= high)
    dates = pd.to_datetime(frame["date"])
    reference &= (dates >= pd.Timestamp("2025-01-01")) & (dates <= pd.Timestamp("2026-09-30"))
    np.testing.assert_array_equal(mask, reference.to_numpy())
    assert len(filtered) == int(mask.sum()) and 0 < len(filtered) < len(frame)


def test_filter_roundtrip_p95_within_one_second_and_recorded(panel, tmp_path) -> None:
    frame, _ = panel
    spec = controls.default_spec(MARKET, TARGET, ("2016-01-04", "2026-09-22"), controls.slider_bounds(frame))
    report = controls.measure_filter_roundtrip(frame, spec, repeats=7)
    assert report["within_budget"] is True and report["latency_ms_p95"] <= controls.FILTER_BUDGET_MS
    assert report["retained_rows"] == int(controls.apply_spec(frame, spec)[0].sum())
    written = controls.record_filter_bench(report, tmp_path)
    assert written == state_path("bench.json", tmp_path)
    payload = json.loads(written.read_text(encoding="utf-8"))[controls.BENCH_KEY]
    assert payload["latency_ms_p95"] == report["latency_ms_p95"] and payload["recorded_utc"]


def test_join_cache_is_written_only_under_the_state_dir(cad) -> None:
    _, index, state_dir = cad
    assert index.cache_path.resolve().is_relative_to(Path(state_dir).resolve())
    assert join_module.cache_path(MARKET) == state_path("join_CAD.parquet")
    assert join_module.MANIFEST_KEY == "joins" and join_module.is_fresh(MARKET, index.fingerprints, state_dir)
