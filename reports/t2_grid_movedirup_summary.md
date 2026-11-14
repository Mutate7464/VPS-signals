# WI-048 — T2 grid `move_dir_up` (D-025 tier 2)

- Generated (UTC): 2026-11-14T04:54:34Z
- Grid: `move_dir_up` x 6 horizons (5, 8, 13, 21, 34, 55) x 2 learners x 2 markets; verdict = pooled OOF AUC + rank-IC (no tau grid, no EVAL)
- Learners: xgboost, lightgbm; variant pinned per market {'USD': 'exact', 'CAD': 'tol2'} (`*_full_k0.8`); rho prune 0.3
- CV: 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, h))`; placebo 5-seed label permutation on the AUC; BH-FDR alpha=0.05 over m=24 per family (design multiplicity)
- Features read at the detection bar only; float32, symbol-sequential, `n_jobs=2`; core cap 2.0 h
- Pickles (survivors only): `data/models/wi048/<MKT>_<learner>_<variant>_<family>_h<h>_f<fold>.pkl`; manifest `data/models/wi048/manifest.parquet` (WI-040 schema)
- Coverage: 24 cells scored, 0 truncated by the core budget (USD 283.7s, CAD 446.9s)

## 1. Cell ranking — cross-market consistent AUC / rank-IC

| rank | learner | h | AUC USD | AUC CAD | min AUC | min IC |
| ---: | :--- | ---: | ---: | ---: | ---: | ---: |
| 1 | xgboost | 5 | 0.6441 | 0.6407 | **0.6407** | +0.2230 |
| 2 | lightgbm | 5 | 0.6350 | 0.6324 | **0.6324** | +0.2098 |
| 3 | xgboost | 8 | 0.6214 | 0.6307 | **0.6214** | +0.2085 |
| 4 | lightgbm | 8 | 0.6138 | 0.6183 | **0.6138** | +0.1955 |
| 5 | xgboost | 13 | 0.5897 | 0.6139 | **0.5897** | +0.1549 |
| 6 | lightgbm | 13 | 0.5854 | 0.5989 | **0.5854** | +0.1474 |
| 7 | xgboost | 21 | 0.5659 | 0.5945 | **0.5659** | +0.1142 |
| 8 | lightgbm | 21 | 0.5551 | 0.5756 | **0.5551** | +0.0955 |
| 9 | xgboost | 34 | 0.5450 | 0.5709 | **0.5450** | +0.0780 |
| 10 | lightgbm | 34 | 0.5257 | 0.5435 | **0.5257** | +0.0447 |
| 11 | xgboost | 55 | 0.5165 | 0.5462 | **0.5165** | +0.0287 |
| 12 | lightgbm | 55 | 0.5139 | 0.5106 | **0.5106** | +0.0184 |

## 2. FDR survivors (BH alpha=0.05, m=24)

| market | family | learner | h | AUC | IC | z | p |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| USD | `move_dir_up` | xgboost | 5 | 0.6441 | +0.2451 | +67.56 | 0.00e+00 |
| CAD | `move_dir_up` | xgboost | 5 | 0.6407 | +0.2230 | +51.00 | 0.00e+00 |
| USD | `move_dir_up` | lightgbm | 5 | 0.6350 | +0.2297 | +690.78 | 0.00e+00 |
| CAD | `move_dir_up` | lightgbm | 5 | 0.6324 | +0.2098 | +47.17 | 0.00e+00 |
| CAD | `move_dir_up` | xgboost | 8 | 0.6307 | +0.2160 | +43.54 | 0.00e+00 |
| USD | `move_dir_up` | xgboost | 8 | 0.6214 | +0.2085 | +57.07 | 0.00e+00 |
| CAD | `move_dir_up` | lightgbm | 8 | 0.6183 | +0.1955 | +46.72 | 0.00e+00 |
| CAD | `move_dir_up` | xgboost | 13 | 0.6139 | +0.1925 | +57.37 | 0.00e+00 |
| USD | `move_dir_up` | lightgbm | 8 | 0.6138 | +0.1955 | +135.52 | 0.00e+00 |
| CAD | `move_dir_up` | lightgbm | 13 | 0.5989 | +0.1671 | +89.00 | 0.00e+00 |
| CAD | `move_dir_up` | xgboost | 21 | 0.5945 | +0.1623 | +43.61 | 0.00e+00 |
| USD | `move_dir_up` | xgboost | 13 | 0.5897 | +0.1549 | +98.78 | 0.00e+00 |
| USD | `move_dir_up` | lightgbm | 13 | 0.5854 | +0.1474 | +70.96 | 0.00e+00 |
| CAD | `move_dir_up` | lightgbm | 21 | 0.5756 | +0.1297 | +63.79 | 0.00e+00 |
| CAD | `move_dir_up` | xgboost | 34 | 0.5709 | +0.1226 | +31.07 | 3.25e-212 |
| USD | `move_dir_up` | xgboost | 21 | 0.5659 | +0.1142 | +72.10 | 0.00e+00 |
| USD | `move_dir_up` | lightgbm | 21 | 0.5551 | +0.0955 | +34.69 | 6.51e-264 |
| CAD | `move_dir_up` | xgboost | 55 | 0.5462 | +0.0803 | +16.11 | 1.10e-58 |
| USD | `move_dir_up` | xgboost | 34 | 0.5450 | +0.0780 | +30.45 | 5.67e-204 |
| CAD | `move_dir_up` | lightgbm | 34 | 0.5435 | +0.0751 | +13.00 | 6.19e-39 |
| USD | `move_dir_up` | lightgbm | 34 | 0.5257 | +0.0447 | +16.26 | 9.11e-60 |
| USD | `move_dir_up` | xgboost | 55 | 0.5165 | +0.0287 | +16.41 | 7.53e-61 |
| USD | `move_dir_up` | lightgbm | 55 | 0.5139 | +0.0241 | +19.03 | 4.84e-81 |
| CAD | `move_dir_up` | lightgbm | 55 | 0.5106 | +0.0184 | +4.60 | 2.08e-06 |

## Notes / deviations

- Pure-signal run: nothing is selected, no portfolio returns, no costs.
- Label definitions live in `src/swing_bsh/targets_ext.py` (one module docstring per family); the density probe `reports/t2_label_density_probe.md` is the smoke gate.
- Verdict PROVISIONAL until the admin ratifies it in chat.

