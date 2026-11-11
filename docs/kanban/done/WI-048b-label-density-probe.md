---
wi_id: WI-048b
title: T2 label-density probe — measure prevalence per family/horizon on both markets, dry-run selection
status: draft
agent: pm
depends_on: [WI-048a]
gate_layer: "1"
board_row: "D-025 tiered workflow (admin direction 2026-11-10)"
parent: WI-048
write_files:
  - reports/t2_label_density_probe.md
read_only_files:
  - src/swing_bsh/targets_ext.py
  - reports/wi016_label_density_USD.csv
  - reports/wi016_label_density_CAD.csv
test_command: uv run python -m src.swing_bsh.targets_ext --probe
core_hours_cap: 0.2
---

## 1. Objective and invariant
- Measure label prevalence per family (`up` / `high_low` / `vol_expand`) × horizon (5,8,13,21,34,55) × market (USD, CAD) — no training. This is the dry-run the brief names: denser market = measured label-density CSV.
- Output: prevalence table per cell; identify the denser market per family; flag cells below a minimum positive count (recorded as sparse, reported not dropped).
- Invariants: no training, no EVAL, no model files; float32, symbol-sequential reads.

## 2. I/O contract
- Output: `reports/t2_label_density_probe.md` (prevalence table + density ranking + sparse-cell flags).
- Smoke gate: this WI is the smoke gate for WI-048c/d/e.

## 3. Definition of Done (binary)
- [ ] Prevalence measured for all 3 families × 6 horizons × 2 markets; denser market identified per family; sparse cells flagged.
- [ ] Core-hour cap: 0.2 (label computation only, n_jobs=2).

## 4. Execution Telemetry
- Commit: PENDING (HEAD bd80bd5; no commit made)
- Test Status: PASS — full-universe probe run by PM: `uv run python -m src.swing_bsh.targets_ext --probe` → EXIT:0, 36 cells, reports/t2_label_density_probe.md
- Result: no sparse cells (all 36 ≥ 25 positives); denser market = USD for all three families (mean prevalence: up 0.546, high_low 0.849, vol_expand 0.499); geometry pinned per market (USD exact, CAD tol2)
- Notes: PM-run (no builder); smoke gate for WI-048c/d/e passed. Full-universe job NOT run by builder — run by PM.
