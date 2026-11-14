# WI-048 — T2 grid `xsec_vol_rank_cont` (D-025 tier 2)

- Generated (UTC): 2026-11-14T05:26:15Z
- Grid: `xsec_vol_rank_cont` x 6 horizons (5, 8, 13, 21, 34, 55) x 2 learners x 2 markets; verdict = pooled OOF AUC + rank-IC (no tau grid, no EVAL)
- Learners: xgboost, lightgbm; variant pinned per market {'USD': 'exact', 'CAD': 'tol2'} (`*_full_k0.8`); rho prune 0.3
- CV: 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, h))`; placebo 5-seed label permutation on the AUC; BH-FDR alpha=0.05 over m=24 per family (design multiplicity)
- Features read at the detection bar only; float32, symbol-sequential, `n_jobs=2`; core cap 2.0 h
- Pickles (survivors only): `data/models/wi048/<MKT>_<learner>_<variant>_<family>_h<h>_f<fold>.pkl`; manifest `data/models/wi048/manifest.parquet` (WI-040 schema)
- Coverage: 24 cells scored, 0 truncated by the core budget (USD 342.4s, CAD 567.3s)

## 1. Cell ranking — cross-market consistent AUC / rank-IC

| rank | learner | h | AUC USD | AUC CAD | min AUC | min IC |
| ---: | :--- | ---: | ---: | ---: | ---: | ---: |
| — | no cross-market cell pairs completed | | | | | |

## 2. FDR survivors (BH alpha=0.05, m=24)

| market | family | learner | h | AUC | IC | z | p |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| CAD | `xsec_vol_rank_cont` | xgboost | 55 | n/a | +0.7135 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 34 | n/a | +0.7005 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 21 | n/a | +0.6862 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 13 | n/a | +0.6606 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | xgboost | 55 | n/a | +0.6475 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | xgboost | 34 | n/a | +0.6362 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 8 | n/a | +0.6282 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | xgboost | 21 | n/a | +0.6219 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | xgboost | 13 | n/a | +0.5970 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 34 | n/a | +0.5938 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 55 | n/a | +0.5932 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 21 | n/a | +0.5837 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 5 | n/a | +0.5797 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | lightgbm | 55 | n/a | +0.5702 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | lightgbm | 34 | n/a | +0.5668 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | lightgbm | 21 | n/a | +0.5617 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | xgboost | 8 | n/a | +0.5603 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 13 | n/a | +0.5571 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 8 | n/a | +0.5364 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | lightgbm | 13 | n/a | +0.5228 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | xgboost | 5 | n/a | +0.5095 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 5 | n/a | +0.4874 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | lightgbm | 8 | n/a | +0.4861 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | lightgbm | 5 | n/a | +0.4068 | n/a | 0.00e+00 |

## Notes / deviations

- Pure-signal run: nothing is selected, no portfolio returns, no costs.
- Label definitions live in `src/swing_bsh/targets_ext.py` (one module docstring per family); the density probe `reports/t2_label_density_probe.md` is the smoke gate.
- Verdict PROVISIONAL until the admin ratifies it in chat.

