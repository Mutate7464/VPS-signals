"""WI-087: View 1 legacy-target stats - decile n, date-cluster CIs, shuffled null.

Evidence is the real artifacts: CAD, target `y_20d_stay`, feature `atr_pct_20`,
filtered to 2025+ (135,343 feature rows, ~430 dates), which is the shape the
Plan 26-W47 latency estimates assume.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import src.visualizer.join as join_module
from src.visualizer import controls, kpi
from src.visualizer.loader import VisualizerLoader
from src.visualizer.stats import bootstrap, null
from src.visualizer.views import v1_feature_target as v1

REPO = Path(__file__).resolve().parents[2]
MARKET = "CAD"
FEATURE = "atr_pct_20"
TARGET = "y_20d_stay"
LABEL = "y_20d_stay"
DATE_RANGE = ("2025-01-01", "2026-09-30")
SEED = bootstrap.SEED_DEFAULT


@pytest.fixture(scope="module")
def view_inputs(tmp_path_factory):
    state_dir = tmp_path_factory.mktemp("viz_state_v1")
    loader = VisualizerLoader(state_dir=state_dir)
    index = join_module.load_or_build(loader, MARKET, state_dir=state_dir)
    spec = controls.default_spec(MARKET, TARGET, DATE_RANGE)
    rows, counts = v1.retained_frame(loader, index, spec, FEATURE, TARGET)
    return loader, index, rows, counts


@pytest.fixture(scope="module")
def payload(view_inputs):
    _, _, rows, _ = view_inputs
    return v1.measure_budget(rows, FEATURE, TARGET, market=MARKET)


def reference_deciles(rows: pd.DataFrame, n_bins: int = 10) -> pd.DataFrame:
    values = rows[FEATURE].to_numpy(dtype="float64")
    edges = np.quantile(values, np.linspace(0.0, 1.0, n_bins + 1))
    bins = np.clip(np.searchsorted(edges[1:-1], values, side="left"), 0, n_bins - 1)
    table = pd.DataFrame({"bin": bins, "label": rows[LABEL].to_numpy(dtype="float64")})
    grouped = table.groupby("bin", sort=True).agg(n=("label", "size"), hits=("label", "sum"))
    return grouped.reindex(range(n_bins), fill_value=0).astype({"n": "int64", "hits": "int64"})


def test_retained_frame_is_join_aligned_filtered_and_typed(view_inputs) -> None:
    _, _, rows, counts = view_inputs
    assert counts["retained_rows"] == len(rows) > 10_000
    assert counts["label_source"] == "targets" and counts["label_column"] == LABEL
    assert counts["rows_after_spec"] >= counts["retained_rows"]
    assert rows[FEATURE].dtype == np.float32 and rows[LABEL].dtype == np.float32
    assert rows[FEATURE].notna().all() and rows[LABEL].notna().all()
    dates = pd.to_datetime(rows["date"])
    assert dates.min() >= pd.Timestamp(DATE_RANGE[0]) and dates.max() <= pd.Timestamp(DATE_RANGE[1])
    assert set(np.unique(rows[LABEL].to_numpy())) <= {0.0, 1.0}
    assert 0.0 < float(rows[LABEL].mean()) < 1.0


def test_label_for_maps_every_selector_onto_the_observed_label() -> None:
    assert v1.label_for("y_20d_stay") == ("targets", "y_20d_stay")
    assert v1.label_for("y_y_15d_high") == ("targets", "y_15d_high")
    assert v1.label_for("p_y_20d_down") == ("targets", "y_20d_down")
    with pytest.raises(KeyError):
        v1.label_for("fold_y_20d_up")
    with pytest.raises(KeyError):
        v1.label_for("not_a_target")


def test_retained_frame_rejects_foreign_market_and_non_feature_columns(view_inputs) -> None:
    loader, index, _, _ = view_inputs
    spec = controls.default_spec(MARKET, TARGET, DATE_RANGE)
    with pytest.raises(ValueError, match="float32 feature"):
        v1.retained_frame(loader, index, spec, "close", TARGET)
    foreign = controls.default_spec(MARKET, TARGET, DATE_RANGE)
    foreign["market"] = "USD"
    with pytest.raises(ValueError, match="join market"):
        v1.retained_frame(loader, index, foreign, FEATURE, TARGET)


def test_decile_n_sums_to_the_retained_count(payload) -> None:
    deciles = payload["deciles"]
    assert len(deciles) == payload["decile_bins"] == v1.DECILE_BINS
    assert sum(entry["n"] for entry in deciles) == payload["decile_n_total"] == payload["retained_rows"]
    assert all(entry["n"] >= 0 and 0 <= entry["hits"] <= entry["n"] for entry in deciles)
    summary = pd.DataFrame(deciles)
    assert summary["n"].sum() == payload["retained_rows"]
    assert summary["hits"].sum() == payload["n_true"]
    assert np.all(np.diff(summary["low"].to_numpy()) >= 0.0)
    rates = summary.loc[summary["n"] > 0, "hit_rate"].to_numpy()
    assert np.all((rates >= 0.0) & (rates <= 1.0))


def test_deciles_match_a_pandas_quantile_reference(view_inputs, payload) -> None:
    _, _, rows, _ = view_inputs
    reference = reference_deciles(rows, payload["decile_bins"])
    deciles = pd.DataFrame(payload["deciles"]).set_index("bin")
    np.testing.assert_array_equal(deciles["n"].to_numpy(), reference["n"].to_numpy())
    np.testing.assert_array_equal(deciles["hits"].to_numpy(), reference["hits"].to_numpy())
    for entry in payload["deciles"]:
        assert entry["hit_rate"] == pytest.approx(entry["hits"] / entry["n"], abs=1e-9)


def test_histograms_split_the_retained_rows_on_shared_edges(payload) -> None:
    hist = payload["histograms"]
    assert hist["bins"] <= v1.BIN_LIMIT and len(hist["edges"]) == hist["bins"] + 1
    assert len(hist["true"]) == len(hist["false"]) == hist["bins"]
    assert sum(hist["true"]) == hist["n_true"] == payload["n_true"]
    assert sum(hist["false"]) == hist["n_false"]
    assert hist["n_true"] + hist["n_false"] == payload["retained_rows"]
    assert np.all(np.diff(hist["edges"]) >= 0.0)
    edges = [payload["deciles"][0]["low"]] + [entry["high"] for entry in payload["deciles"]]
    assert payload["edge_duplicates"] == int(np.sum(np.diff(edges) == 0.0))


def test_bootstrap_cis_are_reproducible_and_resample_dates(view_inputs) -> None:
    _, _, rows, _ = view_inputs
    agg = bootstrap.preaggregate(
        rows["date"].to_numpy(),
        v1.assign_bins(rows[FEATURE].to_numpy(dtype="float32"), v1.decile_edges(rows[FEATURE], 10)),
        rows[LABEL].to_numpy(dtype="float64"),
    )
    first = bootstrap.date_cluster_bootstrap(agg, 10, b=64, seed=SEED)
    again = bootstrap.date_cluster_bootstrap(agg, 10, b=64, seed=SEED)
    assert first["resample_unit"] == "date" and first["n_dates"] == int(rows["date"].nunique())
    np.testing.assert_array_equal(first["low"], again["low"])
    np.testing.assert_array_equal(first["high"], again["high"])
    totals = first["n_resampled_rows"].sum(axis=1)
    assert first["n_resampled_rows"].shape == (64, 10)
    assert abs(totals.mean() - len(rows)) / len(rows) < 0.10
    assert np.all((first["low"] <= first["high"]) | np.isnan(first["low"]))
    other = bootstrap.date_cluster_bootstrap(agg, 10, b=64, seed=SEED + 1)
    assert not np.array_equal(np.nan_to_num(other["low"]), np.nan_to_num(first["low"]))


def test_shuffled_null_mean_matches_the_base_rate_within_mc_error(payload) -> None:
    shuffled = payload["null"]
    assert shuffled["method"].startswith("within-date")
    assert shuffled["within_mc_error"] is True
    assert abs(shuffled["delta"]) <= 3.0 * shuffled["mc_error"] + 1e-9
    assert shuffled["base_rate"] == pytest.approx(payload["hit_rate"], abs=1e-12)
    assert shuffled["n_hits_total"] == payload["n_true"]
    assert shuffled["per_date_hits_preserved"] is True
    rates = [entry["null_rate"] for entry in payload["deciles"]]
    assert max(rates) - min(rates) > 0.0
    assert all(entry["null_low"] <= entry["null_high"] for entry in payload["deciles"])


def test_null_and_cis_are_reproducible_from_the_recorded_seed(view_inputs) -> None:
    _, _, rows, _ = view_inputs
    first = v1.compute_view(rows, FEATURE, TARGET, market=MARKET, b=64, sims=64, seed=SEED)
    again = v1.compute_view(rows, FEATURE, TARGET, market=MARKET, b=64, sims=64, seed=SEED)
    assert first["deciles"] == again["deciles"] and first["null"] == again["null"]
    assert first["bootstrap"]["seed"] == SEED and first["null"]["seed"] == SEED
    other = v1.compute_view(rows, FEATURE, TARGET, market=MARKET, b=64, sims=64, seed=SEED + 1)
    assert any(
        left["ci_low"] != right["ci_low"] or left["null_rate"] != right["null_rate"]
        for left, right in zip(first["deciles"], other["deciles"])
    )


def test_compute_and_serialize_stay_inside_the_server_budgets(payload) -> None:
    assert payload["within_limits"] is True
    assert payload["budget_ms"]["compute_within"] is True
    assert payload["budget_ms"]["compute"] <= v1.COMPUTE_BUDGET_MS
    assert payload["budget_ms"]["serialize_within"] is True
    assert payload["budget_ms"]["serialize"] <= v1.SERIALIZE_BUDGET_MS
    assert 0 < payload["payload_bytes"] <= v1.PAYLOAD_LIMIT_BYTES


def test_payload_is_strict_json_watermarked_and_carries_no_verdict(payload) -> None:
    text = v1.serialize_payload(payload)
    parsed = json.loads(text)
    assert len(text.encode("utf-8")) == parsed["payload_bytes"] == payload["payload_bytes"]
    assert "NaN" not in text and "Infinity" not in text
    assert parsed["watermark"] == kpi.WATERMARK and "no verdicts" in parsed["watermark"]
    assert parsed["decile_n_total"] == parsed["retained_rows"]
    lowered = text.lower()
    for banned in ("verdict", "adopt", "reject", "recommend"):
        assert f'"{banned}"' not in lowered  # no field is named like a verdict
    assert "no verdict" in lowered and parsed["notes"][0].endswith("no adopt/reject field.")
    assert parsed["null"]["within_mc_error"] is True


def test_view_writes_nothing_and_opens_the_artifacts_read_only(view_inputs) -> None:
    _, _, rows, _ = view_inputs
    source = Path(v1.__file__).read_text(encoding="utf-8")
    assert "to_parquet" not in source and "write_text" not in source and "dcc.Interval" not in source
    artifact = REPO / "data" / "features" / "targets_CAD.parquet"
    before = (artifact.stat().st_size, artifact.stat().st_mtime_ns)
    payload = v1.compute_view(rows, FEATURE, TARGET, market=MARKET, b=32, sims=32)
    assert payload["view"] == v1.VIEW_NAME and payload["market"] == MARKET
    assert (artifact.stat().st_size, artifact.stat().st_mtime_ns) == before


def test_figures_render_both_panels_from_the_payload(payload) -> None:
    figures = v1.figures(payload)
    assert set(figures) == {"histogram", "decile"}
    assert len(figures["histogram"].data) == 2 and len(figures["decile"].data) == 4
    assert payload["feature"] in figures["histogram"].layout.title.text


def test_null_module_reports_the_method_and_the_seed() -> None:
    assert null.SIM_DEFAULT == 200
    assert bootstrap.B_DEFAULT == 200
    assert null.SEED_DEFAULT == bootstrap.SEED_DEFAULT == SEED
    assert null.CONFIDENCE == bootstrap.CONFIDENCE == pytest.approx(0.95)
