# Fib-swing Phase 2 test plan — what to test, in what order, and the bar for each

> Status: PROPOSED (Hermes PM, 2026-11-06). Not approved. Supersedes the ordering of
> `reports/fib_swings/IMPROVEMENT_PLAN.md` §P1–P4 (amended in place there).
> Goal anchor: PHASE2_HANDOVER_RUNBOOK P-5 (admin 2026-11-06): **~10%/trade target, few
> trades, low risk, realized per-trade P&L**. Daily shortlist, human gate, no auto-orders.

## Data facts that drive the ordering (probe 2026-11-06, trailing_events_w39.csv, resolved rows)

| Fact | Value | Implication |
|---|---|---|
| P(39d MFE ≥ 10%) — all trailing bottoms, EVAL | 53.8% | +10% is a *common* outcome, not a rare event: the label isn't sparse |
| same, bottom screen, EVAL | 60.1% (n=1,007) | screen adds ~+6pp on the user's actual target |
| Certain win (MFE≥10, MAE never ≤ −8) / certain loss (MAE ≤ −8, MFE<10), screen EVAL | ≥40.3% / ≥28.8%; ~31% path-ambiguous | **exit/stop design dominates per-trade P&L**; daily MFE/MAE can't tell order → need first-touch labels |
| Screened events per signal day, EVAL | mean 2.3, median 1, ≥10 on only 8/438 days | precision@10 ranking is moot; volume already matches "few trades" (~230/yr) |
| CAD vs USD, EVAL fwd-39d median ret, screened vs all | CAD 3.51 vs 3.33 (+0.2pp); USD 5.71 vs 3.23 (+2.5pp) | the return edge is USD-driven; markets must be scored separately |
| Clustering | max 35 screened events on one date | resample by date/month, not by event |

## Screened against negative knowledge (`docs/architecture/DECISIONS_AND_NEGATIVE_KNOWLEDGE.md`)
- NK#1 bar-level binary classifiers are blind → targets here are **event-conditioned** and use
  **realized trade return (R)** or quantiles. Binary outcomes are diagnostic only.
- NK#2 no feature-pool scaling → meta-model features capped at ~15, pre-listed.
- NK#3 sign inversion → monotone constraints + same-sign bar vs the frozen screen.
- NK#5 significance has no gate power → effect-size floor in bps + fold sign stability + permutation null.
- NK#7 leakage → purged CV, 39d embargo, calibration-only priors/cuts.

## Ladder (each rung gates the next; deliverable first, ML last)

> 2026-11-06 overnight-chain spec (`docs/workflow/briefs/2026-11-06-fib-overnight/`) supersedes rows below where they differ: execution order 021→023→022→024→025; rung 3 uses Ridge (continuous R target, NK#1) instead of L2 logistic and equal-volume selection instead of top-k-per-day; cost = 25 bps round trip; `vol21` + `mom_12_1` replace the per-market E5 factor.

| Rung | WI | Test | Method (repo deps only: numpy/pandas/sklearn/statsmodels/xgboost) | Pre-registered bar | Est. compute |
|---|---|---|---|---|---|
| 0 | WI-021 | Fix pass-4 accounting | see P1 design §Prerequisite | tests green, reproduces corrected +3.4pp | 1–3 min |
| 1 | WI-023 | **First-touch trade labels + exit-policy grid** | per event: entry at close (also next open), target {+10, +15}%, stop {−5, −8, −10, −1.5×ATR}, time {20, 39}d; gap-through fills at open; same-bar both-touch = loss; costs 20+5 bps | best policy on CALIB: expectancy ≥ 2× round-trip cost, all 5 folds > 0; then scored once on EVAL per market | 1–3 min |
| 2 | WI-022 | P1 regime overlay | as designed, **re-scored on rung-1 R** as well as grade | as designed + EVAL R-expectancy ≥ ungated | 2–4 min |
| 3 | WI-024 | **Meta-label filter/sizer** | primary = all trailing bottoms (75k; screen as a feature). Target = realized R of the rung-1 policy. Models: (a) frozen screen only, (b) L2 logistic, (c) XGBoost depth ≤3, monotone constraints, n_jobs=2. Same features for b/c | (c) beats (b) beats (a) on EVAL expectancy of top-k-per-day by ≥ cost floor; same sign as screen; permutation null (20 reps, labels shuffled within date) beats < 5% | 5–10 min |
| 4 | WI-025 | Quantile magnitude model | XGBoost `reg:quantileerror` (or sklearn HGB quantile) q10/q50/q90 of MFE and MAE; baseline = per-ticker CALIB priors | pinball loss beats priors on EVAL in both markets; coverage of [q10,q90] within 75–85% | +3 min |
| 5 | WI-026 | Calibration + intervals for the shortlist | isotonic on CALIB-OOF; split-conformal interval on MFE (hand-rolled, ~20 lines) | EVAL reliability: ECE ≤ 0.05; interval coverage ±5pp of nominal | <1 min |
| 6 | (gate) | Paper-track integration | shortlist columns: P(+10% before stop), expected R, MFE interval, regime state | admin gate; realized per-trade P&L ≥ 1 month (P-5) | — |

Feature list for rungs 3–4 (fixed; no additions without admin OK): rsi_f63, spread15_39, bbw_ratio,
rsi_f24−rsi_f39, depth of drawdown from 63d high, drawdown duration, days since last
confirmed trailing bottom, slope of rsi_f15 (5d), R1, R2, per-ticker CALIB prior p_medplus,
market dummy, E5 primary factor (`mom_12_1` USD / `yangzhang_21` CAD), atrp_f63 (vol scale, needed to set stops).

## Methods considered and deferred / rejected (with reason)

| Method | Verdict | Reason |
|---|---|---|
| Learned ranker (LambdaMART / rank:ndcg) | **Demoted** | median 1 candidate/day — nothing to rank; meta-label score covers ordering on busy days |
| Discrete-time hazard (time-to-target) | Deferred to after rung 3 | adds capital-turnover info, not selection; only if rung 1 shows time-stop matters |
| Markov-switching regime (statsmodels `MarkovRegression`, 2-state on equal-weight index) | Challenger only if rung 2 FAILS | cheap, no new dep, but more fit-risk than tercile gates |
| LightGBM / CatBoost | Not added | xgboost already in deps, covers quantile + monotone; a new dep buys nothing here |
| LSTM/TCN/transformer, contrastive torch | Rejected | ~2.7k bars/ticker, ρ 0.03–0.09; WI-009b negative |
| More indicator families / combos | Rejected | NK#2; ADX/KAMA/OBV already |ρ|<0.03 |
| Bar-level binary up/down classifiers | Rejected | NK#1 |

## Known biases to carry into every result
- **Survivorship:** universe = current watchlists; delisted names absent → rally sizes and
  bottom-buying edge are biased up. Prefer EVAL-period claims; state the caveat on the shortlist.
- Daily bars: intraday stop/target order unknown on same-bar touches → conservative (loss) rule.
- Costs are assumptions until P-5 paper-track realizes fills.

## Totals
Compute ≤ 25 min end-to-end on 2 vCPU/8 GB (all symbol-sequential, single process or n_jobs=2).
Wall time dominated by WI dispatch + review: ~4 WIs.
