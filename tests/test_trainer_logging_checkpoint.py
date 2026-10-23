"""Tests for xgb_trainer changes (Step 6): logging, checkpoint, universe."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.xgb_trainer import (
    PurgedWalkForwardSplit,
    build_panel,
    train_market,
)
from src.run_logging import LOG_DIR


@pytest.fixture
def fixture_env(monkeypatch, tmp_path):
    """Point RAW_DIR at the real fixture dir so build_panel uses test data."""
    base = Path(__file__).resolve().parents[1]
    monkeypatch.setattr("src.xgb_trainer.BASE_DIR", tmp_path)
    monkeypatch.setattr("src.feature_engine.BASE_DIR", tmp_path)
    monkeypatch.setattr("src.xgb_trainer.DATA_DIR", tmp_path / "data")
    monkeypatch.setattr("src.xgb_trainer.MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr("src.xgb_trainer.CONFIG_PATH", base / "config" / "settings.yaml")
    monkeypatch.setattr("src.run_logging.LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr("src.stat_metadata.FEATURES_DIR", base / "data" / "features")
    monkeypatch.setattr("src.stat_metadata.CATALOG_PATH", base / "data" / "metadata_catalog_{market}.json")
    monkeypatch.setattr("src.state_manager.LOG_DIR", tmp_path / "logs")
    # Force fixture: set RAW_DIR to empty, FIXTURE_DIR to real fixture
    monkeypatch.setattr("src.feature_engine.RAW_DIR", tmp_path / "nonexistent_raw")
    monkeypatch.setattr("src.feature_engine.FIXTURE_DIR", base / "data" / "raw_ohlcv_test")
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    (tmp_path / "models").mkdir(parents=True, exist_ok=True)
    (tmp_path / "logs").mkdir(parents=True, exist_ok=True)
    # Copy the metadata catalog to where xgb_trainer's load_catalog expects it
    catalog = json.loads((base / "data" / "metadata_catalog_USD.json").read_text())
    (tmp_path / "data" / "metadata_catalog_USD.json").write_text(json.dumps(catalog))
    return tmp_path


def test_build_panel_fixture(fixture_env):
    """build_panel with fixture data produces a valid DataFrame."""
    catalog = json.loads((Path(__file__).resolve().parents[1] / "data" / "metadata_catalog_USD.json").read_text())
    panel = build_panel("USD", catalog, allow_fixture=True, min_date=None)
    assert isinstance(panel, pd.DataFrame)
    assert len(panel) > 0
    assert panel["symbol"].nunique() >= 1
    # Should have cs_pct columns
    surviving = catalog["surviving_features"]
    cs_cols = [f"{c}_cs_pct" for c in surviving if f"{c}_cs_pct" in panel.columns]
    assert len(cs_cols) > 0


def test_xgb_trainer_fixture_run(fixture_env):
    """Smoke test: trainer runs end-to-end on fixture with 1 target, 2 folds, 0 placebo."""
    import yaml
    cfg = yaml.safe_load(open(Path(__file__).resolve().parents[1] / "config" / "settings.yaml"))
    meta = train_market(
        "USD", cfg, n_splits=2, embargo_td=20,
        placebo_seeds=0, targets=["y_15d_high"],
        allow_fixture=True, min_date=None, min_avail_mb=1.0,
    )
    assert meta is not None
    assert "universe" in meta
    assert meta["universe"]["source"] == "fixture"
    assert "targets" in meta
    assert "y_15d_high" in meta["targets"]
    assert len(meta["targets"]["y_15d_high"]["folds"]) >= 1

    # OOF parquet and meta written
    oof_path = fixture_env / "data" / "oof_USD.parquet"
    assert oof_path.exists()
    oof = pd.read_parquet(oof_path)
    assert "p_y_15d_high" in oof.columns or "p_15d_high" in oof.columns

    meta_path = fixture_env / "data" / "train_meta_USD.json"
    assert meta_path.exists()


def test_memory_guard_aborts(fixture_env):
    """Setting min_avail_mb absurdly high causes MemoryGuardError."""
    import yaml
    cfg = yaml.safe_load(open(Path(__file__).resolve().parents[1] / "config" / "settings.yaml"))
    with pytest.raises((RuntimeError, SystemExit)):
        train_market(
            "USD", cfg, n_splits=2, embargo_td=20,
            placebo_seeds=0, targets=["y_15d_high"],
            allow_fixture=True, min_date=None, min_avail_mb=99999999,
        )


def test_purged_walk_forward():
    """PurgedWalkForwardSplit produces non-overlapping date ranges."""
    dates = pd.date_range("2020-01-01", "2022-12-31", freq="B")
    splitter = PurgedWalkForwardSplit(n_splits=3, embargo_td=20)
    folds = list(splitter.split(dates))
    assert len(folds) >= 1
    for tr, va in folds:
        assert len(tr) > 0
        assert len(va) > 0
        # No overlap
        tr_max = dates[tr].max()
        va_min = dates[va].min()
        assert tr_max < va_min