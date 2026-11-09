# FILE: WI-039 — regime-conditional audit of the b_hold signal
---
wi_id: WI-039
title: Break down winning b_hold model performance by WI-027 regime label (up_high/chop_normal etc.), both markets
status: draft
agent: surgical-builder
depends_on: []
board_row: "D-022 thread phase 2 (admin direction in chat 2026-11-09: regime changes)"
write_files:
  - src/swing_bsh/hold_regime_audit.py
  - tests/test_swing_bsh_hold_regime_audit.py
read_only_files:
  - src/swing_bsh/binary_grid.py
  - src/swing_bsh/binary_features_ext.py
  - reports/fib_swings/regime_daily.csv
  - data/models/wi036/
test_command: uv run pytest tests/test_swing_bsh_hold_regime_audit.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
- The b_hold signal IS a volatility-regime prediction; audit whether it is carried by one regime or robust. Join the winning cells' OOF predictions (`exact_full_k0.8`, xgb, h in {5,8,13,21}, both markets) to the WI-027 regime labels (`reports/fib_swings/regime_daily.csv`) by (symbol, date); report per-regime AUC/IC, per-regime hold prevalence, and per-regime counts.
- Inference/join only — no model training, no refit. n_jobs=2, float32.

## 2. I/O contract and blueprint (literal)
- Input: wi036 pickles + variant panel builder; regime_daily.csv.
- Output: `reports/wi039_summary.md` — per market x regime x h: AUC, IC, n, hold rate; plus one-line verdict per market: signal robust across regimes vs concentrated (name the regime if concentrated).
- Dry-run: `WI039_SMOKE=5 --out /tmp/wi039_smoke`.
- Tests (synthetic): join correctness on (symbol,date); empty-regime rows dropped not NaN'd; per-regime AUC matches pooled-input formula on toy data.

## 3. Definition of Done (binary)
- [ ] No edits outside `write_files`.
- [ ] `test_command` exits 0.
- [ ] Per-regime table both markets; concentration verdict recorded (feeds WI-037 interpretation: if the signal lives only in chop_normal, the trade-suppression veto should be regime-gated).
- [ ] Stdout ≤5 lines. Core-hour cap: 0.3.

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes / error tail:** None