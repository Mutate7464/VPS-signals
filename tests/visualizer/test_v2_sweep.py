"""WI-089: View 2 threshold sweep - quantile sweep vs a pandas reference, illustrative line.

Evidence is the real artifacts: CAD OOF is the cheap market (1,400 rows), so `y_20d_up`
leaves a few hundred analysed rows. trades/yr, lift, EV and profit factor follow
``src.visualizer.kpi``; the reference implementation below is plain pandas.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.visualizer import controls, kpi, oof_path
from src.visualizer.loader import VisualizerLoader
from src.visualizer.views import v2_sweep as v2

REPO = Path(__file__).resolve().parents[2]
MARKET = "CAD"
TARGET = "y_20d_up"
OOF_FILE = oof_path(MARKET)


@pytest.fixture(scope="module")
def view_inputs(tmp_path_factory):
    state_dir = tmp_path_factory.mktemp("viz_state_v2")
    loader = VisualizerLoader(state_dir=state_dir)
    columns = v2.columns_for(TARGET)
    frame, counts = v2.load_prob_frame(loader, MARKET, columns)
    return loader, frame, counts, columns


@pytest.fixture(scope="module")
def payload(view_inputs):
    _, frame, _, columns = view_inputs
    return v2.measure_budget(frame, columns, market=MARKET)


def reference_sweep(frame, columns, levels, years, sign, base_rate) -> pd.DataFrame:
    """A plain pandas implementation of the same sweep (the WI-089 reference)."""
    prob = frame[columns["prob_column"]].astype("float64")
    label = frame[columns["label_column"]].astype("float64")
    signed = frame[columns["ev_column"]].astype("float64") * sign
    records = []
    for level in levels:
        threshold = float(prob.quantile(float(level)))
        retained = (prob >= threshold).to_numpy()
        n = int(retained.sum())
        forward = signed[retained]
        positive, negative = float(forward[forward > 0].sum()), float(forward[forward < 0].sum())
        hit = float(label[retained].mean()) if n else float("nan")
        records.append({
            "quantile": float(level), "threshold": threshold, "retained_rows": n,
            "trades_per_year": float(n / years), "hit_rate": hit,
            "lift": float(hit / base_rate) if base_rate else float("nan"),
            "ev": float(forward.mean()) if n else float("nan"),
            "profit_factor": float(positive / abs(negative)) if negative < 0 else float("nan")})
    return pd.DataFrame(records)


def test_columns_for_maps_selectors_and_rejects_targets_without_probabilities() -> None:
    assert v2.columns_for("p_y_20d_up") == {
        "target": "y_20d_up", "prob_column": "p_y_20d_up",
        "label_column": "y_y_20d_up", "ev_column": "fwd_atr_ret_20"}
    assert v2.columns_for("y_y_15d_high")["ev_column"] == "fwd_atr_ret_15"
    assert v2.columns_for("y_20d_down")["prob_column"] == "p_y_20d_down"
    with pytest.raises(KeyError):
        v2.columns_for("y_20d_stay")  # in the targets file, but it has no OOF probability
    with pytest.raises(KeyError):
        v2.columns_for("not_a_target")


def test_load_prob_frame_reads_projected_oof_columns_and_drops_nan_rows(view_inputs) -> None:
    loader, frame, counts, columns = view_inputs
    requested = {columns["prob_column"], columns["label_column"], columns["ev_column"]}
    assert set(frame.columns) == requested | {v2.DATE_COLUMN}
    assert columns["prob_column"].startswith("p_") and columns["label_column"].startswith("y_y_")
    assert columns["ev_column"] in {"fwd_atr_ret_15", "fwd_atr_ret_20"}
    assert counts["rows_read"] == loader.parquet_rows(OOF_FILE) == 1_400
    assert counts["rows_in_range"] == counts["rows_read"]
    assert counts["analysed_rows"] == len(frame) > 100
    assert counts["dropped_nan_rows"] == counts["rows_read"] - counts["analysed_rows"]
    assert counts["market"] == MARKET and counts["sliders_applied"] is False
    assert frame[sorted(requested)].notna().all().all()
    assert counts["date_min"] < counts["date_max"]


def test_load_reads_exactly_one_projected_oof_call(monkeypatch, tmp_path) -> None:
    captured = []
    original = VisualizerLoader.read_projected

    def spy(path, columns):
        captured.append((Path(path).name, list(columns)))
        return original(path, columns)

    monkeypatch.setattr(VisualizerLoader, "read_projected", staticmethod(spy))
    loader = VisualizerLoader(state_dir=tmp_path)
    frame, counts = v2.load_prob_frame(loader, MARKET, v2.columns_for(TARGET))
    assert captured == [("oof_CAD.parquet",
                         ["date", "symbol", "close", "p_y_20d_up", "y_y_20d_up", "fwd_atr_ret_20"])]
    assert counts["analysed_rows"] == len(frame)


def test_quantile_levels_span_zero_to_one_and_reject_bad_step_counts() -> None:
    levels = v2.quantile_levels(11)
    assert levels[0] == 0.0 and levels[-1] == 1.0 and np.all(np.diff(levels) > 0)
    assert v2.quantile_levels(v2.STEP_LIMIT).size == v2.STEP_LIMIT
    for bad in (1, 0, v2.STEP_LIMIT + 1):
        with pytest.raises(ValueError, match="step count"):
            v2.quantile_levels(bad)
    assert 2 <= v2.DEFAULT_STEPS <= v2.STEP_LIMIT


def test_sweep_matches_a_reference_pandas_implementation(payload, view_inputs) -> None:
    _, frame, _, columns = view_inputs
    sweep = pd.DataFrame(payload["sweep"])
    reference = reference_sweep(frame, columns, v2.quantile_levels(payload["steps"]),
                                payload["years"], payload["sign"], payload["base_rate"])
    assert len(sweep) == payload["steps"] == v2.DEFAULT_STEPS
    np.testing.assert_array_equal(sweep["retained_rows"], reference["retained_rows"])
    np.testing.assert_allclose(sweep["threshold"], reference["threshold"], rtol=0, atol=1e-12)
    for column in ("trades_per_year", "hit_rate", "lift"):
        np.testing.assert_allclose(sweep[column], reference[column], rtol=1e-12, equal_nan=True)
    for column in ("ev", "profit_factor"):
        np.testing.assert_allclose(sweep[column], reference[column], rtol=1e-9, equal_nan=True)
    # The sweep is monotone, and the first step is the whole panel (lift 1.0 by construction).
    assert sweep["retained_rows"].is_monotonic_decreasing and (sweep["retained_rows"] > 0).all()
    assert sweep["quantile"].iloc[0] == 0.0 and sweep["quantile"].iloc[-1] == 1.0
    assert sweep["retained_rows"].iloc[0] == payload["analysed_rows"]
    assert sweep["hit_rate"].iloc[0] == pytest.approx(payload["base_rate"], rel=1e-12)
    assert sweep["lift"].iloc[0] == pytest.approx(1.0, rel=1e-12)


def test_sweep_is_exact_on_a_hand_checkable_frame() -> None:
    frame = pd.DataFrame({
        "date": pd.to_datetime(["2025-01-01", "2025-02-01", "2025-03-01", "2025-04-01"]),
        "p": np.array([0.1, 0.2, 0.3, 0.4], dtype="float32"),
        "y": np.array([0, 1, 1, 0], dtype="int8"),
        "ev": np.array([1.0, -2.0, 4.0, 2.0], dtype="float32")})
    columns = {"target": "y_20d_up", "prob_column": "p", "label_column": "y", "ev_column": "ev"}
    payload = v2.compute_view(frame, columns, market=MARKET, n_steps=3, years=2.0)
    sweep = pd.DataFrame(payload["sweep"])
    np.testing.assert_array_equal(sweep["retained_rows"], [4, 2, 1])
    np.testing.assert_allclose(sweep["threshold"], [0.1, 0.25, 0.4], rtol=1e-6)
    np.testing.assert_allclose(sweep["hit_rate"], [0.5, 0.5, 0.0], atol=1e-12)
    np.testing.assert_allclose(sweep["trades_per_year"], [2.0, 1.0, 0.5], rtol=1e-12)
    np.testing.assert_allclose(sweep["ev"], [1.25, 3.0, 2.0], rtol=1e-6)
    assert sweep["profit_factor"].iloc[0] == pytest.approx(3.5, rel=1e-6)
    assert np.isnan(sweep["profit_factor"].iloc[1:].to_numpy()).all()  # no losing trade retained
    assert payload["analysed_rows"] == 4 and payload["base_rate"] == pytest.approx(0.5)


def test_years_in_range_matches_the_kpi_definition(view_inputs) -> None:
    _, frame, _, _ = view_inputs
    assert v2.years_in_range(frame["date"]) == pytest.approx(kpi.years_in_range(frame["date"]), rel=1e-12)


def test_down_target_sign_mode_flips_the_ev_and_is_reported(view_inputs) -> None:
    loader, _, _, _ = view_inputs
    columns = v2.columns_for("y_20d_down")
    frame, _ = v2.load_prob_frame(loader, MARKET, columns)
    raw = v2.compute_view(frame, columns, market=MARKET, n_steps=5)
    flipped = v2.compute_view(frame, columns, market=MARKET, n_steps=5, sign_mode="negate_low_down")
    assert raw["sign"] == 1.0 and flipped["sign"] == -1.0
    assert "unresolved" in flipped["notes"][-1]
    assert flipped["sweep"][0]["ev"] == pytest.approx(-raw["sweep"][0]["ev"], rel=1e-9)
    assert flipped["sweep"][0]["hit_rate"] == raw["sweep"][0]["hit_rate"]


def test_reference_line_is_the_labelled_illustrative_200_per_year_line(payload) -> None:
    reference = payload["reference"]
    assert v2.REFERENCE_TRADES_PER_YEAR == 200.0 and v2.REFERENCE_LABEL == "ILLUSTRATIVE"
    assert reference["trades_per_year"] == 200.0 and reference["label"] == "ILLUSTRATIVE"
    assert reference["label"] in reference["note"] and "gates nothing" in reference["note"]
    assert "display line only" in reference["role"] and reference["watermark"] == kpi.WATERMARK
    nearest = reference["nearest_step"]
    assert nearest in payload["sweep"]
    assert abs(nearest["trades_per_year"] - 200.0) == min(
        abs(step["trades_per_year"] - 200.0) for step in payload["sweep"])


def test_payload_is_watermarked_strict_json_and_carries_no_verdict(payload) -> None:
    text = v2.serialize_payload(payload)
    parsed = json.loads(text)
    assert len(text.encode("utf-8")) == parsed["payload_bytes"] == payload["payload_bytes"]
    assert "NaN" not in text and "Infinity" not in text
    assert parsed["watermark"] == kpi.WATERMARK and "no verdicts" in parsed["watermark"]
    lowered = text.lower()
    for banned in ("verdict", "adopt", "reject", "recommend"):
        assert f'"{banned}"' not in lowered  # no field is named like a verdict
    assert "no verdict" in lowered and parsed["notes"][0].endswith("no adopt/reject field.")
    assert parsed["reference"]["label"] == "ILLUSTRATIVE"
    assert parsed["sweep"][0]["retained_rows"] == parsed["analysed_rows"]


def test_compute_and_serialize_stay_inside_the_server_budgets(payload) -> None:
    assert payload["within_limits"] is True
    assert payload["budget_ms"]["compute_within"] is True
    assert payload["budget_ms"]["compute"] <= v2.COMPUTE_BUDGET_MS
    assert payload["budget_ms"]["serialize_within"] is True
    assert payload["budget_ms"]["serialize"] <= v2.SERIALIZE_BUDGET_MS
    assert 0 < payload["payload_bytes"] <= v2.PAYLOAD_LIMIT_BYTES


def test_view_opens_the_oof_artifact_read_only_and_writes_nothing(view_inputs) -> None:
    _, frame, _, columns = view_inputs
    source = Path(v2.__file__).read_text(encoding="utf-8")
    assert "to_parquet" not in source and "write_text" not in source and "dcc.Interval" not in source
    before = (OOF_FILE.stat().st_size, OOF_FILE.stat().st_mtime_ns)
    payload = v2.compute_view(frame, columns, market=MARKET, n_steps=8)
    assert payload["view"] == v2.VIEW_NAME and payload["market"] == MARKET
    assert (OOF_FILE.stat().st_size, OOF_FILE.stat().st_mtime_ns) == before


def test_build_view_honours_the_spec_market_date_range_and_selector(view_inputs) -> None:
    loader, _, counts, _ = view_inputs
    spec = controls.default_spec(MARKET, "p_y_20d_up", ("2025-09-01", "2026-09-23"))
    payload = v2.build_view(loader, spec, n_steps=8)
    assert payload["market"] == MARKET and payload["prob_column"] == "p_y_20d_up"
    assert payload["counts"]["rows_in_range"] < counts["rows_read"]
    assert payload["counts"]["date_min"] >= "2025-09-01"
    assert payload["counts"]["sliders_applied"] is False
    assert payload["analysed_rows"] == payload["sweep"][0]["retained_rows"]
    overridden = v2.build_view(loader, spec, target="y_y_20d_down", n_steps=4)
    assert overridden["prob_column"] == "p_y_20d_down"
    with pytest.raises(KeyError):
        v2.build_view(loader, spec, target="y_20d_stay")


def test_figures_draw_the_illustrative_reference_line(payload) -> None:
    figure = v2.figures(payload)["sweep"]
    assert figure.data[0].name == "hit rate" and payload["ev_column"] in figure.data[1].name
    assert len(figure.layout.shapes) == 1 and figure.layout.shapes[0].x0 == 200.0
    labels = [annotation.text for annotation in figure.layout.annotations]
    assert any("200 trades/yr" in label and "ILLUSTRATIVE" in label for label in labels)
    assert payload["prob_column"] in figure.layout.title.text
