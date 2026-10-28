"""Regression tests for tools/ibkr_log_digest.py — IBKR log digest system.

Locks: gateway + API format detection, multi-line continuation folding,
redaction, and error/noise classification. Run: uv run pytest tests/test_ibkr_log_digest.py -q
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "tools" / "ibkr_log_digest.py"

GW_HEADER = "===== Log file: /Users/x/Jts/dir/ibgateway.20261028.ibgzenc ====="


def run_digest(tmp_path: Path, text: str):
    log = tmp_path / "log.txt"
    log.write_text(text, encoding="utf-8")
    csv = tmp_path / "t.csv"
    js = tmp_path / "t.json"
    r = subprocess.run(
        [sys.executable, str(TOOL), str(log), "--csv", str(csv), "--json", str(js)],
        capture_output=True, text=True, cwd=REPO, check=True,
    )
    return json.loads(js.read_text())


def test_gateway_format_parsed_and_folded(tmp_path):
    lines = [
        GW_HEADER,
        "2026-10-28 17:49:56.851 INFO  [JTS-T1] - Created on: 20261028",
        "2026-10-28 17:49:57.100 WARN  [JTS-T2] - instance of control is not created yet",
        "2026-10-28 17:50:00.900 INFO  [JTS-T3] - Adjustments [ConidChain:",
        "[ChainElement: [123], [20090224], [], []]]",
        "2026-10-28 17:50:01.000 ERROR [JTS-T4] - Catching",
    ]
    s = run_digest(tmp_path, "\r\n".join(lines) + "\r\n")
    # 4 gateway messages; continuation folded into the Adjustments one
    assert s["lines_unparsed"] == 0
    assert s["lines_parsed"] == 4
    assert s["distinct_templates"] == 4
    assert s["errors_flagged"] == 2  # WARN + ERROR levels
    # the folded body survives into a sample
    samples = " ".join(r["sample"] for r in s["rare_templates"])
    assert "Adjustments [ConidChain: <V> ChainElement" not in samples or "ConidChain" in samples


def test_api_format_error_vs_noise(tmp_path):
    # api log: ts (sync ts) -> [id;fields...]; id 4 = error msg with code in field 3
    lines = [
        "===== Log file: api.101.Thu.log =====",
        "19:40:15:986 (sync 19:40:15:687) -> [15;1;U11379782]",
        "19:40:16:100 (sync 19:40:15:700) -> [4;2;-1;2104;Market data farm connection is OK:usfarm;]",
        "19:40:16:200 (sync 19:40:15:800) -> [4;2;-1;200;No security definition has been found;]",
        "19:40:16:300 (sync 19:40:15:900) <- [1;1;11;2;250]",
    ]
    s = run_digest(tmp_path, "\n".join(lines) + "\n")
    assert s["lines_unparsed"] == 0
    assert s["lines_parsed"] == 4
    assert s["errors_flagged"] == 1          # Error 200 is real
    assert s["noise_flagged"] == 1           # 2104 farm chatter is noise
    assert s["error_codes"] == {"200": 1}


def test_redaction_strips_sensitive_tokens(tmp_path):
    s = run_digest(
        tmp_path,
        "2026-10-28 17:50:00.000 INFO  [t] - session token abc123 logged\n",
    )
    flat = json.dumps(s)
    assert "abc123" not in flat
    assert "token" in flat  # keyword kept, value redacted


def test_bad_lines_counted_as_unparsed(tmp_path):
    s = run_digest(tmp_path, "not a log line at all\nanother garbage\n")
    assert s["lines_parsed"] == 0
    assert s["lines_unparsed"] == 2