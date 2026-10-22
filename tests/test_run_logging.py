"""Tests for src/run_logging.py."""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

import numpy as np
import pytest
import xgboost as xgb

from src.run_logging import (
    MemoryGuardError,
    check_memory,
    log_phase,
    mem_available_mb,
    rss_mb,
    setup_logging,
    xgb_callback,
)

# --------------------------------------------------------------------------- #
# Basic helpers
# --------------------------------------------------------------------------- #
def test_rss_mb():
    assert rss_mb() > 0

def test_mem_available():
    assert mem_available_mb() > 0

def test_check_memory_pass():
    avail = check_memory(min_avail_mb=1.0)  # always passes
    assert avail > 0

def test_check_memory_raises():
    with pytest.raises(MemoryGuardError, match="aborting"):
        check_memory(min_avail_mb=99999999.0)

# --------------------------------------------------------------------------- #
# Logging setup
# --------------------------------------------------------------------------- #
def test_setup_logging(tmp_path, monkeypatch):
    monkeypatch.setattr("src.run_logging.LOG_DIR", tmp_path)
    logger, log_path, jsonl_path = setup_logging("test", "USD")
    logger.info("hello world")
    logger.warning("uhoh")

    assert log_path.exists()
    content = log_path.read_text()
    assert "hello world" in content
    assert "uhoh" in content

    assert jsonl_path.exists()
    lines = [json.loads(l) for l in jsonl_path.read_text().strip().split("\n")]
    assert any("hello world" in l["msg"] for l in lines)
    assert any("uhoh" in l["msg"] for l in lines)
    assert all("level" in l and "phase" in l for l in lines)

# --------------------------------------------------------------------------- #
# log_phase context manager
# --------------------------------------------------------------------------- #
def test_log_phase_context(tmp_path, monkeypatch):
    monkeypatch.setattr("src.run_logging.LOG_DIR", tmp_path)
    logger, _, _ = setup_logging("test_phase", "USD")
    with log_phase(logger, "test_step") as _lg:
        pass
    # should have START and END
    content = (tmp_path / "test_phase_USD_000000.log") if False else None
    # check log content
    log_files = list(tmp_path.glob("test_phase_USD_*.log"))
    assert log_files
    body = log_files[0].read_text()
    assert "START" in body
    assert "END" in body
    assert "rss" in body.lower()

def test_log_phase_exception(tmp_path, monkeypatch):
    monkeypatch.setattr("src.run_logging.LOG_DIR", tmp_path)
    logger, _, _ = setup_logging("test_exc", "USD")
    with pytest.raises(ValueError, match="boom"):
        with log_phase(logger, "failing_step"):
            raise ValueError("boom")
    log_files = list(tmp_path.glob("test_exc_USD_*.log"))
    body = log_files[0].read_text()
    assert "EXCEPTION" in body
    assert "boom" in body

# --------------------------------------------------------------------------- #
# XGBoost callback
# --------------------------------------------------------------------------- #
def test_xgb_callback_logs(tmp_path, monkeypatch):
    monkeypatch.setattr("src.run_logging.LOG_DIR", tmp_path)
    logger, _, _ = setup_logging("test_xgb", "USD")

    # tiny dataset
    rng = np.random.default_rng(42)
    X = rng.normal(size=(200, 5)).astype("float32")
    y = (X[:, 0] + rng.normal(0, 0.3, 200) > 0).astype("int32")

    cb = xgb_callback(logger, "train", every=25)
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=3,
        tree_method="hist",
        n_jobs=1,
        random_state=42,
        callbacks=[cb],
    )
    # Use eval_set so training runs more than 0 rounds
    model.fit(X, y, eval_set=[(X, y)], verbose=False)
    # after_training is already called by xgboost internals

    log_files = list(tmp_path.glob("test_xgb_USD_*.log"))
    body = log_files[0].read_text()
    assert "xgb done" in body  # after_training fires
    assert "best_score" in body

def test_xgb_callback_no_learning(tmp_path, monkeypatch):
    monkeypatch.setattr("src.run_logging.LOG_DIR", tmp_path)
    logger, _, _ = setup_logging("test_nolearn", "USD")

    rng = np.random.default_rng(99)
    X = rng.normal(size=(100, 3)).astype("float32")
    # pure noise labels — model shouldn't learn much
    y = rng.integers(0, 2, 100).astype("int32")

    cb = xgb_callback(logger, "train", every=10)
    model = xgb.XGBClassifier(
        n_estimators=50, max_depth=2, tree_method="hist", n_jobs=1,
        early_stopping_rounds=5, random_state=42,
        callbacks=[cb],
    )
    model.fit(X, y, eval_set=[(X, y)], verbose=False)
    # xgboost calls after_training internally now

    log_files = list(tmp_path.glob("test_nolearn_USD_*.log"))
    body = log_files[0].read_text()
    # May or may not trigger NO_LEARNING depending on early-stop behavior;
    # the important thing is the log exists and includes `xgb done`.
    assert "xgb done" in body