# L2 xsec top-k screener — xsec_vol_rank_cont / USD (D-027 §5 construction (b))

- Generated (UTC): 2026-11-15T19:33:14Z
- Scope: CALIB only (params tuned on CALIB net edge; EVAL unread — WI-071)  (smoke / synthetic)
- Baseline: frozen fib rule; cost 50 bps single-leg round trip
- Params: k=4, band=1.5, horizon=5 dates (24 CALIB trials)
- Capacity: 17.00 trades/week (cap 4), 764 held rows; turnover f 0.8077 -> cost 90.4 bps
- Gross edge +264.8 bps; net edge +174.4 bps (materiality floor 10.0)
- Fold report: max-fold share 0.2095 (ceiling 50%, pass); positive folds 5/5
- Stop flag: **CONTINUE**

| fold | net edge (bps) |
| ---: | ---: |
| 0 | +182.8 |
| 1 | +182.3 |
| 2 | +163.9 |
| 3 | +165.6 |
| 4 | +178.0 |

Record-only: no shortlist, no deployment, no live trading.
