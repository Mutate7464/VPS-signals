# WI-032 probe — swing-conditioned buy/sell/hold (D-021 §5)

- Generated (UTC): 2026-11-09T02:08:28Z
- Universe: wi016 feature whitelist, |Spearman ρ|>0.7 prune, ≥500 resolved events/group
- BH-FDR alpha 0.05 · 5-seed label-permutation placebo · no model trained

## USD — DECISION: **CLEAR**

- Events: 460,314 · features 41/111 kept · tests 328 · FDR-significant 13

| state | k | h | events | resolved | cleared |
| :--- | ---: | ---: | ---: | ---: | :---: |
| at_bottom | 1.5 | 21 | 50,625 | 49,320 | no |
| at_bottom | 1.5 | 55 | 49,662 | 49,569 | no |
| at_bottom | 2.0 | 21 | 50,625 | 45,606 | yes |
| at_bottom | 2.0 | 55 | 49,662 | 49,323 | no |
| at_top | 1.5 | 21 | 65,222 | 63,957 | yes |
| at_top | 1.5 | 55 | 64,648 | 64,566 | yes |
| at_top | 2.0 | 21 | 65,222 | 59,724 | yes |
| at_top | 2.0 | 55 | 64,648 | 64,375 | yes |

| state | k | h | feature | IC | q | same-sign | placebo |
| :--- | ---: | ---: | :--- | ---: | ---: | :---: | :---: |
| at_bottom | 2.0 | 21 | `bb_width_55` | +0.0266 | 0.0314 | Y | Y |
| at_top | 2.0 | 55 | `bb_width_55` | +0.0260 | 0.0032 | Y | Y |
| at_top | 2.0 | 55 | `bb_width_144` | +0.0247 | 0.0038 | Y | Y |
| at_top | 1.5 | 55 | `bb_width_55` | +0.0245 | 0.0038 | Y | Y |
| at_top | 2.0 | 21 | `bb_width_55` | +0.0229 | 0.0120 | Y | Y |
| at_top | 1.5 | 21 | `bb_width_55` | +0.0223 | 0.0120 | Y | Y |
| at_top | 2.0 | 55 | `atr_pct_3` | +0.0214 | 0.0149 | Y | Y |
| at_top | 2.0 | 55 | `pct_from_low_233` | +0.0203 | 0.0314 | Y | Y |
| at_top | 1.5 | 55 | `bb_width_144` | +0.0202 | 0.0285 | Y | Y |
| at_top | 2.0 | 55 | `bb_width_21` | +0.0202 | 0.0285 | Y | Y |
| at_top | 2.0 | 21 | `bb_width_144` | +0.0196 | 0.0445 | Y | Y |
| at_top | 1.5 | 55 | `range_compression_8_55` | -0.0190 | 0.0314 | Y | Y |
| at_top | 1.5 | 21 | `range_compression_8_55` | -0.0176 | 0.0494 | Y | Y |

## CAD — DECISION: **CLEAR**

- Events: 252,420 · features 41/111 kept · tests 328 · FDR-significant 19

| state | k | h | events | resolved | cleared |
| :--- | ---: | ---: | ---: | ---: | :---: |
| at_bottom | 1.5 | 21 | 28,293 | 27,245 | no |
| at_bottom | 1.5 | 55 | 27,771 | 27,705 | yes |
| at_bottom | 2.0 | 21 | 28,293 | 24,652 | no |
| at_bottom | 2.0 | 55 | 27,771 | 27,455 | yes |
| at_top | 1.5 | 21 | 35,257 | 34,308 | yes |
| at_top | 1.5 | 55 | 34,889 | 34,834 | yes |
| at_top | 2.0 | 21 | 35,257 | 31,816 | yes |
| at_top | 2.0 | 55 | 34,889 | 34,639 | yes |

| state | k | h | feature | IC | q | same-sign | placebo |
| :--- | ---: | ---: | :--- | ---: | ---: | :---: | :---: |
| at_top | 1.5 | 55 | `bb_width_55` | +0.0455 | 0.0000 | Y | Y |
| at_top | 1.5 | 21 | `bb_width_55` | +0.0431 | 0.0000 | Y | Y |
| at_top | 2.0 | 55 | `bb_width_55` | +0.0370 | 0.0001 | Y | Y |
| at_top | 1.5 | 55 | `atr_pct_3` | +0.0359 | 0.0002 | Y | Y |
| at_bottom | 1.5 | 55 | `bb_width_233` | -0.0350 | 0.0115 | Y | Y |
| at_top | 1.5 | 21 | `atr_pct_3` | +0.0336 | 0.0009 | Y | Y |
| at_top | 2.0 | 21 | `bb_width_55` | +0.0330 | 0.0016 | Y | Y |
| at_top | 1.5 | 55 | `pct_from_high_233` | -0.0324 | 0.0015 | Y | Y |
| at_bottom | 2.0 | 55 | `pct_from_low_233` | -0.0310 | 0.0325 | Y | Y |
| at_bottom | 1.5 | 55 | `pct_from_low_233` | -0.0294 | 0.0430 | Y | Y |
| at_top | 1.5 | 21 | `pct_from_high_233` | -0.0294 | 0.0072 | Y | Y |
| at_top | 2.0 | 55 | `pct_from_high_233` | -0.0279 | 0.0082 | Y | Y |
| at_top | 2.0 | 55 | `adx_144` | -0.0277 | 0.0078 | Y | Y |
| at_top | 2.0 | 21 | `adx_144` | -0.0256 | 0.0273 | Y | Y |
| at_top | 2.0 | 55 | `vwap_zscore_102` | +0.0254 | 0.0200 | Y | Y |

