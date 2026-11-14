# WI-038 — long-horizon gap fill (h >= 34 cells truncated in WI-036)

- Generated (UTC): 2026-11-10T01:44:56Z
- Grid: 8 families x 5 horizons (34, 55, 89, 144, 233) x 3 binaries x 4 learners x 2 markets; WI-036 machinery imported unchanged (`HORIZONS` overridden in place, nothing else)
- CV: 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, h))`; placebo 5-seed label permutation on the AUC; BH-FDR alpha=0.05 over THIS grid only (m=960, not pooled with WI-036); core cap 2.0 h; `n_jobs=2`, float32, symbol-sequential
- Coverage: 552 cells scored, 408 truncated by the core budget (USD 2232.9s, CAD 4464.1s); 44 cells carry a 5-seed permutation p-value
- Pickles: `data/models/wi038/<MKT>_<learner>_<variant>_<binary>_h<h>_f<fold>.pkl`

## 1. Target ranking — cross-market consistent AUC / rank-IC

| rank | variant | best cell (learner/binary/h) | AUC USD | AUC CAD | min AUC | min IC | median min AUC | cells |
| ---: | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `tol2_full_k0.8` | mlp_torch/b_hold/h34 | 0.6962 | 0.8399 | **0.6962** | +0.0417 | 0.5282 | 24 |
| 2 | `tol2_full_k1.0` | mlp_torch/b_hold/h55 | 0.6546 | 0.8478 | **0.6546** | +0.0351 | 0.5287 | 24 |
| 3 | `exact_full_k0.8` | logistic_l2/b_hold/h34 | 0.7485 | 0.6302 | **0.6302** | +0.0191 | 0.5136 | 32 |
| 4 | `exact_full_k1.0` | hist_gbm/b_hold/h34 | 0.6702 | 0.6064 | **0.6064** | +0.0182 | 0.5122 | 36 |
| 5 | `tol2_mid60_k1.0` | xgboost/b_hold/h34 | 0.5243 | 0.5260 | **0.5243** | +0.0419 | 0.4995 | 24 |
| 6 | `exact_mid60_k0.8` | xgboost/b_hold/h34 | 0.5240 | 0.5254 | **0.5240** | +0.0404 | 0.4987 | 24 |
| 7 | `exact_mid60_k1.0` | xgboost/b_hold/h34 | 0.5216 | 0.5298 | **0.5216** | +0.0372 | 0.4991 | 24 |
| 8 | `tol2_mid60_k0.8` | logistic_l2/b_hold/h34 | 0.5206 | 0.5179 | **0.5179** | +0.0303 | 0.5027 | 24 |

Verdict: winning family `tol2_full_k0.8` (best cell mlp_torch|tol2_full_k0.8|b_hold|h34, min AUC 0.6962); expected the b_hold family again, weaker at long horizons — **consistent**.

## 2. FDR survivors (BH alpha=0.05, m over this grid)

| market | variant | learner | binary | h | AUC | z | p |
| :--- | :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| USD | `exact_full_k1.0` | logistic_l2 | b_hold | 34 | 0.6562 | +16.07 | 2.07e-58 |
| USD | `exact_full_k1.0` | hist_gbm | b_hold | 34 | 0.6702 | +7.05 | 9.07e-13 |
| USD | `exact_full_k0.8` | logistic_l2 | b_hold | 34 | 0.7485 | +8.31 | 4.97e-17 |
| USD | `exact_full_k0.8` | hist_gbm | b_hold | 34 | 0.7476 | +12.68 | 3.84e-37 |
| USD | `tol2_full_k0.8` | mlp_torch | b_hold | 34 | 0.6962 | +7.28 | 1.63e-13 |
| USD | `exact_full_k1.0` | hist_gbm | b_hold | 55 | 0.6642 | +13.42 | 2.37e-41 |
| USD | `exact_full_k0.8` | logistic_l2 | b_hold | 55 | 0.6422 | +6.38 | 9.00e-11 |
| USD | `exact_full_k0.8` | hist_gbm | b_hold | 55 | 0.7082 | +9.59 | 4.33e-22 |
| USD | `tol2_full_k1.0` | mlp_torch | b_hold | 55 | 0.6546 | +10.10 | 2.74e-24 |
| USD | `tol2_full_k0.8` | mlp_torch | b_hold | 55 | 0.6513 | +4.58 | 2.34e-06 |
| USD | `exact_full_k1.0` | logistic_l2 | b_hold | 89 | 0.6364 | +14.51 | 5.52e-48 |
| USD | `exact_full_k1.0` | hist_gbm | b_hold | 89 | 0.7222 | +32.97 | 1.17e-238 |
| CAD | `exact_full_k1.0` | xgboost | b_hold | 34 | 0.6415 | +20.02 | 1.81e-89 |
| CAD | `exact_full_k0.8` | mlp_torch | b_hold | 34 | 0.8120 | +8.26 | 7.57e-17 |
| CAD | `tol2_full_k0.8` | mlp_torch | b_hold | 34 | 0.8399 | +15.35 | 1.87e-53 |
| CAD | `exact_full_k1.0` | mlp_torch | b_hold | 55 | 0.7341 | +15.65 | 1.57e-55 |
| CAD | `tol2_full_k1.0` | mlp_torch | b_hold | 55 | 0.8478 | +15.68 | 1.10e-55 |
| CAD | `tol2_full_k0.8` | mlp_torch | b_hold | 55 | 0.6588 | +7.74 | 4.82e-15 |
| CAD | `exact_full_k1.0` | mlp_torch | b_hold | 89 | 0.6826 | +8.27 | 6.52e-17 |
| CAD | `tol2_full_k1.0` | mlp_torch | b_hold | 89 | 0.6843 | +9.09 | 4.99e-20 |

## 3. Per-fold event counts — data-starvation flags

Folds with fewer than 30 scored events are **FLAGGED** (starved); late folds starve by design at long horizons — counts are never pooled across folds.

| market | h | fold 0 | fold 1 | fold 2 | fold 3 | fold 4 | starved folds |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| CAD | 34 | 7089 | 7776 | 8472 | 8659 | 9300 | none |
| CAD | 55 | 7089 | 7776 | 8472 | 8659 | 9300 | none |
| CAD | 89 | 7089 | 7776 | 8472 | 8659 | 9300 | none |
| CAD | 144 | 7089 | 7776 | 8472 | 8659 | 9300 | none |
| USD | 34 | 13590 | 14774 | 15317 | 15305 | 16216 | none |
| USD | 55 | 13590 | 14774 | 15317 | 15305 | 16216 | none |
| USD | 89 | 13590 | 14774 | 15317 | 15305 | 16216 | none |

## 4. Budget / dropped horizons

- Horizons scored (priority order, ascending): 34, 55, 89, 144, 233
- Truncated by the 2.0 h core budget: 408 cells — horizons [89, 144, 233] (h=233 dropped first, then 144)

## Notes / deviations

- Thin driver: `run_market`/`run_placebo`/`rank_variants`/`bh_fdr` imported and called unchanged; only `ext.HORIZONS` is overridden (restored on exit).
- Pure-signal run: pooled OOF AUC + rank-IC, no tau grid, no entry rule, no returns.
- Targets: `exact` = detected bar; `tol2` = extreme within +/-2 bars; `full` = [t+1, t+h]; `mid60` = [t+ceil(.2h), t+floor(.8h)]; features always read at the detection bar.

