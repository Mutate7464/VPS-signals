# FILE: docs/kanban/_TEMPLATE_WI.md — WI batch spec (kanban staging; BOARD.md is the single board)
# Body cap: sections 1–4 <= 400 tokens (~1,600 bytes). Larger work splits into WIs.
# Frontmatter keys are parsed by the kanban-orchestrator skill. Do not rename them.

---
wi_id: WI-000
title: Short imperative action title
status: draft
agent: surgical-builder
depends_on: []
board_row: "(BOARD.md row this WI executes, if any)"
write_files:
  - src/module/target.py:40-95
read_only_files:
  - src/module/INDEX.md
  - src/module/types.py:1-35
test_command: uv run pytest tests/module/test_target.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
- One sentence: the behavioural change. Name the host invariant that applies (n_jobs=2, float32, symbol-sequential reads).

## 2. I/O contract and blueprint (literal)
- Input: `<exact path>`, schema `<col:dtype, ...>` (from `DATA_CONTRACT.md` or a metadata probe).
- Output: `<exact path>`, schema `<col:dtype, ...>`.
- Dry-run subset: `<file list, or env filter + --out /tmp/<wi>_smoke>`. Smoke output never overwrites frozen report names.
- Input root is a named constant (`data_dir = ...`). Never read inputs from `--out`.
- `<file>` (Lines a–b): signature, formula, constants, edge cases (NaN, empty, index reset).
- `tests/<path>`: exact assertion to add or update. Synthetic data only.

## 3. Definition of Done (binary)
- [ ] No edits outside `write_files`.
- [ ] `test_command` exits 0.
- [ ] Dry-run output shape and null count match section 2.
- [ ] `INDEX.md` updated if an exported signature changed.
- [ ] Stdout ≤5 lines: exit status, output shape, null count, runtime.

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes / error tail:** None
