"""Tests for the rolling failed-swing-signal count (WI-079)."""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.l0_ext.fail_count import (
    HORIZON,
    SWING_WINDOW,
    WINDOW,
    build,
    compute_fail_count,
    fail_count_col,
)

COL = fail_count_col()
WARMUP = (SWING_WINDOW - 1) + HORIZON  # first bar whose outcome can resolve
FIRST_OBS = WARMUP + WINDOW - 1  # first bar with a full, fully-observed window

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


def _bars(symbol: str, n: int = 200, dip_at: int = 60) -> pd.DataFrame:
    """Flat tape, then a V-dip (at_bottom) followed by a stop-through crash.

    ``at_bottom`` signals confirm every 10 bars (20, 30, 40, 50, 60). The dip at
    bar 60 stops the signals at bars 40 and 50 (resolving at 60 and 70), the
    crash stops the signal at bar 60 (resolving at 80); 20/30 survive their
    horizon. The tail never touches a barrier again.
    """
    close = np.full(n, 100.0)
    high = np.full(n, 100.1)
    low = np.full(n, 99.9)
    close[dip_at] = 95.0
    low[dip_at] = 94.0
    crash = slice(dip_at + 1, dip_at + 11)
    close[crash] = 90.0
    high[dip_at + 1 :] = 90.5
    low[dip_at + 1 :] = 88.0
    close[dip_at + 11 :] = 90.0
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
    return pd.concat([_bars("AAA"), _bars("BBB", dip_at=80)], ignore_index=True)


def test_dtypes_columns_and_window_edges(multi_ticker):
    out = compute_fail_count(multi_ticker)
    assert list(out.columns) == ["symbol", "date", COL]
    assert out[COL].dtype == np.float32
    for _, g in out.groupby("symbol"):
        g = g.reset_index(drop=True)
        assert g[COL].iloc[:FIRST_OBS].isna().all()
        assert g[COL].iloc[FIRST_OBS:].notna().all()
        assert (g[COL].iloc[FIRST_OBS:] >= 0).all()


def test_failure_counted_only_after_outcome_resolves():
    bars = _bars("AAA")
    out = compute_fail_count(bars)
    assert out[COL].iloc[59] == 0.0  # nothing resolved yet
    assert out[COL].iloc[60] == 1.0  # signal at bar 40 resolves at 40 + HORIZON
    assert out[COL].iloc[70] == 2.0  # signal at bar 50 resolves at 50 + HORIZON
    assert out[COL].iloc[80] == 2.0  # signal at bar 60 replaces the bar-40 one
    assert out[COL].iloc[99] == 1.0  # only the bar-60 failure is still in window
    assert out[COL].iloc[100] == 0.0  # all three aged out of the 20-bar window
    # the resolution bar itself is the first bar that can show the failure
    truncated = compute_fail_count(bars.iloc[:60].reset_index(drop=True))
    assert truncated[COL].iloc[59] == out[COL].iloc[59] == 0.0


def test_causality_future_perturbation_invariance():
    bars = _bars("AAA")
    cut = bars["date"].iloc[150]
    pert = bars.copy()
    m = pert["date"] > cut
    for c in ("high", "low", "close"):
        pert.loc[m, c] = (pert.loc[m, c] * 3.0).astype("float32")
    a = compute_fail_count(bars)
    b = compute_fail_count(pert)
    assert a[a["date"] <= cut].reset_index(drop=True).equals(
        b[b["date"] <= cut].reset_index(drop=True)
    )


def test_values_not_revised_when_future_is_appended():
    bars = _bars("AAA")
    prefix = bars.iloc[:150].reset_index(drop=True)
    short = compute_fail_count(prefix)
    full = compute_fail_count(bars)
    cut = prefix["date"].max()
    assert short.reset_index(drop=True).equals(
        full[full["date"] <= cut].reset_index(drop=True)
    )


def test_no_symbol_crossing(multi_ticker):
    full = compute_fail_count(multi_ticker)
    solo = multi_ticker[multi_ticker["symbol"] == "BBB"]
    one = compute_fail_count(solo)
    sub = full[full["symbol"] == "BBB"].reset_index(drop=True)
    assert sub[["date", COL]].equals(one[["date", COL]])


def test_index_reset_on_filtered_input(multi_ticker):
    tail = multi_ticker.iloc[30:].reset_index(drop=True)
    assert isinstance(compute_fail_count(tail).index, pd.RangeIndex)


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
    assert got.schema.equals(
        pa.schema([("symbol", pa.string()), ("date", pa.date32()), (COL, pa.int16())])
    )
    vals = got.column(COL).to_pandas()
    assert vals.isna().any()  # window edges stay undefined
    assert (vals.dropna() >= 0).all()
