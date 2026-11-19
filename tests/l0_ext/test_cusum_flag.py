"""Tests for the causal CUSUM break flag (WI-075)."""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.l0_ext.cusum_flag import WINDOW, build, compute_cusum_flag

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


def _bars(symbol: str, n: int, seed: int, shift_at: int | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ret = rng.normal(0.0, 0.01, n)
    if shift_at is not None:
        ret[shift_at:] += 0.06
    close = (100.0 * np.exp(np.cumsum(ret))).astype("float32")
    dates = [dt.date(2020, 1, 1) + dt.timedelta(days=int(k)) for k in range(n)]
    return pd.DataFrame(
        {
            "symbol": symbol,
            "date": dates,
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": np.float32(1e6),
            "average": close,
            "barCount": 1,
        }
    )


@pytest.fixture()
def multi_ticker() -> pd.DataFrame:
    a = _bars("AAA", 90, seed=1, shift_at=45)
    b = _bars("BBB", 90, seed=2)
    return pd.concat([a, b], ignore_index=True)


def test_dtypes_and_window_edges(multi_ticker):
    out = compute_cusum_flag(multi_ticker)
    assert list(out.columns) == ["symbol", "date", "cusum_flag", "cusum_stat"]
    assert out["cusum_stat"].dtype == np.float32
    assert out["cusum_flag"].dtype == np.int8
    for _, g in out.groupby("symbol"):
        assert g["cusum_stat"].iloc[:WINDOW].isna().all()
        assert g["cusum_stat"].iloc[WINDOW:].notna().all()
        assert set(g["cusum_flag"].iloc[:WINDOW].unique()) == {0}


def test_break_is_detected_and_flag_is_a_state(multi_ticker):
    out = compute_cusum_flag(multi_ticker)
    g = out[out["symbol"] == "AAA"]
    assert g["cusum_flag"].sum() > 0
    hit = g.index[g["cusum_stat"] > 2.0]
    assert len(hit) > 0
    assert (g.loc[hit, "cusum_flag"] == 1).all()
    # flag = 1 if detected at or before bar t -> non-decreasing within a block
    for k in range(WINDOW, len(g), WINDOW):
        block = g["cusum_flag"].iloc[k : k + WINDOW].to_numpy()
        assert (np.diff(block.astype("int8")) >= 0).all()


def test_causality_future_perturbation_invariance(multi_ticker):
    cut = dt.date(2020, 2, 15)
    out = compute_cusum_flag(multi_ticker)
    pert = multi_ticker.copy()
    m = pert["date"] > cut
    pert.loc[m, "close"] = (pert.loc[m, "close"] * 3.0).astype("float32")
    out2 = compute_cusum_flag(pert)
    a = out[out["date"] <= cut].reset_index(drop=True)
    b = out2[out2["date"] <= cut].reset_index(drop=True)
    assert a.equals(b)


def test_flags_are_not_revised_on_append(multi_ticker):
    prefix = multi_ticker.groupby("symbol", sort=False).head(60).reset_index(drop=True)
    short = compute_cusum_flag(prefix)
    full = compute_cusum_flag(multi_ticker)
    cut = prefix["date"].max()
    a = short[short["date"] <= cut].reset_index(drop=True)
    b = full[full["date"] <= cut].reset_index(drop=True)
    assert a.equals(b)


def test_no_symbol_crossing(multi_ticker):
    full = compute_cusum_flag(multi_ticker)
    solo = multi_ticker.loc[multi_ticker["symbol"] == "BBB", ["date", "close"]]
    one = compute_cusum_flag(solo)
    sub = full[full["symbol"] == "BBB"].reset_index(drop=True)
    assert sub[["date", "cusum_flag", "cusum_stat"]].equals(one)


def test_index_reset_on_filtered_input(multi_ticker):
    tail = multi_ticker.iloc[30:].reset_index(drop=True)
    assert isinstance(compute_cusum_flag(tail).index, pd.RangeIndex)


def test_build_writes_contract_schema(tmp_path, multi_ticker):
    root = tmp_path / "raw_ohlcv" / "market=USD"
    root.mkdir(parents=True)
    for sym in ("AAA", "BBB"):
        d = multi_ticker[multi_ticker["symbol"] == sym]
        pq.write_table(pa.Table.from_pandas(d, schema=RAW_SCHEMA, preserve_index=False),
                       root / f"symbol={sym}.parquet")
    path, rows = build("USD", out_dir=tmp_path / "out", root=tmp_path / "raw_ohlcv")
    assert rows == len(multi_ticker)
    got = pq.read_table(path)
    assert got.schema.equals(pa.schema([("symbol", pa.string()), ("date", pa.date32()),
                                        ("cusum_flag", pa.int8()), ("cusum_stat", pa.float32())]))
    assert got.column("cusum_flag").to_pandas().isin([0, 1]).all()
