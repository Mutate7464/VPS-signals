# WI-048 — T2 grid `xsec_vol_rank_bin` (D-025 tier 2)

- Generated (UTC): 2026-11-14T02:22:45Z
- Grid: `xsec_vol_rank_bin` x 6 horizons (5, 8, 13, 21, 34, 55) x 2 learners x 2 markets; verdict = pooled OOF AUC + rank-IC (no tau grid, no EVAL)
- Learners: xgboost, lightgbm; variant pinned per market {'USD': 'exact', 'CAD': 'tol2'} (`*_full_k0.8`); rho prune 0.3
- CV: 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, h))`; placebo 5-seed label permutation on the AUC; BH-FDR alpha=0.05 over m=24 per family (design multiplicity)
- Features read at the detection bar only; float32, symbol-sequential, `n_jobs=2`; core cap 2.0 h
- Pickles (survivors only): `data/models/wi048/<MKT>_<learner>_<variant>_<family>_h<h>_f<fold>.pkl`; manifest `data/models/wi048/manifest.parquet` (WI-040 schema)
- Coverage: 24 cells scored, 0 truncated by the core budget (USD 698.8s, CAD 1089.4s)

## 1. Cell ranking — cross-market consistent AUC / rank-IC

| rank | learner | h | AUC USD | AUC CAD | min AUC | min IC |
| ---: | :--- | ---: | ---: | ---: | ---: | ---: |
| 1 | lightgbm | 55 | 0.8226 | 0.8461 | **0.8226** | +0.5250 |
| 2 | lightgbm | 34 | 0.8216 | 0.8448 | **0.8216** | +0.5250 |
| 3 | xgboost | 55 | 0.8181 | 0.8424 | **0.8181** | +0.5176 |
| 4 | xgboost | 34 | 0.8162 | 0.8404 | **0.8162** | +0.5162 |
| 5 | lightgbm | 21 | 0.8108 | 0.8390 | **0.8108** | +0.5083 |
| 6 | xgboost | 21 | 0.8056 | 0.8351 | **0.8056** | +0.4999 |
| 7 | lightgbm | 13 | 0.8009 | 0.8290 | **0.8009** | +0.4928 |
| 8 | xgboost | 13 | 0.7968 | 0.8257 | **0.7968** | +0.4861 |
| 9 | lightgbm | 8 | 0.7803 | 0.8142 | **0.7803** | +0.4596 |
| 10 | xgboost | 8 | 0.7784 | 0.8118 | **0.7784** | +0.4564 |
| 11 | lightgbm | 5 | 0.7608 | 0.7887 | **0.7608** | +0.4279 |
| 12 | xgboost | 5 | 0.7595 | 0.7879 | **0.7595** | +0.4257 |

## 2. FDR survivors (BH alpha=0.05, m=24)

| market | family | learner | h | AUC | z | p |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| CAD | `xsec_vol_rank_bin` | lightgbm | 55 | 0.8461 | +114.79 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | lightgbm | 34 | 0.8448 | +106.08 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | xgboost | 55 | 0.8424 | +131.37 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | xgboost | 34 | 0.8404 | +145.61 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | lightgbm | 21 | 0.8390 | +72.03 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | xgboost | 21 | 0.8351 | +88.86 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | lightgbm | 13 | 0.8290 | +134.25 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | xgboost | 13 | 0.8257 | +99.68 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | lightgbm | 55 | 0.8226 | +226.05 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | lightgbm | 34 | 0.8216 | +189.27 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | xgboost | 55 | 0.8181 | +186.81 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | xgboost | 34 | 0.8162 | +338.41 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | lightgbm | 8 | 0.8142 | +182.80 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | xgboost | 8 | 0.8118 | +118.66 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | lightgbm | 21 | 0.8108 | +124.90 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | xgboost | 21 | 0.8056 | +102.72 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | lightgbm | 13 | 0.8009 | +142.53 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | xgboost | 13 | 0.7968 | +136.75 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | lightgbm | 5 | 0.7887 | +125.67 | 0.00e+00 |
| CAD | `xsec_vol_rank_bin` | xgboost | 5 | 0.7879 | +76.91 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | lightgbm | 8 | 0.7803 | +126.63 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | xgboost | 8 | 0.7784 | +123.42 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | lightgbm | 5 | 0.7608 | +332.69 | 0.00e+00 |
| USD | `xsec_vol_rank_bin` | xgboost | 5 | 0.7595 | +222.51 | 0.00e+00 |

## Notes / deviations

- Pure-signal run: nothing is selected, no portfolio returns, no costs.
- Label definitions live in `src/swing_bsh/targets_ext.py` (one module docstring per family); the density probe `reports/t2_label_density_probe.md` is the smoke gate.
- Verdict PROVISIONAL until the admin ratifies it in chat.

