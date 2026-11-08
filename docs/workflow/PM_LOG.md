# PM_LOG.md — cursor for the Hermes PM cycle

> One entry per PM cycle, newest first. The newest entry's cursor (`cursor:` line)
> defines which opencode sessions the next cycle ingests. Kam's trigger: tell Hermes
> "run PM cycle". Full procedure: `docs/human/PM-CYCLE.md`.

## 2026-11-07 — Cycle 25 (fib research ladder: 3 WIs executed, charter established, session close)

- **WI-027 (rule-based regime labels): PASS** — `up_high/USD` 5/5 fold-stable +22.75pp, `chop_normal/ALL` 5/5 +3.89pp. Fold5 isolated to failing regimes. Rule-based labels chosen for downstream.
- **WI-027b (unsupervised GMM): FAIL** — 0 pooled fold-stable states. Per-market 5/5 combos found but don't aggregate. Soft probs kept as supplementary features.
- **WI-028 (entry-window study): INCONCLUSIVE → k=0 dominates** — at-bottom entry 5/5 +0.73% full vol; k=3/5 worse on every metric. Confirmation falsified. At-bottom entry adopted.
- **Four cheap probes:** ensemble all-bottoms label 5/5 fold-stable (adopted as y), ensemble screened 4/5, regime-gated too sparse, sector grouping no 5/5, sequential depth no isolation. GMM probe showed random-CV 20/20 passes while blocked-CV catches regime concentration.
- **Decisions:** all-bottoms ensemble as label; screen_bottom promoted to filter→feature; at-bottom entry; WI-027 rules as regime features; fold-stability guard unchanged; EVAL virgin.
- **Charter:** `docs/tech_approach/fib_swings/README.md` — full ladder WI-027→030 with supplements (sector, ensemble, survival, backlog).
- **Session findings:** `docs/tech_approach/fib_swings/FINDINGS_2026-11-07.md`.
- **Next (admin-gated): WI-030** — conditional exit policy on the stable all-bottoms ensemble label, regime + event features, horizon-adaptive optional.
- cursor: none — PM-side execution; next cycle ingests WI-030 opencode session when dispatched.

## 2026-11-02 — Cycle 24 (WI-019 MVP closeout executed PM-side; gate ACCEPT)

- **Gate decision (admin in-chat 2026-11-02): ACCEPT** — WI-019 closed DONE: repo consolidation, governance docs (`docs/{governance,architecture,execution}/`), INDEX/AGENT routing, negative-knowledge register stand as delivered; suite 662 passed EXIT:0 verified (`logs/wi019_full_suite.out`); commit `c9b9b7c`.
- **Phase 2 now open:** first sprint = P-1 module splits (debt D-1 blueprint, 34 files >250 lines) per `docs/governance/PHASE2_HANDOVER_RUNBOOK.md`; D-019 recalibration governs any post-MVP research; MVP baseline tag available on demand (`561f299`).
- cursor: none — PM-side session; next cycle ingests any Phase-2 opencode sessions.

## 2026-11-02 — Cycle 24 (WI-019 MVP closeout executed PM-side; QA/GATE open)

- **Admin closeout spec executed in-session** (3 steps, no Build dispatch — docs/consolidation work): discovery audit (34 source files >250 lines) → `git mv` `Design/` + root `plan.md` into `docs/archive/` (signals preserved, nothing deleted) → governance artifacts created: `docs/governance/MVP_CLOSURE_REPORT.md` (sign-off matrix, velocity variance, debt register D-1..D-10), `PHASE2_HANDOVER_RUNBOOK.md` (P-1..P-7 backlog + rollback to `561f299`), `docs/execution/WI_AND_RUN_LEDGER.md` (19-WI reconciliation), `docs/architecture/DECISIONS_AND_NEGATIVE_KNOWLEDGE.md` (6 ADRs + 12 negative entries) → INDEX.md in src/+11 dirs, root `AGENT.md` (<180 words), `.aiignore`/`.cursorrules`, README + docs-router links repaired.
- **Source splits DEFERRED** (spec-sanctioned): MVP code-frozen post-ACCEPT; blueprint = debt register D-1, first Phase 2 task.
- Board: WI-019 BACKLOG → ACTIVE **QA/GATE**, awaiting admin ACCEPT; suite re-verify detached `logs/wi019_full_suite.out`.
- cursor: none — PM-side session; next cycle ingests any Phase-2 opencode sessions.
