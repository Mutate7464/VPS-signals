---
wi_id: WI-027
title: Rule-based point-in-time regime labels → conditional edge table (stage 1 of fib research ladder WI-027→030)
status: draft
agent: surgical-builder
depends_on: [WI-022]
board_row: "BOARD.md ACTIVE — DESIGN (admin direction 2026-11-07, research ladder stage 1)"
write_files:
  - scripts/fib_regime_labels.py:new
  - tests/test_fib_regime_labels.py:new
read_only_files:
  - scripts/fib_regime_overlay.py
  - scripts/fib_walkforward.py
  - reports/fib_swings/trailing_events_w39.csv
  - reports/fib_swings/regime_daily.csv
test_command: uv run pytest tests/test_fib_regime_labels.py -q --tb=short --maxfail=1
---

## 1. OBJECTIVE & ARCHITECTURAL INVARIANT
- Extend the existing binary regime gate (R1R2, WI-022) to a 3×2 categorical regime label per (market, date): trend {up, down, chop} × volatility {normal, high}. All categories computed point-in-time from trailing windows only — no future data anywhere. Output a conditional edge table showing the bottom screen's per-regime performance on CALIB (date < 2022-05-02), fold-stable (5 contiguous date blocks, same machinery as WI-023). float32 output, n_jobs=2, symbol-sequential reads where applicable.

## 2. SURGICAL IMPLEMENTATION BLUEPRINT

### 2a. Trend category (up / down / chop)
- Per market, per date: compute trailing 63-trading-day return and trailing 126-trading-day return from the market-level close (cross-sectional mean or median close — use `regime_daily.csv`'s existing per-date structure; falls back to the ALL pool if market column not computable). The raw OHLCV reader reuses the symbol-sequential loop from `scripts/fib_regime_overlay.py` (already reads `data/raw_ohlcv/market=<M>/symbol=<S>.parquet`).
- `up` = both trailing returns > 0 AND 63d return > 0.001 (flat-noise filter).
- `down` = both trailing returns < 0 AND 63d return < −0.001.
- `chop` = everything else (mixed signs or near-zero).
- These are point-in-time: at date t, only data from ≤ t is used.

### 2b. Volatility category (normal / high)
- Per market, per date: compute `atrp63` (Wilder ATR(63) / close) and `vol21` (std of 21-bar log returns × √252) cross-sectional median across active tickers that date.
- Cut point: CALIB-date median of each series, frozen (computed on dates < 2022-05-02, never updated).
- `high` = BOTH atrp63 and vol21 > their CALIB-frozen medians.
- `normal` = all other dates.
- These indicators already exist in the repo (`scripts/fib_walkforward.py` has the RSI and ATR helpers; `regime_daily.csv` has r1/r1_s5/r2 — this WI adds new columns to the same structure without replacing them).

### 2c. Output 1: `reports/fib_swings/regime_daily_extended.csv`
- Same row structure as `regime_daily.csv` (market, date, columns), extended with: `trend` (str: up/down/chop), `vol_cat` (str: normal/high), `regime` (str: concat of trend_vol, e.g. "up_normal").
- Append, never replace — the existing r1/r1_s5/r2/n_tickers columns are untouched.

### 2d. Output 2: `reports/fib_swings/regime_conditional_edge.csv`
- Join `trailing_events_w39.csv` (type == 'bottom') with `regime_daily_extended.csv` on (market, date). Columns: regime, market (CAD/USD/ALL), n_events, n_screened (screen_bottom==True), screen_rate, base_rate_medplus (global share of CALIB resolved bottoms with grade >= med), screen_rate_medplus, edge_pp (screen − base), mean_39d_fwd_ret (fwd_ret_pct column from events, resolved only), fwd_ret_fold1_mean..fold5_mean (5 contiguous date-block folds of resolved bottom events, date-sorted, same fold machinery as WI-023 `scripts/fib_trade_labels.py:162-174` — reuse the `group_stats(g, period)` function), n_folds_pos.
- CALIB only: date < '2022-05-02' (same embargo as WI-023). EVAL is NOT computed (reserved for later stages).
- Per-market (CAD, USD) and pooled (ALL). Pooled is the headline; per-market is descriptive (markets assumed different per standing repo rule).

### 2e. Output 3: `reports/fib_swings/REGIME_LABELS.md`
- Summary text file: table of regime categories × market with n_events, screened rate, edge_pp, n_folds_pos. Callout for fold5 (the fatal fold from the overnight chain) — which regime(s) does fold5's date range (2020-01→2022-04) map to? State whether that regime's fold-stability FAILS (as expected) and whether any other regime shows fold-stability (n_folds_pos==5), which is the acceptance condition.
- `VERDICT: PASS` if ≥1 regime × market has n_folds_pos==5 for screened events AND fold5 is isolated to identifiable regime(s). `VERDICT: FAIL` otherwise.
- Print `EXIT:0` at end regardless (this is a descriptive result, not a blocker).

### 2f. CLI
- `--out` (default `reports/fib_swings`), `--smoke` (env `FIB_SMOKE`, comma-separated symbols — limits the regime daily computation to those symbols, skipping the full universe read; fallback to FIB_SMOKE env var). No separate `--embargo` flag — CALIB < '2022-05-02' is hardcoded.

### 2g. Tests (synthetic only, no data/ reads)
- `test_trend_categories`: trailing-return arrays produce correct up/down/chop classification at each date; flat-noise filter (|ret|<0.001 maps to chop); point-in-time assertion (label at t uses only rows ≤ t — test with a mock that calls the category function per row and verifies it doesn't access future indices).
- `test_vol_categories`: ATR/vol arrays with known medians produce correct normal/high split; frozen cut point (not recomputed on EVAL dates).
- `test_regime_join`: synthetic events frame + regime frame merge correctly; fold computation reuses the imported `group_stats` — verify fold count and sign agreement.
- `test_fold5_isolation`: synthetic regime labels where fold5 dates fall in one regime category and that regime fails fold-stability while others pass → VERDICT PASS detection.

## 3. BINARY DEFINITION OF DONE (DoD)
- [ ] Zero edits outside `write_files`.
- [ ] `test_command` exits 0.
- [ ] Do NOT run the full-universe job and do NOT read files under `data/` — tests use synthetic data only.

## 4. EXECUTION TELEMETRY (Appended on Completion/Block)
- **Attempts:** 1/2 | **Commit:** PENDING | **Status:** DONE
- **Notes / Error Trace:** None. `test_command` (`uv run pytest tests/test_fib_regime_labels.py -q --tb=short --maxfail=1`) passed on the first run — 4 passed, exit 0; two subsequent re-runs after line-count compliance rewrites (375→241 lines, behavior identical) also 4 passed. Files (both new, within write_files): `scripts/fib_regime_labels.py` (241 lines: trend 63/126d point-in-time labels with 0.001 flat-noise + ALL-pool fallback; atrp63/vol21 cross-sectional medians with CALIB-frozen (<2022-05-02) median cuts; regime_daily_extended.csv append-only; regime_conditional_edge.csv CALIB-only with WI-023 group_stats fold reuse; REGIME_LABELS.md + VERDICT + EXIT:0; --out/--smoke CLI with FIB_SMOKE fallback) and `tests/test_fib_regime_labels.py` (190 lines, 4 synthetic-only tests: trend categories incl. point-in-time index probe, vol categories incl. frozen-cut check, regime join incl. group_stats spy + fold sign agreement, fold5 isolation → PASS detection with 2 FAIL controls). Full-universe job NOT run (per DoD); no data/ reads; no files outside write_files touched.