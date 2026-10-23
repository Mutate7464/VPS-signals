"""Tests for loader changes (Step 3): quarantine filter, date dtype, fixture guard, iterator."""
from __future__ import annotations

import csv
import datetime as dt
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.feature_engine import (
    FixtureFallbackError,
    iter_market_symbols,
    load_quarantine,
    load_market_frame,
)
from src.run_logging import LOG_DIR


def _write_mini_parquet(dir_path: Path, symbol: str, market: str, start_date: dt.date, n_rows: int, close: float = 100.0):
    """Write a tiny parquet file simulating real OHLCV data."""
    import pandas as pd
    market_dir = dir_path / f"market={market}"
    market_dir.mkdir(parents=True, exist_ok=True)
    dates = pd.date_range(start=start_date, periods=n_rows, freq="D")
    table = pa.table({
        "date": pa.array([d.date() for d in dates], type=pa.date32()),
        "open": pa.array([float(close)] * n_rows, type=pa.float64()),
        "high": pa.array([float(close)] * n_rows, type=pa.float64()),
        "low": pa.array([float(close)] * n_rows, type=pa.float64()),
        "close": pa.array([float(close)] * n_rows, type=pa.float64()),
        "volume": pa.array([1000.0] * n_rows, type=pa.float64()),
        "average": pa.array([float(close)] * n_rows, type=pa.float64()),
        "barCount": pa.array([1] * n_rows, type=pa.int64()),
    })
    pq.write_table(table, market_dir / f"symbol={symbol}.parquet")


def _write_dead_letter(base: Path, lines: list[dict]):
    """Write a dead_letter_tickers.csv in `base/data/`."""
    d = base / "data"
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "dead_letter_tickers.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp_utc", "symbol", "market", "sprint", "reason"])
        w.writeheader()
        for d2 in lines:
            w.writerow(d2)


# --------------------------------------------------------------------------- #
# quarantine
# --------------------------------------------------------------------------- #
def test_load_quarantine_empty(tmp_path, monkeypatch):
    monkeypatch.setattr("src.feature_engine.BASE_DIR", tmp_path)
    assert load_quarantine("USD") == set()

def test_load_quarantine_filters(tmp_path, monkeypatch):
    monkeypatch.setattr("src.feature_engine.BASE_DIR", tmp_path)
    _write_dead_letter(tmp_path, [
        {"timestamp_utc": "", "symbol": "AAPL", "market": "USD", "sprint": "1", "reason": "CB-01"},
        {"timestamp_utc": "", "symbol": "RY", "market": "CAD", "sprint": "1", "reason": "CB-01"},
        {"timestamp_utc": "", "symbol": "MSFT", "market": "USD", "sprint": "1", "reason": "CB-02"},
    ])
    assert load_quarantine("USD") == {"AAPL", "MSFT"}
    assert load_quarantine("CAD") == {"RY"}
    assert load_quarantine("EUR") == set()


# --------------------------------------------------------------------------- #
# iter_market_symbols
# --------------------------------------------------------------------------- #
def test_iter_symbols_dtype_and_filter(tmp_path, monkeypatch):
    """Iterator yields datetime64 dates, skips quarantine and <125-row tickers."""
    monkeypatch.setattr("src.feature_engine.RAW_DIR", tmp_path)
    monkeypatch.setattr("src.feature_engine.BASE_DIR", tmp_path)
    _write_mini_parquet(tmp_path, "AAPL", "USD", dt.date(2024, 1, 1), 199, 150.0)
    _write_mini_parquet(tmp_path, "BAD", "USD", dt.date(2024, 1, 1), 1, 10.0)
    _write_mini_parquet(tmp_path, "MSFT", "USD", dt.date(2024, 1, 1), 199, 300.0)
    # quarantine AAPL
    _write_dead_letter(tmp_path, [
        {"timestamp_utc": "", "symbol": "AAPL", "market": "USD", "sprint": "1", "reason": "test"},
    ])

    symbols = []
    for sym, df in iter_market_symbols("USD"):
        symbols.append(sym)
        assert df["date"].dtype == "datetime64[ns]"
        assert len(df) >= 125

    assert symbols == ["MSFT"]


def test_fixture_fallback_raises(tmp_path, monkeypatch):
    """When real dir is empty and allow_fixture=False, raise."""
    monkeypatch.setattr("src.feature_engine.RAW_DIR", tmp_path / "nonexistent")
    with pytest.raises(FixtureFallbackError, match="fixture fallback is disallowed"):
        list(iter_market_symbols("USD", allow_fixture=False))


def test_fixture_fallback_ok(tmp_path, monkeypatch):
    """When allow_fixture=True, use fixture dir."""
    monkeypatch.setattr("src.feature_engine.RAW_DIR", tmp_path / "nonexistent")
    fix_dir = tmp_path / "fixture"
    monkeypatch.setattr("src.feature_engine.FIXTURE_DIR", fix_dir)
    _write_mini_parquet(fix_dir, "FIX1", "USD", dt.date(2024, 1, 1), 199, 100.0)
    # need to avoid quarantine check
    symbols = []
    for sym, df in iter_market_symbols("USD", allow_fixture=True):
        symbols.append(sym)
    assert symbols == ["FIX1"]


def test_iter_symbols_min_date(tmp_path, monkeypatch):
    """min_date trimming: data read from min_date-250d; output includes warmup dates."""
    monkeypatch.setattr("src.feature_engine.RAW_DIR", tmp_path)
    _write_mini_parquet(tmp_path, "AAPL", "USD", dt.date(2024, 1, 1), 365, 150.0)
    for sym, df in iter_market_symbols("USD", min_date="2024-09-01"):
        # Data should include dates back to ~2023-12-26 (~250d before 2024-09-01)
        assert df["date"].min() <= pd.Timestamp("2024-09-01")
        assert df["date"].min() >= pd.Timestamp("2023-12-01")
        # Should still have >= 125 rows
        assert len(df) >= 125
        assert df["date"].dtype == "datetime64[ns]"


# --------------------------------------------------------------------------- #
# load_market_frame legacy
# --------------------------------------------------------------------------- #
def test_load_market_frame_legacy_works(tmp_path, monkeypatch):
    """Legacy load_market_frame still works with fixture data."""
    monkeypatch.setattr("src.feature_engine.RAW_DIR", tmp_path / "nonexistent")
    fix_dir = tmp_path / "fixture"
    monkeypatch.setattr("src.feature_engine.FIXTURE_DIR", fix_dir)
    _write_mini_parquet(fix_dir, "T1", "CAD", dt.date(2024, 1, 1), 199, 50.0)
    df = load_market_frame("CAD")
    assert len(df) == 199
    assert df["symbol"].iloc[0] == "T1"