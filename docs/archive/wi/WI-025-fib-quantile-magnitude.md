---
wi_id: WI-025
title: Quantile model of rally (MFE) and drawdown (MAE) on fib bottom events
status: draft
agent: surgical-builder
depends_on: [WI-024]
board_row: "(none yet — PM inserts at morning review; overnight chain 2026-11-06)"
write_files:
  - scripts/fib_quantile_model.py:new
  - tests/test_fib_quantile_model.py:new
read_only_files:
  - scripts/fib_event_features.py
test_command: uv run pytest tests/test_fib_quantile_model.py -q --tb=short --maxfail=1
---

## 1. OBJECTIVE & ARCHITECTURAL INVARIANT
- Predict q10/q50/q90 of 39-day MFE and MAE per bottom event and test against per-ticker historical quantiles. CALIB-only fitting; EVAL scored once; n_jobs=2; float32.

## 2. SURGICAL IMPLEMENTATION BLUEPRINT
- Inputs: `<out>/event_features.parquet` (same feature columns as WI-024, excluding keys), targets fwd_mfe_pct and fwd_mae_pct joined from `trailing_events_w39.csv` on (symbol, date) (`keep_default_na=False, na_values=['']`); drop NaN targets.
- Split: CALIB date < '2022-05-02'; EVAL ≥ '2022-07-01'.
- Model: for each target, XGBRegressor(objective='reg:quantileerror', quantile_alpha=[0.1,0.5,0.9], max_depth=3, n_estimators=300, learning_rate=0.05, min_child_weight=50, n_jobs=2, random_state=0). Sort each row's 3 predictions ascending (no crossing).
- Baseline: per-symbol CALIB empirical q10/q50/q90; symbols with < 20 CALIB events use the global CALIB quantiles.
- Metrics on EVAL, per market {CAD, USD, ALL}, per target: mean pinball loss per alpha (model vs baseline), coverage = share of y within [q10, q90], interval width median.
- Outputs: `<out>/quantile_results.csv`, `<out>/QUANTILE_MODEL.md` ending `VERDICT: PASS` if, for both targets, the model's mean pinball loss (average of 3 alphas) < baseline in CAD AND USD AND coverage within [0.75, 0.85]; else `VERDICT: FAIL`.
- CLI `--out` (default `reports/fib_swings`); env `FIB_SMOKE`. Print `EXIT:0`.
- Tests (synthetic): pinball loss function matches a hand calculation; quantile sort removes crossing; baseline falls back to global for a symbol with 5 events.

## 3. BINARY DEFINITION OF DONE (DoD)
- [ ] Zero edits outside `write_files` (plus this WI file's telemetry footer).
- [ ] `test_command` exits 0.
- [ ] Do NOT run the full job.

## 4. EXECUTION TELEMETRY (Appended on Completion/Block)
- **Attempts:** 1/2 | **Commit:** PENDING | **Status:** DONE
- **Notes / Error Trace:** test_command exit 0 (3 passed). New: scripts/fib_quantile_model.py, tests/test_fib_quantile_model.py. Full job NOT run.
