---
wi_id: WI-068
title: Fixed time-based exits vs event exits on identical entries (code+smoke)
status: draft
agent: surgical-builder
depends_on: ["WI-065"]
gate_layer: "2 (overlay/trading; WI-030 re-entry justification below)"
board_row: "D-027 Phase 3 (a)"
write_files:
  - src/l2_overlay/constructions/time_exit.py
  - tests/l2_overlay/test_time_exit.py
read_only_files:
  - src/l2_overlay/harness.py
  - src/l2_overlay/costs.py
  - src/l2_overlay/fold_report.py
  - docs/workflow/designs/D-027-l2-rebuild.md
test_command: uv run pytest tests/l2_overlay/test_time_exit.py -q --tb=short --maxfail=1 && uv run python -m src.l2_overlay.constructions.time_exit --smoke
---

## 1. Objective and invariant
- Compare pre-registered fixed horizons (h13/h55) and a time/event hybrid (whichever comes first) against event exits on **identical entries**, CALIB-only. Entries from WI-066/067 survivors if alive, else frozen fib baseline. Invariants: n_jobs=2, float32, no EVAL reads.
- **RE-ENTRY JUSTIFICATION (required paragraph — card is defective without it):** WI-030 (learned exit chooser) closed on REJECT; mechanism = selection on predictive stats judged on edge. Structural change: **no learned chooser** — horizons are fixed ex ante and pre-registered. New input: regression read-outs (WI-059b) and post-WI-058 families (xsec/mfe_mae/move_*). D-024 closure binds to the original inputs; this paragraph names both changes per the reopen protocol.

## 2. I/O contract and blueprint (literal)
- Input: entry sets (WI-066/067 outputs or fib baseline artifact via `--entries`), price panel via causal builder. Root named constant.
- Output: CALIB comparison report `reports/l2_time_exit/calib_<market>.md` (per-horizon net edge, fold report, stop/continue); smoke to `*_smoke` paths.
- `time_exit.py`: `simulate_fixed_horizon(entries, h)`, `simulate_hybrid(entries, h, event_rules)` — costs via `costs.single_leg_cost`; fold report emitted every run (fails closed).
- Tests: identical-entry invariant proven (same entries across exit rules); hybrid exits at min(t_event, t_h); net-edge arithmetic matches `costs` exactly; placebo shows nothing.

## 3. Definition of Done (binary)
- [ ] No edits outside `write_files`.
- [ ] `test_command` exits 0; identical-entry and hybrid tests pass.
- [ ] Fold report + stop/continue recorded in report structure.
- [ ] Stdout ≤5 lines.

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes / error tail:** None
