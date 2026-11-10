# D-025 — Tiered workflow: features → prediction families → trade action

- Admin direction (chat 2026-11-10): docs must reflect a three-tier pipeline; sprint considers (a) feature/TA additions for missing elements + strengthening existing, (b) prediction expansion, (c) other trade mechanisms.
- Grounded inventory: `reports/tiered_workflow_status_2026-11-10.md` (tool-verified same day).

## §1 The three tiers (doc restructure of existing gates, not a new system)

The tiers map 1:1 onto the ALREADY-RATIFIED gate layers — D-025 reorganizes the docs, it does not re-derive the protocol:

| Tier | Contents | Gate | License |
|---|---|---|---|
| T1 — Features + metafeatures | The causal panel at the detection bar; feature gap research; attribution | D-023 §2 (no model claim; attribution + alignment stats only) | Feeds T2 |
| T2 — Predictions | Target families × horizons × learners → FDR-gated pickle library | D-023 Layer 1 (OOF AUC/IC + BH-FDR + calibration) | Predictive only, NO trading claim |
| T3 — Trade action / strategy | Overlays, entry/exit rules, mechanisms vs frozen baseline + costs | D-024 Layer 2 (CALIB-only tuning, placebo, one-shot EVAL) | Deployment only via ratified ADOPT |

Rules that carry unchanged: pre-committed closures; probe-first with core-hour caps; BH-FDR family = every tested cell; conditioning axes fold into the same family; two-strike breaker; computed verdicts PROVISIONAL until admin ratifies.

## §2 Sprint scope

1. **Doc restructure (WI-046):** WORKFLOW.md gains the tier map; BOARD rows cite tier; cross-links D-023/D-024. Doc-only, one commit.
2. **T1 feature/TA research (WI-047):** category inventory of the current panel vs a checklist of feature families (momentum, mean-reversion, volatility-forecast [realized vol, Parkman/Yang-Zhang style], volume/liquidity profile, seasonality, breadth/cross-asset, event-quality); literature/web scan for the missing families; output = gap report + proposed extension list with expected alignment rationale, grounded in the WI-040 attribution (strengthen entropy/Hurst/ATR% families first). NO training, NO new data ingestion — research + proposal only.
3. **T2 prediction expansion (WI-048):** new target families beyond b_hold per admin's list — directional (up/down over h bars), extreme touch (high/low of window), volatility expansion (ATR%/realized-vol up regime) — each an explicit TARGET FAMILY in the WI-036-style variant grid, own BH-FDR family, denser market (measured label-density CSV) as dry-run. Depends on WI-047 only if new features are adopted; can run on the current panel.
4. **T3 survey (WI-049):** scoping doc only — alternative trade mechanisms (volatility-target sizing, time-based exits vs event-based, relative-value ranking on L1 probabilities, hedged/long-short constructions) with cost-model math on the FROZEN baseline. Explicitly gated on WI-045: the L2 pause policy stands until the edge-decay mechanism is named.
5. **Edge-decay probe (WI-045):** the remaining open probe — decompose where the CALIB edge dies before EVAL (tau-mass vs fold concentration vs cost floor) on the ratified WI-042 artifacts. Cheap; unblocks T3.

## §3 Anti-cherry-picking and budgets

- WI-048's target-family axes join ONE BH-FDR family per grid run; horizons ladder capped; learners limited to library learners already in the manifest (grep pyproject before proposing new deps).
- Core-hour caps: WI-045 ≤0.3, WI-046 =0, WI-047 ≤0.2, WI-048 ≤2.0 (probe-first smoke on dry-run market before full grid), WI-049 ≤0.1.
- Correctness invariants (purged/embargoed CV, CALIB-only selection, float32, symbol-sequential, n_jobs caps) are not budget knobs.
