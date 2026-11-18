# L2 xsec top-k screener — xsec_vol_rank_cont / USD (D-027 §5 construction (b))

- Generated (UTC): 2026-11-15T17:02:18Z
- Scope: CALIB only (params tuned on CALIB net edge; EVAL unread — WI-071)
- Baseline: frozen fib rule; cost 50 bps single-leg round trip
- Params: k=4, band=1.5, horizon=5 dates (24 CALIB trials)
- Capacity: 3.65 trades/week (cap 4), 2,141 held rows; turnover f 0.5135 -> cost 75.7 bps
- Gross edge +12.9 bps; net edge -62.8 bps (materiality floor 10.0)
- Fold report: max-fold share n/a (ceiling 50%, FAIL); positive folds 0/2
- Stop flag: **STOP** — CALIB net edge -62.8069 bps <= materiality floor 10.0; fold ceiling failed (share n/a, positive folds 0/2)

| fold | net edge (bps) |
| ---: | ---: |
| 0 | -49.1 |
| 1 | -73.2 |

Record-only: no shortlist, no deployment, no live trading.
