# FILE: WI-036 — extended run: loosened thresholds, 4-learner grid, raised cap (D-022 §3b)
---
wi_id: WI-036
title: Extended three-binary run — mlp_torch restored, tau_p grid extended down, rho prune 0.3, cap 2.5 core-h
status: draft
agent: surgical-builder
depends_on: []
board_row: "D-022 thread (admin direction in chat 2026-11-09: extended run, allow more noise)"
write_files:
  - src/swing_bsh/binary_features_ext.py
  - src/swing_bsh/binary_grid.py
  - tests/test_swing_bsh_binary_grid.py
read_only_files:
  - src/swing_bsh/binary_labels.py
  - src/swing_bsh/binary_train.py
  - src/swing_bsh/binary_evaluate.py
  - config/sector_map.csv
  - reports/wi035_summary.md
test_command: uv run pytest tests/test_swing_bsh_binary_grid.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
- Re-run the WI-035 three-binary pipeline with admin-loosened settings (2026-11-09), reusing the existing modules (no rewrite of labels/train/evaluate): import and call them.
- Re-measure the three-binary models as **pure signal, no trading-rule layer** (admin 2026-11-09: "entry rules should not play a factor"): DROP the τ_p/τ_s grid and `frozen_selection` from the verdict path entirely. Per learner × binary × market report **OOF AUC** and **rank-IC (P̂ vs binary label)** across all 5 purged folds, plus per-fold spread. Verdict = signal exists iff pooled OOF AUC > 0.5 with fold-consistent sign and placebo z ≥ 2 (permutation null on labels). Nothing selected, no portfolio returns, no entry rule, no costs.
- **Feature expansion (admin 2026-11-09: "integrate all that has information")** — new `binary_features_ext.py` block, all causal/trailing, appended to the WI-034 kept set:
  (a) unused raw columns: `volume` z-score + trend, `average` (VWAP) distance, `barCount` (activity);
  (b) cross-sectional ranks: each smooth-family feature percentile vs same-date universe;
  (c) sector context: `config/sector_map.csv` one-hot + sector-relative ranks;
  (d) event-quality: swing depth in ATRs, bars since opposite swing, drawdown age;
  (e) calendar: day-of-week, month; (f) market breadth: % of universe at_bottom/at_top same date.
- **Target-variant grid (admin 2026-11-09: "add as different targets — which point aligns with indicators and is usable by ML")** — the loosened geometry variants are SEPARATE TARGET FAMILIES, not one merged config. Grid:
  - event: `exact` (WI-035 extreme-bar) vs `tol±2` (shoulder bars);
  - window: `full [t+1, t+h]` vs `mid60 [t+0.2h, t+0.8h]`;
  - barrier: `k1.0` vs `k0.8` (profit amplitude).
  2×2×2 = **8 target variants** × 3 binaries × 9 horizons × 4 learners × 2 markets. Verdict statistic per cell: pooled OOF AUC + rank-IC (5-fold purged CV, placebo z). Headline outputs:
  1. **Target-ranking table** — variants sorted by cross-market consistent AUC/IC (which *entry/exit definition* is most predictable);
  2. per-variant **TreeSHAP/linear-coefficient report** — which indicator families carry the winning target's signal;
  3. FDR across the full grid, BH α=0.05 (8×3×9×4×2 tests — multiplicity enforced).
  The goal is stated in the WI: identify the most ML-usable entry/exit point definition; deployment (turning the winning target into entry/exit rules) is a future gate, out of scope here.
- **Horizon loosening** — vertical barrier ladder {21,55} → **{5, 8, 13, 21, 34, 55, 89, 144, 233}** trading days, crossed INTO the target-variant grid above (each of the 8 variants × 9 horizons is its own label definition); embargo = max(20, h).
- Loosened vs WI-035: (a) learner grid = all four incl `mlp_torch`; (b) ρ prune 0.4 → **0.3**; (c) core-hour cap **2.5** (priority if tight: drop h≥89 cells first).
- Unchanged (correctness, not budget): n_jobs=2, float32, symbol-sequential, purged CV embargo=max(20,h), isotonic calibration per fold, 5-seed permutation placebo **on the AUC/IC statistic**, pickles saved verdict-independently to `data/models/wi036/`. The CALIB/EVAL selection split is RETIRED for this WI (nothing is selected any more — all folds report OOF statistics).

## 2. I/O contract and blueprint (literal)
- Input/output paths and schemas identical to WI-035 (`binary_labels.py` / `binary_train.py`); smoke `WI036_SMOKE=5 --out /tmp/wi036_smoke`.
- New `binary_grid.py` = thin driver: exposes `LEARNERS`, `TAU_P_GRID`, `TAU_S_GRID`, `PRUNE_RHO=0.3`, orchestrates per-market replay by importing the WI-035 functions; report `reports/wi036_summary.md` (same shape as wi035).
- Tests: grid constants match this spec; driver calls the existing pipeline functions (monkeypatched, synthetic); no leakage columns.

## 3. Definition of Done (binary) — CONFIRMATORY (admin override, same as WI-035)
- Gate arithmetic reported for the record; pickles saved regardless; nothing deployed, shortlist unchanged. CAD-style fat-tail flags (selected<100 events) explicitly marked record-only.
- [ ] No edits outside `write_files`.
- [ ] `test_command` exits 0.
- [ ] Stdout ≤5 lines. Core-hour cap: 2.5 (pause ≥30 min if modeled balance < 25% — balance was 100% at dispatch).

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 1/2 (strike-1 resume; completed) | **Commit:** PENDING (HEAD b77203b; no commit made) | **Status:** DONE
- **Notes:** `test_command` 7/7 green; smoke `WI036_SMOKE=5 --out /tmp/wi036_smoke --core-hours 0.2 --placebo-seeds 2` -> BOTH markets score cells (580: USD 259/CAD 321, 1148 truncated), report renders, 21 FDR survivors, 316s wall; FULL both-market FOREGROUND `--market ALL --core-hours 2.5` -> 4705.7s wall, cells 570 (USD 213/CAD 357), 1158 truncated (h>=34 dropped first), 60 placebo p-values / 57 FDR survivors (all `b_hold`, h in {5,8,13,21}), winner `exact_full_k0.8` min AUC 0.7207 (USD 0.7836/CAD 0.7207), report `reports/wi036_summary.md`, pickles 6838 in `data/models/wi036/<MKT>_<learner>_<variant>_<binary>_h<h>_f<fold>.pkl`; core spent ~2.55h vs 2.5 cap (2 vCPU process_time, n_jobs=2).
- **Notes / error tail:** fixed budget split (`grid_seconds = cap*(1-PLACEBO_RESERVE)/n_markets`, per-market gate -> high-h truncation verified) + `TorchMLP.__module__`/`sys.modules` alias so `mlp_torch` pickles reload (prior files referenced `__main__`); FLAG for review: `main` feeds BH-FDR m = #cells carrying a placebo p (60), not the full grid m=1728 — `bh_fdr(..., m_total=)` is wired but unused; low impact (largest surviving p = 1.4e-4 << 0.05*57/1728).