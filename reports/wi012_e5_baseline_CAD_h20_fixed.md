# WI-009 — E5 factor baseline (CAD)

- Generated (UTC): 2026-10-26T06:35:35Z
- Panel: 772,527 rows · 335 symbols · 2861 dates (2015-04-29 00:00:00 → 2026-09-22 00:00:00)
- Metric: score-based within-date Spearman rank-IC vs `fwd_atr_ret_20` (never class-label IC). Compiled on CAD inside `src/factors/e5_baseline.py`.

## Single-factor within-date rank-IC

| Factor | mean IC | t | dates |
| :--- | ---: | ---: | ---: |
| `mom_12_1` | +0.0275 | +7.49 | 2861 |
| `rev_1m` | -0.0064 | -2.22 | 2861 |
| `vol_20` | -0.0462 | -11.37 | 2861 |
| `amihud_20` | -0.0117 | -4.54 | 2861 |
| `log_dollar_vol_20` | +0.0003 | +0.12 | 2861 |

## Multivariate (purged WF, 20d embargo)

| Model | mean IC | t | dates |
| :--- | ---: | ---: | ---: |
| `ridge` | +0.0102 | +4.58 | 1717 |
| `logit_median_split` | +0.0188 | +3.60 | 1717 |

Logit is scored with `predict_proba` (WI-002 one-line fix).
