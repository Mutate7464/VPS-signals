# D-026 Phase 1 — L0 R12 reference grids (PROVISIONAL)

- Generated (UTC): 2026-11-13T23:36:09Z
- R12: 2 targets (`b_hold`, `xsec_vol_rank_bin`) x horizons (8, 13, 21) x lightgbm x 2 markets = 12 cells per block
- Test statistic: fold-paired OOF AUC delta vs baseline; paired t (df=4); BH alpha=0.05, m=12 per block

### L0-1_swing_structure — 3/12 BH-FDR survivors

| market | target | h | base AUC | block AUC | ΔAUC | p | FDR | prec25 lift |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | ---: |
| CAD | `b_hold` | 21 | 0.8209 | 0.8384 | +0.0176 | 0.116 |  | 2.000x |
| CAD | `xsec_vol_rank_bin` | 21 | 0.8448 | 0.8495 | +0.0048 | 0.00624 | YES | 1.000x |
| CAD | `xsec_vol_rank_bin` | 13 | 0.8353 | 0.8396 | +0.0043 | 0.0024 | YES | 1.000x |
| CAD | `xsec_vol_rank_bin` | 8 | 0.8192 | 0.8234 | +0.0042 | 0.00149 | YES | 0.833x |
| USD | `xsec_vol_rank_bin` | 21 | 0.8200 | 0.8238 | +0.0039 | 0.0249 |  | 1.000x |
| USD | `b_hold` | 13 | 0.7792 | 0.7825 | +0.0033 | 0.761 |  | 0.792x |
| USD | `xsec_vol_rank_bin` | 13 | 0.8099 | 0.8132 | +0.0032 | 0.0534 |  | 1.095x |
| USD | `xsec_vol_rank_bin` | 8 | 0.7892 | 0.7922 | +0.0029 | 0.0771 |  | 1.000x |
| USD | `b_hold` | 21 | 0.8833 | 0.8820 | -0.0013 | 0.728 |  | 0.760x |
| CAD | `b_hold` | 8 | 0.6258 | 0.6188 | -0.0069 | 0.378 |  | 1.000x |
| USD | `b_hold` | 8 | 0.6522 | 0.6448 | -0.0074 | 0.241 |  | 0.960x |
| CAD | `b_hold` | 13 | 0.6913 | 0.6831 | -0.0082 | 0.189 |  | 1.333x |

### L0-2_realized_asymmetry — 4/12 BH-FDR survivors

| market | target | h | base AUC | block AUC | ΔAUC | p | FDR | prec25 lift |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | ---: |
| CAD | `b_hold` | 21 | 0.8209 | 0.8343 | +0.0134 | 0.271 |  | 1.500x |
| CAD | `xsec_vol_rank_bin` | 21 | 0.8448 | 0.8500 | +0.0052 | 0.00466 | YES | 1.043x |
| CAD | `xsec_vol_rank_bin` | 13 | 0.8353 | 0.8396 | +0.0043 | 0.00162 | YES | 1.000x |
| USD | `xsec_vol_rank_bin` | 21 | 0.8200 | 0.8242 | +0.0042 | 0.00887 | YES | 1.000x |
| CAD | `xsec_vol_rank_bin` | 8 | 0.8192 | 0.8227 | +0.0036 | 0.0122 | YES | 0.875x |
| USD | `xsec_vol_rank_bin` | 13 | 0.8099 | 0.8135 | +0.0035 | 0.0563 |  | 1.048x |
| USD | `b_hold` | 13 | 0.7792 | 0.7817 | +0.0025 | 0.791 |  | 0.917x |
| USD | `xsec_vol_rank_bin` | 8 | 0.7892 | 0.7917 | +0.0024 | 0.172 |  | 1.150x |
| USD | `b_hold` | 21 | 0.8833 | 0.8816 | -0.0018 | 0.807 |  | 0.760x |
| USD | `b_hold` | 8 | 0.6522 | 0.6480 | -0.0042 | 0.578 |  | 0.920x |
| CAD | `b_hold` | 8 | 0.6258 | 0.6125 | -0.0132 | 0.145 |  | 0.833x |
| CAD | `b_hold` | 13 | 0.6913 | 0.6690 | -0.0223 | 0.26 |  | 1.000x |

### L0-3_regime_age — 5/12 BH-FDR survivors

| market | target | h | base AUC | block AUC | ΔAUC | p | FDR | prec25 lift |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | ---: |
| CAD | `b_hold` | 21 | 0.8209 | 0.8402 | +0.0193 | 0.252 |  | 1.000x |
| USD | `b_hold` | 13 | 0.7792 | 0.7896 | +0.0104 | 0.344 |  | 0.792x |
| CAD | `xsec_vol_rank_bin` | 21 | 0.8448 | 0.8504 | +0.0056 | 0.0069 | YES | 0.870x |
| USD | `xsec_vol_rank_bin` | 21 | 0.8200 | 0.8239 | +0.0039 | 0.00966 | YES | 1.000x |
| CAD | `xsec_vol_rank_bin` | 8 | 0.8192 | 0.8230 | +0.0039 | 0.000607 | YES | 1.042x |
| CAD | `xsec_vol_rank_bin` | 13 | 0.8353 | 0.8391 | +0.0038 | 0.00376 | YES | 0.958x |
| USD | `xsec_vol_rank_bin` | 13 | 0.8099 | 0.8132 | +0.0033 | 0.0782 |  | 1.143x |
| USD | `xsec_vol_rank_bin` | 8 | 0.7892 | 0.7920 | +0.0027 | 0.0894 |  | 1.100x |
| USD | `b_hold` | 21 | 0.8833 | 0.8827 | -0.0006 | 0.912 |  | 0.880x |
| CAD | `b_hold` | 8 | 0.6258 | 0.6167 | -0.0091 | 0.429 |  | 1.000x |
| CAD | `b_hold` | 13 | 0.6913 | 0.6753 | -0.0160 | 0.0342 |  | 1.222x |
| USD | `b_hold` | 8 | 0.6522 | 0.6343 | -0.0180 | 0.00716 | YES | 0.880x |

### L0-4_jump_intensity — 4/12 BH-FDR survivors

| market | target | h | base AUC | block AUC | ΔAUC | p | FDR | prec25 lift |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | ---: |
| CAD | `b_hold` | 21 | 0.8209 | 0.8343 | +0.0134 | 0.271 |  | 1.500x |
| CAD | `xsec_vol_rank_bin` | 21 | 0.8448 | 0.8500 | +0.0052 | 0.00466 | YES | 1.043x |
| CAD | `xsec_vol_rank_bin` | 13 | 0.8353 | 0.8396 | +0.0043 | 0.00162 | YES | 1.000x |
| USD | `xsec_vol_rank_bin` | 21 | 0.8200 | 0.8242 | +0.0042 | 0.00887 | YES | 1.000x |
| CAD | `xsec_vol_rank_bin` | 8 | 0.8192 | 0.8227 | +0.0036 | 0.0122 | YES | 0.875x |
| USD | `xsec_vol_rank_bin` | 13 | 0.8099 | 0.8135 | +0.0035 | 0.0563 |  | 1.048x |
| USD | `b_hold` | 13 | 0.7792 | 0.7817 | +0.0025 | 0.791 |  | 0.917x |
| USD | `xsec_vol_rank_bin` | 8 | 0.7892 | 0.7917 | +0.0024 | 0.172 |  | 1.150x |
| USD | `b_hold` | 21 | 0.8833 | 0.8816 | -0.0018 | 0.807 |  | 0.760x |
| USD | `b_hold` | 8 | 0.6522 | 0.6480 | -0.0042 | 0.578 |  | 0.920x |
| CAD | `b_hold` | 8 | 0.6258 | 0.6125 | -0.0132 | 0.145 |  | 0.833x |
| CAD | `b_hold` | 13 | 0.6913 | 0.6690 | -0.0223 | 0.26 |  | 1.000x |

### L0-5_universe_dispersion — 4/12 BH-FDR survivors

| market | target | h | base AUC | block AUC | ΔAUC | p | FDR | prec25 lift |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | ---: |
| CAD | `b_hold` | 21 | 0.8209 | 0.8341 | +0.0132 | 0.0868 |  | 2.000x |
| CAD | `xsec_vol_rank_bin` | 21 | 0.8448 | 0.8496 | +0.0048 | 0.00819 | YES | 1.043x |
| USD | `xsec_vol_rank_bin` | 21 | 0.8200 | 0.8241 | +0.0041 | 0.0149 | YES | 1.000x |
| CAD | `xsec_vol_rank_bin` | 8 | 0.8192 | 0.8233 | +0.0041 | 0.000762 | YES | 1.042x |
| CAD | `xsec_vol_rank_bin` | 13 | 0.8353 | 0.8393 | +0.0040 | 0.00462 | YES | 1.000x |
| USD | `xsec_vol_rank_bin` | 13 | 0.8099 | 0.8129 | +0.0030 | 0.0677 |  | 1.048x |
| USD | `xsec_vol_rank_bin` | 8 | 0.7892 | 0.7921 | +0.0028 | 0.0998 |  | 1.150x |
| USD | `b_hold` | 13 | 0.7792 | 0.7794 | +0.0002 | 0.978 |  | 0.833x |
| USD | `b_hold` | 8 | 0.6522 | 0.6467 | -0.0056 | 0.509 |  | 0.920x |
| USD | `b_hold` | 21 | 0.8833 | 0.8771 | -0.0062 | 0.587 |  | 0.720x |
| CAD | `b_hold` | 13 | 0.6913 | 0.6808 | -0.0105 | 0.407 |  | 1.222x |
| CAD | `b_hold` | 8 | 0.6258 | 0.6136 | -0.0121 | 0.189 |  | 1.167x |

### L0-6_effort_result — 3/12 BH-FDR survivors

| market | target | h | base AUC | block AUC | ΔAUC | p | FDR | prec25 lift |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | ---: |
| CAD | `b_hold` | 21 | 0.8209 | 0.8343 | +0.0134 | 0.271 |  | 1.500x |
| CAD | `xsec_vol_rank_bin` | 21 | 0.8448 | 0.8500 | +0.0052 | 0.00466 | YES | 1.043x |
| USD | `b_hold` | 13 | 0.7792 | 0.7838 | +0.0046 | 0.698 |  | 1.000x |
| CAD | `xsec_vol_rank_bin` | 13 | 0.8353 | 0.8396 | +0.0043 | 0.00162 | YES | 1.000x |
| USD | `xsec_vol_rank_bin` | 21 | 0.8200 | 0.8236 | +0.0036 | 0.0195 |  | 1.000x |
| CAD | `xsec_vol_rank_bin` | 8 | 0.8192 | 0.8227 | +0.0036 | 0.0122 | YES | 0.875x |
| USD | `xsec_vol_rank_bin` | 13 | 0.8099 | 0.8133 | +0.0034 | 0.0444 |  | 1.000x |
| USD | `xsec_vol_rank_bin` | 8 | 0.7892 | 0.7918 | +0.0026 | 0.148 |  | 1.100x |
| USD | `b_hold` | 21 | 0.8833 | 0.8745 | -0.0088 | 0.262 |  | 0.560x |
| USD | `b_hold` | 8 | 0.6522 | 0.6427 | -0.0096 | 0.492 |  | 0.840x |
| CAD | `b_hold` | 8 | 0.6258 | 0.6125 | -0.0132 | 0.145 |  | 0.833x |
| CAD | `b_hold` | 13 | 0.6913 | 0.6690 | -0.0223 | 0.26 |  | 1.000x |


## Footer

- START_UTC: 2026-11-13T23:13:09Z
- END_UTC: 2026-11-13T23:36:09Z
- core: 2113.1s of 9000s cap
- NEXT_ALLOWED_RUN_UTC: 2026-11-14T00:06Z (burst < 1 core-h)
- Verdict PROVISIONAL — computed labels are advisory until admin ratification.
- PREDICTIVE DIAGNOSTIC — no economic claim (D-023).

