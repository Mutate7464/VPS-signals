"""Structured logging, RSS telemetry, memory guard, and XGBoost callback."""

from __future__ import annotations

import contextlib
import datetime as dt
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Callable

import psutil
import xgboost as xgb

try:
    from xgboost.callback import TrainingCallback as _XGBTrainingCallback
except ImportError:
    _XGBTrainingCallback = object

BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "logs"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def rss_mb() -> float:
    """Current process RSS in MB."""
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)


def mem_available_mb() -> float:
    """System MemAvailable in MB (from /proc/meminfo)."""
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return float(line.split()[1]) / 1024.0
    except Exception:
        pass
    # fallback: psutil virtual_memory
    return psutil.virtual_memory().available / (1024 * 1024)


class MemoryGuardError(RuntimeError):
    """Raised when available memory drops below the configured floor."""


def check_memory(logger: logging.Logger | None = None, min_avail_mb: float = 1000.0) -> float:
    """Check MemAvailable; if below `min_avail_mb`, log ERROR and raise MemoryGuardError.

    Returns MemAvailable in MB.
    """
    avail = mem_available_mb()
    if avail < min_avail_mb:
        msg = f"MemAvailable {avail:.0f} MB < floor {min_avail_mb:.0f} MB — aborting"
        if logger:
            logger.error(msg)
        raise MemoryGuardError(msg)
    if logger:
        logger.debug("MemAvailable %.0f MB (floor %.0f MB)", avail, min_avail_mb)
    return avail


# --------------------------------------------------------------------------- #
# JSON line file (machine-readable events)
# --------------------------------------------------------------------------- #
class JSONLHandler(logging.Handler):
    """Write each log record as a JSON line to a file."""

    def __init__(self, path: Path):
        super().__init__()
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fd = open(path, "a")

    def emit(self, record: logging.LogRecord):
        entry = {
            "ts": dt.datetime.fromtimestamp(record.created, tz=dt.timezone.utc).isoformat(),
            "level": record.levelname,
            "phase": getattr(record, "phase", "?"),
            "msg": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1]:
            entry["exc"] = str(record.exc_info[1])
        self._fd.write(json.dumps(entry) + "\n")
        self._fd.flush()

    def close(self):
        super().close()
        if hasattr(self, "_fd"):
            self._fd.close()


# --------------------------------------------------------------------------- #
# Setup
# --------------------------------------------------------------------------- #
class _PhaseFilter(logging.Filter):
    """Ensure every log record has a `phase` attribute (default 'main')."""
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "phase") or record.phase is None:
            record.phase = "main"
        return True


def setup_logging(name: str, market: str) -> tuple[logging.Logger, Path, Path]:
    """Create a logger writing to console + file + JSONL.

    Returns (logger, log_path, jsonl_path).
    """
    xgb.set_config(verbosity=1)

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_path = LOG_DIR / f"{name}_{market}_{ts}.log"
    jsonl_path = LOG_DIR / f"{name}_{market}_{ts}.jsonl"

    logger = logging.getLogger(f"{name}_{market}_{ts}")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    phase_filter = _PhaseFilter()
    fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(phase)-20s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S")

    # console
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)
    sh.addFilter(phase_filter)
    logger.addHandler(sh)

    # file
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    fh.addFilter(phase_filter)
    logger.addHandler(fh)

    # JSONL
    jh = JSONLHandler(jsonl_path)
    jh.setLevel(logging.DEBUG)
    logger.addHandler(jh)

    logger.info("logger started  name=%s  market=%s  log=%s  jsonl=%s", name, market, log_path, jsonl_path)
    return logger, log_path, jsonl_path


# --------------------------------------------------------------------------- #
# Phase context manager
# --------------------------------------------------------------------------- #
def _make_phase(logger: logging.Logger, phase: str, rss_start: float, mem_start: float, t0: float) -> logging.LoggerAdapter:
    return logging.LoggerAdapter(logger, {"phase": phase})


@contextlib.contextmanager
def log_phase(logger: logging.Logger, phase: str):
    """Context manager logging phase start, end, wall time, RSS delta, MemAvailable."""
    adapter = _make_phase(logger, phase, rss_mb(), mem_available_mb(), 0.0)
    t0 = time.time()
    r0 = rss_mb()
    m0 = mem_available_mb()
    adapter.info("START  rss=%.0fMB  mem_avail=%.0fMB", r0, m0)
    try:
        yield adapter
    except Exception:
        adapter.error("EXCEPTION  elapsed=%.1fs  rss=%.0fMB", time.time() - t0, rss_mb(), exc_info=True)
        raise
    else:
        r1 = rss_mb()
        m1 = mem_available_mb()
        adapter.info("END  elapsed=%.1fs  rss_before=%.0fMB  rss_after=%.0fMB  delta=%.0fMB  mem_avail=%.0fMB",
                     time.time() - t0, r0, r1, r1 - r0, m1)


# --------------------------------------------------------------------------- #
# XGBoost callback
# --------------------------------------------------------------------------- #
class XGBLogCallback(_XGBTrainingCallback):
    """Log eval metric every N rounds + summary.  Subclasses xgboost.callback.TrainingCallback."""

    def __init__(self, logger: logging.Logger | logging.LoggerAdapter, label: str, every: int = 25):
        super().__init__()
        self.logger = logger
        self.label = label
        self.every = every
        self._last_round = 0
        self._best_iteration = -1
        self._best_score = float("inf")
        self._rounds_run = 0

    def __call__(self, env):
        """Called after each boosting iteration.  env.model, env.iteration, env.evaluation_result_list."""
        i = env.iteration
        self._rounds_run = i + 1
        results = env.evaluation_result_list  # list of (name, metric) pairs
        # log every N rounds
        if i % self.every == 0:
            parts = "  ".join(f"{name}={metric:.5f}" for name, metric in results)
            self.logger.info("xgb round %4d %s  %s", i, self.label, parts)
        # track best
        if results:
            _, score = results[0]
            if score < self._best_score:
                self._best_iteration = i
                self._best_score = score
        self._last_round = i

    def after_training(self, model):
        """Called after training completes — must return model for xgboost callback protocol."""
        self.logger.info(
            "xgb done %s  rounds=%d  best_iteration=%d  best_score=%.5f",
            self.label, self._rounds_run, self._best_iteration, self._best_score,
        )
        if self._best_iteration <= 1:
            self.logger.warning("NO_LEARNING %s  best_iteration=%d — early stop at round ≤ 1", self.label, self._best_iteration)
        return model


def xgb_callback(logger: logging.Logger | logging.LoggerAdapter, label: str, every: int = 25):
    """Factory returning an XGBLogCallback instance."""
    return XGBLogCallback(logger, label, every)