# Gate decision — WI-010 quarantine classifier consolidation

**Decided:** 2026-10-26, admin "accept all". Gate brief = `reports/wi010_quarantine_consolidated.md`.

## What was decided
1. **Per-row recommendations ACCEPTED** — all report verdicts stand, including the 36
   flips vs the 17/55 WI-008 baseline (full per-symbol table in report §5, flips §6).
   Notable: GME and 7/8 of the 2020-03-09 crash cluster → REINSTATE; ICL/USD and
   HMMC/CAD → FIX_DATA (non-positive closes — repair the data, no reinstate/keep).
2. **OXY/USD residual ACCEPTED** as a conservative keep: its crash level sat near the
   0.25 split fraction (spread 0.327 < 0.35 guard), so the tested rule reads it
   SPLIT_LOOKALIKE → KEEP_QUARANTINED. No tolerance/guard tightening authorized.
3. **Cleanup authorized and executed:** the three deprecated duplicate scripts were
   deleted (`src/final_quarantine_triage.py`, `src/percase_quarantine_triage.py`,
   `src/simple_quarantine_analysis.py`). PM verified after deletion: report
   regenerates exit 0, 38 targeted tests pass, `dead_letter_tickers.csv` sha256
   unchanged.

## What ships
- ONE classifier: `src/quarantine_analysis.py` (tested, re-derived rule).
- ONE entry point: `src/quarantine_triage_report.py` → `reports/wi010_quarantine_consolidated.md`.
- Read-only CB-01 CLEAN_NOW check in `src/verify_synced_data.py` (+11 tests).
- Full suite 223 passed (PM-verified, EXIT:0).

## What doesn't ship / carries forward
- **No quarantine state was changed.** The dead-letter CSV is untouched. Accepting the
  report's recommendations is a *decision record*, not an execution: applying the
  reinstatements (editing `data/dead_letter_tickers.csv` and re-running verification)
  is a separate, explicitly-ordered action — say the word and it becomes a small
  follow-up work item.
- ELE re-download stays admin-owned (Mac/IBKR Gateway).
- ICL + HMMC data repair (non-positive closes) is an open prerequisite before those
  rows can be re-judged.
- TRI/CAD + SPCX/USD: CB-01 CLEAN_NOW ≠ CB-02 cure — their lookback quarantine stands
  unless the CB-02 check is separately cleared.

## GATE DECISION EXECUTED (2026-10-26, same day — admin "apply reinstatements")
The accepted REINSTATE verdicts are now **applied**, not just recorded:
- **47 tickers reinstated** (23 CAD + 24 USD) — removed from the quarantine list;
  they now flow into the feature pipeline again (GME, OVV, the 2020-03-09 crash
  cluster, etc.).
- **25 stay quarantined**: 23 KEEP_QUARANTINED (incl. OXY), 2 FIX_DATA
  (HMMC, ICL — data repair first), and TRI + SPCX whose short-lookback (CB-02)
  quarantine stands.
- New `data/adjudicated_tickers.csv` records all 72 verdicts with citations, and
  `quarantine_ticker` now refuses to re-quarantine a reinstated ticker — the
  next audit cannot bounce them back. Locked by a live test.
- Backup of the pre-edit list: `data/dead_letter_tickers.backup-20261026.csv`.
- Still open for you: HMMC/ICL data repair, ELE re-download (Mac), and TRI/SPCX
  CB-02 clearance if you ever want them back.
