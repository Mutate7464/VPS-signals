# WI-018 G1 condition atlas — `first_touch_34` (USD)

Generated 2026-11-01T04:04:05Z. Inputs: 593 symbols, 2319911 rows, 2006-10-26..2026-10-28 (5032 dates).
Descriptive only — no pass/fail and no multiple-testing budget is spent in G1.

## Unconditional split (reference)

| class | pooled | date-mean | 95% CI |
|---|---|---|---|
| up | 0.3756 | 0.3730 | [0.3562, 0.3899] |
| dn | 0.2971 | 0.2966 | [0.2757, 0.3175] |
| neither | 0.3273 | 0.3303 | [0.3117, 0.3490] |

States are within-date USD cross-sectional quantiles (ties go to the upper bin); bootstrap: circular 20-date blocks, 1000 draws, seed 42 (block_bootstrap_margin).

## Top conditions by |lift| — quintile (up to 12)

| feature | bin | n | n_dates | symbols | up rate | up lift | dn rate | dn lift | neither |
|---|---|---|---|---|---|---|---|---|---|
| atr_pct_34 | 1 | 462174 | 4965 | 406 | 0.2135 | -0.1596 | 0.1662 | -0.1304 | 0.6204 |
| yangzhang_233 | 1 | 438319 | 4765 | 319 | 0.2179 | -0.1552 | 0.1643 | -0.1323 | 0.6179 |
| yangzhang_144 | 1 | 448889 | 4854 | 355 | 0.2172 | -0.1559 | 0.1652 | -0.1314 | 0.6176 |
| atr_pct_34 | 5 | 458096 | 4965 | 517 | 0.5056 | +0.1326 | 0.4281 | +0.1315 | 0.0663 |
| yangzhang_144 | 5 | 444962 | 4854 | 475 | 0.5030 | +0.1300 | 0.4215 | +0.1249 | 0.0754 |
| range_width_233 | 1 | 438436 | 4766 | 484 | 0.2358 | -0.1373 | 0.1813 | -0.1153 | 0.5830 |
| yangzhang_233 | 5 | 434489 | 4765 | 435 | 0.4997 | +0.1267 | 0.4224 | +0.1258 | 0.0779 |
| range_width_233 | 5 | 434604 | 4766 | 526 | 0.4979 | +0.1248 | 0.4196 | +0.1229 | 0.0826 |
| range_width_144 | 5 | 445090 | 4855 | 545 | 0.4990 | +0.1260 | 0.4178 | +0.1212 | 0.0832 |
| range_width_144 | 1 | 449003 | 4855 | 505 | 0.2446 | -0.1285 | 0.1828 | -0.1138 | 0.5726 |
| yangzhang_3 | 1 | 465739 | 4995 | 554 | 0.2442 | -0.1288 | 0.1857 | -0.1109 | 0.5701 |
| bb_width_233 | 5 | 434614 | 4766 | 517 | 0.4887 | +0.1157 | 0.4083 | +0.1117 | 0.1030 |

## Top conditions by |lift| — tercile (up to 12)

| feature | bin | n | n_dates | symbols | up rate | up lift | dn rate | dn lift | neither |
|---|---|---|---|---|---|---|---|---|---|
| donchian_break_55 | 2 | 2024 | 12 | 482 | 0.2351 | -0.1379 | 0.4091 | +0.1124 | 0.3558 |
| atr_pct_34 | 1 | 768491 | 4965 | 490 | 0.2493 | -0.1237 | 0.1892 | -0.1074 | 0.5615 |
| yangzhang_233 | 1 | 728878 | 4765 | 411 | 0.2507 | -0.1223 | 0.1897 | -0.1069 | 0.5596 |
| yangzhang_144 | 1 | 746476 | 4854 | 430 | 0.2518 | -0.1213 | 0.1905 | -0.1061 | 0.5577 |
| atr_pct_34 | 3 | 765097 | 4965 | 558 | 0.4873 | +0.1142 | 0.4061 | +0.1094 | 0.1066 |
| yangzhang_144 | 3 | 743187 | 4854 | 537 | 0.4839 | +0.1109 | 0.4041 | +0.1075 | 0.1120 |
| yangzhang_233 | 3 | 725720 | 4765 | 506 | 0.4812 | +0.1082 | 0.4034 | +0.1068 | 0.1154 |
| range_width_144 | 3 | 743384 | 4855 | 584 | 0.4773 | +0.1042 | 0.3964 | +0.0998 | 0.1263 |
| range_width_233 | 3 | 725910 | 4766 | 572 | 0.4770 | +0.1040 | 0.3963 | +0.0997 | 0.1267 |
| range_width_233 | 1 | 729076 | 4766 | 524 | 0.2636 | -0.1094 | 0.2025 | -0.0941 | 0.5339 |
| range_width_144 | 1 | 746677 | 4855 | 541 | 0.2701 | -0.1030 | 0.2051 | -0.0915 | 0.5248 |
| yangzhang_3 | 1 | 774397 | 4995 | 568 | 0.2715 | -0.1015 | 0.2057 | -0.0910 | 0.5228 |

## Coverage

- cells: 704 total, 702 estimable, 2 unevaluable (0.003).
- features without any estimable cell: none.
- rows with a target value outside {+1, 0, -1}: 0 (excluded from every rate, never folded into 'neither').

## Flagged family representativeness

| family | kept column | kept \|IC\| | family best | best column | share | representative |
|---|---|---|---|---|---|---|
| atr_pct | atr_pct_34 | 0.0348 | 0.0357 | atr_pct_89 | 0.9726 | True |
| fib_dist | fib_dist_3 | 0.0124 | 0.0179 | fib_dist_21 | 0.6943 | False |
| range_pos | range_pos_5 | 0.0145 | 0.0180 | range_pos_102 | 0.8045 | False |

`representative=true` means the surviving column retains at least 90% of its family's best |IC| against this target, so its atlas states are not a prune artifact; `false` means treat that family's conditions as single-window evidence.

## Self-check

```
  OK   all_features_present: 88 reported vs 88 expected
  OK   cells_represented_or_marked: 704 cells present
  OK   estimable_rates_sum_to_one: tolerance 1e-06
  OK   cis_present: all estimable cells carry finite 95% bounds
  OK   flagged_families_checked: atr_pct, fib_dist, range_pos
  OK   unconditional_split_present: rates={'up': 0.373, 'dn': 0.2966, 'neither': 0.3303}
```

No executable rules, no shortlist, no trading integration — G1 is a description.
