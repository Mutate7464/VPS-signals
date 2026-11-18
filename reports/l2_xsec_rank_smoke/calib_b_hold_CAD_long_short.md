# L2 xsec top-k screener — b_hold / CAD (D-027 §5 construction (b))

- Generated (UTC): 2026-11-15T19:54:18Z
- Scope: CALIB only (params tuned on CALIB net edge; EVAL unread — WI-071)  (smoke / synthetic)
- Pass: long_short (D-027 §5 second pass, symmetric bottom-k leg)
- Baseline: frozen fib rule; cost 50 bps single-leg round trip, 100 bps L/S pair cycle
- Params: k=12, band=1.5, horizon=21 dates (60 CALIB trials)
- Capacity: 0.83 trades/week (cap 4), 5,392 held rows (2,712 short rows); turnover f 0.0067 -> cost 100.7 bps
- Gross edge +149.6 bps; net edge +48.9 bps (materiality floor 10.0)
- Fold report: max-fold share 0.2129 (ceiling 50%, pass); positive folds 5/5
- Stop flag: **CONTINUE**

| fold | net edge (bps) |
| ---: | ---: |
| 0 | +50.5 |
| 1 | +48.9 |
| 2 | +41.9 |
| 3 | +52.0 |
| 4 | +51.1 |

Record-only: no shortlist, no deployment, no live trading.
