---
wi_id: WI-055
title: L0-4 jump-intensity block
status: draft
agent: surgical-builder
depends_on: [WI-051]
gate_layer: "1"
board_row: "D-026 SPRINT — L0-4 (admin-accepted 2026-11-13)"
write_files:
  - src/swing_bsh/binary_features_ext.py:190-302
  - tests/test_l0_jump_intensity.py
read_only_files:
  - src/swing_bsh/binary_features_ext.py:60-90
test_command: uv run pytest tests/test_l0_jump_intensity.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
Add a tail-plausibility block: bipower-style jump variation and jump count over trailing windows (realized var minus bipower var). Trailing-only, float32, dimensionless.

## 2. I/O contract and blueprint
- Input: per-symbol `close` (log returns).
- Output: `_jump_intensity(...)` block in `build_variant_panel`: `jump_var_ratio_{w}`, `jump_count_{w}` for `w in (21, 55)`; bipower var = (pi/2)·mean(|r_t|·|r_{t-1}|); ratio = max(RV − BV, 0)/RV.
- Prefixes added to `candidate_features`.
- Tests `tests/test_l0_jump_intensity.py`: smooth series -> ratio≈0, count 0; single large bar -> positive jump var; NaN warmup; no future.
- Smoke: `WI048_SMOKE=3 uv run python -m src.swing_bsh.targets_ext --probe --out /tmp/wi055_smoke` exit 0.

## 3. Definition of Done
- [ ] No edits outside write_files. [ ] test_command exits 0. [ ] cols causal, float32, dimensionless. [ ] candidate_features gains the prefix. [ ] Stdout ≤5 lines.

## 4. Telemetry footer
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes:** None
