---
wi_id: WI-021
title: Fold fib pass-4 script into repo and fix outcome accounting
status: draft
agent: surgical-builder
depends_on: []
board_row: "(none yet — PM inserts at morning review; overnight chain 2026-11-06)"
write_files:
  - scripts/fib_walkforward.py:new
  - tests/test_fib_walkforward_accounting.py:new
read_only_files:
  - reports/fib_swings/_src_snapshot/fib_walkforward.py:1-175
test_command: uv run pytest tests/test_fib_walkforward_accounting.py -q --tb=short --maxfail=1
---

## 1. OBJECTIVE & ARCHITECTURAL INVARIANT
- Port the snapshot to `scripts/fib_walkforward.py` (≤250 lines) and fix 5 accounting bugs. Do NOT change: W=39, GRADE_MED=19.5, GRADE_STRONG=33.9, CALIB_END='2022-07-01', RSI formula, event definition, 10-bar clustering, screen thresholds (bottom rsi_f63<42 AND spread15_39<-8; top rsi_f63>58 AND spread15_39>7). Symbol-sequential reads.

## 2. SURGICAL IMPLEMENTATION BLUEPRINT
- Refactor into module-level functions (importable, no work at import time):
  - `symbol_from_path(path) -> (symbol, market)`: basename minus `.parquet`, strip `symbol=` prefix; market = text after `market=` in the parent dir name.
  - `events_for_symbol(df, sym, market) -> list[dict]`: body of the snapshot's per-file loop (lines 46-97). Add keys `market`, `screen_bottom`, `screen_top` (bool; screen_bottom only for type 'bottom', screen_top only for 'top'). **Fix 2:** if the outcome is NaN (bottom: `fwd_mfe_pct`; top: `fwd_mae_pct`) set `grade` to `None`, never 'weak'.
  - `stats(d, side) -> dict`: same keys as the snapshot. **Fix 1:** `ok = outcome.notna()` applied to BOTH base and screened sets. **Fix 4:** outcome hit = `fwd_mfe_pct >= 19.5` for side 'bottom', `fwd_mae_pct <= -19.5` for side 'top'. `n_screened` = all screened rows (resolved or not); rates and medians on resolved rows only. Add key `outcome_metric` ('mfe>=19.5' or 'mae<=-19.5').
  - `main(out_dir)`: **Fix 3:** screen columns exist BEFORE `to_csv`. **Fix 5:** rally priors computed on bottoms with `fwd_mfe_pct.notna()` only. Precision@10 block unchanged.
- CLI: `--out` (default `reports/fib_swings`). Env `FIB_SMOKE=AAPL,RY` → keep only those symbols. Print `EXIT:0` at the end of main.
- Any CSV re-read uses `keep_default_na=False, na_values=['']` (ticker `NA`).
- Tests (synthetic data only, never files from data/): (a) `symbol_from_path('data/raw_ohlcv/market=CAD/symbol=RY.parquet') == ('RY','CAD')`; (b) a 400-bar falling-then-flat series yields at least one bottom event, and every event in the last 39 bars has `grade is None`; (c) `stats` on a hand-made frame (3 resolved base rows, 1 unresolved screened row) uses resolved rows only on both sides; (d) side 'top' uses `fwd_mae_pct`.

## 3. BINARY DEFINITION OF DONE (DoD)
- [ ] Zero edits outside `write_files` (plus this WI file's telemetry footer).
- [ ] `test_command` exits 0.
- [ ] Do NOT run the full-universe job; the orchestrator runs it and checks golden values (EVAL bottom: n_events 20990, n_screened 1056, screen_rate_medplus 0.2959, base 0.2619).

## 4. EXECUTION TELEMETRY (Appended on Completion/Block)
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes / Error Trace:** None
