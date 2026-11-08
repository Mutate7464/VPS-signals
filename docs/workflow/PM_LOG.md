# PM_LOG.md — cursor for the Hermes PM cycle

> One entry per PM cycle, newest first. The newest entry's cursor (`cursor:` line)
> defines which opencode sessions the next cycle ingests. Kam's trigger: tell Hermes
> "run PM cycle". Full procedure: `docs/human/PM-CYCLE.md`.

## 2026-11-08 — Cycle 26 (WI-030 exit-policy learning: FAIL, ladder closed)

- **WI-030 (conditional exit policy): FAIL (closed negative)** — XGB multi-class chooser over the 32-cell grid (16 event features + WI-027 regime one-hot + WI-025 horizon prior); oracle = per-event argmax ret. CALIB purged 5-block CV fold-stable 5/5 (+0.61%/event pooled OOF) but **below the single frozen cell** `t15_s10_d39_close` on both CALIB (+1.07%) and EVAL (+0.80% vs +2.14%; edge −1.34pp). Per-event policy selection does not generalize; oracle argmax label too noisy at 76k events.
- **Implication:** frozen cell stands as exit policy; EVAL consumed (one-shot, 2026-11-08). Deployable core of the fib signal: at-bottom entry (WI-028) + all-bottoms ensemble label (5/5 fold-stable) + rule-based regime labels as features (WI-027).
- **Ladder status:** WI-027→030 complete. Backlog triggers un-fired (synthetic validation triggers on "edge but borderline fold-stability" — WI-030 produced no edge).
- **Charter updated:** `docs/tech_approach/fib_swings/README.md` rows 2b (DEAD) and 3 (FAIL).
- **Next (admin-gated):** ladder close-out — admin gate on close vs synthetic-data validation of the fold-stability guard.
- cursor: ses_e469cc56dffefRNPRVh5ztEo6g (WI-030 opencode session; ingest next cycle if WI-030 codebase questions arise)

## 2026-11-07 — Cycle 25 (fib research ladder: 3 WIs executed, charter established, session close)

- **WI-027 (rule-based regime labels): PASS** — `up_high/USD` 5/5 fold-stable +22.75pp, `chop_normal/ALL` 5/5 +3.89pp. Fold5 isolated to failing regimes. Rule-based labels chosen for downstream.
- **WI-027b (unsupervised GMM): FAIL** — 0 pooled fold-stable states. Per-market 5/5 combos found but don't aggregate. Soft probs kept as supplementary features.
- **WI-028 (entry-window study): INCONCLUSIVE → k=0 dominates** — at-bottom entry 5/5 +0.73% full vol; k=3/5 worse on every metric. Confirmation falsified. At-bottom entry adopted.
- **Four cheap probes:** ensemble all-bottoms label 5/5 fold-stable (adopted as y); ensemble screened 4/5; regime-gated too sparse; sector grouping no 5/5; sequential depth no isolation. GMM probe showed random-CV 20/20 passes while blocked-CV catches regime concentration.
- **Decisions:** all-bottoms ensemble as label; screen_bottom promoted to filter→feature; at-bottom entry; WI-027 rules as regime features; fold-stability guard unchanged; EVAL virgin (consumed by WI-030 on 2026-11-08).
- **Charter:** `docs/tech_approach/fib_swings/README.md` — full ladder WI-027→030 with supplements.
- **Session findings:** `docs/tech_approach/fib_swings/FINDINGS_2026-11-07.md`.
- **Next (admin-gated): WI-030** — executed as cycle 26 (FAIL, closed).
- cursor: none — PM-side execution; superseded by cycle 26 cursor.
