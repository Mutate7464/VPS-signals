# WI-015 — per-target alignment matrix (USD)

- Generated (UTC): 2026-10-28T04:26:56Z
- Method: 5 chronological held-out folds, 20-session embargo; per-date cross-sectional Spearman IC, mean over held-out dates only.
- Skill bar: sign must match the best E5 factor for that target/horizon **and** |IC| must exceed a 1000-draw circular block-bootstrap noise margin (20-date blocks, seed 42).
- Held-out date blocks: 2014-10-14→2017-03-03, 2017-03-06→2019-07-25, 2019-07-26→2021-12-10, 2021-12-13→2024-05-06, 2024-05-07→2026-09-30
- Candidates: 150 family×window features; E5 five-factor baseline scored the same way.

## Best family×window per target × horizon

| Target | Best family | Window | Held-out IC | Noise margin | Baseline factor | Baseline sign | Pass |
| :--- | :--- | ---: | ---: | ---: | :--- | ---: | :--- |
| T1@15 | `yangzhang` | 144 | +0.2001 | 0.0170 | `e5_vol_20` | + | PASS |
| T1@20 | `yangzhang` | 144 | +0.2907 | 0.0184 | `e5_vol_20` | + | PASS |
| T2@15 | `range_width_f` | 233 | +0.1684 | 0.0163 | `e5_vol_20` | + | PASS |
| T2@20 | `yangzhang` | 144 | +0.2497 | 0.0176 | `e5_vol_20` | + | PASS |
| T3@15 | `atr_pct` | 233 | -0.0575 | 0.0165 | `e5_vol_20` | − | PASS |
| T3@20 | `atr_pct` | 233 | -0.0622 | 0.0169 | `e5_vol_20` | − | PASS |
| T4@15 | `atr_pct` | 8 | -0.0620 | 0.0161 | `e5_vol_20` | − | PASS |
| T4@20 | `atr_pct` | 8 | -0.0690 | 0.0170 | `e5_vol_20` | − | PASS |

**Verdict:** 487 of 1200 candidate rows clear the same-sign + noise-margin bar (8 of 8 best-per-target cells). Prior expectation (WI-009 series): most cells land at noise; a null result is the honest product.

Full matrix: `alignment_USD.csv` · metadata: `alignment_USD.json`

<!-- WI-015 ADDENDUM SUMMARY (generated — do not edit above this line) -->

## Summary — best family and best timeframe (USD)

Best **family** × **window** per target × horizon (by |held-out IC|):

| Target | Best family | Best window | Held-out IC | Noise margin | Pass |
| :--- | :--- | ---: | ---: | ---: | :--- |
| T1@15 | `yangzhang` | 144 | +0.2001 | 0.0170 | PASS |
| T1@20 | `yangzhang` | 144 | +0.2907 | 0.0184 | PASS |
| T2@15 | `range_width_f` | 233 | +0.1684 | 0.0163 | PASS |
| T2@20 | `yangzhang` | 144 | +0.2497 | 0.0176 | PASS |
| T3@15 | `atr_pct` | 233 | -0.0575 | 0.0165 | PASS |
| T3@20 | `atr_pct` | 233 | -0.0622 | 0.0169 | PASS |
| T4@15 | `atr_pct` | 8 | -0.0620 | 0.0161 | PASS |
| T4@20 | `atr_pct` | 8 | -0.0690 | 0.0170 | PASS |

**Family vs timeframe.**

- Most frequent best family across the eight target×horizon cells: `atr_pct` (4/8 cells).
- Most frequent best window: 144, 233, 8.
- Window with the highest mean |held-out IC| over all family×target cells: **233** (0.0561).
- Pass rate: 487 of 1176 finite cells clear the same-sign + noise-margin bar.

Window means (ranked — the timeframe comparison at a glance):

| Window | Mean \|IC\| | Best \|IC\| in window |
| ---: | ---: | ---: |
| 233 | 0.0561 | 0.2889 |
| 144 | 0.0532 | 0.2907 |
| 89 | 0.0504 | 0.2856 |
| 55 | 0.0467 | 0.2796 |
| 34 | 0.0431 | 0.2783 |
| 8 | 0.0413 | 0.2657 |
| 21 | 0.0411 | 0.2760 |
| 13 | 0.0400 | 0.2716 |
| 5 | 0.0392 | 0.2589 |
| 3 | 0.0364 | 0.2499 |
