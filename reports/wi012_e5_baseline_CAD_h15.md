# WI-009 — E5 factor baseline (CAD)

- Generated (UTC): 2026-10-26T06:35:17Z
- Panel: 772,527 rows · 335 symbols · 2861 dates (2015-04-29 00:00:00 → 2026-09-22 00:00:00)
- Metric: score-based within-date Spearman rank-IC vs `fwd_atr_ret_15` (never class-label IC). Compiled on CAD inside `src/factors/e5_baseline.py`.

## Single-factor within-date rank-IC

| Factor | mean IC | t | dates |
| :--- | ---: | ---: | ---: |
| `mom_12_1` | +0.0271 | +7.33 | 2861 |
| `rev_1m` | -0.0091 | -3.08 | 2861 |
| `vol_20` | -0.0432 | -10.74 | 2861 |
| `amihud_20` | -0.0140 | -5.41 | 2861 |
| `log_dollar_vol_20` | +0.0039 | +1.81 | 2861 |

## Multivariate (purged WF, 20d embargo)

| Model | mean IC | t | dates |
| :--- | ---: | ---: | ---: |
| `ridge` | +0.0064 | +2.71 | 1717 |
| `logit_median_split` | +0.0189 | +3.62 | 1717 |

Logit is scored with `predict_proba` (WI-002 one-line fix).
