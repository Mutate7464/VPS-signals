"""WI-009b slim training read: the keep list must never drop a derived column.

Regression-locks the E3 bug class (2026-10-23): a memory-slim `keep_cols` that
dropped every `_cs_pct` column, so five feature-set masks silently resolved to
zero features. Here the same invariant is asserted for the WI-009b read path,
and the existing `xgb_trainer` masks are re-checked against the slimmed column
set so slimming cannot break a downstream mask either.
"""
import numpy as np
import pandas as pd
import pytest

from src.models.training_data import (
    ID_COLUMNS,
    feature_census,
    feature_columns,
    keep_columns,
    load_feature_panel,
    schema_column_names,
)

CAD_PARQUET = "data/features/features_CAD.parquet"
CAD_CATALOG = "data/metadata_catalog_CAD.json"


def _synthetic_schema() -> list[str]:
    """ids + classic indicators + the derived families the E3 bug dropped."""
    return [
        "date", "symbol", "market",
        "rsi_14", "macd_norm_hist", "hb_vol", "resid_sign_frac", "hb_noise_ratio",
        "range_pos_f15", "range_width_f15", "fib_dist_f39", "gap_z",
        "rsi_14_cs_pct", "hb_vol_cs_pct",
        "fwd_atr_ret_15", "fwd_atr_ret_20", "e5_rev_1m", "e5_vol_20",
    ]


# --------------------------------------------------------------------------- #
# the mask rule
# --------------------------------------------------------------------------- #
def test_keep_list_keeps_ids_and_every_feature():
    keep = keep_columns(_synthetic_schema())
    feats = feature_columns(keep)
    assert set(ID_COLUMNS[:2]) <= set(keep)
    assert len(feats) == len(_synthetic_schema()) - 3 - 2 - 2  # ids, labels, e5_*
    assert "rsi_14" in feats


def test_keep_list_retains_derived_cs_pct_and_range_fib_families():
    """The E3 failure mode: derived columns silently dropped by a slim mask."""
    keep = keep_columns(_synthetic_schema())
    for derived in ("rsi_14_cs_pct", "hb_vol_cs_pct", "range_pos_f15", "range_width_f15", "fib_dist_f39", "gap_z"):
        assert derived in keep, f"slim keep list dropped derived column {derived}"
    census = feature_census(keep)
    assert census["cs_pct"] == 2 and census["range_fib"] == 4 and census["classic"] == 5


def test_keep_list_drops_labels_and_e5_factor_columns():
    keep = keep_columns(_synthetic_schema())
    for excluded in ("fwd_atr_ret_15", "fwd_atr_ret_20", "e5_rev_1m", "e5_vol_20"):
        assert excluded not in keep


def test_keep_list_rejects_a_schema_with_no_features():
    with pytest.raises(ValueError):
        keep_columns(["date", "symbol", "market", "fwd_atr_ret_15"])


def test_keep_list_rejects_a_schema_without_identifiers():
    with pytest.raises(ValueError):
        keep_columns(["rsi_14", "macd_norm_hist"])


def test_census_guard_fires_if_a_family_is_ever_filtered_out(monkeypatch):
    """The guard must be able to fire — a tautological check is no check.

    Simulates the E3 bug class directly: a future `feature_columns` that becomes
    a whitelist forgetting the `_cs_pct` family must make `keep_columns` refuse.
    """
    import src.models.training_data as td

    schema = _synthetic_schema()
    assert keep_columns(schema)  # baseline: fine

    real = td.feature_columns
    monkeypatch.setattr(
        td, "feature_columns", lambda names: [c for c in real(names) if not c.endswith("_cs_pct")]
    )
    with pytest.raises(ValueError, match="census"):
        keep_columns(schema)


# --------------------------------------------------------------------------- #
# real CAD schema
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(
    not __import__("pathlib").Path(CAD_PARQUET).exists(), reason="CAD feature panel not built"
)
def test_cad_slim_read_keeps_all_89_features():
    names = schema_column_names(CAD_PARQUET)
    keep = keep_columns(names)
    feats = feature_columns(keep)
    assert len(feats) == 89, f"expected the WI-009 89-feature panel, got {len(feats)}"
    assert len(keep) == len(names), "slim read dropped a column that the source carries"
    # the guard's invariant, asserted explicitly for the real schema
    assert feature_census(keep) == feature_census(names)
    census = feature_census(names)
    # 16 range_pos/width + 2 donchian + 2 compression + 2 pct_from + 3 fib_dist + gap_z
    assert census["range_fib"] == 26, "the range/fib expansion must survive the slim read"


@pytest.mark.skipif(
    not __import__("pathlib").Path(CAD_PARQUET).exists(), reason="CAD feature panel not built"
)
def test_cad_slim_read_loads_float32_and_no_e5_or_label_columns(tmp_path):
    panel, feats, census = load_feature_panel(
        "CAD", start="2026-06-01", end="2026-06-30", path=CAD_PARQUET
    )
    assert len(panel) > 0
    assert "date" in panel.columns and "symbol" in panel.columns
    assert not any(c.startswith("e5_") for c in panel.columns)
    assert not any(c.startswith("fwd_atr_ret_") for c in panel.columns)
    assert set(feats) == {c for c in panel.columns if c not in ID_COLUMNS}
    for c in feats:
        assert panel[c].dtype == np.float32
    assert census == feature_census(panel.columns.tolist() + ["e5_rev_1m"])


@pytest.mark.skipif(
    not __import__("pathlib").Path(CAD_PARQUET).exists()
    or not __import__("pathlib").Path(CAD_CATALOG).exists(),
    reason="CAD panel/catalog not built",
)
def test_every_trainer_mask_still_resolves_nonempty_on_the_slim_read():
    """E3 pattern, extended: slimming must not break any feature-set mask."""
    from src.feature_engine import FIB_FEATURE_NAMES
    from src.xgb_trainer import TARGET_COLUMNS, load_catalog, target_features

    catalog = load_catalog("CAD")
    cols = set(keep_columns(schema_column_names(CAD_PARQUET)))
    cols |= set(TARGET_COLUMNS) | {f"{c}_cs_pct" for c in catalog["surviving_features"]}
    cols |= {"close"} | set(FIB_FEATURE_NAMES)
    for feature_set in ("full", "no_static", "fib_only", "legacy19", "cs_pct_only"):
        for tgt in TARGET_COLUMNS:
            feats = [
                f
                for f in target_features(catalog, tgt, feature_set=feature_set, panel_cols=cols)
                if f in cols
            ]
            assert feats, f"mask {feature_set} resolved to zero features for {tgt}"


# --------------------------------------------------------------------------- #
# loader independence
# --------------------------------------------------------------------------- #
def test_loader_reads_only_the_slim_columns_from_a_fixture(tmp_path):
    import pyarrow as pa
    import pyarrow.parquet as pq

    n = 5
    table = pa.table(
        {
            "date": pd.to_datetime(["2024-01-02"] * n),
            "symbol": [f"S{i}" for i in range(n)],
            "market": ["CAD"] * n,
            "rsi_14": np.arange(n, dtype="float64"),
            "range_pos_f15": np.arange(n, dtype="float64"),
            "rsi_14_cs_pct": np.arange(n, dtype="float64"),
            "fwd_atr_ret_15": np.arange(n, dtype="float64"),
            "e5_rev_1m": np.arange(n, dtype="float64"),
        }
    )
    path = tmp_path / "features_FIX.parquet"
    pq.write_table(table, str(path))

    panel, feats, census = load_feature_panel("FIX", path=path)
    assert set(panel.columns) == {"date", "symbol", "market", "rsi_14", "range_pos_f15", "rsi_14_cs_pct"}
    assert set(feats) == {"rsi_14", "range_pos_f15", "rsi_14_cs_pct"}
    assert census == {"classic": 1, "range_fib": 1, "cs_pct": 1}
    assert all(panel[c].dtype == np.float32 for c in feats)
    assert (panel["date"] == pd.Timestamp("2024-01-02")).all()