> ⚠ **TRUNCATED** at `max_tokens` (finish_reason=length; completion 16000 tokens, reasoning 12761 where known). This plan is INCOMPLETE — raise `max_tokens` in the request and resubmit.

## Recommendation

Run a precision-diagnostics harness and a direction-learnability check first, about 0.8 core-h in total. Then build the L0 swing-leg geometry block and the L1 cross-sectional top-decile-mover target ahead of everything else. The volatility-regime thesis should govern which features and targets come next, and the mean-reversion swing detector stays as the event and side generator. Among L1 architectures, benchmark meta-labeling plus an equal-weight seed ensemble decided in advance. Do not build a stack.

The ordering rests on two findings in the recorded state.

- **The models predict *whether* a name moves, not *which way*.** `b_hold` survives, `b_profit` and `b_stop` do not, and `up` sits at about 0.50. Meta-labeling on the swing side with the default positive class is close to a re-run of the failed `b_profit` target.
- **The `vol_expand` window is described ambiguously in the pack**, which raises a possible leakage question. It has to be checked before anything is built on top of it.

## Goal
Produce a ranked, buildable L0/L1 extension plan with at least six net-new items. The items should raise precision at small k and top-decile calibration toward the ~10%/trade, ~200 trades/yr EV objective. L1 gating stays predictive-only.

## Current conditions
- **L0:** 249 classified columns, coverage 1.000. About 8–10 columns carry nearly all permutation signal, mostly volatility, range-regime and event-quality features.
- **L1 manifest:** 9,745 rows.
- **Three-binary family:** only `b_hold` survives, for h∈{5..89}.
- **WI-048 T2 survivors:** all PROVISIONAL.
  - `vol_expand`: 24/24
  - `high_low`: 24/24
  - `up`: 11/24
- **L2:** closed, with EVAL edge about 0 vs 25 bps.
- **Housekeeping:** the WI-048 d/e/f locks are uncleared.

## Ideal result
The 11-section plan below. It contains 9 net-new items, each with owner, core-h, family boundary, finish condition and EV-proxy rationale. It also includes the L1-options assessment and three risks.

## Plan

All WIs follow the same rules:
- ≤2.5 core-h, `n_jobs=2`, float32, symbol-sequential reads.
- Checkpointed per cell, so a run can stop after any cell.
- The spec and run footer carry `START_UTC`, projected core-h, `END_UTC` and `NEXT_ALLOWED_RUN_UTC`, with at least 30 min idle after any burst of 1 core-h or more.
- The run pauses for a human when modeled credit drops below 25%. The monitor is `credit_monitor.py --vcpus 2 --state <path>`.
- Resume command template: `uv run python -m <wi_runner> --resume --checkpoint <wi_dir>/ckpt --state <path>`. The runner name is set per WI; the pack does not name runners.

Core-h figures are planner estimates. My only anchor is the inference that WI-048 ran 72 cells over 6 sub-batches, about 12 cells per batch. Calibrate the estimates against WI-048 run footers before dispatch.

### Phase 0: pre-dispatch hygiene
- **Owner:** human operator (locks), L1 modeler (code read).
- **Cost:** about 0.1 core-h.
- **Done when:**
  - `.hermes/locks.json` `active_locks` is empty.
  - `targets_ext.py` is confirmed to compute `vol_expand` on returns in [t+1, t+h] compared with [t−h+1, t].
  - A shuffled-future placebo on `USD|lightgbm|vol_expand|h13` returns AUC ≈ 0.50.

### Phase 1: evaluation harness and direction check (items H0, D0; infrastructure, not counted)
- **Owner:** evaluation analyst.
- **Cost:** 0.5 + 0.3 core-h.
- **Done when:**
  - The §8 diagnostics are emitted for every existing survivor family from stored OOF predictions, with no refits.
  - A descriptive table shows directional hit rate (detector side vs sign of the h-return) among events in the top decile of predicted move (1 − p(`b_hold`), and `vol_expand`), compared with all events.

### Phase 2: L0 blocks, in rank order (L0-1 … L0-6)
- **Owner:** feature engineer builds the block; L1 modeler runs the family.
- **Cost:** 1.2–2.0 core-h each, one WI each.
- **Done when:** each block has a closed family, written PROVISIONAL, with a collinearity report.
- **Prerequisite:** WI-047 #1 (regime percentiles) runs first. It is the ratified regime block and L0-4 reuses its percentile machinery.

### Phase 3: L1 targets (L1-1 … L1-3), binary families first, continuous families as separate WIs
- **Owner:** L1 modeler.
- **Cost:** 1.5–2.5 core-h each.
- **Done when:** each family is closed with the §8 diagnostics attached.

### Phase 4: L1.5 meta-labeling and simple ensemble benchmark (§9)
- **Owner:** L1 modeler; admin ratifies.
- **Cost:** about 2.0 core-h per primary family, plus 0.5 for the ensemble.
- **Done when:** both primary families are closed and the ensemble-vs-single descriptive table is filed.

---

## 1. Status assessment (confirm / correct)

**Confirmed:**
- Coverage 1.000 and the causal, dimensionless construction.
- The concentration of signal in the volatility, range and event-quality axis.
- The family-scoped statements about `b_hold` and the T2 survivors.
- h89 lies outside the deployment window and should be excluded from all new grids.

**Corrections and missing distinctions:**

1. **"249 columns" is the wrong unit for signal capacity.**
   - 5 of the 249 are keys (`symbol/date/state/close/atr`). `close` and `atr` are absolute levels, so confirm they are excluded from model inputs (open question).
   - 102 `cs_*` columns are transforms of other columns, and many windowed columns are near-duplicates.
   - The effective number of independent feature axes is far below 244. Coverage 1.000 means every column is *classified*, not that every axis is *covered*.
2. **`vol_expand` definition, possible over-claim or leakage.** The pack says the realized vol is "of the h log-returns ending at t". Read literally, the label is observable at t, which would explain AUC 0.71 with `atr_pct_3` ranked top.
   - If the window really is [t+1, t+h] compared with the trailing window, the label still contains a mechanical vol mean-reversion component: low trailing vol makes expansion likely.
   - That is a legitimate predictive signal, but "expansion relative to own recent vol" does not imply a large *absolute* move. This is why the L1-2 target below ranks moves across the universe.
3. **`b_hold`-only is the finding, not a limitation, but read its sign correctly.**
   - `b_hold` is "neither barrier touched within h". Its complement, "a barrier is touched", is a *move-occurrence* event.
   - Together with `b_profit` and `b_stop` failing, this says the models predict *whether* a move happens, not *which side wins*.
   - The barriers are k∈{0.8,1.0}×ATR. At typical ATR%, the implied move is a few percent, well short of 10%. The payoff ratio implied by the construction is about 1:1.
   - So the surviving signal sits on the right axis (volatility) but at the wrong magnitude and with no side.
4. **`up` has 11/24 survivors at AUC ≈ 0.504.** These are artefacts of large N and are admissible under the no-floor licence. They should be flagged "not screener-eligible" in reports. That is a reporting tag, not a gate.
5. **`high_low` has base rate 0.75–0.87.** AUC 0.61 on such a base rate leaves little headroom for precision. Report lift (precision@k / base rate), not raw precision.
6. **Calibration is global only.** ECE 0.0009 and Brier skill +0.327 are panel-wide. Top-decile calibration has not been measured, and it is the quantity the product needs. §8 adds it.
7. **Economic wording.** "Where 10% moves live" is an economic claim and is not licensed at L1. Restate it as an L2 hypothesis: *the volatility-regime axis is the predictive axis and the L2 candidate for magnitude.*
8. **Thesis tension, resolved.** The volatility-regime thesis governs the next round of features and targets. The mean-reversion detector stays as the **event and side generator**, the primary in meta-labeling terms. Mean-reversion *features* remain silent, and §4 explains why event-anchored versions are more promising than more fixed-window oscillators.
9. **Locks.** The WI-048 d/e/f locks are uncleared. This is a Phase 0 precondition, handled by a human.

## 2. Ranked extension items

Rules shared by all items:

- **L0 family protocol (pre-registered):**
  - Host target `vol_expand` binary, learner lightgbm, 2 markets × 6 h {5,8,13,21,34,55}, so **m=12**.
  - Ba