---
wi_id: WI-042
title: Rerun the four modern L2 overlays (037/033/030/028) under the D-024 harness with multi-horizon library inputs
status: done
verdict: RATIFIED (admin in chat 2026-11-10) — closures stand (REJECT/INERT, per pre-committed D-024 closure); 20 computed ADOPTs ratified as "statistically real, economically nil" (EVAL edges ~0.00000 vs 25 bps costs) — NO deployment
gate_layer: L2
agent: surgical-builder
depends_on: [WI-041]
board_row: "D-024 L2 rebuild (admin direction in chat 2026-11-10: rerun old L2s)"
write_files:
  - src/l2_overlay/rerun_modern.py
  - tests/test_l2_rerun_modern.py
read_only_files:
  - src/l2_overlay/harness.py
  - src/swing_bsh/library_audit.py
  - src/swing_bsh/hold_regime_audit.py
  - src/swing_bsh/binary_features_ext.py
  - src/swing_bsh/hold_filter_gate.py
  - src/swing_bsh/evaluate.py
  - scripts/fib_exit_policy.py
  - scripts/fib_entry_window.py
  - docs/workflow/designs/D-024-l2-overlay-rebuild.md
test_command: uv run pytest tests/test_l2_rerun_modern.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
- Rerun the four rejected overlays — WI-037 (b_hold veto), WI-033 (3-class swing overlay), WI-030 (exit chooser), WI-028 (entry-window chooser) — through `harness.run_overlay`, each vs its NAMED frozen baseline + costs, inputs from the WI-040 manifest now including WI-038 long-h survivors (h in {34,55,89}).
- Input wiring (D-024 §2): model probabilities via manifest `--infer` (features recomputed causally at the decision bar — WI-016 grid + WI-036 expansion incl. event-quality metafeatures `swing_depth_atr`/`bars_since_opp`/`dd_age`, cross-sectional/sector/breadth blocks); **regime metafeatures** (WI-027 labels via `hold_regime_audit`) as an explicit conditioning axis — regime-conditioned and unconditional cells share ONE BH-FDR family (no conditioning free-lunch).
- **Stacked meta-learner input (admin direction 2026-11-10 "add other MLs"):** a CALIB-fit elastic-net logistic stack over the multi-horizon b_hold probability vector (h in {5,8,13,21,34,55,89} from the manifest pickles) is an additional overlay input — one more decision-score source beside the raw per-cell probabilities. The stack is fit on CALIB folds only and frozen before EVAL; its cells join the same BH-FDR family.
- Structural changes vs the originals (D-024 §2): CALIB-only tuning with edge criterion, feasibility precheck (INERT before EVAL burn), 5-seed placebo on edge, BH-FDR across the 4 reruns as ONE family. Admin rerun waiver recorded (D-024 §2).
- Pre-committed closure: REJECT under this harness closes that overlay question permanently.

## 2. I/O contract and blueprint (literal)
- Output: `reports/l2/rerun_modern.md` (per overlay: verdict INERT/ADOPT/REJECT, tau, calib/eval edge, folds, placebo z, FDR-adjusted p) + `reports/l2/rerun_modern.json`.
- Smoke: `L2_SMOKE=5` on 5 symbols per market to /tmp (never touches EVAL scoring on partial data — smoke stops at feasibility precheck).
- Tests: each of the 4 questions maps to a baseline config; FDR family = every tested cell (question × regime-conditioning), never pooled with WI-043's family; smoke excludes EVAL.

## 3. Definition of Done (binary)
- [ ] All four overlays produce verdicts (INERT allowed and honest); FDR table across the family.
- [ ] No edits outside write_files; test_command exit 0; stdout <=5 lines. Core-hour cap: 1.0 (inference + edge grids; learners are NOT re-trained).

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 2/2 (strike-1 resume: PRECHECK-OK cosmetic on the verified 341-line file) | **Commit:** PENDING (HEAD 80fb9bb; no commit made) | **Status:** DONE (code + tests only)
- test_command `uv run pytest tests/test_l2_rerun_modern.py -q --tb=short --maxfail=1` → exit 0 (12 passed, 1.74s); smoke-mode cells that clear the precheck now carry verdict `PRECHECK-OK` (synthetic smoke check: verdicts {INERT, PRECHECK-OK}, family_size 0, no EVAL touched).
- **full-universe run NOT run - PM owns it per WI contract** (smoke artifact `/tmp/l2_rerun_modern_smoke/rerun_modern.md` predates this cosmetic edit).
- PM full-run 2026-11-10 (detached, EXIT:0, 29.2s, USD 32,100 + CAD 17,256 entries; 91 cells / 30 tested, family `wi042_modern_l2_rerun`, α=0.05): verdict counts {ADOPT 20, INCONCLUSIVE 1, INERT 49, REJECT 21}; `reports/l2/rerun_modern.{md,json}`. PM verdict: closures stand; all ADOPT edges are statistically real (placebo z to +5.88, q to 2e-8) but economically nil — EVAL edges ~0.00000 vs 25 bps costs — no deployment. RATIFIED (admin in chat 2026-11-10, "proceed with recs"). Known gaps: wi033 raw h21 USD INERT from missing manifest cell; chop_normal untestable (<200 CALIB events).
