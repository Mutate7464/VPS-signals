---
wi_id: WI-022
title: Regime overlay (R1 vol term structure, R2 breadth63) on fib bottom screen
status: draft
agent: surgical-builder
depends_on: [WI-021, WI-023]
board_row: "(none yet — PM inserts at morning review; overnight chain 2026-11-06)"
write_files:
  - scripts/fib_regime_overlay.py:new
  - tests/test_fib_regime_overlay.py:new
read_only_files:
  - scripts/fib_walkforward.py
test_command: uv run pytest tests/test_fib_regime_overlay.py -q --tb=short --maxfail=1
---

## 1. OBJECTIVE & ARCHITECTURAL INVARIANT
- Test whether 3 pre-registered regime gates improve the frozen bottom screen. Cut points and gate choice from CALIB only; EVAL scored once. Symbol-sequential pass; per-date accumulators only (no all-ticker frame).

## 2. SURGICAL IMPLEMENTATION BLUEPRINT
- Pass A (raw OHLCV, one symbol at a time): per bar `bbw_ratio = (4*std3/mean3)/(4*std39/mean39)` of close (pandas rolling, as in fib_walkforward); `above63 = close > close.rolling(63).mean()` (only where 63 bars exist). Accumulate per (market, date): sum of `log(bbw_ratio)` (finite only), count, n_above63, n_valid63. Market 'ALL' = sum of both. Write `<out>/regime_daily.csv`: market, date, r1 = sum_log/count, r1_s5 = 5-row rolling mean of r1 per market, r2 = n_above63/n_valid63, n_tickers.
- Pass B: join `trailing_events_w39.csv` bottoms (`keep_default_na=False, na_values=['']`) on (market, date) using r1_s5 and r2 of the event's OWN market.
- Periods: CALIB = date < '2022-05-02'; EVAL = date ≥ '2022-07-01'. Resolved = `fwd_mfe_pct` not NaN; outcome = `fwd_mfe_pct >= 19.5`. All rates on resolved rows.
- Terciles: per market, cut points = 1/3 and 2/3 quantiles over CALIB DATES of r1_s5 (and of r2) in regime_daily.csv — dates, not events. Labels T1/T2/T3.
- Candidate allowed sets: {T1},{T2},{T3},{T1,T2},{T2,T3},{T1,T3}. For R1 and R2 separately, on CALIB split into 5 contiguous equal-count date blocks: fold edge = rate(screened AND gated) − rate(all bottoms in fold). Eligible: all 5 fold edges > 0 AND CALIB keep rate (gated screened / screened) ≥ 0.30. Choose max mean fold edge; none eligible → rule 'NONE'. Rule R1R2 = intersection of the two chosen sets (skip if either is NONE).
- If `exit_policy_choice.json` has a non-null policy, also report mean ret for screened vs gated using `trade_labels_w39.parquet` rows of that policy.
- Outputs: `<out>/regime_overlay_results.csv` (rule × period × market: n_bottoms, n_screened, n_gated, keep_rate, base_rate, screen_rate, gated_rate, gated_edge_pp, mean_ret_screened, mean_ret_gated; include rule 'UNGATED'); `<out>/regime_overlay_per_year.csv` (same, per calendar year, market ALL); `<out>/REGIME_OVERLAY.md` listing chosen sets and one line per rule `VERDICT <rule>: PASS|FAIL`, PASS = EVAL ALL (gated_rate − base_rate) ≥ (screen_rate − base_rate) AND 2026 gated edge ≥ 0 AND EVAL keep_rate ≥ 0.30. Final line `VERDICT: PASS` if any rule passes else `VERDICT: FAIL`.
- CLI `--out` (default `reports/fib_swings`); env `FIB_SMOKE`. Print `EXIT:0`.
- Tests (synthetic): tercile cuts unchanged when EVAL rows are altered; breadth on a 3-symbol fixture equals a hand count; 'NONE' returned when no set has 5 positive folds.

## 3. BINARY DEFINITION OF DONE (DoD)
- [ ] Zero edits outside `write_files` (plus this WI file's telemetry footer).
- [ ] `test_command` exits 0.
- [ ] Do NOT run the full job (orchestrator checks UNGATED EVAL ALL screen_rate ≈ 0.2959).

## 4. EXECUTION TELEMETRY (Appended on Completion/Block)
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes / Error Trace:** None
