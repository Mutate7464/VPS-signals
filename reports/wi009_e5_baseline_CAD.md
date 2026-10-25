# WI-009 — E5 factor baseline (CAD)

- Generated (UTC): 2026-10-25T00:33:53Z
- Panel: 715,193 rows · 313 symbols · 2866 dates (2015-04-29 00:00:00 → 2026-09-29 00:00:00)
- Metric: score-based within-date Spearman rank-IC vs `fwd_atr_ret_15` (never class-label IC). Compiled on CAD inside `src/factors/e5_baseline.py`.

## Single-factor within-date rank-IC

| Factor | mean IC | t | dates |
| :--- | ---: | ---: | ---: |
| `mom_12_1` | +0.0243 | +6.47 | 2866 |
| `rev_1m` | -0.0094 | -3.13 | 2866 |
| `vol_20` | -0.0454 | -11.18 | 2866 |
| `amihud_20` | -0.0143 | -5.52 | 2866 |
| `log_dollar_vol_20` | +0.0029 | +1.35 | 2866 |

## Multivariate (purged WF, 20d embargo)

| Model | mean IC | t | dates |
| :--- | ---: | ---: | ---: |
| `ridge` | -0.0046 | -1.26 | 1720 |
| `logit_median_split` | +0.0226 | +4.44 | 1720 |

Logit is scored with `predict_proba` (WI-002 one-line fix).
