# L2 vol-target entry-only sizing — WI-068 survivor (a), USD

- Generated (UTC): 2026-11-16T20:32:05Z
- Survivor arm `r_h55` on 28,220 identical rows (key `02076ff55dc55cef`); EVAL unread (WI-071)
- Entry-only sizing: ann_vol_target 20%, mean weight +0.50 clipped to [0.25, 2.0], no mid-trade resize; entry-vol policy `min_weight` on 0 row(s)
- Per-unit-size net edge: unsized +329.41 bps → sized +218.29 bps (delta -111.12 bps); cost 50 bps round trip
- Risk-adjusted (mean/std): unsized +0.108 → sized +0.106; placebo z -20.58 (observed -111.12 bps)
- Fold report (mandatory, fails closed): max-fold share n/a (ceiling 50%, FAIL); positive folds 0/1
- Stop/continue: **STOP** — fold ceiling failed (share n/a, positive folds 0/1)

| fold | net sizing delta (bps) |
| ---: | ---: |
| 0 | -111.12 |

| regime axis | bucket | n | mean weight | unsized bps | sized bps | delta bps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| vol_regime:atr_pct_21 | 0 | 5,644 | 0.841 | +34.35 | +36.59 | +2.24 |
| vol_regime:atr_pct_21 | 1 | 5,644 | 0.583 | +92.79 | +90.21 | -2.58 |
| vol_regime:atr_pct_21 | 2 | 5,644 | 0.454 | +223.98 | +222.68 | -1.30 |
| vol_regime:atr_pct_21 | 3 | 5,644 | 0.342 | +349.20 | +339.92 | -9.28 |
| vol_regime:atr_pct_21 | 4 | 5,644 | 0.254 | +946.76 | +941.89 | -4.87 |
| disp_entropy_39 | 0 | 5,572 | 0.445 | +415.86 | +290.44 | -125.42 |
| disp_entropy_39 | 1 | 5,566 | 0.485 | +205.56 | +101.95 | -103.61 |
| disp_entropy_39 | 2 | 5,574 | 0.494 | +337.96 | +219.20 | -118.76 |
| disp_entropy_39 | 3 | 5,594 | 0.509 | +384.67 | +268.23 | -116.43 |
| disp_entropy_39 | 4 | 5,554 | 0.533 | +392.35 | +296.75 | -95.61 |

- Attribution axes present: ['disp_entropy_39', 'vol_regime:atr_pct_21'] (absent axes are recorded, never substituted; `xsec_vol_rank_cont` is the forward WI-058 label — post-hoc attribution only)
- Layer separation: no learner refit, no AUC selection, no EVAL read.

Record-only: no shortlist, no deployment, no live trading.
