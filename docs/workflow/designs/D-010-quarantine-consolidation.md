# D-010 — Quarantine classifier consolidation

## Context
WI-010 has three divergent verdict paths (17/55, 11/61, and the repaired tested module at 13/59). Volume corroboration can independently vote for a split-lookalike, risking false positives on genuine crash/regime moves. WI-008 approved consolidation, with row-level decisions reserved for a human.

## Options considered
1. Keep the OR-of-signals rule: minimal code change, but a volume vote can override contrary path/level evidence.
2. Make a persistent non-unity level step and an isolated multi-day path jointly necessary; retain volume as displayed evidence, not an independent verdict vote.
3. Leave the rule unchanged and only report the experiment.

## Decision
Use option 2, but execute the persistence-guard-only anchor experiment first and document its results before editing the rule. Validate the resulting rule against the 2020-03-09 crash cluster, GME, and ICL; report verdict flips against the 17/55 baseline. No report recommendation changes quarantine state.

## Consequences
- Positive: a single volume anomaly cannot label a ticker split-like; the final rule explicitly requires both persistent level-step and isolated-path evidence, with anchor cases and flip symbols reviewable.
- Negative: stricter conjunction may change additional per-row verdicts and may miss genuine corporate actions with non-isolated paths; the gate must review the full table. The rule must be reconsidered if anchor evidence contradicts the intended treatment.

## Status
proposed
