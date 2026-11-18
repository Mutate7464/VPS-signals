# L2 xsec top-k screener — move_dir_up / CAD (D-027 §5 construction (b))

- Generated (UTC): 2026-11-15T19:54:33Z
- Scope: CALIB only (params tuned on CALIB net edge; EVAL unread — WI-071)  (smoke / synthetic)
- Pass: long_short (D-027 §5 second pass, symmetric bottom-k leg)
- Baseline: frozen fib rule; cost 50 bps single-leg round trip, 100 bps L/S pair cycle
- Params: k=12, band=1.5, horizon=10 dates (60 CALIB trials)
- Capacity: 1.08 trades/week (cap 4), 5,376 held rows (2,715 short rows); turnover f 0.0084 -> cost 100.8 bps
- Gross edge +133.8 bps; net edge +32.9 bps (materiality floor 10.0)
- Fold report: max-fold share 0.2292 (ceiling 50%, pass); positive folds 5/5
- Stop flag: **CONTINUE**

| fold | net edge (bps) |
| ---: | ---: |
| 0 | +29.8 |
| 1 | +34.2 |
| 2 | +28.1 |
| 3 | +37.7 |
| 4 | +34.8 |

Record-only: no shortlist, no deployment, no live trading.
