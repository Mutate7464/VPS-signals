# L2 vol-target entry-only sizing — WI-068 survivor (a), CAD

- Generated (UTC): 2026-11-16T20:32:06Z
- Survivor arm `r_h55` on 16,029 identical rows (key `35cdc203569ef507`); EVAL unread (WI-071)
- Entry-only sizing: ann_vol_target 20%, mean weight +0.50 clipped to [0.25, 2.0], no mid-trade resize; entry-vol policy `min_weight` on 4 row(s)
- Per-unit-size net edge: unsized +600.57 bps → sized +453.83 bps (delta -146.74 bps); cost 50 bps round trip
- Risk-adjusted (mean/std): unsized +0.042 → sized +0.043; placebo z -2.23 (observed -146.74 bps)
- Fold report (mandatory, fails closed): max-fold share n/a (ceiling 50%, FAIL); positive folds 0/1
- Stop/continue: **STOP** — fold ceiling failed (share n/a, positive folds 0/1)

| fold | net sizing delta (bps) |
| ---: | ---: |
| 0 | -146.74 |

| regime axis | bucket | n | mean weight | unsized bps | sized bps | delta bps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| vol_regime:atr_pct_21 | 0 | 3,205 | 0.996 | +263.08 | +374.70 | +111.62 |
| vol_regime:atr_pct_21 | 1 | 3,206 | 0.572 | +112.50 | +109.08 | -3.42 |
| vol_regime:atr_pct_21 | 2 | 3,206 | 0.392 | +180.35 | +188.02 | +7.67 |
| vol_regime:atr_pct_21 | 3 | 3,206 | 0.275 | +458.39 | +441.51 | -16.89 |
| vol_regime:atr_pct_21 | 4 | 3,206 | 0.250 | +1988.41 | +1988.41 | +0.00 |
| disp_entropy_39 | 0 | 3,141 | 0.479 | +431.95 | +276.13 | -155.81 |
| disp_entropy_39 | 1 | 3,155 | 0.514 | +356.96 | +214.22 | -142.74 |
| disp_entropy_39 | 2 | 3,175 | 0.514 | +375.38 | +215.82 | -159.56 |
| disp_entropy_39 | 3 | 3,151 | 0.494 | +216.25 | +90.93 | -125.32 |
| disp_entropy_39 | 4 | 3,150 | 0.476 | +1747.72 | +1642.69 | -105.03 |

- Attribution axes present: ['disp_entropy_39', 'vol_regime:atr_pct_21'] (absent axes are recorded, never substituted; `xsec_vol_rank_cont` is the forward WI-058 label — post-hoc attribution only)
- Layer separation: no learner refit, no AUC selection, no EVAL read.

Record-only: no shortlist, no deployment, no live trading.
