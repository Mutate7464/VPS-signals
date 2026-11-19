"""Tests for L1-BIF trailing swing-level distances (WI-081, design D-029)."""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

from src.l1_bif.bif_boundary import BoundaryViolation, assert_boundary
from src.l1_bif.swing_levels import (
    ATR_WINDOW,
    SWING_WINDOW,
    VALUE_COLS,
    compute_swing_levels,
    write_swing_levels,
)

WARMUP = max(SWING_WINDOW, ATR_WINDOW)
N = 90


def _bars(symbol: str, n: int = N, seed: int = 1, scale: float = 1.0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = (100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.01, n)))).astype("float32")
    dates = [dt.date(2020, 1, 1) + dt.timedelta(days=int(k)) for k in range(n)]
    return pd.DataFrame(
        {
            "symbol": symbol,
            "date": dates,
            "open": close,
            "high": (close * 1.01 * scale).astype("float32"),
            "low": (close * 0.99).astype("float32"),
            "close": close,
            "volume": np.float32(1e6),
            "average": close,
            "barCount": 1,
        }
    )


def _flat_tail_bars(symbol: str, n: int = N, flat_from: int = 30) -> pd.DataFrame:
    """Volatile head, then a constant tail: ``high == low == close``, zero-width."""
    d = _bars(symbol, n=n, seed=7)
    m = np.arange(n) >= flat_from
    c0 = float(d["close"].iloc[flat_from - 1])
    d.loc[m, "close"] = np.float32(c0)
    d.loc[m, "high"] = np.float32(c0)
    d.loc[m, "low"] = np.float32(c0)
    return d


def _expected_atr(g: pd.DataFrame, window: int = ATR_WINDOW) -> pd.Series:
    """Independent restatement of the Wilder ATR definition (float64)."""
    prev = g["close"].astype("float64").shift(1)
    tr = pd.concat(
        [
            g["high"].astype("float64") - g["low"].astype("float64"),
            (g["high"].astype("float64") - prev).abs(),
            (g["low"].astype("float64") - prev).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1.0 / window, min_periods=window, adjust=False).mean()


@pytest.fixture()
def multi_ticker() -> pd.DataFrame:
    return pd.concat(
        [_bars("AAA", seed=1), _bars("BBB", seed=2, scale=1.5)], ignore_index=True
    )


def test_output_columns_dtypes_and_index(multi_ticker):
    out = compute_swing_levels(multi_ticker)
    assert list(out.columns) == ["symbol", "date", *VALUE_COLS]
    for col in VALUE_COLS:
        assert out[col].dtype == np.float32
    assert not pd.api.types.is_float_dtype(out["date"])
    assert isinstance(out.index, pd.RangeIndex)
    assert out["symbol"].tolist() == ["AAA"] * N + ["BBB"] * N
    # the emitted column list must clear the D-029 boundary (never a label)
    assert assert_boundary(list(out.columns)) == list(out.columns)
    with pytest.raises(BoundaryViolation):
        assert_boundary([*VALUE_COLS, "fwd_atr_ret_20"])


def test_window_edges_are_nan(multi_ticker):
    out = compute_swing_levels(multi_ticker)
    for _, g in out.groupby("symbol"):
        assert g[VALUE_COLS].iloc[: WARMUP - 1].isna().all().all()
        assert g[VALUE_COLS].iloc[WARMUP - 1 :].notna().all().all()


def test_distances_are_confirmation_dated_and_atr_normalised(multi_ticker):
    out = compute_swing_levels(multi_ticker)
    g = multi_ticker[multi_ticker["symbol"] == "AAA"].reset_index(drop=True)
    sub = out[out["symbol"] == "AAA"].reset_index(drop=True)
    atr = _expected_atr(g)
    for k in (WARMUP - 1, 40, N - 1):
        hi = g["high"].astype("float64").iloc[k - SWING_WINDOW + 1 : k + 1].max()
        lo = g["low"].astype("float64").iloc[k - SWING_WINDOW + 1 : k + 1].min()
        c = g["close"].astype("float64").iloc[k]
        a = atr.iloc[k]
        assert a > 0
        assert np.isclose(sub["dist_to_swing_hi_atr"].iloc[k], (hi - c) / a, rtol=1e-4, atol=1e-4)
        assert np.isclose(sub["dist_to_swing_lo_atr"].iloc[k], (c - lo) / a, rtol=1e-4, atol=1e-4)
        assert np.isclose(sub["dist_ret50_atr"].iloc[k],
                          (c - (lo + 0.5 * (hi - lo))) / a, rtol=1e-4, atol=1e-4)
        assert np.isclose(sub["dist_ret75_atr"].iloc[k],
                          (c - (lo + 0.75 * (hi - lo))) / a, rtol=1e-4, atol=1e-4)


def test_levels_are_not_backfilled_onto_pivot_bar(multi_ticker):
    """Rows before the first confirmation are NaN even though a pivot exists."""
    out = compute_swing_levels(multi_ticker)
    g = out[out["symbol"] == "AAA"].reset_index(drop=True)
    assert g[VALUE_COLS].iloc[: WARMUP - 1].isna().all().all()


def test_zero_width_range_gives_nan_retrace_not_zero():
    flat_from = 30
    out = compute_swing_levels(_flat_tail_bars("FLT", flat_from=flat_from))
    # only bars whose whole trailing window is flat carry zero-width evidence
    g = out.iloc[flat_from + SWING_WINDOW - 1 :].reset_index(drop=True)
    assert len(g) > 0
    assert g["dist_ret50_atr"].isna().all()
    assert g["dist_ret75_atr"].isna().all()
    # swing distances are still well defined (price == level) -> 0.0, not NaN
    assert (g["dist_to_swing_hi_atr"] == np.float32(0.0)).all()
    assert (g["dist_to_swing_lo_atr"] == np.float32(0.0)).all()


def test_causality_future_perturbation_invariance(multi_ticker):
    cut = dt.date(2020, 2, 15)
    base = compute_swing_levels(multi_ticker)
    pert = multi_ticker.copy()
    m = pert["date"] > cut
    pert.loc[m, "high"] = (pert.loc[m, "high"] * 5.0).astype("float32")
    pert.loc[m, "low"] = (pert.loc[m, "low"] * 0.2).astype("float32")
    pert.loc[m, "close"] = (pert.loc[m, "close"] * 3.0).astype("float32")
    other = compute_swing_levels(pert)
    a = base[base["date"] <= cut].reset_index(drop=True)
    b = other[other["date"] <= cut].reset_index(drop=True)
    assert a.equals(b)


def test_distances_are_not_revised_on_append(multi_ticker):
    prefix = multi_ticker.groupby("symbol", sort=False).head(60).reset_index(drop=True)
    short = compute_swing_levels(prefix)
    full = compute_swing_levels(multi_ticker)
    cut = prefix["date"].max()
    assert short[short["date"] <= cut].reset_index(drop=True).equals(
        full[full["date"] <= cut].reset_index(drop=True)
    )


def test_no_symbol_crossing(multi_ticker):
    loud = multi_ticker.copy()
    m = loud["symbol"] == "AAA"
    loud.loc[m, "high"] = (loud.loc[m, "high"] * 5.0).astype("float32")
    out = compute_swing_levels(loud)
    solo = compute_swing_levels(multi_ticker[multi_ticker["symbol"] == "BBB"])
    sub = out[out["symbol"] == "BBB"].reset_index(drop=True)
    assert sub[["date", *VALUE_COLS]].equals(solo[["date", *VALUE_COLS]])


def test_bad_parameters_rejected(multi_ticker):
    with pytest.raises(ValueError):
        compute_swing_levels(multi_ticker, window=1)
    with pytest.raises(ValueError):
        compute_swing_levels(multi_ticker, atr_window=1)


def test_write_schema_matches_io_contract(multi_ticker, tmp_path):
    out = compute_swing_levels(multi_ticker)
    path = write_swing_levels(out, tmp_path / "swing_levels_USD.parquet")
    schema = pq.read_schema(path)
    assert schema.names == ["symbol", "date", *VALUE_COLS]
    assert str(schema.field("date").type) == "date32[day]"
    for col in VALUE_COLS:
        assert str(schema.field(col).type) == "float"
    assert pq.read_table(path).num_rows == len(out)
