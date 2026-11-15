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
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes / error tail:** None
