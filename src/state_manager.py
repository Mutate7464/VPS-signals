"""State ledger, telemetry, and ticker quarantine for the quant-screener pipeline.

Responsibilities:
- `state/PIPELINE_STATE.json` idempotent checkpoint ledger.
- RSS memory telemetry appended to `logs/pipeline_run_YYYYMMDD.jsonl`.
- `quarantine_ticker()` writes broken tickers to `data/dead_letter_tickers.csv`
  without crashing the batch.

The project root is resolved relative to this file so it works regardless of
where the repository lives (no hardcoded `/opt/...` paths).
"""

import csv
import datetime as dt
import json
import os
from pathlib import Path

import psutil

BASE_DIR = Path(__file__).resolve().parents[1]
STATE_FILE = BASE_DIR / "state" / "PIPELINE_STATE.json"
DEAD_LETTER_FILE = BASE_DIR / "data" / "dead_letter_tickers.csv"
LOG_DIR = BASE_DIR / "logs"


def init_dirs() -> None:
    """Create state/log directories and seed the state file if missing."""
    (BASE_DIR / "state").mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.exists():
        default_state = {
            "current_sprint": "EP-01",
            "gates_approved": {
                "gate_1": False,
                "gate_2": False,
                "gate_3": False,
                "gate_4": False,
                "gate_5": False,
            },
            "checkpoints": {},
            "last_updated_utc": None,
            "last_error": None,
        }
        STATE_FILE.write_text(json.dumps(default_state, indent=2))


def update_state(sprint: str, key: str, value) -> None:
    """Set a checkpoint value for a sprint and stamp the ledger."""
    init_dirs()
    state = json.loads(STATE_FILE.read_text())
    state["current_sprint"] = sprint
    state["checkpoints"][key] = value
    state["last_updated_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2))


def log_telemetry(step_name: str, status: str, duration_sec: float, extra: dict = None) -> None:
    """Append an RSS memory telemetry line to the daily run log."""
    init_dirs()
    proc = psutil.Process(os.getpid())
    rss_mb = round(proc.memory_info().rss / (1024 * 1024), 2)
    payload = {
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "step": step_name,
        "status": status,
        "duration_sec": round(duration_sec, 2),
        "rss_memory_mb": rss_mb,
        "extra": extra or {},
    }
    log_file = LOG_DIR / f"pipeline_run_{dt.date.today().strftime('%Y%m%d')}.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(payload) + "\n")


def quarantine_ticker(symbol: str, market: str, sprint: str, reason: str) -> None:
    """Log a broken/insufficient-history ticker to dead_letter_tickers.csv and continue."""
    DEAD_LETTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    file_exists = DEAD_LETTER_FILE.exists()
    with open(DEAD_LETTER_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp_utc", "symbol", "market", "sprint", "reason"])
        writer.writerow(
            [dt.datetime.now(dt.timezone.utc).isoformat(), symbol, market, sprint, reason]
        )
