# WI-048 — T2 grid `high_low` (D-025 tier 2)

- Generated (UTC): 2026-11-13T05:44:07Z
- Grid: `high_low` x 6 horizons (5, 8, 13, 21, 34, 55) x 2 learners x 2 markets; verdict = pooled OOF AUC + rank-IC (no tau grid, no EVAL)
- Learners: xgboost, lightgbm; variant pinned per market {'USD': 'exact', 'CAD': 'tol2'} (`*_full_k0.8`); rho prune 0.3
- CV: 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, h))`; placebo 5-seed label permutation on the AUC; BH-FDR alpha=0.05 over m=24 per family (design multiplicity)
- Features read at the detection bar only; float32, symbol-sequential, `n_jobs=2`; core cap 2.0 h
- Pickles (survivors only): `data/models/wi048/<MKT>_<learner>_<variant>_<family>_h<h>_f<fold>.pkl`; manifest `data/models/wi048/manifest.parquet` (WI-040 schema)
- Coverage: 24 cells scored, 0 truncated by the core budget (USD 265.8s, CAD 408.1s)

## 1. Cell ranking — cross-market consistent AUC / rank-IC

| rank | learner | h | AUC USD | AUC CAD | min AUC | min IC |
| ---: | :--- | ---: | ---: | ---: | ---: | ---: |
| 1 | xgboost | 55 | 0.7039 | 0.6089 | **0.6089** | +0.1343 |
| 2 | xgboost | 34 | 0.7048 | 0.6035 | **0.6035** | +0.1400 |
| 3 | xgboost | 21 | 0.7075 | 0.6000 | **0.6000** | +0.1472 |
| 4 | xgboost | 5 | 0.7241 | 0.5983 | **0.5983** | +0.1695 |
| 5 | xgboost | 8 | 0.7158 | 0.5963 | **0.5963** | +0.1608 |
| 6 | xgboost | 13 | 0.7110 | 0.5939 | **0.5939** | +0.1484 |
| 7 | lightgbm | 34 | 0.6991 | 0.5875 | **0.5875** | +0.1185 |
| 8 | lightgbm | 5 | 0.7212 | 0.5867 | **0.5867** | +0.1496 |
| 9 | lightgbm | 21 | 0.7008 | 0.5835 | **0.5835** | +0.1229 |
| 10 | lightgbm | 8 | 0.7113 | 0.5828 | **0.5828** | +0.1383 |
| 11 | lightgbm | 55 | 0.6954 | 0.5816 | **0.5816** | +0.1006 |
| 12 | lightgbm | 13 | 0.7043 | 0.5768 | **0.5768** | +0.1214 |

## 2. FDR survivors (BH alpha=0.05, m=24)

| market | family | learner | h | AUC | z | p |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| USD | `high_low` | xgboost | 5 | 0.7241 | +67.47 | 0.00e+00 |
| USD | `high_low` | lightgbm | 5 | 0.7212 | +86.64 | 0.00e+00 |
| USD | `high_low` | xgboost | 8 | 0.7158 | +69.14 | 0.00e+00 |
| USD | `high_low` | lightgbm | 8 | 0.7113 | +110.03 | 0.00e+00 |
| USD | `high_low` | xgboost | 13 | 0.7110 | +160.82 | 0.00e+00 |
| USD | `high_low` | xgboost | 21 | 0.7075 | +137.35 | 0.00e+00 |
| USD | `high_low` | xgboost | 34 | 0.7048 | +42.27 | 0.00e+00 |
| USD | `high_low` | lightgbm | 13 | 0.7043 | +69.50 | 0.00e+00 |
| USD | `high_low` | xgboost | 55 | 0.7039 | +55.86 | 0.00e+00 |
| USD | `high_low` | lightgbm | 21 | 0.7008 | +149.66 | 0.00e+00 |
| USD | `high_low` | lightgbm | 34 | 0.6991 | +92.86 | 0.00e+00 |
| USD | `high_low` | lightgbm | 55 | 0.6954 | +42.64 | 0.00e+00 |
| CAD | `high_low` | xgboost | 55 | 0.6089 | +21.33 | 2.92e-101 |
| CAD | `high_low` | xgboost | 34 | 0.6035 | +20.32 | 3.94e-92 |
| CAD | `high_low` | xgboost | 21 | 0.6000 | +36.71 | 2.70e-295 |
| CAD | `high_low` | xgboost | 5 | 0.5983 | +52.05 | 0.00e+00 |
| CAD | `high_low` | xgboost | 8 | 0.5963 | +42.35 | 0.00e+00 |
| CAD | `high_low` | xgboost | 13 | 0.5939 | +80.80 | 0.00e+00 |
| CAD | `high_low` | lightgbm | 34 | 0.5875 | +33.78 | 2.03e-250 |
| CAD | `high_low` | lightgbm | 5 | 0.5867 | +70.75 | 0.00e+00 |
| CAD | `high_low` | lightgbm | 21 | 0.5835 | +36.57 | 3.64e-293 |
| CAD | `high_low` | lightgbm | 8 | 0.5828 | +21.64 | 3.72e-104 |
| CAD | `high_low` | lightgbm | 55 | 0.5816 | +17.49 | 8.49e-69 |
| CAD | `high_low` | lightgbm | 13 | 0.5768 | +27.59 | 6.74e-168 |

## Notes / deviations

- Pure-signal run: nothing is selected, no portfolio returns, no costs.
- Label definitions live in `src/swing_bsh/targets_ext.py` (one module docstring per family); the density probe `reports/t2_label_density_probe.md` is the smoke gate.
- Verdict PROVISIONAL until the admin ratifies it in chat.

