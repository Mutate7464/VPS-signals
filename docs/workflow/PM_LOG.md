# PM_LOG.md — cursor for the Hermes PM cycle

> One entry per PM cycle, newest first. The newest entry's cursor (`cursor:` line)
> defines which opencode sessions the next cycle ingests. Kam's trigger: tell Hermes
> "run PM cycle". Full procedure: `docs/human/PM-CYCLE.md`.

## 2026-11-09 — Cycle 28 (gate verdicts become PROVISIONAL — admin ratification required)

- **Admin direction in chat ("confirm gate protocol … change to human intervention instead of automatic"):** every computed gate verdict (ADOPT/REJECT/INCONCLUSIVE, `evaluate.verdict()`) is now **PROVISIONAL — advisory only** until the admin ratifies it in chat. No adoption, rule change, artifact promotion, or thread close follows a computed verdict without an explicit admin decision. Doc-only change — grep evidence: the bar (`FOLD_THRESHOLD`=4, `PLACEBO_Z_MIN`=2.0 in `src/swing_bsh/evaluate.py`) is computed/reported by code, application is a PM-level step; no source constant changed.
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
