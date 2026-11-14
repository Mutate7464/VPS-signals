# WI-048 — T2 cross-family summary (D-025 tier 2, PROVISIONAL)

- Generated (UTC): 2026-11-14T02:30:33Z
- Families: up, high_low, vol_expand, vol_expand_fwd; 120 cells joined from the per-family sidecars; no new training except the winner-cell attribution refit
- Learners: lightgbm, xgboost; variant pinned per market {'USD': 'exact', 'CAD': 'tol2'} (`*_full_k0.8`); rho prune 0.3
- CV: 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, h))`; placebo 5-seed label permutation on the AUC; BH-FDR alpha=0.05 over m=24 per family (design multiplicity)
- Features read at the detection bar only; float32, symbol-sequential, `n_jobs=2`; core cap 2.0 h
- Pickles (survivors only): `data/models/wi048/<MKT>_<learner>_<variant>_<family>_h<h>_f<fold>.pkl`; manifest `data/models/wi048/manifest.parquet` (WI-040 schema)

## 1. Target ranking — family x best cell (cross-market min AUC)

| rank | family | best cell | AUC USD | AUC CAD | min AUC | min IC | cells |
| ---: | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| 1 | `xsec_vol_rank_bin` | lightgbm/h55 | 0.8226 | 0.8461 | **0.8226** | +0.5250 | 12 |
| 2 | `vol_expand` | lightgbm/h13 | 0.7068 | 0.7130 | **0.7068** | +0.3581 | 12 |
| 3 | `high_low` | xgboost/h55 | 0.7039 | 0.6089 | **0.6089** | +0.1343 | 12 |
| 4 | `up` | xgboost/h8 | 0.5038 | 0.5807 | **0.5038** | +0.0067 | 12 |

## 2. FDR survivors (BH alpha=0.05, m=24 per family)

| market | family | learner | h | AUC | IC | z | p |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| CAD | `xsec_vol_rank_bin` | lightgbm | 55 | 0.8461 | +0.5657 | +114.79 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | lightgbm | 34 | 0.8448 | +0.5654 | +106.08 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | xgboost | 55 | 0.8424 | +0.5596 | +131.37 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | xgboost | 34 | 0.8404 | +0.5582 | +145.61 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | lightgbm | 21 | 0.8390 | +0.5570 | +72.03 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | xgboost | 21 | 0.8351 | +0.5506 | +88.86 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | lightgbm | 13 | 0.8290 | +0.5413 | +134.25 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | xgboost | 13 | 0.8257 | +0.5359 | +99.68 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | lightgbm | 55 | 0.8226 | +0.5250 | +226.05 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | lightgbm | 34 | 0.8216 | +0.5250 | +189.27 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | xgboost | 55 | 0.8181 | +0.5176 | +186.81 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | xgboost | 34 | 0.8162 | +0.5162 | +338.41 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | lightgbm | 8 | 0.8142 | +0.5175 | +182.80 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | xgboost | 8 | 0.8118 | +0.5135 | +118.66 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | lightgbm | 21 | 0.8108 | +0.5083 | +124.90 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | xgboost | 21 | 0.8056 | +0.4999 | +102.72 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | lightgbm | 13 | 0.8009 | +0.4928 | +142.53 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | xgboost | 13 | 0.7968 | +0.4861 | +136.75 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | lightgbm | 5 | 0.7887 | +0.4757 | +125.67 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | xgboost | 5 | 0.7879 | +0.4743 | +76.91 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | lightgbm | 8 | 0.7803 | +0.4596 | +126.63 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | xgboost | 8 | 0.7784 | +0.4564 | +123.42 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | lightgbm | 5 | 0.7608 | +0.4279 | +332.69 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | xgboost | 5 | 0.7595 | +0.4257 | +222.51 | 0.00e+00 |
| USD | `high_low` | xgboost | 5 | 0.7241 | +0.3331 | +67.47 | 0.00e+00 |
| USD | `high_low` | lightgbm | 5 | 0.7212 | +0.3287 | +86.64 | 0.00e+00 |
| CAD | `vol_expand` | lightgbm | 21 | 0.7169 | +0.3750 | +145.46 | 0.00e+00 |
| USD | `high_low` | xgboost | 8 | 0.7158 | +0.2964 | +69.14 | 0.00e+00 |
| CAD | `vol_expand` | xgboost | 21 | 0.7144 | +0.3707 | +76.31 | 0.00e+00 |
| CAD | `vol_expand` | lightgbm | 13 | 0.7130 | +0.3689 | +81.12 | 0.00e+00 |
| CAD | `vol_expand` | xgboost | 13 | 0.7120 | +0.3672 | +46.87 | 0.00e+00 |
| USD | `high_low` | lightgbm | 8 | 0.7113 | +0.2903 | +110.03 | 0.00e+00 |
| USD | `high_low` | xgboost | 13 | 0.7110 | +0.2655 | +160.82 | 0.00e+00 |
| USD | `high_low` | xgboost | 21 | 0.7075 | +0.2373 | +137.35 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 8 | 0.7073 | +0.3584 | +93.89 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 13 | 0.7068 | +0.3581 | +111.11 | 0.00e+00 |
| USD | `high_low` | xgboost | 34 | 0.7048 | +0.2121 | +42.27 | 0.00e+00 |
| USD | `high_low` | lightgbm | 13 | 0.7043 | +0.2570 | +69.50 | 0.00e+00 |
| USD | `high_low` | xgboost | 55 | 0.7039 | +0.1900 | +55.86 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 21 | 0.7022 | +0.3498 | +121.06 | 0.00e+00 |
| USD | `vol_expand` | xgboost | 8 | 0.7013 | +0.3480 | +127.71 | 0.00e+00 |
| USD | `high_low` | lightgbm | 21 | 0.7008 | +0.2297 | +149.66 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 5 | 0.7000 | +0.3441 | +96.24 | 0.00e+00 |
| USD | `high_low` | lightgbm | 34 | 0.6991 | +0.2062 | +92.86 | 0.00e+00 |
| CAD | `vol_expand` | xgboost | 5 | 0.6987 | +0.3424 | +77.29 | 0.00e+00 |
| CAD | `vol_expand` | lightgbm | 5 | 0.6984 | +0.3419 | +129.32 | 0.00e+00 |
| USD | `vol_expand` | xgboost | 13 | 0.6980 | +0.3429 | +96.54 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 34 | 0.6970 | +0.3405 | +64.15 | 0.00e+00 |
| USD | `high_low` | lightgbm | 55 | 0.6954 | +0.1820 | +42.64 | 0.00e+00 |
| USD | `vol_expand` | xgboost | 5 | 0.6954 | +0.3362 | +118.26 | 0.00e+00 |
| USD | `vol_expand` | xgboost | 21 | 0.6954 | +0.3380 | +92.86 | 0.00e+00 |
| CAD | `vol_expand` | xgboost | 8 | 0.6940 | +0.3357 | +59.65 | 0.00e+00 |
| CAD | `vol_expand` | lightgbm | 8 | 0.6936 | +0.3350 | +62.36 | 0.00e+00 |
| USD | `vol_expand` | xgboost | 34 | 0.6935 | +0.3345 | +112.18 | 0.00e+00 |
| CAD | `vol_expand` | xgboost | 34 | 0.6892 | +0.3273 | +81.94 | 0.00e+00 |
| CAD | `vol_expand` | lightgbm | 34 | 0.6890 | +0.3270 | +105.27 | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 55 | n/a | +0.6635 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 55 | n/a | +0.6573 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 34 | n/a | +0.6555 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 34 | n/a | +0.6488 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 21 | n/a | +0.6397 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 21 | n/a | +0.6336 | n/a | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 55 | 0.6212 | +0.2096 | +87.43 | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 13 | n/a | +0.6141 | n/a | 0.00e+00 |
| CAD | `vol_expand` | lightgbm | 55 | 0.6120 | +0.1936 | +32.44 | 3.91e-231 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 13 | n/a | +0.6104 | n/a | 0.00e+00 |
| CAD | `vol_expand` | xgboost | 55 | 0.6095 | +0.1894 | +77.52 | 0.00e+00 |
| CAD | `high_low` | xgboost | 55 | 0.6089 | +0.1343 | +21.33 | 2.92e-101 |
| CAD | `up` | xgboost | 5 | 0.6057 | +0.1832 | +41.14 | 0.00e+00 |
| CAD | `high_low` | xgboost | 34 | 0.6035 | +0.1400 | +20.32 | 3.94e-92 |
| USD | `vol_expand` | xgboost | 55 | 0.6025 | +0.1773 | +62.60 | 0.00e+00 |
| CAD | `high_low` | xgboost | 21 | 0.6000 | +0.1472 | +36.71 | 2.70e-295 |
| CAD | `high_low` | xgboost | 5 | 0.5983 | +0.1695 | +52.05 | 0.00e+00 |
| CAD | `high_low` | xgboost | 8 | 0.5963 | +0.1608 | +42.35 | 0.00e+00 |
| CAD | `up` | lightgbm | 5 | 0.5950 | +0.1646 | +28.21 | 2.45e-175 |
| CAD | `high_low` | xgboost | 13 | 0.5939 | +0.1484 | +80.80 | 0.00e+00 |
| CAD | `high_low` | lightgbm | 34 | 0.5875 | +0.1185 | +33.78 | 2.03e-250 |
| CAD | `high_low` | lightgbm | 5 | 0.5867 | +0.1496 | +70.75 | 0.00e+00 |
| CAD | `high_low` | lightgbm | 21 | 0.5835 | +0.1229 | +36.57 | 3.64e-293 |
| CAD | `high_low` | lightgbm | 8 | 0.5828 | +0.1383 | +21.64 | 3.72e-104 |
| CAD | `xsec_vol_rank_cont` | xgboost | 8 | n/a | +0.5817 | n/a | 0.00e+00 |
| CAD | `high_low` | lightgbm | 55 | 0.5816 | +0.1006 | +17.49 | 8.49e-69 |
| CAD | `up` | xgboost | 8 | 0.5807 | +0.1396 | +64.20 | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 8 | n/a | +0.5777 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | xgboost | 34 | n/a | +0.5772 | n/a | 0.00e+00 |
| CAD | `high_low` | lightgbm | 13 | 0.5768 | +0.1214 | +27.59 | 6.74e-168 |
| CAD | `up` | lightgbm | 8 | 0.5663 | +0.1147 | +43.42 | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | xgboost | 55 | n/a | +0.5652 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | lightgbm | 55 | n/a | +0.5616 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | xgboost | 21 | n/a | +0.5610 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | lightgbm | 34 | n/a | +0.5606 | n/a | 0.00e+00 |
| CAD | `up` | xgboost | 13 | 0.5585 | +0.1012 | +21.47 | 1.34e-102 |
| USD | `xsec_vol_rank_cont` | lightgbm | 21 | n/a | +0.5562 | n/a | 0.00e+00 |
| CAD | `up` | lightgbm | 13 | 0.5410 | +0.0709 | +21.60 | 8.85e-104 |
| USD | `xsec_vol_rank_cont` | xgboost | 13 | n/a | +0.5401 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 5 | n/a | +0.5360 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 5 | n/a | +0.5330 | n/a | 0.00e+00 |
| CAD | `up` | xgboost | 21 | 0.5325 | +0.0560 | +10.34 | 2.40e-25 |
| USD | `xsec_vol_rank_cont` | lightgbm | 13 | n/a | +0.5208 | n/a | 0.00e+00 |
| CAD | `up` | lightgbm | 21 | 0.5145 | +0.0249 | +9.54 | 7.10e-22 |
| USD | `xsec_vol_rank_cont` | xgboost | 8 | n/a | +0.5085 | n/a | 0.00e+00 |
| USD | `up` | xgboost | 8 | 0.5038 | +0.0067 | +4.97 | 3.40e-07 |
| USD | `up` | lightgbm | 8 | 0.5034 | +0.0059 | +2.92 | 1.75e-03 |
| USD | `up` | lightgbm | 5 | 0.5029 | +0.0050 | +2.97 | 1.51e-03 |
| USD | `xsec_vol_rank_cont` | lightgbm | 8 | n/a | +0.4887 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | xgboost | 5 | n/a | +0.4657 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | lightgbm | 5 | n/a | +0.4428 | n/a | 0.00e+00 |

## 3. Feature attribution — winning cell

Winning cell `USD|lightgbm|xsec_vol_rank_bin|h55` (min AUC 0.8226).

- Top TreeSHAP (xgboost, full-panel refit): `atr_pct_3` 0.374, `amihud_3` 0.082, `adx_144` 0.063, `cs_donchian_break_21` 0.042, `disp_entropy_39` 0.042, `di_spread_3` 0.039, `swing_leg_len_3` 0.031, `swing_depth_atr` 0.030
- Top |linear coefficient| (logistic_l2): `atr_pct_3` +1.700, `sec_Metals & Mining` -0.288, `sec_Technology` +0.275, `di_spread_3` +0.270, `vwap_dist` -0.267, `adx_144` +0.254, `sec_Banks` +0.234, `srel_di_spread_21` -0.208

## Notes / deviations

- Ranking uses the cross-market minimum AUC per `(family, learner, h)` cell; the library stays Layer-1 (predictive only, D-023).
- Verdict PROVISIONAL — computed labels are advisory until the admin ratifies them.

