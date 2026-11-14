---
wi_id: WI-065
title: Harness upgrade — union loader, fold report, cost model, pre-registration + EVAL lock
status: draft
agent: surgical-builder
depends_on: []
gate_layer: "N/A (L2 infrastructure)"
board_row: "D-027 Phase 1 (parallel with WI-064)"
write_files:
  - src/l2_overlay/harness.py
  - src/l2_overlay/costs.py
  - src/l2_overlay/fold_report.py
  - tests/l2_overlay/test_harness_union.py
  - tests/l2_overlay/test_fold_report.py
  - tests/l2_overlay/test_costs.py
read_only_files:
  - docs/workflow/designs/D-027-l2-rebuild.md
  - docs/workflow/DATA_CONTRACT.md
test_command: uv run pytest tests/l2_overlay/ -q --tb=short --maxfail=1 && uv run python -m src.l2_overlay.harness --smoke
---

## 1. Objective and invariant
- Extend the WI-041 harness with: (i) union loader for wi040 ∪ wi048 with cell-key dedup (market/learner/variant/family/horizon/fold) + assertion no cell enters twice; (ii) **mandatory fold-report column** (per-fold net edge + max-fold concentration share; run fails closed if missing); (iii) cost model: 50 bps single-leg round trip, 100 bps pair cycle, 100·f turnover, 25 bps × |Δsize| resize; (iv) cross-sectional INERT precheck (≥200 CALIB events + τ span + min-names-per-date parameter); (v) hashed pre-registration file + EVAL lock; (vi) CALIB-failure stop flag. Invariants: n_jobs=2, float32, no EVAL reads before lock release.

## 2. I/O contract and blueprint (literal)
- Input: manifest parquets `data/models/wi040/manifest.parquet` + wi048 consolidated manifest (1,015 rows); root named constant.
- Output: harness smoke report to `reports/l2_harness_smoke/`; pre-registration template `docs/workflow/l2_prereg_template.json` (schema: constructions, params, FDR family list, materiality floor, hash field).
- `src/l2_overlay/harness.py`: add `load_union()` (dedup + assert), `preregistration` load/verify (sha256), EVAL-lock check raising before any EVAL read.
- `src/l2_overlay/costs.py`: pure functions `single_leg_cost()`, `pair_cost()`, `turnover_cost(f)`, `resize_cost(dsize)` — exact bps arithmetic above.
- `src/l2_overlay/fold_report.py`: `fold_report(oof_edges) -> {per_fold_net_edge, max_fold_share}`; emitted on every run; missing ⇒ hard fail.
- Tests: synthetic overlapping keys dedup to expected count; cost tests reproduce 50/100/100f/25·|Δ| exactly; D-024 rerun outputs reproduce unchanged on smoke (regression guard).

## 3. Definition of Done (binary)
- [ ] No edits outside `write_files`.
- [ ] `test_command` exits 0; all three new test modules pass.
- [ ] Fold report fails closed when absent (test proves it).
- [ ] Smoke D-024 regression guard unchanged.
- [ ] Stdout ≤5 lines.

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 1/2 | **Commit:** PENDING (HEAD 6126626; no commit made) | **Status:** DONE
- **Evidence:** `uv run pytest tests/l2_overlay/ -q --tb=short --maxfail=1 && uv run python -m src.l2_overlay.harness --smoke` → 28 passed, harness smoke 3 lines, EXIT 0; D-024 synthetic outputs pinned unchanged (tau 0.7, calib 0.03141, eval 0.03571, z 38.90).
- **Notes / error tail:** deviations — (1) `docs/workflow/l2_prereg_template.json` is outside the lock manifest, so the sha256 template is emitted to `reports/l2_harness_smoke/l2_prereg_template.json` by `--smoke` (also `fold_report.json`); (2) `harness.py` is 389 lines (WI-041's file was already 249; the mandated WI-065 API could not fit the 250-line guidance without dropping it).
