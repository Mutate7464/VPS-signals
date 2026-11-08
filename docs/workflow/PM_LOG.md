# PM_LOG.md — cursor for the Hermes PM cycle

> One entry per PM cycle, newest first. The newest entry's cursor (`cursor:` line)
> defines which opencode sessions the next cycle ingests. Kam's trigger: tell Hermes
> "run PM cycle". Full procedure: `docs/human/PM-CYCLE.md`.

## 2026-11-08 — Cycle 27 (WI-031 verdict adopted: fold-stability gate loosens 5/5 → 4/5)

- **Admin gate discharged in chat ("adopt and make the change"):** WI-031's ADOPT_LOOSE_4OF5 recommendation adopted. Fold-stability bar for gating learned artifacts is now **4/5 folds positive** (n_folds_pos ≥ 4); strict 5/5 retained for re-opening frozen decisions; not retroactive.
- **Basis (WI-031, PM-verified from `reports/fib_swings/gate_comparison.csv`):** chaotic detect 18/20 (4/5) vs 17/20 (strict), NULL FP 0/20 both; `pooled_only_t2` rejected (FP 5/20); 3/5 adds nothing. 469 core-s (3% of cap).
- **Change landed:** new "Gate decisions" section in `docs/tech_approach/fib_swings/README.md`; BOARD last-updated + WI-031 row; WI-031 frontmatter status draft→done. No source change required — the bar is a PM-level decision rule, `n_folds_pos` is computed/reported by code, no 5/5 constant enforced in scripts.
- **Fib ladder: closed.** Deployable core: at-bottom entry + all-bottoms ensemble label + WI-027 regime features + frozen `t15_s10_d39_close` exit; EVAL consumed. Backlog triggers un-fired.
- **Next (admin-gated):** none queued — admin direction required for the next research thread.
- cursor: none — doc-adoption cycle; no new opencode sessions to ingest.

## 2026-11-08 — Cycle 26 (WI-030 exit-policy learning: FAIL, ladder closed)

- **WI-030 (conditional exit policy): FAIL (closed negative)** — XGB multi-class chooser over the 32-cell grid (16 event features + WI-027 regime one-hot + WI-025 horizon prior); oracle = per-event argmax ret. CALIB purged 5-block CV fold-stable 5/5 (+0.61%/event pooled OOF) but **below the single frozen cell** `t15_s10_d39_close` on both CALIB (+1.07%) and EVAL (+0.80% vs +2.14%; edge −1.34pp). Per-event policy selection does not generalize; oracle argmax label too noisy at 76k events.
- **Implication:** frozen cell stands as exit policy; EVAL consumed (one-shot, 2026-11-08). Deployable core of the fib signal: at-bottom entry (WI-028) + all-bottoms ensemble label (5/5 fold-stable) + rule-based regime labels as features (WI-027).
- **Ladder status:** WI-027→030 complete. Backlog triggers un-fired (synthetic validation triggers on "edge but borderline fold-stability" — WI-030 produced no edge).
- **Charter updated:** `docs/tech_approach/fib_swings/README.md` rows 2b (DEAD) and 3 (FAIL).
- **Next (admin-gated):** ladder close-out — admin gate on close vs synthetic-data validation of the fold-stability guard.
- cursor: ses_e469cc56dffefRNPRVh5ztEo6g (WI-030 opencode session; ingest next cycle if WI-030 codebase questions arise)
