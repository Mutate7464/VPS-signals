"""WI-015 step 2 — market run-target dataset builder tests."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pyarrow.dataset as pads
import pytest

from src.perfanalytics.targets import (
    build_run_targets,
    dataset_dir,
    resolve_markets,
    target_columns,
    target_value_columns,
)
from src.perfanalytics.targets import dataset as dataset_mod
from src.market_cli import MarketSelectionError


def _symbol(name: str, n: int = 120, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100.0 * np.cumprod(1.0 + rng.normal(0.0005, 0.02, n))
    return pd.DataFrame(
        {
            "date": pd.date_range("2021-01-01", periods=n, freq="B"),
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": 1_000_000.0,
            "symbol": name,
            "market": "CAD",
        }
    )


def _source(symbols=("AAA", "BBB", "CCC")):
    return [(s, _symbol(s, seed=i)) for i, s in enumerate(symbols)]


def test_resolve_markets_orders_cad_first():
    assert resolve_markets(None) == ["CAD", "USD"]
    assert resolve_markets("BOTH") == ["CAD", "USD"]
    assert resolve_markets("usd") == ["USD"]
    with pytest.raises(MarketSelectionError):
        resolve_markets("XYZ")


def test_dataset_dir_is_market_suffixed(tmp_path):
    assert dataset_dir("cad", tmp_path).name == "run_targets_CAD"


def test_build_writes_market_suffixed_parquet_dataset(tmp_path):
    out = build_run_targets("CAD", out_dir=tmp_path, symbol_iter=_source())
    assert out.name == "run_targets_CAD"
    files = sorted(p.name for p in out.glob("symbol=*.parquet"))
    assert files == ["symbol=AAA.parquet", "symbol=BBB.parquet", "symbol=CCC.parquet"]

    table = pads.dataset(out).to_table()
    frame = table.to_pandas()
    assert list(frame.columns) == ["date", "symbol"] + target_columns()
    assert set(frame["symbol"]) == {"AAA", "BBB", "CCC"}
    assert pd.api.types.is_datetime64_any_dtype(frame["date"])
    for col in target_columns():
        assert str(frame[col].dtype) == "float32", col
    # rows survive per symbol (labelled rows only, never an all-NaN row)
    value_cols = target_value_columns()
    for _, g in frame.groupby("symbol"):
        assert len(g) > 0
        assert g[value_cols].notna().any(axis=1).all()


def test_streams_symbol_by_symbol(tmp_path):
    """Each symbol's file must exist before the next symbol is read."""
    out_dir = tmp_path / "run_targets_CAD"
    seen: list[str] = []

    def streaming():
        for symbol, df in _source(("AAA", "BBB", "CCC")):
            if seen:
                prev = out_dir / f"symbol={seen[-1]}.parquet"
                assert prev.exists(), f"{prev} not written before reading {symbol}"
            seen.append(symbol)
            yield symbol, df

    build_run_targets("CAD", out_dir=tmp_path, symbol_iter=streaming())
    assert seen == ["AAA", "BBB", "CCC"]


def test_symbol_with_no_labelled_rows_is_skipped(tmp_path):
    src = _source(("AAA",)) + [("TINY", _symbol("TINY", n=15, seed=9))]
    out = build_run_targets("CAD", out_dir=tmp_path, symbol_iter=src)
    assert [p.name for p in out.glob("symbol=*.parquet")] == ["symbol=AAA.parquet"]


def test_schema_record_written_next_to_dataset(tmp_path):
    build_run_targets("CAD", out_dir=tmp_path, symbol_iter=_source())
    schema = json.loads((tmp_path / "run_targets_CAD_schema.json").read_text())
    assert schema["market"] == "CAD"
    assert schema["horizons"] == [15, 20]
    assert schema["symbols"] == 3 and schema["rows"] > 0
    assert set(target_columns()) <= set(schema["columns"])
    assert schema["columns"]["t1_amp_15"].startswith("float32:")


def test_cli_rejects_invalid_market_before_writing(tmp_path, capsys):
    rc = dataset_mod.main(["--market", "XYZ", "--out-dir", str(tmp_path)])
    assert rc == 2
    assert "invalid market" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_cli_calls_markets_in_cad_then_usd_order(tmp_path, monkeypatch):
    calls: list[str] = []

    def fake(market, **kwargs):
        calls.append(market)
        return tmp_path / f"run_targets_{market}"

    monkeypatch.setattr(dataset_mod, "build_run_targets", fake)
    rc = dataset_mod.main(["--out-dir", str(tmp_path)])
    assert rc == 0 and calls == ["CAD", "USD"]
