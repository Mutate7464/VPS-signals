"""WI-047 — feature-inventory parser tests against the current WI-036 panel schema.

The inventory is research-only (D-025 Tier 1 / D-023 §2): the tests check that the
source parser sees every panel block, that classification covers the panel bar
(>= 95%), and that the WI-040 permutation top-20 in both markets is classified.
"""

from __future__ import annotations

import pandas as pd

from src.feature_engine import wi016_feature_names
from src.swing_bsh import feature_inventory as fi

# reports/wi040_calibration.md — winner-cell OOF permutation top-20 (USD / CAD).
TOP20_USD = ["cs_entropy_102", "entropy_24", "atr_pct_3", "hurst_15", "kama_er_15",
             "hurst_39", "adx_144", "month", "di_spread_233", "adx_21", "entropy_9",
             "adx_3", "dow", "state_is_bottom", "sec_Capital Markets",
             "sec_Consumer Cyclical", "sec_Retail - Cyclical", "sec_Software",
             "sec_Oil & Gas", "sec_Hardware"]
TOP20_CAD = ["atr_pct_3", "di_spread_3", "range_compression_8_55", "entropy_39",
             "hurst_39", "adx_21", "kama_er_15", "swing_depth_atr", "cs_di_spread_144",
             "donchian_break_233", "cs_hurst_9", "k", "sec_Consumer Defensive",
             "hurst_9", "sec_Asset Management", "sec_Metals & Mining", "sec_Industrials",
             "sec_Energy", "sec_Oil & Gas", "sec_REITs"]

EXPECTED_FAMILY = {
    "atr_pct_3": "volatility", "yangzhang_21": "volatility", "range_compression_8_55": "volatility",
    "entropy_24": "entropy_fractal", "hurst_39": "entropy_fractal", "kama_er_15": "entropy_fractal",
    "adx_21": "momentum", "donchian_break_233": "momentum", "di_spread_233": "momentum",
    "rsi_14": "mean_reversion", "bb_pct_b_21": "mean_reversion", "range_pos_55": "mean_reversion",
    "amihud_21": "volume_liquidity", "obv_zscore_55": "volume_liquidity", "vwap_dist": "volume_liquidity",
    "volume_z_21": "volume_liquidity", "cs_entropy_102": "cross_sectional",
    "sec_Oil & Gas": "sector", "srel_atr_pct_21": "sector", "breadth_top": "breadth",
    "swing_depth_atr": "event_quality", "bars_since_opp": "event_quality", "dd_age": "event_quality",
    "dow": "calendar", "month": "calendar", "symbol": "keys", "state_is_bottom": "keys", "k": "keys",
}


def test_parser_reads_every_panel_block():
    p = fi.parse_panel_schema()
    assert set(p["ext_columns"]) == {"volume_z_21", "volume_z_55", "volume_trend_21",
                                     "vwap_dist", "bar_count_z_55", "bar_count_trend_21"}
    assert p["event_quality"] == ["swing_depth_atr", "bars_since_opp", "dd_age"]
    assert p["calendar"] == ["dow", "month"]
    assert p["breadth"] == ["breadth_bottom", "breadth_top"]
    assert set(p["key_columns"]) >= {"symbol", "date", "state", "close", "atr"}
    assert p["sector_prefixes"] == ["sec_", "srel_"]
    assert p["cs_prefix"] == "cs_"
    assert {"adx_", "entropy_", "amihud_"} <= set(p["smooth_prefixes"])
    assert {"volume_", "sec_", "cs_"} <= set(p["ext_prefixes"])
    assert p["sector_rank"] == ["adx_21", "di_spread_21", "atr_pct_21", "bb_pct_b_21",
                                "range_pos_21", "rsi_14"]


def test_schema_covers_the_wi016_grid_and_the_derived_blocks():
    schema = fi.panel_schema()
    grid = wi016_feature_names()
    assert [c for c in grid if c not in schema] == []
    assert len(schema) >= len(grid) + 100  # grid + keys/ext/meta/calendar/breadth/sector/cs
    assert schema["cs_entropy_102"] == "cs_rank" and schema["sec_Oil & Gas"] == "sector"
    assert schema["atr_pct_3"] == "wi016" and schema["volume_z_21"] == "ext"


def test_inventory_coverage_bar_and_no_unclaimed_columns():
    inv = fi.build_inventory()
    assert fi.coverage(inv) >= fi.MIN_COVERAGE
    assert fi.unmatched(inv) == []
    assert set(inv["family"]) <= set(fi.FAMILIES)
    assert set(inv["block"]) == {"key", "wi016", "ext", "event_quality", "calendar",
                                 "breadth", "sector", "cs_rank"}


def test_unknown_column_is_reported_not_guessed():
    panel = pd.DataFrame(columns=["atr_pct_3", "entropy_24", "symbol", "foo_ratio"])
    inv = fi.build_inventory(panel=panel)
    assert fi.unmatched(inv) == ["foo_ratio"]
    assert fi.classify("foo_ratio") is None
    assert inv.loc[inv["column"] == "symbol", "family"].item() == "keys"
    assert fi.coverage(inv) == 0.75


def test_families_cover_the_wi040_top20_in_both_markets():
    for column in TOP20_USD + TOP20_CAD:
        assert fi.classify(column) is not None, column
    for column, family in EXPECTED_FAMILY.items():
        assert fi.classify(column) == family, column


def test_aligned_flag_tracks_wi040_evidence():
    inv = fi.build_inventory().set_index("column")
    assert bool(inv.loc["cs_entropy_102", "aligned"])
    assert inv.loc["cs_entropy_102", "usd_auc_drop"] == 0.0292
    assert inv.loc["atr_pct_3", "cad_auc_drop"] == 0.0469
    assert not bool(inv.loc["volume_z_21", "aligned"])          # family present, no evidence yet
    assert not bool(inv.loc["symbol", "aligned"])
    evidence = set(fi.ATTRIBUTION_USD) | set(fi.ATTRIBUTION_CAD)
    dropped = {c for c in evidence if (fi.ATTRIBUTION_USD.get(c, 0.0)
                                       + fi.ATTRIBUTION_CAD.get(c, 0.0)) > 0}
    assert set(inv.index[inv["aligned"]]) == dropped & set(inv.index)
    assert {"cs_entropy_102", "atr_pct_3", "month", "swing_depth_atr"} <= dropped


def test_family_summary_partitions_the_classified_inventory():
    inv = fi.build_inventory()
    fam = fi.family_summary(inv)
    assert int(fam["columns"].sum()) == int(inv["family"].notna().sum()) == len(inv)
    assert set(fam.index) <= set(fi.FAMILIES)
    assert fam.loc["entropy_fractal", "aligned"] >= 1 and fam.loc["cross_sectional", "columns"] > 50
    assert fam.loc["volume_liquidity", "aligned"] == 0             # the volume/liquidity gap


def test_inventory_accepts_an_explicit_column_iterable():
    inv = fi.build_inventory(panel=["atr_pct_3", "month"], sectors=["Oil & Gas"])
    assert inv["family"].tolist() == ["volatility", "calendar"]
    assert fi.panel_schema(sectors=["Oil & Gas"])["sec_Oil & Gas"] == "sector"
