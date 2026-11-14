# WI-008 Brief — quarantine triage: per-case verification (evidence, not classes)

Context: 72 symbol/market rows sit in `data/dead_letter_tickers.csv` (70 CB-01
single-day |ret| triggers, 2 CB-02 short history). A read-only classifier
(`reports/wi008_quarantine_triage.md`, 2026-10-23) tagged them SPLIT_LOOKALIKE (44) /
GENUINE_VOL (26) / CLEAN_NOW (2). **The classifier is a hypothesis generator, not
evidence** — it has at least two known contradictions:

1. **2020-03-09 cluster (COVID/oil crash) split inconsistently**: OVV (CAD+USD) and WES
   → GENUINE_VOL, while CVE (CAD+USD), APA, OXY, MTDR, PR, SM on the *same date* →
   SPLIT_LOOKALIKE. These are almost certainly all genuine crash moves, not corp actions.
2. **GME → SPLIT_LOOKALIKE** (2021-01-27, +134%) is the meme squeeze — genuine.
   **GOOG 2014-04-03 (+101%)** coincides with the Class C share structure event — corp
   action territory. **ICL has negative prices** (−381M close) — data corruption, not a split.

## Goal

Produce `reports/wi008_quarantine_percase_evidence.md`: one row per dead-letter
symbol/market with defensible evidence and a recommended action
(REINSTATE / KEEP_QUARANTINED / FIX_DATA / OWNER_ACTION), for a human reinstate/keep gate.
**No mutation of quarantine state, dead_letter file, or verifier config in this work item.**

## Method (per row)

- Level-step test: ratio of median close over [spike+5, spike+20] vs median over
  [spike−20, spike−2]. A permanent level shift with a clean ratio near a simple fraction
  (≈2, ≈0.5, ≈4 …) = corp-action artifact; reversion toward pre-spike level = genuine vol.
- Volume corroboration: median volume ratio (post/pre). Splits leave volume stepping too.
- Multi-day path: spike isolated (1–2 days) vs continuation/reversal regime.
- Where the level test is ambiguous, mark `AMBIGUOUS — needs external corp-action record`;
  do NOT resolve it by assumption. Web lookups are out of scope; leave the cell for the admin.
- CLEAN_NOW rows (SPCX USD, TRI CAD): re-run `uv run python -m src.verify_synced_data` and
  confirm they still pass CB-01 today before recommending REINSTATE.

## Known anchors (use as calibration, verify don't assume)

- 2020-03-09 energy/financials cluster (OVV, WES, CVE×2, APA, OXY, MTDR, PR, SM): genuine.
- GME 2021-01: genuine. GOOG 2014-04: verify the level step (Class C event) — likely artifact.
- ICL: negative prices → FIX_DATA (bad rows), not a return-spike case at all.
- ELE (TSE): no parquet. **OWNER_ACTION — admin re-downloads on Mac via IBKR Gateway.**
  Out of Build scope; just flag it in the report.

## Constraints

- AGENTS.md: n_jobs ≤ 2, float32, bounded memory (<2 GB), no secrets, no live trading.
- Read parquets with Arrow column scans (see `rank_assets.py` post-fix pattern) — do not
  load all 896 files into one frame.
- `uv run python -m src.verify_synced_data` is the only verifier; do not fork a second one.
- Reuse `src/verify_synced_data.py:153` CB-01 logic definitions; cite line numbers in the report.
- Tests: any new helper (e.g. the level-step test) gets a unit test with synthetic
  step-vs-reversal fixtures. Full pytest suite must stay green (56 baseline).

## Acceptance

- Report row count == unique symbol/market rows in dead_letter (72), plus summary verdict counts.
- Every REINSTATE recommendation cites the level-step numbers that justify it.
- Ambiguities are explicit, not silently classed.
- `uv run pytest -q` green; new helper tests included.
- STATUS line in the plan file per contract; board + EXECUTION LOG updated by Build.

## Out of scope

Reinstatement execution (human gate after this report), ELE download, WI-009b.
