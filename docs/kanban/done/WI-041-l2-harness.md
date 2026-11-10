---
wi_id: WI-041
title: Build the Layer-2 overlay harness (D-024) — one protocol module replacing per-WI tuning scripts
status: draft
gate_layer: L2
agent: surgical-builder
depends_on: []
board_row: "D-024 L2 rebuild (admin direction in chat 2026-11-10: work on next WI, rerun old L2s)"
write_files:
  - src/l2_overlay/harness.py
  - src/l2_overlay/__init__.py
  - tests/test_l2_overlay_harness.py
read_only_files:
  - src/swing_bsh/library_audit.py
  - src/swing_bsh/hold_filter_gate.py
  - src/swing_bsh/evaluate.py
  - docs/workflow/designs/D-024-l2-overlay-rebuild.md
test_command: uv run pytest tests/test_l2_overlay_harness.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
- Implement the D-024 §2 protocol ONCE: load a named frozen baseline + costs; load overlay probabilities via the WI-040 manifest/`--infer`; feasibility precheck (CALIB events >= 200 AND tau range spans observed calibrated probability mass, else verdict INERT, no EVAL burn); tune decision params on CALIB-period edge only (criterion function must be max CALIB edge — grep-verifiable); one-shot EVAL; 5-seed placebo on the edge; report per-fold edges. n_jobs=2, float32, symbol-sequential.
- Layer separation: harness never re-fits learners, never reads EVAL during tuning, never selects on AUC.

## 2. I/O contract and blueprint (literal)
- API: `run_overlay(name, baseline, probs, events, tau_grid, calib_mask, eval_mask) -> OverlayResult{verdict, tau, calib_edge, eval_edge, folds, placebo_z, inert_reason}`.
- Smoke: `L2_SMOKE=1 uv run python -m src.l2_overlay.harness --question wi037 --out /tmp/l2_smoke` on synthetic fixtures only (no EVAL burn).
- Output: `/tmp` smoke report; real runs write `reports/l2/<name>.md`.
- Tests: INERT path when probability mass < tau range; tau selection uses CALIB edge only (monkeypatch EVAL, assert unchanged tau); placebo runs; verdict mapping (ADOPT requires calib_edge>0 + placebo_z>=2.0 + eval_edge>=0).

## 3. Definition of Done (binary)
- [ ] All D-024 §2 protections present and test-covered; no edits outside write_files.
- [ ] test_command exit 0; stdout <=5 lines. Core-hour cap: 0.5 (smoke only, synthetic).

## 4. Telemetry footer (executor fills, <=3 lines)
- **Attempts:** 1/2 | **Commit:** PENDING (HEAD 05e214f; no commit made) | **Status:** DONE
- **Evidence:** `uv run pytest tests/test_l2_overlay_harness.py -q --tb=short --maxfail=1` → 14 passed (0.9s); `L2_SMOKE=1 uv run python -m src.l2_overlay.harness --question wi037 --out /tmp/l2_smoke` → ADOPT tau=0.70 z=+38.90, report written; `--inert` → INERT, no EVAL burn. Cap: 0.5 core-h (synthetic smoke only).

