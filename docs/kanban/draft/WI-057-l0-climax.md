---
wi_id: WI-057
title: L0-6 effort-vs-result / climax block
status: draft
agent: surgical-builder
depends_on: [WI-051]
gate_layer: "1"
board_row: "D-026 SPRINT — L0-6 (admin-accepted 2026-11-13)"
write_files:
  - src/swing_bsh/binary_features_ext.py:190-302
  - tests/test_l0_climax.py
read_only_files:
  - src/swing_bsh/binary_features_ext.py:60-90
test_command: uv run pytest tests/test_l0_climax.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
Add a relational volume-vs-range "climax" block: volume spent per unit of range (effort/result) and its trailing z-score. Low prior (volume family is silent) — build anyway as an explicit net-new probe. Trailing-only, float32, dimensionless.

## 2. I/O contract and blueprint
- Input: per-symbol `volume`, `high`, `low`, `close`.
- Output: `_climax(...)` block in `build_variant_panel`: `effort_result_{w}`, `effort_result_z_{w}` for `w in (21, 55)`; effort = volume, result = high−low (ATR-normalized).
- Prefixes added to `candidate_features`.
- Tests `tests/test_l0_climax.py`: large range small volume -> low effort/result; NaN warmup; causal.
- Smoke: `WI048_SMOKE=3 uv run python -m src.swing_bsh.targets_ext --probe --out /tmp/wi057_smoke` exit 0.

## 3. Definition of Done
- [ ] No edits outside write_files. [ ] test_command exits 0. [ ] cols causal, float32, dimensionless. [ ] candidate_features gains the prefix. [ ] Stdout ≤5 lines.

## 4. Telemetry footer
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes:** None
