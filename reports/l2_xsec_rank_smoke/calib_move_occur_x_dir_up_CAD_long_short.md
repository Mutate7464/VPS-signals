# L2 xsec top-k screener — move_occur_x_dir_up / CAD (D-027 §5 construction (b))

- Generated (UTC): 2026-11-15T19:54:13Z
- Scope: CALIB only (params tuned on CALIB net edge; EVAL unread — WI-071)  (smoke / synthetic)
- Pass: long_short (D-027 §5 second pass, symmetric bottom-k leg)
- Baseline: frozen fib rule; cost 50 bps single-leg round trip, 100 bps L/S pair cycle
- Params: k=12, band=1.5, horizon=13 dates (60 CALIB trials)
- Capacity: 0.94 trades/week (cap 4), 5,385 held rows (2,696 short rows); turnover f 0.0075 -> cost 100.7 bps
- Gross edge +123.9 bps; net edge +23.2 bps (materiality floor 10.0)
- Fold report: max-fold share 0.2583 (ceiling 50%, pass); positive folds 5/5
- Stop flag: **CONTINUE**

| fold | net edge (bps) |
| ---: | ---: |
| 0 | +16.6 |
| 1 | +29.9 |
| 2 | +15.2 |
| 3 | +27.6 |
| 4 | +26.5 |

Record-only: no shortlist, no deployment, no live trading.
