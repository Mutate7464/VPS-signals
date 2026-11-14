# WI-048 — T2 grid `mfe_mae_cont` (D-025 tier 2)

- Generated (UTC): 2026-11-14T05:29:19Z
- Grid: `mfe_mae_cont` x 6 horizons (5, 8, 13, 21, 34, 55) x 2 learners x 2 markets; verdict = pooled OOF AUC + rank-IC (no tau grid, no EVAL)
- Learners: xgboost, lightgbm; variant pinned per market {'USD': 'exact', 'CAD': 'tol2'} (`*_full_k0.8`); rho prune 0.3
- CV: 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, h))`; placebo 5-seed label permutation on the AUC; BH-FDR alpha=0.05 over m=24 per family (design multiplicity)
- Features read at the detection bar only; float32, symbol-sequential, `n_jobs=2`; core cap 2.0 h
- Pickles (survivors only): `data/models/wi048/<MKT>_<learner>_<variant>_<family>_h<h>_f<fold>.pkl`; manifest `data/models/wi048/manifest.parquet` (WI-040 schema)
- Coverage: 24 cells scored, 0 truncated by the core budget (USD 186.7s, CAD 314.7s)

## 1. Cell ranking — cross-market consistent AUC / rank-IC

| rank | learner | h | AUC USD | AUC CAD | min AUC | min IC |
| ---: | :--- | ---: | ---: | ---: | ---: | ---: |
| — | no cross-market cell pairs completed | | | | | |

## 2. FDR survivors (BH alpha=0.05, m=24)

| market | family | learner | h | AUC | IC | z | p |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
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

## Notes / deviations

- Pure-signal run: nothing is selected, no portfolio returns, no costs.
- Label definitions live in `src/swing_bsh/targets_ext.py` (one module docstring per family); the density probe `reports/t2_label_density_probe.md` is the smoke gate.
- Verdict PROVISIONAL until the admin ratifies it in chat.

