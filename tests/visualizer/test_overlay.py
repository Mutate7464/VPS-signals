"""WI-088: View 3 OHLC drill-down + recomputed barrier overlays (display math only).

Evidence is the real artifacts: CAD, family `high_low`, horizon 5, feature
`atr_pct_20`. The CAD OOF file carries 1,340 rows over 5 symbols, so the per-symbol
OHLCV LRU bounds the IO of the 100-event MISMATCH sample.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import src.visualizer.join as join_module
from src.visualizer import controls, kpi
from src.visualizer.loader import VisualizerLoader
from src.visualizer.overlay import barriers
from src.visualizer.views import v3_ohlc as v3

REPO = Path(__file__).resolve().parents[2]
MARKET = "CAD"
FAMILY = "high_low"
H = 5
FEATURE = "atr_pct_20"
LABEL_COLUMN = "y_y_15d_high"


@pytest.fixture(scope="module")
def viz(tmp_path_factory):
    state_dir = tmp_path_factory.mktemp("viz_state_v3")
    loader = VisualizerLoader(state_dir=state_dir)
    index = join_module.load_or_build(loader, MARKET, state_dir=state_dir)
    return loader, index


@pytest.fixture(scope="module")
def spec():
    return controls.default_spec(MARKET, "y_20d_stay")


def pick_event(loader, index, h: int = H):
    """First sampled event whose per-symbol file has ATR history and a full +h window."""
    for symbol, entry_date in v3.sample_events(index, n=40, max_symbols=5, seed=0):
        ohlcv = loader.sample_ohlcv(MARKET, symbol).sort_values("date").reset_index(drop=True)
        try:
            position = v3.entry_position(ohlcv, entry_date)
        except KeyError:
            continue
        if position >= v3.MIN_HISTORY and position + h < len(ohlcv):
            return symbol, entry_date
    raise AssertionError("no sampled event carries a full forward window")


@pytest.fixture(scope="module")
def payload(viz, spec):
    loader, index = viz
    symbol, entry_date = pick_event(loader, index)
    return v3.measure_latency(loader, index, spec, symbol, entry_date, family=FAMILY, h=H)


def test_cells_sidecar_loads_and_geometry_is_determined() -> None:
    assert FAMILY in barriers.available_families()
    cell = barriers.select_cell(barriers.load_cells(FAMILY), market="USD", h=H)
    assert cell is not None and cell["h"] == H
    geometry = barriers.geometry_from_cell(cell, entry_close=100.0, atr_entry=2.0)
    assert geometry.reproducible is True and geometry.k == pytest.approx(0.8)
    assert geometry.upper == pytest.approx(100.0 + 0.8 * 2.0)
    assert geometry.lower == pytest.approx(100.0 - 0.8 * 2.0)
    assert geometry.boundary_class == barriers.OVERLAY_CLASS
    assert geometry.boundary_label == barriers.OVERLAY_LABEL


def test_underdetermined_geometry_is_omitted_and_labeled_not_reproducible() -> None:
    missing_k = barriers.geometry_from_cell({"family": FAMILY, "market": "USD", "h": H}, 100.0, 2.0)
    assert missing_k.reproducible is False and missing_k.upper is None and missing_k.lower is None
    assert "k" in missing_k.reason and missing_k.boundary_label == barriers.NOT_REPRODUCIBLE
    bad_atr = barriers.geometry_from_cell(
        {"family": FAMILY, "market": "USD", "h": H, "k": 0.8}, 100.0, float("nan")
    )
    assert bad_atr.reproducible is False and "ATR" in bad_atr.reason
    no_cell = barriers.geometry_from_cell(None, 100.0, 2.0)
    assert no_cell.reproducible is False and no_cell.boundary_label == barriers.NOT_REPRODUCIBLE


def test_first_touch_picks_the_earliest_barrier_and_pessimistic_tie() -> None:
    entry, atr, k = 100.0, 1.0, 0.8
    up_first = barriers.first_touch([100.5, 100.9, 101.5], [99.9, 99.8, 99.7], entry, atr, k, 3)
    assert up_first["touch"] == barriers.TOUCH_UP and up_first["up_offset"] == 2
    down_first = barriers.first_touch([100.2, 100.3, 100.4], [99.1, 99.0, 98.9], entry, atr, k, 3)
    assert down_first["touch"] == barriers.TOUCH_DOWN and down_first["down_offset"] == 1
    neither = barriers.first_touch([100.1, 100.2], [99.9, 99.8], entry, atr, k, 2)
    assert neither["touch"] == barriers.TOUCH_NONE and neither["up_offset"] is None
    tie = barriers.first_touch([100.9], [99.0], entry, atr, k, 1)
    assert tie["touch"] == barriers.TOUCH_DOWN  # same-bar tie -> stop side wins
    assert up_first["boundary_label"] == barriers.OVERLAY_LABEL


def test_mismatch_badge_and_rate_are_evidence_only() -> None:
    agree = barriers.mismatch(barriers.TOUCH_UP, 1)
    assert agree["badge"] == barriers.MATCH and agree["agrees"] is True
    assert agree["reconciled"] is False and agree["boundary_label"] == barriers.OVERLAY_LABEL
    disagree = barriers.mismatch(barriers.TOUCH_DOWN, 1)
    assert disagree["badge"] == barriers.MISMATCH and disagree["agrees"] is False
    unresolved = barriers.mismatch(barriers.TOUCH_UP, None)
    assert unresolved["badge"] == barriers.UNRESOLVED and unresolved["agrees"] is None
    report = barriers.mismatch_rate([agree, disagree, unresolved], sampled=100)
    assert report["n_scored"] == 2 and report["mismatches"] == 1
    assert report["rate"] == pytest.approx(0.5) and report["reconciled"] is False
    assert report["sampled_target"] == 100 and report["boundary_label"] == barriers.OVERLAY_LABEL


def test_window_is_minus_40_plus_15_bars() -> None:
    assert v3.window_bounds(1000, 500) == (460, 516, 40)
    start, _, offset = v3.window_bounds(100, 5)
    assert start == 0 and offset == 5


def test_build_view_labels_every_overlay_element(payload) -> None:
    elements = payload["overlay_elements"]
    assert elements and all(e["boundary_class"] and e["boundary_label"] for e in elements)
    by_element = {e["element"]: e for e in elements}
    assert by_element["candles"]["boundary_class"] == barriers.ARTIFACT_CLASS
    for name in ("barrier_lines", "first_touch_marker", "exit_marker"):
        assert by_element[name]["boundary_label"] == barriers.OVERLAY_LABEL
    assert by_element["feature_subplot"]["boundary_class"] == "artifact (not recomputed)"
    assert payload["barriers"]["reproducible"] is True
    assert payload["barriers"]["boundary_label"] == barriers.OVERLAY_LABEL


def test_payload_window_is_the_drill_down_slice(payload) -> None:
    window = payload["window"]
    assert window["before"] == 40 and window["after"] == 15
    assert len(payload["candles"]) == window["bars"] == window["stop"] - window["start"]
    assert payload["candles"][window["entry_offset"]]["rel"] == 0
    assert payload["entry_marker"]["rel"] == 0 and payload["exit_marker"]["rel"] == payload["h"]
    assert len(payload["feature_subplot"]["values"]) == window["bars"]
    assert payload["mismatch"]["badge"] in {barriers.MATCH, barriers.MISMATCH, barriers.UNRESOLVED}
    assert payload["mismatch"]["reconciled"] is False


def test_click_to_window_is_within_one_second(payload) -> None:
    assert payload["within_budget"] is True
    assert payload["latency_ms"] <= v3.LATENCY_BUDGET_MS
    assert payload["latency_budget_ms"] == v3.LATENCY_BUDGET_MS


def test_mismatch_rate_on_sampled_events_is_reported(viz, spec) -> None:
    loader, index = viz
    report = v3.mismatch_evidence(loader, index, spec, family=FAMILY, h=H, n=100, seed=1, max_symbols=5)
    assert report["n_sampled"] <= 100 and report["n_scored"] >= 1
    assert report["rate"] is not None and 0.0 <= report["rate"] <= 1.0
    assert report["reconciled"] is False and report["sampled_target"] == 100
    assert report["boundary_label"] == barriers.OVERLAY_LABEL and "up-touch" in report["badge_rule"]


def test_sample_events_is_deterministic_and_bounded(viz) -> None:
    _, index = viz
    first = v3.sample_events(index, n=20, max_symbols=5, seed=3)
    again = v3.sample_events(index, n=20, max_symbols=5, seed=3)
    assert first == again and len(first) == 20
    assert len({symbol for symbol, _ in first}) <= 5


def test_payload_is_strict_json_watermarked_and_carries_no_verdict(payload) -> None:
    text = v3.serialize_payload(payload)
    parsed = json.loads(text)
    assert "NaN" not in text and "Infinity" not in text
    assert parsed["watermark"] == kpi.WATERMARK and "no verdicts" in parsed["watermark"]
    lowered = text.lower()
    for banned in ('"verdict"', '"adopt"', '"reject"', '"recommend"'):
        assert banned not in lowered
    assert parsed["mismatch"]["reconciled"] is False
    assert parsed["barriers"]["boundary_label"] == barriers.OVERLAY_LABEL


def test_view_and_overlay_write_nothing_and_poll_nothing() -> None:
    for module in (v3, barriers):
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "to_parquet" not in source and "write_text" not in source
        assert "dcc.Interval" not in source
    artifact = REPO / "data" / "models" / "wi048" / f"{FAMILY}_cells.json"
    before = (artifact.stat().st_size, artifact.stat().st_mtime_ns)
    barriers.load_cells(FAMILY)
    assert (artifact.stat().st_size, artifact.stat().st_mtime_ns) == before


def test_figures_render_ohlc_with_overlays_and_feature_panel(payload) -> None:
    figures = v3.figures(payload)
    assert set(figures) == {"ohlc", "feature"}
    kinds = {trace.type for trace in figures["ohlc"].data}
    assert "candlestick" in kinds and "scatter" in kinds
    assert barriers.OVERLAY_LABEL in figures["ohlc"].layout.title.text
    assert "artifact" in figures["feature"].layout.title.text
