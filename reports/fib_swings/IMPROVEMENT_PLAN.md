# Improvement Plan & Best Practices (from 2026-11-06 analysis, passes 1–4)

Companion to LEARNINGS.md (findings) and DATA_INDEX.md (data access).
Status: recommendations, not yet executed. Priority-ordered.

> Change log: 2026-11-06 (admin chat, "other improvements / ML that fits the data"): ordering
> superseded by `docs/tech_approach/fib_swings/TEST_PLAN.md` (rung ladder anchored to the
> 10%/trade goal). P3.3 learned ranker DEMOTED (median 1 screened event/day). New P0
> exit-policy/first-touch labels added ahead of P1. LightGBM → xgboost (already a dep).

## P1. Regime overlay on the bottom screen (blocking gate)
- **Why:** out-of-time skill is +2.0pp overall, but 2021/2026 fell BELOW base rate
  (walkforward_validation.csv) — the screen is regime-dependent.
- **How:** condition the bottom screen on a regime filter; primary candidate
  `bbw_f3/bbw_f39` (universe-level vol term structure, biserial +0.05 vs y_20d_up);
  secondary candidate: market breadth (share of tickers above 63d mean — needs one
  breadth feature pass). Validate with the same 2022-07 split and per-year table.

## P2. Relabel: 3-class rally grade instead of binary
- Use fixed w=39 MFE terciles: weak < +19.5% ≤ med < +33.9% ≤ strong
  (already in trailing_events_w39.csv `grade` column).
- Model choice: ordinal regression or quantile GBM (LightGBM `objective='quantile'`)
  on fwd MFE — predicts magnitude distribution, which is what sizing needs.
- Metric: precision@10 per day on grade ≥ med (the human gate consumes a top-10
  shortlist, not AUC).

## P3. Model architecture (in order of expected value)
1. **Discrete-time hazard model** (per-day P(turn within k days); Cox or GBM):
   models *time to peak/bottom*, handles censoring — fits swing timing better
   than plain binary classification. Add days-since-last-swing as a feature.
2. **Meta-labeling** (López de Prado): primary rule decides side (frozen screens),
   secondary model predicts P(trade pays) → filter/size the shortlist. Aligns with
   the existing WI-015 plan.
3. ~~**Learned ranker** (LambdaMART / GBM rank objective) for precision@10 —
  oversold-ranking is saturated (precision_at10.csv: 28.8% vs 29.6%).~~
  **DEMOTED 2026-11-06 (admin chat):** EVAL screen fires a median 1 name/day (≥10 on
  8/438 days) — no ranking problem exists; meta-label score orders busy days.
4. **HMM/regime-switching** only if P1's simple filter underperforms.
- Keep LightGBM/CatBoost over XGBoost for incremental speed; skip sequence models
  (LSTM/TCN) — ~2,700 bars/ticker, effect sizes ρ 0.03–0.09 don't justify it.
- **Calibrate probabilities** (isotonic/Platt, out-of-time) on anything shown to
  the human gate.

## P4. Features to add (ranked)
1. days-since-last-confirmed-swing (hazard feature) — cheap, absent today.
2. Per-ticker rolling percentile of vol-scaled meta-features (`rsi_f63/atrp_f63`
   has NO portable absolute threshold — self-normalize; bounded indicators
   (RSI, bbw ratios) may take absolute cuts).
3. Velocity/slope features: slope of rsi_f15, slope of bbw_f3.
4. Drawdown depth + duration from last confirmed top.
5. Cross-sectional sector-relative ranks (needs sector map — not in dataset).
6. Rally-grade priors per ticker (rally_grade_priors.csv) as model inputs.
- Already rejected: ADX/KAMA/OBV cross-window combos (|ρ|<0.03), sequence models,
  top-side alpha screens (no out-of-sample edge).

## P5. Frozen thresholds (do not re-fit on eval data)
| Signal | Condition | Use |
|---|---|---|
| Bottom candidate | rsi_f63 < 42 AND rsi_f15−rsi_f39 < −8 | candidate generator (validated) |
| Turn confirmation | rsi_f24−rsi_f39 crossing −3.8 / +3.3 | timing refinement |
| Vol release | bbw_f3/bbw_f39 > 0.7 (1.1 = violent) | regime/continuation flag |
| Exhaustion/avoid | rsi_f15−rsi_f39 > +10.2 with rsi_f63 > 58 | sizing/avoid only |

## P6. Validation best practices (non-negotiable for P1–P4)
- **Purged K-fold CV with embargo** (≥ label length 39d) — overlapping labels
  otherwise leak; plain time-split is insufficient.
- Thresholds frozen before evaluation (pass-4 pattern); never re-fit on eval.
- Report per-year stability (2021/2026 pattern must be visible in every result).
- Multiple-testing discipline: ~2,500 combo×target tests were run; winners survive
  Bonferroni, but cross-sectional correlation inflates significance — validate final
  2–3 features out-of-time, drop near-duplicates (keep ONE of rsi_f63/atrp_f63,
  rsi_f102/atrp_f102).
- CAD/USD split pass before any shortlist integration (never yet run).
- Cost reality check: +1.5pp/39d edge requires selective entries to clear
  equity costs — gate on confluence, never a single flag.
