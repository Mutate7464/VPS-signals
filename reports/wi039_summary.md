# WI-039 — regime-conditional audit of the `b_hold` signal (D-022 phase 2)

- Generated (UTC): 2026-11-09T20:38:14Z · inference/join only: WI-036 `exact_full_k0.8`|xgboost|`b_hold`|h in (5, 8, 13, 21) fold pickles (`wi036/`) re-score only their own OOF block (no training, no refit)
- WI-027 3x2 regime labels from `regime_daily_extended.csv` joined on (symbol, date) — market-daily, so the join resolves inside each row's own market; unmatched rows dropped, never NaN-filled
- Per market x regime x h: pooled OOF AUC + rank-IC, n, `b_hold` hold prevalence (cells with n < 100 reported, not scored); `n_jobs=2`, float32, symbol-sequential

## USD

- 224,205 joined OOF rows from 658 symbols (40 features, 117,025 panel rows); 1,401 dropped (no regime label); folds h5:5/5, h8:5/5, h13:5/5; not scored: h21 (no fold pickles)
- EVAL window: included (full-universe run)

| h | regime | n | AUC | rank-IC | hold rate |
| ---: | :--- | ---: | ---: | ---: | ---: |
| 5 | `chop_high` | 9,174 | 0.6270 | +0.0929 | 0.0467 |
| 8 | `chop_high` | 9,174 | 0.6996 | +0.0761 | 0.0122 |
| 13 | `chop_high` | 9,174 | 0.8805 | +0.0820 | 0.0038 |
| 5 | `chop_normal` | 928 | 0.6462 | +0.1033 | 0.0431 |
| 8 | `chop_normal` | 928 | 0.8218 | +0.0909 | 0.0065 |
| 13 | `chop_normal` | 928 | 0.8236 | +0.0657 | 0.0032 |
| 5 | `down_high` | 12,685 | 0.6505 | +0.1120 | 0.0484 |
| 8 | `down_high` | 12,685 | 0.7243 | +0.0849 | 0.0119 |
| 13 | `down_high` | 12,685 | 0.8162 | +0.0702 | 0.0039 |
| 5 | `down_normal` | 86 | n/a | n/a | 0.0000 |
| 8 | `down_normal` | 86 | n/a | n/a | 0.0000 |
| 13 | `down_normal` | 86 | n/a | n/a | 0.0000 |
| 5 | `up_high` | 33,534 | 0.5917 | +0.0678 | 0.0477 |
| 8 | `up_high` | 33,534 | 0.6182 | +0.0453 | 0.0124 |
| 13 | `up_high` | 33,534 | 0.8133 | +0.0569 | 0.0027 |
| 5 | `up_normal` | 18,328 | 0.6370 | +0.0922 | 0.0390 |
| 8 | `up_normal` | 18,328 | 0.7373 | +0.0795 | 0.0094 |
| 13 | `up_normal` | 18,328 | 0.9306 | +0.0878 | 0.0033 |

VERDICT USD: **robust across regimes** (no regime above the 0.6 excess-AUC share; share 0.36, AUC 0.6744, n=100,602; others below 0.52)
- runtime 8.6s core 9.3s


## CAD

- 164,524 joined OOF rows from 381 symbols (38 features, 64,166 panel rows); 660 dropped (no regime label); folds h5:5/5, h8:5/5, h13:5/5, h21:5/5; not scored: none
- EVAL window: included (full-universe run)

| h | regime | n | AUC | rank-IC | hold rate |
| ---: | :--- | ---: | ---: | ---: | ---: |
| 5 | `chop_high` | 4,760 | 0.6091 | +0.0905 | 0.0609 |
| 8 | `chop_high` | 4,760 | 0.6512 | +0.0734 | 0.0200 |
| 13 | `chop_high` | 4,760 | 0.8715 | +0.0932 | 0.0053 |
| 21 | `chop_high` | 4,760 | 0.8456 | +0.0426 | 0.0013 |
| 5 | `chop_normal` | 1,123 | 0.5420 | +0.0298 | 0.0419 |
| 8 | `chop_normal` | 1,123 | 0.7274 | +0.0885 | 0.0125 |
| 13 | `chop_normal` | 1,123 | 0.8706 | +0.0765 | 0.0036 |
| 21 | `chop_normal` | 1,123 | 0.9973 | +0.0514 | 0.0009 |
| 5 | `down_high` | 5,664 | 0.6226 | +0.0853 | 0.0420 |
| 8 | `down_high` | 5,664 | 0.6661 | +0.0628 | 0.0120 |
| 13 | `down_high` | 5,664 | 0.7245 | +0.0388 | 0.0025 |
| 21 | `down_high` | 5,664 | 0.9248 | +0.0521 | 0.0012 |
| 5 | `down_normal` | 54 | n/a | n/a | 0.0000 |
| 8 | `down_normal` | 54 | n/a | n/a | 0.0000 |
| 13 | `down_normal` | 54 | n/a | n/a | 0.0000 |
| 21 | `down_normal` | 54 | n/a | n/a | 0.0000 |
| 5 | `up_high` | 11,924 | 0.5711 | +0.0612 | 0.0659 |
| 8 | `up_high` | 11,924 | 0.6472 | +0.0720 | 0.0203 |
| 13 | `up_high` | 11,924 | 0.7420 | +0.0680 | 0.0066 |
| 21 | `up_high` | 11,924 | 0.7231 | +0.0469 | 0.0037 |
| 5 | `up_normal` | 17,606 | 0.5856 | +0.0629 | 0.0472 |
| 8 | `up_normal` | 17,606 | 0.6508 | +0.0585 | 0.0126 |
| 13 | `up_normal` | 17,606 | 0.7648 | +0.0459 | 0.0025 |
| 21 | `up_normal` | 17,606 | 0.9069 | +0.0425 | 0.0009 |

VERDICT CAD: **robust across regimes** (no regime above the 0.6 excess-AUC share; share 0.45, AUC 0.7270, n=70,424; others below 0.52)
- runtime 7.0s core 16.7s

## Notes / deviations

- Regime source: the WI names `regime_daily.csv` (r1/r1_s5/r2 only) — the WI-027 `regime` column is written by `scripts/fib_regime_labels.py` to `regime_daily_extended.csv` (= `regime_daily.csv` + atrp63/vol21/trend/vol_cat/regime), so that superset is read (override with `--regime-daily`).
- Inference/join only: WI-036 pickles score their own OOF blocks, nothing is fitted or tuned; concentration feeds WI-037 (a one-regime signal implies a regime-gated veto).
- `b_hold` prevalence is a few tenths of a percent (WI-036), so hold rate is small by construction and a per-cell AUC needs both classes in the cell.
