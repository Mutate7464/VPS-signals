"""Regression test: iter_market_symbols must yield a clean 0..n-1 index.

A non-reset index after the `read_from` filter made compute_features (which
inherits df.index) misalign with compute_targets (RangeIndex) in
pd.concat(axis=1), silently truncating the labeled panel to overlapping-index
rows only (the 533,017-row bug, 2026-10-23).
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.feature_engine import iter_market_symbols


def test_iterator_yields_reset_index(tmp_path, monkeypatch):
    n = 400
    dates = pd.bdate_range("2010-01-01", periods=n)
    close = 100.0 * np.exp(np.cumsum(np.random.default_rng(1).normal(0, 0.01, n)))
    df = pd.DataFrame(
        {
            "date": dates,
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": 1e6,
        }
    )
    raw_dir = tmp_path / "raw_ohlcv" / "market=USD"
    raw_dir.mkdir(parents=True)
    df.to_parquet(raw_dir / "symbol=AAA.parquet", index=False)
    monkeypatch.setattr("src.feature_engine.RAW_DIR", tmp_path / "raw_ohlcv")
    monkeypatch.setattr("src.feature_engine.FIXTURE_DIR", tmp_path / "no_fixture")

    symbols = list(iter_market_symbols("USD", min_date="2011-06-01", allow_fixture=False))
    assert len(symbols) == 1
    _, g = symbols[0]
    # rows start at read_from = min_date - 250d (caller trims to min_date),
    # and the index is a clean range
    assert (g["date"] >= pd.Timestamp("2011-06-01") - pd.Timedelta(days=250)).all()
    assert (g.index == range(len(g))).all()
    expected = (df["date"] >= pd.Timestamp("2011-06-01") - pd.Timedelta(days=250)).sum()
    assert len(g) == expected
