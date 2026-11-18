# Brief — WI-009c: classifier route to usable targets (continuous-first combo)

You are the planner. Write ONE plan file to:
`docs/plans/2026-10-25-WI-009c-classifier-route.md`
(contract format: GOAL / CONSTRAINTS / STEPS with acceptance + verify commands /
EXECUTION LOG table / final `STATUS: PLAN` line). You may edit ONLY that path,
`docs/workflow/BOARD.md`, and `docs/workflow/designs/**`. Read nothing else in
the repo except the files named below.

## Read first
1. `docs/plans/2026-10-25-WI-009c-classifier-research.md` — the research doc
   (open questions + ADMIN DIRECTION section = your scope).
2. `docs/plans/2026-10-24-WI-009-contrastive-learning.md` — the WI-009 executed
   plan: harness, splits, purge discipline to reuse.
3. AGENTS.md guardrails.

## Scope (admin direction 2026-10-25 — fixed, do not re-open)
- **Continuous-first combo**: regression on the continuous 20d forward move is
  the STARTING POINT; band probabilities (up ≥2×ATR-dollar / down ≤−2×ATR /
  stay within ±5% RELATIVE) DERIVE from the regressor's forecast distribution
  (conformal or quantile split, planner's choice — state the choice and why).
  NOT three independent binary classifiers.
- **Step 1 stays the cheap probe**: logistic on the 5 E5 factors only, per
  existing target, purged CV — bounds whether the LABELS are learnable before
  any feature spend. (Prior: Gate 4 USD all 4 targets ≈ random.)
- **Contrastive score as a stacked INPUT feature** (from
  `models/contrastive_ranker_wi009b.pt` via `score_numpy`) — candidate, not
  the ranker; final ranking stays the derived-band-probability composite.
- **Robustness candidates, each gated on step-1 evidence, NOT all built**:
  regime-aware features (e.g. trailing market state buckets), signal stacking
  (factor + contrastive + regressor), dynamic feature selection. Plan them as
  OPTIONAL steps with explicit evidence-based go/no-go criteria.
- **Skill bar carries the same-sign clause** (WI-009b decision): clause (a) =
  same sign as best factor AND |IC| ≥. Any model failing it is a documented
  negative result, not a FAIL-to-hide.
- Dataset: CAD (`data/features/features_CAD.parquet`, 89 float32 features,
  targets incl. new `y_20d_stay`). Purge/embargo 20td unchanged. No live
  trading; shortlist only.

## Plan requirements
- Steps ≤ 6, each with: action, acceptance criteria, a deterministic verify
  command (`uv run python ... && grep ...`), and what NOT to do (STOP-at-gate rows).
- Step 0 verifies inputs (row counts 701,599 CAD targets; stay base ≈44.8%).
- Budget: probe = minutes; regressor = one detached chain run (~1–2 h max);
  report `reports/wi009c_*.md` regenerated per run.
- End with `STATUS: PLAN`.