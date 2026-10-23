"""Tests: trainer's persisted-parquet join produces the same panel as recompute (Step 3)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.feature_engine import compute_features
from src.targets import compute_targets
from src.xgb_trainer import build_panel

BASE = Path(__file__).resolve().parents[1]


def _synthetic_ohlcv(seed: int, n: int = 400) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.02, n)))
    spread = np.abs(rng.normal(0, 0.01, n)) + 0.005
    return pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=n, freq="B"),
            "open": close * (1 + rng.normal(0, 0.003, n)),
            "high": close * (1 + spread),
            "low": close * (1 - spread),
            "close": close,
            "volume": rng.integers(1e5, 1e7, n).astype("float64"),
        }
    )


@pytest.fixture()
def market_env(monkeypatch, tmp_path):
    """Two synthetic USD tickers with raw parquet + persisted features/targets."""
    raw_dir = tmp_path / "raw_ohlcv" / "market=USD"
    raw_dir.mkdir(parents=True)
    feats_parts, targets_parts = [], []
    for i, sym in enumerate(("AAA", "BBB")):
        df = _synthetic_ohlcv(seed=10 + i)
        df.to_parquet(raw_dir / f"symbol={sym}.parquet", index=False)
        f = compute_features(df)
        t = compute_targets(df)
        feats_parts.append(pd.DataFrame({"date": df["date"], "symbol": sym, "market": "USD"}).join(
            f.drop(columns=["date"], errors="ignore").reset_index(drop=True)
        ))
        targets_parts.append(pd.DataFrame({
            "date": df["date"], "symbol": sym, "market": "USD",
        }).join(t.reset_index(drop=True)))
    feat_dir = tmp_path / "data" / "features"
    feat_dir.mkdir(parents=True)
    pd.concat(feats_parts, ignore_index=True).to_parquet(feat_dir / "features_USD.parquet", index=False)
    pd.concat(targets_parts, ignore_index=True).to_parquet(feat_dir / "targets_USD.parquet", index=False)

    (tmp_path / "data").mkdir(exist_ok=True)
    catalog = json.loads((BASE / "data" / "metadata_catalog_USD.json").read_text())
    (tmp_path / "data" / "metadata_catalog_USD.json").write_text(json.dumps(catalog))

    monkeypatch.setattr("src.xgb_trainer.BASE_DIR", tmp_path)
    monkeypatch.setattr("src.xgb_trainer.DATA_DIR", tmp_path / "data")
    monkeypatch.setattr("src.feature_engine.RAW_DIR", tmp_path / "raw_ohlcv")
    monkeypatch.setattr("src.feature_engine.FIXTURE_DIR", tmp_path / "no_fixture")
    monkeypatch.setattr("src.run_logging.LOG_DIR", tmp_path / "logs")
    (tmp_path / "logs").mkdir(exist_ok=True)
    return tmp_path, catalog


def test_join_panel_equals_recompute(market_env):
    tmp_path, catalog = market_env
    p_join = build_panel("USD", catalog, allow_fixture=False, min_date=None, recompute_features=False)
    p_rec = build_panel("USD", catalog, allow_fixture=False, min_date=None, recompute_features=True)

    cols = [c for c in p_join.columns if c in p_rec.columns]
    j = p_join.sort_values(["symbol", "date"]).reset_index(drop=True)[cols]
    r = p_rec.sort_values(["symbol", "date"]).reset_index(drop=True)[cols]
    assert len(j) == len(r) > 0
    pd.testing.assert_frame_equal(j, r, check_dtype=False, check_exact=False, rtol=1e-6)


def test_join_fallback_when_parquets_missing(market_env, monkeypatch):
    tmp_path, catalog = market_env
    (tmp_path / "data" / "features" / "features_USD.parquet").unlink()
    panel = build_panel("USD", catalog, allow_fixture=False, min_date=None, recompute_features=False)
    assert len(panel) > 0  # fell back to recompute, still produces a panel
