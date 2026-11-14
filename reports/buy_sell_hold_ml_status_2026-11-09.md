# Buy/Sell/Hold ML — Status Summary & Plan (2026-11-09)

> Scope: ML models for buy/sell/hold decisions on ticker data using peak/bottom detection,
> volatility, momentum, and meta parameters. Consolidates current model inventory, gate
> verdicts, and what a new ML thread must satisfy.

## 1. Current model inventory

| Artifact | Location | Status |
|---|---|---|
| XGBoost classifiers (4 targets × USD/CAD, calibrated) | `models/{usd,cad}/y_{15d_high,15d_low,20d_up,20d_down}.pkl` | Saved Oct 21 (CAD) / Oct 24 (USD); **Gate 4 FAIL all 8 combos** |
| XGBoost QA / governance report | `reports/sprint4_model_qa.md` | P@K lift, BSS, PR-AUC lift, IC all below bar; placebos clean → not overfit, just no edge |
| Trainer + provenance | `src/xgb_trainer.py`, `data/train_meta_{USD,CAD}.json`, `data/oof_*.parquet`, `data/predictions_*_latest.parquet`, `logs/xgb_trainer_*.log` | 5-fold purged walk-forward, 20-day embargo, isotonic/sigmoid calibration |
| Contrastive ranker | `models/contrastive_ranker_*.pt` | **Closed NEGATIVE** (WI-009/009b/009c, 2026-10-25): no usable model |
| Triple-barrier meta shortlist (CAD) | `reports/wi016_shortlist_CAD.parquet` etc. | **ACCEPT** (WI-016, 2026-10-31): 133 TRADE / 15 NO_TRADE, paper-tracked behind human gate |
| Fib swing regime labels / conditional exits | `reports/fib_swings/` | Regime labels PASS (WI-027); learned exit FAIL (WI-030 — frozen rule `t15_s10_d39_close` stands); at-bottom entry recommended (WI-028) |

## 2. Key learnings that constrain any new buy/sell/hold ML

1. **Plain 15/20-day directional targets carry no edge** with the current feature set
   (sprint4 Gate 4 FAIL). A new model must not re-run the same panel→XGBoost recipe
   expecting a different result.
2. **The fib-swing thread found the only live structure**: at-bottom entries in
   up_high regimes (+22.75pp USD, WI-027) with frozen exit rules. A buy/sell/hold
   model should be *conditioned on swing state* (at-bottom/at-top), not trained on
   all dates uniformly.
3. **Gating regime updated 2026-11-08 (cycle 27)**: ADOPT_LOOSE_4OF5 — learned
   artifacts must beat baseline in ≥4/5 folds (was 5/5). This is the acceptance bar
   for any new model (WI-031, synthetic-validated).
4. **Hostinger constraints**: `n_jobs=2`, no all-ticker uncompressed DataFrames,
   float32, checkpointed heavy jobs (AGENTS.md).

## 3. Proposed framing: buy/sell/hold conditioned on meta parameters

- **Label**: 3-class {buy, hold, sell} on swing-anchored windows (from peak/at-bottom
  state) rather than fixed 15/20d horizons — aligns with WI-028 at-bottom finding.
- **Features**: peak/bottom proximity (fib ladder levels), realized volatility,
  momentum (ts-momentum set already built in WI-011/012), plus meta parameters
  (regime label from WI-027, liquidity/label-density covariates from WI-016).
- **Model**: start with the existing purged walk-forward harness (`src/xgb_trainer.py`
  components) extended to 3-class; compare against the frozen fib rules as baseline,
  not against raw direction.
- **Gate**: WI-016-style ADOPT_LOOSE_4OF5 fold-stability + placebo CB-05; human gate
  on shortlist before any paper-trade promotion.

## 4. Plan status — CONFIRMED

- **Board (2026-11-08): ACTIVE = none. EXECUTING = 0, TODO = none, BLOCKED = none.
  "Next: none queued — admin direction required for next research thread."**
- Last completed: WI-031 (fold-stability gate adopted) and WI-030 (fib ladder closed,
  FAIL). WI-021–025 overnight chain is DONE with PM review pending.
- This summary is **not** a queued work item. Per WORKFLOW.md, the next step is a
  design (`docs/workflow/designs/`) for the buy/sell/hold ML thread, then a WI spec
  (≤400 tokens) staged in `docs/kanban/ready/` with admin (human) approval — Hermes
  does not edit source; OpenCode surgical-builder executes locked WIs.
- Human gate still applies: daily shortlist only, no auto-execution of orders.

*Generated from BOARD.md (2026-11-08), sprint4 QA report, WI-016/027/028/030/031 verdicts.*
