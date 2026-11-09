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

## 4. Retroactive layer map of all WIs (audit 2026-11-09, from BOARD rows + reports)

**Layer 1 — pickle library / predictive (attempted):**

| WI | What was attempted | Outcome |
|---|---|---|
| WI-002 | diagnose original model signal | closed → pivot (WI-009) |
| WI-009/009b | contrastive ranking of signals | NEGATIVE (baseline not beaten); same-sign clause adopted |
| WI-009c | classifier route on ranked signals | NEGATIVE (no usable model) |
| WI-010 | quarantine classifier consolidation (47 reinstated) | ACCEPT (classifier hygiene) |
| WI-014 | E5 factor screener (CSV + PDF) | ACCEPT (descriptive screening) |
| WI-016 | triple-barrier + meta labels (CAD), 133 TRADE / 15 NO_TRADE shortlist | ACCEPT; library entry (behind human gate) |
| WI-017 | brute-force target/feature confirmation | ACCEPT (confirmation) |
| WI-025 | quantile magnitude ranking | fib chain member (record) |
| WI-032 | swing-event probe (13/19 FDR-sig features, same-sign, placebo clear) | CLEAR |
| WI-035 | three-binary models h21 k1.5, confirmatory | no-edge CONFIRMED; 96 pickles |
| WI-036 | 8 variants × 9 h × 3 binaries × 4 learners × 2 markets, pure-signal AUC/IC + BH-FDR | 57 FDR survivors, ALL b_hold short-h; 6838 pickles |
| WI-039 | regime-conditional audit of the winning cell | robust across regimes (PROVISIONAL) |
| WI-038 | h ∈ {34,55,89,144,233} gap fill (the truncated high-h cells) | in flight |

**Layer 1 — NOT yet attempted:** only the WI-034 binary-decompose probe (per-binary univariate IC
decomposition of first-touch labels; staged in `ready/`, admin-DEFERRED 2026-11-09 as superseded
by the WI-035/036 outcome). Coverage check — binaries × variants × horizons: WI-035 (h21) +
WI-036 (short h, all variants) + WI-038 (high h, in flight); meta labels: WI-016; ranking:
WI-009b; classifier route: WI-009c (negative); regime conditioning: WI-027 labels + WI-039 audit;
screening: WI-014. No other Layer-1 direction is known unattempted.

**Layer 2 — overlay / trading decision (attempted):**

| WI | Overlay attempted | Outcome |
|---|---|---|
| WI-011/012 | condition-first meta application; cross-market validation | closed negative; NO_TRADE default |
| WI-018 | condition-first first_touch_34 trading condition | documented negative (G2 wall); NO_TRADE |
| WI-028 | entry-window rule choice | INCONCLUSIVE; at-bottom entry frozen |
| WI-030 | learned exit chooser vs frozen cell | FAIL — frozen `t15_s10_d39_close` stands |
| WI-033 | swing-conditioned 3-class XGB vs frozen rules | REJECT both markets |
| WI-037 | P(hold) veto filter (τ on CALIB edge) | REJECT — τ grid inert at 0.4% prevalence (PROVISIONAL) |

**N/A (infra, not gated by this structure):** WI-000/001/003–008/010/013–015/019/020 (pipeline,
ingest, QA, docs), WI-021–024 (fib label/rule chain feeding L2), WI-027/027b (regime labels =
features/labels, not models), WI-031 (fold-stability gate validation).

**Reading:** every Layer-2 attempt has REJECTed/failed against the frozen rules — the frozen
fib rules remain the only deployable core; Layer-1 has one robust, cross-market,
regime-stable signal family (b_hold short-horizon) stocked in the library.
