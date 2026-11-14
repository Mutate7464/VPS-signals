# RAW BRIEF — L2 rebuild scoping (batch-planner input)

> Input to the batch-planner pipeline (`batch_brief.py --input`). Facts below are
> gathered and verified from repo artifacts on 2026-11-14; the batch model adds
> judgment, not retrieval.

## GOAL (one sentence)

Produce an L2 (trading-overlay) rebuild scoping plan — a design-level D-0XX brief
with a WI decomposition — that converts the frozen, ratified L1 predictive library
into a manually-operated screener judged on economic expected value, treating the
D-024 overlay closures as binding to their original inputs: closed questions may
re-enter ONLY via a named structural change or a materially new input (new L1
families, meta-label layer, regression read-out, extended feature panel).

## PRODUCT OBJECTIVE (objective function — optimise THIS, not AUC)

Manual screener for a single human operator: target **~10% gain per trade NET of
costs** (25 bps per-side cost floor inside `r_frozen`; gross targets repeat the
"economically nil ADOPT" trap at the goal level) at ~200 trades/year — the
~10%/trade figure is the admin's aspiration; measured library edges are currently
≤1 bp net, so the plan must state the magnitude path honestly (the aspiration
shapes and ranks design; it is NOT a gate on any individual sprint step — each
step is judged by its own tier gate: L1 predictive-only; L2 economic). No
automated order execution; Discord-private, single-user; IBKR Gateway stays
manual on the operator's Mac.

## CURRENT CONDITIONS (verified 2026-11-14)

### Layer 1 library — FROZEN for this rebuild (admin ruling 2026-11-14)
- Manifest `data/models/wi040/manifest.parquet` — **9,745 rows** (original L1
  library core: b_hold, up, high_low, vol_expand lineage); plus
  `data/models/wi048/manifest.parquet` — **1,015 rows** (post-WI-058 new-family
  superset: xsec_vol_rank, mfe_mae, move_*). Both are frozen L2 inputs (see the
  L2 inputs ruling below).
- Strongest cells (all BH-FDR survivors, cross-market min statistics, Layer-1
  predictive-only verdicts — NO trading claim licensed):
  - `xsec_vol_rank_bin` (WI-058): 24/24 survivors, **min cross-market AUC 0.8226**
    (lightgbm/h55) — library best binary.
  - `xsec_vol_rank_cont` (WI-059b, regression read-out): 24/24, **min IC +0.6475**
    (best +0.7135 CAD/xgb/h55).
  - `b_hold` incumbent (WI-036/040): pooled OOF AUC 0.7836 (xgb/h13 USD),
    Brier skill +0.327, ECE 0.0009 — **calibration is usable**.
  - `move_dir_up` (WI-060): 24/24, min AUC 0.6407 — direction learnable conditional
    on a move (`up` unconditionally is chance, min AUC ≈ 0.5038).
  - `move_occur` (WI-060): 24/24, min AUC 0.6033. `mfe_mae_bin` (WI-059a): weak,
    min AUC 0.5515. `mfe_mae_cont` (WI-059b): min IC +0.1665.
  - L0 block survivor: `disp_entropy_39` (L0-5, WI-053…057 + R12 rerun).
- Training machinery available: 6 learners (xgboost, lightgbm, catboost,
  RandomForest, ExtraTrees, elastic-net logistic — WI-044); average-uniqueness
  `sample_weight` opt-in (WI-061); L1.5 meta-label layer with leakage-hardened
  purged CV (WI-062, machinery ratified; **full-universe meta-label run NOT yet
  run** — a separate future gate); regression read-out path
  (`cell_cv(regression=True)`, float32 labels, OOF `fit_regressor`, WI-060).
- **L2 inputs ruling (admin 2026-11-14, corrected 2026-11-14 after intake audit):**
  L2 models consume the **UNION of both frozen manifests** —
  `data/models/wi040/manifest.parquet` (9,745 rows: the original L1 library —
  b_hold, up, high_low, vol_expand lineage) AND
  `data/models/wi048/manifest.parquet` (1,015 rows: the post-WI-058 new-family
  superset — xsec_vol_rank, mfe_mae, move_* families) — plus the
  **full causal feature panel + regime metafeatures** via `--infer` — not just the
  top cells. More inputs = more correlation signal for the L2 layer, provided the
  L2 fit stays CALIB-only and regularised; redundancy across correlated cells is
  handled by regularisation/stack pruning inside the harness, never by silently
  dropping library inputs. This must be EARNED in the plan (regularisation /
  pruning design), not asserted. Fits must be sized to the 2.5 core-h per-WI cap
  on 2 vCPU / 8 GB.
- `vol_expand` label is BACKWARD-looking — quarantined (D-026 ruling); forward use
  only via `vol_expand_fwd`. The WI-058 cont top-of-date indicator artifact is
  retained for later use per admin (flagged not-continuous).

### Layer 2 — what already failed and why (D-024 §1, gate records)
1. Inert decision grids on thin probability mass (WI-037: calibrated P(hold)
   max ~0.011 at ~0.4% prevalence; τ grid had no feasible operating point).
2. Selection on predictive stats, judged on trading edge (WI-030: won 5/5 CALIB
   folds on its training criterion, lost to frozen cell on CALIB +0.61% vs +1.07%
   and EVAL +0.80% vs +2.14%).
3. Overlays vs a strong frozen baseline (WI-033: pooled edge −0.15pp vs frozen).
4. Cross-market transfer failure (WI-012: USD-tuned decisions did not carry to CAD).
5. Bespoke per-WI scripts, no cross-WI FDR (fixed by the WI-041 harness).

### D-024 rerun closure (pre-committed, executed)
- WI-042 (modern four) + WI-043 (legacy three) rerun under the
  `src/l2_overlay/harness.py` protocol: counts {'ADOPT': 20, 'INCONCLUSIVE': 1,
  'INERT': 49, 'REJECT': 21}. **All 20 ADOPTs are statistically real but
  economically nil** (edges ≤1 bp vs the 25 bps cost floor) — NO deployment.
  REJECT/INERT questions are **permanently closed** under D-024 §2 pre-committed
  closure; a re-proposal without a stated structural change is a defect.
- Evidence: `reports/l2/rerun_modern.md`, `reports/l2/rerun_legacy.md`.

### Failure-mechanism ranking (WI-045 edge-decay probe, frozen artifacts)
Decay of 87.0 bps CALIB→EVAL over 20 ratified ADOPT cells:
**fold-concentration 55.0% (17 cells) > cost-floor 44.8% (3 cells) > tau-mass 0.2%
(0 cells)**. Any new L2 construction must name which of these it attacks.

### Harness assets that survive
`src/l2_overlay/harness.py` (WI-041): frozen baseline + costs, decision params
tuned ONLY on CALIB edge, one-shot EVAL, 5-seed placebo, INERT precheck (≥200
CALIB events + τ span), cross-WI BH-FDR family. `--infer` recomputes the full
causal feature panel at the decision bar + regime metafeatures (WI-027/039).

### Folded-in scope (admin 2026-11-14)
WI-049's T3 trade-mechanism survey (card `docs/kanban/draft/WI-049-trade-mechanism-survey.md`)
is absorbed as this plan's framing section. Its four mechanisms, each needing cost
math at 25 bps + named attacked mechanism + go/no-go:
(a) time-based exits vs event-based (bypasses thin-mass tau problem);
(b) relative-value / cross-sectional ranking on L1 probabilities (long top-decile
vs short bottom-decile — cost-amortizing);
(c) volatility-target sizing on the frozen fib baseline;
(d) hedged/long-short constructions on sector pairs.

### Parked (explicitly out of scope for this rebuild)
- Larger-variant L1 family (lower ρ-prune threshold, parameter-max; re-admission
  population = 21 not-kept L0 block cols) — parked post-rebuild; L1 is FROZEN.
- **Meta-label full-universe run — AUTHORIZED NOW (admin 2026-11-14):** run as the
  rebuild's first input-prep WI, BEFORE the L2 chain. Note: `meta_label_ext.py` is
  library-only — a small PM-owned driver WI is required first (wire primary swing
  sides + outcomes from the frozen fib baseline, features from the `--infer`
  panel, run `meta_oof` on both markets; ~0.2–0.5 core-h).

- **Meta-label freeze clarification (admin 2026-11-14):** the full-universe
  meta-label fit is **NOT an L1 refit** — it consumes frozen library OOF/manifest
  predictions and fits only the small secondary meta-model (ratified WI-062
  machinery). It is input-prep, same standing as `--infer`; the L1 freeze is
  intact.

### Old-artifact relevance (admin question, 2026-11-14)
- Older runs/models remain relevant as **evidence, not as verdicts**: gate records,
  failure mechanisms, and frozen artifacts carry forward; verdicts bind only to the
  inputs they were computed on. A closed question may be re-opened when materially
  NEW inputs exist (L1 families WI-058…062 post-date every D-024 rerun; the
  regression read-out and meta-label layer did not exist then) — the re-open must
  name the new input AND the old failure mechanism it changes.
- **WI-041 harness upgrade is IN SCOPE** (admin 2026-11-14): fold-distribution
  reporting (per-fold edge + concentration share) as a mandatory column, full-L1
  manifest input support, and any other upgrade the plan justifies — extend, don't
  rebuild.

## INTAKE ANSWERS (round-2 editor questions, resolved by admin 2026-11-14)

1. **~10%/trade target:** design aspiration ONLY — explicitly NOT a gate on any
   gate or step (see Product Objective). Measured edges are ≤1 bp net; the plan
   must state the magnitude path honestly.
2. **25 bps cost floor:** **per side** (inside `r_frozen`), consistent with all
   D-024 edge comparisons; round-trip ≈ 50 bps. Edge comparisons use the same
   convention as the frozen baseline.
3. **Manifests:** BOTH are inputs, union — wi040 (9,745 rows, original library)
   and wi048 (1,015 rows, new-family superset). Neither is discarded; the earlier
   "1,015-row superset of wi040" phrasing was an error, corrected above.
4. **D-024 closures:** binding **to the inputs they were computed on**. REJECT
   closes a question as-run; it re-enters ONLY via a named structural change or a
   materially new input (new L1 families, meta-label layer, regression read-out,
   extended feature panel). INERT likewise (an INERT caused by a coverage gap —
   e.g. missing manifest cells — is reconsiderable once the gap is filled).
5. **Meta-label output standing:** the L1.5 meta-label is a **D-026 fixed product**
   (not-stacking ruling intact at L1.5), AND its OOF probabilities are a
   **permitted L2 stack input** (stacking in L2 is authorized — Decision 8).
   Both statements hold simultaneously; no contradiction.
6. **Rebuild stop condition:** CALIB failure ALONE fires the stop for a
   construction (no EVAL burn on a dead CALIB gate); the consolidated EVAL gate
   fires only at the end for constructions that survived CALIB. The whole rebuild
   hands back to admin when every lead construction has failed CALIB.
7. **Manifest dedup:** the wi040 ∪ wi048 union is **deduplicated on the cell key**
   (market/learner/variant/family/horizon/fold) inside the harness — no cell
   enters an L2 fit twice.
8. **EV convention:** **25 bps per side** everywhere, the D-024 convention
   (round-trip ≈ 50 bps as a derived note only).
9. **~10%/trade role:** qualitative aspiration that RANKS designs — not an
   optimisation objective, not a gate.

## IDEAL RESULT

A design brief (D-0XX) containing:
1. **Framing (WI-049 absorption):** the four mechanism surveys with cost math at
   25 bps, attacked failure mechanism, data prerequisites, go/no-go + falsification
   condition each.
2. **A ranked, scoped WI decomposition** (draft-ready for kanban cards): per WI —
   objective, layer (L2), core-hour cap (default 2.5), write_files, test_command,
   DoD, dependency order. First WI = the meta-label full-universe run (input prep,
   admin-authorized to run BEFORE the L2 chain).
3. **Brainstorm (admin direction 2026-11-14):** beyond the four WI-049 mechanisms,
   enumerate ADDITIONAL trade-construction options for profit-taking and
   loss-prevention implied by L1 predictions + the feature/metafeature panel —
   e.g. probability-decay exits, hold-probability-conditioned trailing stops,
   time-stops vs event-stops hybrids, regime-switched sizing, sector-relative
   long/short pairing, decile-spreading for cost amortization. For each: the L1
   input it consumes, cost math at 25 bps, attacked failure mechanism, and whether
   it is NEW or a re-proposal of a closed question (re-proposals need the
   new-input justification). The batch model should reason from its trained
   knowledge of trading-strategy design; label any concrete external citation a
   recollection to verify.
4. **Gate design:** how each WI is judged (CALIB-only tuning, one-shot EVAL
   discipline, FDR family definition, INERT precheck thresholds, fold-report
   mandate) and what would make the whole rebuild stop.
5. **A decision memo**: REC first, options with outcome + risk-cost, "do nothing"
   counted, tagged (domain / one-way vs two-way door).

## CONSTRAINTS

- L1 library FROZEN — the rebuild consumes it via `--infer`/manifest; no L1 refits
  inside L2 WIs.
- Permanently closed overlay questions (D-024 §2, as-run): WI-037 b_hold veto,
  WI-033 3-class overlay, WI-030 learned exit chooser, WI-028 entry-window
  chooser, WI-012 cross-market transfer (as ported), WI-018 first-touch 34
  overlay, WI-011 condition-first meta overlay — re-propose ONLY with a named
  structural change OR a materially new input (admin 2026-11-14: new L1 families
  and the meta-label/regression layer qualify as candidate new inputs; see
  Old-artifact relevance above).
- Compute: 2 vCPU / 8 GB, no swap; `n_jobs=2` everywhere; per-WI cap 2.5 core-h
  (raise only on explicit admin approval); checkpointed + pausable; credit-balance
  pause rule (<25% → hand back). float32 immediately after calculation. No
  all-ticker uncompressed DataFrames.
- EVAL split discipline: one-shot; a subset score on EVAL is a partial burn.
  Research WIs deliver code + synthetic tests + `--smoke` only; PM owns full runs.
- Verdicts PROVISIONAL until admin ratifies in chat; no auto-adoption.
- No secrets in git; no automated order execution; human gate on every sprint gate.
- Environment quirk: no system libgomp; lightgbm imports need the sitecustomize
  torch preload (re-create after any `uv sync`).

## DECISIONS ALREADY MADE (do NOT relitigate)

1. Two-layer gate (D-023): L1 predictive-only, L2 economic; layers never
   cross-justify. L1 has no effect-size floor.
2. D-024 closure: the seven rerun overlay questions are permanently closed on
   REJECT; 20 ADOPTs are non-deployable (economically nil).
3. One harness (`src/l2_overlay/`), never bespoke per-WI scripts.
4. Product north-star (~10%/trade, ~200 trades/yr) shapes and ranks design; it is
   not a gate on any step.
5. L1 frozen for the rebuild; larger-variant family parked post-rebuild.
6. Not-stacking ruling (D-026): fixed product of separately-fitted models is NOT
   stacking.
7. Manual screener product; no order automation in MVP.
8. **Stacking is permitted in L2** (admin 2026-11-14) — stacked meta-learners over
   L1 probability vectors fit CALIB-only, inside the harness FDR family. (The
   D-026 not-stacking ruling is untouched: it governs the L1.5 fixed-product
   construction, not L2 stacks.)
9. **Closed items are re-evaluable on new data** (admin 2026-11-14): a D-024
   closure binds to the inputs it was computed on; re-evaluation requires naming
   the materially new input (post-WI-058 L1 families, meta-label layer,
   regression read-out, extended feature panel) and the old failure mechanism it
   changes. Evidence-only reuse of old runs needs no justification.
10. **WI-041 harness upgrade is in scope** (admin 2026-11-14) — fold-report
   mandate, full-L1 manifest input, plus plan-justified extensions.

## OPEN QUESTIONS (SCQA — ratify or overturn in one line)

1. **Primary construction bet (RESOLVED by admin 2026-11-14: yes, proceed stepwise).** S: The L1 library's strength is ranking +
   calibration (IC +0.65, AUC 0.82) but every threshold-based overlay died of thin
   mass; prevalence at the frozen fib entries is ~0.4%. C: Thresholding calibrated
   probabilities converts a ranking asset into a decision-grid liability.
   Q: Should the rebuild lead with mechanism (b) cross-sectional top/bottom-decile
   ranking (cost-amortizing, plays to ranking strength) rather than any
   probability-threshold overlay? **A/DECIDED: yes — (b) leads the WI chain
   stepwise, (a) time-based exits second; (c)/(d) are follow-ons only if
   (a)/(b) show life.**
2. **Fold-concentration attack (RESOLVED by admin 2026-11-14: yes).** S: 55% of measured decay is fold-concentration
   (edge lives in 1–2 folds). C: Any single-split CALIB/EVAL verdict inherits it.
   Q: Should the rebuild mandate fold-distribution reporting (per-fold edge +
   concentration share) as a mandatory L2 report column before EVAL burn?
   **A/DECIDED: yes — harness-level mandate, prevents repeating WI-042's illusion.**
3. **Meta-label sequencing (RESOLVED by admin 2026-11-14).** S: WI-062 machinery is
   ratified but unrun on the full universe; a precision filter is most valuable
   inside a ranking construction. C: `meta_label_ext.py` is library-only — a
   driver WI is needed before any run. Q: When does the full-universe meta-label
   run? **A/DECIDED: now, as the rebuild's FIRST input-prep WI (driver WI first,
   ~0.2–0.5 core-h), before the L2 chain — the run feeds the L2 stack as an
   additional probability input.**
4. **EVAL virginity budget (RESOLVED by admin 2026-11-14: yes).** S: EVAL remains
   unburned for the new families.
   C: The rebuild may want more than one EVAL look across its WIs.
   Q: One pre-registered EVAL spend for the whole rebuild (single consolidated
   gate), or per-WI? **A/DECIDED: single consolidated EVAL gate at the end of the
   WI chain; per-WI EVAL only via explicit admin waiver.**

## ALREADY PLANNED — do NOT re-propose

- All seven D-024 rerun overlay questions (closed; structural-change rule above).
- L1 family grids for xsec_vol_rank, mfe_mae, move_occur/move_dir_up, L0 blocks
  (done, ratified).
- The WI-041 harness itself (exists; extend, don't rebuild).
- Average-uniqueness weighting, meta-label machinery, regression read-out (built).

## OUTPUT FORMAT (heading skeleton for the plan)

1. REC (BLUF, ≤5 lines)
2. Framing: four mechanism surveys (cost math, attacked mechanism, go/no-go)
3. Ranked WI decomposition (per-WI: objective, layer, cap, write_files,
   test_command, DoD, deps)
4. Gate design (FDR family, INERT precheck, fold-report mandate, EVAL budget)
5. Decision memo (options + risk-cost + do-nothing; domain/door tags)
6. Top-3 risks + cheapest mitigation each
7. Open questions (things the pack is silent on — never guessed)
