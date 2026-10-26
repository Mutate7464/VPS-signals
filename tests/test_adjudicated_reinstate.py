"""WI-010 gate follow-through: quarantine_ticker honours adjudicated REINSTATE verdicts.

Admin accepted the WI-010 report 2026-10-26 ("accept all"); 47 tickers were reinstated
by removing their rows from `data/dead_letter_tickers.csv`. These tests lock the
durable part: `quarantine_ticker` must not re-append a gate-reinstated ticker, while
KEEP_QUARANTINED / FIX_DATA / unknown tickers still land in the CSV.
"""

import csv
from pathlib import Path

import pytest

from src import state_manager


@pytest.fixture()
def isolated_data(tmp_path, monkeypatch):
    """Point the state files at a tmp dir; return (dead_letter, adjudicated) paths."""
    dead = tmp_path / "dead_letter.csv"
    adj = tmp_path / "adjudicated.csv"
    monkeypatch.setattr(state_manager, "DEAD_LETTER_FILE", dead)
    monkeypatch.setattr(state_manager, "ADJUDICATED_FILE", adj)
    return dead, adj


def _write_adj(path: Path, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp_utc", "symbol", "market", "verdict", "source"])
        w.writerows(rows)


def _rows(path: Path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def test_reinstate_verdict_skips_quarantine(isolated_data):
    dead, adj = isolated_data
    _write_adj(adj, [["2026-10-26T00:00:00Z", "GME", "USD", "REINSTATE", "wi010"]])
    state_manager.quarantine_ticker("GME", "USD", "EP-01", "UNVERIFIED_CORP_ACTION")
    assert not dead.exists(), "reinstated ticker must not be re-quarantined"


def test_reinstate_verdict_is_case_insensitive(isolated_data):
    dead, adj = isolated_data
    _write_adj(adj, [["t", "gme", "usd", "reinstate", "wi010"]])
    state_manager.quarantine_ticker("GME", "USD", "EP-01", "UNVERIFIED_CORP_ACTION")
    assert not dead.exists()


def test_market_must_match(isolated_data):
    dead, adj = isolated_data
    _write_adj(adj, [["t", "GME", "CAD", "REINSTATE", "wi010"]])
    state_manager.quarantine_ticker("GME", "USD", "EP-01", "UNVERIFIED_CORP_ACTION")
    assert len(_rows(dead)) == 1, "different market has no adjudication"


def test_keep_and_fix_data_still_quarantined(isolated_data):
    dead, adj = isolated_data
    _write_adj(adj, [
        ["t", "OXY", "USD", "KEEP_QUARANTINED", "wi010"],
        ["t", "ICL", "USD", "FIX_DATA", "wi010"],
    ])
    state_manager.quarantine_ticker("OXY", "USD", "EP-01", "UNVERIFIED_CORP_ACTION")
    state_manager.quarantine_ticker("ICL", "USD", "EP-01", "UNVERIFIED_CORP_ACTION")
    assert len(_rows(dead)) == 2


def test_unknown_ticker_still_quarantined(isolated_data):
    dead, adj = isolated_data
    _write_adj(adj, [["t", "GME", "USD", "REINSTATE", "wi010"]])
    state_manager.quarantine_ticker("NEW", "USD", "EP-01", "UNVERIFIED_CORP_ACTION")
    assert len(_rows(dead)) == 1


def test_missing_adjudication_file_quarantines(isolated_data):
    dead, _ = isolated_data
    state_manager.quarantine_ticker("GME", "USD", "EP-01", "UNVERIFIED_CORP_ACTION")
    assert len(_rows(dead)) == 1


def test_corrupt_adjudication_file_quarantines(isolated_data):
    dead, adj = isolated_data
    adj.write_text("not,a,csv\x00binary")
    state_manager.quarantine_ticker("GME", "USD", "EP-01", "UNVERIFIED_CORP_ACTION")
    assert len(_rows(dead)) == 1


def test_existing_dead_letter_rows_never_modified(isolated_data):
    dead, adj = isolated_data
    _write_adj(adj, [["t", "GME", "USD", "REINSTATE", "wi010"]])
    with open(dead, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp_utc", "symbol", "market", "sprint", "reason"])
        w.writerow(["t0", "OXY", "USD", "EP-01", "UNVERIFIED_CORP_ACTION"])
    before = dead.read_bytes()
    state_manager.quarantine_ticker("GME", "USD", "EP-01", "UNVERIFIED_CORP_ACTION")
    assert dead.read_bytes() == before, "skip must not touch the CSV"


def test_live_adjudication_file_blocks_reinstated_bounce():
    """Against the real data/ dir: a reinstated row must not re-append (uses live CSVs)."""
    if not state_manager.ADJUDICATED_FILE.exists():
        pytest.skip("live adjudication file not present")
    before = state_manager.DEAD_LETTER_FILE.read_bytes()
    n_before = len(before.splitlines())
    # GME/USD and OVV/CAD are REINSTATE in the live adjudication file.
    state_manager.quarantine_ticker("GME", "USD", "EP-01", "UNVERIFIED_CORP_ACTION")
    state_manager.quarantine_ticker("OVV", "CAD", "EP-01", "UNVERIFIED_CORP_ACTION")
    # OXY/USD is KEEP_QUARANTINED there; it must append. Remove it again after.
    state_manager.quarantine_ticker("OXY", "USD", "EP-01", "UNVERIFIED_CORP_ACTION")
    after = state_manager.DEAD_LETTER_FILE.read_bytes()
    n_after = len(after.splitlines())
    assert n_after == n_before + 1, "only the KEEP_QUARANTINED ticker may append"
    # restore the file byte-for-byte (the OXY test row is test residue, not state)
    state_manager.DEAD_LETTER_FILE.write_bytes(before)