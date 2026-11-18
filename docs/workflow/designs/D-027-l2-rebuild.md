# D-027 — L2 rebuild: (b)-led stepwise screener chain

Status: EXECUTED + CLOSED 2026-11-16 (admin ratified the terminal EVAL verdict in chat; outcome in §13) · Source: batch-planner output `docs/plans/26-W47-L2-rebuild-scoping-fullpack.md` + intake brief `docs/workflow/briefs/2026-11-14-L2-rebuild-scoping-raw.md` · Date: 2026-11-14

## 1. Goal

Convert the frozen L1 library (wi040 9,745 rows ∪ wi048 1,015 rows) into a manually operated screener judged on net economic EV. Product aspiration (~10%/trade, ~200 trades/yr) **ranks designs only; it is not a gate** (AGENTS.md north-star rule). Honest magnitude claim: *net-positive, fold-stable, material edge at 25 bps/side*. Current library delivers ≤1 bp net; fib baseline reference cell: +1.07% CALIB / +2.14% EVAL (WI-030 comparison).

## 2. Cost conventions (binding for every L2 card)

- Single-leg: 2×25 = 50 bps round trip; breakeven gross > 50 bps; 10% aspiration ⇒ gross ≳ 1,050 bps.
- Pair (L/S): 4 sides = 100 bps per pair cycle; with turnover fraction f ⇒ ≈100·f bps per rebalance.
- Mid-trade resize: 25 bps × |Δsize|.
- Amortization via low turnover (hysteresis, longer holds), not via L/S structure.

## 3. Decay attribution (design driver)

87.0 bps CALIB→EVAL across the 20 D-024 ADOPT cells: fold-concentration 55% (~48 bps, 17 cells), cost-floor 44.8% (~39 bps, 3 cells), tau-mass 0.2% (~0.2 bps, 0 cells). The chain therefore attacks fold-concentration and cost-floor; tau gets no budget.

## 4. Phase 0 — default rulings (admin ack pending; cheap to reverse)

| Ambiguity | Default adopted |
|---|---|
| Meta-label run | WI authorized now for **code + smoke**; full-universe run is a separate PM go/no-go gate |
| INERT closure | REJECT and INERT closed **as-run**, bound to input hash; coverage-gap INERT reconsiderable only via named new input in the registry |
| "Seven questions" | The seven named overlay questions (WI-037, 033, 030, 028, 012, 018, 011); 91 outcomes = their cell-level results, registry keyed at outcome level with `question_id` |
| wi040/wi048 overlap | Not assumed; WI-B measures it; dedup on cell key (market/learner/variant/family/horizon/fold) handles either case |
| 10%-per-trade horizon | Unknown; ranking uses net bps × trades/yr; horizon flagged open |

Intake contradiction rulings to ratify: (1) meta-label in scope now as first WI ("AUTHORIZED NOW" supersedes "Parked"); (2) INERT closes as-run; (3) seven-questions mapping above; (4) wi048 is NOT a superset of wi040.

## 5. Mechanism survey summary (full table in source plan)

| # | Construction | Attacks | Status | Go condition | Falsifier |
|---|---|---|---|---|---|
| (b) LEAD | Cross-sectional top-k rank screener + hysteresis (long-only first, L/S second) | Fold-concentration + cost-floor | NEW (not among the 7 closed) | Net CALIB edge > placebo AND fold ceiling passes | Edge in ≤2 folds, or net ≤ materiality floor |
| (a) 2nd | Fixed time exits (h13/h55) + time/event hybrid on identical entries | WI-037 thin-mass coverage (tau=0.2% ⇒ coverage fix, not decay fix) | Adjacent to closed WI-030 — **re-entry paragraph required** | Lifts net edge vs event exits, CALIB | WI-033 pattern (below frozen baseline) |
| (c) follow-on | Vol-target entry-only sizing | Fold-concentration if vol-regime-driven | NEW | Only if (a)/(b) survive CALIB | No risk-adjusted improvement |
| (d) follow-on | Within-market sector pairs | Fold-concentration via neutralisation | NEW; needs sector map; within-market only (WI-012) | Only if (b) survives | Spread ≤ 100 bps |

Lead-input caveat: if xsec_vol_rank is non-directional it selects *where*, not *side*; side comes from move_dir_up conditional on move_occur. **Switch lead to (a)** if xsec is non-directional AND move_dir_up dispersion cannot fill top-k on most dates (INERT precheck fails). **Drop WI-L2-04** if every single signal fails the fold ceiling in 03 (stacking failed signals = WI-033 pattern).

## 6. WI chain (numbered WI-064…071; batch names WI-L2-01…08)

| WI | Content | Depends | Layer | Cap (core-h) |
|---|---|---|---|---|
| WI-064 | Meta-label driver + synthetic tests (`--smoke` only; full run = PM gate) | — | L1.5 input-prep | 0.5 |
| WI-065 | Harness upgrade: union loader + dedup assertion, mandatory fold report, multi-leg/turnover cost model, xsec INERT precheck, pre-registration + EVAL lock, CALIB-failure stop flag | — (parallel with 064) | infra | 1.0 |
| WI-066 | Single-signal xsec top-k screener (CALIB-only tuning of k/band/horizon; long-only then L/S) | 065 | L2 | 2.5 |
| WI-067 | Regularised stack ranker (OOF-correlation clustering → cluster reps → elastic-net/ridge CALIB-only → 066 ranker) | 064,065,066 | L2 | 2.5 |
| WI-068 | Fixed time exits + hybrid vs event exits on identical entries (carries WI-030 re-entry justification) | 065 (066/067 entries if alive, else fib baseline) | L2 | 2.5 |
| WI-069 | (c) vol-target entry sizing — conditional on a CALIB survivor | survivor | L2 | 2.5 |
| WI-070 | (d) sector pairs — conditional, requires confirmed sector map | 066 survivor | L2 | 2.5 |
| WI-071 | One-shot EVAL: hashed pre-registration → single EVAL score → BH-FDR across rebuild family → provisional verdict + admin ratification | all surviving | L2 | 2.5 |

Aggregate ≈ 11–14 core-h, no single card over cap. Phase gating: Phase 1 (064+065) → Phase 2 (066→067) → Phase 3 (068) → Phase 4 (069/070 conditional) → Phase 5 (071). Research WIs deliver code + synthetic tests + `--smoke` only; PM owns full runs.

## 7. Gate design (binding)

- **Tuning:** decision parameters tuned on CALIB edge only; stack fit CALIB-only; EVAL unread until WI-071 — any subset look is a burn.
- **INERT precheck:** keep ≥200 CALIB events + τ span; add min candidate names per date for ranking constructions (value set at pre-registration, admin sign-off).
- **Fold-report mandate (proposed, admin-set):** max-fold share ≤ 50% of CALIB net edge AND net edge positive in a majority of folds; ceiling failure = CALIB failure.
- **Materiality floor:** ADOPT requires net edge above a pre-registered floor (blocks repeat of "≤1 bp ADOPT"); value set by admin before WI-066 runs.
- **Placebo:** 5-seed, must be beaten on CALIB.
- **FDR family:** one rebuild family over all constructions × markets × signals reaching EVAL, listed in pre-registration; reported alongside, not pooled with, the D-024 family (pooling is an admin choice).
- **Stop rules:** CALIB failure alone kills a construction (no EVAL burn); (b) fails in both 066+067 AND (a) fails in 068 ⇒ hand back to admin; credit < 25% ⇒ pause and hand back; any WI over cap ⇒ pause for admin approval.
- **Re-entry discipline:** any card touching a closed question carries a fixed paragraph naming the new input/structural change and the D-024 mechanism changed; missing paragraph = card defect.

## 8. Input wiring (declared per D-023 discipline)

- Model probabilities: wi040 manifest (`data/models/wi040/manifest.parquet`) ∪ wi048/consolidated manifest (1,015 rows superset); loader = WI-065 union loader; no silent drops.
- Meta OOF: WI-064 driver output, purged-CV OOF only, float32, per market, manifest hash.
- Feature panel / regime metafeatures + disp_entropy_39: recomputed via the existing causal panel builder at bar t (cached), never from EVAL rows in CALIB.
- Out of decision space: all quarantined `vol_expand` (backward) artifacts; only `vol_expand_fwd` lineage permitted.
- Conditioning axes (regime labels), if used in 067, fold into the SAME BH-FDR family as unconditional cells.

## 9. Correctness invariants (not budget knobs)

n_jobs=2; float32 immediately; symbol-sequential reads; purged/embargoed CV; CALIB-only selection; no-renormalization. Budget knobs (grids, caps, sampling) may loosen only with admin direction.

## 10. Top-3 risks

1. Fold-concentration survives inside the cross-section — mitigated by the fold-report ceiling as a CALIB kill (cheap: one report column in WI-065).
2. Leakage/duplicate inputs corrupt the stack — dedup assertion, synthetic leakage tests (064/065), hashed pre-registration + EVAL lock; all unit-test cost.
3. Compute/memory overrun on the union stack — correlation-cluster pruning before fitting, chunked float32 loading, smoke-scaled extrapolation gate in WI-067 DoD; pause rather than raise cap.

## 11. Open questions — RULINGS (admin "proceed with recommendations", 2026-11-14)

1. **Materiality floor: ADOPT requires net edge ≥ 10 bps** after costs (10× the library's ≤1 bp best; blocks a repeat of the D-024 nil-ADOPT). Applied at CALIB stop/continue and at EVAL.
2. **Fold ceiling CONFIRMED as proposed:** max single fold ≤ 50% of CALIB net edge AND net edge positive in a majority of folds; failure = CALIB failure.
3. **Min names per date: 20** for the xsec INERT precheck (conservative vs the full-universe cross-section; revisit only if the precheck trips on real data and the universe is genuinely thinner).
4. xsec_vol_rank directionality: checked in WI-066 recon; lead-switch rule in §5 covers the failure case.
5. **Shorting: default LONG-ONLY for the WI-066 first pass** (plan order already long-only first); L/S leg only after admin confirms borrow feasibility/cost.
6. **Sector map: assumed ABSENT** until confirmed — WI-070 stays conditional and is skipped+logged if no map lands.
7. **Single INCONCLUSIVE D-024 outcome: closed as-run** (same rule as REJECT/INERT); reopenable only via the registry protocol.
8. **FDR pooling: rebuild family kept SEPARATE from the D-024 family** (reported alongside).

## 12. What would change this plan

Lead switch to (a), drop WI-067, promote meta-label filter ahead of the stack (if 064 OOF shows clear precision gain at fib entries), move (c) up (if fold report attributes concentration to vol regimes), narrow to long-only and drop (d) if shorting unavailable. Second REJECT on a re-proposed thread closes it permanently per the closure rule.

## 13. OUTCOME (2026-11-16, sprint closed; verdicts in BOARD.md + PM_LOG.md cycle 42)

- **(b) xsec top-k screener — KILLED on CALIB** (WI-066 full run, cycle 41): both pre-registered falsifiers tripped (USD net −62.8 bps, 0/2 folds; CAD fold 0 +248.8 / fold 1 −150.9). WI-072 retry on the amended universe (wider grids, L/S, rebuilt b_hold OOF) also closed as code+smoke only; the CALIB full run stayed green-lighted for WI-066/068 only — the retry's full read was never gated. No EVAL burn.
- **Stack ranker (WI-067) — dropped per the §5 pre-commitment** ("stacking failed signals = WI-033 pattern").
- **(a) fixed time exits — fixed_h55 unsized: ADOPTED (Layer 2, admin in chat 2026-11-16).** The only construction that survived CALIB (+231.8 USD / +473.0 CAD net vs event; placebo passed 5-seed; h13 arms negative; hybrid_h55 ≡ event exit) and the one-shot EVAL: net +452.1 USD (z +30.6) / +445.7 CAD (z +28.6), both pre-registered date-block folds positive (USD +422.6/+481.6; CAD +359.0/+532.5), BH q ≈ 0. Computed ceiling FAIL (max-share 0.533/0.597 vs ≤0.50 on 2 folds) was overridden at ratification as a 2-fold discretization artifact — ceiling content (no single-fold dependence) demonstrably satisfied; extends the §11 fold-ceiling inapplicability ruling one step. EVAL split SPENT; prereg `reports/l2_eval/l2_prereg_template.json` (frozen aeaa195a → amended pre-burn cf39228e, fold leg = 2 date-blocks at median EVAL date, admin choice (a)). Verdict artifacts `reports/l2_eval/`.
- **(c) vol-target entry-only sizing — REJECT on CALIB, RATIFIED (admin in chat 2026-11-16)** (WI-069 full run): sizing REDUCES net edge both markets (USD −111.1 / CAD −146.7 bps delta; risk-adjusted flat); §5 falsifier "no risk-adjusted improvement" tripped. Mechanism: sizing is edge-neutral on the atr axis but shreds 96–160 bps per bucket on disp_entropy_39, where h55 returns are structurally larger — vol is orthogonal to where this edge lives. PROVISIONAL tag stripped at ratification (recorded 2026-11-16).
- **(d) within-market sector pairs — descoped unbuilt** (sector map landed via WI-073 with 59 blanks residual named; the construction never reached code). Any future (d) EVAL requires a NEW pre-registration AND a new split.
- **What enters the workflow:** fixed_h55 unsized as the adopted L2 overlay exit rule, both markets — research shortlist with human gate only; no live trading, no automated orders (product boundaries).
- **Gate ledger (§7 vs outcome):** materiality floor passed everywhere it applied; 5-seed placebo passed on CALIB (placebo report `reports/l2_time_exit/placebo_{USD,CAD}.md`) and the EVAL read used a pre-registered analytic z instead (declared in the prereg amendment); fold ceiling — binding as written, tripped on discretization at EVAL, overridden by admin; FDR family = 2 members (fixed_h55 × USD/CAD), reported separately from D-024 as ruled; stop rules — no EVAL burn occurred before the one-shot.
