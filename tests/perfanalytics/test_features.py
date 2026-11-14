"""WI-015 step 3 — fib-window enriched feature panel tests."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pyarrow.dataset as pads
import pytest

from src.feature_engine import compute_features
from src.perfanalytics.features import panel as panel_mod
from src.perfanalytics.features.panel import (
    FIB_GRID,
    FAMILIES,
    build_feature_panel,
    compute_fib_features,
    dataset_dir,
    family_of,
    feature_columns,
    window_of,
)


def _frame(n: int = 300, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100.0 * np.cumprod(1.0 + rng.normal(0.0004, 0.015, n))
    high = close * (1.0 + np.abs(rng.normal(0.004, 0.002, n)))
    low = close * (1.0 - np.abs(rng.normal(0.004, 0.002, n)))
    open_ = close * (1.0 + rng.normal(0.0, 0.003, n))
    return pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=n, freq="B"),
            "open": open_,
            "high": np.maximum.reduce([high, open_, close]),
            "low": np.minimum.reduce([low, open_, close]),
            "close": close,
            "volume": rng.uniform(5e5, 5e6, n),
        }
    )


def test_columns_family_major_and_float32():
    feats = compute_fib_features(_frame())
    assert list(feats.columns) == feature_columns()
    assert len(feats.columns) == len(FAMILIES) * len(FIB_GRID)
    assert all(str(d) == "float32" for d in feats.dtypes)


def test_family_and_window_roundtrip():
    for col in feature_columns():
        assert f"{family_of(col)}" in FAMILIES
        assert window_of(col) in FIB_GRID


def test_reuses_existing_family_definitions():
    """Overlapping family×window columns must equal the shipped 92-col pool."""
    g = _frame()
    shipped = compute_features(g)
    mine = compute_fib_features(g)
    for col in (
        "rsi_5",
        "rsi_21",
        "bb_pct_b_5",
        "bb_width_5",
        "adx_5",
        "di_spread_5",
        "atr_pct_5",
        "obv_zscore_5",
        "kama_er_5",
        "vwap_zscore_5",
        "amihud_5",
        "yangzhang_5",
        "range_pos_f3",
        "range_width_f3",
    ):
        assert col in shipped.columns, col
        a = mine[col].to_numpy("float64")
        b = shipped[col].to_numpy("float64")
        np.testing.assert_allclose(a, b, rtol=1e-5, atol=1e-6, equal_nan=True, err_msg=col)


def test_full_window_warmup_never_partial():
    # n=600 leaves room for the 233 windows: `_adx` chains two EWM(min_periods=w),
    # so it warms at ~2w-1, the widest requirement on the grid.
    g = _frame(n=600)
    feats = compute_fib_features(g)
    for col in feats.columns:
        if family_of(col) == "hurst":
            continue
        w = window_of(col)
        assert feats[col].iloc[: w - 1].isna().all(), col
        assert feats[col].notna().any(), col


def test_short_history_leaves_long_windows_nan():
    feats = compute_fib_features(_frame(n=60), windows=(3, 34, 144, 233))
    assert feats["range_pos_f233"].isna().all()
    assert feats["range_pos_f144"].isna().all()
    assert feats["range_pos_f34"].notna().any()


def test_coverage_counter_records_symbol_support():
    cov: dict[int, int] = {}
    compute_fib_features(_frame(n=100), windows=(34, 233), coverage=cov)
    assert cov == {34: 1, 233: 0}


def test_hurst_columns_absent_below_estimator_floor():
    feats = compute_fib_features(_frame(), windows=(5, 13))
    assert feats["hurst_5"].isna().all()
    assert feats["hurst_13"].notna().any()


def test_donchian_break_compares_prior_window_high():
    close = [10.0, 10.0, 10.0, 12.0, 10.0]
    g = pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=len(close), freq="B"),
            "open": close,
            "high": close,
            "low": close,
            "close": close,
            "volume": 1_000_000.0,
        }
    )
    feats = compute_fib_features(g, windows=(3,))
    # row 3 (close 12) breaks the prior 3-bar high (10); row 2 has no prior window
    assert np.isnan(feats["donchian_break_f3"][2])
    assert feats["donchian_break_f3"][3] == 1.0
    assert feats["donchian_break_f3"][4] == 0.0


def _source(symbols=("AAA", "BBB")):
    return [(s, _frame(n=200, seed=i)) for i, s in enumerate(symbols)]


def test_build_panel_writes_dataset_schema_and_summary(tmp_path):
    reports = tmp_path / "reports"
    out = build_feature_panel("CAD", out_dir=tmp_path, symbol_iter=_source(), reports_dir=reports)
    assert out.name == "features_CAD"
    assert dataset_dir("cad", tmp_path) == out

    table = pads.dataset(out).to_table()
    frame = table.to_pandas()
    assert list(frame.columns) == ["date", "symbol"] + feature_columns()
    assert set(frame["symbol"]) == {"AAA", "BBB"}

    schema = json.loads((tmp_path / "features_CAD_schema.json").read_text())
    assert schema["fib_grid"] == list(FIB_GRID)
    assert schema["columns"] == feature_columns()
    assert schema["symbols"] == 2
    assert set(schema["window_coverage_symbols"]) == {str(w) for w in FIB_GRID}

    summary = (reports / "features_summary_CAD.md").read_text()
    assert "enriched feature panel (CAD)" in summary
    assert "`233`" in summary or "| 233 |" in summary


def test_build_panel_streams_symbol_by_symbol(tmp_path):
    out_dir = tmp_path / "features_CAD"
    seen: list[str] = []

    def streaming():
        for symbol, df in _source(("AAA", "BBB")):
            if seen:
                assert (out_dir / f"symbol={seen[-1]}.parquet").exists()
            seen.append(symbol)
            yield symbol, df

    build_feature_panel("CAD", out_dir=tmp_path, symbol_iter=streaming(), reports_dir=tmp_path)
    assert seen == ["AAA", "BBB"]
    assert (tmp_path / "features_summary_CAD.md").exists()


def test_cli_rejects_invalid_market(tmp_path, capsys):
    rc = panel_mod.main(["--market", "XYZ", "--out-dir", str(tmp_path)])
    assert rc == 2
    assert "invalid market" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []
