# PM_LOG.md — cursor for the Hermes PM cycle

> One entry per PM cycle, newest first. The newest entry's cursor (`cursor:` line)
> defines which opencode sessions the next cycle ingests. Kam's trigger: tell Hermes
> "run PM cycle". Full procedure: `docs/human/PM-CYCLE.md`.

## 2026-11-09 — Cycle 29 (admin ratifies WI-039/WI-037; Layer-1 focus; WI-038 full run dispatched)

- **Admin ratification in chat ("focus on layer 1 improvements … approve ones that provisional pass"):** WI-039 PROVISIONAL PASS → **PASS RATIFIED** (b_hold robust across regimes, NOT regime-gated; Layer-1 artifact stands). WI-037 PROVISIONAL REJECT → **REJECT RATIFIED, confirmed as a Layer-2 trading verdict** (overlay gate vs frozen rules; τ tuned on CALIB edge — `hold_filter_gate.py:110 pick_tau()`); per D-023 it does not retro-doubt the WI-036 Layer-1 pickles.
- **Admin direction:** focus on Layer 1 (pickle library) improvements; proceed with model development. All open provisional verdicts now resolved; WI-036 PASS and earlier verdicts stand as issued.
- **WI-038 (Layer-1 long-horizon gap fill):** builder pass audited earlier (test_command exit 0, smoke 0.126 core-h); PM dispatched the full-universe run `python -m src.swing_bsh.binary_grid_longh --market ALL` (cap 2.0 core-h, h∈{34,55,89,144,233}); credit balance 100% (3.0 h burst room) at dispatch. Verdict to be recorded on completion — PROVISIONAL until admin ratifies.
- **Next (admin-gated):** WI-038 close-out + ratification; then next Layer-1 direction per D-023 §4 coverage audit (remaining gap: admin-deferred WI-034 binary-decompose probe).
- cursor: none — doc-adoption cycle; no new opencode sessions to ingest.

## 2026-11-09 — Cycle 29b (WI-040 approved; L2 rebuild queued as the following WI)

- **Admin approval in chat ("approve. proceed with current WI; next WI will include rebuilding L2 method and layer"):** WI-040 (L1 library consolidation — manifest across wi035/036/038 pickles, winner-cell calibration + Brier, permutation attribution, `--infer` entrypoint; cap 0.5 core-h) APPROVED — dispatch after WI-038 closes; lock manifest `src/swing_bsh/library_audit.py` + `tests/test_swing_bsh_library_audit.py`.
- **Admin direction for the WI after WI-040: rebuild the Layer-2 method/layer.** All seven prior L2 attempts (WI-011/012/018/028/030/033/037) REJECTed vs the frozen rules; a rebuild must therefore come as a NEW design doc naming why the prior mechanism failed and what structurally changes — present matrix for admin gate before drafting WIs. Sequence: WI-038 close-out → WI-040 → L2 rebuild design + matrix.
- **WI-038 run note:** full-universe attempt 1 died at the PM's own tool timeout (EXIT 143, no grid output; partial pickles written — overwritten by attempt 2, idempotent). Attempt 2 relaunched as a tracked background process with notify-on-complete.
- cursor: none.

## 2026-11-09 — Cycle 28 (gate verdicts become PROVISIONAL — admin ratification required)

- **Admin direction in chat ("confirm gate protocol … change to human intervention instead of automatic"):** every computed gate verdict (ADOPT/REJECT/INCONCLUSIVE, `evaluate.verdict()`) is now **PROVISIONAL — advisory only** until the admin ratifies it in chat. No adoption, rule change, artifact promotion, or thread close follows a computed verdict without an explicit admin decision. Doc-only change — grep evidence: the bar (`FOLD_THRESHOLD`=4, `PLACEBO_Z_MIN`=2.0 in `src/swing_bsh/evaluate.py`) is computed/reported by code, application is a PM-level step; no source constant changed.
- **Admin direction in chat (same day, "current basis is finding ML pickles good enough and adding another ML on top — change gate/structure"):** two-layer ML gate adopted as `designs/D-023-two-layer-ml-gate.md`. Layer 1 = pickle-library gate (predictive: OOF AUC/IC + BH-FDR + calibration; stocks `data/models/`; licenses no trading claim). Layer 2 = overlay gate (trading: decision parameters such as τ tuned on CALIB-period edge only — verified: `hold_filter_gate.py:110 pick_tau()` selects max CALIB edge, never AUC — frozen before EVAL, judged by edge vs the named frozen baseline + fold stability + placebo on the edge). WI specs must state their layer; layers never cross-justify; Layer-2 REJECT never retro-doubts Layer-1 artifacts (WI-037 REJECT leaves WI-036 pickles intact).
- **Retroactive layer audit (admin, same day, "revisit old WI to confirm layer-1 items attempted"):** D-023 §4 now holds the full layer map — every Layer-1 direction confirmed attempted except the admin-DEFERRED WI-034 probe (binaries × variants × horizons: WI-035/036/038; meta labels: WI-016; ranking: WI-009b; classifier route: WI-009c NEG; regime conditioning: WI-027+039; screening: WI-014). Every Layer-2 attempt (WI-011/012/018/028/030/033/037) has REJECTed/failed vs the frozen rules. Integration: `gate_layer` frontmatter key added to `_TEMPLATE_WI.md`; WORKFLOW two-layer section now requires checking D-023 §4 before drafting new Layer-1 WIs.
- **Landed in ONE commit:** WORKFLOW.md "Provisional-verdict rule" (QA/GATE table note); AGENTS.md hard-constraints bullet; `docs/tech_approach/fib_swings/README.md` Gate decisions entry; BOARD WI-037/WI-039 rows re-labelled PROVISIONAL + last-updated header.
- **Open provisional verdicts awaiting admin:** WI-037 REJECT (τ grid inert, edge +0.0001); WI-039 robust-across-regimes (top-regime share 0.36/0.45 < 0.60); WI-038 long-horizon grid in flight. WI-036 PASS and earlier verdicts stand as issued (rule not retroactive).
- **Next (admin-gated):** WI-038 close-out, then admin decision on the D-022 thread.
- cursor: none — doc-adoption cycle; no new opencode sessions to ingest.

## 2026-11-08 — Cycle 27 (WI-031 verdict adopted: fold-stability gate loosens 5/5 → 4/5)

- **Admin gate discharged in chat ("adopt and make the change"):** WI-031's ADOPT_LOOSE_4OF5 recommendation adopted. Fold-stability bar for gating learned artifacts is now **4/5 folds positive** (n_folds_pos ≥ 4); strict 5/5 retained for re-opening frozen decisions; not retroactive.
- **Basis (WI-031, PM-verified from `reports/fib_swings/gate_comparison.csv`):** chaotic detect 18/20 (4/5) vs 17/20 (strict), NULL FP 0/20 both; `pooled_only_t2` rejected (FP 5/20); 3/5 adds nothing. 469 core-s (3% of cap).
- **Change landed:** new "Gate decisions" section in `docs/tech_approach/fib_swings/README.md`; BOARD last-updated + WI-031 row; WI-031 frontmatter status draft→done. No source change required — the bar is a PM-level decision rule, `n_folds_pos` is computed/reported by code, no 5/5 constant enforced in scripts.
- **Fib ladder: closed.** Deployable core: at-bottom entry + all-bottoms ensemble label + WI-027 regime features + frozen `t15_s10_d39_close` exit; EVAL consumed. Backlog triggers un-fired.
- **Next (admin-gated):** none queued — admin direction required for the next research thread.
- cursor: none — doc-adoption cycle; no new opencode sessions to ingest.
