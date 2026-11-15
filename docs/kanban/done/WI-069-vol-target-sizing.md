---
wi_id: WI-069
title: (c) Vol-target entry-only sizing on CALIB survivor (conditional)
status: draft
agent: surgical-builder
depends_on: ["WI-066"]
gate_layer: "2 (overlay/trading; conditional — dispatch only on admin go after a CALIB survivor exists)"
board_row: "D-027 Phase 4 (c)"
write_files:
  - src/l2_overlay/constructions/vol_target.py
  - tests/l2_overlay/test_vol_target.py
read_only_files:
  - src/l2_overlay/harness.py
  - src/l2_overlay/costs.py
  - src/l2_overlay/fold_report.py
  - docs/workflow/designs/D-027-l2-rebuild.md
test_command: uv run pytest tests/l2_overlay/test_vol_target.py -q --tb=short --maxfail=1 && uv run python -m src.l2_overlay.constructions.vol_target --smoke
---

## 1. Objective and invariant
- CONDITIONAL WI (D-027 §6): dispatch only if WI-066/067/068 produced a CALIB survivor AND admin gives the go; otherwise skip and log the skip. Volatility-target sizing on the surviving construction, **sized at entry only** (no mid-trade resizing; that would cost 25 bps × |Δ|). Inputs: xsec_vol_rank_cont, regime metafeatures, disp_entropy_39. Attacks fold-concentration IF folds differ by vol regime. Invariants: n_jobs=2, float32, no EVAL reads.

## 2. I/O contract and blueprint (literal)
- Input: survivor entries artifact + causal feature panel (vol/regime columns). Root named constant.
- Output: CALIB report `reports/l2_vol_target/calib_<market>.md` — risk-adjusted edge sized vs unsized, fold report with regime attribution; smoke to `*_smoke`.
- `vol_target.py`: `target_weights(panel, ann_vol_target) -> weights` (entry-only, no intraday resizing); `compare_sized_vs_unsized()` with fold report (fails closed).
- Tests: weights constant within trade (entry-only invariant); sized-vs-unsized edge arithmetic via `costs`; placebo shows nothing.

## 3. Definition of Done (binary)
- [ ] No edits outside `write_files`.
- [ ] `test_command` exits 0.
- [ ] Fold report + stop/continue recorded.
- [ ] Stdout ≤5 lines.

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 1/2 | **Commit:** PENDING (HEAD 1d6d0c8; no commit made) | **Status:** DONE
**Notes:** PM-verified interactive close-out: pytest exit 0 (9 passed), smoke EXIT 0 (reports/l2_vol_target_smoke/), only-manifest files touched; full CALIB run = PM gate, stays with interactive session.
- **Evidence:** `uv run pytest tests/l2_overlay/test_vol_target.py -q --tb=short --maxfail=1 && uv run python -m src.l2_overlay.constructions.vol_target --smoke` → exit 0, 9 passed in 1.39s, smoke 2 markets, stdout 4 lines; artifacts `reports/l2_vol_target_smoke/{calib_USD,calib_CAD}_smoke.md` + `fold_{USD,CAD}_smoke.json`.
- **Notes:** survivor input root constant `ENTRIES_ROOT=data/models/l2_time_exit` (`<market>_fib.parquet`, arm `r_h55`; `xsec_vol_rank_cont` is the forward WI-058 label ⇒ attribution axis only, asserted weight-blind). Read-only real-path check (no non-smoke artifacts written — PM owns the full run, D-027 §6): USD unsized +329.4 → sized +218.3 bps (Δ −111.1), CAD +600.6 → +453.8 (Δ −146.7), fold ceiling FAILS on the single fallback fold id ⇒ STOP both markets; 4 CAD rows take the documented `min_weight` entry-vol policy. File is 350 lines vs the 250-line guidance (siblings time_exit 333 / stack_rank 356). No EVAL read.
