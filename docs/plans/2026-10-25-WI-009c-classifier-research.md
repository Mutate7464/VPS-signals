# 2026-10-25 — WI-009c — Classifier route to usable targets (RESEARCH / PROPOSAL, not an execution plan)

> Status: DRAFT for admin decision. Written by PM (Hermes) at admin direction
> ("note/plan for next run with classifier route — keep open ended").
> This doc aligns the goal (usable screener targets) with what exists and states
> the open questions. No gate is claimed; nothing here is executed.

## Goal alignment (where this fits)

- Product goal (G-001/D-003 Option 2): a **shortlist** — ranked tickers with a
  defensible probabilistic statement ("upward potential ≥ 10%-ish move",
  "downward risk", "stays within ±5%"). Admin's 2026-10-25 direction names the
  three target families explicitly; the ±5% band now exists as `y_20d_stay`.
- What WI-009b bought us: a **verifiable evaluation harness** (same-row
  factor-vs-model comparison, purge/embargo splits, skill-bar clauses) and a
  **negative result** — the pairwise ranker learns a stable inverse signal on
  the recent CAD window (every epoch negative; sign question open at the gate).

## What already exists (reuse, don't rebuild)

| Piece | State | Notes for WI-009c |
|---|---|---|
| `src/xgb_trainer.py` | done, USD run | Purged walk-forward XGB, per-fold calibration (isotonic→Platt CB-04), placebo seeds, SHAP drivers, `--targets` flag already parameterized |
| `src/model_qa.py` + Gate 4 | done | PR-AUC lift > 1.35× prior, P@K ≥ 1.5, BSS > 0.05, deflated IC > 0.04/t > 2.5, placebo CB-05 (AUC > 0.52 & z > 3) |
| `src/targets.py` | +`y_20d_stay` (2026-10-25) | 5 targets now; CAD base rates: up 18.5% / down 10.9% / stay 44.8% / high 29.8% / low 32.2% |
| Gate-3 whitelists | USD done | CAD catalog was rebuilt with the 2026-10-23 panel; a `y_20d_stay` whitelist needs a Sprint-3 metadata pass |
| WI-009b harness | done | `src/models/skill_bar.py`, within-date rank-IC, purge gap — reusable for classifier score evaluation |

## The decisive prior: Gate 4 on USD (2026-10-21/22)

All four USD class targets ≈ random (IC ≤ 0.01, PR-AUC lift ≤ 1.09, every gate
FAIL — `reports/sprint4_model_qa.md`). WI-002's E-diagnostics interpreted this
as **H2/H4: real signal lives in the continuous forward-ATR-return space;
binary labels + class-label gates are blind to it** (E5 factors significant
there). So the classifier route is not a fresh start — it is the known-negative
branch, and WI-009c must answer *why CAD + these targets would differ* before
spending compute.

## Open research questions (admin picks scope; none are decided)

1. **Is the class-target failure a label problem or a feature problem?**
   WI-002 showed E5 factors carry significant signal in continuous space on
   both USD and CAD. Test cheaply: logistic/GBM on the **5 E5 factors only** per
   class target. If factors alone fail the class gates but win in continuous
   space, the labels (not the features) are the bottleneck → target redesign
   (e.g. ATR-scaled move bands), not more model.
2. **Does the rebuilt CAD panel change the Gate 4 verdict?** The stale
   2026-10-21 CAD run predated the fib expansion + R-08 index fix + quarantine
   triage. A CAD `xgb_trainer` run on the current panel (with placebo + Gate 4
   metrics) is the missing datum — but see Q1 first; it bounds expectations.
3. **Should the target family move to ordinal/threshold-probabilistic?**
   Admin's phrasing ("upward potential of 10% or downward 10%, within 5%") is a
   3-class ordinal band on the *same* 20d forward move — currently realized as
   independent binary labels. Options: (a) independent binaries per band
   (current), (b) one 3-class multinomial (up/stay/down), (c) **regression on
   the continuous move + derive band probabilities from the forecast
   distribution** (closest to WI-002's finding that continuous space carries
   signal). (c) also eliminates the up/down overlap ambiguity (`2×ATR` dollar
   vs ±5% relative thresholds can both fire).
4. **Alignment question: Gate 4 metrics vs the skill bar.** Gate 4 grades class
   discrimination (PR-AUC lift, P@K); WI-009b added the factor-baseline skill
   bar. For a *screener*, the deliverable metric is top-decile/shortlist quality
   — decide which bar governs WI-009c before running (re-specification is the
   same class of question as the WI-009b sign clause).
5. **What carries over from WI-009b's negative result?** The ranker's stable
   inverse signal may be exploitable *as a feature* (negated score → down-side
   candidate ranking) rather than as the final ranker. Cheap to test as an
   additional feature in Q1/Q2 models; risky to ship standalone (regime
   inversion, single window).
6. **Compute order (PM proposal, not decided):** Q1 (factor-only logistic, all 5
   targets, CAD+USD) → Q3 design pick informed by Q1 → then, only if Q1 shows the
   labels are learnable, the full `xgb_trainer` CAD run. Each step is cheap
   (logistic fits are minutes); the expensive Gate-4-style run comes last.

## Guardrails carried over

- Purge/embargo discipline unchanged (20td); no live trading (MVP boundary);
  shortlist-only output, human gate before any execution use (product boundary).
- `y_20d_stay` is relative-return based while up/down are ATR-dollar based —
  unit mismatch is deliberate (admin wording) but must be stated in any report
  that pools the three (see Q3c).
- WI-010 (classifier/script consolidation) is unrelated but touches the same
  `src/` — sequence around it.

## Decision asked of admin

Pick Q-order and the target design (a/b/c from Q3); whether the Gate-4 bar or
the skill bar governs; then WI-009c gets a planner pass → execution plan → Build.

---

## ADMIN DIRECTION (2026-10-25, cycle 9 close) — supersedes "Decision asked"

- **WI-009b gate: HOLD + re-spec** (see gate brief decision record). Same-sign
  clause adopted into every future skill bar — **including WI-009c's**.
- **Q3 design: combo (c), continuous-first** — regression on the continuous
  20d forward move is the *starting point*; band probabilities
  (up/down/stay ±5%) derive from its forecast distribution rather than from
  independent binary classifiers. Factor-only logistic probe (Q1) stays as the
  cheap step-1 bound on label learnability.
- **Robustness techniques in scope as candidates** (admin: "assume these will
  change training/params"): regime-aware features (per-market-state feature
  sets), ensemble/stacked weak signals, dynamic feature selection. NONE were
  built in WI-009/009b (verified against the executed plan + code: no regime,
  ensemble, stacking, or dynamic-selection constructs exist). They enter here
  as scoped Build options, each behind the cheap probe.
- **Contrastive ranker role:** `scripts/rank_assets.py` (WI-009 Step 4) already
  refines to top-10 by scalar score + pairwise win-rate confidence; under the
  combo design it becomes one *input* to the stack, not the final ranker.