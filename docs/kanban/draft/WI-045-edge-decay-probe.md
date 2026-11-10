---
wi_id: WI-045
title: Decompose why CALIB edge dies before EVAL on the ratified WI-042 artifacts
status: draft
agent: surgical-builder
depends_on: []
gate_layer: "1"
board_row: "D-025 tiered workflow (admin direction 2026-11-10)"
write_files:
  - src/l2_overlay/edge_decay_probe.py
  - tests/test_edge_decay_probe.py
read_only_files:
  - reports/l2/rerun_modern.json
  - src/l2_overlay/harness.py
  - src/l2_overlay/rerun_modern.py
  - docs/workflow/designs/D-025-tiered-workflow.md
test_command: uv run pytest tests/test_edge_decay_probe.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
- On the ratified WI-042 cells (smoke on synthetic, PM full-run for real numbers): quantify which mechanism kills the CALIB→EVAL edge — (a) tau-mass concentration (how many events the selected tau actually trades), (b) fold concentration (is the CALIB edge one fold, e.g. fold-1?), (c) cost floor (is raw edge < 25 bps everywhere). Output ranks the three mechanisms by share of edge decay. Host invariants: no re-fit of learners; read-only inputs; float32, symbol-sequential.
- Gate layer L1: this is a diagnostic on frozen artifacts — no trading metrics beyond the already-computed edges, no new verdicts.

## 2. I/O contract and blueprint (literal)
- Output: `reports/l2/edge_decay_probe.md` (+ `.json`): per adopted cell, CALIB edge decomposition (fold-wise edges, event counts at tau, gross-vs-net edge), and a one-line mechanism ranking across the family.
- Smoke: `--smoke` on synthetic fixtures to /tmp. Tests: decomposition identities on synthetic data (gross - costs = net; fold shares sum to CALIB edge).

## 3. Definition of Done (binary)
- [ ] Decomposition table for all 20 ratified ADOPT cells; mechanism ranking stated; report derives only from the frozen JSON + recomputed returns.
- [ ] No edits outside write_files; test_command exit 0. Core-hour cap: 0.3.
