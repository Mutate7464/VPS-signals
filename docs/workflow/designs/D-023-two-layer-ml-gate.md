# D-023 — Two-layer ML gate: pickle library vs trading overlay

**Status:** adopted (admin, in chat, 2026-11-09) · **Supersedes:** none (structural clarification of the existing gate arithmetic) · **Thread:** D-022 phase 2

## 1. Basis (admin direction, 2026-11-09)

The current pipeline's basis is: (a) **find ML pickles that are good enough** (signal library,
WI-035/036), then (b) **add another ML on top** of the frozen rules (overlay, WI-033/037).
These are different questions and were being answered by one undifferentiated gate. Verified
example: the τ veto threshold in WI-037 is a *trading-strategy* parameter (`pick_tau()` selects
max CALIB-period edge of the filtered frozen rule; AUC/IC never enter), yet its verdict was
presented alongside predictive statistics as if one gate produced it.

## 2. The two layers

**Layer 1 — pickle/library gate (predictive).** Question: is a model cell good enough to keep
in the library? Evidence: pooled OOF AUC + rank-IC, BH-FDR across the grid, calibration quality,
cross-market consistency. Output: pickles under `data/models/wiXXX/` + a ranking report.
Passing Layer 1 licenses **no** trading claim — it only stocks the library.

**Layer 2 — overlay gate (trading decision).** Question: does an ML layer bolted on top of the
frozen rules (veto, chooser, position scaler, regime gate) improve realized trading? All
decision parameters (τ, thresholds, selectors) are tuned on CALIB-period *trading edge* only and
frozen before EVAL. Evidence: edge vs the frozen baseline, fold stability (ADOPT_LOOSE_4OF5),
placebo on the edge statistic (CB-05). Layer-1 statistics never justify a Layer-2 adoption;
a Layer-2 REJECT never retro-doubts the Layer-1 artifact (WI-037's REJECT does not weaken
WI-036's pickles).

## 3. Gate protocol consequences

1. WI specs state which layer they gate. A Layer-1 WI's DoD contains no trading metrics; a
   Layer-2 WI's DoD contains no predictive metrics beyond provenance of the pickles it consumes.
2. Verdicts remain PROVISIONAL until admin ratifies (cycle 28 rule) — for BOTH layers.
3. A Layer-2 WI must name its baseline (frozen rule + costs) and its decision parameter's
   tuning criterion in the spec, before dispatch.
4. Layer-2 adoption criteria may be tuned by admin per WI; Layer-1 criteria stay
   FDR-conservative (selection-multiplicity is the dominant failure mode there).

## 4. Current inventory under this structure

| WI | Layer | Verdict (PROVISIONAL) |
|---|---|---|
| WI-035/036 grid cells | 1 | library stocked (6838 + 96 pickles); b_hold short-h cells pass FDR |
| WI-033 (3-class chooser) | 2 | REJECT — edge below frozen rules |
| WI-037 (P(hold) veto, τ) | 2 | REJECT — τ grid inert at 0.4% prevalence; edge +0.0001 |
| WI-038 (long-horizon grid) | 1 | in flight |
| WI-039 (regime audit) | 1 (descriptive) | robust across regimes; informs whether any future overlay needs regime gating |
