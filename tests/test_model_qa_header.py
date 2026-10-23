"""Tests for model_qa header changes (Step 7): universe info, fixture check, K warning."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.model_qa import main


@pytest.fixture
def tmp_qadata(monkeypatch, tmp_path):
    """Set up fake oof + meta data for QA testing."""
    base = Path(__file__).resolve().parents[1]
    monkeypatch.setattr("src.model_qa.DATA_DIR", tmp_path)
    monkeypatch.setattr("src.model_qa.REPORT_PATH", tmp_path / "sprint4_model_qa.md")
    monkeypatch.setattr("src.model_qa.STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr("src.state_manager.LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr("src.state_manager.STATE_FILE", tmp_path / "state.json")
    (tmp_path / "logs").mkdir()

    # Create minimal OOF + meta with fixture source → should trigger exit 3
    import pandas as pd
    import numpy as np

    oof = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=20),
        "symbol": ["S1"] * 20,
        "close": np.random.randn(20) + 100,
        "fwd_atr_ret_15": np.random.randn(20),
        "fwd_atr_ret_20": np.random.randn(20),
        "y_15d_high": np.random.randint(0, 2, 20).astype("int8"),
        "y_15d_low": np.random.randint(0, 2, 20).astype("int8"),
        "y_20d_up": np.random.randint(0, 2, 20).astype("int8"),
        "y_20d_down": np.random.randint(0, 2, 20).astype("int8"),
        "p_15d_high": np.random.rand(20).astype("float32"),
        "p_15d_low": np.random.rand(20).astype("float32"),
        "p_20d_up": np.random.rand(20).astype("float32"),
        "p_20d_down": np.random.rand(20).astype("float32"),
        "fold_15d_high": np.zeros(20, dtype="int16"),
        "fold_15d_low": np.zeros(20, dtype="int16"),
        "fold_20d_up": np.zeros(20, dtype="int16"),
        "fold_20d_down": np.zeros(20, dtype="int16"),
    })
    oof["close"] = oof["close"].astype("float32")
    oof["fwd_atr_ret_15"] = oof["fwd_atr_ret_15"].astype("float32")
    oof["fwd_atr_ret_20"] = oof["fwd_atr_ret_20"].astype("float32")
    # Add placebo columns
    for s in range(5):
        oof[f"y_15d_high_pl{s}"] = np.random.randint(0, 2, 20).astype("int8")
        oof[f"p_15d_high_pl{s}"] = np.random.rand(20).astype("float32")
    oof.to_parquet(tmp_path / "oof_USD.parquet")

    meta = {
        "market": "USD",
        "universe": {"n_symbols": 1, "n_rows": 20, "date_min": "2024-01-01", "date_max": "2024-01-20",
                      "source": "fixture", "min_date": "2024-01-01", "quarantined_excluded": 0},
        "targets": {
            "y_15d_high": {"features": ["rsi_14"], "folds": [{"fold": 0, "train_pos_rate": 0.5,
                "train_pr_auc": 0.6, "val_pr_auc": 0.5, "calibration": "isotonic", "best_iteration": 10}]},
            "y_15d_low": {"features": ["rsi_14"], "folds": [{"fold": 0, "train_pos_rate": 0.4,
                "train_pr_auc": 0.5, "val_pr_auc": 0.45, "calibration": "isotonic", "best_iteration": 5}]},
        },
    }
    (tmp_path / "train_meta_USD.json").write_text(json.dumps(meta))
    return tmp_path


def test_qa_rejects_fixture(tmp_qadata, monkeypatch):
    """QA exits with code 3 when universe source is 'fixture'."""
    monkeypatch.setattr("sys.argv", ["model_qa", "--market", "USD"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 3


def test_qa_fixture_output(tmp_qadata, monkeypatch, capsys):
    """Fixture detection prints message to stderr."""
    monkeypatch.setattr("sys.argv", ["model_qa", "--market", "USD"])
    try:
        main()
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert "FIXTURE" in captured.err.upper()
    assert "FATAL" in captured.err.upper()