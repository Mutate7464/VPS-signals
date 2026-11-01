# D-018 — Condition-first directional study: first_touch @ w≈34 (USD)

Status: **proposed** (definition gate — open questions at the end, admin decides)
Admin direction 2026-11-01: WI-017 gate REC A+C accepted in chat. Parent evidence:
`docs/human/briefings/2026-11-01-gate-WI-017-brute-force.md` (WI-017 confirmation).

## Context / why this WI

WI-017's brute force (593 symbols, full fib grid 3–233) found exactly one
genuinely new, actionable region: window ≈ 34 gives the only balanced 3-way
directional split (38% up-first / 30% dn-first / 33% neither, run-2 summary).
Direction everywhere else is thin (first_touch best |IC| ≈ 0.03–0.06 across all
264 features; first_touch_63 zero passes) — consistent with WI-002/009*/016
negatives and WI-011's "conditions, not levels" frame. This WI asks the
condition-first question at w≈34 that has never been asked: is there a
*condition set* (feature-state combinations) under which first-touch direction
is predictable enough to survive costs?

## Goal ladder (guaranteed-deliverable first, cheap falsification second)

1. **G1 (guaranteed): descriptive condition atlas** — per feature-state condition
   (quintiles/terciles of the 88-column pruned grid), conditional base rates of
   first_touch_34, with block-bootstrap CIs. Deliverable regardless of outcome.
2. **G2 (cheap falsification probe)**: best condition sets by held-out lift vs
   the 38/30/33 unconditional split, WI-015-style folds + embargo, same-sign
   bar. NO-GO if no condition clears |lift| with CI excluding zero out-of-fold.
3. **G3 (uncertain bet, only if G2 clears)**: cost overlay at 20+5 bps
   (WI-011 params, still assumptions) → decision rules → shortlist-shaped
   artifact for the human gate. Pre-registered expectation from the WI-017
   gate: with an unconditional |IC| ceiling ≈ 0.05, most likely outcome is a
   documented negative; the E5 factor screener stands as MVP signal either way.

## Design

- **Target**: `first_touch_34` (run-2 derived parquets already on disk,
  `reports/wi017/derived/`). Secondary read at w∈{24, 39} for robustness only.
- **Features**: WI-017 pruned grid (88 columns, `reports/wi017/run5_prune_recs.json`),
  recomputed per-symbol (features parquets on disk). Family-representative
  check for atr_pct/fib_dist/range_pos against THIS target before use (prune
  caveat in run-5 report).
- **Method**: condition extraction (univariate state rules first; small AND/OR
  conjunctions only if univariate survives multiple-testing correction —
  BH-FDR per WI-016 probe machinery), 5 chronological folds, 20-session
  embargo (horizon-scaled: max(20, w)), circular block bootstrap (20-date
  blocks), same-sign clause carried from WI-009b.
- **Costs**: WI-011 overlay params 20+5 bps, explicitly labeled assumptions.
- **Constraints**: standing bars by pointer — n_jobs=2/float32/symbol-sequential,
  point-in-time only, no order execution, human gate on every ship decision.
  USD only. Frozen artifacts untouched.

## Open questions (definition gate — admin decides)

| # | Question | Options | PM REC |
|---|---|---|---|
| 1 | Condition granularity for the atlas: quantile bins (5) or terciles (3)? | (a) quintiles (b) terciles (c) both | (c) both — atlas is cheap; the probe reads off whichever the atlas favors |
| 2 | Include CAD as a confirmation market, or USD-only? | (a) USD-only (b) add CAD replication if G2 clears | (b) — replication only on a G2 pass, keeps cost near zero unless warranted |
| 3 | Conjunction depth cap for G2 rules | (a) univariate only (b) ≤2 conditions (c) ≤3 | (b) — depth 3 on 88 features with 2.34M rows is a combinatorial pit and WI-009c precedent says depth doesn't rescue thin signal |
| 4 | Multiple-testing budget | (a) BH-FDR 5% across all probed conditions (b) 1% | (a) 5% consistent with WI-016 probe machinery, with the bootstrap CI as the binding filter |
| 5 | Ship-shape if G3 clears: shortlist CSV (WI-014 format) vs decision-rules memo only | (a) memo only (b) CSV | (a) memo at this WI's gate; CSV only as a follow-up if admin accepts the rules |

## DEFERRED

- Trading integration, ranking changes to the shipped screener — not ordered.
- Any CAD-only work beyond the conditional replication in Q2.
