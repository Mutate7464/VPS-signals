# L2 vol-target entry-only sizing — WI-068 survivor (a), USD  (smoke / synthetic fixture)

- Generated (UTC): 2026-11-15T17:25:45Z
- Survivor arm `r_h55` on 240 identical rows (key `82cde9993256ae45`); EVAL unread (WI-071)
- Entry-only sizing: ann_vol_target 20%, mean weight +0.57 clipped to [0.25, 2.0], no mid-trade resize; entry-vol policy `min_weight` on 0 row(s)
- Per-unit-size net edge: unsized +298.69 bps → sized +370.80 bps (delta +72.11 bps); cost 50 bps round trip
- Risk-adjusted (mean/std): unsized +1.977 → sized +0.902; placebo z +7.19 (observed +72.11 bps)
- Fold report (mandatory, fails closed): max-fold share +1.00 (ceiling 50%, FAIL); positive folds 1/1
- Stop/continue: **STOP** — fold ceiling failed (share 1.0000, positive folds 1/1)

| fold | net sizing delta (bps) |
| ---: | ---: |
| 0 | +72.11 |

| regime axis | bucket | n | mean weight | unsized bps | sized bps | delta bps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| vol_regime:atr_pct_21 | 0 | 48 | 1.376 | +446.26 | +445.61 | -0.65 |
| vol_regime:atr_pct_21 | 1 | 48 | 0.554 | +443.47 | +444.17 | +0.70 |
| vol_regime:atr_pct_21 | 2 | 48 | 0.380 | +293.54 | +300.92 | +7.38 |
| vol_regime:atr_pct_21 | 3 | 48 | 0.293 | +160.35 | +160.47 | +0.13 |
| vol_regime:atr_pct_21 | 4 | 48 | 0.251 | +149.84 | +149.81 | -0.02 |
| disp_entropy_39 | 0 | 50 | 0.488 | +305.55 | +354.37 | +48.82 |
| disp_entropy_39 | 1 | 50 | 0.546 | +266.56 | +350.65 | +84.09 |
| disp_entropy_39 | 2 | 50 | 0.611 | +310.03 | +379.95 | +69.92 |
| disp_entropy_39 | 3 | 50 | 0.680 | +324.36 | +401.16 | +76.81 |
| disp_entropy_39 | 4 | 40 | 0.518 | +284.03 | +353.43 | +69.40 |

- Attribution axes present: ['disp_entropy_39', 'vol_regime:atr_pct_21'] (absent axes are recorded, never substituted; `xsec_vol_rank_cont` is the forward WI-058 label — post-hoc attribution only)
- Layer separation: no learner refit, no AUC selection, no EVAL read.

Record-only: no shortlist, no deployment, no live trading.
