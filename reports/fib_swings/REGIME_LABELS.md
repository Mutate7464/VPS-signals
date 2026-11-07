# REGIME LABELS (WI-027): trend {up,down,chop} x vol {normal,high}

Bottom screen per regime on CALIB (date < 2022-05-02; EVAL not computed); pooled (ALL) is the headline, per-market rows are descriptive.

| regime | market | n_events | screened rate | edge_pp | n_folds_pos |
|---|---|---|---|---|---|
| up_normal | CAD | 5316 | 0.0480 | 2.7249 | 2 |
| up_high | CAD | 1932 | 0.0378 | 11.6693 | 3 |
| down_normal | CAD | 2841 | 0.0634 | -3.3535 | 3 |
| down_high | CAD | 4573 | 0.1052 | 20.2986 | 4 |
| chop_normal | CAD | 3020 | 0.0566 | 8.9857 | 4 |
| chop_high | CAD | 1822 | 0.0681 | 14.4422 | 3 |
| up_normal | USD | 4675 | 0.0468 | -2.1149 | 2 |
| up_high | USD | 4384 | 0.0440 | 22.7485 | 5 |
| down_normal | USD | 8461 | 0.0479 | -0.3053 | 3 |
| down_high | USD | 8957 | 0.0915 | 22.0525 | 4 |
| chop_normal | USD | 4276 | 0.0496 | -1.0100 | 3 |
| chop_high | USD | 3231 | 0.0616 | 7.8527 | 2 |
| up_normal | ALL | 9991 | 0.0474 | 1.4237 | 1 |
| up_high | ALL | 6316 | 0.0421 | 19.2213 | 4 |
| down_normal | ALL | 11302 | 0.0518 | -1.5505 | 3 |
| down_high | ALL | 13530 | 0.0962 | 21.4324 | 4 |
| chop_normal | ALL | 7296 | 0.0525 | 3.8942 | 5 |
| chop_high | ALL | 5053 | 0.0639 | 10.4863 | 2 |

## fold5 callout (the fatal fold from the overnight chain; expected date range 2020-01 -> 2022-04)
- fold5 (5th contiguous equal-count block of pooled CALIB screened resolved bottoms): 2020-01-29 -> 2022-04-29
- fold5 regime(s): chop_high (n=91), chop_normal (n=1), down_high (n=440), up_high (n=77), up_normal (n=57)
- chop_high fold-stability (pooled): n_folds_pos=2 -> FAILS
- chop_normal fold-stability (pooled): n_folds_pos=5 -> holds
- down_high fold-stability (pooled): n_folds_pos=4 -> FAILS
- up_high fold-stability (pooled): n_folds_pos=4 -> FAILS
- up_normal fold-stability (pooled): n_folds_pos=1 -> FAILS
- fold-stable rows (n_folds_pos==5): up_high/USD; chop_normal/ALL
VERDICT: PASS
