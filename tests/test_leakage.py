"""Mandatory anti-leakage unit tests (Sprint 2 baseline, run at Gate 1).

Verifies that feature computation at time t is invariant to any future data
perturbation, and that the purged walk-forward split respects the 20-day embargo.
"""

import numpy as np
import pandas as pd
import pytest


def compute_sample_causal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Reference wrapper to test feature_engine causal invariance."""
    out = pd.DataFrame(index=df.index)
    close = df["close"].astype("float64")
    high = df["high"].astype("float64")
    low = df["low"].astype("float64")

    # Trailing 20d Bollinger %B
    sma20 = close.rolling(20, min_periods=20).mean()
    std20 = close.rolling(20, min_periods=20).std(ddof=1)
    out["bb_pct_b_20"] = ((close - (sma20 - 2.0 * std20)) / (4.0 * std20 + 1e-12)).astype("float32")

    # Trailing 20d Wilder ATR
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    out["atr_20"] = tr.ewm(alpha=1.0 / 20.0, min_periods=20, adjust=False).mean().astype("float32")

    return out


def test_future_perturbation_invariance():
    """Mutating t+1..T with +500% price spikes MUST NOT alter any feature at index <= t."""
    rng = np.random.default_rng(42)
    n_bars = 250
    cutoff_t = 200
    dates = pd.date_range("2025-01-01", periods=n_bars, freq="B")
    close = 100.0 * np.exp(np.cumsum(rng.normal(0.0005, 0.015, size=n_bars)))

    df_orig = pd.DataFrame(
        {
            "date": dates,
            "open": close * 0.998,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": rng.integers(100_000, 1_000_000, size=n_bars),
        }
    )

    df_mutated = df_orig.copy()
    # Inject massive future look-ahead spike after cutoff_t
    df_mutated.loc[cutoff_t + 1 :, ["open", "high", "low", "close"]] *= 6.0

    feat_orig = compute_sample_causal_features(df_orig)
    feat_mut = compute_sample_causal_features(df_mutated)

    for col in feat_orig.columns:
        a = feat_orig.loc[:cutoff_t, col].to_numpy()
        b = feat_mut.loc[:cutoff_t, col].to_numpy()
        assert np.allclose(a, b, rtol=1e-6, atol=1e-6, equal_nan=True), (
            f"DATA LEAKAGE DETECTED in feature {col} prior to cutoff {cutoff_t}!"
        )


def test_purged_walk_forward_embargo_gap():
    """For every fold: max(train date) + 20 trading days < min(val date)."""
    from src.xgb_trainer import PurgedWalkForwardSplit

    embargo_td = 20
    uniq = pd.bdate_range("2021-01-01", periods=1000)
    dates = np.repeat(uniq.to_numpy(), 3)  # 3 tickers per date
    pos = {d: i for i, d in enumerate(uniq.to_numpy())}

    folds = list(PurgedWalkForwardSplit(n_splits=5, embargo_td=embargo_td).split(dates))
    assert len(folds) == 5
    for train_idx, val_idx in folds:
        max_train = max(pos[d] for d in dates[train_idx])
        min_val = min(pos[d] for d in dates[val_idx])
        assert max_train + embargo_td < min_val, (
            "Purged Walk-Forward split violated 20-day embargo boundary!"
        )


def test_cross_sectional_rank_isolation():
    """cs_pct ranks at date t depend only on tickers at t and ignore dates > t."""
    from src.stat_metadata import add_cs_percentile

    rng = np.random.default_rng(3)
    dates = pd.bdate_range("2025-01-01", periods=40)
    panel = pd.DataFrame(
        [(d, f"S{i}", rng.normal()) for d in dates for i in range(6)],
        columns=["date", "symbol", "feat"],
    )
    cutoff = dates[25]
    full = add_cs_percentile(panel, ["feat"])
    trunc = add_cs_percentile(panel[panel["date"] <= cutoff], ["feat"])

    a = full.loc[full["date"] <= cutoff, "feat_cs_pct"].to_numpy()
    b = trunc["feat_cs_pct"].to_numpy()
    assert np.array_equal(a, b), "cross-sectional ranks leak information from dates > t"


def test_feature_engine_causal_invariance():
    """The full feature_engine matrix must be invariant to future price spikes."""
    from src.feature_engine import compute_features

    rng = np.random.default_rng(7)
    n_bars = 250
    cutoff_t = 200
    dates = pd.date_range("2025-01-01", periods=n_bars, freq="B")
    close = 100.0 * np.exp(np.cumsum(rng.normal(0.0005, 0.015, size=n_bars)))

    df_orig = pd.DataFrame(
        {
            "date": dates,
            "open": close * 0.998,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": rng.integers(100_000, 1_000_000, size=n_bars),
        }
    )
    df_mut = df_orig.copy()
    df_mut.loc[cutoff_t + 1 :, ["open", "high", "low", "close"]] *= 6.0

    feat_a = compute_features(df_orig)
    feat_b = compute_features(df_mut)
    feat_cols = [c for c in feat_a.columns if c != "date"]

    a = feat_a.loc[:cutoff_t, feat_cols].to_numpy(dtype="float64")
    b = feat_b.loc[:cutoff_t, feat_cols].to_numpy(dtype="float64")
    assert np.allclose(a, b, rtol=1e-5, atol=1e-5, equal_nan=True), (
        "feature_engine leaks future data: a +500% future spike altered features at t <= cutoff"
    )
