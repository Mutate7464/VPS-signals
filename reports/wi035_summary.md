# WI-035 — three binary first-touch models + two-threshold entry gate (D-022 §3)

- Generated (UTC): 2026-11-09T04:39:50Z
- Learners: xgboost, logistic_l2, hist_gbm on `b_profit/b_stop/b_hold`; `n_jobs=2`, float32, symbol-sequential; per-fold isotonic calibration, sigmoid fallback < 25 positives (CB-04)
- CV: 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, horizon))`; entry rule `P̂_profit ≥ τ_p AND P̂_stop ≤ τ_s` (no renormalisation), grid τ_p∈(0.4, 0.5, 0.6, 0.7), τ_s∈(0.2, 0.3, 0.4, 0.5), selected on CALIB folds only and frozen before EVAL
- Gate geometry: at-bottom k=1.5, h=21; baseline frozen fib rules (WI-028 + WI-030 `t15_s10_d39_close`, 25 bps); placebo CB-05 label permutation (3 seeds)
- Gate (for the record, confirmatory run): ADOPT iff ≥ 4/5 folds AND pooled edge > 0 AND placebo z ≥ 2.0
- Model pickles (admin override 2026-11-09): every fitted model saved under `data/models/wi035/<MKT>_<learner>_<binary>_f<fold>.pkl` regardless of verdict (kept for future testing; nothing deployed, shortlist unchanged)

| market | events | selected | folds won | pooled baseline | pooled model | pooled edge | placebo z | rule | verdict |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :---: |
| USD | 32,177 | 79 | 1/5 | 0.0121 | -0.0004 | -0.0124 | -0.89 | logistic_l2 τ_p=0.40/τ_s=0.30 | **REJECT** |
| CAD | 17,332 | 39 | 4/5 | 0.0158 | 0.1945 | 0.1787 | +4.10 | logistic_l2 τ_p=0.40/τ_s=0.30 | **ADOPT** |

## USD — VERDICT: **REJECT** (confirmatory)

- Events: 460,314 panel rows · 658 symbols · 23 features (20/111 kept, ρ>0.4 prune) · embargo 55 td · runtime 153.2s
- Rule (frozen on CALIB folds): `logistic_l2` τ_p=0.40 / τ_s=0.30 — calib-selected 87 rows, calib edge +0.0950
- Placebo: observed edge -0.0124, null mean 0.0234, sd 0.0404, z -0.89 (3/3 seeds run)
- Pooled rank-IC (P̂_profit vs frozen return): 0.0210
- Pickles: 48 saved in `/home/yycuser/projects/signals/data/models/wi035` (all learners × 3 binaries × folds, verdict-independent)

| fold | events | selected | baseline mean | model mean | edge | IC | win |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| 0 | 4,992 | 5 | 0.0144 | 0.2844 | 0.2700 | 0.1601 | yes |
| 1 | 7,166 | 0 | -0.0016 | n/a | n/a | -0.0255 | no |
| 2 | 6,917 | 39 | 0.0178 | -0.0041 | -0.0219 | -0.0151 | no |
| 3 | 6,789 | 20 | 0.0120 | -0.0441 | -0.0561 | 0.0411 | no |
| 4 | 6,313 | 15 | 0.0195 | -0.0272 | -0.0467 | 0.0011 | no |

- ⚠ **Small selected set** (79 of 32,177 canonical events): the frozen-rule return `r_frozen` is fat-tailed (|max| ≈ 7.40), so the pooled edge can be set by a handful of extreme events while the pooled rank-IC stays near zero (+0.021). Treat this verdict as record-only — no edge is claimed (admin direction 2026-11-09).
- Top TreeSHAP — `b_profit`: `state_is_bottom` 0.258, `di_spread_3` 0.109, `horizon` 0.104, `range_compression_8_55` 0.071, `k` 0.055, `range_compression_21_144` 0.049
- Top TreeSHAP — `b_stop`: `state_is_bottom` 0.324, `horizon` 0.108, `di_spread_3` 0.106, `range_compression_8_55` 0.082, `k` 0.077, `adx_144` 0.057
- Top TreeSHAP — `b_hold`: `horizon` 0.499, `k` 0.223, `atr_pct_3` 0.061, `range_compression_21_144` 0.046, `entropy_102` 0.039, `di_spread_144` 0.032

## CAD — VERDICT: **ADOPT** (confirmatory)

- Events: 252,420 panel rows · 381 symbols · 24 features (21/111 kept, ρ>0.4 prune) · embargo 55 td · runtime 98.4s
- Rule (frozen on CALIB folds): `logistic_l2` τ_p=0.40 / τ_s=0.30 — calib-selected 25 rows, calib edge +0.2837
- Placebo: observed edge 0.1787, null mean -0.0030, sd 0.0444, z +4.10 (3/3 seeds run)
- Pooled rank-IC (P̂_profit vs frozen return): 0.0423
- Pickles: 48 saved in `/home/yycuser/projects/signals/data/models/wi035` (all learners × 3 binaries × folds, verdict-independent)

| fold | events | selected | baseline mean | model mean | edge | IC | win |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| 0 | 2,816 | 23 | 0.0207 | 0.2850 | 0.2643 | -0.0106 | yes |
| 1 | 3,685 | 2 | -0.0001 | 0.1642 | 0.1643 | 0.0045 | yes |
| 2 | 3,912 | 0 | 0.0140 | n/a | n/a | -0.0087 | no |
| 3 | 3,712 | 5 | 0.0166 | 0.0546 | 0.0381 | 0.0062 | yes |
| 4 | 3,207 | 9 | 0.0309 | 0.0474 | 0.0166 | 0.0082 | yes |

- ⚠ **Small selected set** (39 of 17,332 canonical events): the frozen-rule return `r_frozen` is fat-tailed (|max| ≈ 8.00), so the pooled edge can be set by a handful of extreme events while the pooled rank-IC stays near zero (+0.042). Treat this verdict as record-only — no edge is claimed (admin direction 2026-11-09).
- Top TreeSHAP — `b_profit`: `state_is_bottom` 0.211, `horizon` 0.117, `k` 0.083, `entropy_102` 0.081, `amihud_55` 0.064, `di_spread_3` 0.059
- Top TreeSHAP — `b_stop`: `state_is_bottom` 0.263, `horizon` 0.134, `k` 0.071, `di_spread_3` 0.070, `entropy_102` 0.059, `atr_pct_3` 0.058
- Top TreeSHAP — `b_hold`: `horizon` 0.432, `k` 0.209, `amihud_55` 0.043, `entropy_102` 0.040, `di_spread_144` 0.038, `atr_pct_3` 0.037

## Notes / deviations

- Confirmatory no-edge run (admin 2026-11-09): the gate arithmetic is reported for the record; no shortlist, no deployment, no live trading.
- The two-threshold rule is a filter, not a renormalisation: rows are taken on the intersection `P̂_profit ≥ τ_p AND P̂_stop ≤ τ_s` over canonical at-bottom rows.
- Pickles exist for every grid point (admin override), including folds whose gate fold lost; they are evaluation artefacts only.

