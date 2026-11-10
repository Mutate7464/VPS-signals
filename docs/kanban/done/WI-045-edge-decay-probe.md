---
wi_id: WI-045
title: Decompose why CALIB edge dies before EVAL on the ratified WI-042 artifacts
status: done
verdict: PASS (diagnostic probe — PROVISIONAL, advisory only)
agent: surgical-builder
depends_on: []
gate_layer: "1"
board_row: "D-025 tiered workflow (admin direction 2026-11-10)"
write_files:
  - src/l2_overlay/edge_decay_probe.py
  - tests/test_edge_decay_probe.py
read_only_files:
  - reports/l2/rerun_modern.json
  - src/l2_overlay/harness.py
  - src/l2_overlay/rerun_modern.py
  - docs/workflow/designs/D-025-tiered-workflow.md
test_command: uv run pytest tests/test_edge_decay_probe.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
- On the ratified WI-042 cells (smoke on synthetic, PM full-run for real numbers): quantify which mechanism kills the CALIB→EVAL edge — (a) tau-mass concentration (how many events the selected tau actually trades), (b) fold concentration (is the CALIB edge one fold, e.g. fold-1?), (c) cost floor (is raw edge < 25 bps everywhere). Output ranks the three mechanisms by share of edge decay. Host invariants: no re-fit of learners; read-only inputs; float32, symbol-sequential.
- Gate layer L1: this is a diagnostic on frozen artifacts — no trading metrics beyond the already-computed edges, no new verdicts.

## 2. I/O contract and blueprint (literal)
- Output: `reports/l2/edge_decay_probe.md` (+ `.json`): per adopted cell, CALIB edge decomposition (fold-wise edges, event counts at tau, gross-vs-net edge), and a one-line mechanism ranking across the family.
- Smoke: `--smoke` on synthetic fixtures to /tmp. Tests: decomposition identities on synthetic data (gross - costs = net; fold shares sum to CALIB edge).

## 3. Definition of Done (binary)
- [x] Decomposition table for all 20 ratified ADOPT cells; mechanism ranking stated; report derives only from the frozen JSON + recomputed returns.
- [x] No edits outside write_files; test_command exit 0. Core-hour cap: 0.3.

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 1/2 (one in-session assertion fix on a fixture expectation; no escalation) | **Commit:** PENDING (no commit made) | **Status:** DONE (code + tests + probe report)
- test_command `uv run pytest tests/test_edge_decay_probe.py -q --tb=short --maxfail=1` → exit 0 (11 passed, 1.7s); identities asserted on synthetic CALIB-only fixtures (gross-cost=net, fold contributions reconstruct the CALIB edge exactly under uniform per-fold keeping, shares sum to 1, payload never mutated); smoke `--smoke --out /tmp/l2_edge_decay_probe_smoke` → 3 synthetic cells, no EVAL rows (`n_eval=0`), ranking line rendered; core-hour use ≪0.3 (JSON read + arithmetic, zero learner inference).
- Full-run 2026-11-10 in-session (foreground, EXIT:0, <1s) on the frozen `reports/l2/rerun_modern.json` → `reports/l2/edge_decay_probe.{md,json}`: 20 ratified ADOPT cells. Ranking (decay 87.0 bps): **1. fold-concentration 55.0% (drives 17 cells); 2. cost-floor 44.8% (3); 3. tau-mass 0.2% (0)** — mass kept 99.5–99.99% everywhere (tau is NOT the killer), top fold = fold 1 in 18 cells (share to 1.00), and the 25 bps cost floor binds in all 20 cells (net edge 0.22–9.83 bps). Read-only: no refit, no EVAL rescoring, no new verdicts; PROVISIONAL per the gate rule.
