---
wi_id: WI-048
title: T2 prediction expansion — umbrella (split into WI-048a/b/c/d/e/f, 2026-11-10)
status: draft
agent: pm
depends_on: []
gate_layer: "1"
board_row: "D-025 tiered workflow (admin direction 2026-11-10)"
core_hours_cap: 3.4 (aggregate)
---

## 1. Objective and invariant
- Implement three TARGET FAMILIES as explicit grid axes (never merged with label-geometry knobs):
  (a) directional `up`, (b) extreme-touch `high_low` (event-window extreme re-test), (c) volatility `vol_expand`.
- ONE BH-FDR family per sub-grid (m=24 each); learners = `xgboost` + `lightgbm` (library learners only);
  variant pinning = `exact_full_k0.8` (USD) / `tol2_full_k0.8` (CAD).
- Correctness invariants are not budget knobs: purged/embargoed CV (embargo max(20,h)), CALIB-only selection,
  float32, symbol-sequential, n_jobs=2, rho prune 0.3.

## 2. Split (admin-approved 2026-11-10: over-aggregate OK, per-WI caps hold)
- WI-048a | builder | label builders + synthetic tests + smoke | 0.05
- WI-048b | PM | label-density probe (prevalence per family/h/Market, dry-run) | 0.2
- WI-048c | PM | full grid `up` (24 cells) | 2.0
- WI-048d | PM | full grid `high_low` (24 cells) | 2.0
- WI-048e | PM | full grid `vol_expand` (24 cells) | 2.0
- WI-048f | PM | cross-family summary + FDR + attribution | 0.3
- Aggregate: ~3.4 core-h vs 2.0 original; per-WI cap 2.0 ≤ 2.5 policy default. No WI breaches its own cap.

## 3. Definition of Done (binary)
- [ ] WI-048a–f all done; `reports/t2_targets_ext_summary.md` produced; no single WI over its cap.
- [ ] Verdict PROVISIONAL until admin ratification in chat.
