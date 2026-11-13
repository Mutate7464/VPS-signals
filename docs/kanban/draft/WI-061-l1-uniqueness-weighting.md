---
wi_id: WI-061
title: L1-4 sample-uniqueness weighting (training variant)
status: draft
agent: surgical-builder
depends_on: [WI-050]
gate_layer: "1"
board_row: "D-026 SPRINT — L1-4 (admin-accepted 2026-11-13)"
write_files:
  - src/swing_bsh/learner_ext.py
  - tests/test_swing_bsh_learner_ext.py
read_only_files:
  - src/swing_bsh/train.py
  - src/swing_bsh/binary_labels.py
test_command: uv run pytest tests/test_swing_bsh_learner_ext.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
Add average-uniqueness sample weights (down-weight overlapping h-bar event labels) as an optional training weight, addressing calibration bias from label overlap. Method variant only — no new label, no new cell family (m=12 reference).

## 2. I/O contract and blueprint
- Input: event index `t0`, horizons `h`, series length `n`.
- Output: `average_uniqueness(t0, h, n) -> float32[m]` in `learner_ext.py`, plus a `sample_weight=` pass-through where the learner is fit. Weight = 1/concurrency, clipped to (0,1].
- Tests `tests/test_swing_bsh_learner_ext.py`: non-overlapping events -> weight 1; fully overlapping -> 1/count; monotone in overlap.
- Cap 1.0 core-h.

## 3. Definition of Done
- [ ] No edits outside write_files. [ ] test_command exits 0. [ ] weights in (0,1], causal. [ ] existing learner tests still pass. [ ] Stdout ≤5 lines.

## 4. Telemetry footer
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes:** None
