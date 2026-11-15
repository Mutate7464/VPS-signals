# L2 xsec top-k screener — move_occur_x_dir_up / CAD (D-027 §5 construction (b))

- Generated (UTC): 2026-11-15T17:02:26Z
- Scope: CALIB only (params tuned on CALIB net edge; EVAL unread — WI-071)
- Baseline: frozen fib rule; cost 50 bps single-leg round trip
- Params: k=12, band=2, horizon=13 dates (24 CALIB trials)
- Capacity: 10.80 trades/week (cap 4), 3,950 held rows; turnover f 0.4463 -> cost 72.3 bps
- Gross edge +7.7 bps; net edge -64.6 bps (materiality floor 10.0)
- Fold report: max-fold share n/a (ceiling 50%, FAIL); positive folds 0/2
- Stop flag: **STOP** — CALIB net edge -64.6190 bps <= materiality floor 10.0; fold ceiling failed (share n/a, positive folds 0/2)

| fold | net edge (bps) |
| ---: | ---: |
| 0 | -76.2 |
| 1 | -52.3 |

Record-only: no shortlist, no deployment, no live trading.
