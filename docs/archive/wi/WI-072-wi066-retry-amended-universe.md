---
wi_id: WI-072
title: WI-066 retry — amended-universe xsec top-k screener (code+smoke; full CALIB = PM gate)
status: draft
agent: surgical-builder
depends_on: ["WI-066", "WI-068"]
gate_layer: "2 (overlay/trading; CALIB-only tuning declared below)"
board_row: "D-027 Phase 2 (b) retry"
write_files:
  - src/l2_overlay/constructions/xsec_rank.py
  - src/l2_overlay/constructions/b_hold_scores.py
  - tests/l2_overlay/test_xsec_rank.py
  - tests/l2_overlay/test_b_hold_scores.py
read_only_files:
  - src/l2_overlay/harness.py
  - src/l2_overlay/costs.py
  - src/l2_overlay/fold_report.py
  - scripts/build_l2_prepared.py
  - docs/workflow/designs/D-027-l2-rebuild.md
test_command: uv run pytest tests/l2_overlay/test_xsec_rank.py tests/l2_overlay/test_b_hold_scores.py -q --tb=short --maxfail=1 && uv run python -m src.l2_overlay.constructions.xsec_rank --smoke && uv run python -m src.l2_overlay.constructions.b_hold_scores --smoke
---

## 1. Objective and re-open basis (admin chat 2026-11-15)
Re-open of the WI-066 (b) CALIB kill, per admin direction ("do not blacklist — assume L0/L1 data can be modified to make it work"). Named new inputs: (1) amended universe (ALL swing events, ≥20-name quorum — cycle 41 panel), (2) rebuilt b_hold OOF coverage (0 scored events was a WI-035 coverage gap, not a verdict), (3) widened signal set from the union library, (4) wider CALIB grid + long/short pass. Falsifiers UNCHANGED: 10 bps net floor, fold ceiling 50% max-share + majority-positive (admin 2026-11-15: keep as kill). WI-068(a) fixed_h55 provisional survivor stays in the test set — this WI does not touch it.

## 2. Scope (code + synthetic tests + smoke ONLY; PM runs full CALIB)
- `xsec_rank.py`: (a) generic signal column — score any union-library cell by name (score column in the panel; keep the 3 existing named signals); (b) widen grids: HORIZON_GRID adds {10, 21, 34}, BAND_GRID adds {2.0, 3.0} (larger band = lower turnover; USD died on f=0.51 cost); (c) `direction="long"|"long_short"` mode — long bottom-k with symmetric hysteresis in the L/S pass, pre-registered as D-027 §5 second pass.
- NEW `b_hold_scores.py`: rebuild b_hold (1−P(hold)) OOF scores for the amended universe using the WI-035 feature list from pickle provenance (23 features); fold split matches the prepared panel's fold column; writes `data/models/l2_b_hold_scores/<MKT>.parquet` (float32) + smoke to `*_smoke`. n_jobs=2, no EVAL reads.
- Tests: planted-signal recovery net of cost (long and L/S); placebo (shuffled scores) shows nothing; grid-widening reduces turnover on a synthetic high-churn fixture; b_hold smoke produces finite scores on a synthetic panel with the 23-feature schema.
- Layer-2 declaration: baseline = frozen fib rule + 50 bps round trip; all decision params tuned on CALIB net edge only, frozen before EVAL (WI-071).

## 3. Definition of Done (binary)
- [x] No edits outside `write_files`.
- [x] `test_command` exit 0; planted-signal, placebo, turnover and b_hold-schema tests pass.
- [x] Smoke artifacts under `reports/l2_xsec_rank_smoke/`, `reports/l2_b_hold_scores_smoke/`, `data/models/*_smoke/`.
- [x] Stdout ≤5 lines per module.

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 1 | **Commit:** PENDING (HEAD df00421; no commit made) | **Status:** DONE
- **Compute:** 2026-11-15T19:38:13Z / 2026-11-15T19:39:19Z ≈ 0.02 core-h (cap 2.5) | NEXT_ALLOWED_RUN_UTC: n/a (burst ≪ 1 core-h)
- **Notes:** test_command exit 0 (24 passed; 86 in tests/l2_overlay). xsec smoke 61 s of 66 s = 6 signals × 2 passes × 60-trial grid; planted L/S +263 bps gross vs 100 bps pair cycle, placebo −159 bps net. b_hold smoke uses stub fold models (no fit); its full CALIB run is PM-gated (`--full`) and, per the prepared panel's `fold` column, only folds 0–1 carry rows — the other ~38.7k rows stay NaN by design.
