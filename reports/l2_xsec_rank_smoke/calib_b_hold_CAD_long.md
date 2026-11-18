# L2 xsec top-k screener — b_hold / CAD (D-027 §5 construction (b))

- Generated (UTC): 2026-11-15T19:54:15Z
- Scope: CALIB only (params tuned on CALIB net edge; EVAL unread — WI-071)  (smoke / synthetic)
- Pass: long (D-027 §5 first pass)
- Baseline: frozen fib rule; cost 50 bps single-leg round trip, 100 bps L/S pair cycle
- Params: k=4, band=1.5, horizon=10 dates (60 CALIB trials)
- Capacity: 17.17 trades/week (cap 4), 759 held rows (0 short rows); turnover f 0.8199 -> cost 91.0 bps
- Gross edge +300.2 bps; net edge +209.2 bps (materiality floor 10.0)
- Fold report: max-fold share 0.2098 (ceiling 50%, pass); positive folds 5/5
- Stop flag: **CONTINUE**

| fold | net edge (bps) |
| ---: | ---: |
| 0 | +210.2 |
| 1 | +203.7 |
| 2 | +197.3 |
| 3 | +219.4 |
| 4 | +215.3 |

Record-only: no shortlist, no deployment, no live trading.
