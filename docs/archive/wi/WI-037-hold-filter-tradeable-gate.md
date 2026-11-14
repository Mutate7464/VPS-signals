# FILE: WI-037 — P(hold) trade-suppression filter on frozen fib rules (tradeable downstream test)
---
wi_id: WI-037
title: Use winning b_hold model (exact_full_k0.8 xgb h13) as a veto filter on frozen fib entries; gate vs frozen baseline
status: done
verdict: REJECT both markets — RATIFIED 2026-11-09 (admin in chat); Layer-2 trading verdict; WI-036 Layer-1 pickles unaffected
agent: surgical-builder
depends_on: []
board_row: "D-022 thread phase 2 (admin direction in chat 2026-11-09: test ML for tradeable decisions)"
write_files:
  - src/swing_bsh/hold_filter_gate.py
  - tests/test_swing_bsh_hold_filter.py
read_only_files:
  - src/swing_bsh/binary_features_ext.py
  - src/swing_bsh/binary_grid.py
  - data/models/wi036/
  - reports/wi036_summary.md
  - reports/fib_swings/ (frozen baseline artifacts)
test_command: uv run pytest tests/test_swing_bsh_hold_filter.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
- First tradeable-decision test of the only surviving ML signal: at frozen-rule fib entry events (WI-028 at-bottom entry), query the saved `exact_full_k0.8` xgb b_hold h13 models (pickles `data/models/wi036/`, folds f0–f4 per market) for P(hold) and VETO the entry when P(hold) ≥ τ. Gate: does the filtered rule beat the unfiltered frozen baseline (WI-030 exit `t15_s10_d39_close`, 25 bps) under ADOPT_LOOSE_4OF5 + CB-05 5-seed placebo.
- Inference only (no refit except the placebo arms). τ grid {0.5,0.6,0.7,0.8} tuned on CALIB-period events only, frozen before EVAL. Purged 5-fold CV as WI-036. n_jobs=2, float32, symbol-sequential.
- Fold-consistency of pickles: use each fold's model on its own OOF rows (pickles are fold-fitted; never apply fold-f's model outside its time block).

## 2. I/O contract and blueprint (literal)
- Input: frozen baseline event/return series (see `reports/fib_swings/OVERNIGHT_REPORT.md` and WI-030 grid artifacts); b_hold pickles + variant panel builder from `binary_features_ext.py`/`binary_grid.py`.
- Output: `reports/wi037_summary.md` — per market: fold table (baseline vs filtered mean return, n events kept/vetoed), pooled edge, placebo z, τ chosen, verdict ADOPT/REJECT. No pickle unless ADOPT (`data/models/wi037/`).
- Dry-run: `WI037_SMOKE=5 --out /tmp/wi037_smoke`.
- Tests (synthetic): veto logic is P≥τ intersection; fold-model mapped to fold rows only; no leakage columns.

## 3. Definition of Done (binary)
- [ ] No edits outside `write_files`.
- [ ] `test_command` exits 0.
- [ ] ADOPT/REJECT both markets under ADOPT_LOOSE_4OF5 + placebo z ≥ 2; report kept/vetoed counts and precision at τ (class-prevalence caveat from wi036).
- [ ] Stdout ≤5 lines. Core-hour cap: 0.5 (inference + placebo only).

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 1/2 | **Commit:** PENDING (HEAD 8706305; no commit made) | **Status:** DONE — tests green + dry run OK; full-universe job NOT run (PM owns it; EVAL split unscored, no `reports/wi037_summary.md`, no pickle on REJECT).
- **Notes / error tail:** fixed `labels[BINARY]` KeyError -> `labels[(VARIANT, HORIZON)][BINARY]`; ADOPT pickle now targets `data/models/wi037/`; `--limit`/`WI037_SMOKE` dry runs drop EVAL rows (splits excluded, not just withheld from the report). Tests `12 passed` (~1.3s). Smoke `WI037_SMOKE=5`: USD 91/91 kept, CAD 48/48 kept, tau=0.50, REJECT both, core 7.6s+8.1s. `WI037_SMOKE=20`: USD 383/383 z=-2.86, CAD 280/280, 19.6s. Note: calibrated P(hold) max ~0.011 in dry runs, so tau {0.5..0.8} is inert (WI-036 prevalence caveat, stated in the report); file is 333 lines (>250 guideline) to keep the full report generator.