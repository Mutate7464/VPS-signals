---
wi_id: WI-062
title: L1.5 meta-label (swing-side primary) + seed-averaging companion
status: draft
agent: surgical-builder
depends_on: [WI-058, WI-059]
gate_layer: "1"
board_row: "D-026 SPRINT — L1.5 (admin-accepted 2026-11-13; not-stacking ruling)"
write_files:
  - src/swing_bsh/meta_label_ext.py
  - tests/test_meta_label_ext.py
read_only_files:
  - src/swing_bsh/train.py
  - src/swing_bsh/library_audit.py
  - src/swing_bsh/grid_targets_ext.py
test_command: uv run pytest tests/test_meta_label_ext.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
Add an L1.5 precision filter: secondary model predicting the primary's favourable outcome, primary = swing side (and frozen fib rule as a second family). Positive class = the primary wins. Gated Layer-1 (predictive only). The decomposed positive class uses a **fixed product of separately-fitted models** — the admin ruled this **NOT stacking** (D-026).

## 2. I/O contract and blueprint
- Input: primary side + primary outcome, detection-bar features, OOF probabilities.
- Output: `src/swing_bsh/meta_label_ext.py` with `build_meta_labels(...)` and `meta_oof(...)` (purged/embargoed CV inside; never uses a fold's own OOF as a feature).
- **Mandatory DoD:** a permuted-label leakage test — with labels permuted, meta AUC ≈ 0.50 (no leakage).
- Tests `tests/test_meta_label_ext.py`: synthetic separation -> AUC>0.5; permuted labels -> ≈0.5; no OOF-as-feature.
- Cap 2.5 core-h; PM owns the full run.

## 3. Definition of Done
- [ ] No edits outside write_files. [ ] test_command exits 0. [ ] permuted-label leakage test present and passing. [ ] Layer-1 predictive header (no economic claim). [ ] Stdout ≤5 lines.

## 4. Telemetry footer
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes:** None
