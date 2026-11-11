# WI-048 — T2 grid `up` (D-025 tier 2)

- Generated (UTC): 2026-11-11T05:15:18Z
- Grid: `up` x 6 horizons (5, 8, 13, 21, 34, 55) x 2 learners x 2 markets; verdict = pooled OOF AUC + rank-IC (no tau grid, no EVAL)
- Learners: xgboost, lightgbm; variant pinned per market {'USD': 'exact', 'CAD': 'tol2'} (`*_full_k0.8`); rho prune 0.3
- CV: 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, h))`; placebo 5-seed label permutation on the AUC; BH-FDR alpha=0.05 over m=24 per family (design multiplicity)
- Features read at the detection bar only; float32, symbol-sequential, `n_jobs=2`; core cap 2.0 h
- Pickles (survivors only): `data/models/wi048/<MKT>_<learner>_<variant>_<family>_h<h>_f<fold>.pkl`; manifest `data/models/wi048/manifest.parquet` (WI-040 schema)
- Coverage: 24 cells scored, 0 truncated by the core budget (USD 513.6s, CAD 788.9s)

## 1. Cell ranking — cross-market consistent AUC / rank-IC

| rank | learner | h | AUC USD | AUC CAD | min AUC | min IC |
| ---: | :--- | ---: | ---: | ---: | ---: | ---: |
| 1 | xgboost | 8 | 0.5038 | 0.5807 | **0.5038** | +0.0067 |
| 2 | lightgbm | 8 | 0.5034 | 0.5663 | **0.5034** | +0.0059 |
| 3 | lightgbm | 5 | 0.5029 | 0.5950 | **0.5029** | +0.0050 |
| 4 | lightgbm | 13 | 0.5014 | 0.5410 | **0.5014** | +0.0024 |
| 5 | xgboost | 5 | 0.4935 | 0.6057 | **0.4935** | -0.0114 |
| 6 | xgboost | 13 | 0.4920 | 0.5585 | **0.4920** | -0.0140 |
| 7 | lightgbm | 21 | 0.4856 | 0.5145 | **0.4856** | -0.0249 |
| 8 | lightgbm | 34 | 0.4855 | 0.4914 | **0.4855** | -0.0251 |
| 9 | xgboost | 34 | 0.4784 | 0.4986 | **0.4784** | -0.0374 |
| 10 | xgboost | 21 | 0.4774 | 0.5325 | **0.4774** | -0.0394 |
| 11 | lightgbm | 55 | 0.4762 | 0.4766 | **0.4762** | -0.0411 |
| 12 | xgboost | 55 | 0.4692 | 0.4713 | **0.4692** | -0.0534 |

## 2. FDR survivors (BH alpha=0.05, m=24)

| market | family | learner | h | AUC | z | p |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| CAD | `up` | xgboost | 5 | 0.6057 | +41.14 | 0.00e+00 |
| CAD | `up` | lightgbm | 5 | 0.5950 | +28.21 | 2.45e-175 |
| CAD | `up` | xgboost | 8 | 0.5807 | +64.20 | 0.00e+00 |
| CAD | `up` | lightgbm | 8 | 0.5663 | +43.42 | 0.00e+00 |
| CAD | `up` | xgboost | 13 | 0.5585 | +21.47 | 1.34e-102 |
| CAD | `up` | lightgbm | 13 | 0.5410 | +21.60 | 8.85e-104 |
| CAD | `up` | xgboost | 21 | 0.5325 | +10.34 | 2.40e-25 |
| CAD | `up` | lightgbm | 21 | 0.5145 | +9.54 | 7.10e-22 |
| USD | `up` | xgboost | 8 | 0.5038 | +4.97 | 3.40e-07 |
| USD | `up` | lightgbm | 8 | 0.5034 | +2.92 | 1.75e-03 |
| USD | `up` | lightgbm | 5 | 0.5029 | +2.97 | 1.51e-03 |

## Notes / deviations

- Pure-signal run: nothing is selected, no portfolio returns, no costs.
- Label definitions live in `src/swing_bsh/targets_ext.py` (one module docstring per family); the density probe `reports/t2_label_density_probe.md` is the smoke gate.
- Verdict PROVISIONAL until the admin ratifies it in chat.

