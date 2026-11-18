# L2 xsec top-k screener — move_occur_x_dir_up / USD (D-027 §5 construction (b))

- Generated (UTC): 2026-11-15T17:02:21Z
- Scope: CALIB only (params tuned on CALIB net edge; EVAL unread — WI-071)
- Baseline: frozen fib rule; cost 50 bps single-leg round trip
- Params: k=12, band=2, horizon=21 dates (24 CALIB trials)
- Capacity: 13.51 trades/week (cap 4), 7,378 held rows; turnover f 0.5595 -> cost 78.0 bps
- Gross edge +10.9 bps; net edge -67.0 bps (materiality floor 10.0)
- Fold report: max-fold share n/a (ceiling 50%, FAIL); positive folds 0/2
- Stop flag: **STOP** — CALIB net edge -67.0448 bps <= materiality floor 10.0; fold ceiling failed (share n/a, positive folds 0/2)

| fold | net edge (bps) |
| ---: | ---: |
| 0 | -85.9 |
| 1 | -46.1 |

Record-only: no shortlist, no deployment, no live trading.
