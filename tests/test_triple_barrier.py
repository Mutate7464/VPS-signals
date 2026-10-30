"""WI-016 step 2 — triple-barrier fib-ladder label tests.

Verify: `uv run pytest tests/test_triple_barrier.py`
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.targets import wilder_atr
from src.wi016 import triple_barrier as tb
from src.wi016.triple_barrier import (
    TOUCH_PROFIT,
    TOUCH_STOP,
    TOUCH_VERTICAL,
    TripleBarrierAccumulator,
    barrier_levels,
    compute_triple_barrier,
    label_columns,
)


def _base_df(n: int = 400, close: float = 100.0, high: float = 101.0, low: float = 99.0) -> pd.DataFrame:
    """Flat series: TR = 2, so `wilder_atr` = 2.0 from index 19 on."""
    return pd.DataFrame(
        {
            "date": pd.date_range("2015-01-01", periods=n, freq="B"),
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "volume": 1000.0,
        }
    )


# --------------------------------------------------------------------------- #
# Barrier syntax / grid
# --------------------------------------------------------------------------- #
def test_barrier_levels_are_symmetric_k_atr():
    close = np.array([100.0, 50.0])
    atr = np.array([2.0, 4.0])
    upper, lower = barrier_levels(close, atr, 1.5)
    assert np.allclose(upper, [103.0, 56.0])
    assert np.allclose(lower, [97.0, 44.0])


def test_label_columns_cover_grid():
    cols = label_columns()
    for k_tag in ("k15", "k20"):
        for h in (8, 21, 55, 144, 233):
            assert f"tb_label_{k_tag}_h{h}" in cols
            assert f"tb_touch_{k_tag}_h{h}" in cols
    assert "tb_fret_h233" in cols


# --------------------------------------------------------------------------- #
# First-touch classes
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("k", [1.5, 2.0])
def test_profit_touch_first(k):
    df = _base_df()
    df.loc[201, "high"] = 104.0  # >= close+2.0·ATR = 104 for both k
    lab = compute_triple_barrier(df, k_values=(k,), horizons=(21,))
    assert lab.loc[200, f"tb_label_k{int(k * 10)}_h21"] == 1.0
    assert lab.loc[200, f"tb_touch_k{int(k * 10)}_h21"] == TOUCH_PROFIT


@pytest.mark.parametrize("k", [1.5, 2.0])
def test_stop_touch_first(k):
    df = _base_df()
    df.loc[201, "low"] = 96.0  # <= close-2.0·ATR = 96
    lab = compute_triple_barrier(df, k_values=(k,), horizons=(21,))
    assert lab.loc[200, f"tb_label_k{int(k * 10)}_h21"] == -1.0
    assert lab.loc[200, f"tb_touch_k{int(k * 10)}_h21"] == TOUCH_STOP


def test_stop_is_conservative_on_same_bar_tie():
    df = _base_df()
    df.loc[201, "high"] = 104.0
    df.loc[201, "low"] = 96.0  # both barriers in the same forward bar
    lab = compute_triple_barrier(df, k_values=(1.5,), horizons=(21,))
    assert lab.loc[200, "tb_label_k15_h21"] == -1.0
    assert lab.loc[200, "tb_touch_k15_h21"] == TOUCH_STOP


def test_vertical_up_sign():
    df = _base_df()
    df.loc[221, "close"] = 105.0  # untraded path, +5% realized at t+h
    lab = compute_triple_barrier(df, k_values=(1.5,), horizons=(21,))
    assert lab.loc[200, "tb_touch_k15_h21"] == TOUCH_VERTICAL
    assert lab.loc[200, "tb_label_k15_h21"] == 1.0


def test_vertical_down_sign():
    df = _base_df()
    df.loc[221, "close"] = 95.0
    lab = compute_triple_barrier(df, k_values=(1.5,), horizons=(21,))
    assert lab.loc[200, "tb_touch_k15_h21"] == TOUCH_VERTICAL
    assert lab.loc[200, "tb_label_k15_h21"] == -1.0


def test_vertical_neutral_sign():
    df = _base_df()  # constant close -> realized return exactly 0
    lab = compute_triple_barrier(df, k_values=(1.5,), horizons=(21,))
    assert lab.loc[200, "tb_touch_k15_h21"] == TOUCH_VERTICAL
    assert lab.loc[200, "tb_label_k15_h21"] == 0.0


# --------------------------------------------------------------------------- #
# Masks
# --------------------------------------------------------------------------- #
def test_horizon_tail_mask():
    df = _base_df(n=400)
    lab = compute_triple_barrier(df, k_values=(1.5,), horizons=(8, 233))
    # h=8: last 8 rows undefined.
    assert np.isnan(lab["tb_label_k15_h8"].to_numpy()[-8:]).all()
    assert np.isfinite(lab["tb_label_k15_h8"].to_numpy()[-9])
    # h=233: rows >= n - h undefined.
    assert np.isnan(lab["tb_label_k15_h233"].to_numpy()[167:]).all()
    assert np.isfinite(lab["tb_label_k15_h233"].to_numpy()[166])


def test_atr_warmup_masked():
    df = _base_df(n=60)
    lab = compute_triple_barrier(df, k_values=(1.5,), horizons=(8,))
    assert np.isnan(lab["tb_label_k15_h8"].to_numpy()[:19]).all()  # ATR warm-up
    assert np.isfinite(lab["tb_label_k15_h8"].to_numpy()[19])


# --------------------------------------------------------------------------- #
# Causality
# --------------------------------------------------------------------------- #
def test_atr_thresholds_ignore_future_data():
    df = _base_df(n=400)
    atr_before = wilder_atr(df).to_numpy()
    upper_before, lower_before = barrier_levels(df["close"].to_numpy(), atr_before, 1.5)

    future = df.copy()
    future.loc[300:, "high"] = 200.0
    future.loc[300:, "low"] = 10.0
    atr_after = wilder_atr(future).to_numpy()
    upper_after, lower_after = barrier_levels(future["close"].to_numpy(), atr_after, 1.5)

    # Nothing at or before the cutoff changes.
    assert np.allclose(atr_before[:300], atr_after[:300], equal_nan=True)
    assert upper_before[200] == upper_after[200]
    assert lower_before[200] == lower_after[200]
    # The future perturbation really does change future ATR (guard the premise).
    assert not np.allclose(atr_before[300:], atr_after[300:])


# --------------------------------------------------------------------------- #
# Dtypes
# --------------------------------------------------------------------------- #
def test_outputs_are_float32_and_touch_int8():
    df = _base_df()
    lab = compute_triple_barrier(df, k_values=(1.5,), horizons=(8,))
    assert lab["tb_label_k15_h8"].dtype == np.float32
    assert lab["tb_fret_h8"].dtype == np.float32
    assert lab["tb_touch_k15_h8"].dtype == np.int8


# --------------------------------------------------------------------------- #
# Report / diagnostics
# --------------------------------------------------------------------------- #
def test_accumulator_density_and_class_balance():
    df = _base_df(n=120)
    df.loc[100, "high"] = 104.0  # a profit-touch bar inside h=21 forward windows
    lab = compute_triple_barrier(df, k_values=(1.5,), horizons=(21,))
    acc = TripleBarrierAccumulator(k_values=(1.5,), horizons=(21,))
    acc.add_symbol(lab, df["date"])
    s = acc.summary()
    row = s["grid"][0]
    assert row["n_events"] > 0
    assert row["profit"] > 0
    # Density is the profit share of defined events.
    assert row["profit_density"] == pytest.approx(row["profit"] / row["n_events"])
    # Profit touches are class +1; there are no vertical-up events in a flat close.
    assert row["class_plus"] == row["profit"]
    assert row["class_neutral"] > 0  # constant close -> vertical neutrals
    assert row["profit"] + row["stop"] + row["vertical"] == row["n_events"]


def test_report_written_with_wi016_prefix(tmp_path):
    df = _base_df(n=120)
    lab = compute_triple_barrier(df, k_values=(1.5,), horizons=(8,))
    acc = TripleBarrierAccumulator(k_values=(1.5,), horizons=(8,))
    acc.add_symbol(lab, df["date"])
    md_path, csv_path = tb._write_report(acc.summary(), "USD", out_dir=tmp_path)
    assert md_path.name == "wi016_label_density_USD.md"
    assert csv_path.name == "wi016_label_density_USD.csv"
    assert md_path.exists() and "triple-barrier label density" in md_path.read_text()


# --------------------------------------------------------------------------- #
# CLI market parameterization
# --------------------------------------------------------------------------- #
def test_cli_market_parameterization(monkeypatch):
    calls: list[str] = []

    def _fake_run_market(market, **kwargs):
        calls.append(market)
        return {"n_symbols": 0, "n_rows": 0}

    monkeypatch.setattr(tb, "run_market", _fake_run_market)

    assert tb.main(["--market", "USD", "--dry-run"]) == 0
    assert calls == ["USD"]
    calls.clear()

    assert tb.main(["--market", "CAD", "--dry-run"]) == 0
    assert calls == ["CAD"]
    calls.clear()

    # Omitted market and the both-alias run USD then CAD.
    assert tb.main(["--market", "ALL", "--dry-run"]) == 0
    assert calls == ["USD", "CAD"]
    calls.clear()

    assert tb.main(["--market", "EUR", "--dry-run"]) == 2
    assert calls == []
