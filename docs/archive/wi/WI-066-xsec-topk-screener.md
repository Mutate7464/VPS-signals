---
wi_id: WI-066
title: Single-signal cross-sectional top-k screener (code+smoke; full CALIB run is PM gate)
status: draft
agent: surgical-builder
depends_on: ["WI-065"]
gate_layer: "2 (overlay/trading; frozen baseline + CALIB-only tuning declared below)"
board_row: "D-027 Phase 2 (b)"
write_files:
  - src/l2_overlay/constructions/xsec_rank.py
  - tests/l2_overlay/test_xsec_rank.py
read_only_files:
  - src/l2_overlay/harness.py
  - src/l2_overlay/costs.py
  - src/l2_overlay/fold_report.py
  - docs/workflow/designs/D-027-l2-rebuild.md
test_command: uv run pytest tests/l2_overlay/test_xsec_rank.py -q --tb=short --maxfail=1 && uv run python -m src.l2_overlay.constructions.xsec_rank --smoke
---

## 1. Objective and invariant
- Small **pre-registered** set of single-signal cross-sectional rankers per market — long-only first, long/short second, with rank hysteresis (enter top-k, exit below top-2k). Candidate signals: xsec_vol_rank_cont, move_occur×move_dir_up product, b_hold. Tune ONLY on CALIB (k, band, hold horizon); k constrained to ~4 trades/week (operator capacity ~200/yr). Invariants: n_jobs=2, float32, no EVAL reads.
- Layer-2 declaration: baseline = frozen fib rule + 50 bps round trip; decision parameters (k, band, horizon) tuned on **CALIB net edge only**, frozen before any EVAL. Fold-report ceiling and materiality floor apply (D-027 §7).

## 2. I/O contract and blueprint (literal)
- Input: union library scores via `src/l2_overlay/harness.load_union()`; prices via the existing causal panel builder. Root named constant.
- Output: CALIB report `reports/l2_xsec_rank/calib_<signal>_<market>.md` + positions parquet `data/models/l2_xsec_rank/` (float32); smoke to `*_smoke` paths only.
- `xsec_rank.py`: functions `rank_scores(panel, signal)`, `topk_with_hysteresis(scores, k, band)`, `simulate(entries, costs)` — costs via `costs.single_leg_cost` / `turnover_cost`; emit fold report every run (fails closed).
- Tests: synthetic planted-signal recovered net of cost; placebo (shuffled scores) shows nothing; CALIB report includes fold distribution, turnover f, net edge; stop/continue recorded per signal.

## 3. Definition of Done (binary)
- [ ] No edits outside `write_files`.
- [ ] `test_command` exits 0; planted-signal and placebo tests pass.
- [ ] Fold report emitted and ceiling check wired (50% max-fold share; majority-positive).
- [ ] Stdout ≤5 lines.

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 3 test-command runs / 2 distinct defects (missing parquet parent dir; card token) — both fixed, final run clean | **Commit:** PENDING (HEAD e72434157d6e; no commit made) | **Status:** DONE
- **Compute:** START_UTC 2026-11-14T22:36Z / END_UTC 22:41Z ≈ 0.05 core-h (cap 2.5) | NEXT_ALLOWED_RUN_UTC: none (no burst ≥1 core-h)
- **Notes:** code+tests only; no EVAL read; smoke stdout 3 lines; module 249 lines (single blank line between top-level defs to hold the 250-line cap). Smoke artifacts: reports/l2_xsec_rank_smoke/, data/models/l2_xsec_rank_smoke/ (both `*_smoke`).
