---
wi_id: WI-030
title: Learned conditional exit policy — per-event (target, stop, max_days) from features + regime on the all-bottoms ensemble label
status: draft
agent: surgical-builder
depends_on: [WI-027, WI-028, WI-025, WI-023]
board_row: "BOARD.md ACTIVE — EXECUTING (fib research ladder stage 3)"
write_files:
  - scripts/fib_exit_policy.py:new
  - tests/test_fib_exit_policy.py:new
read_only_files:
  - scripts/fib_meta_model.py
  - scripts/fib_trade_labels.py
  - scripts/fib_quantile_model.py
  - reports/fib_swings/trade_labels_w39.parquet
  - reports/fib_swings/event_features.parquet
  - reports/fib_swings/regime_daily_extended.csv
  - reports/fib_swings/quantile_results.csv
test_command: uv run pytest tests/test_fib_exit_policy.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
Learn a per-event exit-policy chooser: predict the best 32-cell grid cell (target × stop × max_days) per bottom event from features (event_features + WI-027 regime) + per-event horizon from the WI-025 quantile priors, replacing the frozen grid. Invariants: n_jobs=2, float32 immediately after calc, symbol-sequential reads, CALIB-only learning, EVAL touched exactly once at final scoring.

## 2. I/O contract and blueprint
- Input: `reports/fib_swings/trade_labels_w39.parquet` (2.43M rows: symbol, market, date, screen_bottom, policy, ret, reason, days) — per-event per-policy realized rets; `event_features.parquet` (76,049 bottoms, 17 cols); `regime_daily_extended.csv` (join market+date); `quantile_results.csv` (pinball baselines).
- Oracle label: per-event argmax ret across the 32 cells (from trade_labels long format).
- Model: gradient boosting (xgboost, n_jobs=2) multi-class over 32 cells; features = 16 event features + regime one-hot (rule labels, `regime` col) + per-event horizon prior from quantile model (expected MFE duration → max_days ∈ {20, 39}).
- CV: 5-block purged date-block CV on CALIB (< 2022-05-02), 60-day purge between blocks; fold-stability bar: chosen policy's mean ret > 0 in ALL 5 folds.
- Output: `reports/fib_swings/exit_policy_learned.csv` (per-event chosen cell + ret), `reports/fib_swings/EXIT_POLICY.md` (fold table, EVAL verdict vs frozen-grid baseline, VERDICT line).
- CLI: `--out reports/fib_swings`, `--smoke` (symbol subset, /tmp outputs).

## 3. Definition of Done (binary)
- [ ] No edits outside `write_files`.
- [ ] `test_command` exits 0.
- [ ] CALIB fold table printed; learned policy mean ret fold-stable (all 5 folds > 0) OR negative result documented.
- [ ] EVAL scored exactly once, net edge vs frozen-grid baseline stated.
- [ ] Stdout ≤5 lines: exit status, CALIB edge, EVAL edge, verdict.

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 1/2 | **Commit:** PENDING | **Status:** DONE
- **Notes / error tail:** `uv run pytest tests/test_fib_exit_policy.py -q --tb=short` → 5 passed; full-universe run PM-side 2026-11-08: CALIB OOF folds 5/5 positive (pooled +0.0061) but below frozen cell (+0.0107); EVAL one-shot learned +0.0080 vs frozen t15_s10_d39_close +0.0214 (edge −0.0134).
- **VERDICT: FAIL** — learned per-event policy does not beat the single frozen cell on CALIB or EVAL; per-event argmax oracle does not generalize. Closed negative; frozen t15_s10_d39_close stands.
