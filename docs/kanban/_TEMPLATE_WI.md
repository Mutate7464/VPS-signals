# FILE: docs/kanban/_TEMPLATE_WI.md — atomic Work Item template (kanban staging; BOARD.md stays the single source of truth)

---
wi_id: WI-000
title: Short imperative action title
status: draft
agent: surgical-builder
depends_on: []
board_row: "(BOARD.md ACTIVE row this WI executes, if any)"
write_files:
  - src/module/target.py:40-95
read_only_files:
  - src/module/INDEX.md
  - src/module/types.py:1-35
test_command: uv run pytest tests/module/test_target.py -q --tb=short --maxfail=1
---

## 1. OBJECTIVE & ARCHITECTURAL INVARIANT
- Single-sentence behavioral change required and non-negotiable constraint (host limits: n_jobs=2, float32 feature frames, symbol-sequential / pyarrow.dataset reads).

## 2. SURGICAL IMPLEMENTATION BLUEPRINT
- `src/module/target.py` (Lines 40-95): Exact function signature, input/output types, edge-case handling, and algorithmic steps.
- `tests/module/test_target.py`: Exact unit test assertion to add/update.

## 3. BINARY DEFINITION OF DONE (DoD)
- [ ] Zero edits outside `write_files`.
- [ ] `test_command` exits with code `0`.
- [ ] Local `INDEX.md` updated if exported signatures changed.

## 4. EXECUTION TELEMETRY (Appended on Completion/Block)
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes / Error Trace:** None
