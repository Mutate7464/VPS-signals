# Gate brief — WI-016 step 6 (CAD meta-labeled shortlist)

**Date:** 2026-10-30 · **Decision requested:** ACCEPT / HOLD / REJECT the first model-bearing shortlist artifact

## What shipped (PM-verified)

- `src/wi016/{meta_labeler,actions}.py` + 27 new tests; full suite **542 passed EXIT:0** (PM re-ran targeted 27 + read the fold tables).
- `reports/wi016_shortlist_CAD.parquet` — 148 rows @ 2026-10-28, WI-014 head columns + meta columns (p_meta, barriers, time stop, expected/net bps, size, decision, abstain_reason). 147 TRADE / 1 NO_TRADE. Frozen WI-014/WI-015 artifacts untouched.
- Primary `yangzhang_21` top-decile (E5 lost the bake-off; tc_rating excluded point-in-time); 4 addendum-cleared targets only; training on top-2 deciles w/ decile flag; embargo max(20,h) — fold gaps verified 21/56/145 td; isotonic calibration all folds; 5-seed placebo.

## The honest numbers

- **Edge is thin but real:** OOF AP lift over placebo +0.037–0.043 on the h8 targets (0.57–0.60 vs 0.53–0.56); AUC lift only 0.007–0.028; h55/h144 weaker (AUC ~0.51, AP ≈ placebo). Top-decile stratum outperforms second-decile on 3/4 targets — the primary gate is doing real work.
- **Abstention is nearly inert (wart):** 99.3% TRADE. The expected-edge formula prices barrier distance (k·ATR), which dwarfs the 20 bps cost, so the cost overlay rarely binds; filtering rests on the probability floor. Net-edge units (bps) and barrier-capture units (% of price) are not directly comparable in the current formula — flagged for the next iteration, not silently shipped.

## What this artifact is NOT

- Not a validated trading edge: no paper-tracked performance exists yet; AP lift is in-sample-CV, costs are assumptions, and slippage/intra-horizon drift are unmodelled. Human gate + NO live execution unchanged.

## Options

| Option | What | Consequence |
|---|---|---|
| A — ACCEPT | Ship the shortlist as a research artifact beside WI-014's; paper-track decisions daily | First model-bearing artifact on record; thin-edge risk visible to the human gate |
| B — HOLD | Fix the abstention/edge-unit wart first (expected-bps vs barrier-distance), re-run | One more Build cycle before anything ships |
| C — REJECT | Close WI-016 at step 5+addendum as the validated record; discard the step-6 artifact | Model path documented negative-ish (thin), no artifact |

## GATE DECISION (admin, 2026-10-30)

**HOLD + fix (Option B).** The step-6 artifact is not accepted as-is: the near-inert abstention filter (99.3% TRADE) must be reconciled first — expected edge and cost compared on consistent terms, breakeven probability derived from cost + slippage, probability floor calibrated out-of-fold. Shortlist to be re-emitted under the corrected rule with the trade share reported per cost/slippage band. USD stays descriptive. Model remains research context behind the human gate; no live execution.

## FIX DELIVERED (2026-10-31, PM-verified)

Rule v2 shipped: breakeven probability derived per event from cost+slippage vs barrier geometry; OOF-calibrated floor 0.5303 (precision 0.568 vs 0.545 base). Re-emitted shortlist: 148 rows — 133 TRADE / 15 NO_TRADE (89.9%, was 99.3%); all abstentions carry `p_below_floor`; trade share stable across cost 10–30 × slippage 0–10 bps (only 30+10 drops one row); median tradeable net edge 122 bps at 20+5. Full suite 550 passed EXIT:0 (PM ran). Honest note: with OOF precision 0.568 on a 0.545 base rate, the model's discrimination is thin — the floor cannot abstain harder without killing recall. That ceiling is the model's, not the rule's.

**Re-gate decision requested:** ACCEPT the corrected artifact (research context, paper-track daily) | further HOLD.

## RE-GATE DECISION (admin, 2026-10-31)

**ACCEPT.** The corrected step-6 artifact ships as research context alongside WI-014: `reports/wi016_shortlist_CAD.parquet` (133 TRADE / 15 NO_TRADE @ 20+5 bps, rule v2, OOF floor 0.5303). WI-016 → DONE. Carries forward: paper-track the shortlist daily behind the human gate; discrimination ceiling (OOF precision 0.568 vs 0.545, AUC 0.51–0.53) is the next iteration's target — new data/families, not more rule tuning. USD remains descriptive. No live execution anywhere.
