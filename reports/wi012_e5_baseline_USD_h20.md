# WI-009 — E5 factor baseline (USD)

- Generated (UTC): 2026-10-26T06:36:20Z
- Panel: 1,342,206 rows · 532 symbols · 2869 dates (2015-04-28 00:00:00 → 2026-09-23 00:00:00)
- Metric: score-based within-date Spearman rank-IC vs `fwd_atr_ret_20` (never class-label IC). Compiled on CAD inside `src/factors/e5_baseline.py`.

## Single-factor within-date rank-IC

| Factor | mean IC | t | dates |
| :--- | ---: | ---: | ---: |
| `mom_12_1` | +0.0202 | +5.89 | 2869 |
| `rev_1m` | +0.0018 | +0.66 | 2869 |
| `vol_20` | -0.0166 | -5.36 | 2869 |
| `amihud_20` | -0.0075 | -3.46 | 2869 |
| `log_dollar_vol_20` | +0.0043 | +2.23 | 2869 |

## Multivariate (purged WF, 20d embargo)

| Model | mean IC | t | dates |
| :--- | ---: | ---: | ---: |
| `ridge` | +0.0082 | +2.80 | 1722 |
| `logit_median_split` | -0.0094 | -2.63 | 1722 |

Logit is scored with `predict_proba` (WI-002 one-line fix).
