---
wi_id: WI-048d
title: T2 full grid — `high_low` family (24 cells: 2 learners × 6 horizons × 2 markets)
status: done
verdict: RATIFIED (admin in chat 2026-11-14, Layer 1) — all 24 BH-FDR survivors accepted into the L1 pickle library (predictive-only rule, no effect-size floor, EVAL unburned)
agent: pm
depends_on: [WI-048b]
gate_layer: "1"
board_row: "D-025 tiered workflow (admin direction 2026-11-10)"
parent: WI-048
write_files:
  - reports/t2_grid_highlow_summary.md
read_only_files:
  - src/swing_bsh/targets_ext.py
  - src/swing_bsh/grid_targets_ext.py
  - reports/t2_label_density_probe.md
test_command: uv run python -m src.swing_bsh.grid_targets_ext --family high_low --family-only
core_hours_cap: 2.0
---

## 1. Objective and invariant
- Full grid run for the `high_low` family only: 2 learners (`xgboost`, `lightgbm`) × 6 horizons (5,8,13,21,34,55) × 2 markets = 24 cells. Variant pinning: `exact_full_k0.8` (USD), `tol2_full_k0.8` (CAD). Definition: event-window extreme RE-TEST (admin-approved).
- ONE BH-FDR family (m=24 over this sub-grid). Placebo permutation on the largest |AUC−0.5| cells first.
- Invariants: purged/embargoed CV (embargo max(20,h)), CALIB-only selection, float32, symbol-sequential, n_jobs=2, rho prune 0.3.

## 2. I/O contract
- Output: `reports/t2_grid_highlow_summary.md` + pickles `data/models/wi048/` (survivors only).
- Budget check: 24 cells ≈ 0.55 h; cap 2.0 leaves headroom.

## 3. Definition of Done (binary)
- [ ] 24 cells scored or truncated-and-reported; FDR table; pickles for survivors only.
- [ ] Core-hour cap: 2.0, declared in the run footer.

---

## Execution Telemetry Footer

- Commit: PENDING (HEAD d92a7f4; no commit made)
- Test Status: PASS — chain stage EXIT:0 (log logs/wi-048def_run.out, marker EXIT_D:0, chain done 2026-11-13T05:59:32Z); artifacts PM-verified this session
- Index Updated: Y — PM-run outputs; untracked data/ + reports/ artifacts stay out of git
- PM-run verdict (PROVISIONAL): 24 cells scored, 0 truncated; BH-FDR (a=0.05, m=24) survivors 24 — 12 USD + 12 CAD (all 6 horizons, both learners); report reports/t2_grid_highlow_summary.md; 121 pickles on disk; manifest 295 rows == 295 disk pickles (set-identical).
