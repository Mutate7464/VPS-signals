"""WI-011 Step 2 — point-in-time tests for the trailing condition definitions.

The point of these tests is the causality contract, not the values: a condition
observed at date t must be computable from bars at or before t, and changing any
future bar must leave it bit-identical. They run on synthetic bars only, so they
cost nothing and never touch the CAD parquets.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.feature_engine import _efficiency_ratio
from src.wi011.conditions import (
    ATOMIC_SPECS,
    CONDITION_SPECS,
    CROSS_SPECS,
    add_e5_primitives,
    add_state_columns,
    compute_conditions,
    efficiency_ratio_20,
    rolling_percentile_last,
    trailing_ols_slope_r2,
)
from src.wi011.panel import attach_forward_returns, corwin_schultz_daily_spread

N_BARS = 420


def _synthetic_bars(n: int = N_BARS, seed: int = 11) -> pd.DataFrame:
    """Deterministic OHLCV with drifting vol, a trend leg and a chop leg."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    drift = np.where(t < n // 3, 0.0016, np.where(t < 2 * n // 3, -0.0012, 0.0002))
    vol = np.where(t < n // 2, 0.008, 0.020)
    ret = drift + vol * rng.standard_normal(n)
    close = 40.0 * np.exp(np.cumsum(ret))
    spread = close * np.abs(rng.standard_normal(n)) * 0.006 + 0.02
    high = close + spread
    low = close - spread
    open_ = close * (1.0 + 0.001 * rng.standard_normal(n))
    volume = np.exp(11.0 + 0.5 * rng.standard_normal(n))
    return pd.DataFrame(
        {
            "date": pd.bdate_range("2015-01-02", periods=n),
            "open": open_,
            "high": np.maximum.reduce([high, open_, close]),
            "low": np.minimum.reduce([low, open_, close]),
            "close": close,
            "volume": volume,
        }
    )


def _state_and_conds(df: pd.DataFrame) -> pd.DataFrame:
    state = add_state_columns(df)
    conds = compute_conditions(state)
    return pd.concat([state, conds], axis=1)


def _state_columns(state: pd.DataFrame) -> list[str]:
    return [
        "mom_12_1",
        "rev_1m",
        "vol_20",
        "amihud_20",
        "log_dollar_vol_20",
        "atr_pct_20",
        "er_20",
        "ols_slope_20",
        "ols_r2_20",
        "ma_50",
        "ch52_pos",
        "atr_pct_pctile_252",
        "amihud_pctile_252",
        "dollarvol_pctile_252",
    ]


def _assert_frames_equal_on_rows(a: pd.DataFrame, b: pd.DataFrame, upto: int, columns: list[str]) -> None:
    pa = a.loc[: upto - 1, columns]
    pb = b.loc[: upto - 1, columns]
    for c in columns:
        va = pa[c].to_numpy(dtype="float64")
        vb = pb[c].to_numpy(dtype="float64")
        assert np.allclose(va, vb, rtol=0.0, atol=0.0, equal_nan=True), (
            f"column {c!r} differs in rows < {upto} (max abs diff "
            f"{np.nanmax(np.abs(va - vb)) if np.isfinite(va - vb).any() else float('nan')})"
        )


# --------------------------------------------------------------------------- #
# Point-in-time / no-lookahead
# --------------------------------------------------------------------------- #
def test_future_perturbation_leaves_earlier_conditions_unchanged():
    """Row t is a pure function of bars <= t: wrecking the future cannot move it."""
    df = _synthetic_bars()
    base = _state_and_conds(df)
    cut = 300

    perturbed = df.copy()
    for col in ("open", "high", "low", "close"):
        perturbed.loc[cut:, col] = perturbed.loc[cut:, col] * 1.37
    perturbed.loc[cut:, "volume"] = perturbed.loc[cut:, "volume"] * 0.21

    after = _state_and_conds(perturbed)
    cols = _state_columns(base) + [s.name for s in CONDITION_SPECS]
    _assert_frames_equal_on_rows(base, after, cut, cols)


def test_truncated_recompute_matches_the_live_row():
    """Computing on data up to t only reproduces exactly the row computed at t."""
    df = _synthetic_bars()
    full = _state_and_conds(df)
    cut = 320
    trunc = _state_and_conds(df.iloc[:cut].reset_index(drop=True))
    cols = _state_columns(full) + [s.name for s in CONDITION_SPECS]
    _assert_frames_equal_on_rows(full, trunc, cut, cols)


def test_last_bar_condition_depends_only_on_history():
    """The final bar still has a defined condition set — nothing needs t+1."""
    df = _synthetic_bars()
    state = add_state_columns(df)
    conds = compute_conditions(state)
    assert np.isfinite(state["atr_pct_20"].iloc[-1])
    for name in ("trend_chop", "above_ma_50", "ch52_high", "ch52_low", "mom_pos", "rev1m_neg"):
        assert name in conds.columns, name
        assert np.isfinite(conds[name].iloc[-1]), f"{name} undefined on the last bar"


def test_forward_labels_do_change_when_future_changes():
    """Sanity guard: the harness detects future dependence when it exists."""
    df = _synthetic_bars()
    a = attach_forward_returns(add_state_columns(df))
    perturbed = df.copy()
    perturbed.loc[300:, "close"] = perturbed.loc[300:, "close"] * 1.37
    b = attach_forward_returns(add_state_columns(perturbed))
    assert not np.allclose(
        a["fwd_ret_20"].to_numpy(dtype="float64")[:299],
        b["fwd_ret_20"].to_numpy(dtype="float64")[:299],
        equal_nan=True,
    )


def test_corwin_schultz_stored_spread_is_lagged_and_causal():
    """The stored CS spread at t comes from bars (t-1, t) — never bar t+1."""
    df = _synthetic_bars()
    full = corwin_schultz_daily_spread(df["high"], df["low"])
    lagged_full = np.concatenate([[np.nan], full[:-1]])
    cut = 320
    trunc = corwin_schultz_daily_spread(df["high"].iloc[:cut], df["low"].iloc[:cut])
    lagged_trunc = np.concatenate([[np.nan], trunc[:-1]])
    assert np.allclose(lagged_full[: cut - 1], lagged_trunc[: cut - 1], equal_nan=True)


# --------------------------------------------------------------------------- #
# Warm-up / dtype / vocabulary
# --------------------------------------------------------------------------- #
def test_conditions_are_float32_and_three_valued():
    conds = compute_conditions(add_state_columns(_synthetic_bars()))
    assert all(str(d) == "float32" for d in conds.dtypes), conds.dtypes.to_dict()
    vals = np.unique(conds.to_numpy(dtype="float64"))
    finite = vals[np.isfinite(vals)]
    assert set(np.round(finite, 6)).issubset({0.0, 1.0}), finite


def test_warmup_rows_are_nan_not_zero():
    """Percentile-based conditions are *undefined* before a full trailing window."""
    conds = compute_conditions(add_state_columns(_synthetic_bars()))
    for name in ("vol_low", "vol_high", "liq_illiquid", "liq_liquid", "dollarvol_high"):
        head = conds[name].to_numpy(dtype="float64")[:200]
        assert np.isnan(head).all(), f"{name} should be undefined for the first 200 bars"
    # NaN must never be silently read as "does not fire".
    assert (conds["vol_high"].to_numpy(dtype="float64")[:200] != 0.0).all()


def test_condition_vocabulary_matches_declared_specs():
    conds = compute_conditions(add_state_columns(_synthetic_bars()))
    assert list(conds.columns) == [s.name for s in CONDITION_SPECS]
    assert len(ATOMIC_SPECS) == 18
    assert len(CROSS_SPECS) == 8
    assert {s.family for s in CONDITION_SPECS} == {"trend", "volatility", "liquidity", "position", "cross"}


def test_indicator_subset_adds_two_conditions_per_indicator():
    state = add_state_columns(_synthetic_bars())
    pct = pd.Series(rolling_percentile_last(state["er_20"].to_numpy()))
    conds = compute_conditions(state, {"kama_er_20": pct})
    assert "ind_kama_er_20_low" in conds.columns
    assert "ind_kama_er_20_high" in conds.columns
    assert len(conds.columns) == len(CONDITION_SPECS) + 2


# --------------------------------------------------------------------------- #
# Primitive fidelity
# --------------------------------------------------------------------------- #
def test_efficiency_ratio_matches_feature_engine():
    close = pd.Series(_synthetic_bars()["close"])
    mine = efficiency_ratio_20(close)
    theirs = _efficiency_ratio(close, 20)
    assert np.allclose(mine.to_numpy(), theirs.to_numpy(), rtol=0, atol=0, equal_nan=True)


def test_e5_primitives_match_reference_formulas():
    df = _synthetic_bars()
    out = add_e5_primitives(df)
    close = df["close"].astype("float64")
    ret = close.pct_change()
    dollar_vol = close * df["volume"].astype("float64") + 1e-12
    assert np.allclose(out["mom_12_1"], close.shift(21) / close.shift(252) - 1.0, equal_nan=True)
    assert np.allclose(out["rev_1m"], close / close.shift(21) - 1.0, equal_nan=True)
    assert np.allclose(out["vol_20"], ret.rolling(20, min_periods=20).std(ddof=1), equal_nan=True)
    assert np.allclose(
        out["amihud_20"], (ret.abs() / dollar_vol).rolling(20, min_periods=20).mean(), equal_nan=True
    )
    assert np.allclose(
        out["log_dollar_vol_20"], np.log(dollar_vol).rolling(20, min_periods=20).mean(), equal_nan=True
    )


def test_trailing_ols_recovers_a_known_slope_and_is_causal():
    n, w = 300, 20
    x = np.arange(n, dtype="float64")
    logp = 0.004 * x + 0.05 * np.sin(x / 7.0)
    slope, r2 = trailing_ols_slope_r2(logp, w)
    assert np.isnan(slope[: w - 1]).all()
    assert slope[w - 1] == pytest.approx((logp[:w] - logp[:w].mean()) @ (np.arange(w) - (w - 1) / 2) / (
        ((np.arange(w) - (w - 1) / 2) ** 2).sum()
    ))
    assert (r2[w - 1 :] <= 1.0 + 1e-12).all()
    # causality: extending the series cannot change an earlier fit
    slope2, r2b = trailing_ols_slope_r2(np.concatenate([logp, np.linspace(9, 1, 40)]), w)
    assert np.allclose(slope[:n], slope2[:n], equal_nan=True)
    assert np.allclose(r2[:n], r2b[:n], equal_nan=True)


def test_rolling_percentile_is_bounded_and_ignores_the_future():
    a = np.arange(300, dtype="float64")
    pct = rolling_percentile_last(a, window=100, min_periods=50)
    assert np.isnan(pct[:99]).all()
    assert pct[99] == pytest.approx(1.0)
    assert (pct[99:] >= 1.0 / 100.0 - 1e-12).all() and (pct[99:] <= 1.0).all()
    b = np.concatenate([a, np.full(50, -1e6)])
    pct_b = rolling_percentile_last(b, window=100, min_periods=50)
    assert np.allclose(pct, pct_b[:300], equal_nan=True)


def test_trend_conditions_fire_on_a_clean_ramp():
    n = 300
    close = 20.0 * np.exp(0.002 * np.arange(n))
    df = pd.DataFrame(
        {
            "date": pd.bdate_range("2015-01-02", periods=n),
            "open": close,
            "high": close * 1.001,
            "low": close * 0.999,
            "close": close,
            "volume": np.full(n, 1e6),
        }
    )
    conds = compute_conditions(add_state_columns(df))
    tail = slice(60, None)
    assert conds["trend_up"].to_numpy(dtype="float64")[tail].mean() == pytest.approx(1.0, abs=1e-12)
    assert np.nansum(conds["trend_down"].to_numpy(dtype="float64")) == 0.0
    assert conds["above_ma_50"].to_numpy(dtype="float64")[60:].mean() == pytest.approx(1.0, abs=1e-12)
    assert conds["mom_pos"].to_numpy(dtype="float64")[260:].mean() == pytest.approx(1.0, abs=1e-12)


def test_cross_conditions_are_conjunctions_with_nan_propagation():
    conds = compute_conditions(add_state_columns(_synthetic_bars()))
    up = conds["trend_up"].to_numpy(dtype="float64")
    vh = conds["vol_high"].to_numpy(dtype="float64")
    cross = conds["trend_up_vol_high"].to_numpy(dtype="float64")
    both_finite = np.isfinite(up) & np.isfinite(vh)
    assert np.array_equal(np.isfinite(cross), both_finite)
    assert np.allclose(cross[both_finite], (up[both_finite] * vh[both_finite]), equal_nan=True)
    assert np.isnan(cross[~both_finite]).all()