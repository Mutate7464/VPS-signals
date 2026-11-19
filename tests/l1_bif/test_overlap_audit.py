"""Tests for the WI-082 swing-overlap audit (audit-only; no in-repo writes)."""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pytest

from src.l1_bif.overlap_audit import (
    audit_overlap,
    audit_symbol,
    prepare_frame,
    swing_events,
)
from src.swing_bsh.events import SWING_WINDOW

WINDOW = 4
GAP = 2
HOLD = 3


def _frame(symbol: str, low, high, close=None) -> pd.DataFrame:
    n = len(low)
    close = list(close) if close is not None else list(high)
    dates = [dt.date(2020, 1, 1) + dt.timedelta(days=k) for k in range(n)]
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


def _designed() -> pd.DataFrame:
    """Hand-computed case: trailing window 4, same-side gap 2, hold 3 bars."""
    low = [5, 4, 3, 2, 3, 4, 5, 6, 7, 6, 5, 4]
    high = [9, 8, 7, 6, 7, 8, 9, 10, 11, 10, 9, 8]
    return _frame("AAA", [float(v) for v in low], [float(v) for v in high])


def _walk(symbol: str, n: int = 200, seed: int = 1, scale: float = 1.0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.012, n)))
    return _frame(
        symbol,
        list(close * 0.99),
        list(close * 1.01 * scale),
        list(close),
    )


@pytest.fixture()
def multi_ticker() -> pd.DataFrame:
    return pd.concat([_walk("AAA", seed=3), _walk("BBB", seed=9, scale=1.4)],
                     ignore_index=True)


def test_designed_overlap_counts_match_hand_computation():
    df = _designed()
    events = swing_events(df, window=WINDOW, gap=GAP)
    assert events == [(3, "at_bottom"), (5, "at_top"), (7, "at_top"), (10, "at_bottom")]
    t = audit_overlap(df, window=WINDOW, gap=GAP, hold_bars=HOLD)["totals"]
    # pairs closer than 3 bars: (3,5) and (5,7) -> 2; chained runs {3,5,7} {10} -> 2
    assert t["total_triggers"] == 4
    assert t["overlapping_pairs"] == 2
    assert t["clusters"] == 2
    # keep-first-while-open keeps 3, 7, 10 -> one suppressed (bar 5)
    assert t["suppressed_by_no_concurrent"] == 1
    assert t["at_bottom"] == 2 and t["at_top"] == 2


def test_hold_window_zero_suppression_when_triggers_are_spaced():
    df = _designed()
    t = audit_overlap(df, window=WINDOW, gap=GAP, hold_bars=1)["totals"]
    assert t["overlapping_pairs"] == 0
    assert t["clusters"] == 4
    assert t["suppressed_by_no_concurrent"] == 0


def test_prepare_frame_casts_float32_and_resets_index():
    raw = _designed().astype({c: "float64" for c in ("open", "high", "low", "close")})
    shuffled = raw.sample(frac=1.0, random_state=0)
    g = prepare_frame(shuffled)
    for col in ("open", "high", "low", "close"):
        assert g[col].dtype == np.float32
    assert isinstance(g.index, pd.RangeIndex)
    assert g["date"].is_monotonic_increasing
    assert len(g) == len(raw)


def test_window_edges_and_nan_yield_no_trigger():
    g = _walk("NAN", n=60, seed=5)
    clean = swing_events(g, window=WINDOW, gap=GAP)
    assert clean and all(t >= WINDOW - 1 for t, _ in clean)
    dirty = g.copy()
    dirty.loc[10:11, ["low", "high"]] = np.nan
    ev = swing_events(dirty, window=WINDOW, gap=GAP)
    # no trigger may sit in a trailing window that contains a NaN bar
    assert all(not (10 <= t <= 10 + WINDOW - 1) for t, _ in ev)
    assert [e for e in ev if e[0] < 10] == [e for e in clean if e[0] < 10]
    assert any(t > 10 + WINDOW - 1 for t, _ in ev)


def test_causality_truncation_and_future_perturbation(multi_ticker):
    cut = 80
    for _, g in multi_ticker.groupby("symbol", sort=False):
        g = g.reset_index(drop=True)
        full = swing_events(g)
        prefix = swing_events(g.iloc[: cut + 1])
        assert prefix == [e for e in full if e[0] <= cut]
        pert = g.copy()
        m = np.arange(len(g)) > cut
        pert.loc[m, "high"] = (pert.loc[m, "high"] * 3.0).astype("float32")
        pert.loc[m, "low"] = (pert.loc[m, "low"] * 0.4).astype("float32")
        assert [e for e in swing_events(pert) if e[0] <= cut] == prefix
        # counts are reproducible and prefix-stable
        assert audit_symbol(g, "X") == audit_symbol(g.copy(), "X")


def test_multi_ticker_totals_are_per_symbol_sums(multi_ticker):
    rep = audit_overlap(multi_ticker, window=SWING_WINDOW, hold_bars=SWING_WINDOW)
    assert rep["n_symbols"] == 2
    assert [p["symbol"] for p in rep["per_symbol"]] == ["AAA", "BBB"]
    assert rep["totals"]["total_triggers"] > 0
    for key in ("total_triggers", "overlapping_pairs", "clusters",
                "suppressed_by_no_concurrent"):
        assert rep["totals"][key] == sum(p[key] for p in rep["per_symbol"])
    expected = sum(
        len(swing_events(g)) for _, g in multi_ticker.groupby("symbol", sort=False)
    )
    assert rep["totals"]["total_triggers"] == expected
    assert rep["totals"]["suppressed_by_no_concurrent"] <= rep["totals"]["total_triggers"]


def test_no_symbol_crossing(multi_ticker):
    loud = multi_ticker.copy()
    m = loud["symbol"] == "AAA"
    loud.loc[m, ["high", "low"]] = loud.loc[m, ["high", "low"]] * 4.0
    out = audit_overlap(loud, window=SWING_WINDOW, hold_bars=SWING_WINDOW)
    solo = audit_symbol(multi_ticker[multi_ticker["symbol"] == "BBB"], "BBB",
                        window=SWING_WINDOW, hold_bars=SWING_WINDOW)
    bbb = next(p for p in out["per_symbol"] if p["symbol"] == "BBB")
    assert bbb == solo


def test_bad_parameters_rejected():
    with pytest.raises(ValueError):
        audit_overlap(_designed(), window=1)
    with pytest.raises(ValueError):
        audit_overlap(_designed(), gap=0)
    with pytest.raises(ValueError):
        audit_overlap(_designed(), hold_bars=0)
