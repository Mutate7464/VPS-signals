---
wi_id: WI-048
title: T2 prediction expansion — directional, extreme-touch, and volatility target families on the D-023 grid
status: draft
agent: surgical-builder
depends_on: [WI-047]
gate_layer: "1"
board_row: "D-025 tiered workflow (admin direction 2026-11-10)"
write_files:
  - src/swing_bsh/targets_ext.py
  - src/swing_bsh/grid_targets_ext.py
  - tests/test_targets_ext.py
read_only_files:
  - src/swing_bsh/binary_grid.py
  - src/swing_bsh/train.py
  - reports/tiered_workflow_status_2026-11-10.md
  - docs/workflow/designs/D-025-tiered-workflow.md
test_command: uv run pytest tests/test_targets_ext.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
- Implement three new TARGET FAMILIES as explicit grid axes (never merged with label-geometry knobs): (a) directional `up` (close t+h > close t, h in ladder), (b) extreme-touch `high_low` (window high/low touched within h), (c) volatility `vol_expand` (realized-vol ratio t-window vs prior window above threshold). Each family × horizon ladder (5,8,13,21,34,55) × 2–3 library learners × 2 markets = ONE BH-FDR family; probe-first: dry-run on the denser measured label-density market, smoke before full grid.
- Correctness invariants are not budget knobs: purged/embargoed CV (embargo max(20,h)), CALIB-only selection, float32, symbol-sequential, n_jobs=2, rho prune 0.3. Grep pyproject before proposing learners — library learners only.

## 2. I/O contract and blueprint (literal)
- Output: `reports/t2_targets_ext_summary.md` (+ pickles `data/models/wi048/` in WI-040 manifest schema, only for FDR survivors); target-ranking table (which family is most predictable, cross-market min AUC + rank-IC) + BH-FDR survivor table + feature attribution on the winner cell.
- Smoke: `WI048_SMOKE=5` to /tmp, excludes EVAL; smoke stops at label-density report.
- Builder delivers code + synthetic tests + smoke only; PM owns the full grid run (cap 2.0 core-h).

## 3. Definition of Done (binary)
- [ ] Label builders per family verified on synthetic series (causality: features read at detection bar only); target-ranking table + FDR table produced by PM full run.
- [ ] No edits outside write_files; test_command exit 0; stdout ≤5 lines. Core-hour cap: 2.0 (PM-run).
