---
wi_id: WI-024
title: Event feature table and meta-label filter on fib bottom events
status: draft
agent: surgical-builder
depends_on: [WI-023, WI-022]
board_row: "(none yet — PM inserts at morning review; overnight chain 2026-11-06)"
write_files:
  - scripts/fib_event_features.py:new
  - scripts/fib_meta_model.py:new
  - tests/test_fib_meta_model.py:new
read_only_files:
  - scripts/fib_walkforward.py
test_command: uv run pytest tests/test_fib_meta_model.py -q --tb=short --maxfail=1
---

## 1. OBJECTIVE & ARCHITECTURAL INVARIANT
- Build one feature row per trailing bottom, then test whether Ridge or a shallow XGBoost regressor picks better trades than the frozen screen at the SAME trade volume. Train on CALIB only; EVAL scored once. n_jobs=2. float32 features. Fixed feature list — no additions.

## 2. SURGICAL IMPLEMENTATION BLUEPRINT
- `fib_event_features.py` → `<out>/event_features.parquet`, one row per bottom in `trailing_events_w39.csv` (all bottoms; read with `keep_default_na=False, na_values=['']`). Keys symbol, market, date. Features: rsi_f63, spread15_39, bbw_ratio (copied from the events file); computed per symbol from raw OHLCV using `rsi` imported from `scripts/fib_walkforward.py`: `rsi24_39 = rsi(c,24)-rsi(c,39)`, `rsi15_slope5 = rsi(c,15) - rsi(c,15).shift(5)`, `dd63 = c/c.rolling(63).max() - 1`, `dd63_days` = bars since the 63-bar max, `days_since_prev_bottom` (bars since the same symbol's previous bottom event; NaN if none), `mom_12_1 = c.shift(21)/c.shift(252) - 1`, `vol21` = std of log returns over 21 bars × sqrt(252), `atrp63` = Wilder ATR(63)/close; `r1_s5`, `r2` joined from `regime_daily.csv` (own market); `prior_p_medplus` = per-symbol share of `fwd_mfe_pct >= 19.5` over that symbol's CALIB (date < '2022-05-02') resolved bottoms, shrunk `(k + 10*g)/(n + 10)`, g = global CALIB share; `is_usd` (1/0); `screen_bottom` (1/0).
- `fib_meta_model.py`: read `exit_policy_choice.json`. If policy is null → write `META_MODEL.md` with `VERDICT: BLOCKED_PRECONDITION (no exit policy cleared)`, print `EXIT:0`, stop. Else y = ret of that policy from `trade_labels_w39.parquet`, clipped to [-0.15, 0.15]; drop NaN y.
- Split: CALIB date < '2022-05-02'; EVAL ≥ '2022-07-01'. Impute NaN with CALIB medians for Ridge only (XGBoost takes NaN).
- Models: (a) SCREEN: score = screen_bottom − 0.001*rsi_f63. (b) RIDGE: StandardScaler + Ridge(alpha=1.0). (c) XGB: XGBRegressor(max_depth=3, n_estimators=300, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, min_child_weight=50, n_jobs=2, random_state=0), monotone −1 on rsi_f63 and spread15_39, 0 elsewhere.
- Equal-volume selection: select on EVAL the events whose score is ≥ the CALIB score quantile that reproduces the screen's CALIB flag rate (share of CALIB bottoms with screen_bottom==1). Per model report: n_selected, mean_ret, hit_rate (ret>0), Spearman(pred, y) on EVAL, per-year mean_ret, per-market mean_ret.
- CALIB sanity CV: 5 contiguous date blocks; train on the others minus rows within 60 calendar days of the test block; report fold Spearman for (b) and (c).
- Permutation null for (c): 20 reps, shuffle y within date on CALIB, retrain, record EVAL selected mean_ret.
- Outputs: `<out>/meta_model_results.csv`, `<out>/META_MODEL.md` ending `VERDICT: PASS` if XGB mean_ret − SCREEN mean_ret ≥ 0.005 AND XGB EVAL Spearman > 0 AND XGB beats ≥ 19 of 20 null reps; else `VERDICT: FAIL`. Also state Ridge vs SCREEN. Log peak RSS (psutil).
- CLI `--out` (default `reports/fib_swings`) on both scripts; env `FIB_SMOKE`. Print `EXIT:0`.
- Tests (synthetic): purge removes rows within 60 days of a test block; prior_p_medplus ignores EVAL rows; monotone vector length == feature count; null policy writes the BLOCKED_PRECONDITION verdict.

## 3. BINARY DEFINITION OF DONE (DoD)
- [ ] Zero edits outside `write_files` (plus this WI file's telemetry footer).
- [ ] `test_command` exits 0. Each script ≤ 250 lines.
- [ ] Do NOT run the full job.

## 4. EXECUTION TELEMETRY (Appended on Completion/Block)
- **Attempts:** 2/2 | **Commit:** PENDING | **Status:** DONE (tests green; PM to commit)
- **Notes / Error Trace:** 1st run smoke failed: `KeyError: 'symbol'` at fib_event_features.py:108 — `rows` was empty because the event loop did `d = str(d)` on `iterrows()`'s integer row index instead of the event date, so `pos.get(d)` never matched and every event was skipped. Fix: `d = str(erow['date'])` (line 94-95 only change). Smoke `FIB_SMOKE=AAPL,MSFT,NVDA,JPM,XOM,RY,TD,SHOP,CNQ,ENB --out /tmp/opencode/wi024` → 1113 rows, EXIT:0. `uv run pytest tests/test_fib_meta_model.py -q --tb=short --maxfail=1` → 4 passed. Files: scripts/fib_event_features.py (129), scripts/fib_meta_model.py (228), tests/test_fib_meta_model.py (57). Zero edits outside write_files. Full-universe job NOT run; data/ and large reports/ files NOT read.
