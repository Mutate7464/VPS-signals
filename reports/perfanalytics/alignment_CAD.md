# WI-015 — per-target alignment matrix (CAD)

- Generated (UTC): 2026-10-28T04:21:17Z
- Method: 5 chronological held-out folds, 20-session embargo; per-date cross-sectional Spearman IC, mean over held-out dates only.
- Skill bar: sign must match the best E5 factor for that target/horizon **and** |IC| must exceed a 1000-draw circular block-bootstrap noise margin (20-date blocks, seed 42).
- Held-out date blocks: 2015-04-08→2017-07-21, 2017-07-24→2019-11-07, 2019-11-08→2022-02-24, 2022-02-25→2024-06-11, 2024-06-12→2026-09-29
- Candidates: 150 family×window features; E5 five-factor baseline scored the same way.

## Best family×window per target × horizon

| Target | Best family | Window | Held-out IC | Noise margin | Baseline factor | Baseline sign | Pass |
| :--- | :--- | ---: | ---: | ---: | :--- | ---: | :--- |
| T1@15 | `bb_width` | 233 | +0.2084 | 0.0192 | `e5_vol_20` | + | PASS |
| T1@20 | `range_width_f` | 233 | +0.2972 | 0.0223 | `e5_vol_20` | + | PASS |
| T2@15 | `bb_width` | 233 | +0.1882 | 0.0191 | `e5_vol_20` | + | PASS |
| T2@20 | `range_width_f` | 233 | +0.2686 | 0.0217 | `e5_vol_20` | + | PASS |
| T3@15 | `amihud` | 89 | -0.2081 | 0.0157 | `e5_amihud_20` | − | PASS |
| T3@20 | `amihud` | 89 | -0.2218 | 0.0162 | `e5_amihud_20` | − | PASS |
| T4@15 | `rsi` | 144 | +0.0510 | 0.0175 | `e5_rev_1m` | + | PASS |
| T4@20 | `yangzhang` | 21 | -0.0637 | 0.0191 | `e5_amihud_20` | − | PASS |

**Verdict:** 558 of 1200 candidate rows clear the same-sign + noise-margin bar (8 of 8 best-per-target cells). Prior expectation (WI-009 series): most cells land at noise; a null result is the honest product.

Full matrix: `alignment_CAD.csv` · metadata: `alignment_CAD.json`

<!-- WI-015 ADDENDUM SUMMARY (generated — do not edit above this line) -->

## Summary — best family and best timeframe (CAD)

Best **family** × **window** per target × horizon (by |held-out IC|):

| Target | Best family | Best window | Held-out IC | Noise margin | Pass |
| :--- | :--- | ---: | ---: | ---: | :--- |
| T1@15 | `bb_width` | 233 | +0.2084 | 0.0192 | PASS |
| T1@20 | `range_width_f` | 233 | +0.2972 | 0.0223 | PASS |
| T2@15 | `bb_width` | 233 | +0.1882 | 0.0191 | PASS |
| T2@20 | `range_width_f` | 233 | +0.2686 | 0.0217 | PASS |
| T3@15 | `amihud` | 89 | -0.2081 | 0.0157 | PASS |
| T3@20 | `amihud` | 89 | -0.2218 | 0.0162 | PASS |
| T4@15 | `rsi` | 144 | +0.0510 | 0.0175 | PASS |
| T4@20 | `yangzhang` | 21 | -0.0637 | 0.0191 | PASS |

**Family vs timeframe.**

- Most frequent best family across the eight target×horizon cells: `bb_width` (2/8 cells).
- Most frequent best window: 233, 89, 144.
- Window with the highest mean |held-out IC| over all family×target cells: **233** (0.0734).
- Pass rate: 558 of 1176 finite cells clear the same-sign + noise-margin bar.

Window means (ranked — the timeframe comparison at a glance):

| Window | Mean \|IC\| | Best \|IC\| in window |
| ---: | ---: | ---: |
| 233 | 0.0734 | 0.2972 |
| 144 | 0.0706 | 0.2938 |
| 89 | 0.0682 | 0.2918 |
| 55 | 0.0654 | 0.2878 |
| 34 | 0.0611 | 0.2874 |
| 21 | 0.0573 | 0.2846 |
| 8 | 0.0569 | 0.2756 |
| 13 | 0.0563 | 0.2805 |
| 5 | 0.0543 | 0.2696 |
| 3 | 0.0505 | 0.2607 |
