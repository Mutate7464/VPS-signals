# WI-009c gate decision record (human stream) — 2026-10-25

**Decision: A — CLOSE AS NEGATIVE RESULT.** Admin direction ("a close out 009c.
note findings", 2026-10-25). The classifier route is closed; no model ships
from it. The factor-baseline screener stands as the MVP signal.

## What was run (all loop-v2 headless, PM-verified)

1. **Step 1 — factor-only probe** (the cheap gate): logistic on the 5 E5
   factors, purged walk-forward, 1,615 OOF dates, all 5 binary targets.
2. **Step 2 — continuous 20d forecast**: regression on the continuous forward
   move (the combo core), band probabilities derived from its distribution.
3. **Step 3 — stacked contrastive input**: WI-009b score as fold-safe feature.
4. **Step 4 — robustness candidates**: regime features, signal stacking,
   dynamic feature selection — each behind an explicit evidence gate.

## Findings (the durable knowledge)

- **Labels are the bottleneck, not features.** 0/5 binary targets are
  learnable *by the factors that demonstrably carry signal in continuous
  space* — so no richer feature set would have rescued them. Confirmed by the
  89-feature spend staying gated (Step 1(d)) and every robustness option
  reading NO-GO for the same reason.
- **The continuous route dies at the same place.** The 5-factor continuous
  forecast is pure noise (|IC| 0.0001 vs `vol_20` 0.0307). WI-002's "signal
  lives in continuous space" was true of *recent-window factors*, not of
  anything a model learns from the 89-feature history.
- **The pattern across three independent methods** (WI-002 Gate-4 fail,
  WI-009b sign inversion, WI-009c probe): on this CAD universe and window,
  *the E5 factors themselves are the signal*. `vol_20` (recent window),
  `mom_12_1` + `amihud_20` (full history) are the only things that ever
  cleared a bar honestly.
- **Process findings:** the same-sign skill-bar clause (adopted at WI-009b
  close) did exactly its job — three separate sign-inverted "wins" were
  caught and reported as negatives instead of shipped. Loop-v2 (headless
  planner + Build) ran the whole route in one session with honest STATUS
  lines and zero silent failures; STOP clauses and evidence gates fired as
  designed (nothing was built that its gate didn't justify).

## Consequence

- The screener MVP ranks by factor baseline (documented in
  `reports/wi009c_summary.md` §4); the P(up)−P(down) shortlist composite from
  the Step-2 noise forecast is **not** usable for trading and is not shipped.
- Follow-ups unchanged: WI-010 (quarantine classifier consolidation,
  BACKLOG), ELE re-download (Mac/IBKR, admin-owned). Any future model work on
  this universe starts from a *new target/data spec*, probe-first, carrying
  the same-sign clause.

Full evidence: `reports/wi009c_summary.md` (gate package),
`reports/wi009c_probe.md`, `reports/wi009c_regression.md`,
`reports/wi009c_robustness.md`; plan
`docs/plans/2026-10-25-WI-009c-classifier-route.md` (all steps [x]);
commits `92f4716`, `7187ccf`, `4443539`, `43b7681`.