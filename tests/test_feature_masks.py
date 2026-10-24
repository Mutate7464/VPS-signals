"""Regression: every E3 ablation mask must resolve non-empty, and `full` must be
E2-faithful (wl + wl_cs_pct).

Covers the 2026-10-23 bug where the trainer's memory-slim `keep_cols` dropped all
`_cs_pct` columns: cs_pct_only then resolved to zero features ("no valid features"
on every target) while the other four sets silently trained raw-only instead of
wl + wl_cs_pct.
"""
import pandas as pd
import pytest

from src.xgb_trainer import TARGET_COLUMNS, load_catalog, target_features
from src.feature_engine import FIB_FEATURE_NAMES


@pytest.fixture()
def slim_panel_cols():
    catalog = load_catalog("USD")
    surviving = list(catalog["surviving_features"])
    # columns the slim mask keeps AFTER the fix (mirrors train_market's keep_cols)
    cols = (
        set(surviving)
        | {f"{c}_cs_pct" for c in surviving}
        | set(FIB_FEATURE_NAMES)
        | set(TARGET_COLUMNS)
        | {"date", "symbol", "market", "close", "fwd_atr_ret_15", "fwd_atr_ret_20"}
    )
    return catalog, cols


def test_all_masks_nonempty_for_all_targets(slim_panel_cols):
    catalog, cols = slim_panel_cols
    for fs in ("full", "no_static", "fib_only", "legacy19", "cs_pct_only"):
        for tgt in TARGET_COLUMNS:
            feats = [f for f in target_features(catalog, tgt, feature_set=fs, panel_cols=cols)
                     if f in cols]
            assert feats, f"mask {fs} resolved to zero features for {tgt}"


def test_full_is_e2_faithful_wl_plus_cs_pct(slim_panel_cols):
    catalog, cols = slim_panel_cols
    tgt = TARGET_COLUMNS[0]
    feats = [f for f in target_features(catalog, tgt, feature_set="full", panel_cols=cols)
             if f in cols]
    wl = catalog["whitelist_per_target"][tgt]
    assert set(feats) == set(wl) | {f"{f}_cs_pct" for f in wl}


def test_cs_pct_only_is_ranks_only(slim_panel_cols):
    catalog, cols = slim_panel_cols
    tgt = TARGET_COLUMNS[0]
    feats = [f for f in target_features(catalog, tgt, feature_set="cs_pct_only", panel_cols=cols)
             if f in cols]
    assert feats and all(f.endswith("_cs_pct") for f in feats)
