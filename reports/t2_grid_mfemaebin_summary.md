# WI-048 — T2 grid `mfe_mae_bin` (D-025 tier 2)

- Generated (UTC): 2026-11-14T02:55:37Z
- Grid: `mfe_mae_bin` x 6 horizons (5, 8, 13, 21, 34, 55) x 2 learners x 2 markets; verdict = pooled OOF AUC + rank-IC (no tau grid, no EVAL)
- Learners: xgboost, lightgbm; variant pinned per market {'USD': 'exact', 'CAD': 'tol2'} (`*_full_k0.8`); rho prune 0.3
- CV: 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, h))`; placebo 5-seed label permutation on the AUC; BH-FDR alpha=0.05 over m=24 per family (design multiplicity)
- Features read at the detection bar only; float32, symbol-sequential, `n_jobs=2`; core cap 2.0 h
- Pickles (survivors only): `data/models/wi048/<MKT>_<learner>_<variant>_<family>_h<h>_f<fold>.pkl`; manifest `data/models/wi048/manifest.parquet` (WI-040 schema)
- Coverage: 24 cells scored, 0 truncated by the core budget (USD 529.4s, CAD 861.5s)

## 1. Cell ranking — cross-market consistent AUC / rank-IC

| rank | learner | h | AUC USD | AUC CAD | min AUC | min IC |
| ---: | :--- | ---: | ---: | ---: | ---: | ---: |
| 1 | xgboost | 55 | 0.5515 | 0.5572 | **0.5515** | +0.0890 |
| 2 | xgboost | 34 | 0.5465 | 0.5501 | **0.5465** | +0.0804 |
| 3 | xgboost | 21 | 0.5338 | 0.5383 | **0.5338** | +0.0582 |
| 4 | lightgbm | 55 | 0.5491 | 0.5274 | **0.5274** | +0.0475 |
| 5 | xgboost | 13 | 0.5243 | 0.5285 | **0.5243** | +0.0419 |
| 6 | xgboost | 8 | 0.5218 | 0.5340 | **0.5218** | +0.0374 |
| 7 | lightgbm | 34 | 0.5452 | 0.5210 | **0.5210** | +0.0364 |
| 8 | lightgbm | 21 | 0.5279 | 0.5194 | **0.5194** | +0.0336 |
| 9 | lightgbm | 13 | 0.5207 | 0.5189 | **0.5189** | +0.0327 |
| 10 | lightgbm | 8 | 0.5179 | 0.5263 | **0.5179** | +0.0307 |
| 11 | xgboost | 5 | 0.5109 | 0.5435 | **0.5109** | +0.0186 |
| 12 | lightgbm | 5 | 0.5090 | 0.5337 | **0.5090** | +0.0155 |

## 2. FDR survivors (BH alpha=0.05, m=24)

| market | family | learner | h | AUC | IC | z | p |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| CAD | `mfe_mae_bin` | xgboost | 55 | 0.5572 | +0.0991 | +33.34 | 5.05e-244 |
| USD | `mfe_mae_bin` | xgboost | 55 | 0.5515 | +0.0890 | +47.81 | 0.00e+00 |
| CAD | `mfe_mae_bin` | xgboost | 34 | 0.5501 | +0.0869 | +14.53 | 3.97e-48 |
| USD | `mfe_mae_bin` | lightgbm | 55 | 0.5491 | +0.0849 | +30.75 | 6.60e-208 |
| USD | `mfe_mae_bin` | xgboost | 34 | 0.5465 | +0.0804 | +24.98 | 4.90e-138 |
| USD | `mfe_mae_bin` | lightgbm | 34 | 0.5452 | +0.0779 | +18.64 | 7.36e-78 |
| CAD | `mfe_mae_bin` | xgboost | 5 | 0.5435 | +0.0754 | +17.75 | 9.26e-71 |
| CAD | `mfe_mae_bin` | xgboost | 21 | 0.5383 | +0.0664 | +10.90 | 5.54e-28 |
| CAD | `mfe_mae_bin` | xgboost | 8 | 0.5340 | +0.0590 | +12.75 | 1.47e-37 |
| USD | `mfe_mae_bin` | xgboost | 21 | 0.5338 | +0.0582 | +24.41 | 6.01e-132 |
| CAD | `mfe_mae_bin` | lightgbm | 5 | 0.5337 | +0.0584 | +12.94 | 1.35e-38 |
| CAD | `mfe_mae_bin` | xgboost | 13 | 0.5285 | +0.0495 | +10.37 | 1.79e-25 |
| USD | `mfe_mae_bin` | lightgbm | 21 | 0.5279 | +0.0481 | +9.34 | 4.71e-21 |
| CAD | `mfe_mae_bin` | lightgbm | 55 | 0.5274 | +0.0475 | +11.06 | 9.74e-29 |
| CAD | `mfe_mae_bin` | lightgbm | 8 | 0.5263 | +0.0457 | +5.81 | 3.15e-09 |
| USD | `mfe_mae_bin` | xgboost | 13 | 0.5243 | +0.0419 | +10.59 | 1.73e-26 |
| USD | `mfe_mae_bin` | xgboost | 8 | 0.5218 | +0.0374 | +7.89 | 1.50e-15 |
| CAD | `mfe_mae_bin` | lightgbm | 34 | 0.5210 | +0.0364 | +10.94 | 3.66e-28 |
| USD | `mfe_mae_bin` | lightgbm | 13 | 0.5207 | +0.0356 | +6.34 | 1.14e-10 |
| CAD | `mfe_mae_bin` | lightgbm | 21 | 0.5194 | +0.0336 | +6.33 | 1.25e-10 |
| CAD | `mfe_mae_bin` | lightgbm | 13 | 0.5189 | +0.0327 | +9.18 | 2.12e-20 |
| USD | `mfe_mae_bin` | lightgbm | 8 | 0.5179 | +0.0307 | +5.58 | 1.18e-08 |
| USD | `mfe_mae_bin` | xgboost | 5 | 0.5109 | +0.0186 | +12.14 | 3.24e-34 |
| USD | `mfe_mae_bin` | lightgbm | 5 | 0.5090 | +0.0155 | +6.20 | 2.89e-10 |

## Notes / deviations

- Pure-signal run: nothing is selected, no portfolio returns, no costs.
- Label definitions live in `src/swing_bsh/targets_ext.py` (one module docstring per family); the density probe `reports/t2_label_density_probe.md` is the smoke gate.
- Verdict PROVISIONAL until the admin ratifies it in chat.

