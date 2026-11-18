# L2 xsec top-k screener — move_occur_x_dir_up / USD (D-027 §5 construction (b))

- Generated (UTC): 2026-11-15T19:33:15Z
- Scope: CALIB only (params tuned on CALIB net edge; EVAL unread — WI-071)  (smoke / synthetic)
- Baseline: frozen fib rule; cost 50 bps single-leg round trip
- Params: k=4, band=1.5, horizon=5 dates (24 CALIB trials)
- Capacity: 17.47 trades/week (cap 4), 761 held rows; turnover f 0.8319 -> cost 91.6 bps
- Gross edge +234.0 bps; net edge +142.4 bps (materiality floor 10.0)
- Fold report: max-fold share 0.2174 (ceiling 50%, pass); positive folds 5/5
- Stop flag: **CONTINUE**

| fold | net edge (bps) |
| ---: | ---: |
| 0 | +141.2 |
| 1 | +150.7 |
| 2 | +116.9 |
| 3 | +155.0 |
| 4 | +149.2 |

Record-only: no shortlist, no deployment, no live trading.
