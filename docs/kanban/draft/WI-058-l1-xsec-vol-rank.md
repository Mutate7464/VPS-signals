---
wi_id: WI-058
title: L1-1 forward cross-sectional vol-rank label + grid
status: draft
agent: surgical-builder
depends_on: [WI-051]
gate_layer: "1"
board_row: "D-026 SPRINT — L1-1 (admin-accepted 2026-11-13)"
write_files:
  - src/swing_bsh/targets_ext.py:40-60
  - src/swing_bsh/targets_ext.py:160-215
  - src/swing_bsh/grid_targets_ext.py:38-50
  - tests/test_targets_ext.py
read_only_files:
  - src/swing_bsh/targets_ext.py
test_command: uv run pytest tests/test_targets_ext.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
Add the product-question target: forward cross-sectional vol rank at `t0+h` (rank of the name's realized vol among the universe), in **both** binary (top-tercile) and continuous (rank in [0,1]) forms — two separate BH-FDR families. Removes the `vol_expand` self-relative inversion risk. Features read at detection bar only.

## 2. I/O contract and blueprint
- Input: per-market panel + `close`; forward window `[t0+1, t0+h]`.
- Output: `xsec_vol_rank_bin_labels(...)`, `xsec_vol_rank_cont_labels(...)` in `targets_ext.py`; registered as families `xsec_vol_rank_bin` / `xsec_vol_rank_cont`; `grid_targets_ext.SUMMARY_NAME` entries for each.
- Rank is same-date cross-sectional -> requires the market's full event set; compute per-market (like the breadth block).
- Tests: crafted universe -> expected tercile labels + ranks; NaN tail handling; causality (forward window only).
- **PM owns the full grid** (`--family xsec_vol_rank_bin --family-only`, then `_cont`); core cap 2.0 per family.

## 3. Definition of Done
- [ ] No edits outside write_files. [ ] test_command exits 0. [ ] two families registered, each one BH-FDR (m=24). [ ] forward-only window asserted. [ ] Stdout ≤5 lines.

## 4. Telemetry footer
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes:** None
