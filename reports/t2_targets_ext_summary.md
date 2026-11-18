# WI-048 — T2 cross-family summary (D-025 tier 2, PROVISIONAL)

- Generated (UTC): 2026-11-13T05:59:18Z
- Families: up, high_low, vol_expand; 72 cells joined from the per-family sidecars; no new training except the winner-cell attribution refit
- Learners: lightgbm, xgboost; variant pinned per market {'USD': 'exact', 'CAD': 'tol2'} (`*_full_k0.8`); rho prune 0.3
- CV: 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, h))`; placebo 5-seed label permutation on the AUC; BH-FDR alpha=0.05 over m=24 per family (design multiplicity)
- Features read at the detection bar only; float32, symbol-sequential, `n_jobs=2`; core cap 2.0 h
- Pickles (survivors only): `data/models/wi048/<MKT>_<learner>_<variant>_<family>_h<h>_f<fold>.pkl`; manifest `data/models/wi048/manifest.parquet` (WI-040 schema)

## 1. Target ranking — family x best cell (cross-market min AUC)

| rank | family | best cell | AUC USD | AUC CAD | min AUC | min IC | cells |
| ---: | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| 1 | `vol_expand` | lightgbm/h13 | 0.7068 | 0.7130 | **0.7068** | +0.3581 | 12 |
| 2 | `high_low` | xgboost/h55 | 0.7039 | 0.6089 | **0.6089** | +0.1343 | 12 |
| 3 | `up` | xgboost/h8 | 0.5038 | 0.5807 | **0.5038** | +0.0067 | 12 |

## 2. FDR survivors (BH alpha=0.05, m=24 per family)

| market | family | learner | h | AUC | z | p |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| USD | `high_low` | xgboost | 5 | 0.7241 | +67.47 | 0.00e+00 |
| USD | `high_low` | lightgbm | 5 | 0.7212 | +86.64 | 0.00e+00 |
| CAD | `vol_expand` | lightgbm | 21 | 0.7169 | +145.46 | 0.00e+00 |
| USD | `high_low` | xgboost | 8 | 0.7158 | +69.14 | 0.00e+00 |
| CAD | `vol_expand` | xgboost | 21 | 0.7144 | +76.31 | 0.00e+00 |
| CAD | `vol_expand` | lightgbm | 13 | 0.7130 | +81.12 | 0.00e+00 |
| CAD | `vol_expand` | xgboost | 13 | 0.7120 | +46.87 | 0.00e+00 |
| USD | `high_low` | lightgbm | 8 | 0.7113 | +110.03 | 0.00e+00 |
| USD | `high_low` | xgboost | 13 | 0.7110 | +160.82 | 0.00e+00 |
| USD | `high_low` | xgboost | 21 | 0.7075 | +137.35 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 8 | 0.7073 | +93.89 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 13 | 0.7068 | +111.11 | 0.00e+00 |
| USD | `high_low` | xgboost | 34 | 0.7048 | +42.27 | 0.00e+00 |
| USD | `high_low` | lightgbm | 13 | 0.7043 | +69.50 | 0.00e+00 |
| USD | `high_low` | xgboost | 55 | 0.7039 | +55.86 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 21 | 0.7022 | +121.06 | 0.00e+00 |
| USD | `vol_expand` | xgboost | 8 | 0.7013 | +127.71 | 0.00e+00 |
| USD | `high_low` | lightgbm | 21 | 0.7008 | +149.66 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 5 | 0.7000 | +96.24 | 0.00e+00 |
| USD | `high_low` | lightgbm | 34 | 0.6991 | +92.86 | 0.00e+00 |
| CAD | `vol_expand` | xgboost | 5 | 0.6987 | +77.29 | 0.00e+00 |
| CAD | `vol_expand` | lightgbm | 5 | 0.6984 | +129.32 | 0.00e+00 |
| USD | `vol_expand` | xgboost | 13 | 0.6980 | +96.54 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 34 | 0.6970 | +64.15 | 0.00e+00 |
| USD | `high_low` | lightgbm | 55 | 0.6954 | +42.64 | 0.00e+00 |
| USD | `vol_expand` | xgboost | 5 | 0.6954 | +118.26 | 0.00e+00 |
| USD | `vol_expand` | xgboost | 21 | 0.6954 | +92.86 | 0.00e+00 |
| CAD | `vol_expand` | xgboost | 8 | 0.6940 | +59.65 | 0.00e+00 |
| CAD | `vol_expand` | lightgbm | 8 | 0.6936 | +62.36 | 0.00e+00 |
| USD | `vol_expand` | xgboost | 34 | 0.6935 | +112.18 | 0.00e+00 |
| CAD | `vol_expand` | xgboost | 34 | 0.6892 | +81.94 | 0.00e+00 |
| CAD | `vol_expand` | lightgbm | 34 | 0.6890 | +105.27 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 55 | 0.6212 | +87.43 | 0.00e+00 |
| CAD | `vol_expand` | lightgbm | 55 | 0.6120 | +32.44 | 3.91e-231 |
| CAD | `vol_expand` | xgboost | 55 | 0.6095 | +77.52 | 0.00e+00 |
| CAD | `high_low` | xgboost | 55 | 0.6089 | +21.33 | 2.92e-101 |
| CAD | `up` | xgboost | 5 | 0.6057 | +41.14 | 0.00e+00 |
| CAD | `high_low` | xgboost | 34 | 0.6035 | +20.32 | 3.94e-92 |
| USD | `vol_expand` | xgboost | 55 | 0.6025 | +62.60 | 0.00e+00 |
| CAD | `high_low` | xgboost | 21 | 0.6000 | +36.71 | 2.70e-295 |
| CAD | `high_low` | xgboost | 5 | 0.5983 | +52.05 | 0.00e+00 |
| CAD | `high_low` | xgboost | 8 | 0.5963 | +42.35 | 0.00e+00 |
| CAD | `up` | lightgbm | 5 | 0.5950 | +28.21 | 2.45e-175 |
| CAD | `high_low` | xgboost | 13 | 0.5939 | +80.80 | 0.00e+00 |
| CAD | `high_low` | lightgbm | 34 | 0.5875 | +33.78 | 2.03e-250 |
| CAD | `high_low` | lightgbm | 5 | 0.5867 | +70.75 | 0.00e+00 |
| CAD | `high_low` | lightgbm | 21 | 0.5835 | +36.57 | 3.64e-293 |
| CAD | `high_low` | lightgbm | 8 | 0.5828 | +21.64 | 3.72e-104 |
| CAD | `high_low` | lightgbm | 55 | 0.5816 | +17.49 | 8.49e-69 |
| CAD | `up` | xgboost | 8 | 0.5807 | +64.20 | 0.00e+00 |
| CAD | `high_low` | lightgbm | 13 | 0.5768 | +27.59 | 6.74e-168 |
| CAD | `up` | lightgbm | 8 | 0.5663 | +43.42 | 0.00e+00 |
| CAD | `up` | xgboost | 13 | 0.5585 | +21.47 | 1.34e-102 |
| CAD | `up` | lightgbm | 13 | 0.5410 | +21.60 | 8.85e-104 |
| CAD | `up` | xgboost | 21 | 0.5325 | +10.34 | 2.40e-25 |
| CAD | `up` | lightgbm | 21 | 0.5145 | +9.54 | 7.10e-22 |
| USD | `up` | xgboost | 8 | 0.5038 | +4.97 | 3.40e-07 |
| USD | `up` | lightgbm | 8 | 0.5034 | +2.92 | 1.75e-03 |
| USD | `up` | lightgbm | 5 | 0.5029 | +2.97 | 1.51e-03 |

## 3. Feature attribution — winning cell

Winning cell `USD|lightgbm|vol_expand|h13` (min AUC 0.7068).

- Top TreeSHAP (xgboost, full-panel refit): `bars_since_opp` 0.192, `atr_pct_3` 0.152, `di_spread_3` 0.082, `cs_donchian_break_21` 0.081, `kama_er_15` 0.067, `entropy_24` 0.056, `kama_er_3` 0.052, `month` 0.047
- Top |linear coefficient| (logistic_l2): `atr_pct_3` +0.533, `kama_er_15` -0.234, `srel_di_spread_21` +0.200, `cs_hurst_9` +0.172, `swing_depth_atr` -0.134, `di_spread_233` +0.122, `adx_144` -0.117, `entropy_9` -0.077

## Notes / deviations

- Ranking uses the cross-market minimum AUC per `(family, learner, h)` cell; the library stays Layer-1 (predictive only, D-023).
- Verdict PROVISIONAL — computed labels are advisory until the admin ratifies them.

