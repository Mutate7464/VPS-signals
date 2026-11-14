# WI-017 run 4 — target x feature alignment matrix (USD, full grid)

Generated (UTC): 2026-11-01T02:02:59Z · targets: 165 (+5 skipped degenerate) · features: 264 · symbols: 593

Method: WI-015 shape: 5 chronological folds, 20-session embargo, per-date cross-sectional Spearman IC (>=3 names), mean over held-out dates; 1000-draw circular block bootstrap (20-date blocks, seed 42); same-sign vs best E5 factor.

**Passes: 20004 of 43560 candidate cells clear the same-sign + noise-margin bar.**

## Best feature per target (top 30 by |IC|)

| Target | Best feature | Held-out IC | Margin | Baseline | Pass |
|---|---|---:|---:|---|---|
| rung_63 | atr_pct_34 | +0.7091 | 0.0079 | e5_vol_20 | PASS |
| rung_55 | atr_pct_34 | +0.7089 | 0.0080 | e5_vol_20 | PASS |
| rung_39 | atr_pct_39 | +0.7084 | 0.0083 | e5_vol_20 | PASS |
| rung_34 | atr_pct_34 | +0.7084 | 0.0081 | e5_vol_20 | PASS |
| rung_24 | atr_pct_34 | +0.7072 | 0.0079 | e5_vol_20 | PASS |
| rung_21 | atr_pct_34 | +0.7063 | 0.0080 | e5_vol_20 | PASS |
| rung_15 | atr_pct_34 | +0.7027 | 0.0077 | e5_vol_20 | PASS |
| rung_13 | atr_pct_34 | +0.7012 | 0.0077 | e5_vol_20 | PASS |
| rung_3 | atr_pct_21 | +0.6997 | 0.0066 | e5_vol_20 | PASS |
| rung_9 | atr_pct_34 | +0.6984 | 0.0076 | e5_vol_20 | PASS |
| rung_89 | atr_pct_34 | +0.6979 | 0.0079 | e5_vol_20 | PASS |
| rung_8 | atr_pct_24 | +0.6978 | 0.0077 | e5_vol_20 | PASS |
| rung_5 | atr_pct_24 | +0.6974 | 0.0073 | e5_vol_20 | PASS |
| rung_6 | atr_pct_24 | +0.6973 | 0.0075 | e5_vol_20 | PASS |
| rung_102 | atr_pct_34 | +0.6927 | 0.0076 | e5_vol_20 | PASS |
| rung_144 | yangzhang_144 | +0.6772 | 0.0090 | e5_vol_20 | PASS |
| rung_233 | yangzhang_144 | +0.6442 | 0.0111 | e5_vol_20 | PASS |
| stay5_5 | atr_pct_24 | -0.4813 | 0.0093 | e5_vol_20 | PASS |
| stay5_6 | atr_pct_24 | -0.4788 | 0.0094 | e5_vol_20 | PASS |
| stay5_8 | atr_pct_34 | -0.4648 | 0.0109 | e5_vol_20 | PASS |
| stay5_3 | atr_pct_21 | -0.4593 | 0.0095 | e5_vol_20 | PASS |
| stay5_9 | atr_pct_34 | -0.4548 | 0.0118 | e5_vol_20 | PASS |
| stay5_13 | atr_pct_34 | -0.4120 | 0.0134 | e5_vol_20 | PASS |
| days_to_up_144 | atr_pct_34 | -0.4086 | 0.0148 | e5_vol_20 | PASS |
| days_to_up_89 | atr_pct_34 | -0.4067 | 0.0154 | e5_vol_20 | PASS |
| days_to_up_102 | atr_pct_34 | -0.4066 | 0.0144 | e5_vol_20 | PASS |
| days_to_up_63 | atr_pct_39 | -0.4017 | 0.0156 | e5_vol_20 | PASS |
| days_to_up_233 | atr_pct_34 | -0.3997 | 0.0157 | e5_vol_20 | PASS |
| days_to_up_55 | atr_pct_34 | -0.3981 | 0.0151 | e5_vol_20 | PASS |
| stay5_15 | atr_pct_39 | -0.3898 | 0.0153 | e5_vol_20 | PASS |

## Standing-assumption checks

- WI-015 positive `bb_width_233`: best target `rung_55` IC +0.5673 (margin 0.0130), clears bar on 162/165 targets.
- WI-015 positive `range_width_233`: best target `rung_55` IC +0.6435 (margin 0.0100), clears bar on 162/165 targets.
- WI-015 positive `yangzhang_144`: best target `rung_63` IC +0.7053 (margin 0.0089), clears bar on 163/165 targets.
- WI-015 positive `atr_pct_233`: best target `rung_55` IC +0.6488 (margin 0.0127), clears bar on 163/165 targets.
- 'E5 factors are the signal' (WI-009 triple-confirmation): fib-grid features beat the best E5 |IC| on 5757 of 43560 scored target cells.
- WI-016 USD NOT_CLEAR (barrier-resolved): this matrix is descriptive; total PASS cells above quantify what clears the WI-015-style bar on USD.
