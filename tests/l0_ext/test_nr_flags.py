"""WI-074 tests: NR4/NR7 causality, dtype, window edges, multi-ticker grouping."""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.l0_ext.nr_flags import build, compute_nr_flags

# AAA ranges: known-min positions for hand-computed expectations.
AAA_RANGES = [5.0, 4.0, 3.0, 2.0, 10.0, 9.0, 8.0, 1.0]
BBB_RANGES = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
DATES = [dt.date(2024, 1, 1) + dt.timedelta(days=i) for i in range(8)]


def _bars(symbol: str, ranges: list[float], offset: float = 0.0) -> pd.DataFrame:
    low = np.full(len(ranges), 100.0 + offset, dtype="float32")
    high = (low + np.asarray(ranges, dtype="float32")).astype("float32")
    return pd.DataFrame(
        {
            "symbol": symbol,
            "date": DATES,
            "open": low,
            "high": high,
            "low": low,
            "close": high,
            "volume": np.full(len(ranges), 1e5, dtype="float32"),
        }
    )


@pytest.fixture()
def multi_ticker() -> pd.DataFrame:
    return pd.concat(
        [_bars("AAA", AAA_RANGES), _bars("BBB", BBB_RANGES, offset=7.0)],
        ignore_index=True,
    )


def test_flags_are_float32(multi_ticker):
    out = compute_nr_flags(multi_ticker)
    assert out["nr4"].dtype == np.float32
    assert out["nr7"].dtype == np.float32


def test_window_edges_are_nan(multi_ticker):
    out = compute_nr_flags(multi_ticker)
    aaa = out[out["symbol"] == "AAA"].reset_index(drop=True)
    assert aaa["nr4"].iloc[:3].isna().all()
    assert aaa["nr7"].iloc[:6].isna().all()
    assert not aaa["nr4"].iloc[3:].isna().any()
    assert not aaa["nr7"].iloc[6:].isna().any()


def test_expected_values_and_no_symbol_crossing(multi_ticker):
    out = compute_nr_flags(multi_ticker)
    aaa = out[out["symbol"] == "AAA"].reset_index(drop=True)
    bbb = out[out["symbol"] == "BBB"].reset_index(drop=True)
    assert aaa["nr4"].iloc[3:].tolist() == [1.0, 0.0, 0.0, 0.0, 1.0]
    assert aaa["nr7"].iloc[6:].tolist() == [0.0, 1.0]
    # BBB is monotonically widening: never narrowest of the trailing window.
    assert bbb["nr4"].iloc[3:].tolist() == [0.0] * 5
    assert bbb["nr7"].iloc[6:].tolist() == [0.0, 0.0]
    # AAA's last-bar flag must not leak into BBB (grouping, not a global roll).
    assert bbb["nr7"].iloc[-1] == 0.0


def test_causality_future_perturbation_invariance(multi_ticker):
    base = compute_nr_flags(multi_ticker)
    perturbed = multi_ticker.copy()
    cut = 5  # first perturbed bar index
    mask = (perturbed["symbol"] == "AAA") & (perturbed.index >= cut)
    perturbed.loc[mask, "high"] = perturbed.loc[mask, "high"] + 1000.0
    after = compute_nr_flags(perturbed)
    for sym in ("AAA", "BBB"):
        b = base[base["symbol"] == sym].reset_index(drop=True)
        a = after[after["symbol"] == sym].reset_index(drop=True)
        for col in ("nr4", "nr7"):
            np.testing.assert_array_equal(
                b[col].iloc[:cut].to_numpy(), a[col].iloc[:cut].to_numpy()
            )


def test_build_writes_contract_schema(tmp_path):
    root = tmp_path / "raw_ohlcv" / "market=USD"
    root.mkdir(parents=True)
    for sym, ranges in (("AAA", AAA_RANGES), ("BBB", BBB_RANGES)):
        bars = _bars(sym, ranges)
        pq.write_table(
            pa.table(
                {
                    "date": pa.array(bars["date"].tolist(), type=pa.date32()),
                    "open": pa.array(bars["open"], type=pa.float32()),
                    "high": pa.array(bars["high"], type=pa.float32()),
                    "low": pa.array(bars["low"], type=pa.float32()),
                    "close": pa.array(bars["close"], type=pa.float32()),
                    "volume": pa.array(bars["volume"], type=pa.float32()),
                    "average": pa.array(bars["close"], type=pa.float32()),
                    "barCount": pa.array(np.ones(len(ranges), dtype="int64")),
                }
            ),
            root / f"symbol={sym}.parquet",
        )
    path, rows = build("USD", out_dir=tmp_path / "out", limit=10, root=tmp_path / "raw_ohlcv")
    assert path.name == "nr_flags_USD.parquet"
    assert rows == 16
    schema = pq.read_schema(path)
    assert schema.names == ["symbol", "date", "nr4", "nr7"]
    assert schema.field("date").type == pa.date32()
    assert schema.field("nr4").type == pa.float32()
    assert schema.field("nr7").type == pa.float32()
    tbl = pq.read_table(path)
    assert tbl.column("symbol").to_pylist() == ["AAA"] * 8 + ["BBB"] * 8
