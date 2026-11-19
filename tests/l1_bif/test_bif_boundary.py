"""Tests for the L1 bifurcation boundary (WI-080, design D-029)."""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pytest

from src.l1_bif.bif_boundary import (
    WINDOW,
    BoundaryViolation,
    assert_boundary,
    concat_frames,
    is_expost_label,
    is_model_output,
    label_only_columns,
    to_float32,
    trailing_level,
)

RCOL = "retrace_50"
LEVELS = ["level_high", "level_low", RCOL]


def _bars(symbol: str, n: int = 90, seed: int = 1, scale: float = 1.0) -> pd.DataFrame:
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


@pytest.fixture()
def multi_ticker() -> pd.DataFrame:
    return pd.concat([_bars("AAA", seed=1), _bars("BBB", seed=2, scale=1.5)],
                     ignore_index=True)


def test_boundary_returns_validated_feature_list():
    cols = ["close", "atr", "state", "level_high", RCOL]
    assert assert_boundary(cols) == cols
    assert assert_boundary([]) == []


@pytest.mark.parametrize(
    "col",
    ["mfe", "mae", "mfe_mae_cont", "capture_eff", "fwd_vol", "fwd_atr_ret_20",
     "y_20d_high", "label_up_h20"],
)
def test_expost_label_names_are_detected(col):
    assert is_expost_label(col)
    with pytest.raises(BoundaryViolation) as err:
        assert_boundary(["close", col])
    assert col in str(err.value)


def test_causal_names_are_not_expost():
    for col in ("close", "atr", "kama_er_15", "level_high", "retrace_50", "rvol_pctile_20d"):
        assert not is_expost_label(col)
        assert not is_model_output(col)
    assert is_model_output("p_y_20d_high") and is_model_output("fold_y_15d_low")
    avec = ["close", "p_y_20d_high", "fwd_atr_ret_15", "mae"]
    assert label_only_columns(avec) == ["p_y_20d_high", "fwd_atr_ret_15", "mae"]
    with pytest.raises(BoundaryViolation):
        assert_boundary(avec)


def test_dtypes_are_float32_with_keys_preserved(multi_ticker):
    out = trailing_level(multi_ticker)
    assert list(out.columns) == ["symbol", "date", "level_high", "level_low", RCOL]
    for col in LEVELS:
        assert out[col].dtype == np.float32
    assert not pd.api.types.is_float_dtype(out["date"])
    assert pd.api.types.is_float_dtype(to_float32(multi_ticker)["high"])


def test_window_edges_are_nan(multi_ticker):
    out = trailing_level(multi_ticker)
    for _, g in out.groupby("symbol"):
        assert g[LEVELS].iloc[: WINDOW - 1].isna().all().all()
        assert g[LEVELS].iloc[WINDOW - 1 :].notna().all().all()


def test_level_is_confirmation_dated_not_backfilled(multi_ticker):
    out = trailing_level(multi_ticker)
    g = multi_ticker[multi_ticker["symbol"] == "AAA"].reset_index(drop=True)
    sub = out[out["symbol"] == "AAA"].reset_index(drop=True)
    for k in (WINDOW - 1, 40, len(g) - 1):
        hi = g["high"].iloc[k - WINDOW + 1 : k + 1].max()
        lo = g["low"].iloc[k - WINDOW + 1 : k + 1].min()
        assert sub["level_high"].iloc[k] == np.float32(hi)
        assert sub["level_low"].iloc[k] == np.float32(lo)
        assert np.isclose(sub[RCOL].iloc[k], np.float32(lo + 0.5 * (hi - lo)))


def test_causality_future_perturbation_invariance(multi_ticker):
    cut = dt.date(2020, 2, 15)
    base = trailing_level(multi_ticker)
    pert = multi_ticker.copy()
    m = pert["date"] > cut
    pert.loc[m, "high"] = (pert.loc[m, "high"] * 5.0).astype("float32")
    pert.loc[m, "low"] = (pert.loc[m, "low"] * 0.2).astype("float32")
    other = trailing_level(pert)
    a = base[base["date"] <= cut].reset_index(drop=True)
    b = other[other["date"] <= cut].reset_index(drop=True)
    assert a.equals(b)


def test_levels_are_not_revised_on_append(multi_ticker):
    prefix = multi_ticker.groupby("symbol", sort=False).head(60).reset_index(drop=True)
    short = trailing_level(prefix)
    full = trailing_level(multi_ticker)
    cut = prefix["date"].max()
    a = short[short["date"] <= cut].reset_index(drop=True)
    b = full[full["date"] <= cut].reset_index(drop=True)
    assert a.equals(b)


def test_no_symbol_crossing(multi_ticker):
    loud = multi_ticker.copy()
    m = loud["symbol"] == "AAA"
    loud.loc[m, "high"] = (loud.loc[m, "high"] * 5.0).astype("float32")
    out = trailing_level(loud)
    solo = trailing_level(multi_ticker[multi_ticker["symbol"] == "BBB"])
    sub = out[out["symbol"] == "BBB"].reset_index(drop=True)
    assert sub[["date", *LEVELS]].equals(solo[["date", *LEVELS]])


def test_index_reset_before_concat(multi_ticker):
    out = trailing_level(multi_ticker)
    assert isinstance(out.index, pd.RangeIndex)
    tail = multi_ticker.iloc[30:].reset_index(drop=True)
    assert isinstance(trailing_level(tail).index, pd.RangeIndex)
    a = _bars("AAA", 5, seed=3).iloc[2:]
    b = _bars("BBB", 5, seed=4).iloc[3:]
    cat = concat_frames([a, b])
    assert isinstance(cat.index, pd.RangeIndex)
    assert len(cat) == 5
    with pytest.raises(ValueError):
        concat_frames([])


def test_bad_parameters_rejected(multi_ticker):
    with pytest.raises(ValueError):
        trailing_level(multi_ticker, window=1)
    with pytest.raises(ValueError):
        trailing_level(multi_ticker, retrace=1.0)
