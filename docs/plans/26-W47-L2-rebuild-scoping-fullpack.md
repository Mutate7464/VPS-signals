## Recommendation
Issue D-0XX as an **(b)-led, stepwise L2 chain**. It runs in this order:

1. Meta-label driver and full-universe run (input prep).
2. WI-041 harness upgrade: union manifest with dedup, a mandatory fold report, and multi-leg/turnover cost.
3. Cross-sectional top-k ranking screener, first on single signals and then as a regularised stack.
4. Fixed time-based exits.
5. One consolidated EVAL gate.

(c) and (d) run only if (a) or (b) survive CALIB. The plan's honest magnitude claim is narrower than the north-star: **net-positive, fold-stable, material edge at 25 bps per side**. Nothing in the library yet supports ~10% per trade. That figure only ranks designs.

## Goal
Write a design-level D-0XX brief that turns the frozen L1 library (wi040 ∪ wi048) into a manually operated screener judged on net economic EV. The brief must contain:
- the WI-049 mechanism surveys,
- a ranked WI decomposition,
- a gate design,
- a decision memo,
- the top-3 risks.

D-024 closures bind to their original inputs. A closed question reopens only by naming both the new input or structural change and the old failure mechanism it changes.

## Current conditions
- **L1 is frozen** (admin, 2026-11-14).
  - wi040 has 9,745 rows: b_hold, up, high_low, vol_expand lineage.
  - wi048 has 1,015 rows: xsec_vol_rank, mfe_mae, move_*.
  - The "superset" wording was an error. L2 consumes the union, deduplicated on market/learner/variant/family/horizon/fold.
- **Strongest cells are predictive-only verdicts.**

  | Cell | Score |
  |---|---|
  | xsec_vol_rank_bin | min AUC 0.8226 |
  | xsec_vol_rank_cont | min IC +0.6475 |
  | b_hold | AUC 0.7836, ECE 0.0009 (calibration usable) |
  | move_dir_up | min AUC 0.6407 |
  | move_occur | min AUC 0.6033 |
  | mfe_mae_cont | IC +0.1665 |
  | mfe_mae_bin | min AUC 0.5515 |
  | up (unconditional) | ≈0.5038 |

  L0 survivor: disp_entropy_39.
- **D-024 rerun** (WI-042/043): 20 ADOPT (all ≤1 bp net, not deployable), 1 INCONCLUSIVE, 49 INERT, 21 REJECT, for 91 outcomes in total.
  - The task header says "1 INERT". The pack says INCONCLUSIVE, and I use INCONCLUSIVE.
- **Decay of 87.0 bps CALIB→EVAL across the 20 ADOPT cells**, attributed as follows (bps shares are my arithmetic):

  | Mechanism | Share | Approx. bps | Cells |
  |---|---|---|---|
  | Fold-concentration | 55.0% | ≈47.9 | 17 |
  | Cost-floor | 44.8% | ≈39.0 | 3 |
  | Tau-mass | 0.2% | ≈0.2 | 0 |

- **Prior L2 failures:**
  - WI-037: thin mass, P(hold) max ~0.011 at ~0.4% prevalence.
  - WI-030: predictive-stat selection judged on edge.
  - WI-033: overlay below the frozen baseline.
  - WI-012: transfer failure.
  - Bespoke scripts, since fixed by the WI-041 harness.
- **Meta-label status:** the full-universe run has not been executed. It is now authorized as the first input-prep WI and is not an L1 refit. `meta_label_ext.py` is library-only, so a driver is needed (~0.2–0.5 core-h).
- **Harness:** WI-041 has a frozen baseline with costs, CALIB-only tuning, one-shot EVAL, a 5-seed placebo, an INERT precheck (≥200 CALIB events plus τ span), cross-WI BH-FDR, and `--infer`.
- **Constraints:**
  - 2 vCPU / 8 GB, no swap, n_jobs=2.
  - 2.5 core-h per WI.
  - Pause and hand back if credit falls below 25%.
  - float32 immediately after calculation.
  - Research WIs deliver code, synthetic tests and `--smoke` only; the PM owns full runs.
  - No order automation.
  - Verdicts are provisional until admin ratifies.

**Intake contradictions, resolved from the pack's later admin rulings (ratify in one line each):**
1. The meta-label run is **in scope now as the first WI**. The 2026-11-14 "AUTHORIZED NOW" ruling supersedes the "separate future gate" and "Parked" lines.
2. **INERT closes as-run, like REJECT.** An INERT caused by a coverage gap is reconsiderable once the gap is filled (intake answer 4). Decision 2's "closed on REJECT" is read as covering this.
3. **"Seven questions" means the seven named overlay questions** (WI-037, 033, 030, 028, 012, 018, 011). The 91 outcomes are their cell-level results.
4. **wi048 is not a superset of wi040.** The overlap is unknown, and dedup on the cell key handles either case.

## Ideal result
One D-0XX brief containing:
- the four WI-049 mechanism surveys plus a brainstorm, each with 25 bps per-side cost math, the attacked mechanism, prerequisites, go/no-go, and a falsifier;
- a ranked, card-ready WI list with objective, layer, cap, write_files, test_command, DoD and dependencies;
- a gate design with a stop rule;
- a decision memo with a REC and tags;
- the top-3 risks.

---

## Plan

### Cost conventions (apply everywhere)
- **Single-leg trade:** 2 × 25 = 50 bps round trip.
  - Breakeven needs gross > 50 bps.
  - The ~10% aspiration implies gross ≳ 1,050 bps per trade.
- **Long/short or pair:** 4 sides, 100 bps per pair cycle on per-leg notional.
  - With per-rebalance turnover fraction f, cost is ≈100·f bps per rebalance.
  - Amortization comes from **low turnover (hysteresis, longer holds)**, not from the long/short structure. The long/short structure doubles cost.
- **Resizing mid-trade** costs 25 bps × |Δsize| per adjustment.
- **Honest magnitude path.** The current library delivers ≤1 bp net. The frozen fib baseline cell in the WI-030 comparison showed +1.07% CALIB and +2.14% EVAL.
  - 10% per trade is roughly 5–10× that baseline. No measured evidence supports it.
  - The plausible route is fewer, higher-conviction, longer-horizon (h55) trades, then sizing.
  - This rebuild only claims to establish a material, fold-stable net edge.

### Framing: the four WI-049 mechanism surveys

| # | Mechanism | L1 input | Cost at 25 bps/side | Attacks | Status | Go / no-go | Falsifier |
|---|---|---|---|---|---|---|---|
| (b) **LEAD** | Cross-sectional top-k ranking screener: top-k long, optional bottom-k short, with rank hysteresis | xsec_vol_rank_cont/bin, move_occur×move_dir_up, b_hold, meta-label OOF; regularised stack over the union | Long-only 50 bps per position; L/S 100·f bps per rebalance | **Fold-concentration** (breadth across names each date spreads edge over dates and folds) and **cost-floor** (hysteresis cuts f) | **NEW.** Not among the seven closed questions. | Go to EVAL only if net CALIB edge > 0 beats the placebo and the fold-report ceiling passes | Edge concentrated in ≤2 folds, or net ≤ materiality floor after turnover cost |
| (a) second | Fixed, pre-registered time exits at L1 horizons (h13/h55) instead of event exits | move_occur, mfe_mae_cont, regression read-outs; entry from frozen fib baseline or (b) | 50 bps round trip, same as event exits; the benefit is full exit coverage, not cost | WI-037 thin-mass inert grid. Tau-mass is only 0.2% of decay, so this is a **coverage fix, not a decay fix**. | **Adjacent to closed WI-030** (learned exit chooser). Structural change: no learned chooser; horizons fixed ex ante. New input: regression read-out and post-WI-058 families. | Go if it lifts net edge over event exits on the same entries, CALIB | No net improvement versus the frozen baseline (WI-033 pattern) |
| (c) follow-on | Volatility-target sizing on the frozen fib baseline, sized at entry only | xsec_vol_rank_cont, regime metafeatures, disp_entropy_39 | No added round trips if sized at entry; resizing costs 25 bps × \|Δ\| | Fold-concentration, if folds differ by vol regime | NEW | Only if (a) or (b) survive CALIB | Risk-adjusted edge not better than unsized, or concentration unchanged |
| (d) follow-on | Hedged sector pairs (long/short within sector) | xsec ranks within sector, move_dir_up | 100 bps per pair cycle; spread must exceed 100 bps | Fold-concentration via beta/regime neutralisation | NEW. Keep within-market to avoid WI-012 transfer failure. | Only if (b) survives, and only if a sector map exists (pack silent) | Spread ≤ 100 bps, or edge in ≤2 folds |

**Caveat on the lead input.** The pack does not say whether xsec_vol_rank carries direction. If it is a volatility-rank label, it selects **where** to trade, not **which side**. Direction must then come from move_dir_up conditional on move_occur.

### Brainstorm: additional constructions
All cost math assumes 50 bps per round trip unless noted.

| Option | L1 input | Cost note | Attacks | NEW or re-proposal |
|---|---|---|---|---|
| Rank hysteresis band (enter top-k, exit only below top-2k) | Any (b) score | Directly lowers f | Cost-floor | NEW, as a component of (b) |
| Decile-spreading (weighted entries across top 1–3 deciles) | (b) score | Same per-position cost, more positions | Fold-concentration | NEW; check operator capacity |
| Meta-label precision filter inside the top-k | WI-062 OOF | Fewer trades, so fewer costs | Cost-floor (fewer, better trades) | Adjacent to WI-011 condition-first overlay. New input: meta-label layer. Structure: inside ranking, not as a pre-gate. |
| move_occur gate → move_dir_up side (two-stage product at L2) | move_* | 50 bps | Fold-concentration | NEW |
| mfe_mae-scaled profit target / stop | mfe_mae_cont (IC +0.17, weak) | 50 bps | Cost-floor (larger captured moves) | NEW; low priority given weak IC |
| Hybrid time-stop + event-stop (whichever comes first) | move_occur, mfe_mae | 50 bps | Thin-mass coverage | Adjacent to WI-030; same justification as (a) |
| Probability-decay exit (exit when re-inferred P falls to a fraction of entry P) | b_hold / meta OOF via `--infer` | 50 bps | Thin mass, via a relative not absolute threshold | **Re-proposal risk** (WI-037, WI-030). Requires meta-label OOF as the new input. Defer. |
| Hold-probability-conditioned trailing stop | b_hold | 50 bps | Cost-floor (lets winners run) | Adjacent to WI-037; same new-input requirement. Defer. |
| Regime-switched sizing | disp_entropy_39, regime metafeatures | Entry-only sizing adds no cost | Fold-concentration | NEW; a variant of (c) |
| Sector-relative long/short | Within-sector ranks | 100 bps per pair | Fold-concentration | NEW; a variant of (d) |

General trading-design knowledge is used here (hysteresis, turnover control, vol targeting). No external citation is relied on; any specific citation is a recollection to verify.

### Phase 1 — Input prep and harness

**WI-L2-01: meta-label driver and full-universe run** (no dependencies)
- **Objective:** wire primary swing sides and outcomes from the frozen fib baseline and features from `--infer`, then run `meta_oof` on both markets. Write OOF probabilities as an L2 input artifact.
- **Layer:** L1.5 input-prep. This is not an L1 refit.
- **Owner:** Research writes the driver; PM runs the full universe.
- **Cap:** 0.5 core-h, within the pack's 0.2–0.5 estimate.
- **write_files (proposed):** `src/l2_overlay/drivers/meta_label_full.py`, `tests/l2_overlay/test_meta_label_full.py`
- **test_command:** `uv run pytest tests/l2_overlay/test_meta_label_full.py && uv run python -m src.l2_overlay.drivers.meta_label_full --smoke`. Re-create the sitecustomize torch preload first if `uv sync` ran.
- **DoD:**
  - Synthetic test proves purged-CV OOF only and no EVAL rows touched.
  - Smoke passes.
  - The full PM run writes float32 OOF probabilities per market with a manifest hash.

**WI-L2-02: harness upgrade (extend WI-041)** (parallel with 01)
- **Objective:**
  - (i) Union loader for wi040 ∪ wi048 with cell-key dedup, plus an assertion that no cell enters twice.
  - (ii) **Mandatory fold-report column:** per-fold net edge plus the concentration share of the max fold.
  - (iii) Cost model for multi-leg, turnover-based and entry-sizing positions at 25 bps per side.
  - (iv) Cross-sectional INERT precheck (see gate design).
  - (v) Pre-registration file and EVAL lock.
  - (vi) CALIB-failure stop flag.
- **Layer:** L2 infrastructure.
- **Owner:** Research.
- **Cap:** 1.0 core-h.
- **write_files (proposed):** `src/l2_overlay/harness.py` (extend), `src/l2_overlay/costs.py`, `src/l2_overlay/fold_report.py`, `tests/l2_overlay/test_harness_union.py`, `test_fold_report.py`, `test_costs.py`
- **test_command:** `uv run pytest tests/l2_overlay/ && uv run python -m src.l2_overlay.harness --smoke`
- **DoD:**
  - Dedup test passes on synthetic overlapping keys.
  - Fold report is emitted on every run and fails closed if missing.
  - Cost tests reproduce 50 bps single-leg, 100 bps pair, and 100·f turnover.
  - D-024 rerun outputs reproduce unchanged on smoke (regression guard).

*Phase done when:* both WIs are merged, the PM meta-label run is complete, and admin has ratified provisionally.

### Phase 2 — Lead construction (b), stepwise

**WI-L2-03: single-signal cross-sectional top-k screener** (depends on 02)
- **Objective:** a small pre-registered set of single-signal rankers per market, long-only first and long/short second, with hysteresis. Tune only on CALIB (k, band, hold horizon).
  - Candidate signals: xsec_vol_rank_cont, the move_occur×move_dir_up product, and b_hold.
  - Constrain k so the output fits a single operator at ~200 trades per year, roughly 4 per week.
- **Owner:** Research for code and smoke; PM for the full CALIB run.
- **Cap:** 2.5 core-h.
- **write_files (proposed):** `src/l2_overlay/constructions/xsec_rank.py`, `tests/l2_overlay/test_xsec_rank.py`
- **test_command:** `uv run pytest tests/l2_overlay/test_xsec_rank.py && uv run python -m src.l2_overlay.constructions.xsec_rank --smoke`
- **DoD:**
  - Synthetic planted-signal test is recovered net of cost.
  - The placebo test shows nothing.
  - The CALIB report includes fold distribution, turnover f, and net edge.
  - Stop/continue is recorded per signal.

**WI-L2-04: regularised L2 stack ranker over the union plus meta OOF** (depends on 01, 02, 03)
- **Objective:** earn use of the full union.
  1. Pre-cluster correlated cells by OOF correlation on CALIB.
  2. Keep cluster representatives, inside the harness and logged, never silently dropped.
  3. Fit an elastic-net logistic or ridge regressor CALIB-only on cluster scores, meta-label OOF, and regime metafeatures.
  4. Feed the stack score into the 03 ranker.
- **Owner:** Research for code; PM for the run.
- **Cap:** 2.5 core-h, enforced by sampling for smoke, chunked float32 loading, and clustering before fitting.
- **write_files (proposed):** `src/l2_overlay/constructions/stack_rank.py`, `src/l2_overlay/prune.py`, `tests/l2_overlay/test_stack_rank.py`
- **test_command:** `uv run pytest tests/l2_overlay/test_stack_rank.py && uv run python -m src.l2_overlay.constructions.stack_rank --smoke`
- **DoD:**
  - Pruning log lists every input cell and its cluster.
  - The stack must beat the best single signal from 03 on CALIB net edge **and** on the fold report; otherwise it stops. This is the WI-033 guard against overlays below the baseline.
  - Peak memory is under 8 GB on smoke-scaled extrapolation.

### Phase 3 — Second construction (a)

**WI-L2-05: fixed time-based exits** (depends on 02; reuses 03/04 entries if alive, else fib baseline entries)
- **Objective:** compare pre-registered fixed horizons (h13/h55) and a time/event hybrid against event exits on identical entries, CALIB-only.
- **Owner:** Research / PM.
- **Cap:** 2.5 core-h.
- **write_files (proposed):** `src/l2_overlay/constructions/time_exit.py`, `tests/l2_overlay/test_time_exit.py`
- **test_command:** `uv run pytest tests/l2_overlay/test_time_exit.py && uv run python -m src.l2_overlay.constructions.time_exit --smoke`
- **DoD:**
  - The card carries the WI-030 re-entry justification text (structural change plus new input).
  - The CALIB fold report and stop/continue are recorded.

### Phase 4 — Conditional follow-ons (only if 03, 04 or 05 survives CALIB)
- **WI-L2-06 (c):** vol-target entry sizing. 2.5 core-h.
- **WI-L2-07 (d):** within-market sector pairs. 2.5 core-h, and requires a confirmed sector map.
- Both use the same card template. The owner is Research / PM.
- *Done when:* the admin go-ahead is recorded, or the WIs are skipped and the skip is logged.

### Phase 5 — Consolidated EVAL gate

**WI-L2-08: one-shot EVAL** (depends on all surviving constructions)
- **Owner:** PM runs it; admin ratifies.
- **Cap:** ≤2.5 core-h.
- **Steps:**
  1. Freeze the pre-registration file before EVAL: constructions, parameters, FDR family list, and materiality floor, hashed and committed.
  2. Score EVAL once.
  3. Apply BH-FDR across the family and the fold report.
- **DoD:** a provisional verdict per construction and an admin ratification in chat. No deployment without ratification.

---

## Gate design
- **Tuning:** decision parameters are tuned on CALIB edge only. The L2 stack is fit CALIB-only. EVAL is never read before WI-L2-08, and any subset look is a burn.
- **INERT precheck:**
  - Keep the existing ≥200 CALIB events plus τ span.
  - For ranking constructions, add a minimum number of candidate names per date. The value is proposed at pre-registration and needs admin sign-off; the pack gives none.
- **Fold-report mandate:**
  - Every run reports per-fold net edge and max-fold share.
  - **Proposed ceiling:** no single fold contributes more than half of CALIB net edge, and net edge is positive in a majority of folds. These are admin-set numbers; they are proposals.
  - Failing the ceiling counts as CALIB failure.
- **Economic materiality floor:** "ADOPT" also requires net edge above a pre-registered floor, which blocks a repeat of the "≤1 bp ADOPT".
  - Proposal: the floor is set by admin before WI-L2-03 runs. The pack gives no value.
- **Placebo:** 5-seed placebo, which must be beaten on CALIB.
- **FDR family:** one rebuild family covering every construction × market × signal that reaches EVAL, listed in the pre-registration. It sits inside the cross-WI BH-FDR machinery and is reported alongside, not pooled with, the D-024 family. Pooling is an admin choice.
- **Stop rules:**
  - CALIB failure alone kills a construction; no EVAL is burned on it.
  - If (b) fails in both WI-L2-03 and 04 **and** (a) fails in 05, the rebuild hands back to admin.
  - Hand back if credit falls below 25%.
  - Any WI over cap pauses for admin approval.
- **Re-entry discipline:** any card touching a closed question carries a fixed paragraph naming the new input or structural change and the D-024 failure mechanism it changes. If the paragraph is missing, the card is a defect.

## Decision memo
**REC: Option A.**

| Option | Outcome | Risk-cost | Tags |
|---|---|---|---|
| **A. (b)-led stepwise chain (this plan)** | Plays to the library's ranking strength (IC +0.65) and directly targets the two mechanisms behind 99.8% of decay | ~11–14 core-h across 8 WIs; single EVAL spend; (b) may still be fold-concentrated | Domain: L2 economic. Code and harness are a two-way door. The EVAL spend is a **one-way door**. |
| B. (a)-led (time exits first) | Fixes inert-grid coverage | Attacks tau-mass, only 0.2% of decay, so likely another "real but nil" outcome | L2. Two-way until EVAL. |
| C. Big stack over the full union first | Uses all inputs at once | Highest compute and overfit risk; violates the stepwise ruling; WI-033 below-baseline risk | L2. Burns the one-way EVAL on the weakest-justified construction. |
| D. Do nothing (L1 stays a research library) | Zero compute; EVAL stays virgin | No screener; product goal unmet; meta-label machinery idle | Product. Two-way door. |

## Risks and mitigations
1. **Fold-concentration survives inside the cross-section** (edge in 1–2 folds, the 55% mechanism).
   - Mitigation: the fold-report ceiling acts as a CALIB kill before any EVAL. This is cheap because it is a report column built once in WI-L2-02.
2. **Leakage or duplicate inputs corrupt the stack** (union double-counting, meta OOF not purged, EVAL peeking).
   - Mitigation: dedup assertion, synthetic leakage tests in 01/02, and a hashed pre-registration plus EVAL lock in the harness. All are unit tests, with no compute cost.
3. **Compute or memory overrun on the union stack** (2 vCPU / 8 GB, 2.5 core-h).
   - Mitigation: correlation-cluster pruning before fitting, chunked float32 loading, and a smoke-scaled extrapolation gate in the 04 DoD. Pause rather than raise the cap.

## Open questions
- What is the overlap between wi040 and wi048 on cell keys? It changes the dedup effect and the stack size.
- Over what horizon is ~10% per trade measured: per round trip, per holding period, or something else?
- What is the standing of the single INCONCLUSIVE outcome: closed, reconsiderable, or a coverage gap?
- What are the admin values for the materiality floor, the fold-concentration ceiling, and the per-date minimum names?
- Does xsec_vol_rank carry direction, or volatility only? This decides whether it ranks sides or only selects universe.
- Is shorting feasible for the operator in each market, and what is the borrow cost? Borrow cost is not inside 25 bps.
- Does a sector map exist? (d) depends on it.
- What are the event counts per market and fold in CALIB? They are needed to size 04 within 2.5 core-h.
- Is the rebuild FDR family pooled with the D-024 family or kept separate?
- What are the WI numbers and D-number? Placeholders are used here.

## What would change this plan
- **Switch the lead to (a):** if xsec_vol_rank is non-directional **and** move_dir_up rankings show too little cross-sectional dispersion to fill a top-k on most dates (INERT precheck fails).
- **Drop WI-L2-04:** if the 03 fold reports already fail the ceiling for every single signal. Stacking failed signals invites the WI-033 pattern.
- **Promote the meta-label filter ahead of the stack:** if the 01 OOF shows a clear precision gain at the fib entries.
- **Move (c) up:** if the fold report attributes concentration to volatility regimes (disp_entropy_39 / metafeatures).
- **Narrow (b) to long-only and drop (d):** if shorting is unavailable to the operator.