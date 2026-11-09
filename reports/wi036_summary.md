# WI-036 — extended three-binary target-variant grid (D-022 §3c)

- Generated (UTC): 2026-11-09T16:23:16Z
- Grid: 8 target families x 9 horizons (5, 8, 13, 21, 34, 55, 89, 144, 233) x 3 binaries x 4 learners x 2 markets; verdict = pooled OOF AUC + rank-IC, no tau grid / no entry rule (admin 2026-11-09)
- Learners: xgboost, logistic_l2, hist_gbm, mlp_torch; rho prune 0.3; features = WI-016 grid + WI-036 expansion (raw volume/VWAP/barCount, cross-sectional ranks, sector one-hots + ranks, event quality, calendar, breadth); `n_jobs=2`, float32, symbol-sequential
- CV: 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, h))`; placebo 5-seed label permutation on the AUC; BH-FDR alpha=0.05; core cap 2.5 h
- Coverage: 570 cells scored, 1158 truncated by the core budget (USD 3117.2s, CAD 6064.8s); 60 cells carry a 5-seed permutation p-value (FDR over the scored grid)
- Pickles: every fitted fold model under `data/models/wi036/<MKT>_<learner>_<variant>_<binary>_h<h>_f<fold>.pkl` (verdict-independent)

## 1. Target ranking — cross-market consistent AUC / rank-IC

| rank | variant | best cell (learner/binary/h) | AUC USD | AUC CAD | min AUC | min IC | median min AUC | cells |
| ---: | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `exact_full_k0.8` | xgboost/b_hold/h13 | 0.7836 | 0.7207 | **0.7207** | +0.0529 | 0.5179 | 33 |
| 2 | `exact_full_k1.0` | xgboost/b_hold/h13 | 0.6732 | 0.6365 | **0.6365** | +0.0557 | 0.5213 | 36 |
| 3 | `tol2_full_k0.8` | xgboost/b_hold/h8 | 0.6226 | 0.6140 | **0.6140** | +0.0500 | 0.5429 | 24 |
| 4 | `tol2_full_k1.0` | xgboost/b_hold/h8 | 0.5923 | 0.5932 | **0.5923** | +0.0649 | 0.5371 | 24 |
| 5 | `exact_mid60_k0.8` | xgboost/b_hold/h5 | 0.5981 | 0.5894 | **0.5894** | +0.0882 | 0.5231 | 24 |
| 6 | `tol2_mid60_k0.8` | xgboost/b_hold/h5 | 0.5860 | 0.5796 | **0.5796** | +0.0810 | 0.5267 | 24 |
| 7 | `exact_mid60_k1.0` | xgboost/b_hold/h5 | 0.5761 | 0.5850 | **0.5761** | +0.1023 | 0.5235 | 24 |
| 8 | `tol2_mid60_k1.0` | xgboost/b_stop/h5 | 0.5603 | 0.5613 | **0.5603** | +0.0912 | 0.5292 | 24 |

## 2. Feature attribution — winning target

Winning family: `exact_full_k0.8` (best cell xgboost|exact_full_k0.8|b_hold|h13, min AUC 0.7207).

- Top TreeSHAP (xgboost, full-panel refit): `atr_pct_3` 0.117, `month` 0.097, `hurst_39` 0.091, `adx_144` 0.080, `cs_entropy_102` 0.072, `entropy_24` 0.054, `swing_depth_atr` 0.053, `adx_3` 0.045
- Top |linear coefficient| (logistic_l2): `entropy_9` -0.450, `adx_144` +0.372, `dow` +0.365, `kama_er_3` -0.247, `di_spread_233` -0.230, `vwap_dist` -0.213, `bars_since_opp` +0.181, `cs_donchian_break_21` -0.177

## 3. FDR survivors (BH alpha=0.05)

| market | variant | learner | binary | h | AUC | z | p |
| :--- | :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| USD | `exact_full_k0.8` | xgboost | b_hold | 5 | 0.6141 | +22.51 | 1.77e-112 |
| USD | `exact_full_k0.8` | hist_gbm | b_hold | 5 | 0.6017 | +24.21 | 9.07e-130 |
| USD | `exact_mid60_k0.8` | xgboost | b_hold | 5 | 0.5981 | +36.58 | 2.70e-293 |
| USD | `exact_mid60_k0.8` | hist_gbm | b_hold | 5 | 0.5921 | +62.45 | 0.00e+00 |
| USD | `tol2_full_k0.8` | xgboost | b_hold | 5 | 0.5867 | +16.07 | 2.02e-58 |
| USD | `tol2_mid60_k0.8` | xgboost | b_hold | 5 | 0.5860 | +18.73 | 1.38e-78 |
| USD | `exact_full_k1.0` | xgboost | b_hold | 8 | 0.5898 | +13.61 | 1.76e-42 |
| USD | `exact_full_k1.0` | hist_gbm | b_hold | 8 | 0.5891 | +19.65 | 2.87e-86 |
| USD | `exact_full_k0.8` | xgboost | b_hold | 8 | 0.6521 | +32.24 | 2.48e-228 |
| USD | `exact_full_k0.8` | logistic_l2 | b_hold | 8 | 0.6424 | +8.14 | 2.05e-16 |
| USD | `exact_full_k0.8` | hist_gbm | b_hold | 8 | 0.6410 | +15.48 | 2.51e-54 |
| USD | `tol2_full_k1.0` | xgboost | b_hold | 8 | 0.5923 | +23.98 | 2.27e-127 |
| USD | `tol2_full_k1.0` | hist_gbm | b_hold | 8 | 0.5805 | +20.95 | 9.89e-98 |
| USD | `tol2_full_k0.8` | xgboost | b_hold | 8 | 0.6226 | +17.17 | 2.27e-66 |
| USD | `tol2_full_k0.8` | logistic_l2 | b_hold | 8 | 0.6169 | +13.22 | 3.51e-40 |
| USD | `tol2_full_k0.8` | hist_gbm | b_hold | 8 | 0.6051 | +14.77 | 1.20e-49 |
| USD | `exact_full_k1.0` | xgboost | b_hold | 13 | 0.6732 | +42.93 | 0.00e+00 |
| USD | `exact_full_k1.0` | logistic_l2 | b_hold | 13 | 0.6586 | +12.00 | 1.68e-33 |
| USD | `exact_full_k1.0` | hist_gbm | b_hold | 13 | 0.6479 | +15.38 | 1.12e-53 |
| USD | `exact_full_k0.8` | xgboost | b_hold | 13 | 0.7836 | +11.94 | 3.48e-33 |
| CAD | `exact_full_k1.0` | xgboost | b_hold | 5 | 0.5831 | +19.63 | 4.21e-86 |
| CAD | `exact_full_k0.8` | xgboost | b_hold | 5 | 0.5858 | +15.63 | 2.36e-55 |
| CAD | `exact_full_k0.8` | hist_gbm | b_hold | 5 | 0.5831 | +12.67 | 4.27e-37 |
| CAD | `exact_mid60_k1.0` | xgboost | b_hold | 5 | 0.5850 | +29.80 | 1.92e-195 |
| CAD | `exact_mid60_k0.8` | xgboost | b_hold | 5 | 0.5894 | +15.45 | 4.05e-54 |
| CAD | `exact_mid60_k0.8` | hist_gbm | b_hold | 5 | 0.5840 | +9.16 | 2.54e-20 |
| CAD | `tol2_full_k0.8` | xgboost | b_hold | 5 | 0.5854 | +11.93 | 4.24e-33 |
| CAD | `exact_full_k1.0` | xgboost | b_hold | 8 | 0.6003 | +16.35 | 2.25e-60 |
| CAD | `exact_full_k1.0` | hist_gbm | b_hold | 8 | 0.5880 | +8.29 | 5.89e-17 |
| CAD | `exact_full_k0.8` | xgboost | b_hold | 8 | 0.6446 | +39.91 | 0.00e+00 |
| CAD | `exact_full_k0.8` | logistic_l2 | b_hold | 8 | 0.6101 | +23.93 | 7.28e-127 |
| CAD | `exact_full_k0.8` | hist_gbm | b_hold | 8 | 0.6348 | +18.72 | 1.76e-78 |
| CAD | `tol2_full_k1.0` | xgboost | b_hold | 8 | 0.5932 | +20.68 | 2.84e-95 |
| CAD | `tol2_full_k1.0` | hist_gbm | b_hold | 8 | 0.5853 | +12.82 | 5.95e-38 |
| CAD | `tol2_full_k0.8` | xgboost | b_hold | 8 | 0.6140 | +21.12 | 2.64e-99 |
| CAD | `tol2_full_k0.8` | logistic_l2 | b_hold | 8 | 0.5973 | +14.69 | 4.00e-49 |
| CAD | `tol2_full_k0.8` | hist_gbm | b_hold | 8 | 0.6051 | +8.12 | 2.27e-16 |
| CAD | `exact_full_k1.0` | xgboost | b_hold | 13 | 0.6365 | +12.84 | 4.71e-38 |
| CAD | `exact_full_k1.0` | logistic_l2 | b_hold | 13 | 0.5978 | +7.60 | 1.48e-14 |
| CAD | `exact_full_k1.0` | hist_gbm | b_hold | 13 | 0.6346 | +16.38 | 1.26e-60 |
| CAD | `exact_full_k0.8` | xgboost | b_hold | 13 | 0.7207 | +11.68 | 8.36e-32 |
| CAD | `exact_full_k0.8` | logistic_l2 | b_hold | 13 | 0.6550 | +8.43 | 1.73e-17 |
| CAD | `exact_full_k0.8` | hist_gbm | b_hold | 13 | 0.6864 | +10.66 | 7.59e-27 |
| CAD | `tol2_full_k1.0` | xgboost | b_hold | 13 | 0.6124 | +13.25 | 2.29e-40 |
| CAD | `tol2_full_k1.0` | hist_gbm | b_hold | 13 | 0.5954 | +11.41 | 1.97e-30 |
| CAD | `tol2_full_k0.8` | xgboost | b_hold | 13 | 0.6467 | +13.44 | 1.68e-41 |
| CAD | `tol2_full_k0.8` | logistic_l2 | b_hold | 13 | 0.6207 | +10.41 | 1.14e-25 |
| CAD | `tol2_full_k0.8` | hist_gbm | b_hold | 13 | 0.6265 | +8.09 | 3.09e-16 |
| CAD | `exact_full_k1.0` | xgboost | b_hold | 21 | 0.7142 | +15.26 | 6.77e-53 |
| CAD | `exact_full_k1.0` | logistic_l2 | b_hold | 21 | 0.6253 | +3.64 | 1.38e-04 |
| CAD | `exact_full_k1.0` | hist_gbm | b_hold | 21 | 0.6428 | +9.14 | 3.10e-20 |
| CAD | `exact_full_k0.8` | xgboost | b_hold | 21 | 0.6908 | +11.97 | 2.67e-33 |
| CAD | `exact_full_k0.8` | logistic_l2 | b_hold | 21 | 0.6775 | +5.92 | 1.63e-09 |
| CAD | `exact_full_k0.8` | hist_gbm | b_hold | 21 | 0.6425 | +7.56 | 1.97e-14 |
| CAD | `tol2_full_k1.0` | xgboost | b_hold | 21 | 0.6460 | +26.29 | 1.13e-152 |
| CAD | `tol2_full_k1.0` | hist_gbm | b_hold | 21 | 0.5835 | +7.48 | 3.79e-14 |
| CAD | `tol2_full_k0.8` | xgboost | b_hold | 21 | 0.6357 | +5.82 | 2.89e-09 |

## Notes / deviations

- Pure-signal run: the tau/entry-rule layer is retired from the verdict (admin 2026-11-09) — nothing selected, no portfolio returns, no costs.
- Target definitions: `exact` = detected swing bar; `tol2` = extreme bar within +/-2 bars (shoulder); `full` = touch window [t+1, t+h]; `mid60` = [t+ceil(.2h), t+floor(.8h)]; features are always read at the detection bar.
- `k` and `horizon` are constant inside a cell, so the shared design matrix carries them as zero-variance columns (no information; mirrors WI-035).
- Cells not reached before the core cap are reported as truncated, not dropped; placebo (FDR) is run on the cells with the largest |AUC-0.5| first.

