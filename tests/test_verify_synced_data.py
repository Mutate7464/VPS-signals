"""Unit tests for the read-only CB-01 CLEAN_NOW check in `verify_synced_data`.

The check re-tests dead-letter tickers against the CB-01 thresholds (>+100% or
<-50% single-day return) using the on-disk parquet only. These tests lock the
read-only contract: `data/dead_letter_tickers.csv` must be byte-identical after
the check, and the quarantine mutation path (`quarantine_ticker`) must never be
called.
"""

import hashlib

import numpy as np
import pandas as pd
import pytest

import src.verify_synced_data as vsd


def _write_parquet(root, market, symbol, closes):
    """Write a minimal OHLCV parquet for `symbol` under `root`."""
    out_dir = root / f"market={market}"
    out_dir.mkdir(parents=True, exist_ok=True)
    n = len(closes)
    closes = np.asarray(closes, dtype="float32")
    df = pd.DataFrame(
        {
            "date": pd.bdate_range("2020-01-01", periods=n),
            "open": closes,
            "high": closes,
            "low": closes,
            "close": closes,
            "volume": np.full(n, 1000.0, dtype="float32"),
        }
    )
    path = out_dir / f"symbol={symbol}.parquet"
    df.to_parquet(path, index=False)
    return path


def _write_dead_letter(root, rows):
    """Write a dead-letter CSV copy (read-only input for the check)."""
    path = root / "dead_letter_tickers.csv"
    lines = ["timestamp_utc,symbol,market,sprint,reason"]
    lines += [
        f"2026-10-22T00:00:00+00:00,{symbol},{market},EP-01,{reason}"
        for symbol, market, reason in rows
    ]
    path.write_text("\n".join(lines) + "\n")
    return path


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# CLEAN_NOW / SPIKE classification
# --------------------------------------------------------------------------- #
def test_clean_ticker_is_clean_now(tmp_path):
    dead_letter = _write_dead_letter(
        tmp_path, [("CLEAN", "USD", "UNVERIFIED_CORP_ACTION")]
    )
    _write_parquet(tmp_path, "USD", "CLEAN", [10.0 + 0.1 * i for i in range(30)])

    results = vsd.cb01_clean_now_check(dead_letter_path=dead_letter, raw_dir=tmp_path)

    assert len(results) == 1
    assert results[0]["symbol"] == "CLEAN"
    assert results[0]["status"] == "CLEAN_NOW"
    assert results[0]["clean_now"] is True


def test_positive_cb01_spike_is_not_clean_now(tmp_path):
    dead_letter = _write_dead_letter(tmp_path, [("SPIKE", "USD", "UNVERIFIED_CORP_ACTION")])
    _write_parquet(tmp_path, "USD", "SPIKE", [10.0] * 5 + [21.0] * 25)

    results = vsd.cb01_clean_now_check(dead_letter_path=dead_letter, raw_dir=tmp_path)

    assert results[0]["status"] == "SPIKE"
    assert results[0]["clean_now"] is False


def test_negative_cb01_spike_is_not_clean_now(tmp_path):
    dead_letter = _write_dead_letter(tmp_path, [("DROP", "CAD", "UNVERIFIED_CORP_ACTION")])
    _write_parquet(tmp_path, "CAD", "DROP", [10.0] * 5 + [4.0] * 25)

    results = vsd.cb01_clean_now_check(dead_letter_path=dead_letter, raw_dir=tmp_path)

    assert results[0]["status"] == "SPIKE"
    assert results[0]["clean_now"] is False


def test_thresholds_match_cb01_definition():
    ok = pd.DataFrame({"close": np.asarray([10.0, 19.9, 19.9], dtype="float32")})
    upper = pd.DataFrame({"close": np.asarray([10.0, 20.1, 20.1], dtype="float32")})
    lower = pd.DataFrame({"close": np.asarray([10.0, 4.9, 4.9], dtype="float32")})

    assert vsd.CB01_UPPER_RETURN == 1.0
    assert vsd.CB01_LOWER_RETURN == -0.5
    assert vsd.cb01_spike_flag(ok) is False
    assert vsd.cb01_spike_flag(upper) is True
    assert vsd.cb01_spike_flag(lower) is True
    assert vsd.cb01_spike_flag(pd.DataFrame({"close": np.asarray([10.0], dtype="float32")})) is False


# --------------------------------------------------------------------------- #
# Missing / unreadable parquet
# --------------------------------------------------------------------------- #
def test_missing_parquet_reports_no_file(tmp_path):
    dead_letter = _write_dead_letter(tmp_path, [("GONE", "USD", "UNVERIFIED_CORP_ACTION")])

    results = vsd.cb01_clean_now_check(dead_letter_path=dead_letter, raw_dir=tmp_path)

    assert results[0]["status"] == "NO_FILE"
    assert results[0]["clean_now"] is False


def test_unreadable_parquet_reports_read_error(tmp_path):
    dead_letter = _write_dead_letter(tmp_path, [("BROKEN", "USD", "UNVERIFIED_CORP_ACTION")])
    bad_dir = tmp_path / "market=USD"
    bad_dir.mkdir(parents=True, exist_ok=True)
    (bad_dir / "symbol=BROKEN.parquet").write_bytes(b"not a parquet file")

    results = vsd.cb01_clean_now_check(dead_letter_path=dead_letter, raw_dir=tmp_path)

    assert results[0]["status"] == "READ_ERROR"
    assert results[0]["clean_now"] is False
    assert results[0]["detail"]


def test_mixed_rows_each_keep_their_own_status(tmp_path):
    dead_letter = _write_dead_letter(
        tmp_path,
        [
            ("CLEAN", "USD", "UNVERIFIED_CORP_ACTION"),
            ("SPIKE", "USD", "UNVERIFIED_CORP_ACTION"),
            ("GONE", "USD", "UNVERIFIED_CORP_ACTION"),
        ],
    )
    _write_parquet(tmp_path, "USD", "CLEAN", [10.0 + 0.1 * i for i in range(30)])
    _write_parquet(tmp_path, "USD", "SPIKE", [10.0] * 5 + [21.0] * 25)

    results = vsd.cb01_clean_now_check(dead_letter_path=dead_letter, raw_dir=tmp_path)

    assert [r["symbol"] for r in results] == ["CLEAN", "SPIKE", "GONE"]
    assert [r["status"] for r in results] == ["CLEAN_NOW", "SPIKE", "NO_FILE"]


# --------------------------------------------------------------------------- #
# Read-only contract
# --------------------------------------------------------------------------- #
def test_dead_letter_csv_bytes_preserved(tmp_path):
    dead_letter = _write_dead_letter(
        tmp_path, [("CLEAN", "USD", "UNVERIFIED_CORP_ACTION")]
    )
    _write_parquet(tmp_path, "USD", "CLEAN", [10.0 + 0.1 * i for i in range(30)])
    before = _sha256(dead_letter)

    vsd.cb01_clean_now_check(dead_letter_path=dead_letter, raw_dir=tmp_path)

    assert _sha256(dead_letter) == before


def test_never_calls_quarantine_mutator(tmp_path, monkeypatch):
    dead_letter = _write_dead_letter(
        tmp_path,
        [
            ("CLEAN", "USD", "UNVERIFIED_CORP_ACTION"),
            ("SPIKE", "USD", "UNVERIFIED_CORP_ACTION"),
            ("GONE", "USD", "UNVERIFIED_CORP_ACTION"),
        ],
    )
    _write_parquet(tmp_path, "USD", "CLEAN", [10.0 + 0.1 * i for i in range(30)])
    _write_parquet(tmp_path, "USD", "SPIKE", [10.0] * 5 + [21.0] * 25)

    def _forbidden(*args, **kwargs):
        pytest.fail("CB-01 CLEAN_NOW check must not touch the quarantine mutation path")

    monkeypatch.setattr(vsd, "quarantine_ticker", _forbidden)

    vsd.cb01_clean_now_check(dead_letter_path=dead_letter, raw_dir=tmp_path)


def test_read_dead_letter_rows_is_read_only(tmp_path):
    dead_letter = _write_dead_letter(tmp_path, [("CLEAN", "USD", "UNVERIFIED_CORP_ACTION")])
    before = _sha256(dead_letter)

    rows = vsd.read_dead_letter_rows(dead_letter)

    assert rows[0]["symbol"] == "CLEAN"
    assert rows[0]["market"] == "USD"
    assert _sha256(dead_letter) == before


def test_real_dead_letter_file_is_never_modified():
    """Guardrail: the repo's dead-letter CSV is byte-identical after a real run."""
    if not vsd.DEAD_LETTER_PATH.exists():
        pytest.skip("no data/dead_letter_tickers.csv in this checkout")
    before = _sha256(vsd.DEAD_LETTER_PATH)

    results = vsd.cb01_clean_now_check()

    assert results
    assert all(r["status"] in {"CLEAN_NOW", "SPIKE", "NO_FILE", "READ_ERROR"} for r in results)
    assert _sha256(vsd.DEAD_LETTER_PATH) == before


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
