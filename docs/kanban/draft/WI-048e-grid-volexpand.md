---
wi_id: WI-048e
title: T2 full grid — `vol_expand` family (24 cells: 2 learners × 6 horizons × 2 markets)
status: draft
agent: pm
depends_on: [WI-048b]
gate_layer: "1"
board_row: "D-025 tiered workflow (admin direction 2026-11-10)"
parent: WI-048
write_files:
  - reports/t2_grid_volexpand_summary.md
read_only_files:
  - src/swing_bsh/targets_ext.py
  - src/swing_bsh/grid_targets_ext.py
  - reports/t2_label_density_probe.md
test_command: uv run python -m src.swing_bsh.grid_targets_ext --family vol_expand --family-only
core_hours_cap: 2.0
---

## 1. Objective and invariant
- Full grid run for the `vol_expand` family only: 2 learners (`xgboost`, `lightgbm`) × 6 horizons (5,8,13,21,34,55) × 2 markets = 24 cells. Variant pinning: `exact_full_k0.8` (USD), `tol2_full_k0.8` (CAD). Definition: realized-vol ratio (t-window vs prior window of same length) above threshold.
- ONE BH-FDR family (m=24 over this sub-grid). Placebo permutation on the largest |AUC−0.5| cells first.
- Invariants: purged/embargoed CV (embargo max(20,h)), CALIB-only selection, float32, symbol-sequential, n_jobs=2, rho prune 0.3.

## 2. I/O contract
- Output: `reports/t2_grid_volexpand_summary.md` + pickles `data/models/wi048/` (survivors only).
- Budget check: 24 cells ≈ 0.55 h; cap 2.0 leaves headroom.

## 3. Definition of Done (binary)
- [ ] 24 cells scored or truncated-and-reported; FDR table; pickles for survivors only.
- [ ] Core-hour cap: 2.0, declared in the run footer.
