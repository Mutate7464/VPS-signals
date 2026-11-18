# L2 xsec top-k screener — move_occur / CAD (D-027 §5 construction (b))

- Generated (UTC): 2026-11-15T19:54:28Z
- Scope: CALIB only (params tuned on CALIB net edge; EVAL unread — WI-071)  (smoke / synthetic)
- Pass: long_short (D-027 §5 second pass, symmetric bottom-k leg)
- Baseline: frozen fib rule; cost 50 bps single-leg round trip, 100 bps L/S pair cycle
- Params: k=12, band=3, horizon=34 dates (60 CALIB trials)
- Capacity: 2.56 trades/week (cap 4), 5,320 held rows (289 short rows); turnover f 0.0197 -> cost 102.0 bps
- Gross edge +2.5 bps; net edge -99.5 bps (materiality floor 10.0)
- Fold report: max-fold share n/a (ceiling 50%, FAIL); positive folds 0/5
- Stop flag: **STOP** — CALIB net edge -99.5151 bps <= materiality floor 10.0; fold ceiling failed (share n/a, positive folds 0/5)

| fold | net edge (bps) |
| ---: | ---: |
| 0 | -99.9 |
| 1 | -91.5 |
| 2 | -100.5 |
| 3 | -109.0 |
| 4 | -96.6 |

Record-only: no shortlist, no deployment, no live trading.
