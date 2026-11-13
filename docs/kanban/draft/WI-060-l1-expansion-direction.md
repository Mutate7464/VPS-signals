---
wi_id: WI-060
title: L1-3 expansion-direction decomposition (A·B) label + grid
status: draft
agent: surgical-builder
depends_on: [WI-058]
gate_layer: "1"
board_row: "D-026 SPRINT — L1-3 (admin-accepted 2026-11-13)"
write_files:
  - src/swing_bsh/targets_ext.py:40-60
  - src/swing_bsh/targets_ext.py:160-215
  - src/swing_bsh/grid_targets_ext.py:38-50
  - tests/test_targets_ext.py
read_only_files:
  - src/swing_bsh/targets_ext.py
test_command: uv run pytest tests/test_targets_ext.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
Decompose expansion into two labels: A = a move happens (`high_low`-like), B = its direction is up (conditional on a move). Report the fixed product P(A)·P(B|A) as a description, never as a stacked OOF feature. `up` is chance unconditionally — this tests whether direction is learnable *given* a move.

## 2. I/O contract and blueprint
- Input: per-symbol `high/low/close/atr`.
- Output: `move_occur_labels(...)` (family `move_occur`) and `move_dir_up_labels(...)` (family `move_dir_up`) in `targets_ext.py`; SUMMARY_NAME entries. Both binary, forward window `[t0+1,t0+h]`.
- Tests: constructed paths -> A=1 with a move, B=1 only when up; no-move rows excluded from B's denominator.
- PM owns the full grid (two families); cap 1.5 each.

## 3. Definition of Done
- [ ] No edits outside write_files. [ ] test_command exits 0. [ ] A/B conditional construction tested. [ ] two families, one BH-FDR each. [ ] Stdout ≤5 lines.

## 4. Telemetry footer
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes:** None
