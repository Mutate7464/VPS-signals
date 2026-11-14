---
wi_id: WI-048f
title: T2 cross-family summary — target-ranking table, FDR consolidation, winner-cell attribution
status: done
verdict: RATIFIED (admin in chat 2026-11-14, Layer 1) — consolidation stands; the `vol_expand` ranking row (0.7068) is QUARANTINED per D-026 ruling 2 (backward-looking label) — ranking excludes it for any forward use; winner-cell attribution retained as provenance
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

---

## Execution Telemetry Footer

- Commit: PENDING (HEAD d92a7f4; no commit made)
- Test Status: PASS — chain stage EXIT:0 (log logs/wi-048def_run.out, marker EXIT_F:0, chain done 2026-11-13T05:59:32Z); artifacts PM-verified this session
- Index Updated: Y — PM-run outputs; untracked data/ + reports/ artifacts stay out of git
- PM-run verdict (PROVISIONAL): 72 cells joined; family ranking by cross-market min AUC — vol_expand 0.7068 > high_low 0.6089 > up 0.5038; winner cell USD|lightgbm|vol_expand|h13 attribution (TreeSHAP + linear) recorded; report reports/t2_targets_ext_summary.md.
