# WI-044 — L1 learner extension on the winning `b_hold` cells (D-024 §2)

- Generated (UTC): 2026-11-10T05:32:32Z
- Grid: exact_full_k0.8, tol2_full_k0.8 x h in (13, 21, 34, 55) x `b_hold` x 6 learners (lightgbm, catboost, random_forest, extra_trees, xgboost_isotonic, elasticnet_logistic) x 2 markets; WI-036 machinery imported unchanged (variant grid, binary set and learner hooks overridden in place, restored afterwards)
- CV: 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, h))`; placebo 5-seed permutation on the AUC; BH-FDR alpha=0.05 over THIS grid only (m=96); core cap 2.0 h; float32, symbol-sequential, `n_jobs=2` (LightGBM/CatBoost CPU limits re-imposed per fit)
- Coverage: 80 cells scored, 16 truncated by the core budget (USD 2251.0s, CAD 4244.0s); 6 cells carry a permutation p-value
- Pickles: `data/models/wi044/<MKT>_<learner>_<variant>_b_hold_h<h>_f<fold>.pkl`; Layer 1 only (D-023): no tau grid, no entry rule — P(hold) reliability is reported for the L2 tau-mass precheck and nothing else.

## 1. Target ranking — cross-market consistent AUC / rank-IC

| rank | variant | best cell (learner/binary/h) | AUC USD | AUC CAD | min AUC | min IC | median min AUC | cells |
| ---: | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `exact_full_k0.8` | random_forest/b_hold/h21 | 0.7985 | 0.7341 | **0.7341** | +0.0413 | 0.6796 | 18 |
| 2 | `tol2_full_k0.8` | xgboost_isotonic/b_hold/h13 | 0.7090 | 0.6447 | **0.6447** | +0.0407 | 0.5861 | 14 |

## 2. FDR survivors (BH alpha=0.05, m over this grid)

| market | variant | learner | binary | h | AUC | z | p |
| :--- | :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| USD | `exact_full_k0.8` | lightgbm | b_hold | 21 | 0.7965 | +10.86 | 9.41e-28 |
| USD | `exact_full_k0.8` | catboost | b_hold | 21 | 0.8130 | +12.65 | 5.27e-37 |
| USD | `exact_full_k0.8` | random_forest | b_hold | 21 | 0.7985 | +21.33 | 3.31e-101 |
| CAD | `exact_full_k0.8` | elasticnet_logistic | b_hold | 34 | 0.8958 | +10.41 | 1.06e-25 |
| CAD | `tol2_full_k0.8` | elasticnet_logistic | b_hold | 34 | 0.8892 | +26.86 | 3.14e-159 |
| CAD | `tol2_full_k0.8` | elasticnet_logistic | b_hold | 55 | 0.8148 | +13.34 | 7.04e-41 |

## 3. Per-learner OOF calibration reliability (Brier, ascending)

| learner | cells | events | prevalence | mean p̂ | max p̂ | Brier |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| elasticnet_logistic | 13 | 706378 | 0.0035 | 0.0024 | 1.0000 | 0.0029 |
| extra_trees | 13 | 706378 | 0.0035 | 0.0026 | 1.0000 | 0.0030 |
| random_forest | 13 | 706378 | 0.0035 | 0.0019 | 1.0000 | 0.0030 |
| catboost | 14 | 781580 | 0.0035 | 0.0017 | 1.0000 | 0.0030 |
| lightgbm | 14 | 781580 | 0.0035 | 0.0018 | 1.0000 | 0.0030 |
| xgboost_isotonic | 13 | 706378 | 0.0035 | 0.0020 | 1.0000 | 0.0032 |

## Notes / deviations

- Thin driver: `run_market`/`run_placebo`/`rank_variants`/`bh_fdr`/`_fmt` imported and called unchanged; only the variant grid, the binary set, the learner registry and the two learner hooks are overridden in place (restored on exit).
- `xgboost_isotonic` = the WI-036 winner learner under `CalibratedClassifierCV(method='isotonic', cv<= 3)`; the inner fold count is capped by the fold's minority class and falls back to the uncalibrated base when it cannot be split — the per-fold WI-035 calibrator always follows (nested calibration).
- `elasticnet_logistic` picks `l1_ratio` from (0.1, 0.5, 0.9) on the fold's calibration block by log-loss (saga) — the sparse cross-check on the WI-040 attribution.
- Truncated cells are reported as truncated, never dropped; placebo (FDR) runs on the largest |AUC-0.5| cells first.

