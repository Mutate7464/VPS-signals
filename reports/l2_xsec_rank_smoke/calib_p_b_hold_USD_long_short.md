# L2 xsec top-k screener — p_b_hold / USD (D-027 §5 construction (b))

- Generated (UTC): 2026-11-15T19:53:51Z
- Scope: CALIB only (params tuned on CALIB net edge; EVAL unread — WI-071)  (smoke / synthetic)
- Pass: long_short (D-027 §5 second pass, symmetric bottom-k leg)
- Baseline: frozen fib rule; cost 50 bps single-leg round trip, 100 bps L/S pair cycle
- Params: k=12, band=3, horizon=34 dates (60 CALIB trials)
- Capacity: 2.53 trades/week (cap 4), 5,317 held rows (316 short rows); turnover f 0.0191 -> cost 101.9 bps
- Gross edge -9.0 bps; net edge -110.9 bps (materiality floor 10.0)
- Fold report: max-fold share n/a (ceiling 50%, FAIL); positive folds 0/5
- Stop flag: **STOP** — CALIB net edge -110.9024 bps <= materiality floor 10.0; fold ceiling failed (share n/a, positive folds 0/5)

| fold | net edge (bps) |
| ---: | ---: |
| 0 | -104.3 |
| 1 | -109.6 |
| 2 | -115.6 |
| 3 | -114.4 |
| 4 | -110.5 |

Record-only: no shortlist, no deployment, no live trading.
