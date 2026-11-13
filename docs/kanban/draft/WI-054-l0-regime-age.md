---
wi_id: WI-054
title: L0-3 regime age / run-length block
status: draft
agent: surgical-builder
depends_on: [WI-051]
gate_layer: "1"
board_row: "D-026 SPRINT — L0-3 (admin-accepted 2026-11-13)"
write_files:
  - src/swing_bsh/binary_features_ext.py:190-302
  - tests/test_l0_regime_age.py
read_only_files:
  - src/swing_bsh/binary_features_ext.py:60-90
test_command: uv run pytest tests/test_l0_regime_age.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
Add a temporal-duration block: bars since the current vol/hurst regime began (run-length) and the previous run's length. Targets "release vs just-released" timing. Trailing-only, float32, dimensionless (counts as float32).

## 2. I/O contract and blueprint
- Input: per-symbol series; regime state derived *causally* from an existing trailing percentile (e.g. `atr_pct_21` vs its rolling 233 median) — no future look.
- Output: `_regime_age(...)` block in `build_variant_panel`: `regime_age_vol`, `regime_prev_dur_vol`, `regime_age_hurst`. float32.
- Soft dependency on WI-047 #1 (regime percentiles) — if absent, derive the state inline from the existing `atr_pct_21`; state this in the docstring.
- Prefixes added to `candidate_features`.
- Tests `tests/test_l0_regime_age.py`: known regime flips -> expected run lengths; monotone series -> increasing age; causal (no future).
- Smoke: `WI048_SMOKE=3 uv run python -m src.swing_bsh.targets_ext --probe --out /tmp/wi054_smoke` exit 0.

## 3. Definition of Done
- [ ] No edits outside write_files. [ ] test_command exits 0. [ ] state derived causally. [ ] candidate_features gains the prefix. [ ] Stdout ≤5 lines.

## 4. Telemetry footer
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes:** None
