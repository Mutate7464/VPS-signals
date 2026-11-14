# Brief — WI-011: condition-first meta-analysis (tradeable conditions → decision rules)

You are the planner. Write ONE plan file, overwriting the existing draft at:
`docs/plans/2026-10-25-WI-011-condition-first-meta-analysis.md`
(contract format: GOAL / CONSTRAINTS / STEPS with acceptance + deterministic verify
commands / OUT OF SCOPE / pointer to the sibling execution log). You may edit ONLY
that path and `docs/workflow/designs/**`. Do NOT touch BOARD.md or the log file.
Read nothing else in the repo except the files named below.

## Read first
1. `docs/plans/2026-10-25-WI-011-condition-first-meta-analysis.md` — the current
   draft (admin brainstorm + amendments): scope, usage spec, steps 1/1b/2/3/4/5.
2. `docs/plans/2026-10-24-WI-009-contrastive-learning.md` — executed plan:
   harness, walk-forward/purge discipline (20td), report conventions to reuse.
3. `docs/plans/logs/WI-011-condition-first-meta-analysis.md` — the log stub you
   must NOT edit (exists, STATUS: PLAN).
4. AGENTS.md guardrails (2 vCPU/8 GB, n_jobs=2, float32, no full-universe frames).

## Scope (admin direction 2026-10-25 — fixed, do not re-open)
- **Descriptive meta-analysis, NO ML, no trained models, no binary-target rebuild.**
- Conditions are trailing, point-in-time, per-symbol; built from
  `src/targets.py`/E5 primitives + the empirically-selected indicator subset
  (Step 1b), NOT the full 89-feature pile.
- Step 2 horizon sweep {1,2,5,10,15,20,60,120}d IS the core; Step 3 TS-momentum
  probe never ran before (all prior runs cross-sectional); Step 4 cost overlay
  with the 1-action/day preference (not cap): conditions firing 100–400×/yr,
  5–15d concurrency envelope 4–12 positions.
- "None survive costs at this universe size" is a valid, publishable answer.
- Step 5 decision rules are data specs, NOT backtested-optimized — STOP at the
  human gate before any backtest/optimization.

## Plan requirements
- Steps ≤ 6 (draft's 1/1b/2/3/4/5 structure is approved — keep it), each with:
  action, acceptance criteria, a deterministic verify command
  (`uv run python scripts/<step>.py && grep -E "<markers>" reports/wi011_<step>.md`),
  and what NOT to do.
- Step 0: verify inputs (CAD parquet row counts, alignment) before anything.
- Budget: all steps minutes-scale on this host (no training runs); n_jobs=2;
  sequential symbol iteration; float32.
- Reports to `reports/wi011_*.md`; end the plan with `STATUS: PLAN` in the
  contract's status section, pointing at the sibling log.
- Same-sign clause (WI-009b/c standing rule) applies to any "stable-sign
  condition" acceptance wording.