---
wi_id: WI-023
title: First-touch trade labels and exit-policy grid for fib trailing bottoms
status: draft
agent: surgical-builder
depends_on: [WI-021]
board_row: "(none yet — PM inserts at morning review; overnight chain 2026-11-06)"
write_files:
  - scripts/fib_trade_labels.py:new
  - tests/test_fib_trade_labels.py:new
read_only_files:
  - scripts/fib_walkforward.py
test_command: uv run pytest tests/test_fib_trade_labels.py -q --tb=short --maxfail=1
---

## 1. OBJECTIVE & ARCHITECTURAL INVARIANT
- Simulate a fixed exit-policy grid on every trailing-bottom event from raw OHLCV (one symbol at a time), write per-event trade returns, summarize, and choose ONE policy using calibration data only. No policy is chosen or tuned on EVAL. float32 outputs.

## 2. SURGICAL IMPLEMENTATION BLUEPRINT
- Inputs: `reports/fib_swings/trailing_events_w39.csv` (read with `keep_default_na=False, na_values=['']`; rows `type=='bottom'`; columns symbol, market, date, screen_bottom); raw `data/raw_ohlcv/market=<M>/symbol=<S>.parquet` (date, open, high, low, close). Match event to bar by date string `YYYY-MM-DD`.
- `simulate(o, h, l, c, i, entry, tgt_pct, stop_px, max_days, entry_mode) -> (ret, reason, days)`. Target `T = entry*(1+tgt_pct)`; stop `S = stop_px`. If `i+max_days >= len(c)` → return `(nan, 'unresolved', 0)`. Loop `j = i+1 .. i+max_days`:
  1. if entry_mode=='close' or j>i+1: if `o[j] <= S` → exit `o[j]`, 'stop_gap'; elif `o[j] >= T` → exit `o[j]`, 'target_gap'.
  2. if `l[j] <= S and h[j] >= T` → exit `S`, 'stop_tie' (conservative).
  3. elif `l[j] <= S` → exit `S`, 'stop'; elif `h[j] >= T` → exit `T`, 'target'.
  4. after the loop → exit `c[i+max_days]`, 'time'.
  `ret = exit/entry - 1 - 0.0025` (25 bps round-trip cost assumption). `days = j - i` (time exit: max_days).
- Entry modes: 'close' → entry `c[i]`; 'next_open' → entry `o[i+1]` (gap rule skipped on bar i+1).
- Stops: fixed 0.05/0.08/0.10 → `S = entry*(1-s)`; 'atr1.5' → `S = entry - 1.5*ATR14[i]`, ATR14 Wilder: TR = max(h-l, |h-c_prev|, |l-c_prev|), `ewm(alpha=1/14, adjust=False).mean()`.
- Grid (32 policies): target {0.10, 0.15} × stop {0.05, 0.08, 0.10, atr1.5} × max_days {20, 39} × entry {close, next_open}. Policy id format `t10_s8_d39_close`, `t15_satr_d20_next_open`.
- Output 1 `<out>/trade_labels_w39.parquet`, long format, one row per (bottom event, policy), ALL bottoms kept (unresolved → NaN ret): symbol, market, date, screen_bottom, policy, ret (float32), reason (category), days (int16).
- Output 2 `<out>/exit_policy_grid.csv`: groups policy × period {CALIB, EVAL} × market {CAD, USD, ALL} × set {all, screened}; resolved rows only. CALIB = date < '2022-05-02' (embargo for the 39-day label); EVAL = date ≥ '2022-07-01'. Columns: policy, period, market, set, n, hit_rate (reason in target/target_gap), mean_ret, median_ret, p10_ret, max_consec_losses (rows sorted by date, ret<0), fold1_mean..fold5_mean (CALIB only: 5 contiguous equal-count blocks after sorting by date), n_folds_pos.
- Output 3 `<out>/exit_policy_choice.json`: among CALIB, market ALL, set screened: eligible if mean_ret ≥ 0.005 AND n_folds_pos == 5; choose max mean_ret (tie → smaller stop). Write `{"policy": id or null, "reason": "...", "calib_mean_ret": x}`; null reason "NO_POLICY_CLEARS".
- CLI `--out` (default `reports/fib_swings`); env `FIB_SMOKE=AAPL,RY`. Print `EXIT:0` at the end.
- Tests (synthetic 10-bar arrays): target-first; stop-first; open gaps below stop → 'stop_gap' at the open price; same bar touches both → 'stop_tie'; neither → 'time' at close; too few bars → 'unresolved'; cost deducted exactly 0.0025.

## 3. BINARY DEFINITION OF DONE (DoD)
- [ ] Zero edits outside `write_files` (plus this WI file's telemetry footer).
- [ ] `test_command` exits 0.
- [ ] Do NOT run the full job (orchestrator checks: policy t10_s8_d39_close, EVAL, ALL, screened → n 1007, hit_rate within [0.403, 0.712]).

## 4. EXECUTION TELEMETRY (Appended on Completion/Block)
- **Attempts:** 1/2 | **Commit:** PENDING (left for Hermes) | **Status:** DONE
- **Notes / Error Trace:** First test run: 6/7 passed; `test_cost_deducted_exactly` failed because synthetic `h[1]=110.0` sits below the float64 target `T=100*(1+0.10)=110.00000000000001` (test-data bug, implementation matches blueprint). One fix: test bar changed to `h[1]=111.0`. Second run: `uv run pytest tests/test_fib_trade_labels.py -q --tb=short --maxfail=1` → 7 passed, exit 0. Full job NOT run per DoD; no edits outside write_files.
