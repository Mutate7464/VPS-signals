# WI-009 — E5 factor baseline (USD)

- Generated (UTC): 2026-10-26T06:35:57Z
- Panel: 1,342,206 rows · 532 symbols · 2869 dates (2015-04-28 00:00:00 → 2026-09-23 00:00:00)
- Metric: score-based within-date Spearman rank-IC vs `fwd_atr_ret_15` (never class-label IC). Compiled on CAD inside `src/factors/e5_baseline.py`.

## Single-factor within-date rank-IC

| Factor | mean IC | t | dates |
| :--- | ---: | ---: | ---: |
| `mom_12_1` | +0.0209 | +6.00 | 2869 |
| `rev_1m` | +0.0025 | +0.90 | 2869 |
| `vol_20` | -0.0158 | -5.11 | 2869 |
| `amihud_20` | -0.0085 | -3.88 | 2869 |
| `log_dollar_vol_20` | +0.0052 | +2.65 | 2869 |

## Multivariate (purged WF, 20d embargo)

| Model | mean IC | t | dates |
| :--- | ---: | ---: | ---: |
| `ridge` | +0.0055 | +1.86 | 1722 |
| `logit_median_split` | -0.0054 | -1.53 | 1722 |

Logit is scored with `predict_proba` (WI-002 one-line fix).
