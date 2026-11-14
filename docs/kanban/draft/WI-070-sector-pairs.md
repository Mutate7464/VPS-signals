---
wi_id: WI-070
title: (d) Within-market sector pairs L/S (conditional; requires confirmed sector map)
status: draft
agent: surgical-builder
depends_on: ["WI-066"]
gate_layer: "2 (overlay/trading; conditional — dispatch only on admin go + sector map confirmed)"
board_row: "D-027 Phase 4 (d)"
write_files:
  - src/l2_overlay/constructions/sector_pairs.py
  - tests/l2_overlay/test_sector_pairs.py
read_only_files:
  - src/l2_overlay/harness.py
  - src/l2_overlay/costs.py
  - src/l2_overlay/fold_report.py
  - docs/workflow/designs/D-027-l2-rebuild.md
test_command: uv run pytest tests/l2_overlay/test_sector_pairs.py -q --tb=short --maxfail=1 && uv run python -m src.l2_overlay.constructions.sector_pairs --smoke
---

## 1. Objective and invariant
- CONDITIONAL WI: dispatch only if (b) survived CALIB, admin gives the go, AND a confirmed sector map exists (D-027 §11 open question 6; card is a no-op without one). Within-market long/short pairs from within-sector xsec ranks + move_dir_up. Cost: 100 bps per pair cycle; spread must exceed 100 bps. Within-market ONLY (WI-012 cross-market transfer failure). Invariants: n_jobs=2, float32, no EVAL reads.

## 2. I/O contract and blueprint (literal)
- Input: sector map (path supplied at pre-registration), xsec ranks, price panel. Root named constant.
- Output: CALIB report `reports/l2_sector_pairs/calib_<market>.md` — per-pair net edge after 100 bps, fold report; smoke to `*_smoke`.
- `sector_pairs.py`: `form_pairs(within_sector_ranks) -> (long, short)`, `simulate_pairs(pairs, costs)` via `costs.pair_cost`; fold report fails closed.
- Tests: pairs never cross markets; cost arithmetic = 100 bps/cycle; spread ≤ 100 bps falsifier wired as a stop; placebo shows nothing.

## 3. Definition of Done (binary)
- [ ] No edits outside `write_files`.
- [ ] `test_command` exits 0.
- [ ] Fold report + stop/continue recorded.
- [ ] Stdout ≤5 lines.

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes / error tail:** None
