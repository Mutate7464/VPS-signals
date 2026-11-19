"""WI-085: byte ledger refusal, projection discipline and LRU caps."""
from __future__ import annotations

import numpy as np
import pytest

import src.visualizer.loader as loader_module
from src.visualizer import COLUMN_LRU_SIZE, DEFAULT_BUDGET_BYTES, OHLCV_LRU_SIZE, raw_ohlcv_path
from src.visualizer.cache import ByteLedger, DataBudgetError, LRUCache, process_rss_bytes
from src.visualizer.loader import FILTER_PROBE_COLUMNS, VisualizerLoader
from src.visualizer.schema import N_FEATURE_COLUMNS, PANEL_ROWS_MEASURED


def test_budget_contract_is_3_gb_and_cost_is_rows_x_cols_x_4() -> None:
    assert DEFAULT_BUDGET_BYTES == 3 * 1024**3
    assert ByteLedger.estimate(1_000_000, 5) == 20_000_000
    assert ByteLedger.estimate(1_240_275, ["a", "b", "c"]) == 1_240_275 * 3 * 4
    assert COLUMN_LRU_SIZE == 64 and OHLCV_LRU_SIZE == 32


def test_over_budget_load_is_refused_before_any_read(monkeypatch) -> None:
    reads: list[dict] = []
    original = loader_module.pq.read_table
    monkeypatch.setattr(
        loader_module.pq, "read_table", lambda *a, **kw: (reads.append(kw), original(*a, **kw))[1]
    )
    loader = VisualizerLoader(budget_bytes=1 * 2**20)  # 1 MB budget
    with pytest.raises(DataBudgetError, match="refused"):
        loader.load_columns("USD", list(FILTER_PROBE_COLUMNS))
    assert reads == [], "the loader read before the ledger refused"
    assert loader.ledger.used_bytes == 0
    assert loader.ledger.snapshot()["n_entries"] == 0
    assert len(loader.columns) == 0


def test_projection_is_keyed_and_never_the_full_panel(monkeypatch) -> None:
    seen: list[tuple[str, ...]] = []
    original = loader_module.pq.read_table

    def recorder(path, columns=None, **kwargs):
        seen.append(tuple(columns or ()))
        return original(path, columns=columns, **kwargs)

    monkeypatch.setattr(loader_module.pq, "read_table", recorder)
    loader = VisualizerLoader(budget_bytes=256 * 2**20)
    frame = loader.load_columns("CAD", ["rsi_5", "atr_pct_20"])
    assert len(seen) == 1
    assert seen[0] == ("date", "symbol", "market", "rsi_5", "atr_pct_20")
    assert len(seen[0]) < N_FEATURE_COLUMNS
    assert len(frame) == PANEL_ROWS_MEASURED["CAD"]
    assert frame["rsi_5"].dtype == np.float32 and frame["atr_pct_20"].dtype == np.float32
    assert str(frame["date"].dtype).startswith("datetime64")
    assert frame["symbol"].dtype.name == "category"
    assert loader.ledger.used_bytes == ByteLedger.estimate(len(frame), len(seen[0]))
    assert loader.ledger.used_bytes < DEFAULT_BUDGET_BYTES


def test_column_lru_evicts_and_releases_ledger_bytes() -> None:
    loader = VisualizerLoader()
    loader.columns = LRUCache(capacity=2, name="columns")
    for column in ("rsi_5", "rsi_14", "atr_pct_20"):
        loader.load_columns("CAD", [column])
    assert len(loader.columns) == 2
    assert loader.ledger.snapshot()["n_entries"] == 2
    assert 0 < loader.ledger.used_bytes <= 2 * ByteLedger.estimate(PANEL_ROWS_MEASURED["CAD"], 4)


def test_ohlcv_lru_caps_at_32_symbols(monkeypatch) -> None:
    loader = VisualizerLoader()
    real_file = raw_ohlcv_path("USD", "A")
    monkeypatch.setattr(loader_module, "raw_ohlcv_path", lambda market, symbol: real_file)
    for index in range(OHLCV_LRU_SIZE + 8):
        frame = loader.sample_ohlcv("USD", f"SYN{index:02d}")
        assert len(frame) > 0
    assert len(loader.ohlcv) == OHLCV_LRU_SIZE
    assert ("USD", "SYN00") not in loader.ohlcv
    assert ("USD", f"SYN{OHLCV_LRU_SIZE + 7:02d}") in loader.ohlcv


def test_real_projected_load_fits_budget_and_keeps_float32() -> None:
    loader = VisualizerLoader()
    frame = loader.load_columns("CAD", list(FILTER_PROBE_COLUMNS))
    assert len(frame) == PANEL_ROWS_MEASURED["CAD"]
    for column in FILTER_PROBE_COLUMNS:
        assert frame[column].dtype == np.float32, column
    assert 0 < loader.ledger.used_bytes < DEFAULT_BUDGET_BYTES
    assert process_rss_bytes() > 0
