"""WI-085 schema contracts asserted against the REAL artifacts (both markets).

Measured on disk 2026-11-19: features = 92 columns (89 float32 + `date`/`symbol`/`market`
keys), NOT the plan's assumed 249; OOF canonical = 41 columns (CAD's primary OOF file is
an extended 57-column variant); l0_ext = 2,593,425 USD / 1,401,504 CAD rows.
"""
from __future__ import annotations

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.visualizer import MARKETS, feature_path, l0_ext_path, oof_path, targets_path
from src.visualizer.loader import VisualizerLoader
from src.visualizer.schema import (
    FEATURE_COLUMNS,
    FEATURE_FLOAT_COLUMNS,
    L0_EXT_COLUMNS,
    L0_EXT_ROWS_MEASURED,
    N_FEATURE_COLUMNS,
    N_FEATURE_FLOAT32,
    OOF_CANONICAL_COLUMNS,
    OOF_CANONICAL_N,
    OOF_TARGETS,
    OOF_VARIANT_RE,
    PANEL_ROWS_MEASURED,
    SAMPLE_OHLCV_PER_MARKET,
    TARGET_COLUMNS,
    SchemaError,
    assert_all_artifacts,
    assert_features_schema,
    assert_oof_schema,
    sampled_ohlcv_paths,
)


@pytest.fixture(scope="module")
def report() -> dict:
    """One full startup-contract pass over every real artifact."""
    return assert_all_artifacts()


def test_feature_contract_is_the_measured_92_column_set(report: dict) -> None:
    assert N_FEATURE_COLUMNS == 92 and N_FEATURE_FLOAT32 == 89
    assert len(FEATURE_COLUMNS) == 92 and len(FEATURE_FLOAT_COLUMNS) == 89
    for market in MARKETS:
        entry = report["markets"][market]["features"]
        assert entry["columns"] == 92
        assert entry["columns"] != 249  # the plan's assumed panel width
        assert entry["float32_columns"] == 89
        assert entry["keys"] == ["date", "symbol", "market"]
        assert entry["rows"] == PANEL_ROWS_MEASURED[market]
        assert entry["key_duplicate_rows"] == 0
        assert entry["date_type"].startswith("timestamp")


def test_feature_float_columns_are_float32_on_disk() -> None:
    for market in MARKETS:
        schema = pq.ParquetFile(feature_path(market)).schema_arrow
        assert [n for n in schema.names if n not in ("date", "symbol", "market")] == list(FEATURE_FLOAT_COLUMNS)
        for name in FEATURE_FLOAT_COLUMNS:
            assert schema.field(name).type == pa.float32(), name


def test_targets_contract(report: dict) -> None:
    for market in MARKETS:
        entry = report["markets"][market]["targets"]
        assert entry["columns"] == len(TARGET_COLUMNS) == 8
        assert entry["required_present"] == ["market", "y_20d_stay"]
        assert entry["key_duplicate_rows"] == 0
        assert entry["rows"] == PANEL_ROWS_MEASURED[market]


def test_oof_canonical_41_columns_and_variant_extras(report: dict) -> None:
    assert OOF_CANONICAL_N == 41 and len(OOF_CANONICAL_COLUMNS) == 41
    usd = report["markets"]["USD"]["oof"]
    assert usd["columns"] == 41 and usd["variant_extra_columns"] == []
    cad = report["markets"]["CAD"]["oof"]
    assert cad["canonical_columns"] == 41
    assert len(cad["variant_extra_columns"]) == 16
    assert cad["columns"] == 57
    assert all(OOF_VARIANT_RE.match(c) for c in cad["variant_extra_columns"])


def test_oof_probability_fold_and_label_contract(report: dict) -> None:
    for market in MARKETS:
        entry = report["markets"][market]["oof"]
        assert entry["p_ranges"], "no p_* columns recorded"
        for name, (low, high) in entry["p_ranges"].items():
            assert low is None or 0.0 <= low <= high <= 1.0, f"{name}: {low}..{high}"
        assert all(kind.startswith("int") for kind in entry["fold_types"].values())
        for name, values in entry["y_value_sets"].items():
            assert set(values) <= {0, 1, None}, f"{name}: {values}"
        for target in OOF_TARGETS:
            assert f"y_{target}" in entry["y_value_sets"]
            assert f"p_{target}" in entry["p_ranges"]
            assert f"fold_{target}" in entry["fold_types"]


def test_every_usd_oof_variant_carries_the_41_column_set() -> None:
    variants = VisualizerLoader().row_counts()["oof_variants"]["USD"]
    assert variants, "no USD OOF variants found"
    for stem, rows in variants.items():
        schema = pq.ParquetFile(oof_path("USD", stem.replace("oof_USD_", ""))).schema_arrow
        assert tuple(schema.names) == OOF_CANONICAL_COLUMNS, stem
        assert rows == PANEL_ROWS_MEASURED["USD"]


def test_l0_ext_contract_all_features_both_markets(report: dict) -> None:
    assert len(report["l0_ext"]) == len(L0_EXT_COLUMNS) * len(MARKETS) == 12
    for market in MARKETS:
        for feature, columns in L0_EXT_COLUMNS.items():
            entry = report["l0_ext"][f"{feature}_{market}"]
            assert entry["columns"] == list(columns)
            assert entry["date_type"] == "date32[day]"
            assert entry["rows"] == L0_EXT_ROWS_MEASURED[market]
            if feature == "nr_flags":
                assert entry["key_duplicate_rows"] == 0
        assert L0_EXT_ROWS_MEASURED[market] > PANEL_ROWS_MEASURED[market]


def test_l0_ext_join_reports_unmatched_counts() -> None:
    loader = VisualizerLoader()
    for market in MARKETS:
        frame, counts = loader.join_l0_ext(market, "nr_flags")
        assert counts["feature"] == "nr_flags" and counts["market"] == market
        assert counts["matched_rows"] == counts["panel_rows"]
        assert counts["unmatched_panel_rows"] == 0
        assert counts["ext_rows"] == L0_EXT_ROWS_MEASURED[market]
        assert counts["ext_rows_outside_panel"] == counts["ext_rows"] - counts["matched_rows"] > 0
        assert "nr4" in frame.columns and len(frame) == counts["ext_rows"]


def test_raw_ohlcv_sample_is_10_files_with_date32(report: dict) -> None:
    assert len(sampled_ohlcv_paths()) == 10 == 2 * SAMPLE_OHLCV_PER_MARKET
    assert len(report["raw_ohlcv"]) == 10
    for entry in report["raw_ohlcv"]:
        assert entry["date_type"] == "date32[day]"
        assert entry["dates_monotonic"] is True
        assert entry["rows"] > 0
        assert len(entry["columns"]) == 8


def test_drift_is_detected_not_ignored(tmp_path) -> None:
    bad = tmp_path / "features_USD.parquet"
    pq.write_table(
        pa.table(
            {
                "date": pa.array([], type=pa.timestamp("ns")),
                "symbol": pa.array([], type=pa.string()),
                "market": pa.array([], type=pa.string()),
                "rsi_5": pa.array([], type=pa.float32()),
            }
        ),
        bad,
    )
    with pytest.raises(SchemaError):
        assert_features_schema(bad, "USD")

    bad_oof = tmp_path / "oof_USD.parquet"
    pq.write_table(
        pa.table({"date": pa.array([], type=pa.timestamp("ns")), "unexpected_metric": pa.array([], type=pa.float32())}),
        bad_oof,
    )
    with pytest.raises(SchemaError):
        assert_oof_schema(bad_oof, "USD")
