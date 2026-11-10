# D-024 — Layer-2 overlay rebuild + old-L2 rerun protocol

Admin direction 2026-11-10: "accept changes. work on next WI. rerun old L2s." WI-038 PROVISIONAL PASS ratified in chat same day (long-h b_hold survivors join the L1 library). This design rebuilds the Layer-2 method/layer and re-runs the seven rejected L2 attempts under it.

## 1. Why the old L2 layer failed (mechanisms, from gate records)

1. **Inert decision grids on thin probability mass** — WI-037: calibrated P(hold) max ~0.011 at prevalence ~0.4%; the τ grid had no feasible operating point, so the "edge" was noise around +0.0001.
2. **Selection on predictive stats, judged on trading edge** — WI-030: the learned exit chooser won 5/5 CALIB folds on its training criterion yet landed below the frozen cell on CALIB (+0.61% vs +1.07%) and EVAL (+0.80% vs +2.14%). Criterion and verdict mismatched by construction.
3. **Overlays vs a strong frozen baseline** — WI-033: 4/5 fold stability but pooled edge −0.15pp vs frozen rules; fold stability of a difference is not edge.
4. **Cross-market transfer** — WI-012: NO_TRADE cross-market confirmed; USD-tuned decisions did not carry to CAD.
5. **Bespoke per-WI scripts** — every attempt re-implemented its own tuning/judging loop, so anti-cherry-picking protections varied by author and no cross-WI FDR was applied to the overlay family.

## 2. What structurally changes (the rebuild)

- **One harness, not seven scripts**: `src/l2_overlay/` implements the protocol once — named frozen baseline + costs, decision params tuned ONLY on CALIB-period edge (grep-verifiable criterion), one-shot EVAL, 5-seed placebo on the edge, and an **INERT** verdict when the calibrated probability mass cannot span the pre-registered τ range (fixes mechanism 1: an INERT verdict records "no operating point exists" instead of burning EVAL on noise).
- **Library-first inputs**: overlays read the WI-040 manifest (`data/models/wi040/manifest.parquet`) and its `--infer` entrypoint — no bespoke refits. Multi-horizon probability mass now includes the WI-038 long-h survivors (h∈{34,55,89}), the missing input in every prior attempt.
- **Feasibility precheck + event floors**: each overlay cell must carry ≥ 200 CALIB events and a τ range spanning the observed calibrated probability distribution, or it is INERT before any edge is computed.
- **Cross-WI FDR**: the seven reruns are one BH-FDR family (mechanism 5) — an overlay only ADOPTs if its CALIB edge survives family-wide correction.
- **Pre-committed closure**: on REJECT under this harness, an overlay question closes permanently (second-REJECT rule from WORKFLOW); the frozen artifact stands. Admin waived fresh probes for the reruns by explicit direction 2026-11-10 — waiver recorded here per protocol.

## 3. Rerun batch (admin direction: rerun old L2s)

| Old WI | Question | Runnable code | Status |
|---|---|---|---|
| WI-037 | b_hold veto on frozen fib entries | `src/swing_bsh/hold_filter_gate.py` | rerun under harness, multi-h inputs |
| WI-033 | 3-class swing-conditioned overlay | `src/swing_bsh/{train,evaluate}.py` | rerun under harness |
| WI-030 | learned exit chooser vs frozen exit | `scripts/fib_exit_policy.py` | rerun with edge-tuned criterion |
| WI-028 | entry-window chooser | `scripts/fib_entry_window.py` | rerun with edge-tuned criterion |
| WI-012 | cross-market transfer gate | `src/xgb_trainer.py` + harness | port question to harness |
| WI-018 | first-touch 34 overlay | `src/wi018/cost_overlay.py` | port question to harness |
| WI-011 | condition-first meta overlay | `scripts/wi011_*`, `src/wi011/` | port question to harness |

## 4. WI plan (approval matrix presented in chat 2026-11-10)

- **WI-041** — build `src/l2_overlay/` harness (protocol code + tests + smoke on one legacy question). Cap 0.5 core-h. Probe-first substitute: harness smoke IS the probe; admin's rerun waiver is recorded.
- **WI-042** — rerun the four modern L2s (037/033/030/028) under the harness. Cap 1.0 core-h.
- **WI-043** — port + rerun the three legacy L2s (012/018/011). Cap 1.5 core-h. Depends on WI-042's verdicts (a strong REJECT on the modern four can close the thread before the legacy ports burn budget).
