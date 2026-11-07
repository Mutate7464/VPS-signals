# fib_swings — trailing-bottom swing screen + regime → exit policy → meta-label pipeline

> Research topic for the Phase 2 fib-swing signal. Charter for the new 3-stage research
> ladder (WI-027→030), superseding the overnight chain's frozen-exit-policy approach
> that returned `NO_POLICY_CLEARS`.

## What's built

| WI | Deliverable | Status | Key numbers |
|---|---|---|---|
| WI-021 | pass-4 accounting fix + `trailing_events_w39.csv` (186,729 events, both types, both markets) + `precision_at10.csv` + `rally_grade_priors.csv` + `walkforward_validation.csv` | DONE (chain) | EVAL bottom screen 0.2959 vs base 0.2619 (+3.4pp edge); 2026 partial 0.2436 |
| WI-023 | 32-policy exit grid (target {10,15}% × stop {5,8,10%,ATR} × max_days {20,39} × entry {close,next_open}), per-event trade sim, `trade_labels_w39.parquet` (2.43M rows) | DONE (chain) | Hit rate 0.4777 within bounds [0.403,0.712]; **0/32 eligible on fold-stability** — fold5 (COVID 2020→2022) negative for all 32 |
| WI-022 | Regime overlay R1 (vol term structure) + R2 (breadth63), `regime_daily.csv` (14,972 rows, 2006→2026, both markets) | DONE (chain) | R1R2 gated rate 0.352 (base 0.2619, keep 0.343); VERDICT PASS |
| WI-024 | Event feature table `event_features.parquet` (76,049 bottoms, 16 features, NaN<25%); meta-model (`scripts/fib_meta_model.py`) | DONE (chain) | Features shipped; meta-model blocked (VERDICT: BLOCKED_PRECONDITION — policy null) |
| WI-025 | XGBoost quantile regressors for rally/drawdown magnitude per bottom event; `quantile_results.csv` (30 rows) | DONE (chain) | Beats per-symbol baseline on all 4 CAD/USD × MFE/MAE combos; coverage 0.78–0.85; VERDICT PASS |

## Key findings from the overnight chain (2026-11-06)

1. **Fold-stability caught a real regime concentration** — the frozen 32-cell exit grid fails because fold5 (Jan 2020→Apr 2022, COVID) is negative for every policy, while fold3 (2015–2018, energy-crash recovery) carries 79% of the CALIB per-trade edge at +13.3% mean. Random-shuffle CV passes 20/20 reps — the blocked-CV bar works and must be applied to every learned artifact.
2. **The screen, not the exits, inverts in fold5** — unscreened all-bottoms trades are 5/5-fold stable (~+1%/trade every fold) for all 32 policies. The filter (oversold confluence) adds alpha in folds 1–4 and anti-alpha in fold5. A regime overlay that isolates fold5 should allow fold-stable edge in surviving regimes.
3. **R1R2 regime overlay already works** as a binary gate (gated 0.352, keep 0.343) — extending to a multi-category regime classifier is the natural next step.
4. **The quantile model (WI-025) provides a per-event magnitude prior** — predicted MFE/MAE beat per-symbol baselines; feeds confirmation and policy-learning stages.
5. **Confirmation (delayed entry after a held low) is a symptom fix, not an assumption** — the close-to-close probe (120-symbol sample) showed confirmation costs mean return (2.86→2.18%) and volume (⅔ lost) with no hit-rate gain. It may still help under the actual barrier sim (entry→stop distance geometry) — must be measured before building any classifier.

## New research ladder (WI-027→028→029→030)

Admin direction in chat 2026-11-07: build a 3-stage ML pipeline where regime awareness + confirmation + learned exit policy replace the frozen-exit-grid approach. **Step-by-step manual gates: each WI's results reviewed by admin before the next stage is drafted.**

| Stage | WI | What | Gated on | Bar |
|---|---|---|---|---|
| 1 | **WI-027** | Rule-based point-in-time regime labels (3×2: trend × vol) → extended `regime_daily` + conditional edge table per regime | None (first) | ≥1 regime where screen edge is fold-stable (5/5 CALIB folds positive); fold5 isolated to identifiable regime(s) |
| 1b | **WI-027b** | Unsupervised regime detection (sklearn GMM → HMM) on regime features (r1, r2, r1_s5, n_tickers + trailing return); soft state probabilities replace hard labels as downstream ML features | WI-027 results | Unsupervised states provide additional separation beyond rules; soft (continuous) membership avoids boundary artifacts and the circularity of rule-defined labels; state characterization must be interpretable (component means) |
| 2a | **WI-028** | Entry-window falsification study: ±{0,3,5,10}d offsets × confirmation variants under the real first-touch barrier sim | WI-027 results | Quantifies the confirmation tradeoff under barriers; go/no-go decision for WI-029 |
| 2b | **WI-029** | Confirmation classifier: per-event P(hold confirmed) from event+regime features; threshold on CALIB, EVAL scored once | WI-028 supports the premise | Selected events beat at-bottom entries on mean_ret + hit_rate, fold-stable |
| 3 | **WI-030** | Conditional exit policy: per-event predicted best grid cell (target/stop/days) from features + regime; CALIB-trained, EVAL scored once | WI-027 + WI-029 (or WI-027 only if 2b is dead) | Learned policy's trade returns fold-stable on CALIB; EVAL net edge ≥ frozen-grid baseline |

**Guards, unchanged from the overnight chain:**
- Fold-stability (5 contiguous date-block folds, all positive) applied to every learned artifact.
- EVAL (Jul 2022→now) scored exactly once per stage — never used for selection.
- Point-in-time trailing only — no future data in any label or feature.
- n_jobs=2, float32 features, symbol-sequential reads.
- Unscreened all-bottoms baseline reported alongside every screened number (the fold-stable reference).

WI-026 (calibration/intervals, parked in the overnight chain brief) stays deferred — not in this ladder.

## References

- Overnight chain brief: `docs/workflow/briefs/2026-11-06-fib-overnight/`
- Overnight results: `reports/fib_swings/OVERNIGHT_REPORT.md`
- P1 regime overlay design: `docs/tech_approach/fib_swings/P1_regime_overlay.md` (implemented in WI-022)
- Test plan: `docs/tech_approach/fib_swings/TEST_PLAN.md`
- Improvement plan (passes 1–4): `reports/fib_swings/IMPROVEMENT_PLAN.md`