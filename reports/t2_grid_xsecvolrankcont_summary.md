# WI-048 — T2 grid `xsec_vol_rank_cont` (D-025 tier 2)

> **QUARANTINED 2026-11-14 (PM):** `cell_cv` casts labels to int8 (`binary_grid.py:199`),
> which silently binarized this family's continuous rank labels (ranks <1.0 → 0, ==1.0 → 1).
> The 24/24 "survivors" and ICs below measure a top-of-date *indicator*, not the registered
> continuous rank target — do NOT cite as the cont-family verdict. Re-run blocked on a
> regression read-out path (regression objectives + `model.predict` OOF in `cell_cv`),
> to be scoped as a new WI. The bin family (`xsec_vol_rank_bin`) is unaffected (labels are
> 0/1 by construction).

- Generated (UTC): 2026-11-14T02:30:22Z
- Grid: `xsec_vol_rank_cont` x 6 horizons (5, 8, 13, 21, 34, 55) x 2 learners x 2 markets; verdict = pooled OOF AUC + rank-IC (no tau grid, no EVAL)
- Learners: xgboost, lightgbm; variant pinned per market {'USD': 'exact', 'CAD': 'tol2'} (`*_full_k0.8`); rho prune 0.3
- CV: 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, h))`; placebo 5-seed label permutation on the AUC; BH-FDR alpha=0.05 over m=24 per family (design multiplicity)
- Features read at the detection bar only; float32, symbol-sequential, `n_jobs=2`; core cap 2.0 h
- Pickles (survivors only): `data/models/wi048/<MKT>_<learner>_<variant>_<family>_h<h>_f<fold>.pkl`; manifest `data/models/wi048/manifest.parquet` (WI-040 schema)
- Coverage: 24 cells scored, 0 truncated by the core budget (USD 354.9s, CAD 587.1s)

## 1. Cell ranking — cross-market consistent AUC / rank-IC

| rank | learner | h | AUC USD | AUC CAD | min AUC | min IC |
| ---: | :--- | ---: | ---: | ---: | ---: | ---: |
| — | no cross-market cell pairs completed | | | | | |

## 2. FDR survivors (BH alpha=0.05, m=24)

| market | family | learner | h | AUC | IC | z | p |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| CAD | `xsec_vol_rank_cont` | lightgbm | 55 | n/a | +0.6635 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 55 | n/a | +0.6573 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 34 | n/a | +0.6555 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 34 | n/a | +0.6488 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 21 | n/a | +0.6397 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 21 | n/a | +0.6336 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 13 | n/a | +0.6141 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 13 | n/a | +0.6104 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 8 | n/a | +0.5817 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 8 | n/a | +0.5777 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | xgboost | 34 | n/a | +0.5772 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | xgboost | 55 | n/a | +0.5652 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | lightgbm | 55 | n/a | +0.5616 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | xgboost | 21 | n/a | +0.5610 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | lightgbm | 34 | n/a | +0.5606 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | lightgbm | 21 | n/a | +0.5562 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | xgboost | 13 | n/a | +0.5401 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | xgboost | 5 | n/a | +0.5360 | n/a | 0.00e+00 |
| CAD | `xsec_vol_rank_cont` | lightgbm | 5 | n/a | +0.5330 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | lightgbm | 13 | n/a | +0.5208 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | xgboost | 8 | n/a | +0.5085 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | lightgbm | 8 | n/a | +0.4887 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | xgboost | 5 | n/a | +0.4657 | n/a | 0.00e+00 |
| USD | `xsec_vol_rank_cont` | lightgbm | 5 | n/a | +0.4428 | n/a | 0.00e+00 |

## Notes / deviations

- Pure-signal run: nothing is selected, no portfolio returns, no costs.
- Label definitions live in `src/swing_bsh/targets_ext.py` (one module docstring per family); the density probe `reports/t2_label_density_probe.md` is the smoke gate.
- Verdict PROVISIONAL until the admin ratifies it in chat.

