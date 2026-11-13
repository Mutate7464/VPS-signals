---
wi_id: WI-048f
title: T2 cross-family summary — target-ranking table, FDR consolidation, winner-cell attribution
status: draft
agent: pm
depends_on: [WI-048c, WI-048d, WI-048e]
gate_layer: "1"
board_row: "D-025 tiered workflow (admin direction 2026-11-10)"
parent: WI-048
write_files:
  - reports/t2_targets_ext_summary.md
read_only_files:
  - reports/t2_grid_up_summary.md
  - reports/t2_grid_highlow_summary.md
  - reports/t2_grid_volexpand_summary.md
  - data/models/wi048/manifest.parquet
test_command: uv run python -m src.swing_bsh.grid_targets_ext --consolidate
core_hours_cap: 0.3
---

## 1. Objective and invariant
- Consolidate the three family sub-grids into `reports/t2_targets_ext_summary.md`: target-ranking table (which family is most predictable: cross-market min AUC + rank-IC), BH-FDR survivor table (per-family m=24, consolidated view), feature attribution on the winner cell.
- No new training; joins existing manifests + pickles. Invariants: float32, symbol-sequential, n_jobs=2.

## 2. I/O contract
- Output: `reports/t2_targets_ext_summary.md` + updated `data/models/wi048/manifest.parquet` (library field = `wi048` for survivors).
- Verdict: PROVISIONAL — computed ADOPT/REJECT/INCONCLUSIVE labels advisory until admin ratifies in chat.

## 3. Definition of Done (binary)
- [ ] Target-ranking table + FDR table + winner-cell attribution produced; no new training; core-hour cap 0.3.
