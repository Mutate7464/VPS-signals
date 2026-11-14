# WI-009 — E5 factor baseline (CAD)

- Generated (UTC): 2026-10-26T06:34:05Z
- Panel: 774,202 rows · 335 symbols · 2866 dates (2015-04-29 00:00:00 → 2026-09-29 00:00:00)
- Metric: score-based within-date Spearman rank-IC vs `fwd_atr_ret_20` (never class-label IC). Compiled on CAD inside `src/factors/e5_baseline.py`.

## Single-factor within-date rank-IC

| Factor | mean IC | t | dates |
| :--- | ---: | ---: | ---: |
| `mom_12_1` | +nan | +nan | 2866 |
| `rev_1m` | +nan | +nan | 2866 |
| `vol_20` | +nan | +nan | 2866 |
| `amihud_20` | +nan | +nan | 2866 |
| `log_dollar_vol_20` | +nan | +nan | 2866 |

## Multivariate (purged WF, 20d embargo)

| Model | mean IC | t | dates |
| :--- | ---: | ---: | ---: |
| `ridge` | +0.0102 | +4.62 | 1715 |
| `logit_median_split` | +0.0191 | +3.66 | 1715 |

Logit is scored with `predict_proba` (WI-002 one-line fix).
