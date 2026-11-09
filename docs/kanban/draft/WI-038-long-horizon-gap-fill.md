# FILE: WI-038 — long-horizon gap fill (h>=34 cells truncated in WI-036)
---
wi_id: WI-038
title: Run the h in {34,55,89,144,233} cells of the WI-036 target-variant grid that were budget-truncated (untested, not negative)
status: draft
agent: surgical-builder
depends_on: []
board_row: "D-022 thread phase 2 (admin direction in chat 2026-11-09: explore more timeframes)"
write_files:
  - src/swing_bsh/binary_grid_longh.py
  - tests/test_swing_bsh_binary_grid_longh.py
read_only_files:
  - src/swing_bsh/binary_grid.py
  - src/swing_bsh/binary_features_ext.py
  - reports/wi036_summary.md
test_command: uv run pytest tests/test_swing_bsh_binary_grid_longh.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
- WI-036 truncated 1,158 high-h cells (h>=34 dropped first) under its 2.5 core-h cap: long-horizon behaviour is UNTESTED, not negative. This WI runs those cells (8 variants x h in {34,55,89,144,233} x 3 binaries x 4 learners x 2 markets) via a thin driver importing `binary_grid.py` machinery; HORIZONS constant overridden, nothing else changed.
- Expectation management: 233d labels x 5 folds x max(20,h) embargo consumes years per symbol — late folds will be data-starved BY DESIGN; report per-fold event counts and mark starved folds rather than silently pooling.
- n_jobs=2, float32, symbol-sequential; BH-FDR across this grid separately (not pooled with the wi036 grid).

## 2. I/O contract and blueprint (literal)
- Input/output identical in shape to WI-036; report `reports/wi038_summary.md` (ranking + FDR survivors + per-fold counts); pickles `data/models/wi038/`.
- Dry-run: `WI038_SMOKE=5 --out /tmp/wi038_smoke`.
- Tests: horizon constant = {34,55,89,144,233}; driver imports (monkeypatched) not re-implements; embargo = max(20, h).

## 3. Definition of Done (binary)
- [ ] No edits outside `write_files`.
- [ ] `test_command` exits 0.
- [ ] Ranking + FDR table for all high-h cells; data-starved folds flagged; verdict recorded (expected: b_hold family again, weaker; honest report either way).
- [ ] Stdout ≤5 lines. Core-hour cap: 2.0 (longer horizons are more expensive per event; if tight drop h=233 first, then 144).

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes / error tail:** None