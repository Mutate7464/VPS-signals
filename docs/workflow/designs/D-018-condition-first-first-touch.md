# D-018 — Condition-first directional study: first_touch @ w≈34 (USD)

Status: **accepted** (all 5 definition-gate questions answered by admin 2026-11-01:
Q1 both binnings · Q2 CAD skipped · Q3 depth ≤2 · Q4 BH-FDR 5% · Q5 memo-only)
Admin direction 2026-11-01: WI-017 gate REC A+C accepted in chat. Parent evidence:
`docs/archive/old-files/human-briefings/2026-11-01-gate-WI-017-brute-force.md` (WI-017 confirmation).

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

## Admin answers (definition gate, 2026-11-01)

1. **Bin granularity: BOTH** (quintiles + terciles) — the atlas emits both
   binnings per feature; the G2 probe reads off whichever the atlas favors.
2. **CAD: SKIP entirely** — USD-only for all of G1–G3, including post-G2
   replication. Explicit DEFERRED line below.
3. **Conjunction depth: ≤2** (admin accepted REC).
4. **Multiple-testing budget: PENDING expansion** — options explained at the
   definition gate; see below.
5. **Ship shape: memo only** at this WI's gate; shortlist CSV only as a
   follow-up WI if admin accepts the rules.

## Open questions (definition gate — admin decides)

| # | Question | Options | PM REC |
|---|---|---|---|
| 1 | Condition granularity for the atlas: quantile bins (5) or terciles (3)? | (a) quintiles (b) terciles (c) both | ANSWERED: both |
| 2 | Include CAD as a confirmation market, or USD-only? | (a) USD-only (b) add CAD replication if G2 clears | ANSWERED: skip — USD-only, no replication stage |
| 3 | Conjunction depth cap for G2 rules | (a) univariate only (b) ≤2 conditions (c) ≤3 | ANSWERED: ≤2 |
| 4 | Multiple-testing budget | (a) BH-FDR 5% across all probed conditions (b) 1% (c) Bonferroni (d) two-stage | ANSWERED: **(a) BH-FDR 5%** (admin "accept rec" 2026-11-01) |
| 5 | Ship-shape if G3 clears | (a) memo only (b) CSV | ANSWERED: memo only |

## Q4 expansion — multiple-testing budget (what's tested, why, ideal results)

**What gets tested (the hypothesis count the budget must cover):**
- G1 atlas is descriptive — no testing budget consumed (CIs reported, no pass/fail).
- G2 probe: 88 features × 8 states (5 quintile + 3 tercile bins) × 2 directions
  ≈ **1,400 univariate condition-vs-outcome hypotheses**, plus conjunction rules
  built only from the top ~50 univariate survivors → ~1,200 pairwise AND/OR
  combinations. **Total ≈ 2,600 hypotheses.**
- Each hypothesis: does the conditional first_touch_34 distribution (up/dn/
  neither shares) differ from the unconditional 38/30/33 split, measured
  out-of-fold (5 chronological folds, 20-session embargo) with a 20-date-block
  circular bootstrap CI.

**Why a budget is needed at all:** at 2,600 tests, pure noise produces ~130
"discoveries" at a naive 5% per-test threshold. The budget is what separates a
real condition set from a curve-fit one — this is exactly how thin signals
(the |IC|≈0.05 zone we are in) die honestly.

**Options:**

| Option | What it controls | Expected result on THIS study |
|---|---|---|
| (a) **BH-FDR 5%** | Expected fraction of FALSE discoveries among those called significant ≤ 5% | Tolerates a small controlled error rate — right fit when the true effect is thin; the binding filter stays the out-of-fold bootstrap CI. Ideal result: a handful (~5–15) of conditions survive, each with out-of-fold CIs excluding zero. Risk: ~1 in 20 of the survivors may be spurious — mitigated by G3's independent cost overlay which must also clear |
| (b) BH-FDR 1% | Same, ≤ 1% | Halves spurious survivors but, with |lift| small, risks a false NO-GO (killing a real-but-thin condition). Use if you prefer "never wrong" over "may find something" |
| (c) Bonferroni α=0.05/2600≈2×10⁻⁵ | P(any false positive at all) ≤ 5% | Strictest; almost certainly zero survivors on thin signal — effectively pre-declaring NO-GO. Not recommended: it converts the probe into a formality |
| (d) Two-stage: FDR 5% screen on folds 1–4, then Bonferroni confirmation on fold 5 | Screens liberally, confirms harshly on untouched data | Cleaner survivors than (a), one fewer fold of training power. Cost: slightly higher false-NO-GO risk than (a), less standard than (a) in this repo's machinery |

**PM REC unchanged: (a)** — consistent with the WI-016 probe machinery already in
the codebase, the out-of-fold + bootstrap + cost-overlay stack already stacks
three independent filters on top of it, and it gives a thin-but-real signal its
fair shot. Ideal result either way: a SMALL, explainable condition set reaching
G3 — a wall of survivors would itself be a red flag (noise or leakage).

## DEFERRED

- Trading integration, ranking changes to the shipped screener — not ordered.
- CAD market work of any kind — explicitly skipped by admin (Q2, 2026-11-01).
