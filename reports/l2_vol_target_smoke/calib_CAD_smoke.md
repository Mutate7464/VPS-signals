# L2 vol-target entry-only sizing — WI-068 survivor (a), CAD  (smoke / synthetic fixture)

- Generated (UTC): 2026-11-15T17:25:45Z
- Survivor arm `r_h55` on 240 identical rows (key `82cde9993256ae45`); EVAL unread (WI-071)
- Entry-only sizing: ann_vol_target 20%, mean weight +0.60 clipped to [0.25, 2.0], no mid-trade resize; entry-vol policy `min_weight` on 0 row(s)
- Per-unit-size net edge: unsized +294.43 bps → sized +372.71 bps (delta +78.27 bps); cost 50 bps round trip
- Risk-adjusted (mean/std): unsized +1.882 → sized +0.925; placebo z +11.39 (observed +78.27 bps)
- Fold report (mandatory, fails closed): max-fold share +1.00 (ceiling 50%, FAIL); positive folds 1/1
- Stop/continue: **STOP** — fold ceiling failed (share 1.0000, positive folds 1/1)

| fold | net sizing delta (bps) |
| ---: | ---: |
| 0 | +78.27 |

| regime axis | bucket | n | mean weight | unsized bps | sized bps | delta bps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| vol_regime:atr_pct_21 | 0 | 48 | 1.417 | +445.64 | +444.64 | -0.99 |
| vol_regime:atr_pct_21 | 1 | 48 | 0.640 | +450.13 | +450.61 | +0.47 |
| vol_regime:atr_pct_21 | 2 | 48 | 0.404 | +285.80 | +301.78 | +15.98 |
| vol_regime:atr_pct_21 | 3 | 48 | 0.292 | +152.80 | +153.04 | +0.23 |
| vol_regime:atr_pct_21 | 4 | 48 | 0.251 | +137.80 | +137.77 | -0.03 |
| disp_entropy_39 | 0 | 50 | 0.618 | +299.07 | +378.89 | +79.82 |
| disp_entropy_39 | 1 | 50 | 0.671 | +336.84 | +392.28 | +55.44 |
| disp_entropy_39 | 2 | 50 | 0.574 | +273.91 | +349.77 | +75.86 |
| disp_entropy_39 | 3 | 40 | 0.670 | +308.61 | +397.07 | +88.47 |
| disp_entropy_39 | 4 | 50 | 0.485 | +256.57 | +337.97 | +81.40 |

- Attribution axes present: ['disp_entropy_39', 'vol_regime:atr_pct_21'] (absent axes are recorded, never substituted; `xsec_vol_rank_cont` is the forward WI-058 label — post-hoc attribution only)
- Layer separation: no learner refit, no AUC selection, no EVAL read.

Record-only: no shortlist, no deployment, no live trading.
