---
wi_id: WI-042
title: Rerun the four modern L2 overlays (037/033/030/028) under the D-024 harness with multi-horizon library inputs
status: draft
gate_layer: L2
agent: surgical-builder
depends_on: [WI-041]
board_row: "D-024 L2 rebuild (admin direction in chat 2026-11-10: rerun old L2s)"
write_files:
  - src/l2_overlay/rerun_modern.py
  - tests/test_l2_rerun_modern.py
read_only_files:
  - src/l2_overlay/harness.py
  - src/swing_bsh/library_audit.py
  - src/swing_bsh/hold_filter_gate.py
  - src/swing_bsh/evaluate.py
  - scripts/fib_exit_policy.py
  - scripts/fib_entry_window.py
  - docs/workflow/designs/D-024-l2-overlay-rebuild.md
test_command: uv run pytest tests/test_l2_rerun_modern.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
- Rerun the four rejected overlays — WI-037 (b_hold veto), WI-033 (3-class swing overlay), WI-030 (exit chooser), WI-028 (entry-window chooser) — through `harness.run_overlay`, each vs its NAMED frozen baseline + costs, inputs from the WI-040 manifest now including WI-038 long-h survivors (h in {34,55,89}).
- Structural changes vs the originals (D-024 §2): CALIB-only tuning with edge criterion, feasibility precheck (INERT before EVAL burn), 5-seed placebo on edge, BH-FDR across the 4 reruns as ONE family. Admin rerun waiver recorded (D-024 §2).
- Pre-committed closure: REJECT under this harness closes that overlay question permanently.

## 2. I/O contract and blueprint (literal)
- Output: `reports/l2/rerun_modern.md` (per overlay: verdict INERT/ADOPT/REJECT, tau, calib/eval edge, folds, placebo z, FDR-adjusted p) + `reports/l2/rerun_modern.json`.
- Smoke: `L2_SMOKE=5` on 5 symbols per market to /tmp (never touches EVAL scoring on partial data — smoke stops at feasibility precheck).
- Tests: each of the 4 questions maps to a baseline config; FDR family = 4; smoke excludes EVAL.

## 3. Definition of Done (binary)
- [ ] All four overlays produce verdicts (INERT allowed and honest); FDR table across the family.
- [ ] No edits outside write_files; test_command exit 0; stdout <=5 lines. Core-hour cap: 1.0 (inference + edge grids; learners are NOT re-trained).

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
