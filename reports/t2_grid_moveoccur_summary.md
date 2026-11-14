# WI-048 — T2 grid `move_occur` (D-025 tier 2)

- Generated (UTC): 2026-11-14T04:38:35Z
- Grid: `move_occur` x 6 horizons (5, 8, 13, 21, 34, 55) x 2 learners x 2 markets; verdict = pooled OOF AUC + rank-IC (no tau grid, no EVAL)
- Learners: xgboost, lightgbm; variant pinned per market {'USD': 'exact', 'CAD': 'tol2'} (`*_full_k0.8`); rho prune 0.3
- CV: 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, h))`; placebo 5-seed label permutation on the AUC; BH-FDR alpha=0.05 over m=24 per family (design multiplicity)
- Features read at the detection bar only; float32, symbol-sequential, `n_jobs=2`; core cap 2.0 h
- Pickles (survivors only): `data/models/wi048/<MKT>_<learner>_<variant>_<family>_h<h>_f<fold>.pkl`; manifest `data/models/wi048/manifest.parquet` (WI-040 schema)
- Coverage: 24 cells scored, 0 truncated by the core budget (USD 355.0s, CAD 543.7s)

## 1. Cell ranking — cross-market consistent AUC / rank-IC

| rank | learner | h | AUC USD | AUC CAD | min AUC | min IC |
| ---: | :--- | ---: | ---: | ---: | ---: | ---: |
| 1 | xgboost | 5 | 0.7219 | 0.6033 | **0.6033** | +0.1782 |
| 2 | xgboost | 21 | 0.6872 | 0.6009 | **0.6009** | +0.1505 |
| 3 | xgboost | 8 | 0.7112 | 0.5970 | **0.5970** | +0.1622 |
| 4 | xgboost | 13 | 0.6998 | 0.5970 | **0.5970** | +0.1539 |
| 5 | xgboost | 34 | 0.6710 | 0.5937 | **0.5937** | +0.1309 |
| 6 | xgboost | 55 | 0.6493 | 0.5922 | **0.5922** | +0.1219 |
| 7 | lightgbm | 5 | 0.7196 | 0.5875 | **0.5875** | +0.1508 |
| 8 | lightgbm | 21 | 0.6831 | 0.5874 | **0.5874** | +0.1304 |
| 9 | lightgbm | 8 | 0.7089 | 0.5843 | **0.5843** | +0.1410 |
| 10 | lightgbm | 34 | 0.6640 | 0.5812 | **0.5812** | +0.1134 |
| 11 | lightgbm | 13 | 0.6939 | 0.5786 | **0.5786** | +0.1248 |
| 12 | lightgbm | 55 | 0.6465 | 0.5781 | **0.5781** | +0.1031 |

## 2. FDR survivors (BH alpha=0.05, m=24)

| market | family | learner | h | AUC | IC | z | p |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| USD | `move_occur` | xgboost | 5 | 0.7219 | +0.3311 | +95.82 | 0.00e+00 |
| USD | `move_occur` | lightgbm | 5 | 0.7196 | +0.3276 | +108.63 | 0.00e+00 |
| USD | `move_occur` | xgboost | 8 | 0.7112 | +0.2927 | +74.52 | 0.00e+00 |
| USD | `move_occur` | lightgbm | 8 | 0.7089 | +0.2896 | +171.71 | 0.00e+00 |
| USD | `move_occur` | xgboost | 13 | 0.6998 | +0.2562 | +91.32 | 0.00e+00 |
| USD | `move_occur` | lightgbm | 13 | 0.6939 | +0.2487 | +124.72 | 0.00e+00 |
| USD | `move_occur` | xgboost | 21 | 0.6872 | +0.2232 | +56.27 | 0.00e+00 |
| USD | `move_occur` | lightgbm | 21 | 0.6831 | +0.2183 | +89.20 | 0.00e+00 |
| USD | `move_occur` | xgboost | 34 | 0.6710 | +0.1920 | +67.19 | 0.00e+00 |
| USD | `move_occur` | lightgbm | 34 | 0.6640 | +0.1841 | +39.29 | 0.00e+00 |
| USD | `move_occur` | xgboost | 55 | 0.6493 | +0.1620 | +36.39 | 3.34e-290 |
| USD | `move_occur` | lightgbm | 55 | 0.6465 | +0.1589 | +41.30 | 0.00e+00 |
| CAD | `move_occur` | xgboost | 5 | 0.6033 | +0.1782 | +39.68 | 0.00e+00 |
| CAD | `move_occur` | xgboost | 21 | 0.6009 | +0.1505 | +27.02 | 4.89e-161 |
| CAD | `move_occur` | xgboost | 8 | 0.5970 | +0.1622 | +51.41 | 0.00e+00 |
| CAD | `move_occur` | xgboost | 13 | 0.5970 | +0.1539 | +55.41 | 0.00e+00 |
| CAD | `move_occur` | xgboost | 34 | 0.5937 | +0.1309 | +70.72 | 0.00e+00 |
| CAD | `move_occur` | xgboost | 55 | 0.5922 | +0.1219 | +23.66 | 5.18e-124 |
| CAD | `move_occur` | lightgbm | 5 | 0.5875 | +0.1508 | +39.25 | 0.00e+00 |
| CAD | `move_occur` | lightgbm | 21 | 0.5874 | +0.1304 | +34.02 | 5.14e-254 |
| CAD | `move_occur` | lightgbm | 8 | 0.5843 | +0.1410 | +32.18 | 1.94e-227 |
| CAD | `move_occur` | lightgbm | 34 | 0.5812 | +0.1134 | +36.31 | 5.68e-289 |
| CAD | `move_occur` | lightgbm | 13 | 0.5786 | +0.1248 | +45.90 | 0.00e+00 |
| CAD | `move_occur` | lightgbm | 55 | 0.5781 | +0.1031 | +18.17 | 4.35e-74 |

## Notes / deviations

- Pure-signal run: nothing is selected, no portfolio returns, no costs.
- Label definitions live in `src/swing_bsh/targets_ext.py` (one module docstring per family); the density probe `reports/t2_label_density_probe.md` is the smoke gate.
- Verdict PROVISIONAL until the admin ratifies it in chat.

