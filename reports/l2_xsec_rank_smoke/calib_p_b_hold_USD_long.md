# L2 xsec top-k screener — p_b_hold / USD (D-027 §5 construction (b))

- Generated (UTC): 2026-11-15T19:53:49Z
- Scope: CALIB only (params tuned on CALIB net edge; EVAL unread — WI-071)  (smoke / synthetic)
- Pass: long (D-027 §5 first pass)
- Baseline: frozen fib rule; cost 50 bps single-leg round trip, 100 bps L/S pair cycle
- Params: k=12, band=3, horizon=34 dates (60 CALIB trials)
- Capacity: 4.33 trades/week (cap 4), 5,033 held rows (0 short rows); turnover f 0.0403 -> cost 52.0 bps
- Gross edge -5.8 bps; net edge -57.9 bps (materiality floor 10.0)
- Fold report: max-fold share n/a (ceiling 50%, FAIL); positive folds 0/5
- Stop flag: **STOP** — CALIB net edge -57.8577 bps <= materiality floor 10.0; fold ceiling failed (share n/a, positive folds 0/5)

| fold | net edge (bps) |
| ---: | ---: |
| 0 | -56.9 |
| 1 | -58.7 |
| 2 | -59.5 |
| 3 | -55.8 |
| 4 | -58.1 |

Record-only: no shortlist, no deployment, no live trading.
