# FILE: WI-034 — three-binary label decomposition + univariate probe (D-022 §2)
---
wi_id: WI-034
title: Decompose swing first-touch labels into 3 binary targets and run per-binary univariate IC probe
status: draft
agent: surgical-builder
depends_on: []
board_row: "D-022 thread (admin direction in chat 2026-11-09)"
write_files:
  - src/swing_bsh/binary_labels.py
  - src/swing_bsh/binary_probe.py
  - tests/test_swing_bsh_binary_probe.py
read_only_files:
  - src/swing_bsh/events.py
  - src/swing_bsh/probe.py
  - reports/wi032_probe.md
test_command: uv run pytest tests/test_swing_bsh_binary_probe.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
- Add `binary_labels.py`: from the existing `label_symbol` first-touch geometry, emit per event three mutually exclusive int8 columns `b_profit, b_stop, b_hold` (profit-first / stop-first / vertical; ties→stop, per events.py). Refactor, not reimplement: call the existing `_first_touch` outcome; do not duplicate geometry.
- Host invariants: n_jobs=2, float32 after calc, symbol-sequential reads, no all-ticker frame.

## 2. I/O contract and blueprint (literal)
- Input: `iter_market_symbols(market)` raw OHLCV (DATA_CONTRACT §1 schema).
- Output: `reports/binary_probe/wi034_probe_<MKT>.md` (+ .csv): per (state,k,h)×binary-target — positives, density; per-feature Spearman IC, BH-FDR q, same-sign flag, 5-seed permutation placebo. No model trained.
- Reuse the WI-032 harness pattern (`src/swing_bsh/probe.py`): full feature whitelist, **|ρ|>0.4 prune** (admin-loosened 2026-11-09, was 0.7), ≥500 resolved events/group, BH-FDR α=0.05. Report kept-feature count per binary target; do not hard-code 41.
- Dry-run: `WI034_SMOKE=5 symbols --out /tmp/wi034_smoke`; never overwrite frozen report names.
- `tests/test_swing_bsh_binary_probe.py` (synthetic OHLCV): (a) b_* triple is one-hot (row sums to 1) on defined events; (b) tie bar → b_stop=1; (c) NaN mask on horizon tail.

## 3. Definition of Done (binary)
- [ ] No edits outside `write_files`.
- [ ] `test_command` exits 0.
- [ ] CLEAR/UNCLEAR verdict per binary target per market, printed ≤5 lines: exit, events, verdicts, runtime.
- [ ] Stdout ≤5 lines. Core-hour cap: 0.3.

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes / error tail:** None
