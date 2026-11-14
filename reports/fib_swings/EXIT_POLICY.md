# EXIT POLICY LEARNED (WI-030)

Oracle: argmax over 32 cells (53488 CALIB + 20407 EVAL).
Features: 16 event features + regime one-hot + horizon prior {'CAD': 20, 'USD': 39}.

## CALIB purged CV (5 blocks, 60d purge)

| fold | n_train | n_test | n_resolved | mean_ret | hit_rate |
|---|---|---|---|---|---|
| 0 | 42532 | 10698 | 10698 | 0.0032 | 0.368 |
| 1 | 42303 | 10697 | 10697 | 0.0074 | 0.456 |
| 2 | 41571 | 10698 | 10698 | 0.0072 | 0.400 |
| 3 | 41819 | 10697 | 10697 | 0.0063 | 0.423 |
| 4 | 41924 | 10698 | 10698 | 0.0064 | 0.404 |

fold-stable: 5/5 folds with mean_ret > 0.

pooled OOF mean_ret +0.0061 vs frozen baseline t15_s10_d39_close +0.0107

## EVAL (scored once with the final CALIB fit)

n=20407 | learned mean_ret +0.0080 vs frozen baseline t15_s10_d39_close +0.0214 (edge -0.0134)

VERDICT: FAIL
