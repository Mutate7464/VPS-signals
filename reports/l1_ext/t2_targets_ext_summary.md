# WI-048 — T2 cross-family summary (D-025 tier 2, PROVISIONAL)

- Generated (UTC): 2026-11-14T05:29:27Z
- Families: up, high_low, vol_expand, vol_expand_fwd; 216 cells joined from the per-family sidecars; no new training except the winner-cell attribution refit
- Learners: lightgbm, xgboost; variant pinned per market {'USD': 'exact', 'CAD': 'tol2'} (`*_full_k0.8`); rho prune 0.3
- CV: 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, h))`; placebo 5-seed label permutation on the AUC; BH-FDR alpha=0.05 over m=24 per family (design multiplicity)
- Features read at the detection bar only; float32, symbol-sequential, `n_jobs=2`; core cap 2.0 h
- Pickles (survivors only): `data/models/wi048/<MKT>_<learner>_<variant>_<family>_h<h>_f<fold>.pkl`; manifest `data/models/wi048/manifest.parquet` (WI-040 schema)

## 1. Target ranking — family x best cell (cross-market min AUC)

| rank | family | best cell | AUC USD | AUC CAD | min AUC | min IC | cells |
| ---: | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| 1 | `xsec_vol_rank_bin` | lightgbm/h55 | 0.8226 | 0.8461 | **0.8226** | +0.5250 | 12 |
| 2 | `vol_expand` | lightgbm/h13 | 0.7068 | 0.7130 | **0.7068** | +0.3581 | 12 |
| 3 | `move_dir_up` | xgboost/h5 | 0.6441 | 0.6407 | **0.6407** | +0.2230 | 12 |
| 4 | `high_low` | xgboost/h55 | 0.7039 | 0.6089 | **0.6089** | +0.1343 | 12 |
| 5 | `move_occur` | xgboost/h5 | 0.7219 | 0.6033 | **0.6033** | +0.1782 | 12 |
| 6 | `mfe_mae_bin` | xgboost/h55 | 0.5515 | 0.5572 | **0.5515** | +0.0890 | 12 |
| 7 | `up` | xgboost/h8 | 0.5038 | 0.5807 | **0.5038** | +0.0067 | 12 |

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
| USD | `move_occur` | xgboost | 5 | 0.7219 | +0.3311 | +95.82 | 0.00e+00 |
| USD | `high_low` | lightgbm | 5 | 0.7212 | +0.3287 | +86.64 | 0.00e+00 |
| USD | `move_occur` | lightgbm | 5 | 0.7196 | +0.3276 | +108.63 | 0.00e+00 |
| CAD | `vol_expand` | lightgbm | 21 | 0.7169 | +0.3750 | +145.46 | 0.00e+00 |
| USD | `high_low` | xgboost | 8 | 0.7158 | +0.2964 | +69.14 | 0.00e+00 |
| CAD | `vol_expand` | xgboost | 21 | 0.7144 | +0.3707 | +76.31 | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 55 | n/a | +0.7135 | n/a | 0.00e+00 |
| CAD | `vol_expand` | lightgbm | 13 | 0.7130 | +0.3689 | +81.12 | 0.00e+00 |
| CAD | `vol_expand` | xgboost | 13 | 0.7120 | +0.3672 | +46.87 | 0.00e+00 |
| USD | `high_low` | lightgbm | 8 | 0.7113 | +0.2903 | +110.03 | 0.00e+00 |
| USD | `move_occur` | xgboost | 8 | 0.7112 | +0.2927 | +74.52 | 0.00e+00 |
| USD | `high_low` | xgboost | 13 | 0.7110 | +0.2655 | +160.82 | 0.00e+00 |
| USD | `move_occur` | lightgbm | 8 | 0.7089 | +0.2896 | +171.71 | 0.00e+00 |
| USD | `high_low` | xgboost | 21 | 0.7075 | +0.2373 | +137.35 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 8 | 0.7073 | +0.3584 | +93.89 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 13 | 0.7068 | +0.3581 | +111.11 | 0.00e+00 |
| USD | `high_low` | xgboost | 34 | 0.7048 | +0.2121 | +42.27 | 0.00e+00 |
| USD | `high_low` | lightgbm | 13 | 0.7043 | +0.2570 | +69.50 | 0.00e+00 |
| USD | `high_low` | xgboost | 55 | 0.7039 | +0.1900 | +55.86 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 21 | 0.7022 | +0.3498 | +121.06 | 0.00e+00 |
| USD | `vol_expand` | xgboost | 8 | 0.7013 | +0.3480 | +127.71 | 0.00e+00 |
| USD | `high_low` | lightgbm | 21 | 0.7008 | +0.2297 | +149.66 | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 34 | n/a | +0.7005 | n/a | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 5 | 0.7000 | +0.3441 | +96.24 | 0.00e+00 |
| USD | `move_occur` | xgboost | 13 | 0.6998 | +0.2562 | +91.32 | 0.00e+00 |
| USD | `high_low` | lightgbm | 34 | 0.6991 | +0.2062 | +92.86 | 0.00e+00 |
| CAD | `vol_expand` | xgboost | 5 | 0.6987 | +0.3424 | +77.29 | 0.00e+00 |
| CAD | `vol_expand` | lightgbm | 5 | 0.6984 | +0.3419 | +129.32 | 0.00e+00 |
| USD | `vol_expand` | xgboost | 13 | 0.6980 | +0.3429 | +96.54 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 34 | 0.6970 | +0.3405 | +64.15 | 0.00e+00 |
| USD | `high_low` | lightgbm | 55 | 0.6954 | +0.1820 | +42.64 | 0.00e+00 |
| USD | `vol_expand` | xgboost | 5 | 0.6954 | +0.3362 | +118.26 | 0.00e+00 |
| USD | `vol_expand` | xgboost | 21 | 0.6954 | +0.3380 | +92.86 | 0.00e+00 |
| CAD | `vol_expand` | xgboost | 8 | 0.6940 | +0.3357 | +59.65 | 0.00e+00 |
| USD | `move_occur` | lightgbm | 13 | 0.6939 | +0.2487 | +124.72 | 0.00e+00 |
| CAD | `vol_expand` | lightgbm | 8 | 0.6936 | +0.3350 | +62.36 | 0.00e+00 |
| USD | `vol_expand` | xgboost | 34 | 0.6935 | +0.3345 | +112.18 | 0.00e+00 |
| CAD | `vol_expand` | xgboost | 34 | 0.6892 | +0.3273 | +81.94 | 0.00e+00 |
| CAD | `vol_expand` | lightgbm | 34 | 0.6890 | +0.3270 | +105.27 | 0.00e+00 |
| USD | `move_occur` | xgboost | 21 | 0.6872 | +0.2232 | +56.27 | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 21 | n/a | +0.6862 | n/a | 0.00e+00 |
| USD | `move_occur` | lightgbm | 21 | 0.6831 | +0.2183 | +89.20 | 0.00e+00 |
| USD | `move_occur` | xgboost | 34 | 0.6710 | +0.1920 | +67.19 | 0.00e+00 |
| USD | `move_occur` | lightgbm | 34 | 0.6640 | +0.1841 | +39.29 | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 13 | n/a | +0.6606 | n/a | 0.00e+00 |
| USD | `move_occur` | xgboost | 55 | 0.6493 | +0.1620 | +36.39 | 3.34e-290 |
| USD | `xsec_vol_rank_cont` | xgboost | 55 | n/a | +0.6475 | n/a | 0.00e+00 |
| USD | `move_occur` | lightgbm | 55 | 0.6465 | +0.1589 | +41.30 | 0.00e+00 |
| USD | `move_dir_up` | xgboost | 5 | 0.6441 | +0.2451 | +67.56 | 0.00e+00 |
| CAD | `move_dir_up` | xgboost | 5 | 0.6407 | +0.2230 | +51.00 | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | xgboost | 34 | n/a | +0.6362 | n/a | 0.00e+00 |
| USD | `move_dir_up` | lightgbm | 5 | 0.6350 | +0.2297 | +690.78 | 0.00e+00 |
| CAD | `move_dir_up` | lightgbm | 5 | 0.6324 | +0.2098 | +47.17 | 0.00e+00 |
| CAD | `move_dir_up` | xgboost | 8 | 0.6307 | +0.2160 | +43.54 | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 8 | n/a | +0.6282 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | xgboost | 21 | n/a | +0.6219 | n/a | 0.00e+00 |
| USD | `move_dir_up` | xgboost | 8 | 0.6214 | +0.2085 | +57.07 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 55 | 0.6212 | +0.2096 | +87.43 | 0.00e+00 |
| CAD | `move_dir_up` | lightgbm | 8 | 0.6183 | +0.1955 | +46.72 | 0.00e+00 |
| CAD | `move_dir_up` | xgboost | 13 | 0.6139 | +0.1925 | +57.37 | 0.00e+00 |
| USD | `move_dir_up` | lightgbm | 8 | 0.6138 | +0.1955 | +135.52 | 0.00e+00 |
| CAD | `vol_expand` | lightgbm | 55 | 0.6120 | +0.1936 | +32.44 | 3.91e-231 |
| CAD | `vol_expand` | xgboost | 55 | 0.6095 | +0.1894 | +77.52 | 0.00e+00 |
| CAD | `high_low` | xgboost | 55 | 0.6089 | +0.1343 | +21.33 | 2.92e-101 |
| CAD | `up` | xgboost | 5 | 0.6057 | +0.1832 | +41.14 | 0.00e+00 |
| CAD | `high_low` | xgboost | 34 | 0.6035 | +0.1400 | +20.32 | 3.94e-92 |
| CAD | `move_occur` | xgboost | 5 | 0.6033 | +0.1782 | +39.68 | 0.00e+00 |
| USD | `vol_expand` | xgboost | 55 | 0.6025 | +0.1773 | +62.60 | 0.00e+00 |
| CAD | `move_occur` | xgboost | 21 | 0.6009 | +0.1505 | +27.02 | 4.89e-161 |
| CAD | `high_low` | xgboost | 21 | 0.6000 | +0.1472 | +36.71 | 2.70e-295 |
| CAD | `move_dir_up` | lightgbm | 13 | 0.5989 | +0.1671 | +89.00 | 0.00e+00 |
| CAD | `high_low` | xgboost | 5 | 0.5983 | +0.1695 | +52.05 | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | xgboost | 13 | n/a | +0.5970 | n/a | 0.00e+00 |
| CAD | `move_occur` | xgboost | 8 | 0.5970 | +0.1622 | +51.41 | 0.00e+00 |
| CAD | `move_occur` | xgboost | 13 | 0.5970 | +0.1539 | +55.41 | 0.00e+00 |
| CAD | `high_low` | xgboost | 8 | 0.5963 | +0.1608 | +42.35 | 0.00e+00 |
| CAD | `up` | lightgbm | 5 | 0.5950 | +0.1646 | +28.21 | 2.45e-175 |
| CAD | `move_dir_up` | xgboost | 21 | 0.5945 | +0.1623 | +43.61 | 0.00e+00 |
| CAD | `high_low` | xgboost | 13 | 0.5939 | +0.1484 | +80.80 | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 34 | n/a | +0.5938 | n/a | 0.00e+00 |
| CAD | `move_occur` | xgboost | 34 | 0.5937 | +0.1309 | +70.72 | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 55 | n/a | +0.5932 | n/a | 0.00e+00 |
| CAD | `move_occur` | xgboost | 55 | 0.5922 | +0.1219 | +23.66 | 5.18e-124 |
| USD | `move_dir_up` | xgboost | 13 | 0.5897 | +0.1549 | +98.78 | 0.00e+00 |
| CAD | `high_low` | lightgbm | 34 | 0.5875 | +0.1185 | +33.78 | 2.03e-250 |
| CAD | `move_occur` | lightgbm | 5 | 0.5875 | +0.1508 | +39.25 | 0.00e+00 |
| CAD | `move_occur` | lightgbm | 21 | 0.5874 | +0.1304 | +34.02 | 5.14e-254 |
| CAD | `high_low` | lightgbm | 5 | 0.5867 | +0.1496 | +70.75 | 0.00e+00 |
| USD | `move_dir_up` | lightgbm | 13 | 0.5854 | +0.1474 | +70.96 | 0.00e+00 |
| CAD | `move_occur` | lightgbm | 8 | 0.5843 | +0.1410 | +32.18 | 1.94e-227 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 21 | n/a | +0.5837 | n/a | 0.00e+00 |
| CAD | `high_low` | lightgbm | 21 | 0.5835 | +0.1229 | +36.57 | 3.64e-293 |
| CAD | `high_low` | lightgbm | 8 | 0.5828 | +0.1383 | +21.64 | 3.72e-104 |
| CAD | `high_low` | lightgbm | 55 | 0.5816 | +0.1006 | +17.49 | 8.49e-69 |
| CAD | `move_occur` | lightgbm | 34 | 0.5812 | +0.1134 | +36.31 | 5.68e-289 |
| CAD | `up` | xgboost | 8 | 0.5807 | +0.1396 | +64.20 | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 5 | n/a | +0.5797 | n/a | 0.00e+00 |
| CAD | `move_occur` | lightgbm | 13 | 0.5786 | +0.1248 | +45.90 | 0.00e+00 |
| CAD | `move_occur` | lightgbm | 55 | 0.5781 | +0.1031 | +18.17 | 4.35e-74 |
| CAD | `high_low` | lightgbm | 13 | 0.5768 | +0.1214 | +27.59 | 6.74e-168 |
| CAD | `move_dir_up` | lightgbm | 21 | 0.5756 | +0.1297 | +63.79 | 0.00e+00 |
| CAD | `move_dir_up` | xgboost | 34 | 0.5709 | +0.1226 | +31.07 | 3.25e-212 |
| USD | `xsec_vol_rank_cont` | lightgbm | 55 | n/a | +0.5702 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | lightgbm | 34 | n/a | +0.5668 | n/a | 0.00e+00 |
| CAD | `up` | lightgbm | 8 | 0.5663 | +0.1147 | +43.42 | 0.00e+00 |
| USD | `move_dir_up` | xgboost | 21 | 0.5659 | +0.1142 | +72.10 | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | lightgbm | 21 | n/a | +0.5617 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | xgboost | 8 | n/a | +0.5603 | n/a | 0.00e+00 |
| CAD | `up` | xgboost | 13 | 0.5585 | +0.1012 | +21.47 | 1.34e-102 |
| CAD | `mfe_mae_bin` | xgboost | 55 | 0.5572 | +0.0991 | +33.34 | 5.05e-244 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 13 | n/a | +0.5571 | n/a | 0.00e+00 |
| USD | `move_dir_up` | lightgbm | 21 | 0.5551 | +0.0955 | +34.69 | 6.51e-264 |
| USD | `mfe_mae_bin` | xgboost | 55 | 0.5515 | +0.0890 | +47.81 | 0.00e+00 |
| CAD | `mfe_mae_bin` | xgboost | 34 | 0.5501 | +0.0869 | +14.53 | 3.97e-48 |
| USD | `mfe_mae_bin` | lightgbm | 55 | 0.5491 | +0.0849 | +30.75 | 6.60e-208 |
| USD | `mfe_mae_bin` | xgboost | 34 | 0.5465 | +0.0804 | +24.98 | 4.90e-138 |
| CAD | `move_dir_up` | xgboost | 55 | 0.5462 | +0.0803 | +16.11 | 1.10e-58 |
| USD | `mfe_mae_bin` | lightgbm | 34 | 0.5452 | +0.0779 | +18.64 | 7.36e-78 |
| USD | `move_dir_up` | xgboost | 34 | 0.5450 | +0.0780 | +30.45 | 5.67e-204 |
| CAD | `move_dir_up` | lightgbm | 34 | 0.5435 | +0.0751 | +13.00 | 6.19e-39 |
| CAD | `mfe_mae_bin` | xgboost | 5 | 0.5435 | +0.0754 | +17.75 | 9.26e-71 |
| CAD | `up` | lightgbm | 13 | 0.5410 | +0.0709 | +21.60 | 8.85e-104 |
| CAD | `mfe_mae_bin` | xgboost | 21 | 0.5383 | +0.0664 | +10.90 | 5.54e-28 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 8 | n/a | +0.5364 | n/a | 0.00e+00 |
| CAD | `mfe_mae_bin` | xgboost | 8 | 0.5340 | +0.0590 | +12.75 | 1.47e-37 |
| USD | `mfe_mae_bin` | xgboost | 21 | 0.5338 | +0.0582 | +24.41 | 6.01e-132 |
| CAD | `mfe_mae_bin` | lightgbm | 5 | 0.5337 | +0.0584 | +12.94 | 1.35e-38 |
| CAD | `up` | xgboost | 21 | 0.5325 | +0.0560 | +10.34 | 2.40e-25 |
| CAD | `mfe_mae_bin` | xgboost | 13 | 0.5285 | +0.0495 | +10.37 | 1.79e-25 |
| USD | `mfe_mae_bin` | lightgbm | 21 | 0.5279 | +0.0481 | +9.34 | 4.71e-21 |
| CAD | `mfe_mae_bin` | lightgbm | 55 | 0.5274 | +0.0475 | +11.06 | 9.74e-29 |
| CAD | `mfe_mae_bin` | lightgbm | 8 | 0.5263 | +0.0457 | +5.81 | 3.15e-09 |
| USD | `move_dir_up` | lightgbm | 34 | 0.5257 | +0.0447 | +16.26 | 9.11e-60 |
| USD | `mfe_mae_bin` | xgboost | 13 | 0.5243 | +0.0419 | +10.59 | 1.73e-26 |
| USD | `xsec_vol_rank_cont` | lightgbm | 13 | n/a | +0.5228 | n/a | 0.00e+00 |
| USD | `mfe_mae_bin` | xgboost | 8 | 0.5218 | +0.0374 | +7.89 | 1.50e-15 |
| CAD | `mfe_mae_bin` | lightgbm | 34 | 0.5210 | +0.0364 | +10.94 | 3.66e-28 |
| USD | `mfe_mae_bin` | lightgbm | 13 | 0.5207 | +0.0356 | +6.34 | 1.14e-10 |
| CAD | `mfe_mae_bin` | lightgbm | 21 | 0.5194 | +0.0336 | +6.33 | 1.25e-10 |
| CAD | `mfe_mae_bin` | lightgbm | 13 | 0.5189 | +0.0327 | +9.18 | 2.12e-20 |
| USD | `mfe_mae_bin` | lightgbm | 8 | 0.5179 | +0.0307 | +5.58 | 1.18e-08 |
| USD | `move_dir_up` | xgboost | 55 | 0.5165 | +0.0287 | +16.41 | 7.53e-61 |
| CAD | `up` | lightgbm | 21 | 0.5145 | +0.0249 | +9.54 | 7.10e-22 |
| USD | `move_dir_up` | lightgbm | 55 | 0.5139 | +0.0241 | +19.03 | 4.84e-81 |
| USD | `mfe_mae_bin` | xgboost | 5 | 0.5109 | +0.0186 | +12.14 | 3.24e-34 |
| CAD | `move_dir_up` | lightgbm | 55 | 0.5106 | +0.0184 | +4.60 | 2.08e-06 |
| USD | `xsec_vol_rank_cont` | xgboost | 5 | n/a | +0.5095 | n/a | 0.00e+00 |
| USD | `mfe_mae_bin` | lightgbm | 5 | 0.5090 | +0.0155 | +6.20 | 2.89e-10 |
| USD | `up` | xgboost | 8 | 0.5038 | +0.0067 | +4.97 | 3.40e-07 |
| USD | `up` | lightgbm | 8 | 0.5034 | +0.0059 | +2.92 | 1.75e-03 |
| USD | `up` | lightgbm | 5 | 0.5029 | +0.0050 | +2.97 | 1.51e-03 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 5 | n/a | +0.4874 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | lightgbm | 8 | n/a | +0.4861 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | lightgbm | 5 | n/a | +0.4068 | n/a | 0.00e+00 |
| CAD | `mfe_mae_cont` | xgboost | 55 | n/a | +0.2241 | n/a | 6.47e-48 |
| USD | `mfe_mae_cont` | xgboost | 55 | n/a | +0.1665 | n/a | 5.83e-31 |
| CAD | `mfe_mae_cont` | xgboost | 34 | n/a | +0.1597 | n/a | 4.66e-34 |
| USD | `mfe_mae_cont` | lightgbm | 55 | n/a | +0.1512 | n/a | 1.27e-28 |
| CAD | `mfe_mae_cont` | lightgbm | 55 | n/a | +0.1397 | n/a | 7.69e-33 |
| USD | `mfe_mae_cont` | lightgbm | 34 | n/a | +0.1295 | n/a | 7.94e-28 |
| USD | `mfe_mae_cont` | xgboost | 34 | n/a | +0.1276 | n/a | 4.33e-26 |
| CAD | `mfe_mae_cont` | xgboost | 21 | n/a | +0.1194 | n/a | 1.63e-22 |
| CAD | `mfe_mae_cont` | lightgbm | 34 | n/a | +0.1113 | n/a | 1.59e-21 |
| USD | `mfe_mae_cont` | xgboost | 21 | n/a | +0.1003 | n/a | 2.33e-14 |
| CAD | `mfe_mae_cont` | xgboost | 13 | n/a | +0.0998 | n/a | 1.03e-25 |
| CAD | `mfe_mae_cont` | xgboost | 5 | n/a | +0.0897 | n/a | 2.89e-24 |
| CAD | `mfe_mae_cont` | xgboost | 8 | n/a | +0.0851 | n/a | 7.10e-20 |
| USD | `mfe_mae_cont` | lightgbm | 21 | n/a | +0.0845 | n/a | 5.39e-17 |
| CAD | `mfe_mae_cont` | lightgbm | 21 | n/a | +0.0835 | n/a | 1.12e-14 |
| USD | `mfe_mae_cont` | xgboost | 13 | n/a | +0.0818 | n/a | 3.83e-08 |
| CAD | `mfe_mae_cont` | lightgbm | 13 | n/a | +0.0600 | n/a | 7.46e-13 |
| USD | `mfe_mae_cont` | xgboost | 8 | n/a | +0.0564 | n/a | 8.65e-06 |
| CAD | `mfe_mae_cont` | lightgbm | 5 | n/a | +0.0562 | n/a | 1.88e-11 |
| USD | `mfe_mae_cont` | lightgbm | 13 | n/a | +0.0548 | n/a | 1.55e-09 |
| CAD | `mfe_mae_cont` | lightgbm | 8 | n/a | +0.0520 | n/a | 7.03e-11 |
| USD | `mfe_mae_cont` | lightgbm | 8 | n/a | +0.0420 | n/a | 8.04e-06 |
| USD | `mfe_mae_cont` | xgboost | 5 | n/a | +0.0350 | n/a | 3.16e-03 |
| USD | `mfe_mae_cont` | lightgbm | 5 | n/a | +0.0300 | n/a | 3.39e-03 |

## 3. Feature attribution — winning cell

Winning cell `USD|lightgbm|xsec_vol_rank_bin|h55` (min AUC 0.8226).

- Top TreeSHAP (xgboost, full-panel refit): `atr_pct_3` 0.374, `amihud_3` 0.082, `adx_144` 0.063, `cs_donchian_break_21` 0.042, `disp_entropy_39` 0.042, `di_spread_3` 0.039, `swing_leg_len_3` 0.031, `swing_depth_atr` 0.030
- Top |linear coefficient| (logistic_l2): `atr_pct_3` +1.700, `sec_Metals & Mining` -0.288, `sec_Technology` +0.275, `di_spread_3` +0.270, `vwap_dist` -0.267, `adx_144` +0.254, `sec_Banks` +0.234, `srel_di_spread_21` -0.208

## Notes / deviations

- Ranking uses the cross-market minimum AUC per `(family, learner, h)` cell; the library stays Layer-1 (predictive only, D-023).
- Verdict PROVISIONAL — computed labels are advisory until the admin ratifies them.

