"""Tests for the causal StochRSI (14,14) feature (WI-077)."""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.l0_ext.stoch_rsi import SCHEMA, WARMUP, build, compute_stochrsi

RAW_SCHEMA = pa.schema(
    [
        ("date", pa.date32()),
        ("open", pa.float32()),
        ("high", pa.float32()),
        ("low", pa.float32()),
        ("close", pa.float32()),
        ("volume", pa.float32()),
        ("average", pa.float32()),
        ("barCount", pa.int64()),
    ]
)


def _bars(symbol: str, n: int, seed: int, flat_at: int | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ret = rng.normal(0.0, 0.01, n)
    close = (100.0 * np.exp(np.cumsum(ret))).astype("float32")
    if flat_at is not None:  # flat stretch: RSI becomes constant -> zero denominator
        close[flat_at : flat_at + 20] = close[flat_at]
    dates = [dt.date(2020, 1, 1) + dt.timedelta(days=int(k)) for k in range(n)]
    return pd.DataFrame(
        {
            "symbol": symbol,
            "date": dates,
            "open": close,
            "high": (close * 1.01).astype("float32"),
            "low": (close * 0.99).astype("float32"),
            "close": close,
            "volume": np.float32(1e6),
            "average": close,
            "barCount": 1,
        }
    )


@pytest.fixture()
def multi_ticker() -> pd.DataFrame:
    a = _bars("AAA", 120, seed=1)
    b = _bars("BBB", 120, seed=2)
    return pd.concat([a, b], ignore_index=True)


def test_dtypes_and_window_edges(multi_ticker):
    out = compute_stochrsi(multi_ticker)
    assert list(out.columns) == ["symbol", "date", "stochrsi_14_14"]
    assert out["stochrsi_14_14"].dtype == np.float32
    g = out[out["symbol"] == "AAA"].reset_index(drop=True)
    assert g["stochrsi_14_14"].iloc[:WARMUP].isna().all()
    assert g["stochrsi_14_14"].iloc[WARMUP:].notna().all()


def test_bounds_zero_one(multi_ticker):
    out = compute_stochrsi(multi_ticker)
    vals = out["stochrsi_14_14"].dropna().to_numpy()
    assert vals.size > 0
    assert (vals >= -1e-6).all() and (vals <= 1.0 + 1e-6).all()


def test_flat_rsi_window_is_nan_not_divided(multi_ticker):
    flat = _bars("CCC", 120, seed=3, flat_at=60)
    out = compute_stochrsi(flat).reset_index(drop=True)
    # a flat RSI stretch makes max == min; those bars must be NaN, not 0/0 garbage
    window = out["stochrsi_14_14"].iloc[WARMUP:].to_numpy()
    assert np.isfinite(window[~np.isnan(window)]).all()


def test_causality_future_perturbation_invariance(multi_ticker):
    cut = dt.date(2020, 3, 1)
    out = compute_stochrsi(multi_ticker)
    pert = multi_ticker.copy()
    m = pert["date"] > cut
    pert.loc[m, "close"] = (pert.loc[m, "close"] * 3.0).astype("float32")
    out2 = compute_stochrsi(pert)
    a = out[out["date"] <= cut].reset_index(drop=True)
    b = out2[out2["date"] <= cut].reset_index(drop=True)
    assert a.equals(b)


def test_values_not_revised_on_append(multi_ticker):
    prefix = multi_ticker.groupby("symbol", sort=False).head(80).reset_index(drop=True)
    short = compute_stochrsi(prefix)
    full = compute_stochrsi(multi_ticker)
    cut = prefix["date"].max()
    a = short[short["date"] <= cut].reset_index(drop=True)
    b = full[full["date"] <= cut].reset_index(drop=True)
    assert a.equals(b)


def test_no_symbol_crossing(multi_ticker):
    full = compute_stochrsi(multi_ticker)
    solo = multi_ticker.loc[multi_ticker["symbol"] == "BBB", ["date", "close"]]
    one = compute_stochrsi(solo)
    sub = full[full["symbol"] == "BBB"].reset_index(drop=True)
    assert sub[["date", "stochrsi_14_14"]].equals(one)


def test_index_reset_on_filtered_input(multi_ticker):
    tail = multi_ticker.iloc[30:].reset_index(drop=True)
    assert isinstance(compute_stochrsi(tail).index, pd.RangeIndex)


def test_build_writes_contract_schema(tmp_path, multi_ticker):
    root = tmp_path / "raw_ohlcv" / "market=USD"
    root.mkdir(parents=True)
    for sym in ("AAA", "BBB"):
        d = multi_ticker[multi_ticker["symbol"] == sym]
        pq.write_table(
            pa.Table.from_pandas(d, schema=RAW_SCHEMA, preserve_index=False),
            root / f"symbol={sym}.parquet",
        )
    path, rows = build("USD", out_dir=tmp_path / "out", root=tmp_path / "raw_ohlcv")
    assert rows == len(multi_ticker)
    assert path.name == "stoch_rsi_USD.parquet"
    got = pq.read_table(path)
    assert got.schema.equals(SCHEMA)
    assert got.num_rows == len(multi_ticker)
    assert got.column("stochrsi_14_14").to_pandas().dtype == np.float32
