# D-002 / E5 — Unpredictability floor (USD)

- Generated (UTC): 2026-10-25T00:34:34Z
- Factors: mom_12_1, rev_1m, vol_20, amihud_20, log_dollar_vol_20 · ridge (continuous `fwd_atr_ret`) + logistic (binary = within-date median split of `fwd_atr_ret_15`) · 5-fold purged WF, 20d embargo

## Single-factor per-date Spearman rank-IC

| Factor | mean IC | t | % dates |
| :--- | ---: | ---: | ---: |
| `mom_12_1` | +0.0194 | +5.54 | 2869 |
| `rev_1m` | +0.0018 | +0.64 | 2869 |
| `vol_20` | -0.0145 | -4.72 | 2869 |
| `amihud_20` | -0.0072 | -3.37 | 2869 |
| `log_dollar_vol_20` | +0.0039 | +2.02 | 2869 |

- ridge `fwd_atr_ret_15` oof rank-IC: +0.0083 (t = +2.25, 1722 dates)
- ridge `fwd_atr_ret_20` oof rank-IC: +0.0075 (t = +2.05, 1722 dates)
- logit_median_split `fwd_atr_ret_15` oof rank-IC: -0.0055 (t = -1.67, 1722 dates)

## Verdict

Verdict: **FLOOR BREACHED** (max single-factor |t| = 5.54, ridge |t| = 2.25): classic factors DO predict the continuous forward ATR return on this universe. A trivial factor bet cannot be excluded as the source of E4's IC; any E3/H3 redesign must be tested against these factors as a baseline.
