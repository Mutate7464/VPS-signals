# L2 xsec top-k screener — xsec_vol_rank_cont / CAD (D-027 §5 construction (b))

- Generated (UTC): 2026-11-15T17:02:24Z
- Scope: CALIB only (params tuned on CALIB net edge; EVAL unread — WI-071)
- Baseline: frozen fib rule; cost 50 bps single-leg round trip
- Params: k=4, band=1.5, horizon=5 dates (24 CALIB trials)
- Capacity: 3.70 trades/week (cap 4), 1,108 held rows; turnover f 0.5406 -> cost 77.0 bps
- Gross edge +124.2 bps; net edge +47.2 bps (materiality floor 10.0)
- Fold report: max-fold share 2.5416 (ceiling 50%, FAIL); positive folds 1/2
- Stop flag: **STOP** — fold ceiling failed (share 2.5416, positive folds 1/2)

| fold | net edge (bps) |
| ---: | ---: |
| 0 | +248.8 |
| 1 | -150.9 |

Record-only: no shortlist, no deployment, no live trading.
