# WI-011 Step 5 — per-symbol (time-series) momentum probe and TS-vs-CS decomposition (CAD)

- Generated (UTC): 2026-10-25T21:36:32Z
- Panel: 707,899 rows · 315 symbols · 2711 dates (2016-01-04 → 2026-10-21)
- Evaluation order: TS rule first, then its cross-sectional counterpart on the *same* trailing return, so the comparison varies the framing (own level vs within-date rank) and not the information content. No cross-sectional ranking of any model score is involved, and no model is trained.

TS_RULES: `ts_up_20` (own trailing 20d return > 0), `ts_down_20` (own trailing 20d return < 0), `ts_strong_up_20` (own trailing 20d return / (vol_20*sqrt(20)) >= +0.5), `ts_strong_down_20` (own trailing 20d return / (vol_20*sqrt(20)) <= -0.5), `cs_up_20` (own trailing 20d return above the same-date median), `cs_down_20` (own trailing 20d return below the same-date median), `cs_top_quartile_20` (within-date top quartile of the trailing 20d return), `cs_bottom_quartile_20` (within-date bottom quartile of the trailing 20d return), `ts_up_60` (own trailing 60d return > 0), `ts_down_60` (own trailing 60d return < 0), `ts_strong_up_60` (own trailing 60d return / (vol_20*sqrt(60)) >= +0.5), `ts_strong_down_60` (own trailing 60d return / (vol_20*sqrt(60)) <= -0.5), `cs_up_60` (own trailing 60d return above the same-date median), `cs_down_60` (own trailing 60d return below the same-date median), `cs_top_quartile_60` (within-date top quartile of the trailing 60d return), `cs_bottom_quartile_60` (within-date bottom quartile of the trailing 60d return), `ts_up_120` (own trailing 120d return > 0), `ts_down_120` (own trailing 120d return < 0), `ts_strong_up_120` (own trailing 120d return / (vol_20*sqrt(120)) >= +0.5), `ts_strong_down_120` (own trailing 120d return / (vol_20*sqrt(120)) <= -0.5), `cs_up_120` (own trailing 120d return above the same-date median), `cs_down_120` (own trailing 120d return below the same-date median), `cs_top_quartile_120` (within-date top quartile of the trailing 120d return), `cs_bottom_quartile_120` (within-date bottom quartile of the trailing 120d return)

TS_WINDOWS: 20,60,120 trading days · volatility-scaled strength threshold |z| >= 0.5 with z = own trailing return / (vol_20 * sqrt(window))

HORIZONS: 1,2,5,10,15,20,60,120

PURGE_TD: max(20, horizon) trading days (WI-009 `PurgedWalkForwardSplit` over the sorted unique date array) — per horizon: 1d→20td, 2d→20td, 5d→20td, 10d→20td, 15d→20td, 20d→20td, 60d→60td, 120d→120td

SUBWINDOWS: 2 — 2016-01-04→2021-05-26 and 2021-05-27→2026-10-21 (same disjoint halves as Step 4). `STABLE_SIGN` = same sign in both halves with |t| > 2; `STABLE_SIGN_WITHIN` applies the same clause to the within-date component.

Decomposition columns: `mean` = raw mean forward bps; `market` = mean of each firing row's own date all-name mean (the drift the rule inherits); `within` = mean deviation from that date's mean (the 'which name' part); `t_within` = t across dates on the per-date deviation.

## TS_VS_CS_DECOMPOSITION

For each matched pair, the *same* trailing-return element is evaluated as a TS level rule and as a cross-sectional rank rule. `Δ(TS−CS)` is their raw-mean difference in bps; the `within` columns say how much of each rule is a 'which name' effect rather than a market-drift effect.

### Horizon 1d

| Element | TS rule | TS mean | TS market | TS within (t) | CS rule | CS mean | CS market | CS within (t) | Δ(TS−CS) mean bps | TS stable | CS stable |
| :--- | :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| trailing 20d return (w=20) | `ts_up_20` | +8.1 | +9.6 | -1.6 (-2.41) | `cs_up_20` | +6.8 | +9.0 | -2.2 (-2.84) | +1.2 | stable | stable |
| vol-scaled trailing 20d return (w=20) | `ts_strong_up_20` | +7.7 | +9.7 | -2.0 (-1.22) | `cs_top_quartile_20` | +7.3 | +9.0 | -1.6 (-1.17) | +0.4 | single-window | single-window |
| trailing 20d return (down side) (w=20) | `ts_down_20` | +10.3 | +8.1 | +2.1 (+3.27) | `cs_bottom_quartile_20` | +14.5 | +9.0 | +5.6 (+4.04) | -4.3 | stable | stable |
| trailing 60d return (w=60) | `ts_up_60` | +7.6 | +8.9 | -1.3 (-2.96) | `cs_up_60` | +7.9 | +9.0 | -1.1 (-1.50) | -0.2 | stable | stable |
| vol-scaled trailing 60d return (w=60) | `ts_strong_up_60` | +7.8 | +8.9 | -1.1 (-1.55) | `cs_top_quartile_60` | +8.6 | +9.0 | -0.4 (-0.27) | -0.8 | stable | stable |
| trailing 60d return (down side) (w=60) | `ts_down_60` | +11.0 | +9.1 | +1.9 (+2.08) | `cs_bottom_quartile_60` | +13.3 | +9.0 | +4.3 (+3.08) | -2.3 | stable | stable |
| trailing 120d return (w=120) | `ts_up_120` | +8.5 | +8.7 | -0.2 (-0.92) | `cs_up_120` | +9.2 | +9.0 | +0.2 (+0.13) | -0.7 | stable | stable |
| vol-scaled trailing 120d return (w=120) | `ts_strong_up_120` | +8.4 | +8.6 | -0.1 (-0.39) | `cs_top_quartile_120` | +10.2 | +9.0 | +1.2 (+0.83) | -1.8 | stable | stable |
| trailing 120d return (down side) (w=120) | `ts_down_120` | +10.0 | +9.6 | +0.4 (+0.05) | `cs_bottom_quartile_120` | +11.3 | +9.0 | +2.3 (+1.66) | -1.3 | stable | stable |

### Horizon 2d

| Element | TS rule | TS mean | TS market | TS within (t) | CS rule | CS mean | CS market | CS within (t) | Δ(TS−CS) mean bps | TS stable | CS stable |
| :--- | :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| trailing 20d return (w=20) | `ts_up_20` | +16.1 | +18.9 | -2.8 (-3.10) | `cs_up_20` | +14.2 | +17.8 | -3.6 (-3.30) | +1.9 | stable | stable |
| vol-scaled trailing 20d return (w=20) | `ts_strong_up_20` | +15.3 | +19.0 | -3.6 (-1.61) | `cs_top_quartile_20` | +15.4 | +17.8 | -2.4 (-1.18) | -0.1 | stable | stable |
| trailing 20d return (down side) (w=20) | `ts_down_20` | +19.9 | +16.4 | +3.5 (+3.61) | `cs_bottom_quartile_20` | +27.5 | +17.8 | +9.7 (+4.84) | -7.5 | stable | stable |
| trailing 60d return (w=60) | `ts_up_60` | +15.2 | +17.4 | -2.1 (-3.34) | `cs_up_60` | +15.9 | +17.8 | -1.9 (-1.75) | -0.7 | stable | stable |
| vol-scaled trailing 60d return (w=60) | `ts_strong_up_60` | +15.8 | +17.3 | -1.6 (-1.51) | `cs_top_quartile_60` | +17.9 | +17.8 | +0.1 (+0.03) | -2.1 | stable | stable |
| trailing 60d return (down side) (w=60) | `ts_down_60` | +21.7 | +18.4 | +3.3 (+2.24) | `cs_bottom_quartile_60` | +25.3 | +17.8 | +7.5 (+3.68) | -3.6 | stable | stable |
| trailing 120d return (w=120) | `ts_up_120` | +16.9 | +17.1 | -0.1 (-0.72) | `cs_up_120` | +18.4 | +17.9 | +0.6 (+0.40) | -1.5 | stable | stable |
| vol-scaled trailing 120d return (w=120) | `ts_strong_up_120` | +16.9 | +16.8 | +0.0 (-0.37) | `cs_top_quartile_120` | +21.1 | +17.8 | +3.3 (+1.51) | -4.2 | stable | stable |
| trailing 120d return (down side) (w=120) | `ts_down_120` | +19.8 | +19.2 | +0.6 (+0.01) | `cs_bottom_quartile_120` | +21.4 | +17.8 | +3.6 (+1.75) | -1.6 | stable | stable |

### Horizon 5d

| Element | TS rule | TS mean | TS market | TS within (t) | CS rule | CS mean | CS market | CS within (t) | Δ(TS−CS) mean bps | TS stable | CS stable |
| :--- | :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| trailing 20d return (w=20) | `ts_up_20` | +38.7 | +45.1 | -6.4 (-4.52) | `cs_up_20` | +37.3 | +44.5 | -7.1 (-4.28) | +1.4 | stable | stable |
| vol-scaled trailing 20d return (w=20) | `ts_strong_up_20` | +37.0 | +45.2 | -8.2 (-0.32) | `cs_top_quartile_20` | +40.6 | +44.5 | -3.9 (-1.24) | -3.6 | stable | stable |
| trailing 20d return (down side) (w=20) | `ts_down_20` | +51.5 | +43.8 | +7.8 (+4.52) | `cs_bottom_quartile_20` | +64.6 | +44.4 | +20.1 (+6.55) | -13.0 | stable | stable |
| trailing 60d return (w=60) | `ts_up_60` | +38.0 | +42.1 | -4.0 (-4.11) | `cs_up_60` | +40.8 | +44.5 | -3.7 (-2.11) | -2.8 | stable | stable |
| vol-scaled trailing 60d return (w=60) | `ts_strong_up_60` | +39.9 | +42.5 | -2.6 (-2.11) | `cs_top_quartile_60` | +46.5 | +44.5 | +2.0 (+0.62) | -6.6 | stable | stable |
| trailing 60d return (down side) (w=60) | `ts_down_60` | +54.3 | +48.1 | +6.2 (+1.69) | `cs_bottom_quartile_60` | +58.9 | +44.5 | +14.4 (+4.35) | -4.6 | stable | stable |
| trailing 120d return (w=120) | `ts_up_120` | +42.6 | +41.8 | +0.8 (-0.10) | `cs_up_120` | +47.7 | +44.6 | +3.0 (+1.48) | -5.0 | stable | stable |
| vol-scaled trailing 120d return (w=120) | `ts_strong_up_120` | +43.0 | +41.2 | +1.9 (+0.17) | `cs_top_quartile_120` | +55.4 | +44.5 | +11.0 (+3.19) | -12.4 | stable | stable |
| trailing 120d return (down side) (w=120) | `ts_down_120` | +49.0 | +49.3 | -0.3 (-0.55) | `cs_bottom_quartile_120` | +51.1 | +44.5 | +6.6 (+2.02) | -2.1 | stable | stable |

### Horizon 10d

| Element | TS rule | TS mean | TS market | TS within (t) | CS rule | CS mean | CS market | CS within (t) | Δ(TS−CS) mean bps | TS stable | CS stable |
| :--- | :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| trailing 20d return (w=20) | `ts_up_20` | +83.9 | +90.7 | -6.8 (-2.09) | `cs_up_20` | +83.8 | +89.6 | -5.8 (-2.81) | +0.1 | stable | stable |
| vol-scaled trailing 20d return (w=20) | `ts_strong_up_20` | +82.0 | +90.9 | -9.0 (+0.41) | `cs_top_quartile_20` | +93.8 | +89.6 | +4.2 (+0.86) | -11.8 | stable | stable |
| trailing 20d return (down side) (w=20) | `ts_down_20` | +96.9 | +88.4 | +8.5 (+3.61) | `cs_bottom_quartile_20` | +114.1 | +89.6 | +24.5 (+6.19) | -17.2 | stable | stable |
| trailing 60d return (w=60) | `ts_up_60` | +77.6 | +83.7 | -6.1 (-5.05) | `cs_up_60` | +84.9 | +89.6 | -4.8 (-2.13) | -7.3 | stable | stable |
| vol-scaled trailing 60d return (w=60) | `ts_strong_up_60` | +81.1 | +84.4 | -3.4 (-2.39) | `cs_top_quartile_60` | +98.8 | +89.7 | +9.1 (+2.01) | -17.7 | stable | stable |
| trailing 60d return (down side) (w=60) | `ts_down_60` | +108.3 | +98.6 | +9.7 (+1.08) | `cs_bottom_quartile_60` | +114.1 | +89.7 | +24.4 (+5.60) | -5.8 | stable | stable |
| trailing 120d return (w=120) | `ts_up_120` | +85.0 | +82.6 | +2.5 (+0.25) | `cs_up_120` | +97.1 | +89.8 | +7.2 (+2.49) | -12.0 | stable | stable |
| vol-scaled trailing 120d return (w=120) | `ts_strong_up_120` | +87.3 | +81.6 | +5.8 (-0.01) | `cs_top_quartile_120` | +113.9 | +89.6 | +24.2 (+5.06) | -26.5 | stable | stable |
| trailing 120d return (down side) (w=120) | `ts_down_120` | +99.9 | +102.0 | -2.0 (-0.94) | `cs_bottom_quartile_120` | +98.8 | +89.6 | +9.2 (+2.19) | +1.1 | stable | stable |

### Horizon 15d

| Element | TS rule | TS mean | TS market | TS within (t) | CS rule | CS mean | CS market | CS within (t) | Δ(TS−CS) mean bps | TS stable | CS stable |
| :--- | :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| trailing 20d return (w=20) | `ts_up_20` | +126.3 | +133.2 | -6.9 (-3.33) | `cs_up_20` | +131.5 | +136.0 | -4.5 (-2.04) | -5.2 | stable | stable |
| vol-scaled trailing 20d return (w=20) | `ts_strong_up_20` | +123.4 | +132.4 | -9.0 (-0.93) | `cs_top_quartile_20` | +149.5 | +136.0 | +13.6 (+2.38) | -26.1 | stable | stable |
| trailing 20d return (down side) (w=20) | `ts_down_20` | +147.8 | +139.9 | +8.0 (+3.25) | `cs_bottom_quartile_20` | +164.4 | +136.0 | +28.5 (+5.90) | -16.6 | stable | stable |
| trailing 60d return (w=60) | `ts_up_60` | +117.8 | +125.2 | -7.3 (-5.75) | `cs_up_60` | +129.8 | +136.0 | -6.2 (-2.32) | -12.0 | stable | stable |
| vol-scaled trailing 60d return (w=60) | `ts_strong_up_60` | +124.2 | +126.0 | -1.8 (-3.88) | `cs_top_quartile_60` | +154.8 | +136.1 | +18.7 (+3.31) | -30.6 | stable | stable |
| trailing 60d return (down side) (w=60) | `ts_down_60` | +164.5 | +152.4 | +12.1 (+0.71) | `cs_bottom_quartile_60` | +170.0 | +136.1 | +34.0 (+6.28) | -5.5 | stable | stable |
| trailing 120d return (w=120) | `ts_up_120` | +126.7 | +123.2 | +3.5 (+0.39) | `cs_up_120` | +147.0 | +136.4 | +10.6 (+2.97) | -20.3 | stable | stable |
| vol-scaled trailing 120d return (w=120) | `ts_strong_up_120` | +130.5 | +121.7 | +8.8 (-0.59) | `cs_top_quartile_120` | +172.8 | +136.1 | +36.6 (+6.24) | -42.3 | stable | stable |
| trailing 120d return (down side) (w=120) | `ts_down_120` | +155.7 | +158.3 | -2.6 (-1.36) | `cs_bottom_quartile_120` | +150.9 | +136.1 | +14.8 (+2.72) | +4.8 | stable | stable |

### Horizon 20d

| Element | TS rule | TS mean | TS market | TS within (t) | CS rule | CS mean | CS market | CS within (t) | Δ(TS−CS) mean bps | TS stable | CS stable |
| :--- | :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| trailing 20d return (w=20) | `ts_up_20` | +167.5 | +175.1 | -7.6 (-3.93) | `cs_up_20` | +176.7 | +181.4 | -4.7 (-2.04) | -9.2 | stable | stable |
| vol-scaled trailing 20d return (w=20) | `ts_strong_up_20` | +163.2 | +173.9 | -10.7 (-3.04) | `cs_top_quartile_20` | +201.5 | +181.4 | +20.1 (+3.08) | -38.4 | stable | stable |
| trailing 20d return (down side) (w=20) | `ts_down_20` | +198.1 | +189.8 | +8.3 (+3.32) | `cs_bottom_quartile_20` | +212.4 | +181.4 | +31.0 (+5.96) | -14.3 | stable | stable |
| trailing 60d return (w=60) | `ts_up_60` | +158.6 | +166.3 | -7.8 (-5.91) | `cs_up_60` | +176.3 | +181.4 | -5.2 (-1.83) | -17.7 | stable | stable |
| vol-scaled trailing 60d return (w=60) | `ts_strong_up_60` | +167.6 | +167.7 | -0.1 (-4.44) | `cs_top_quartile_60` | +210.8 | +181.5 | +29.3 (+4.58) | -43.1 | stable | stable |
| trailing 60d return (down side) (w=60) | `ts_down_60` | +217.4 | +204.2 | +13.1 (+0.17) | `cs_bottom_quartile_60` | +221.3 | +181.5 | +39.9 (+6.55) | -4.0 | stable | stable |
| trailing 120d return (w=120) | `ts_up_120` | +169.0 | +164.1 | +4.9 (+0.97) | `cs_up_120` | +195.6 | +182.0 | +13.6 (+3.45) | -26.6 | stable | stable |
| vol-scaled trailing 120d return (w=120) | `ts_strong_up_120` | +173.6 | +162.0 | +11.5 (-0.39) | `cs_top_quartile_120` | +231.9 | +181.7 | +50.2 (+7.67) | -58.3 | stable | stable |
| trailing 120d return (down side) (w=120) | `ts_down_120` | +208.3 | +211.8 | -3.5 (-1.80) | `cs_bottom_quartile_120` | +200.8 | +181.7 | +19.1 (+3.06) | +7.5 | stable | stable |

### Horizon 60d

| Element | TS rule | TS mean | TS market | TS within (t) | CS rule | CS mean | CS market | CS within (t) | Δ(TS−CS) mean bps | TS stable | CS stable |
| :--- | :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| trailing 20d return (w=20) | `ts_up_20` | +498.7 | +522.9 | -24.3 (-6.62) | `cs_up_20` | +533.5 | +546.8 | -13.3 (-2.48) | -34.8 | stable | stable |
| vol-scaled trailing 20d return (w=20) | `ts_strong_up_20` | +492.2 | +517.5 | -25.3 (-1.40) | `cs_top_quartile_20` | +607.7 | +546.7 | +60.9 (+5.38) | -115.5 | stable | stable |
| trailing 20d return (down side) (w=20) | `ts_down_20` | +600.9 | +578.5 | +22.4 (+2.61) | `cs_bottom_quartile_20` | +637.6 | +546.7 | +90.9 (+8.87) | -36.7 | stable | stable |
| trailing 60d return (w=60) | `ts_up_60` | +492.6 | +509.7 | -17.0 (-4.74) | `cs_up_60` | +546.0 | +546.9 | -1.0 (-0.49) | -53.3 | stable | stable |
| vol-scaled trailing 60d return (w=60) | `ts_strong_up_60` | +495.9 | +505.4 | -9.5 (-4.34) | `cs_top_quartile_60` | +649.8 | +546.7 | +103.2 (+8.54) | -154.0 | stable | stable |
| trailing 60d return (down side) (w=60) | `ts_down_60` | +629.3 | +603.3 | +26.0 (+1.93) | `cs_bottom_quartile_60` | +635.8 | +546.6 | +89.2 (+7.81) | -6.5 | stable | stable |
| trailing 120d return (w=120) | `ts_up_120` | +537.8 | +513.2 | +24.5 (+4.04) | `cs_up_120` | +598.7 | +548.7 | +50.0 (+7.96) | -61.0 | stable | stable |
| vol-scaled trailing 120d return (w=120) | `ts_strong_up_120` | +542.4 | +507.4 | +34.9 (+2.57) | `cs_top_quartile_120` | +712.3 | +548.5 | +163.8 (+14.98) | -169.9 | stable | stable |
| trailing 120d return (down side) (w=120) | `ts_down_120` | +576.4 | +608.1 | -31.7 (-3.25) | `cs_bottom_quartile_120` | +571.3 | +548.5 | +22.8 (+2.17) | +5.1 | stable | stable |

### Horizon 120d

| Element | TS rule | TS mean | TS market | TS within (t) | CS rule | CS mean | CS market | CS within (t) | Δ(TS−CS) mean bps | TS stable | CS stable |
| :--- | :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| trailing 20d return (w=20) | `ts_up_20` | +1048.9 | +1074.4 | -25.5 (-1.28) | `cs_up_20` | +1105.1 | +1102.3 | +2.8 (-0.18) | -56.2 | stable | stable |
| vol-scaled trailing 20d return (w=20) | `ts_strong_up_20` | +1042.8 | +1069.5 | -26.7 (+2.23) | `cs_top_quartile_20` | +1286.7 | +1101.5 | +185.2 (+10.36) | -243.9 | stable | stable |
| trailing 20d return (down side) (w=20) | `ts_down_20` | +1154.2 | +1140.6 | +13.6 (+1.77) | `cs_bottom_quartile_20` | +1251.4 | +1101.4 | +150.0 (+9.32) | -97.2 | stable | stable |
| trailing 60d return (w=60) | `ts_up_60` | +1084.5 | +1071.2 | +13.3 (+0.86) | `cs_up_60` | +1161.1 | +1103.7 | +57.5 (+5.14) | -76.7 | stable | stable |
| vol-scaled trailing 60d return (w=60) | `ts_strong_up_60` | +1118.9 | +1082.5 | +36.5 (+0.72) | `cs_top_quartile_60` | +1397.3 | +1103.0 | +294.3 (+16.79) | -278.4 | stable | stable |
| trailing 60d return (down side) (w=60) | `ts_down_60` | +1130.7 | +1154.0 | -23.3 (-2.41) | `cs_bottom_quartile_60` | +1179.9 | +1103.0 | +76.9 (+4.37) | -49.2 | stable | stable |
| trailing 120d return (w=120) | `ts_up_120` | +1128.0 | +1062.0 | +66.0 (+5.56) | `cs_up_120` | +1238.5 | +1106.1 | +132.4 (+13.46) | -110.5 | stable | stable |
| vol-scaled trailing 120d return (w=120) | `ts_strong_up_120` | +1168.2 | +1061.6 | +106.5 (+4.94) | `cs_top_quartile_120` | +1491.9 | +1105.6 | +386.4 (+22.58) | -323.8 | stable | stable |
| trailing 120d return (down side) (w=120) | `ts_down_120` | +1072.5 | +1179.8 | -107.3 (-9.21) | `cs_bottom_quartile_120` | +1075.9 | +1105.6 | -29.6 (-1.44) | -3.4 | stable | stable |

## Horizon 1d — TS/CS rule expectancy (sorted by |within bps|)

| Rule | mean bps | market bps | within bps | t_within | t_date | hit% | n | dates | purged mean bps (n, dates) | stability | stability (within) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |
| `ch52_low` | +15.8 | +8.4 | +7.4 | +3.29 | +4.79 | 47.8% | 96,810 | 2,710 | +18.9 (54,150, 1,622) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_20` | +14.5 | +9.0 | +5.6 | +4.04 | +4.96 | 48.8% | 177,544 | 2,710 | +15.5 (114,409, 1,622) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_down_20` | +11.7 | +7.2 | +4.5 | +3.93 | +5.47 | 49.7% | 179,743 | 2,710 | +15.5 (111,900, 1,622) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_60` | +13.3 | +9.0 | +4.3 | +3.08 | +4.52 | 48.3% | 176,628 | 2,710 | +14.5 (113,665, 1,622) | STABLE_SIGN | single-window |
| `ts_strong_down_60` | +12.9 | +9.0 | +3.9 | +2.57 | +4.69 | 49.1% | 154,643 | 2,709 | +16.3 (93,648, 1,621) | STABLE_SIGN | single-window |
| `below_ma_50` | +10.6 | +8.3 | +2.4 | +3.13 | +4.97 | 49.2% | 299,491 | 2,710 | +12.8 (186,812, 1,622) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_120` | +11.3 | +9.0 | +2.3 | +1.66 | +3.83 | 47.8% | 175,228 | 2,710 | +12.4 (112,565, 1,622) | STABLE_SIGN | single-window |
| `cs_down_20` | +11.2 | +9.0 | +2.2 | +2.92 | +4.69 | 49.5% | 352,046 | 2,710 | +12.6 (227,205, 1,622) | STABLE_SIGN | single-window |
| `cs_up_20` | +6.8 | +9.0 | -2.2 | -2.84 | +3.27 | 49.4% | 352,044 | 2,710 | +9.4 (227,200, 1,622) | STABLE_SIGN | single-window |
| `ts_down_20` | +10.3 | +8.1 | +2.1 | +3.27 | +5.07 | 49.4% | 309,573 | 2,710 | +13.1 (196,214, 1,622) | STABLE_SIGN | single-window |
| `ts_strong_up_20` | +7.7 | +9.7 | -2.0 | -1.22 | +2.54 | 49.9% | 262,074 | 2,704 | +8.8 (172,880, 1,622) | single-window | single-window |
| `ts_strong_down_120` | +11.2 | +9.2 | +2.0 | +1.13 | +3.80 | 48.7% | 134,414 | 2,710 | +14.3 (82,397, 1,622) | STABLE_SIGN | single-window |
| `ts_down_60` | +11.0 | +9.1 | +1.9 | +2.08 | +4.57 | 49.1% | 282,136 | 2,710 | +13.8 (173,707, 1,622) | STABLE_SIGN | single-window |
| `above_ma_50` | +7.8 | +9.5 | -1.7 | -3.60 | +2.61 | 49.7% | 403,498 | 2,710 | +9.8 (266,241, 1,622) | single-window | single-window |
| `cs_top_quartile_20` | +7.3 | +9.0 | -1.6 | -1.17 | +2.90 | 48.7% | 177,528 | 2,710 | +10.4 (114,407, 1,622) | single-window | single-window |
| `ts_up_20` | +8.1 | +9.6 | -1.6 | -2.41 | +3.14 | 49.6% | 391,881 | 2,709 | +9.3 (257,126, 1,622) | STABLE_SIGN | single-window |
| `ch52_high` | +7.0 | +8.4 | -1.5 | -2.46 | +2.68 | 50.8% | 229,333 | 2,706 | +8.9 (152,430, 1,622) | single-window | single-window |
| `ts_up_60` | +7.6 | +8.9 | -1.3 | -2.96 | +3.25 | 49.8% | 418,006 | 2,710 | +9.3 (277,826, 1,622) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_top_quartile_120` | +10.2 | +9.0 | +1.2 | +0.83 | +3.86 | 49.2% | 175,223 | 2,710 | +12.8 (112,563, 1,622) | STABLE_SIGN | single-window |
| `cs_down_60` | +10.2 | +9.0 | +1.2 | +1.59 | +4.29 | 49.2% | 350,162 | 2,710 | +11.9 (225,654, 1,622) | STABLE_SIGN | single-window |
| `cs_up_60` | +7.9 | +9.0 | -1.1 | -1.50 | +3.71 | 49.7% | 350,159 | 2,710 | +10.2 (225,653, 1,622) | STABLE_SIGN | single-window |
| `ts_strong_up_60` | +7.8 | +8.9 | -1.1 | -1.55 | +3.07 | 50.1% | 292,786 | 2,709 | +9.2 (196,330, 1,622) | STABLE_SIGN | single-window |
| `mom_neg` | +10.2 | +10.9 | -0.7 | -1.31 | +2.99 | 48.2% | 240,006 | 2,710 | +12.0 (144,827, 1,622) | single-window | single-window |
| `mom_pos` | +8.4 | +8.0 | +0.5 | +0.16 | +4.44 | 50.2% | 442,535 | 2,710 | +10.8 (292,273, 1,622) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_down_120` | +10.0 | +9.6 | +0.4 | +0.05 | +3.64 | 48.7% | 260,670 | 2,710 | +12.3 (158,462, 1,622) | STABLE_SIGN | single-window |
| `cs_top_quartile_60` | +8.6 | +9.0 | -0.4 | -0.27 | +3.29 | 49.0% | 176,624 | 2,710 | +11.1 (113,663, 1,622) | STABLE_SIGN | single-window |
| `ts_up_120` | +8.5 | +8.7 | -0.2 | -0.92 | +4.24 | 50.0% | 434,538 | 2,710 | +10.5 (288,813, 1,622) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_up_120` | +9.2 | +9.0 | +0.2 | +0.13 | +4.29 | 50.0% | 347,326 | 2,710 | +11.7 (223,356, 1,622) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_up_120` | +8.4 | +8.6 | -0.1 | -0.39 | +3.70 | 50.2% | 315,526 | 2,710 | +10.5 (213,061, 1,622) | STABLE_SIGN | single-window |
| `cs_down_120` | +9.0 | +9.0 | -0.0 | +0.01 | +3.75 | 48.9% | 347,325 | 2,710 | +10.7 (223,356, 1,622) | STABLE_SIGN | single-window |

## Horizon 2d — TS/CS rule expectancy (sorted by |within bps|)

| Rule | mean bps | market bps | within bps | t_within | t_date | hit% | n | dates | purged mean bps (n, dates) | stability | stability (within) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |
| `ch52_low` | +29.2 | +16.4 | +12.8 | +3.74 | +5.99 | 49.1% | 96,767 | 2,709 | +35.9 (53,999, 1,617) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_20` | +27.5 | +17.8 | +9.7 | +4.84 | +6.51 | 50.2% | 177,465 | 2,709 | +29.6 (114,046, 1,617) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_down_60` | +25.4 | +17.9 | +7.5 | +3.24 | +6.25 | 50.6% | 154,566 | 2,708 | +31.8 (93,433, 1,616) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_60` | +25.3 | +17.8 | +7.5 | +3.68 | +5.90 | 49.7% | 176,549 | 2,709 | +27.8 (113,306, 1,617) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_down_20` | +22.5 | +15.1 | +7.4 | +4.18 | +6.95 | 51.1% | 179,629 | 2,709 | +30.2 (111,598, 1,617) | STABLE_SIGN | single-window |
| `cs_down_20` | +21.5 | +17.8 | +3.7 | +3.40 | +6.31 | 50.8% | 351,889 | 2,709 | +24.5 (226,487, 1,617) | STABLE_SIGN | single-window |
| `below_ma_50` | +20.6 | +16.9 | +3.7 | +3.27 | +6.44 | 50.5% | 299,316 | 2,709 | +25.1 (186,343, 1,617) | STABLE_SIGN | single-window |
| `ts_strong_up_20` | +15.3 | +19.0 | -3.6 | -1.61 | +4.20 | 51.0% | 261,971 | 2,703 | +16.9 (172,234, 1,617) | STABLE_SIGN | single-window |
| `cs_up_20` | +14.2 | +17.8 | -3.6 | -3.30 | +4.84 | 50.5% | 351,887 | 2,709 | +19.0 (226,482, 1,617) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_120` | +21.4 | +17.8 | +3.6 | +1.75 | +4.97 | 49.0% | 175,149 | 2,709 | +23.2 (112,208, 1,617) | STABLE_SIGN | single-window |
| `ts_down_20` | +19.9 | +16.4 | +3.5 | +3.61 | +6.66 | 50.7% | 309,406 | 2,709 | +25.9 (195,683, 1,617) | STABLE_SIGN | single-window |
| `ts_down_60` | +21.7 | +18.4 | +3.3 | +2.24 | +6.04 | 50.4% | 281,992 | 2,709 | +27.2 (173,272, 1,617) | STABLE_SIGN | single-window |
| `cs_top_quartile_120` | +21.1 | +17.8 | +3.3 | +1.51 | +5.65 | 50.4% | 175,144 | 2,709 | +26.5 (112,206, 1,617) | STABLE_SIGN | single-window |
| `ts_strong_down_120` | +20.9 | +18.0 | +2.9 | +0.99 | +4.88 | 49.9% | 134,360 | 2,709 | +26.6 (82,190, 1,617) | STABLE_SIGN | single-window |
| `ts_up_20` | +16.1 | +18.9 | -2.8 | -3.10 | +4.47 | 50.8% | 391,733 | 2,708 | +18.3 (256,223, 1,617) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `above_ma_50` | +15.9 | +18.5 | -2.6 | -3.97 | +4.06 | 50.9% | 403,358 | 2,709 | +19.5 (265,277, 1,617) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_top_quartile_20` | +15.4 | +17.8 | -2.4 | -1.18 | +4.33 | 49.7% | 177,449 | 2,709 | +20.6 (114,044, 1,617) | STABLE_SIGN | single-window |
| `ch52_high` | +14.4 | +16.6 | -2.2 | -2.57 | +4.92 | 52.1% | 229,252 | 2,705 | +17.9 (151,931, 1,617) | STABLE_SIGN | single-window |
| `ts_up_60` | +15.2 | +17.4 | -2.1 | -3.34 | +4.88 | 51.0% | 417,835 | 2,709 | +18.4 (276,832, 1,617) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_down_60` | +19.9 | +17.8 | +2.1 | +1.88 | +5.78 | 50.6% | 350,005 | 2,709 | +23.2 (224,939, 1,617) | STABLE_SIGN | single-window |
| `cs_up_60` | +15.9 | +17.8 | -1.9 | -1.75 | +5.40 | 50.9% | 350,002 | 2,709 | +20.5 (224,938, 1,617) | STABLE_SIGN | single-window |
| `ts_strong_up_60` | +15.8 | +17.3 | -1.6 | -1.51 | +4.55 | 51.3% | 292,679 | 2,708 | +18.5 (195,584, 1,617) | STABLE_SIGN | single-window |
| `mom_neg` | +20.2 | +21.5 | -1.3 | -1.64 | +4.17 | 49.4% | 239,923 | 2,709 | +23.4 (144,339, 1,617) | STABLE_SIGN | single-window |
| `mom_pos` | +16.7 | +15.9 | +0.8 | +0.16 | +6.27 | 51.5% | 442,304 | 2,709 | +21.5 (291,379, 1,617) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_down_120` | +19.8 | +19.2 | +0.6 | +0.01 | +5.01 | 49.9% | 260,557 | 2,709 | +23.9 (157,963, 1,617) | STABLE_SIGN | single-window |
| `cs_up_120` | +18.4 | +17.9 | +0.6 | +0.40 | +6.17 | 51.2% | 347,169 | 2,709 | +23.4 (222,649, 1,617) | STABLE_SIGN | single-window |
| `cs_down_120` | +17.6 | +17.9 | -0.3 | -0.17 | +5.08 | 50.2% | 347,168 | 2,709 | +20.8 (222,649, 1,617) | STABLE_SIGN | single-window |
| `ts_up_120` | +16.9 | +17.1 | -0.1 | -0.72 | +6.12 | 51.2% | 434,337 | 2,709 | +21.1 (287,898, 1,617) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_top_quartile_60` | +17.9 | +17.8 | +0.1 | +0.03 | +4.91 | 50.0% | 176,545 | 2,709 | +22.5 (113,304, 1,617) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_up_120` | +16.9 | +16.8 | +0.0 | -0.37 | +5.58 | 51.5% | 315,390 | 2,709 | +20.9 (212,388, 1,617) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |

## Horizon 5d — TS/CS rule expectancy (sorted by |within bps|)

| Rule | mean bps | market bps | within bps | t_within | t_date | hit% | n | dates | purged mean bps (n, dates) | stability | stability (within) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |
| `ch52_low` | +68.8 | +43.6 | +25.2 | +4.30 | +8.06 | 51.4% | 96,641 | 2,706 | +84.4 (53,511, 1,602) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_20` | +64.6 | +44.4 | +20.1 | +6.55 | +9.44 | 52.2% | 177,228 | 2,706 | +72.5 (112,957, 1,602) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_down_60` | +64.2 | +48.4 | +15.8 | +4.00 | +8.96 | 52.8% | 154,317 | 2,705 | +78.8 (92,674, 1,601) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_60` | +58.9 | +44.5 | +14.4 | +4.35 | +8.34 | 51.4% | 176,312 | 2,706 | +66.2 (112,229, 1,602) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_down_20` | +56.2 | +42.2 | +14.0 | +5.19 | +9.99 | 53.6% | 179,372 | 2,706 | +75.0 (110,809, 1,602) | STABLE_SIGN | single-window |
| `cs_top_quartile_120` | +55.4 | +44.5 | +11.0 | +3.19 | +9.16 | 51.9% | 174,907 | 2,706 | +68.6 (111,137, 1,602) | STABLE_SIGN | single-window |
| `ts_strong_up_20` | +37.0 | +45.2 | -8.2 | -0.32 | +5.56 | 52.4% | 261,664 | 2,700 | +40.8 (170,214, 1,602) | STABLE_SIGN | single-window |
| `ts_down_20` | +51.5 | +43.8 | +7.8 | +4.52 | +9.75 | 52.9% | 308,962 | 2,706 | +67.1 (194,184, 1,602) | STABLE_SIGN | single-window |
| `cs_down_20` | +52.0 | +44.5 | +7.6 | +4.51 | +9.36 | 52.9% | 351,418 | 2,706 | +60.5 (224,333, 1,602) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `below_ma_50` | +51.4 | +44.1 | +7.3 | +4.03 | +9.29 | 52.6% | 298,797 | 2,706 | +63.9 (184,882, 1,602) | STABLE_SIGN | single-window |
| `cs_up_20` | +37.3 | +44.5 | -7.1 | -4.28 | +7.79 | 52.2% | 351,416 | 2,706 | +48.1 (224,328, 1,602) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_120` | +51.1 | +44.5 | +6.6 | +2.02 | +7.19 | 50.8% | 174,912 | 2,706 | +56.3 (111,138, 1,602) | STABLE_SIGN | single-window |
| `ts_up_20` | +38.7 | +45.1 | -6.4 | -4.52 | +7.55 | 52.3% | 391,234 | 2,705 | +43.7 (253,426, 1,602) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_down_60` | +54.3 | +48.1 | +6.2 | +1.69 | +8.47 | 52.4% | 281,552 | 2,706 | +68.3 (171,808, 1,602) | STABLE_SIGN | single-window |
| `above_ma_50` | +39.9 | +44.8 | -4.9 | -4.56 | +7.56 | 52.5% | 402,932 | 2,706 | +48.0 (262,439, 1,602) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_down_120` | +50.3 | +45.6 | +4.7 | +1.01 | +7.13 | 51.9% | 134,173 | 2,706 | +62.2 (81,455, 1,602) | STABLE_SIGN | single-window |
| `cs_down_60` | +48.6 | +44.5 | +4.1 | +2.35 | +8.58 | 52.4% | 349,534 | 2,706 | +57.4 (222,794, 1,602) | STABLE_SIGN | single-window |
| `ch52_high` | +36.6 | +40.6 | -4.1 | -3.30 | +8.33 | 53.9% | 229,005 | 2,702 | +45.2 (150,483, 1,602) | STABLE_SIGN | single-window |
| `ts_up_60` | +38.0 | +42.1 | -4.0 | -4.11 | +8.10 | 52.7% | 417,330 | 2,706 | +45.8 (274,006, 1,602) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_top_quartile_20` | +40.6 | +44.5 | -3.9 | -1.24 | +7.01 | 51.1% | 177,212 | 2,706 | +52.2 (112,955, 1,602) | STABLE_SIGN | single-window |
| `cs_up_60` | +40.8 | +44.5 | -3.7 | -2.11 | +8.48 | 52.6% | 349,531 | 2,706 | +51.8 (222,793, 1,602) | STABLE_SIGN | single-window |
| `cs_up_120` | +47.7 | +44.6 | +3.0 | +1.48 | +9.79 | 53.1% | 346,698 | 2,706 | +59.6 (220,532, 1,602) | STABLE_SIGN | single-window |
| `mom_neg` | +50.9 | +53.7 | -2.7 | -2.32 | +6.35 | 51.2% | 239,656 | 2,706 | +58.8 (142,843, 1,602) | STABLE_SIGN | single-window |
| `ts_strong_up_60` | +39.9 | +42.5 | -2.6 | -2.11 | +7.85 | 53.0% | 292,369 | 2,705 | +47.3 (193,631, 1,602) | STABLE_SIGN | single-window |
| `cs_down_120` | +42.4 | +44.6 | -2.2 | -1.07 | +7.43 | 52.0% | 346,697 | 2,706 | +50.8 (220,532, 1,602) | STABLE_SIGN | single-window |
| `cs_top_quartile_60` | +46.5 | +44.5 | +2.0 | +0.62 | +7.88 | 51.5% | 176,308 | 2,706 | +56.6 (112,227, 1,602) | STABLE_SIGN | single-window |
| `mom_pos` | +41.6 | +39.7 | +2.0 | +0.17 | +9.63 | 53.4% | 441,629 | 2,706 | +53.7 (288,731, 1,602) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_up_120` | +43.0 | +41.2 | +1.9 | +0.17 | +8.75 | 53.2% | 315,008 | 2,706 | +53.2 (210,530, 1,602) | STABLE_SIGN | single-window |
| `ts_up_120` | +42.6 | +41.8 | +0.8 | -0.10 | +9.78 | 52.9% | 433,769 | 2,706 | +53.6 (285,281, 1,602) | STABLE_SIGN | single-window |
| `ts_down_120` | +49.0 | +49.3 | -0.3 | -0.55 | +7.33 | 51.9% | 260,182 | 2,706 | +58.0 (156,345, 1,602) | STABLE_SIGN | single-window |

## Horizon 10d — TS/CS rule expectancy (sorted by |within bps|)

| Rule | mean bps | market bps | within bps | t_within | t_date | hit% | n | dates | purged mean bps (n, dates) | stability | stability (within) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |
| `ch52_low` | +138.8 | +93.7 | +45.1 | +5.03 | +10.46 | 53.4% | 96,418 | 2,701 | +154.3 (52,671, 1,577) | STABLE_SIGN | single-window |
| `ts_strong_down_60` | +127.6 | +100.6 | +26.9 | +4.23 | +11.96 | 54.8% | 153,872 | 2,700 | +143.2 (91,331, 1,576) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_20` | +114.1 | +89.6 | +24.5 | +6.19 | +12.13 | 53.3% | 176,833 | 2,701 | +126.6 (111,144, 1,577) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_60` | +114.1 | +89.7 | +24.4 | +5.60 | +11.68 | 52.9% | 175,917 | 2,701 | +126.2 (110,434, 1,577) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_top_quartile_120` | +113.9 | +89.6 | +24.2 | +5.06 | +13.18 | 53.2% | 174,512 | 2,701 | +140.4 (109,357, 1,577) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_down_20` | +102.6 | +88.1 | +14.4 | +4.44 | +12.72 | 55.1% | 178,826 | 2,701 | +129.5 (109,399, 1,577) | STABLE_SIGN | single-window |
| `below_ma_50` | +99.5 | +89.8 | +9.7 | +3.67 | +12.38 | 54.1% | 297,844 | 2,701 | +120.1 (182,269, 1,577) | STABLE_SIGN | single-window |
| `ts_down_60` | +108.3 | +98.6 | +9.7 | +1.08 | +11.46 | 54.2% | 280,811 | 2,701 | +128.5 (169,145, 1,577) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_120` | +98.8 | +89.6 | +9.2 | +2.19 | +9.94 | 52.1% | 174,517 | 2,701 | +107.5 (109,358, 1,577) | STABLE_SIGN | single-window |
| `cs_top_quartile_60` | +98.8 | +89.7 | +9.1 | +2.01 | +11.73 | 52.7% | 175,913 | 2,701 | +116.8 (110,432, 1,577) | STABLE_SIGN | single-window |
| `ts_strong_up_20` | +82.0 | +90.9 | -9.0 | +0.41 | +8.84 | 53.9% | 261,248 | 2,695 | +93.3 (167,070, 1,577) | STABLE_SIGN | single-window |
| `ts_strong_down_120` | +103.4 | +94.8 | +8.6 | +1.54 | +9.80 | 53.7% | 133,806 | 2,701 | +120.4 (80,109, 1,577) | STABLE_SIGN | single-window |
| `ts_down_20` | +96.9 | +88.4 | +8.5 | +3.61 | +12.70 | 54.3% | 308,097 | 2,701 | +120.7 (191,545, 1,577) | STABLE_SIGN | single-window |
| `cs_up_120` | +97.1 | +89.8 | +7.2 | +2.49 | +13.85 | 54.5% | 345,913 | 2,701 | +120.0 (217,012, 1,577) | STABLE_SIGN | single-window |
| `ts_up_20` | +83.9 | +90.7 | -6.8 | -2.09 | +11.62 | 53.8% | 390,526 | 2,700 | +96.1 (248,895, 1,577) | STABLE_SIGN | single-window |
| `cs_down_20` | +96.2 | +89.6 | +6.6 | +3.18 | +12.35 | 54.2% | 350,633 | 2,701 | +110.0 (220,743, 1,577) | STABLE_SIGN | single-window |
| `above_ma_50` | +83.2 | +89.5 | -6.3 | -4.60 | +11.82 | 53.9% | 402,310 | 2,701 | +99.2 (257,889, 1,577) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_up_60` | +77.6 | +83.7 | -6.1 | -5.05 | +11.79 | 53.9% | 416,497 | 2,701 | +95.0 (269,520, 1,577) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_down_60` | +95.5 | +89.6 | +5.9 | +2.57 | +11.99 | 54.1% | 348,749 | 2,701 | +111.5 (219,219, 1,577) | STABLE_SIGN | single-window |
| `cs_up_20` | +83.8 | +89.6 | -5.8 | -2.81 | +12.08 | 53.7% | 350,631 | 2,701 | +104.7 (220,738, 1,577) | STABLE_SIGN | single-window |
| `ts_strong_up_120` | +87.3 | +81.6 | +5.8 | -0.01 | +13.09 | 54.5% | 314,417 | 2,701 | +109.3 (207,533, 1,577) | STABLE_SIGN | single-window |
| `cs_down_120` | +84.4 | +89.8 | -5.4 | -1.87 | +10.49 | 53.5% | 345,912 | 2,701 | +98.4 (217,012, 1,577) | STABLE_SIGN | single-window |
| `ch52_high` | +76.1 | +81.4 | -5.3 | -4.02 | +12.21 | 55.3% | 228,631 | 2,697 | +92.8 (148,141, 1,577) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_up_60` | +84.9 | +89.6 | -4.8 | -2.13 | +12.20 | 53.9% | 348,746 | 2,701 | +104.7 (219,218, 1,577) | STABLE_SIGN | single-window |
| `cs_top_quartile_20` | +93.8 | +89.6 | +4.2 | +0.86 | +11.31 | 52.3% | 176,817 | 2,701 | +116.5 (111,143, 1,577) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_up_60` | +81.1 | +84.4 | -3.4 | -2.39 | +10.69 | 54.3% | 291,840 | 2,700 | +97.8 (190,549, 1,577) | STABLE_SIGN | single-window |
| `ts_up_120` | +85.0 | +82.6 | +2.5 | +0.25 | +13.73 | 54.2% | 432,853 | 2,701 | +108.2 (281,000, 1,577) | STABLE_SIGN | single-window |
| `mom_neg` | +105.2 | +107.5 | -2.3 | -2.56 | +9.01 | 53.0% | 239,265 | 2,701 | +117.9 (140,310, 1,577) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_pos` | +82.4 | +80.3 | +2.1 | -0.87 | +13.43 | 54.6% | 440,455 | 2,701 | +105.2 (284,372, 1,577) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_down_120` | +99.9 | +102.0 | -2.0 | -0.94 | +10.06 | 53.8% | 259,525 | 2,701 | +110.7 (153,576, 1,577) | STABLE_SIGN | single-window |

## Horizon 15d — TS/CS rule expectancy (sorted by |within bps|)

| Rule | mean bps | market bps | within bps | t_within | t_date | hit% | n | dates | purged mean bps (n, dates) | stability | stability (within) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |
| `ch52_low` | +210.9 | +151.0 | +59.9 | +4.64 | +11.74 | 54.5% | 96,202 | 2,696 | +217.9 (51,753, 1,552) | STABLE_SIGN | single-window |
| `cs_top_quartile_120` | +172.8 | +136.1 | +36.6 | +6.24 | +15.90 | 54.0% | 174,117 | 2,696 | +211.7 (107,581, 1,552) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_down_60` | +195.0 | +159.1 | +35.8 | +4.34 | +14.20 | 55.8% | 153,418 | 2,695 | +207.5 (89,842, 1,551) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_60` | +170.0 | +136.1 | +34.0 | +6.28 | +14.00 | 53.7% | 175,522 | 2,696 | +182.9 (108,639, 1,552) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_20` | +164.4 | +136.0 | +28.5 | +5.90 | +14.01 | 53.9% | 176,438 | 2,696 | +183.0 (109,337, 1,552) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_top_quartile_60` | +154.8 | +136.1 | +18.7 | +3.31 | +14.70 | 53.6% | 175,518 | 2,696 | +184.3 (108,637, 1,552) | STABLE_SIGN | single-window |
| `ts_strong_down_120` | +165.5 | +150.6 | +14.9 | +1.67 | +11.86 | 55.0% | 133,491 | 2,696 | +185.5 (78,894, 1,552) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_120` | +150.9 | +136.1 | +14.8 | +2.72 | +12.11 | 53.0% | 174,122 | 2,696 | +162.4 (107,582, 1,552) | STABLE_SIGN | single-window |
| `cs_top_quartile_20` | +149.5 | +136.0 | +13.6 | +2.38 | +14.48 | 53.3% | 176,422 | 2,696 | +180.9 (109,336, 1,552) | STABLE_SIGN | single-window |
| `ts_down_60` | +164.5 | +152.4 | +12.1 | +0.71 | +13.76 | 55.1% | 280,070 | 2,696 | +183.2 (166,333, 1,552) | STABLE_SIGN | single-window |
| `below_ma_50` | +153.2 | +141.4 | +11.8 | +3.30 | +14.48 | 54.8% | 296,850 | 2,696 | +181.0 (179,500, 1,552) | STABLE_SIGN | single-window |
| `cs_up_120` | +147.0 | +136.4 | +10.6 | +2.97 | +16.60 | 55.5% | 345,128 | 2,696 | +180.7 (213,492, 1,552) | STABLE_SIGN | single-window |
| `ts_strong_down_20` | +151.2 | +140.9 | +10.3 | +3.53 | +14.37 | 55.7% | 178,158 | 2,696 | +181.2 (107,702, 1,552) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_up_20` | +123.4 | +132.4 | -9.0 | -0.93 | +11.04 | 55.0% | 260,935 | 2,690 | +143.9 (164,093, 1,552) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_up_120` | +130.5 | +121.7 | +8.8 | -0.59 | +15.78 | 55.6% | 313,807 | 2,696 | +165.2 (204,433, 1,552) | STABLE_SIGN | single-window |
| `cs_down_60` | +144.1 | +136.0 | +8.1 | +2.90 | +14.50 | 55.1% | 347,964 | 2,696 | +163.5 (215,644, 1,552) | STABLE_SIGN | single-window |
| `ts_down_20` | +147.8 | +139.9 | +8.0 | +3.25 | +14.86 | 55.2% | 307,100 | 2,696 | +175.9 (188,654, 1,552) | STABLE_SIGN | single-window |
| `cs_down_120` | +128.5 | +136.4 | -7.8 | -2.18 | +12.83 | 54.5% | 345,127 | 2,696 | +145.9 (213,492, 1,552) | STABLE_SIGN | single-window |
| `above_ma_50` | +124.5 | +132.1 | -7.6 | -4.94 | +14.48 | 55.1% | 401,729 | 2,696 | +147.0 (253,498, 1,552) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_up_60` | +117.8 | +125.2 | -7.3 | -5.75 | +14.35 | 55.0% | 415,663 | 2,696 | +147.8 (265,181, 1,552) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_up_20` | +126.3 | +133.2 | -6.9 | -3.33 | +14.49 | 54.8% | 389,949 | 2,695 | +146.7 (244,615, 1,552) | STABLE_SIGN | single-window |
| `cs_up_60` | +129.8 | +136.0 | -6.2 | -2.32 | +14.76 | 54.8% | 347,961 | 2,696 | +160.1 (215,643, 1,552) | STABLE_SIGN | single-window |
| `ch52_high` | +113.8 | +119.8 | -6.1 | -4.86 | +14.62 | 56.7% | 228,264 | 2,692 | +139.1 (145,828, 1,552) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_down_20` | +141.7 | +136.0 | +5.7 | +2.44 | +14.51 | 55.1% | 349,848 | 2,696 | +161.2 (217,156, 1,552) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_up_20` | +131.5 | +136.0 | -4.5 | -2.04 | +15.12 | 54.7% | 349,846 | 2,696 | +159.7 (217,152, 1,552) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_up_120` | +126.7 | +123.2 | +3.5 | +0.39 | +16.26 | 55.2% | 431,928 | 2,696 | +161.3 (276,618, 1,552) | STABLE_SIGN | single-window |
| `ts_down_120` | +155.7 | +158.3 | -2.6 | -1.36 | +12.14 | 54.7% | 258,876 | 2,696 | +166.7 (150,907, 1,552) | STABLE_SIGN | single-window |
| `ts_strong_up_60` | +124.2 | +126.0 | -1.8 | -3.88 | +13.27 | 55.6% | 291,341 | 2,695 | +154.6 (187,603, 1,552) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `mom_pos` | +124.3 | +122.6 | +1.7 | -1.59 | +16.09 | 55.5% | 439,271 | 2,696 | +156.2 (279,971, 1,552) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_neg` | +160.8 | +161.9 | -1.0 | -2.85 | +10.97 | 54.2% | 238,884 | 2,696 | +178.4 (137,818, 1,552) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |

## Horizon 20d — TS/CS rule expectancy (sorted by |within bps|)

| Rule | mean bps | market bps | within bps | t_within | t_date | hit% | n | dates | purged mean bps (n, dates) | stability | stability (within) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |
| `ch52_low` | +276.4 | +207.5 | +68.9 | +4.37 | +12.93 | 55.1% | 95,991 | 2,691 | +269.0 (50,691, 1,527) | STABLE_SIGN | single-window |
| `cs_top_quartile_120` | +231.9 | +181.7 | +50.2 | +7.67 | +18.33 | 54.7% | 173,722 | 2,691 | +283.6 (105,806, 1,527) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_down_60` | +255.1 | +214.3 | +40.7 | +4.25 | +16.21 | 56.7% | 153,021 | 2,690 | +255.8 (88,375, 1,526) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_60` | +221.3 | +181.5 | +39.9 | +6.55 | +15.98 | 54.4% | 175,127 | 2,691 | +230.7 (106,844, 1,527) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_20` | +212.4 | +181.4 | +31.0 | +5.96 | +15.87 | 54.3% | 176,043 | 2,691 | +231.8 (107,532, 1,527) | STABLE_SIGN | single-window |
| `cs_top_quartile_60` | +210.8 | +181.5 | +29.3 | +4.58 | +17.17 | 54.4% | 175,123 | 2,691 | +251.5 (106,842, 1,527) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_top_quartile_20` | +201.5 | +181.4 | +20.1 | +3.08 | +16.93 | 54.1% | 176,027 | 2,691 | +239.9 (107,531, 1,527) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_120` | +200.8 | +181.7 | +19.1 | +3.06 | +14.07 | 53.6% | 173,727 | 2,691 | +212.1 (105,807, 1,527) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_down_120` | +221.3 | +203.4 | +17.9 | +1.78 | +13.71 | 55.9% | 133,247 | 2,691 | +238.1 (77,626, 1,527) | STABLE_SIGN | single-window |
| `cs_up_120` | +195.6 | +182.0 | +13.6 | +3.45 | +19.00 | 56.3% | 344,343 | 2,691 | +239.6 (209,972, 1,527) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_down_60` | +217.4 | +204.2 | +13.1 | +0.17 | +15.71 | 55.8% | 279,337 | 2,691 | +227.8 (163,559, 1,527) | STABLE_SIGN | single-window |
| `below_ma_50` | +205.6 | +192.6 | +13.0 | +2.90 | +16.26 | 55.5% | 295,952 | 2,691 | +235.7 (176,560, 1,527) | STABLE_SIGN | single-window |
| `ts_strong_up_120` | +173.6 | +162.0 | +11.5 | -0.39 | +18.49 | 56.6% | 313,146 | 2,691 | +222.5 (201,479, 1,527) | STABLE_SIGN | single-window |
| `ts_strong_up_20` | +163.2 | +173.9 | -10.7 | -3.04 | +15.33 | 55.8% | 260,656 | 2,685 | +192.4 (161,580, 1,527) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_down_120` | +172.3 | +182.0 | -9.6 | -2.43 | +14.98 | 55.3% | 344,342 | 2,691 | +191.4 (209,972, 1,527) | STABLE_SIGN | single-window |
| `ts_down_20` | +198.1 | +189.8 | +8.3 | +3.32 | +16.79 | 55.8% | 306,044 | 2,691 | +226.8 (185,411, 1,527) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `above_ma_50` | +165.1 | +173.2 | -8.1 | -4.52 | +17.17 | 56.0% | 401,052 | 2,691 | +195.5 (249,278, 1,527) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_down_60` | +189.3 | +181.4 | +7.8 | +2.55 | +16.63 | 55.9% | 347,179 | 2,691 | +209.6 (212,073, 1,527) | STABLE_SIGN | single-window |
| `ts_up_60` | +158.6 | +166.3 | -7.8 | -5.91 | +16.65 | 55.8% | 414,823 | 2,691 | +203.1 (260,809, 1,527) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_up_20` | +167.5 | +175.1 | -7.6 | -3.93 | +17.26 | 55.7% | 389,434 | 2,690 | +196.5 (240,709, 1,527) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_down_20` | +199.4 | +192.9 | +6.5 | +2.81 | +15.82 | 56.1% | 177,469 | 2,691 | +224.0 (105,839, 1,527) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ch52_high` | +151.7 | +157.9 | -6.1 | -5.31 | +16.86 | 57.7% | 227,855 | 2,687 | +191.3 (143,591, 1,527) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_down_20` | +187.6 | +181.5 | +6.1 | +2.48 | +16.65 | 55.8% | 349,063 | 2,691 | +211.1 (213,571, 1,527) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_up_60` | +176.3 | +181.4 | -5.2 | -1.83 | +17.11 | 55.6% | 347,176 | 2,691 | +216.5 (212,072, 1,527) | STABLE_SIGN | single-window |
| `ts_up_120` | +169.0 | +164.1 | +4.9 | +0.97 | +18.44 | 56.0% | 430,951 | 2,691 | +215.3 (272,359, 1,527) | STABLE_SIGN | single-window |
| `cs_up_20` | +176.7 | +181.4 | -4.7 | -2.04 | +17.53 | 55.6% | 349,061 | 2,691 | +211.3 (213,567, 1,527) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_down_120` | +208.3 | +211.8 | -3.5 | -1.80 | +14.01 | 55.5% | 258,279 | 2,691 | +215.5 (148,113, 1,527) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_pos` | +165.1 | +163.6 | +1.5 | -2.15 | +18.41 | 56.2% | 438,056 | 2,691 | +205.6 (275,581, 1,527) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_neg` | +215.5 | +215.8 | -0.3 | -3.30 | +12.65 | 55.1% | 238,534 | 2,691 | +235.3 (135,316, 1,527) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_up_60` | +167.6 | +167.7 | -0.1 | -4.44 | +15.86 | 56.5% | 290,806 | 2,690 | +215.0 (184,555, 1,527) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |

## Horizon 60d — TS/CS rule expectancy (sorted by |within bps|)

| Rule | mean bps | market bps | within bps | t_within | t_date | hit% | n | dates | purged mean bps (n, dates) | stability | stability (within) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |
| `cs_top_quartile_120` | +712.3 | +548.5 | +163.8 | +14.98 | +30.62 | 58.5% | 170,562 | 2,651 | +843.5 (91,606, 1,327) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ch52_low` | +749.8 | +617.6 | +132.3 | +5.04 | +19.74 | 58.7% | 94,955 | 2,651 | +544.9 (41,756, 1,327) | STABLE_SIGN | single-window |
| `cs_top_quartile_60` | +649.8 | +546.7 | +103.2 | +8.54 | +27.14 | 57.7% | 171,963 | 2,651 | +778.6 (92,532, 1,327) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_20` | +637.6 | +546.7 | +90.9 | +8.87 | +26.84 | 58.2% | 172,883 | 2,651 | +629.6 (93,147, 1,327) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_60` | +635.8 | +546.6 | +89.2 | +7.81 | +25.71 | 58.4% | 171,967 | 2,651 | +584.3 (92,534, 1,327) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_top_quartile_20` | +607.7 | +546.7 | +60.9 | +5.38 | +26.01 | 57.7% | 172,867 | 2,651 | +692.9 (93,148, 1,327) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_down_60` | +679.2 | +619.5 | +59.6 | +4.28 | +26.34 | 60.9% | 150,832 | 2,650 | +557.3 (77,643, 1,326) | STABLE_SIGN | single-window |
| `cs_up_120` | +598.7 | +548.7 | +50.0 | +7.96 | +31.99 | 60.5% | 338,063 | 2,651 | +703.0 (181,839, 1,327) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_down_120` | +508.0 | +548.7 | -40.7 | -6.58 | +25.26 | 59.6% | 338,062 | 2,651 | +512.3 (181,839, 1,327) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_up_120` | +542.4 | +507.4 | +34.9 | +2.57 | +30.44 | 60.9% | 307,675 | 2,651 | +690.4 (180,588, 1,327) | STABLE_SIGN | single-window |
| `below_ma_50` | +619.6 | +585.8 | +33.8 | +3.94 | +29.24 | 60.0% | 290,467 | 2,651 | +580.4 (152,316, 1,327) | STABLE_SIGN | single-window |
| `ts_down_120` | +576.4 | +608.1 | -31.7 | -3.25 | +22.73 | 59.5% | 254,132 | 2,651 | +493.1 (122,711, 1,327) | STABLE_SIGN | single-window |
| `ts_strong_down_20` | +616.8 | +588.7 | +28.1 | +2.79 | +26.88 | 60.2% | 174,033 | 2,651 | +590.5 (91,124, 1,327) | STABLE_SIGN | single-window |
| `ts_down_60` | +629.3 | +603.3 | +26.0 | +1.93 | +27.77 | 60.3% | 274,383 | 2,651 | +553.9 (141,358, 1,327) | STABLE_SIGN | single-window |
| `ts_strong_up_20` | +492.2 | +517.5 | -25.3 | -1.40 | +22.83 | 60.0% | 256,423 | 2,645 | +589.9 (140,988, 1,327) | STABLE_SIGN | single-window |
| `ts_up_120` | +537.8 | +513.2 | +24.5 | +4.04 | +30.97 | 60.4% | 422,512 | 2,651 | +664.3 (241,389, 1,327) | STABLE_SIGN | single-window |
| `ts_up_20` | +498.7 | +522.9 | -24.3 | -6.62 | +27.99 | 59.8% | 382,834 | 2,650 | +577.8 (209,727, 1,327) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_120` | +571.3 | +548.5 | +22.8 | +2.17 | +22.56 | 57.0% | 170,567 | 2,651 | +536.0 (91,607, 1,327) | STABLE_SIGN | single-window |
| `ts_down_20` | +600.9 | +578.5 | +22.4 | +2.61 | +28.96 | 60.1% | 300,065 | 2,651 | +602.0 (159,308, 1,327) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `above_ma_50` | +497.3 | +517.9 | -20.6 | -6.76 | +28.10 | 59.9% | 393,937 | 2,651 | +608.8 (216,407, 1,327) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ch52_high` | +456.7 | +476.2 | -19.6 | -8.91 | +29.71 | 61.8% | 224,187 | 2,647 | +599.3 (126,754, 1,327) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_up_60` | +492.6 | +509.7 | -17.0 | -4.74 | +28.42 | 59.8% | 407,181 | 2,651 | +624.0 (226,131, 1,327) | STABLE_SIGN | single-window |
| `cs_down_20` | +563.3 | +546.7 | +16.5 | +3.02 | +28.81 | 60.2% | 342,783 | 2,651 | +580.0 (184,964, 1,327) | STABLE_SIGN | single-window |
| `cs_up_20` | +533.5 | +546.8 | -13.3 | -2.48 | +27.92 | 59.6% | 342,781 | 2,651 | +607.9 (184,960, 1,327) | STABLE_SIGN | single-window |
| `ts_strong_up_60` | +495.9 | +505.4 | -9.5 | -4.34 | +26.71 | 60.0% | 286,150 | 2,650 | +651.4 (161,301, 1,327) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_down_60` | +554.9 | +546.9 | +7.9 | +1.54 | +27.91 | 60.3% | 340,899 | 2,651 | +551.5 (183,656, 1,327) | STABLE_SIGN | single-window |
| `ts_strong_down_120` | +571.6 | +577.0 | -5.4 | -1.31 | +20.74 | 59.1% | 131,526 | 2,651 | +465.9 (64,360, 1,327) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_up_60` | +546.0 | +546.9 | -1.0 | -0.49 | +28.30 | 59.6% | 340,896 | 2,651 | +647.6 (183,655, 1,327) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_pos` | +494.3 | +493.6 | +0.7 | -3.65 | +32.20 | 60.2% | 428,230 | 2,651 | +592.2 (239,399, 1,327) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_neg` | +647.9 | +648.3 | -0.4 | -4.57 | +20.92 | 59.8% | 235,841 | 2,651 | +631.0 (116,529, 1,327) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |

## Horizon 120d — TS/CS rule expectancy (sorted by |within bps|)

| Rule | mean bps | market bps | within bps | t_within | t_date | hit% | n | dates | purged mean bps (n, dates) | stability | stability (within) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |
| `cs_top_quartile_120` | +1491.9 | +1105.6 | +386.4 | +22.58 | +42.87 | 62.5% | 165,822 | 2,591 | +1696.9 (70,525, 1,027) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_top_quartile_60` | +1397.3 | +1103.0 | +294.3 | +16.79 | +38.37 | 61.5% | 167,223 | 2,591 | +1660.5 (71,220, 1,027) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_top_quartile_20` | +1286.7 | +1101.5 | +185.2 | +10.36 | +34.18 | 60.4% | 168,127 | 2,591 | +1491.5 (71,732, 1,027) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ch52_low` | +1340.7 | +1173.8 | +166.9 | +5.08 | +22.54 | 59.8% | 92,990 | 2,591 | +1114.4 (27,779, 1,027) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_20` | +1251.4 | +1101.4 | +150.0 | +9.32 | +33.74 | 60.3% | 168,143 | 2,591 | +1294.8 (71,730, 1,027) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_up_120` | +1238.5 | +1106.1 | +132.4 | +13.46 | +43.61 | 64.1% | 328,643 | 2,591 | +1437.0 (139,939, 1,027) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_down_120` | +982.3 | +1106.1 | -123.7 | -12.98 | +31.17 | 61.4% | 328,642 | 2,591 | +1036.0 (139,939, 1,027) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_down_120` | +1026.3 | +1136.3 | -110.0 | -6.73 | +22.52 | 60.3% | 128,599 | 2,591 | +1006.0 (45,046, 1,027) | STABLE_SIGN | single-window |
| `ts_down_120` | +1072.5 | +1179.8 | -107.3 | -9.21 | +27.26 | 60.8% | 248,019 | 2,591 | +1004.3 (87,587, 1,027) | STABLE_SIGN | single-window |
| `ts_strong_up_120` | +1168.2 | +1061.6 | +106.5 | +4.94 | +41.00 | 65.0% | 298,041 | 2,591 | +1416.4 (146,315, 1,027) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_60` | +1179.9 | +1103.0 | +76.9 | +4.37 | +29.59 | 59.4% | 167,227 | 2,591 | +1133.2 (71,222, 1,027) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_up_120` | +1128.0 | +1062.0 | +66.0 | +5.56 | +41.79 | 63.9% | 409,787 | 2,591 | +1336.9 (192,647, 1,027) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_up_60` | +1161.1 | +1103.7 | +57.5 | +5.14 | +39.71 | 63.1% | 331,476 | 2,591 | +1380.8 (141,440, 1,027) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_down_60` | +1056.2 | +1103.7 | -47.5 | -4.15 | +33.92 | 62.2% | 331,479 | 2,591 | +1064.2 (141,441, 1,027) | STABLE_SIGN | single-window |
| `ts_strong_up_60` | +1118.9 | +1082.5 | +36.5 | +0.72 | +35.84 | 63.8% | 278,458 | 2,590 | +1435.2 (134,068, 1,027) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_bottom_quartile_120` | +1075.9 | +1105.6 | -29.6 | -1.44 | +27.30 | 58.5% | 165,827 | 2,591 | +1077.3 (70,525, 1,027) | STABLE_SIGN | single-window |
| `ts_strong_up_20` | +1042.8 | +1069.5 | -26.7 | +2.23 | +23.76 | 62.6% | 249,545 | 2,585 | +1275.0 (111,066, 1,027) | STABLE_SIGN | single-window |
| `ts_up_20` | +1048.9 | +1074.4 | -25.5 | -1.28 | +35.30 | 62.7% | 372,232 | 2,590 | +1239.7 (164,397, 1,027) | STABLE_SIGN | single-window |
| `mom_neg` | +1255.6 | +1230.7 | +24.9 | -4.73 | +27.11 | 62.3% | 231,967 | 2,591 | +1447.4 (91,893, 1,027) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_down_60` | +1130.7 | +1154.0 | -23.3 | -2.41 | +32.71 | 61.8% | 266,585 | 2,591 | +983.1 (98,593, 1,027) | STABLE_SIGN | single-window |
| `mom_pos` | +1012.8 | +1034.0 | -21.3 | -7.39 | +44.49 | 63.2% | 413,341 | 2,591 | +1114.3 (182,155, 1,027) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `below_ma_50` | +1162.8 | +1143.4 | +19.4 | +2.37 | +36.38 | 62.2% | 282,453 | 2,591 | +1099.3 (111,532, 1,027) | STABLE_SIGN | single-window |
| `ts_strong_down_20` | +1174.2 | +1156.8 | +17.4 | +2.70 | +33.79 | 62.4% | 169,687 | 2,591 | +1131.0 (67,702, 1,027) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_down_20` | +1154.2 | +1140.6 | +13.6 | +1.77 | +37.41 | 62.5% | 291,799 | 2,591 | +1145.8 (119,741, 1,027) | STABLE_SIGN | single-window |
| `ts_up_60` | +1084.5 | +1071.2 | +13.3 | +0.86 | +39.02 | 63.3% | 396,098 | 2,591 | +1345.6 (184,368, 1,027) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_down_60` | +1187.6 | +1174.5 | +13.0 | -0.56 | +27.68 | 62.0% | 147,006 | 2,590 | +978.9 (52,328, 1,026) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `above_ma_50` | +1066.4 | +1074.0 | -7.6 | -2.14 | +38.06 | 63.0% | 383,051 | 2,591 | +1296.4 (172,454, 1,027) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ch52_high` | +1000.8 | +1006.4 | -5.7 | -7.08 | +42.08 | 65.8% | 217,228 | 2,587 | +1245.6 (102,117, 1,027) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_up_20` | +1105.1 | +1102.3 | +2.8 | -0.18 | +36.94 | 62.5% | 333,361 | 2,591 | +1269.3 (142,455, 1,027) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_down_20` | +1104.7 | +1102.3 | +2.3 | +0.75 | +36.99 | 62.7% | 333,363 | 2,591 | +1150.1 (142,460, 1,027) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |

## Condition-level comparison with Step 4

Step 4's own-history *position* conditions re-evaluated through the identical machinery — these are the same numbers Step 4 reports, repeated here so the TS-vs-CS reading sits next to the condition-level one instead of requiring two documents.

| Condition | Horizon | mean bps | market bps | within bps | t_within | stability | stability (within) |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- | :--- |
| `above_ma_50` | 5d | +39.9 | +44.8 | -4.9 | -4.56 | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `above_ma_50` | 20d | +165.1 | +173.2 | -8.1 | -4.52 | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `above_ma_50` | 60d | +497.3 | +517.9 | -20.6 | -6.76 | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `above_ma_50` | 120d | +1066.4 | +1074.0 | -7.6 | -2.14 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `below_ma_50` | 5d | +51.4 | +44.1 | +7.3 | +4.03 | STABLE_SIGN | single-window |
| `below_ma_50` | 20d | +205.6 | +192.6 | +13.0 | +2.90 | STABLE_SIGN | single-window |
| `below_ma_50` | 60d | +619.6 | +585.8 | +33.8 | +3.94 | STABLE_SIGN | single-window |
| `below_ma_50` | 120d | +1162.8 | +1143.4 | +19.4 | +2.37 | STABLE_SIGN | single-window |
| `ch52_high` | 5d | +36.6 | +40.6 | -4.1 | -3.30 | STABLE_SIGN | single-window |
| `ch52_high` | 20d | +151.7 | +157.9 | -6.1 | -5.31 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ch52_high` | 60d | +456.7 | +476.2 | -19.6 | -8.91 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ch52_high` | 120d | +1000.8 | +1006.4 | -5.7 | -7.08 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ch52_low` | 5d | +68.8 | +43.6 | +25.2 | +4.30 | STABLE_SIGN | single-window |
| `ch52_low` | 20d | +276.4 | +207.5 | +68.9 | +4.37 | STABLE_SIGN | single-window |
| `ch52_low` | 60d | +749.8 | +617.6 | +132.3 | +5.04 | STABLE_SIGN | single-window |
| `ch52_low` | 120d | +1340.7 | +1173.8 | +166.9 | +5.08 | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `mom_pos` | 5d | +41.6 | +39.7 | +2.0 | +0.17 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_pos` | 20d | +165.1 | +163.6 | +1.5 | -2.15 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_pos` | 60d | +494.3 | +493.6 | +0.7 | -3.65 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_pos` | 120d | +1012.8 | +1034.0 | -21.3 | -7.39 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_neg` | 5d | +50.9 | +53.7 | -2.7 | -2.32 | STABLE_SIGN | single-window |
| `mom_neg` | 20d | +215.5 | +215.8 | -0.3 | -3.30 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_neg` | 60d | +647.9 | +648.3 | -0.4 | -4.57 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_neg` | 120d | +1255.6 | +1230.7 | +24.9 | -4.73 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |

## Findings summary (TS vs CS)

- TS rule × horizon cells: 96; CS rule × horizon cells: 96.
- Cells whose *within-date* component passed the stable-sign clause: TS 15, CS 33.
- Mean |within bps| across TS cells: 14.1; across CS cells: 29.7 (cross-sectionally framed rules are, on this panel, the larger 'which name' effect).
- Raw `mean bps` is dominated by the market component for every rule and horizon: the own-history rules mostly identify *when*, not *which*, and the when is the CAD market drift shared by the whole equal-weight universe.
- Null and insufficient cases are recorded in each horizon table rather than dropped.

## Limits

- Descriptive only: no model, no threshold tuned on forward returns, no multiplicity correction across cells, no claim of causality and no cost/net-expectancy claim (that is Step 6).
- The TS rules use only a symbol's own trailing returns and trailing vol; the CS rules use the same trailing return ranked within date. Neither uses any forward information.
- Purge: `max(20td, horizon)` embargo and the label-end rule inside each validation block, identical to Step 4; the fold sets are the same, so TS/CS and Step 4 numbers are directly comparable.
