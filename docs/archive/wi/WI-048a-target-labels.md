---
wi_id: WI-048a
title: T2 label builders — `up` / `high_low` / `vol_expand` families + synthetic tests + smoke
status: done
verdict: n/a — infrastructure WI (label builders + tests + smoke), no gate verdict; PM-verified 2026-11-11
agent: surgical-builder
depends_on: []
gate_layer: "1"
board_row: "D-025 tiered workflow (admin direction 2026-11-10)"
parent: WI-048
write_files:
  - src/swing_bsh/targets_ext.py
  - src/swing_bsh/grid_targets_ext.py
  - tests/test_targets_ext.py
read_only_files:
  - src/swing_bsh/binary_grid.py
  - src/swing_bsh/train.py
  - src/swing_bsh/binary_features_ext.py
  - reports/tiered_workflow_status_2026-11-10.md
  - docs/workflow/designs/D-025-tiered-workflow.md
test_command: uv run pytest tests/test_targets_ext.py -q --tb=short --maxfail=1
core_hours_cap: 0.05
---

## 1. Objective and invariant
- Implement three TARGET FAMILIES as explicit grid axes (never merged with label-geometry knobs):
  - (a) `up`: close t+h > close t, h in ladder (5,8,13,21,34,55).
  - (b) `high_low`: event-window extreme RE-TEST — "does price touch the event window's high/low again within h bars after the detection bar?" (admin-approved definition).
  - (c) `vol_expand`: realized-vol ratio (t-window vs prior window of same length) above threshold.
- Each family × horizon ladder × 2 learners (`xgboost`, `lightgbm`) × 2 markets = ONE BH-FDR family.
- Correctness invariants are not budget knobs: purged/embargoed CV (embargo max(20,h)), CALIB-only selection, float32, symbol-sequential, n_jobs=2, rho prune 0.3. Library learners only (both in pyproject + WI-040/044 manifests).

## 2. I/O contract and blueprint (literal)
- Output: `reports/t2_targets_ext_summary.md` (+ pickles `data/models/wi048/` in WI-040 manifest schema, survivors only); target-ranking table + BH-FDR survivor table + feature attribution on winner cell.
- Smoke: `WI048_SMOKE=5` to /tmp, excludes EVAL; smoke stops at label-density report.
- Builder delivers code + synthetic tests + smoke only; PM owns the full grid (WI-048b–e).

## 3. Definition of Done (binary)
- [ ] Label builders per family verified on synthetic series (causality: features read at detection bar only).
- [ ] No edits outside write_files; test_command exit 0; stdout ≤5 lines. Core-hour cap: 0.05 (build+tests only).

## 4. Execution Telemetry
- Commit: bd80bd5
- Test Status: PASS — `uv run pytest tests/test_targets_ext.py -q --maxfail=1` → 12 passed (1.40s)
- Smoke: PM-run — `WI048_SMOKE=5 uv run python -m src.swing_bsh.targets_ext --probe` → EXIT:0, 36 cells, /tmp/wi048_smoke; `WI048_SMOKE=5 uv run python -m src.swing_bsh.grid_targets_ext --family up` → EXIT:0 (smoke stops at label-density report per spec)
- Notes: builder killed by Hermes tool timeout at 04:39:09 UTC after all three locked files landed (998 lines; grid_targets_ext.py mtime 04:39:02 POSTDATES log last write 04:38:48 — mid-edit provenance, flagged). PM-verified: tests exit 0, smoke exits 0 with correct artifact, git status shows only-manifest files + pre-existing untracked junk. Builder did not run smoke itself; PM ran it. Full-universe job NOT run.
