"""Tests for the causal Connors RSI feature (WI-078)."""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.l0_ext.connors_rsi import SCHEMA, WARMUP, build, compute_connors_rsi

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
N_BARS = WARMUP + 48


def _bars(symbol: str, n: int, seed: int, flat: bool = False) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    if flat:
        close = np.full(n, 100.0)
    else:
        close = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.01, n)))
    close = close.astype("float32")
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
    a = _bars("AAA", N_BARS, seed=1)
    b = _bars("BBB", N_BARS, seed=2)
    return pd.concat([a, b], ignore_index=True)


def test_dtypes_and_window_edges(multi_ticker):
    out = compute_connors_rsi(multi_ticker)
    assert list(out.columns) == ["symbol", "date", "connors_rsi"]
    assert out["connors_rsi"].dtype == np.float32
    g = out[out["symbol"] == "AAA"].reset_index(drop=True)
    assert g["connors_rsi"].iloc[:WARMUP].isna().all()
    assert g["connors_rsi"].iloc[WARMUP:].notna().all()


def test_bounds_zero_hundred(multi_ticker):
    vals = compute_connors_rsi(multi_ticker)["connors_rsi"].dropna().to_numpy()
    assert vals.size > 0
    assert (vals >= -1e-4).all() and (vals <= 100.0 + 1e-4).all()


def test_flat_market_is_finite_composite():
    # flat: RSI(3)=100, RSI(2) of streak=100, percent-rank of a constant
    # return = 0 -> (100 + 100 + 0) / 3, never NaN-by-division
    out = compute_connors_rsi(_bars("CCC", N_BARS, seed=3, flat=True))
    tail = out["connors_rsi"].iloc[WARMUP:].to_numpy()
    assert np.isfinite(tail).all()
    assert tail == pytest.approx(200.0 / 3.0, rel=1e-5)


def test_causality_future_perturbation_invariance(multi_ticker):
    cut = dt.date(2021, 4, 1)
    out = compute_connors_rsi(multi_ticker)
    pert = multi_ticker.copy()
    m = pert["date"] > cut
    pert.loc[m, "close"] = (pert.loc[m, "close"] * 3.0).astype("float32")
    out2 = compute_connors_rsi(pert)
    a = out[out["date"] <= cut].reset_index(drop=True)
    b = out2[out2["date"] <= cut].reset_index(drop=True)
    assert a.equals(b)
    assert len(a) > 0


def test_values_not_revised_on_append(multi_ticker):
    prefix = multi_ticker.groupby("symbol", sort=False).head(N_BARS - 20)
    prefix = prefix.reset_index(drop=True)
    short = compute_connors_rsi(prefix)
    full = compute_connors_rsi(multi_ticker)
    cut = prefix["date"].max()
    a = short[short["date"] <= cut].reset_index(drop=True)
    b = full[full["date"] <= cut].reset_index(drop=True)
    assert a.equals(b)


def test_no_symbol_crossing(multi_ticker):
    full = compute_connors_rsi(multi_ticker)
    solo = multi_ticker.loc[multi_ticker["symbol"] == "BBB", ["date", "close"]]
    one = compute_connors_rsi(solo)
    sub = full[full["symbol"] == "BBB"].reset_index(drop=True)
    assert sub[["date", "connors_rsi"]].equals(one)


def test_index_reset_on_filtered_input(multi_ticker):
    tail = multi_ticker.iloc[30:].reset_index(drop=True)
    assert isinstance(compute_connors_rsi(tail).index, pd.RangeIndex)


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
    assert path.name == "connors_rsi_USD.parquet"
    got = pq.read_table(path)
    assert got.schema.equals(SCHEMA)
    assert got.num_rows == len(multi_ticker)
    assert got.column("connors_rsi").to_pandas().dtype == np.float32
