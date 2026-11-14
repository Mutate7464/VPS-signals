# WI-037 — P(hold) veto filter on the frozen fib rules (D-022 phase 2)

- Generated (UTC): 2026-11-09T19:44:09Z
- Filter: fold-consistent OOF P(hold) from the WI-036 cell `exact_full_k0.8`|xgboost|`b_hold`|h13 (`wi036/`); an at-bottom frozen-rule entry is VETOED when P(hold) >= tau; tau grid (0.5, 0.6, 0.7, 0.8) tuned on CALIB entries (date < 2022-05-02) only, frozen before EVAL (date >= 2022-07-01)
- Baseline: frozen fib rules (WI-028 entry + WI-030 `t15_s10_d39_close`, 25 bps inside `r_frozen`); gate: ADOPT iff >= 4/5 fold wins AND pooled edge > 0 AND CB-05 placebo z >= 2.0 (5 permuted-label seeds, refit-only arms)

| market | entries | kept | vetoed | folds won | pooled baseline | pooled filtered | pooled edge | placebo z | tau | verdict |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| USD | 32,100 | 32,048 | 52 | 2/5 | 0.0119 | 0.0120 | 0.0001 | n/a | 0.50 | **REJECT** |

## USD — VERDICT: **REJECT**

- 32,100 at-bottom OOF entries with a priced frozen return (5/5 fold pickles, embargo 20 td, 117,025 panel rows); tau=0.50 on CALIB (10,268 entries): tau 0.50 kept 10,268/vetoed 0 edge +0.00000; tau 0.60 kept 10,268/vetoed 0 edge +0.00000; tau 0.70 kept 10,268/vetoed 0 edge +0.00000; tau 0.80 kept 10,268/vetoed 0 edge +0.00000
- Veto precision 0.9615 (true `b_hold` among the 52 vetoed) vs prevalence 0.0039
- EVAL window: n=20,616 kept=20,564 baseline 0.0159 edge 0.0001
- Placebo (CB-05): observed 0.0001 null 0.0000 sd 0.0000 z n/a (5/5 seeds); runtime 27.7s core 45.4s

| fold | entries | kept | vetoed | baseline mean | filtered mean | edge | IC | win |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| 0 | 5,109 | 5,109 | 0 | 0.0135 | 0.0135 | 0.0000 | -0.0243 | no |
| 1 | 7,469 | 7,469 | 0 | -0.0045 | -0.0045 | 0.0000 | -0.0113 | no |
| 2 | 6,857 | 6,823 | 34 | 0.0238 | 0.0239 | 0.0001 | -0.0039 | yes |
| 3 | 6,601 | 6,583 | 18 | 0.0106 | 0.0108 | 0.0002 | 0.0092 | yes |
| 4 | 6,064 | 6,064 | 0 | 0.0190 | 0.0190 | 0.0000 | -0.0029 | no |
| CAD | 17,256 | 17,248 | 8 | 1/5 | 0.0155 | 0.0156 | 0.0001 | n/a | 0.50 | **REJECT** |

## CAD — VERDICT: **REJECT**

- 17,256 at-bottom OOF entries with a priced frozen return (5/5 fold pickles, embargo 20 td, 64,166 panel rows); tau=0.50 on CALIB (5,315 entries): tau 0.50 kept 5,307/vetoed 8 edge +0.00026; tau 0.60 kept 5,307/vetoed 8 edge +0.00026; tau 0.70 kept 5,313/vetoed 2 edge -0.00007; tau 0.80 kept 5,313/vetoed 2 edge -0.00007
- Veto precision 0.6250 (true `b_hold` among the 8 vetoed) vs prevalence 0.0051
- EVAL window: n=11,237 kept=11,237 baseline 0.0194 edge 0.0000
- Placebo (CB-05): observed 0.0001 null 0.0000 sd 0.0000 z n/a (5/5 seeds); runtime 21.3s core 34.3s

| fold | entries | kept | vetoed | baseline mean | filtered mean | edge | IC | win |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| 0 | 2,820 | 2,818 | 2 | 0.0196 | 0.0195 | -0.0001 | 0.0345 | no |
| 1 | 3,840 | 3,834 | 6 | -0.0027 | -0.0023 | 0.0004 | -0.0229 | yes |
| 2 | 3,907 | 3,907 | 0 | 0.0180 | 0.0180 | 0.0000 | 0.0161 | no |
| 3 | 3,570 | 3,570 | 0 | 0.0159 | 0.0159 | 0.0000 | 0.0030 | no |
| 4 | 3,119 | 3,119 | 0 | 0.0306 | 0.0306 | 0.0000 | 0.0231 | no |

## Notes / deviations

- Class-prevalence caveat (WI-036): `b_hold` prevalence is a few tenths of a percent, so the isotonic-calibrated P(hold) rarely clears 0.5 and the tau grid is close to a no-op veto — the kept/vetoed counts and the veto precision are the informative numbers.
- Baseline = the WI-033 lineage `r_frozen` (WI-028 entry + WI-030 exit, 25 bps inside) from the cached canonical panel or `binary_labels.build_binary_panel` (k=1.5, h=21); inference only (pickles score their own OOF rows) and the CB-05 placebo arms are the only refits (permuted labels, tau frozen). Record-only: no shortlist, no deployment, no live trading.

