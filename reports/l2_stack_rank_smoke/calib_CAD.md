# L2 stack ranker — CAD (D-027 §6 regularised stack)

- Generated (UTC): 2026-11-15T03:12:33Z
- Scope: CALIB only (cluster → fit → rank; EVAL unread — WI-071)  (smoke / synthetic)
- Cells: 12 input, 2 clusters at |rho|>0.7 (representatives kept and logged; nothing dropped silently)
- Design: 5,400 CALIB rows x 5 features (cluster scores + meta OOF + 2 regime metafeatures: disp_entropy_39, vol_regime_spread)
- Fit: ridge, 5 purged folds, embargo 20 td; projected peak 2.27 GB at 500,000 x 120 (ceiling 8.0 GB, pass)
- Ranker window: 3,240/5,400 CALIB rows carry a purged-CV OOF score; the rest are unranked, never scored in-sample
- Stack: k=4, band=1.5, horizon=5 (24 trials), 17.55 trades/week, turnover f 0.8421 -> cost 92.1 bps; net edge +324.7 bps (gross +416.8)
- Best single: `xsec_vol_rank_cont` net edge +142.8 bps (k=4, band=1.5, horizon=5)
- Guard beats-best-single: **YES**
- Fold report: max-fold share 0.2055 (ceiling 50%, pass); positive folds 5/5
- Stop flag: **CONTINUE**
- Stack-score artifact: CAD_stack.parquet

| cell | cluster | representative | kept | reason |
| --- | ---: | --- | --- | --- |
| cell_CAD_00 | 0 | cell_CAD_04 | no | |rho|>0.7 with cell_CAD_04 |
| cell_CAD_01 | 0 | cell_CAD_04 | no | |rho|>0.7 with cell_CAD_04 |
| cell_CAD_02 | 0 | cell_CAD_04 | no | |rho|>0.7 with cell_CAD_04 |
| cell_CAD_03 | 0 | cell_CAD_04 | no | |rho|>0.7 with cell_CAD_04 |
| cell_CAD_04 | 0 | cell_CAD_04 | yes | cluster representative |
| cell_CAD_05 | 0 | cell_CAD_04 | no | |rho|>0.7 with cell_CAD_04 |
| cell_CAD_06 | 1 | cell_CAD_07 | no | |rho|>0.7 with cell_CAD_07 |
| cell_CAD_07 | 1 | cell_CAD_07 | yes | cluster representative |
| cell_CAD_08 | 1 | cell_CAD_07 | no | |rho|>0.7 with cell_CAD_07 |
| cell_CAD_09 | 1 | cell_CAD_07 | no | |rho|>0.7 with cell_CAD_07 |
| cell_CAD_10 | 1 | cell_CAD_07 | no | |rho|>0.7 with cell_CAD_07 |
| cell_CAD_11 | 1 | cell_CAD_07 | no | |rho|>0.7 with cell_CAD_07 |

Record-only: no shortlist, no deployment, no live trading.
