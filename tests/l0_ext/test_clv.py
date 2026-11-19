"""Tests for the causal Close Location Value feature (WI-076)."""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.l0_ext.clv import SCHEMA, WINDOW, build, compute_clv

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
    high = (close * 1.01).astype("float32")
    low = (close * 0.99).astype("float32")
    if flat_at is not None:  # zero-range bar: CLV undefined
        high[flat_at] = close[flat_at]
        low[flat_at] = close[flat_at]
    dates = [dt.date(2020, 1, 1) + dt.timedelta(days=int(k)) for k in range(n)]
    return pd.DataFrame(
        {
            "symbol": symbol,
            "date": dates,
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.float32(1e6),
            "average": close,
            "barCount": 1,
        }
    )


@pytest.fixture()
def multi_ticker() -> pd.DataFrame:
    a = _bars("AAA", 90, seed=1)
    b = _bars("BBB", 90, seed=2, flat_at=40)
    return pd.concat([a, b], ignore_index=True)


def test_dtypes_and_window_edges(multi_ticker):
    out = compute_clv(multi_ticker)
    assert list(out.columns) == ["symbol", "date", "clv", "clv_ma14"]
    assert out["clv"].dtype == np.float32
    assert out["clv_ma14"].dtype == np.float32
    # AAA has no zero-range bar, so its rolling mean is NaN only during warmup
    g = out[out["symbol"] == "AAA"].reset_index(drop=True)
    assert g["clv_ma14"].iloc[: WINDOW - 1].isna().all()
    assert g["clv_ma14"].iloc[WINDOW - 1 :].notna().all()


def test_clv_formula_and_bounds(multi_ticker):
    out = compute_clv(multi_ticker)
    g = multi_ticker[multi_ticker["symbol"] == "AAA"].reset_index(drop=True)
    ref = ((g["close"] - g["low"]) - (g["high"] - g["close"])) / (g["high"] - g["low"])
    got = out[out["symbol"] == "AAA"]["clv"].to_numpy()
    assert np.allclose(got, ref.to_numpy(), atol=1e-6)
    assert (np.abs(got) <= 1.0 + 1e-6).all()


def test_zero_range_bar_is_nan_and_propagates(multi_ticker):
    out = compute_clv(multi_ticker)
    g = out[out["symbol"] == "BBB"].reset_index(drop=True)
    assert np.isnan(g["clv"].iloc[40])
    # every rolling window containing bar 40 is NaN
    assert g["clv_ma14"].iloc[40 : 40 + WINDOW].isna().all()
    assert g["clv_ma14"].iloc[40 + WINDOW :].notna().all()


def test_causality_future_perturbation_invariance(multi_ticker):
    cut = dt.date(2020, 2, 15)
    out = compute_clv(multi_ticker)
    pert = multi_ticker.copy()
    m = pert["date"] > cut
    for col in ("high", "low", "close"):
        pert.loc[m, col] = (pert.loc[m, col] * 3.0).astype("float32")
    out2 = compute_clv(pert)
    a = out[out["date"] <= cut].reset_index(drop=True)
    b = out2[out2["date"] <= cut].reset_index(drop=True)
    assert a.equals(b)


def test_no_symbol_crossing(multi_ticker):
    full = compute_clv(multi_ticker)
    solo = multi_ticker.loc[multi_ticker["symbol"] == "BBB", ["date", "high", "low", "close"]]
    one = compute_clv(solo)
    sub = full[full["symbol"] == "BBB"].reset_index(drop=True)
    assert sub[["date", "clv", "clv_ma14"]].equals(one)


def test_index_reset_on_filtered_input(multi_ticker):
    tail = multi_ticker.iloc[30:].reset_index(drop=True)
    assert isinstance(compute_clv(tail).index, pd.RangeIndex)


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
    got = pq.read_table(path)
    assert got.schema.equals(SCHEMA)
    assert got.num_rows == len(multi_ticker)
    assert got.column("clv").to_pandas().dtype == np.float32
