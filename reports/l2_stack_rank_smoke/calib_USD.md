# L2 stack ranker — USD (D-027 §6 regularised stack)

- Generated (UTC): 2026-11-15T03:12:30Z
- Scope: CALIB only (cluster → fit → rank; EVAL unread — WI-071)  (smoke / synthetic)
- Cells: 12 input, 2 clusters at |rho|>0.7 (representatives kept and logged; nothing dropped silently)
- Design: 5,400 CALIB rows x 5 features (cluster scores + meta OOF + 2 regime metafeatures: disp_entropy_39, vol_regime_spread)
- Fit: ridge, 5 purged folds, embargo 20 td; projected peak 2.27 GB at 500,000 x 120 (ceiling 8.0 GB, pass)
- Ranker window: 3,240/5,400 CALIB rows carry a purged-CV OOF score; the rest are unranked, never scored in-sample
- Stack: k=4, band=1.5, horizon=5 (24 trials), 17.36 trades/week, turnover f 0.8187 -> cost 90.9 bps; net edge +318.5 bps (gross +409.4)
- Best single: `xsec_vol_rank_cont` net edge +151.4 bps (k=4, band=1.5, horizon=13)
- Guard beats-best-single: **YES**
- Fold report: max-fold share 0.2116 (ceiling 50%, pass); positive folds 5/5
- Stop flag: **CONTINUE**
- Stack-score artifact: USD_stack.parquet

| cell | cluster | representative | kept | reason |
| --- | ---: | --- | --- | --- |
| cell_USD_00 | 0 | cell_USD_01 | no | |rho|>0.7 with cell_USD_01 |
| cell_USD_01 | 0 | cell_USD_01 | yes | cluster representative |
| cell_USD_02 | 0 | cell_USD_01 | no | |rho|>0.7 with cell_USD_01 |
| cell_USD_03 | 0 | cell_USD_01 | no | |rho|>0.7 with cell_USD_01 |
| cell_USD_04 | 0 | cell_USD_01 | no | |rho|>0.7 with cell_USD_01 |
| cell_USD_05 | 0 | cell_USD_01 | no | |rho|>0.7 with cell_USD_01 |
| cell_USD_06 | 1 | cell_USD_10 | no | |rho|>0.7 with cell_USD_10 |
| cell_USD_07 | 1 | cell_USD_10 | no | |rho|>0.7 with cell_USD_10 |
| cell_USD_08 | 1 | cell_USD_10 | no | |rho|>0.7 with cell_USD_10 |
| cell_USD_09 | 1 | cell_USD_10 | no | |rho|>0.7 with cell_USD_10 |
| cell_USD_10 | 1 | cell_USD_10 | yes | cluster representative |
| cell_USD_11 | 1 | cell_USD_10 | no | |rho|>0.7 with cell_USD_10 |

Record-only: no shortlist, no deployment, no live trading.
