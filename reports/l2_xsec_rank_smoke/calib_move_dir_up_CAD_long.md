# L2 xsec top-k screener — move_dir_up / CAD (D-027 §5 construction (b))

- Generated (UTC): 2026-11-15T19:54:30Z
- Scope: CALIB only (params tuned on CALIB net edge; EVAL unread — WI-071)  (smoke / synthetic)
- Pass: long (D-027 §5 first pass)
- Baseline: frozen fib rule; cost 50 bps single-leg round trip, 100 bps L/S pair cycle
- Params: k=4, band=1.5, horizon=5 dates (60 CALIB trials)
- Capacity: 17.39 trades/week (cap 4), 767 held rows (0 short rows); turnover f 0.8256 -> cost 91.3 bps
- Gross edge +264.5 bps; net edge +173.3 bps (materiality floor 10.0)
- Fold report: max-fold share 0.2172 (ceiling 50%, pass); positive folds 5/5
- Stop flag: **CONTINUE**

| fold | net edge (bps) |
| ---: | ---: |
| 0 | +179.5 |
| 1 | +156.4 |
| 2 | +156.4 |
| 3 | +188.3 |
| 4 | +186.1 |

Record-only: no shortlist, no deployment, no live trading.
