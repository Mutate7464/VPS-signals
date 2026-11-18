## Recommendation
Issue D-0XX as a screener-first L2 brief with nine WIs. Three cheap infrastructure WIs run first: a closure registry, a manifest reconciliation check and a WI-041 harness extension. The meta-label pipeline follows as the first input-prep WI, delivered as code and `--smoke` only. Its full-universe run is a PM-owned run behind its own go/no-go. Mechanism surveys at 25 bps per side then feed one consolidated EVAL gate and a manual ranked screener.

Each gate criterion is built from a prior failure or a measured decay driver. Fold concentration explains 55.0% of decay and the cost floor 44.8%, so gate robustness and cost margin carry the design. Tau tuning (0.2%) gets no budget.

## Goal
Convert the frozen L1 library (wi040: 9,745 rows; wi048: 1,015 rows) into a manually operated screener for one operator. The brief must contain:
- mechanism surveys costed at 25 bps per side,
- a ranked WI decomposition with dependency order and caps,
- a single gate design,
- a decision memo with a REC,
- the top-3 risks.

D-024 closures bind to their original inputs. They can be reopened only through a named structural change or a materially new input.

## Current conditions
- **L1 library:** frozen (admin 2026-11-14). No L1 refits are allowed inside L2.
- **L1 verdicts:** the strongest cells are predictive-only, with no trading claim.
- **D-024 rerun:** 20 ADOPT (economically nil, ≤1 bp net), 1 + 49 INERT, 21 REJECT, for 91 outcomes in total.
- **Measured decay:** 87.0 bps from CALIB to EVAL across the 20 ADOPT cells.
- **Decay attribution:** fold concentration 55.0%, cost floor 44.8%, tau mass 0.2%.
- **Prior L2 failures to design against:**
  - inert grids on thin mass (WI-037),
  - selection on predictive stats (WI-030),
  - overlay below the frozen baseline (WI-033),
  - cross-market transfer failure (WI-012),
  - bespoke scripts (fixed by WI-041).
- **Stacking:** permitted in L2. D-026 governs the L1.5 fixed product only.
- **Compute:** 2 vCPU, 8 GB, n_jobs=2, 2.5 core-h per WI.
- **Run ownership:** research delivers code, synthetic tests and `--smoke`; PM owns full runs.
- **Execution:** no automated orders; IBKR Gateway stays manual.
- **Verdicts:** provisional until admin ratifies in chat.
- **Meta-label full-universe run:** not yet executed.
- **Product target:** about 10% per trade and about 200 trades per year. This ranks designs; it is not a gate.

## Ideal result
D-0XX is ratified by admin and contains:
1. A closure registry covering all 91 D-024 outcomes, each bound to its input hash, with a reopen protocol.
2. Mechanism surveys, each with expected net bps after a 50 bps round trip.
3. A ranked, dependency-ordered WI list, each WI capped at ≤2.5 core-h.
4. A pre-registered consolidated EVAL gate.
5. A decision memo with a single REC.
6. The top-3 risks.

PM can then execute the full runs without needing to interpret anything further.

## Plan

### Phase 0: Default rulings for the waived ambiguities (one chat message)
The brief adopts these defaults explicitly, so an admin reversal is cheap.

| Ambiguity | Default adopted |
|---|---|
| Meta-label run: first WI or separate gate? | **Both.** The WI is authorized now for code and smoke. The full-universe run is a separate PM gate. This fits the rule that research does not do full runs. |
| Is INERT permanently closed? | REJECT and INERT are both closed **as-run**, bound to their inputs. Filling a coverage gap counts as a "materially new input" only if it changes the input hash and is named in the registry. |
| Seven questions vs 91 outcomes | The registry is keyed at outcome level (91 rows), with a `question_id` column mapping each row to the seven overlay questions. Closure applies per row. |
| Do wi040 and wi048 share keys? | Not assumed either way. WI-B measures the overlap. "Superset" wording is dropped, per intake answer 3. |
| Horizon of the 10% per trade figure | Unknown. Ranking uses net bps per trade × trades per year, and the horizon is flagged as open. |

- **Owner:** Research drafts; Admin ratifies.
- **Cost:** 0.5 h effort, 0 core-h.
- **Done when:** admin acknowledges the five defaults in chat, or overrides them.

### Phase 1: Infrastructure WIs (sequential; each is a prerequisite for everything later)

**WI-A: Closure registry and reopen protocol**
- **Contents:**
  - 91 rows with cell key, outcome, `question_id`, input manifest and input hash.
  - A reopen requires a filed record of type `structural_change: <name>` or `new_input: <hash diff>`.
  - The harness refuses to evaluate closed cells without that record.
- **Owner:** Research.
- **Cost:** about 0.2 core-h; about 1 day.
- **Done when:** synthetic tests pass three cases:
  - a closed cell is blocked,
  - a valid reopen record unblocks it,
  - an ADOPT-nil cell is flagged as "baseline, not edge".

**WI-B: Manifest reconciliation (wi040 / wi048)**
- **Contents:**
  - Reports key overlap, disjointness and conflicting values.
  - Writes a provenance column.
  - Fails loudly on any conflict.
- **Owner:** Research; PM runs the full check.
- **Cost:** about 0.3 core-h.
- **Done when:** smoke passes and the PM run reports the overlap count.

**WI-C: WI-041 harness extension (the core)**
- **Contents:**
  - Applies the 25 bps per side cost inside r_frozen. The roughly 50 bps round trip is reported only as a derived note.
  - Computes the fold-concentration metric (largest single fold's share of net PnL).
  - Enforces a minimum-support floor per cell (fixes WI-037).
  - Selects on net-of-cost CALIB economics, never on predictive stats (fixes WI-030).
  - Compares every candidate to the r_frozen baseline (fixes WI-033).
  - Supports per-market evaluation only, with no transfer claims (fixes WI-012).
  - Provides stacking primitives.
- **Owner:** Research.
- **Cost:** about 1.0 core-h (smoke + tests); 3–4 days.
- **Done when:**
  - synthetic tests reproduce a known 25 bps per side net figure,
  - a single-fold-dominated synthetic series is flagged,
  - a below-baseline overlay is rejected.

### Phase 2: Input preparation

**WI-D: Meta-label pipeline**
- **Scope:** code, synthetic tests and `--smoke` on a subset, using the WI-C harness.
- **Owner:** Research for code; PM for the full-universe run, which is a separate go/no-go.
- **Cost:** ≤2.5 core-h for smoke. The full-run cost is estimated from smoke scaling and submitted to admin if it exceeds the cap.
- **Done when:**
  - smoke completes inside the cap,
  - PM has a scaled cost estimate,
  - admin decides go/no-go on the full run.

### Phase 3: Mechanism surveys (parallel after WI-C; each ≤2.5 core-h smoke)
Survey families are ranked by how much of the measured decay they target. The pack does not name specific mechanisms, so these families are proposals and must be confirmed in the brief.

| Rank | WI | Target | Content | Ranking metric |
|---|---|---|---|---|
| 1 | **WI-E: Fold-robust selection** | 55.0% of decay | Select cells and stacks whose CALIB net is spread across folds, not concentrated in one. | Net bps at 25 bps per side, fold-concentration score, trades per year |
| 2 | **WI-F: Turnover and holding-period reduction** | 44.8% of decay | Fewer, larger-move trades, so the roughly 50 bps round trip is a smaller share of each trade. | Net bps at 25 bps per side, fold-concentration score, trades per year |
| 3 | **WI-G: Stacking of L1 cells** | Uses the 2026-11-14 permission | Combinations scored net of cost against the r_frozen baseline. ADOPT-nil cells may serve as components but not as stand-alone edges. | Net bps at 25 bps per side, fold-concentration score, trades per year |
| 4 | **WI-H: Meta-label filter** | Depends on WI-D | Uses meta-label output to gate the WI-E/F/G candidates. | Net bps at 25 bps per side, fold-concentration score, trades per year |

- **Tau tuning:** explicitly excluded, since it accounts for 0.2% of decay.
- **Owner:** Research for code and smoke; PM for full CALIB runs.
- **Cost:** about 4 × ≤2.5 core-h for smoke.
- **Done when:** each survey reports, on CALIB only:
  - net bps per trade,
  - fold concentration,
  - support,
  - delta versus baseline.

### Phase 4: Consolidated EVAL gate and screener

**WI-I: Gate specification, runner and manual screener output**
- **Gate** (pre-registered before any EVAL touch, one run for all finalists, no per-WI EVAL unless admin waives):
  - (a) net EVAL bps per trade > 0 after 25 bps per side, with a margin stated in the brief;
  - (b) largest-fold share of net PnL ≤ a cap stated in the brief;
  - (c) support ≥ the floor;
  - (d) beats r_frozen;
  - (e) CALIB-to-EVAL decay reported against the 87.0 bps reference.
- **Ranking:** gate passers are ranked by the aspiration proxy (net per trade × trades per year).
- **Screener output:** a ranked candidate list for manual review, with no order path.
- **Owner:** Research for code; PM runs EVAL; Admin ratifies verdicts in chat.
- **Cost:** about 1.0 core-h for smoke. The EVAL run cost is set by PM.
- **Done when:** EVAL has run once, and admin has ratified or declined each verdict.

**Decision memo (inside D-0XX)**
- **REC:** proceed with WI-A → B → C → D (smoke) → E/F/G in parallel → H → I.
- The memo states that no current cell carries a trading claim, and that a "no candidate passes" EVAL outcome is acceptable and ends L2.
- **Owner:** Research.
- **Cost:** 0.5 day.
- **Done when:** admin ratifies.

**Budget:** total research smoke is about 14 core-h across nine WIs, every one under its 2.5 core-h cap. PM full runs are budgeted separately.

## Risks and mitigations

1. **The 87 bps decay repeats, and survey "wins" are CALIB artifacts.**
   - Mitigation: fold concentration is a hard criterion in CALIB selection (WI-C/E), not only at EVAL.
   - Cost: one metric, already inside WI-C.

2. **Closure creep: a loose "new input" reopens D-024 cells, especially INERT.**
   - Mitigation: WI-A requires an input-hash diff or a named structural change, and the harness blocks closed cells without one.
   - Cost: about 1 day.

3. **Compute overrun from stacking combinatorics or the meta-label full run on 10,760 rows (or fewer if keys overlap).**
   - Mitigation:
     - pre-declare grid sizes in each WI,
     - extrapolate cost from smoke,
     - go to admin before any run above 2.5 core-h.
   - Cost: none beyond the smoke run already planned.

## Open questions
- Will admin confirm the five Phase 0 defaults? This matters most for the meta-label run's gate status and for whether INERT can be reopened.
- What is the horizon of the 10% per trade figure? It changes how designs are ranked.
- What are the exact gate thresholds (net margin, fold-concentration cap, support floor)? The pack is silent; the brief must set them and admin must ratify.
- How do the 91 outcomes map to the seven overlay questions?
- Do wi040 and wi048 share keys? WI-B will answer this.
- Which specific mechanisms belong in each survey family? The pack names none beyond stacking and meta-labelling.

## What would change this plan
- **Admin defers the meta-label run entirely:** drop WI-D and WI-H, and add the freed budget to WI-E/F.
- **WI-B shows heavy key conflicts between manifests:** pause Phase 3 until provenance is resolved.
- **WI-F smoke shows that no achievable turnover clears roughly 50 bps round trip with margin:** recommend closing L2 at the memo stage rather than running EVAL.
- **Admin grants per-WI EVAL waivers:** WI-E could be gated alone first. I would still prefer the consolidated gate, to avoid repeated EVAL touches.