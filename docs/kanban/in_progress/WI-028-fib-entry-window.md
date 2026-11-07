---
wi_id: WI-028
title: Entry-window measurement — all-bottoms ensemble label under first-touch barrier sim at offset entries
status: draft
agent: surgical-builder
depends_on: [WI-027, WI-023]
board_row: "BOARD.md ACTIVE — DESIGN (research ladder stage 2a, refactored with all-bottoms label)"
write_files:
  - scripts/fib_entry_window.py:new
  - tests/test_fib_entry_window.py:new
read_only_files:
  - scripts/fib_trade_labels.py
  - scripts/fib_walkforward.py
  - reports/fib_swings/trailing_events_w39.csv
  - reports/fib_swings/regime_daily_extended.csv
test_command: uv run pytest tests/test_fib_entry_window.py -q --tb=short --maxfail=1
---

## 1. OBJECTIVE & ARCHITECTURAL INVARIANT
- Run the all-bottoms ensemble trade sim (average ret of all 32 exit policies) at different entry offsets on every trailing bottom: at-bottom (k=0) and delayed (k=3, k=5) with a trailing confirmation rule (no deeper 39d-low within the k-day window). Use the actual first-touch barrier simulation from WI-023 (`simulate()` from `scripts/fib_trade_labels.py`). Report per-offset × per-regime (WI-027 labels) mean ret, hit rate, n trades, and CALIB fold-stability to decide whether delayed entry improves trade outcomes before committing to a confirmation classifier or exit-policy stage. float32 outputs. CALIB only — EVAL reserved for final scoring.

## 2. SURGICAL IMPLEMENTATION BLUEPRINT

### 2a. Label: all-bottoms ensemble ret
- Read `reports/fib_swings/trade_labels_w39.parquet` (already computed by WI-023). For each (symbol, date) bottom event, compute `ensemble_ret = mean(ret)` across all 32 policies. This is the per-event label — no policy selection needed.
- The ensemble IS fold-stable on all-bottoms (5/5 folds, 52,751 CALIB trades) as pre-verified — this WI just varies the entry timing.

### 2b. Entry offsets + confirmation rule
- Per bottom event (all trailing bottoms, type=='bottom', 76,049 events): locate the bar in raw OHLCV by date string. Entry modes:
  - `k=0`: entry = close at event bar (current behavior). Simulate exit using ensemble entry ret across the 32 policies — i.e., for each of the 32 policies, compute `simulate(o,h,l,c,i,entry,target_pct,stop_px,max_days,entry_mode)` and average the 32 returns. (Or equivalently: run each of the 32 simulations, store all returns, then mean per policy.)
  - `k=3` confirmed: seek forward from event bar i; find the earliest bar j ∈ [i+1, i+3] where no NEW 39d-low occurred during [i+1..j] (i.e., `min(low[i+1:j+1]) > low[i]`). Entry = close[j], entry_mode='close'. If no such j exists (the low kept breaking), this k-entry produces NO trade for this event (unresolved).
  - `k=5` confirmed: same rule, window [i+1, i+5].
- Reuse WI-023's `simulate(o, h, l, c, event_index, entry_price, target_pct, stop_px, max_days, 'close')` function imported from `scripts/fib_trade_labels.py`.
- The 32 policies: target ∈ {0.10, 0.15}, stop ∈ {0.05, 0.08, 0.10, 'atr'}, max_days ∈ {20, 39}, entry='close'. ATR14 computed from `scripts/fib_trade_labels.py`'s `atr14()`.

### 2c. Outputs
- `reports/fib_swings/entry_window_labels.parquet`: long-format, one row per (bottom event, policy, k), columns: symbol, market, date, k (0/3/5), policy, ret (float32), reason (category), days (int16). Unresolved → NaN ret. Same format as WI-023's trade_labels but with the added k dimension.
- `reports/fib_swings/entry_window_summary.csv`: grouped by k × regime (WI-027 label, joined from `regime_daily_extended.csv` on market+date) × market (CAD/USD/ALL), CALIB only. Columns: k, regime, market, n, n_resolved, mean_ret, hit_rate (ret>0), median_ret, p10_ret, fold1_mean..fold5_mean (5 contiguous date-block folds on CALIB date-sorted resolved rows), n_folds_pos.
- `reports/fib_swings/ENTRY_WINDOW.md`: table per k with overall (ALL screened + all-bottoms) summary, per-regime breakdown, fold-stability results. Callout: does any k>0 regime produce n_folds_pos==5 where k=0 does not? VERDICT: `RECOMMEND_AT_BOTTOM` if k=0 dominates, `RECOMMEND_DELAYED_k` if a specific k wins on mean_ret + hit_rate + fold-stability, `INCONCLUSIVE` if unclear. Print EXIT:0.

### 2d. CLI
- `--out` (default `reports/fib_swings`), `--smoke` (comma-separated symbols, fallback FIB_SMOKE). Input OHLCV from `data/raw_ohlcv/market=*/symbol=*.parquet`; regime from `data_dir='reports/fib_swings'`.

### 2e. Tests (synthetic only)
- `test_at_bottom_entry`: synthetic 20-bar OHLCV with a known event at i=5, target_hit on bar 12 → at-bottom entry ret matches expected (cost deducted 0.0025).
- `test_delayed_confirmed_entry`: synthetic where low holds for 3 days → k=3 entry = close[8]; a stop hit on bar 15 → ret matches expected stop exit with 25bps cost.
- `test_no_confirmation_skips`: synthetic where low breaks on day 2 → k=3 produces no trade (NaN ret); k=0 still produces a trade.
- `test_ensemble_mean`: on a small trade_label DataFrame (synthetic, 4 policies), ensemble_mean = mean of the 4 rets per event to within float32 tolerance.

## 3. BINARY DEFINITION OF DONE (DoD)
- [ ] Zero edits outside `write_files`.
- [ ] `test_command` exits 0.
- [ ] Do NOT run the full-universe job and do NOT read files under `data/` — tests use synthetic data only.

## 4. EXECUTION TELEMETRY (Appended on Completion/Block)
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes / Error Trace:** None