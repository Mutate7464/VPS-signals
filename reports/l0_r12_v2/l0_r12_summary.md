# D-026 Phase 1 — L0 R12 reference grids (PROVISIONAL)

- Generated (UTC): 2026-11-14T00:58:42Z
- R12: 2 targets (`b_hold`, `xsec_vol_rank_bin`) x horizons (8, 13, 21) x lightgbm x 2 markets = 12 cells per block
- Test statistic: fold-paired OOF AUC delta vs baseline; paired t (df=4); BH alpha=0.05, m=12 per block

### L0-1_swing_structure — 0/12 BH-FDR survivors

| market | target | h | base AUC | block AUC | ΔAUC | p | FDR | prec25 lift |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | ---: |
| CAD | `b_hold` | 21 | 0.8209 | 0.8318 | +0.0109 | 0.569 |  | n/a |
| USD | `xsec_vol_rank_bin` | 13 | 0.8099 | 0.8112 | +0.0012 | 0.137 |  | n/a |
| CAD | `xsec_vol_rank_bin` | 21 | 0.8448 | 0.8458 | +0.0011 | 0.117 |  | n/a |
| USD | `xsec_vol_rank_bin` | 21 | 0.8200 | 0.8210 | +0.0011 | 0.0647 |  | n/a |
| CAD | `xsec_vol_rank_bin` | 8 | 0.8192 | 0.8200 | +0.0008 | 0.189 |  | n/a |
| USD | `xsec_vol_rank_bin` | 8 | 0.7892 | 0.7899 | +0.0006 | 0.406 |  | n/a |
| CAD | `xsec_vol_rank_bin` | 13 | 0.8353 | 0.8356 | +0.0003 | 0.626 |  | n/a |
| USD | `b_hold` | 21 | 0.8833 | 0.8817 | -0.0016 | 0.727 |  | n/a |
| CAD | `b_hold` | 8 | 0.6258 | 0.6216 | -0.0041 | 0.577 |  | n/a |
| USD | `b_hold` | 13 | 0.7792 | 0.7747 | -0.0045 | 0.212 |  | n/a |
| USD | `b_hold` | 8 | 0.6522 | 0.6439 | -0.0083 | 0.297 |  | n/a |
| CAD | `b_hold` | 13 | 0.6913 | 0.6763 | -0.0150 | 0.168 |  | n/a |

### L0-3_regime_age — 0/12 BH-FDR survivors

| market | target | h | base AUC | block AUC | ΔAUC | p | FDR | prec25 lift |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | ---: |
| CAD | `b_hold` | 21 | 0.8209 | 0.8450 | +0.0241 | 0.245 |  | n/a |
| USD | `b_hold` | 13 | 0.7792 | 0.7873 | +0.0081 | 0.66 |  | n/a |
| USD | `xsec_vol_rank_bin` | 21 | 0.8200 | 0.8214 | +0.0014 | 0.0897 |  | n/a |
| USD | `xsec_vol_rank_bin` | 13 | 0.8099 | 0.8112 | +0.0013 | 0.248 |  | n/a |
| USD | `b_hold` | 21 | 0.8833 | 0.8843 | +0.0010 | 0.756 |  | n/a |
| CAD | `xsec_vol_rank_bin` | 21 | 0.8448 | 0.8453 | +0.0006 | 0.593 |  | n/a |
| USD | `xsec_vol_rank_bin` | 8 | 0.7892 | 0.7897 | +0.0004 | 0.543 |  | n/a |
| CAD | `xsec_vol_rank_bin` | 13 | 0.8353 | 0.8355 | +0.0002 | 0.697 |  | n/a |
| CAD | `xsec_vol_rank_bin` | 8 | 0.8192 | 0.8191 | -0.0001 | 0.909 |  | n/a |
| CAD | `b_hold` | 13 | 0.6913 | 0.6838 | -0.0075 | 0.5 |  | n/a |
| USD | `b_hold` | 8 | 0.6522 | 0.6361 | -0.0162 | 0.246 |  | n/a |
| CAD | `b_hold` | 8 | 0.6258 | 0.6088 | -0.0169 | 0.174 |  | n/a |

### L0-5_universe_dispersion — 4/12 BH-FDR survivors

| market | target | h | base AUC | block AUC | ΔAUC | p | FDR | prec25 lift |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | ---: |
| USD | `b_hold` | 13 | 0.7792 | 0.7850 | +0.0058 | 0.548 |  | n/a |
| CAD | `xsec_vol_rank_bin` | 21 | 0.8448 | 0.8491 | +0.0043 | 0.00704 | YES | n/a |
| CAD | `xsec_vol_rank_bin` | 8 | 0.8192 | 0.8224 | +0.0032 | 0.00555 | YES | n/a |
| CAD | `xsec_vol_rank_bin` | 13 | 0.8353 | 0.8383 | +0.0030 | 0.0115 | YES | n/a |
| USD | `xsec_vol_rank_bin` | 21 | 0.8200 | 0.8220 | +0.0021 | 0.00475 | YES | n/a |
| CAD | `b_hold` | 21 | 0.8209 | 0.8228 | +0.0019 | 0.862 |  | n/a |
| USD | `xsec_vol_rank_bin` | 8 | 0.7892 | 0.7908 | +0.0016 | 0.0599 |  | n/a |
| USD | `xsec_vol_rank_bin` | 13 | 0.8099 | 0.8115 | +0.0016 | 0.171 |  | n/a |
| USD | `b_hold` | 21 | 0.8833 | 0.8810 | -0.0023 | 0.791 |  | n/a |
| CAD | `b_hold` | 8 | 0.6258 | 0.6191 | -0.0067 | 0.23 |  | n/a |
| USD | `b_hold` | 8 | 0.6522 | 0.6443 | -0.0079 | 0.483 |  | n/a |
| CAD | `b_hold` | 13 | 0.6913 | 0.6778 | -0.0135 | 0.328 |  | n/a |

### L0-6_effort_result — 0/12 BH-FDR survivors

| market | target | h | base AUC | block AUC | ΔAUC | p | FDR | prec25 lift |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | ---: |
| USD | `b_hold` | 21 | 0.8833 | 0.8885 | +0.0052 | 0.394 |  | n/a |
| USD | `b_hold` | 13 | 0.7792 | 0.7821 | +0.0029 | 0.482 |  | n/a |
| USD | `b_hold` | 8 | 0.6522 | 0.6544 | +0.0022 | 0.86 |  | n/a |
| USD | `xsec_vol_rank_bin` | 13 | 0.8099 | 0.8107 | +0.0008 | 0.211 |  | n/a |
| USD | `xsec_vol_rank_bin` | 8 | 0.7892 | 0.7897 | +0.0005 | 0.286 |  | n/a |
| USD | `xsec_vol_rank_bin` | 21 | 0.8200 | 0.8203 | +0.0004 | 0.307 |  | n/a |
| CAD | `b_hold` | 8 | 0.6258 | 0.6258 | +0.0000 | 1 |  | n/a |
| CAD | `b_hold` | 13 | 0.6913 | 0.6913 | +0.0000 | 1 |  | n/a |
| CAD | `b_hold` | 21 | 0.8209 | 0.8209 | +0.0000 | 1 |  | n/a |
| CAD | `xsec_vol_rank_bin` | 8 | 0.8192 | 0.8192 | +0.0000 | 1 |  | n/a |
| CAD | `xsec_vol_rank_bin` | 13 | 0.8353 | 0.8353 | +0.0000 | 1 |  | n/a |
| CAD | `xsec_vol_rank_bin` | 21 | 0.8448 | 0.8448 | +0.0000 | 1 |  | n/a |


## Footer

- START_UTC: 2026-11-14T00:50:24Z
- END_UTC: 2026-11-14T00:58:42Z
- core: 888.6s of 9000s cap
- NEXT_ALLOWED_RUN_UTC: 2026-11-14T01:28Z (burst < 1 core-h)
- Verdict PROVISIONAL — computed labels are advisory until admin ratification.
- PREDICTIVE DIAGNOSTIC — no economic claim (D-023).

