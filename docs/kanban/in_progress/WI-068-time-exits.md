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
- **Attempts:** 4 gate runs / 3 distinct defects — (1) test-side: the per-rule fixture kept its `fib_exit` columns, so the missing-rule `KeyError` could not fire; (2) source: `load_entries` re-derived an artifact's *given* `r_h<h>` columns instead of passing them through → all-NaN horizons → empty entry set; (3) source, found by a read-only check of the full path: a `*_smoke` artifact was picked up as a real entry set, and the `/tmp/wi036` cache is a sparse swing-event panel (median gap 18 d, not daily bars) so "`h` observations" ≠ "`h` dates" and the derived edge was nonsense (+1208 bps) — the cache path now fails closed, smoke artifacts are never scanned in a real run. All fixed; final gate clean | **Commit:** WI-068 commit on base 6bece0b (manifest paths + this card) | **Status:** DONE
- **Evidence:** `uv run pytest tests/l2_overlay/test_time_exit.py -q --tb=short --maxfail=1 && uv run python -m src.l2_overlay.constructions.time_exit --smoke` → exit 0, 12 passed (plus `tests/l2_overlay` 59 passed); smoke USD+CAD best `fixed_h13` net +103.2 bps vs the event exit (-50.0 bps; absolute +68.7 vs -84.5), `hybrid_h13` +33.3 CONTINUE, `fixed_h55`/`hybrid_h55` STOP, identical-entry key `ab0f6f2652dad19c` in all 5 arms, stdout 3 lines.
- **Notes / error tail:** RE-ENTRY JUSTIFICATION paragraph carried in the module docstring per D-027 §7 (structural: no learned chooser, horizons pre-registered; new input: WI-059b read-outs + post-WI-058 families). No EVAL read; the full-run fib path now raises rather than emitting a mis-dated horizon (PM must pass an `--entries` artifact carrying `r_h13`/`r_h55`). DEVIATION: `time_exit.py` is 333 lines vs the 250-line guidance — the mandated I/O contract (entry loading + causal-horizon attachment + report) does not fit; same deviation WI-065 logged. `src/l2_overlay/INDEX.md` is outside this lock manifest and still lacks a line for `constructions/time_exit.py`.
