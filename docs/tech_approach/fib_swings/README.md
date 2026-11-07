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

## Research ladder (WI-027→030, with supplements)

Admin direction in chat 2026-11-07: build a staged ML pipeline where regime awareness + confirmation + learned exit policy replace the frozen-exit-grid approach. **Step-by-step manual gates: each WI's results reviewed by admin before the next stage is drafted.** Brainstorm additions (2026-11-07): sector grouping, ensemble label probe, survival analysis, horizon-adaptive exit, sequential-bottom depth + volume ratio features.

| Stage | WI | What | Gated on | Bar |
|---|---|---|---|---|
| 1 | **WI-027** | Rule-based point-in-time regime labels (3×2: trend × vol) → extended `regime_daily` + conditional edge table per regime | None (first) | ≥1 regime where screen edge is fold-stable; fold5 isolated ✓ **DONE — PASS** |
| 1b | **WI-027b** | Unsupervised regime detection (sklearn GMM, 3–4 components) on r1/r2/r1_s5/n_tickers + trailing return/vol features → soft state probabilities as downstream ML features; compare vs WI-027 rules | WI-027 results | Any GMM state with n_folds_pos==5 AND fold5 isolation; soft probabilities continuous (no boundary artifacts) |
| 1c | **WI-027c** | Sector grouping analysis: per-sector conditional edge tables using `config/sector_map.csv`; sector × regime interaction table (does sector explain variance regime misses?) | WI-027 + WI-027b | Per-sector fold-stability; ≥1 sector×regime combo with n_folds_pos==5 beyond the market-level regime alone |
| S1 | **WI-027-ensemble** | Ensemble label probe: average all 32 exit policies' per-event returns → check CALIB fold-stability. All-bottoms ensemble is 5/5 fold-stable (+0.65%/trade ✓); screened ensemble is 4/5 (fold5 still negative). Provides a fallback label source (all-bottoms + screen as feature) if screened labels keep failing | WI-023 data | Already computed from `trade_labels_w39.parquet` — all-bottoms fold-stable 5/5; no new code needed yet |
| 2a | **WI-028** | Entry-window falsification study: ±{0,3,5,10}d offsets × confirmation variants under the real first-touch barrier sim | WI-027 series | Quantifies the confirmation tradeoff under barriers; go/no-go decision for WI-029 |
| 2b | **WI-029** | **Survival analysis** (replacing binary confirmation): Cox proportional hazards (`statsmodels PHReg`) or random survival forest on time-to-next-low per event; right-censored at 39d; survival probability at h ∈ {3,5,10,20}d becomes the feature for stage 3. Add new features: [sequential bottom depth](#feature-additions), volume-at-event ratio | WI-028 supports the premise | Survival model C-index > 0.55 on CALIB CV; selected high-survival-probability events beat at-bottom entries; fold-stable |
| 3 | **WI-030** | Conditional exit policy + horizon-adaptive vertical barrier: per-event predicted best (target, stop) grid cell from features + regime + survival prob; max_days set per event from quantile model (WI-025) expected rally duration | WI-027 series + WI-029 (or ensemble label if 2b is dead) | Learned policy's trade returns fold-stable on CALIB; EVAL net edge ≥ frozen-grid baseline |

### Feature additions (fold into WI-029)

- **Sequential bottom depth**: count of consecutive new-39d-lows before a hold — computed from `trailing_events_w39.csv` (per symbol, date-sorted). Sustained sequential breakdowns behave differently from isolated flushes.
- **Volume-at-event**: relative volume (event day volume / 20d median) from raw OHLCV — capitulation volume correlates with bottom-hold probability. Not yet in `event_features.parquet`.

### Backlog

| Item | Trigger | Cost |
|---|---|---|
| Synthetic data validation: generate GARCH + regime-switching OHLCV with known structure, run full pipeline on it — validates method before trusting EVAL scores | If WI-029/WI-030 show edge but fold-stability is borderline | Day |
| Correlation-structure regime: eigenvalue of cross-sectional correlation matrix as a "market mode" feature. Streaming product-sum avoids full 903×903 matrix | If market-level regime alone doesn't fully isolate fold5 | Medium |
| HMM upgrade (hmmlearn or torch): replace GMM with Markov-switching for temporal persistence — regimes should last. Pip-install needed | If GMM states are temporally fragmented (high-frequency switching) | Medium |
| Horizon-adaptive multi-model: fit separate models for h ∈ {10,20,39}d exits, ensemble | If WI-030 shows horizon interacts with regime | Day |

## References

- Overnight chain brief: `docs/workflow/briefs/2026-11-06-fib-overnight/`
- Overnight results: `reports/fib_swings/OVERNIGHT_REPORT.md`
- P1 regime overlay design: `docs/tech_approach/fib_swings/P1_regime_overlay.md` (implemented in WI-022)
- Test plan: `docs/tech_approach/fib_swings/TEST_PLAN.md`
- Improvement plan (passes 1–4): `reports/fib_swings/IMPROVEMENT_PLAN.md`