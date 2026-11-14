# WI-033 — swing-conditioned 3-class buy/sell/hold gate (ADOPT_LOOSE_4OF5)

- Generated (UTC): 2026-11-09T02:47:02Z
- Model: `XGBClassifier(objective="multi:softprob", tree_method="hist", n_jobs=2)`; per-fold OvR isotonic calibration, sigmoid fallback < 25 positives (CB-04)
- CV: 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, horizon))`; gate geometry k=1.5, h=21 (at-bottom rows)
- Baseline: frozen fib rules — WI-028 at-bottom entry + WI-030 exit `t15_s10_d39_close` (25 bps cost); placebo: CB-05 5-seed label permutation
- Model filter: take an at-bottom event when calibrated P(BUY) >= 0.5
- Gate: ADOPT iff model beats baseline in >= 4/5 folds AND pooled edge > 0 AND placebo z >= 2.0

| market | events | selected | folds won | pooled baseline | pooled model | pooled edge | placebo z | verdict |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| USD | 32,177 | 19,139 | 4/5 | 0.0121 | 0.0105 | -0.0015 | -19.71 | **REJECT** |
| CAD | 17,332 | 10,996 | 2/5 | 0.0158 | 0.0150 | -0.0007 | -8.01 | **REJECT** |

## USD — VERDICT: **REJECT**

- Events: 460,314 swing-event rows · 658 symbols · 44 features (41/111 kept)
- Embargo: 55 td · runtime 458.4s · final calibration: ['isotonic', 'isotonic', 'isotonic']
- Placebo: observed edge -0.0015, null mean 0.0000, sd 0.0001, z -19.71 (5 seeds)
- Pooled rank-IC (P(BUY) vs frozen return): -0.0396

| fold | events | selected | baseline mean | model mean | edge | IC | win |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| 0 | 4,992 | 4,738 | 0.0144 | 0.0154 | 0.0010 | -0.0623 | yes |
| 1 | 7,166 | 7,155 | -0.0016 | -0.0016 | 0.0000 | 0.0231 | yes |
| 2 | 6,917 | 22 | 0.0178 | -0.0025 | -0.0203 | -0.0301 | no |
| 3 | 6,789 | 1,083 | 0.0120 | 0.0153 | 0.0032 | -0.0016 | yes |
| 4 | 6,313 | 6,141 | 0.0195 | 0.0201 | 0.0006 | 0.0554 | yes |

Top TreeSHAP drivers (mean |contrib| share, 20k-row sample): `horizon` 0.421, `k` 0.195, `bb_width_21` 0.035, `atr_pct_3` 0.034, `range_compression_21_144` 0.032, `vwap_zscore_102` 0.025, `entropy_39` 0.022, `kama_er_63` 0.016

- No model pickle written (gate not ADOPT; DoD §3).

## CAD — VERDICT: **REJECT**

- Events: 252,420 swing-event rows · 381 symbols · 44 features (41/111 kept)
- Embargo: 55 td · runtime 262.1s · final calibration: ['isotonic', 'isotonic', 'isotonic']
- Placebo: observed edge -0.0007, null mean -0.0000, sd 0.0001, z -8.01 (5 seeds)
- Pooled rank-IC (P(BUY) vs frozen return): -0.0166

| fold | events | selected | baseline mean | model mean | edge | IC | win |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| 0 | 2,816 | 2,476 | 0.0207 | 0.0221 | 0.0014 | -0.0123 | yes |
| 1 | 3,685 | 3,627 | -0.0001 | 0.0002 | 0.0003 | 0.0397 | yes |
| 2 | 3,912 | 1,959 | 0.0140 | 0.0107 | -0.0033 | -0.0218 | no |
| 3 | 3,712 | 50 | 0.0166 | -0.0058 | -0.0224 | 0.0266 | no |
| 4 | 3,207 | 2,884 | 0.0309 | 0.0308 | -0.0001 | 0.0244 | no |

Top TreeSHAP drivers (mean |contrib| share, 20k-row sample): `horizon` 0.371, `k` 0.181, `atr_pct_3` 0.031, `vwap_zscore_102` 0.027, `amihud_3` 0.025, `frac_diff_close` 0.025, `bb_width_233` 0.022, `bb_width_55` 0.021

- No model pickle written (gate not ADOPT; DoD §3).

## Notes / deviations

- Gate geometry restricted to the primary at-bottom k=1.5/h=21 rows (one row per event); the model itself is trained on all states/k/horizons.
- The placebo is the CB-05 label-permutation form: 5 seeds retrain the full CV on permuted labels and re-select; z compares the observed selection edge to that null.

