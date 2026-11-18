# WI-048 — T2 grid `vol_expand` (D-025 tier 2)

- Generated (UTC): 2026-11-13T05:59:16Z
- Grid: `vol_expand` x 6 horizons (5, 8, 13, 21, 34, 55) x 2 learners x 2 markets; verdict = pooled OOF AUC + rank-IC (no tau grid, no EVAL)
- Learners: xgboost, lightgbm; variant pinned per market {'USD': 'exact', 'CAD': 'tol2'} (`*_full_k0.8`); rho prune 0.3
- CV: 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, h))`; placebo 5-seed label permutation on the AUC; BH-FDR alpha=0.05 over m=24 per family (design multiplicity)
- Features read at the detection bar only; float32, symbol-sequential, `n_jobs=2`; core cap 2.0 h
- Pickles (survivors only): `data/models/wi048/<MKT>_<learner>_<variant>_<family>_h<h>_f<fold>.pkl`; manifest `data/models/wi048/manifest.parquet` (WI-040 schema)
- Coverage: 24 cells scored, 0 truncated by the core budget (USD 333.3s, CAD 532.8s)

## 1. Cell ranking — cross-market consistent AUC / rank-IC

| rank | learner | h | AUC USD | AUC CAD | min AUC | min IC |
| ---: | :--- | ---: | ---: | ---: | ---: | ---: |
| 1 | lightgbm | 13 | 0.7068 | 0.7130 | **0.7068** | +0.3581 |
| 2 | lightgbm | 21 | 0.7022 | 0.7169 | **0.7022** | +0.3498 |
| 3 | lightgbm | 5 | 0.7000 | 0.6984 | **0.6984** | +0.3419 |
| 4 | xgboost | 13 | 0.6980 | 0.7120 | **0.6980** | +0.3429 |
| 5 | xgboost | 5 | 0.6954 | 0.6987 | **0.6954** | +0.3362 |
| 6 | xgboost | 21 | 0.6954 | 0.7144 | **0.6954** | +0.3380 |
| 7 | xgboost | 8 | 0.7013 | 0.6940 | **0.6940** | +0.3357 |
| 8 | lightgbm | 8 | 0.7073 | 0.6936 | **0.6936** | +0.3350 |
| 9 | xgboost | 34 | 0.6935 | 0.6892 | **0.6892** | +0.3273 |
| 10 | lightgbm | 34 | 0.6970 | 0.6890 | **0.6890** | +0.3270 |
| 11 | lightgbm | 55 | 0.6212 | 0.6120 | **0.6120** | +0.1936 |
| 12 | xgboost | 55 | 0.6025 | 0.6095 | **0.6025** | +0.1773 |

## 2. FDR survivors (BH alpha=0.05, m=24)

| market | family | learner | h | AUC | z | p |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| CAD | `vol_expand` | lightgbm | 21 | 0.7169 | +145.46 | 0.00e+00 |
| CAD | `vol_expand` | xgboost | 21 | 0.7144 | +76.31 | 0.00e+00 |
| CAD | `vol_expand` | lightgbm | 13 | 0.7130 | +81.12 | 0.00e+00 |
| CAD | `vol_expand` | xgboost | 13 | 0.7120 | +46.87 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 8 | 0.7073 | +93.89 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 13 | 0.7068 | +111.11 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 21 | 0.7022 | +121.06 | 0.00e+00 |
| USD | `vol_expand` | xgboost | 8 | 0.7013 | +127.71 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 5 | 0.7000 | +96.24 | 0.00e+00 |
| CAD | `vol_expand` | xgboost | 5 | 0.6987 | +77.29 | 0.00e+00 |
| CAD | `vol_expand` | lightgbm | 5 | 0.6984 | +129.32 | 0.00e+00 |
| USD | `vol_expand` | xgboost | 13 | 0.6980 | +96.54 | 0.00e+00 |
| USD | `vol_expand` | lightgbm | 34 | 0.6970 | +64.15 | 0.00e+00 |
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
| USD | `vol_expand` | xgboost | 55 | 0.6025 | +62.60 | 0.00e+00 |

## Notes / deviations

- Pure-signal run: nothing is selected, no portfolio returns, no costs.
- Label definitions live in `src/swing_bsh/targets_ext.py` (one module docstring per family); the density probe `reports/t2_label_density_probe.md` is the smoke gate.
- Verdict PROVISIONAL until the admin ratifies it in chat.

