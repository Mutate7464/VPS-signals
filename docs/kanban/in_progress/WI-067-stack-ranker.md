---
wi_id: WI-067
title: Regularised L2 stack ranker over union + meta OOF (code+smoke)
status: draft
agent: surgical-builder
depends_on: ["WI-064", "WI-065", "WI-066"]
gate_layer: "2 (overlay/trading; CALIB-only fit, beats-best-single-signal guard)"
board_row: "D-027 Phase 2 (b), step 2"
write_files:
  - src/l2_overlay/constructions/stack_rank.py
  - src/l2_overlay/prune.py
  - tests/l2_overlay/test_stack_rank.py
read_only_files:
  - src/l2_overlay/harness.py
  - src/l2_overlay/constructions/xsec_rank.py
  - src/l2_overlay/fold_report.py
  - docs/workflow/designs/D-027-l2-rebuild.md
test_command: uv run pytest tests/l2_overlay/test_stack_rank.py -q --tb=short --maxfail=1 && uv run python -m src.l2_overlay.constructions.stack_rank --smoke
---

## 1. Objective and invariant
- Earn use of the full union: (1) pre-cluster correlated cells by OOF correlation on CALIB; (2) keep cluster representatives **inside the harness and logged, never silently dropped**; (3) fit elastic-net logistic or ridge CALIB-only on cluster scores + meta-label OOF (WI-064 artifact) + regime metafeatures; (4) feed stack score into the WI-066 ranker. Invariants: n_jobs=2, float32, chunked loading, cluster BEFORE fit, purged CV, no EVAL reads.
- Layer-2 guard (WI-033 pattern): stack must beat the best single signal from WI-066 on CALIB net edge AND on the fold report; otherwise it stops.

## 2. I/O contract and blueprint (literal)
- Input: union OOF scores (harness loader), `data/models/l2_meta_oof/<MARKET>_oof.parquet` (WI-064 PM artifact; smoke uses `*_smoke` variant), regime metafeatures from the causal panel builder.
- Output: stack scores + CALIB report `reports/l2_stack_rank/calib_<market>.md`; smoke to `*_smoke` paths.
- `prune.py`: `cluster_by_correlation(oof_matrix, threshold) -> {cell: cluster, rep: cluster}` + full pruning log (every input cell listed with its cluster).
- `stack_rank.py`: `fit_stack(X_calib, y_calib)` (elastic-net/ridge, CALIB only), `score()`; memory guard: smoke-scaled extrapolation asserts peak < 8 GB.
- Tests: synthetic correlated cells cluster as expected; pruning log complete; stack-beats-single guard triggers stop when it should; leakage test (EVAL rows absent from fit).

## 3. Definition of Done (binary)
- [ ] No edits outside `write_files`.
- [ ] `test_command` exits 0; pruning-log completeness test passes.
- [ ] Beats-best-single guard wired with stop behavior proven by test.
- [ ] Stdout ≤5 lines.

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes / error tail:** None
