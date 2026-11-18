# WI-010b — reinstate execution (admin order "apply reinstatements", 2026-10-26)

> PM-executed follow-through on the accepted WI-010 gate ("accept all").
> No new plan: single mechanical edit + durable skip, recorded here.

## What was executed
- `data/dead_letter_tickers.csv`: 72 → 25 rows. Removed the 47 REINSTATE rows
  (23 CAD + 24 USD) per the accepted `reports/wi010_quarantine_consolidated.md` §5.
  Kept rows byte-identical (CRLF preserved); backup at
  `data/dead_letter_tickers.backup-20261026.csv`.
- Kept (25): 21 KEEP_QUARANTINED + OXY/USD (KEEP) already counted, HMMC/CAD + ICL/USD
  (FIX_DATA — data repair prerequisite), TRI/CAD + SPCX/USD (classifier REINSTATE
  but CB-02 quarantine stands — CLEAN_NOW cannot clear CB-02).
- `data/adjudicated_tickers.csv`: NEW — full 72-row adjudication record
  (timestamp, symbol, market, verdict, source citation incl. CB-02 notes).
- `src/state_manager.py`: `is_adjudicated_reinstate()` + skip in `quarantine_ticker`
  — a gate-reinstated ticker can never bounce back into the dead-letter CSV on a
  later audit (CB-01 spikes would otherwise re-append it). Read-only lookup,
  case-insensitive, OSError-safe.
- `tests/test_adjudicated_reinstate.py`: 9 tests incl. a LIVE test against the real
  data dir (reinstated no-append, KEEP still appends, CSV restored byte-for-byte).

## Verification (PM, 2026-10-26)
- Targeted: `tests/test_adjudicated_reinstate.py` + `test_quarantine_analysis.py` +
  `test_verify_synced_data.py` → **47 passed**.
- Consumer sanity: `feature_engine.load_quarantine` → CAD 12 + USD 13 excluded
  (= 25 kept); GME/USD no longer excluded; OXY/USD still excluded.
- Full suite: see STATUS line below (detached `logs/wi010b_full_suite.out`).
- Pre-existing wart (out of scope, flagged): `verify_synced_data` main() blind-appends
  the 25 kept rows on every real-data audit run (no dedupe) — file grew to 72 exactly
  because audits were run once. Candidate tiny hygiene WI if it bites.

STATUS: DONE (47 reinstated applied; adjudication skip locked by live test; PM-verified; full suite 232 passed EXIT:0 — logs/wi010b_full_suite.out)