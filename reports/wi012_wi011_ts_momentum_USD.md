# WI-011 Step 5 — per-symbol (time-series) momentum probe and TS-vs-CS decomposition (CAD)

- Generated (UTC): 2026-10-26T06:47:08Z
- Panel: 1,314,936 rows · 533 symbols · 2716 dates (2016-01-04 → 2026-10-21)
- Evaluation order: TS rule first, then its cross-sectional counterpart on the *same* trailing return, so the comparison varies the framing (own level vs within-date rank) and not the information content. No cross-sectional ranking of any model score is involved, and no model is trained.

TS_RULES: `ts_up_20` (own trailing 20d return > 0), `ts_down_20` (own trailing 20d return < 0), `ts_strong_up_20` (own trailing 20d return / (vol_20*sqrt(20)) >= +0.5), `ts_strong_down_20` (own trailing 20d return / (vol_20*sqrt(20)) <= -0.5), `cs_up_20` (own trailing 20d return above the same-date median), `cs_down_20` (own trailing 20d return below the same-date median), `cs_top_quartile_20` (within-date top quartile of the trailing 20d return), `cs_bottom_quartile_20` (within-date bottom quartile of the trailing 20d return), `ts_up_60` (own trailing 60d return > 0), `ts_down_60` (own trailing 60d return < 0), `ts_strong_up_60` (own trailing 60d return / (vol_20*sqrt(60)) >= +0.5), `ts_strong_down_60` (own trailing 60d return / (vol_20*sqrt(60)) <= -0.5), `cs_up_60` (own trailing 60d return above the same-date median), `cs_down_60` (own trailing 60d return below the same-date median), `cs_top_quartile_60` (within-date top quartile of the trailing 60d return), `cs_bottom_quartile_60` (within-date bottom quartile of the trailing 60d return), `ts_up_120` (own trailing 120d return > 0), `ts_down_120` (own trailing 120d return < 0), `ts_strong_up_120` (own trailing 120d return / (vol_20*sqrt(120)) >= +0.5), `ts_strong_down_120` (own trailing 120d return / (vol_20*sqrt(120)) <= -0.5), `cs_up_120` (own trailing 120d return above the same-date median), `cs_down_120` (own trailing 120d return below the same-date median), `cs_top_quartile_120` (within-date top quartile of the trailing 120d return), `cs_bottom_quartile_120` (within-date bottom quartile of the trailing 120d return)

TS_WINDOWS: 20,60,120 trading days · volatility-scaled strength threshold |z| >= 0.5 with z = own trailing return / (vol_20 * sqrt(window))

HORIZONS: 1,2,5,10,15,20,60,120

PURGE_TD: max(20, horizon) trading days (WI-009 `PurgedWalkForwardSplit` over the sorted unique date array) — per horizon: 1d→20td, 2d→20td, 5d→20td, 10d→20td, 15d→20td, 20d→20td, 60d→60td, 120d→120td

SUBWINDOWS: 2 — 2016-01-04→2021-05-25 and 2021-05-26→2026-10-21 (same disjoint halves as Step 4). `STABLE_SIGN` = same sign in both halves with |t| > 2; `STABLE_SIGN_WITHIN` applies the same clause to the within-date component.

Decomposition columns: `mean` = raw mean forward bps; `market` = mean of each firing row's own date all-name mean (the drift the rule inherits); `within` = mean deviation from that date's mean (the 'which name' part); `t_within` = t across dates on the per-date deviation.

## TS_VS_CS_DECOMPOSITION

For each matched pair, the *same* trailing-return element is evaluated as a TS level rule and as a cross-sectional rank rule. `Δ(TS−CS)` is their raw-mean difference in bps; the `within` columns say how much of each rule is a 'which name' effect rather than a market-drift effect.

### Horizon 1d

| Element | TS rule | TS mean | TS market | TS within (t) | CS rule | CS mean | CS market | CS within (t) | Δ(TS−CS) mean bps | TS stable | CS stable |
| :--- | :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| trailing 20d return (w=20) | `ts_up_20` | +7.8 | +8.3 | -0.5 (-0.90) | `cs_up_20` | +8.2 | +8.6 | -0.4 (-0.60) | -0.3 | stable | stable |
| vol-scaled trailing 20d return (w=20) | `ts_strong_up_20` | +7.6 | +7.9 | -0.3 (-0.50) | `cs_top_quartile_20` | +9.4 | +8.6 | +0.8 (+0.64) | -1.8 | stable | stable |
| trailing 20d return (down side) (w=20) | `ts_down_20` | +9.5 | +9.0 | +0.6 (+1.07) | `cs_bottom_quartile_20` | +10.5 | +8.6 | +1.9 (+1.42) | -1.0 | single-window | single-window |
| trailing 60d return (w=60) | `ts_up_60` | +6.8 | +7.1 | -0.3 (-1.10) | `cs_up_60` | +8.3 | +8.6 | -0.3 (-0.39) | -1.5 | stable | stable |
| vol-scaled trailing 60d return (w=60) | `ts_strong_up_60` | +6.5 | +6.6 | -0.1 (-1.02) | `cs_top_quartile_60` | +9.6 | +8.6 | +1.0 (+0.77) | -3.1 | single-window | stable |
| trailing 60d return (down side) (w=60) | `ts_down_60` | +11.1 | +10.8 | +0.3 (+0.31) | `cs_bottom_quartile_60` | +10.3 | +8.6 | +1.7 (+1.23) | +0.7 | single-window | single-window |
| trailing 120d return (w=120) | `ts_up_120` | +7.5 | +7.6 | -0.1 (-0.50) | `cs_up_120` | +8.9 | +8.6 | +0.3 (+0.36) | -1.4 | stable | stable |
| vol-scaled trailing 120d return (w=120) | `ts_strong_up_120` | +7.5 | +7.3 | +0.2 (-0.34) | `cs_top_quartile_120` | +10.2 | +8.6 | +1.6 (+1.18) | -2.8 | stable | stable |
| trailing 120d return (down side) (w=120) | `ts_down_120` | +10.4 | +10.3 | +0.1 (+0.18) | `cs_bottom_quartile_120` | +10.3 | +8.6 | +1.7 (+1.17) | +0.1 | single-window | single-window |

### Horizon 2d

| Element | TS rule | TS mean | TS market | TS within (t) | CS rule | CS mean | CS market | CS within (t) | Δ(TS−CS) mean bps | TS stable | CS stable |
| :--- | :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| trailing 20d return (w=20) | `ts_up_20` | +15.8 | +16.8 | -1.0 (-0.85) | `cs_up_20` | +16.2 | +17.1 | -0.8 (-0.81) | -0.4 | stable | stable |
| vol-scaled trailing 20d return (w=20) | `ts_strong_up_20` | +15.4 | +16.1 | -0.6 (-0.62) | `cs_top_quartile_20` | +18.9 | +17.1 | +1.8 (+0.99) | -3.4 | stable | stable |
| trailing 20d return (down side) (w=20) | `ts_down_20` | +18.5 | +17.4 | +1.1 (+1.36) | `cs_bottom_quartile_20` | +21.2 | +17.1 | +4.1 (+2.13) | -2.7 | stable | stable |
| trailing 60d return (w=60) | `ts_up_60` | +13.4 | +14.2 | -0.8 (-1.46) | `cs_up_60` | +16.3 | +17.1 | -0.8 (-0.69) | -2.9 | stable | stable |
| vol-scaled trailing 60d return (w=60) | `ts_strong_up_60` | +12.9 | +13.2 | -0.3 (-1.85) | `cs_top_quartile_60` | +18.9 | +17.1 | +1.8 (+0.96) | -6.0 | stable | stable |
| trailing 60d return (down side) (w=60) | `ts_down_60` | +22.1 | +21.3 | +0.9 (+0.43) | `cs_bottom_quartile_60` | +20.8 | +17.1 | +3.7 (+1.82) | +1.3 | stable | stable |
| trailing 120d return (w=120) | `ts_up_120` | +15.1 | +15.2 | -0.1 (-0.57) | `cs_up_120` | +17.7 | +17.1 | +0.6 (+0.47) | -2.6 | stable | stable |
| vol-scaled trailing 120d return (w=120) | `ts_strong_up_120` | +15.0 | +14.6 | +0.4 (-0.07) | `cs_top_quartile_120` | +20.4 | +17.1 | +3.3 (+1.70) | -5.4 | stable | stable |
| trailing 120d return (down side) (w=120) | `ts_down_120` | +20.5 | +20.2 | +0.3 (+0.18) | `cs_bottom_quartile_120` | +20.6 | +17.1 | +3.5 (+1.64) | -0.1 | stable | stable |

### Horizon 5d

| Element | TS rule | TS mean | TS market | TS within (t) | CS rule | CS mean | CS market | CS within (t) | Δ(TS−CS) mean bps | TS stable | CS stable |
| :--- | :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| trailing 20d return (w=20) | `ts_up_20` | +38.1 | +40.4 | -2.3 (-1.58) | `cs_up_20` | +40.9 | +42.7 | -1.8 (-1.25) | -2.8 | stable | stable |
| vol-scaled trailing 20d return (w=20) | `ts_strong_up_20` | +37.5 | +38.8 | -1.4 (-1.57) | `cs_top_quartile_20` | +47.2 | +42.7 | +4.5 (+1.67) | -9.7 | stable | stable |
| trailing 20d return (down side) (w=20) | `ts_down_20` | +48.4 | +45.7 | +2.7 (+2.31) | `cs_bottom_quartile_20` | +52.3 | +42.7 | +9.5 (+3.35) | -3.9 | stable | stable |
| trailing 60d return (w=60) | `ts_up_60` | +33.2 | +34.9 | -1.7 (-2.34) | `cs_up_60` | +41.1 | +42.7 | -1.7 (-1.00) | -7.9 | stable | stable |
| vol-scaled trailing 60d return (w=60) | `ts_strong_up_60` | +32.2 | +32.6 | -0.4 (-2.65) | `cs_top_quartile_60` | +46.6 | +42.7 | +3.9 (+1.36) | -14.4 | stable | stable |
| trailing 60d return (down side) (w=60) | `ts_down_60` | +56.1 | +54.2 | +2.0 (+0.17) | `cs_bottom_quartile_60` | +51.6 | +42.7 | +8.8 (+2.84) | +4.6 | stable | stable |
| trailing 120d return (w=120) | `ts_up_120` | +38.3 | +37.8 | +0.5 (-0.44) | `cs_up_120` | +45.0 | +42.7 | +2.3 (+1.19) | -6.7 | stable | stable |
| vol-scaled trailing 120d return (w=120) | `ts_strong_up_120` | +38.5 | +36.7 | +1.8 (+0.48) | `cs_top_quartile_120` | +52.8 | +42.7 | +10.1 (+3.39) | -14.3 | stable | stable |
| trailing 120d return (down side) (w=120) | `ts_down_120` | +50.4 | +50.8 | -0.4 (-0.38) | `cs_bottom_quartile_120` | +49.4 | +42.7 | +6.7 (+2.06) | +1.0 | stable | stable |

### Horizon 10d

| Element | TS rule | TS mean | TS market | TS within (t) | CS rule | CS mean | CS market | CS within (t) | Δ(TS−CS) mean bps | TS stable | CS stable |
| :--- | :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| trailing 20d return (w=20) | `ts_up_20` | +76.2 | +79.2 | -2.9 (-2.24) | `cs_up_20` | +83.9 | +85.7 | -1.7 (-1.10) | -7.7 | stable | stable |
| vol-scaled trailing 20d return (w=20) | `ts_strong_up_20` | +74.0 | +75.6 | -1.7 (-2.03) | `cs_top_quartile_20` | +95.7 | +85.7 | +10.0 (+2.94) | -21.8 | stable | stable |
| trailing 20d return (down side) (w=20) | `ts_down_20` | +97.4 | +94.0 | +3.4 (+2.33) | `cs_bottom_quartile_20` | +99.0 | +85.7 | +13.2 (+3.93) | -1.5 | stable | stable |
| trailing 60d return (w=60) | `ts_up_60` | +66.6 | +70.0 | -3.4 (-4.05) | `cs_up_60` | +82.9 | +85.7 | -2.8 (-1.37) | -16.3 | stable | stable |
| vol-scaled trailing 60d return (w=60) | `ts_strong_up_60` | +66.0 | +66.7 | -0.7 (-4.23) | `cs_top_quartile_60` | +92.5 | +85.7 | +6.9 (+1.90) | -26.6 | stable | stable |
| trailing 60d return (down side) (w=60) | `ts_down_60` | +112.6 | +108.5 | +4.1 (+0.07) | `cs_bottom_quartile_60` | +101.5 | +85.7 | +15.8 (+3.98) | +11.1 | stable | stable |
| trailing 120d return (w=120) | `ts_up_120` | +76.2 | +75.3 | +0.9 (-0.15) | `cs_up_120` | +90.3 | +85.7 | +4.6 (+1.87) | -14.1 | stable | stable |
| vol-scaled trailing 120d return (w=120) | `ts_strong_up_120` | +76.8 | +73.1 | +3.7 (+0.81) | `cs_top_quartile_120` | +107.4 | +85.7 | +21.7 (+5.64) | -30.6 | stable | stable |
| trailing 120d return (down side) (w=120) | `ts_down_120` | +102.1 | +102.8 | -0.6 (-0.96) | `cs_bottom_quartile_120` | +97.3 | +85.7 | +11.6 (+2.86) | +4.8 | stable | stable |

### Horizon 15d

| Element | TS rule | TS mean | TS market | TS within (t) | CS rule | CS mean | CS market | CS within (t) | Δ(TS−CS) mean bps | TS stable | CS stable |
| :--- | :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| trailing 20d return (w=20) | `ts_up_20` | +110.3 | +114.5 | -4.2 (-2.49) | `cs_up_20` | +126.7 | +129.8 | -3.2 (-1.59) | -16.3 | stable | stable |
| vol-scaled trailing 20d return (w=20) | `ts_strong_up_20` | +104.5 | +107.4 | -2.9 (-2.59) | `cs_top_quartile_20` | +144.5 | +129.9 | +14.6 (+3.46) | -40.0 | stable | stable |
| trailing 20d return (down side) (w=20) | `ts_down_20` | +154.2 | +149.5 | +4.7 (+3.03) | `cs_bottom_quartile_20` | +149.8 | +129.9 | +19.9 (+4.78) | +4.4 | stable | stable |
| trailing 60d return (w=60) | `ts_up_60` | +101.1 | +105.5 | -4.4 (-4.78) | `cs_up_60` | +125.1 | +129.8 | -4.7 (-1.82) | -24.0 | stable | stable |
| vol-scaled trailing 60d return (w=60) | `ts_strong_up_60` | +100.3 | +101.6 | -1.3 (-4.98) | `cs_top_quartile_60` | +139.7 | +129.8 | +9.9 (+2.15) | -39.4 | stable | stable |
| trailing 60d return (down side) (w=60) | `ts_down_60` | +170.5 | +165.2 | +5.3 (-0.35) | `cs_bottom_quartile_60` | +154.9 | +129.8 | +25.1 (+5.03) | +15.6 | stable | stable |
| trailing 120d return (w=120) | `ts_up_120` | +112.0 | +111.2 | +0.8 (-0.60) | `cs_up_120` | +135.3 | +129.9 | +5.4 (+1.77) | -23.3 | stable | stable |
| vol-scaled trailing 120d return (w=120) | `ts_strong_up_120` | +112.1 | +107.5 | +4.6 (+0.31) | `cs_top_quartile_120` | +161.2 | +129.9 | +31.2 (+6.66) | -49.1 | stable | stable |
| trailing 120d return (down side) (w=120) | `ts_down_120` | +160.6 | +160.6 | -0.0 (-1.21) | `cs_bottom_quartile_120` | +148.8 | +129.9 | +18.8 (+3.77) | +11.8 | stable | stable |

### Horizon 20d

| Element | TS rule | TS mean | TS market | TS within (t) | CS rule | CS mean | CS market | CS within (t) | Δ(TS−CS) mean bps | TS stable | CS stable |
| :--- | :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| trailing 20d return (w=20) | `ts_up_20` | +146.0 | +151.3 | -5.3 (-2.89) | `cs_up_20` | +167.4 | +172.9 | -5.5 (-2.34) | -21.4 | stable | stable |
| vol-scaled trailing 20d return (w=20) | `ts_strong_up_20` | +138.1 | +142.2 | -4.1 (-2.84) | `cs_top_quartile_20` | +190.8 | +172.9 | +17.9 (+3.68) | -52.7 | stable | stable |
| trailing 20d return (down side) (w=20) | `ts_down_20` | +206.3 | +200.6 | +5.7 (+3.34) | `cs_bottom_quartile_20` | +199.4 | +172.9 | +26.5 (+5.60) | +6.9 | stable | stable |
| trailing 60d return (w=60) | `ts_up_60` | +133.7 | +140.4 | -6.7 (-6.04) | `cs_up_60` | +166.8 | +172.8 | -6.1 (-2.06) | -33.1 | stable | stable |
| vol-scaled trailing 60d return (w=60) | `ts_strong_up_60` | +134.9 | +135.6 | -0.7 (-5.80) | `cs_top_quartile_60` | +187.9 | +172.9 | +15.0 (+2.86) | -53.0 | stable | stable |
| trailing 60d return (down side) (w=60) | `ts_down_60` | +228.4 | +220.2 | +8.2 (-0.17) | `cs_bottom_quartile_60` | +206.2 | +172.9 | +33.3 (+5.85) | +22.3 | stable | stable |
| trailing 120d return (w=120) | `ts_up_120` | +148.6 | +147.7 | +0.9 (-0.57) | `cs_up_120` | +180.3 | +173.0 | +7.3 (+2.17) | -31.7 | stable | stable |
| vol-scaled trailing 120d return (w=120) | `ts_strong_up_120` | +148.5 | +143.0 | +5.4 (+0.41) | `cs_top_quartile_120` | +213.4 | +173.0 | +40.3 (+7.68) | -64.9 | stable | stable |
| trailing 120d return (down side) (w=120) | `ts_down_120` | +214.7 | +214.5 | +0.3 (-1.08) | `cs_bottom_quartile_120` | +197.3 | +173.0 | +24.3 (+4.30) | +17.4 | stable | stable |

### Horizon 60d

| Element | TS rule | TS mean | TS market | TS within (t) | CS rule | CS mean | CS market | CS within (t) | Δ(TS−CS) mean bps | TS stable | CS stable |
| :--- | :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| trailing 20d return (w=20) | `ts_up_20` | +450.1 | +459.6 | -9.4 (-4.72) | `cs_up_20` | +507.1 | +517.9 | -10.8 (-2.12) | -57.0 | stable | stable |
| vol-scaled trailing 20d return (w=20) | `ts_strong_up_20` | +436.0 | +438.3 | -2.3 (-3.49) | `cs_top_quartile_20` | +575.4 | +517.9 | +57.5 (+6.51) | -139.4 | stable | stable |
| trailing 20d return (down side) (w=20) | `ts_down_20` | +603.0 | +592.8 | +10.3 (+1.84) | `cs_bottom_quartile_20` | +599.1 | +517.9 | +81.3 (+8.66) | +3.9 | stable | stable |
| trailing 60d return (w=60) | `ts_up_60` | +427.9 | +441.4 | -13.5 (-5.48) | `cs_up_60` | +508.2 | +517.9 | -9.8 (-1.86) | -80.2 | stable | stable |
| vol-scaled trailing 60d return (w=60) | `ts_strong_up_60` | +421.8 | +416.8 | +5.0 (-2.42) | `cs_top_quartile_60` | +594.5 | +517.9 | +76.6 (+8.19) | -172.7 | stable | stable |
| trailing 60d return (down side) (w=60) | `ts_down_60` | +651.2 | +629.2 | +21.9 (-0.97) | `cs_bottom_quartile_60` | +608.4 | +517.9 | +90.6 (+9.05) | +42.8 | stable | stable |
| trailing 120d return (w=120) | `ts_up_120` | +492.9 | +478.7 | +14.2 (+3.39) | `cs_up_120` | +552.7 | +518.4 | +34.3 (+6.92) | -59.8 | stable | stable |
| vol-scaled trailing 120d return (w=120) | `ts_strong_up_120` | +493.9 | +464.0 | +29.9 (+5.80) | `cs_top_quartile_120` | +664.4 | +518.8 | +145.6 (+16.86) | -170.6 | stable | stable |
| trailing 120d return (down side) (w=120) | `ts_down_120` | +568.8 | +583.2 | -14.4 (-1.44) | `cs_bottom_quartile_120` | +558.5 | +518.8 | +39.7 (+4.53) | +10.4 | stable | stable |

### Horizon 120d

| Element | TS rule | TS mean | TS market | TS within (t) | CS rule | CS mean | CS market | CS within (t) | Δ(TS−CS) mean bps | TS stable | CS stable |
| :--- | :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| trailing 20d return (w=20) | `ts_up_20` | +982.9 | +975.1 | +7.7 (+1.42) | `cs_up_20` | +1052.8 | +1030.1 | +22.7 (+3.12) | -70.0 | stable | stable |
| vol-scaled trailing 20d return (w=20) | `ts_strong_up_20` | +981.9 | +956.0 | +25.9 (+4.86) | `cs_top_quartile_20` | +1223.1 | +1030.0 | +193.0 (+14.83) | -241.2 | stable | stable |
| trailing 20d return (down side) (w=20) | `ts_down_20` | +1092.1 | +1101.1 | -9.1 (-0.86) | `cs_bottom_quartile_20` | +1135.5 | +1030.0 | +105.5 (+8.00) | -43.4 | stable | stable |
| trailing 60d return (w=60) | `ts_up_60` | +1003.1 | +986.0 | +17.1 (+3.47) | `cs_up_60` | +1090.2 | +1030.3 | +59.9 (+7.69) | -87.1 | stable | stable |
| vol-scaled trailing 60d return (w=60) | `ts_strong_up_60` | +1034.5 | +981.9 | +52.6 (+6.34) | `cs_top_quartile_60` | +1302.6 | +1030.6 | +272.0 (+20.61) | -268.1 | stable | stable |
| trailing 60d return (down side) (w=60) | `ts_down_60` | +1079.9 | +1095.3 | -15.5 (-2.49) | `cs_bottom_quartile_60` | +1095.6 | +1030.6 | +65.0 (+4.73) | -15.7 | stable | stable |
| trailing 120d return (w=120) | `ts_up_120` | +1042.1 | +995.2 | +46.9 (+10.69) | `cs_up_120` | +1132.7 | +1031.9 | +100.8 (+16.49) | -90.6 | stable | stable |
| vol-scaled trailing 120d return (w=120) | `ts_strong_up_120` | +1067.7 | +992.7 | +75.0 (+10.67) | `cs_top_quartile_120` | +1393.6 | +1032.2 | +361.4 (+30.17) | -325.9 | stable | stable |
| trailing 120d return (down side) (w=120) | `ts_down_120` | +1026.3 | +1092.1 | -65.8 (-4.02) | `cs_bottom_quartile_120` | +1031.2 | +1032.2 | -1.0 (+0.38) | -5.0 | stable | stable |

## Horizon 1d — TS/CS rule expectancy (sorted by |within bps|)

| Rule | mean bps | market bps | within bps | t_within | t_date | hit% | n | dates | purged mean bps (n, dates) | stability | stability (within) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |
| `ch52_low` | +15.2 | +11.2 | +4.0 | +2.56 | +3.77 | 50.6% | 177,310 | 2,715 | +16.7 (115,475, 1,625) | single-window | single-window |
| `cs_bottom_quartile_20` | +10.5 | +8.6 | +1.9 | +1.42 | +3.19 | 51.1% | 328,847 | 2,715 | +12.0 (207,121, 1,625) | single-window | single-window |
| `cs_bottom_quartile_60` | +10.3 | +8.6 | +1.7 | +1.23 | +3.08 | 50.8% | 327,691 | 2,715 | +12.1 (206,523, 1,625) | single-window | single-window |
| `cs_bottom_quartile_120` | +10.3 | +8.6 | +1.7 | +1.17 | +3.04 | 50.5% | 325,951 | 2,715 | +11.8 (205,624, 1,625) | single-window | single-window |
| `ts_strong_down_60` | +13.7 | +12.0 | +1.7 | +1.40 | +3.54 | 51.4% | 290,500 | 2,712 | +15.8 (183,091, 1,622) | STABLE_SIGN | single-window |
| `cs_top_quartile_120` | +10.2 | +8.6 | +1.6 | +1.18 | +4.06 | 51.8% | 325,951 | 2,715 | +12.3 (205,624, 1,625) | STABLE_SIGN | single-window |
| `ts_strong_down_20` | +10.2 | +8.6 | +1.6 | +2.13 | +3.86 | 51.7% | 337,442 | 2,715 | +13.3 (213,138, 1,625) | single-window | single-window |
| `ts_strong_down_120` | +11.8 | +10.5 | +1.3 | +0.15 | +2.80 | 51.0% | 251,463 | 2,715 | +13.3 (162,030, 1,625) | single-window | single-window |
| `cs_top_quartile_60` | +9.6 | +8.6 | +1.0 | +0.77 | +3.93 | 51.5% | 327,691 | 2,715 | +11.3 (206,523, 1,625) | STABLE_SIGN | single-window |
| `cs_top_quartile_20` | +9.4 | +8.6 | +0.8 | +0.64 | +3.85 | 51.1% | 328,844 | 2,715 | +11.5 (207,120, 1,625) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `below_ma_50` | +10.3 | +9.7 | +0.6 | +1.33 | +3.53 | 51.6% | 555,658 | 2,715 | +12.3 (351,626, 1,625) | single-window | UNSTABLE_SIGN_WITHIN |
| `ts_down_20` | +9.5 | +9.0 | +0.6 | +1.07 | +3.49 | 51.6% | 574,662 | 2,715 | +11.8 (364,939, 1,625) | single-window | single-window |
| `above_ma_50` | +7.2 | +7.8 | -0.6 | -1.15 | +3.42 | 51.3% | 752,511 | 2,715 | +8.6 (472,628, 1,625) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_up_20` | +7.8 | +8.3 | -0.5 | -0.90 | +3.53 | 51.3% | 734,753 | 2,715 | +8.9 (460,013, 1,625) | STABLE_SIGN | single-window |
| `cs_up_20` | +8.2 | +8.6 | -0.4 | -0.60 | +3.60 | 51.4% | 655,495 | 2,715 | +9.8 (412,985, 1,625) | STABLE_SIGN | single-window |
| `ch52_high` | +6.4 | +6.8 | -0.4 | -1.50 | +3.08 | 51.9% | 432,245 | 2,713 | +7.7 (263,265, 1,625) | single-window | UNSTABLE_SIGN_WITHIN |
| `cs_down_20` | +9.0 | +8.6 | +0.4 | +0.53 | +3.20 | 51.4% | 655,496 | 2,715 | +10.5 (412,985, 1,625) | single-window | single-window |
| `mom_neg` | +10.4 | +10.8 | -0.4 | -1.00 | +2.64 | 50.7% | 454,674 | 2,715 | +11.3 (290,541, 1,625) | single-window | UNSTABLE_SIGN_WITHIN |
| `cs_up_120` | +8.9 | +8.6 | +0.3 | +0.36 | +3.93 | 51.9% | 649,630 | 2,715 | +10.7 (409,900, 1,625) | STABLE_SIGN | single-window |
| `ts_up_60` | +6.8 | +7.1 | -0.3 | -1.10 | +3.52 | 51.5% | 774,813 | 2,715 | +8.0 (487,965, 1,625) | STABLE_SIGN | single-window |
| `cs_up_60` | +8.3 | +8.6 | -0.3 | -0.39 | +3.68 | 51.7% | 653,169 | 2,715 | +9.8 (411,750, 1,625) | STABLE_SIGN | single-window |
| `ts_down_60` | +11.1 | +10.8 | +0.3 | +0.31 | +3.20 | 51.4% | 531,495 | 2,715 | +13.3 (335,355, 1,625) | single-window | single-window |
| `cs_down_120` | +8.3 | +8.6 | -0.3 | -0.33 | +2.92 | 50.9% | 649,630 | 2,715 | +9.8 (409,900, 1,625) | single-window | single-window |
| `ts_strong_up_20` | +7.6 | +7.9 | -0.3 | -0.50 | +3.15 | 51.2% | 494,329 | 2,714 | +8.6 (306,782, 1,625) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_down_60` | +8.8 | +8.6 | +0.2 | +0.23 | +3.09 | 51.1% | 653,168 | 2,715 | +10.5 (411,749, 1,625) | STABLE_SIGN | single-window |
| `ts_strong_up_120` | +7.5 | +7.3 | +0.2 | -0.34 | +3.81 | 51.8% | 574,711 | 2,715 | +8.8 (360,397, 1,625) | STABLE_SIGN | single-window |
| `mom_pos` | +7.6 | +7.5 | +0.2 | -0.07 | +3.77 | 51.9% | 828,693 | 2,715 | +9.6 (521,118, 1,625) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_down_120` | +10.4 | +10.3 | +0.1 | +0.18 | +3.10 | 51.0% | 493,228 | 2,715 | +11.9 (312,154, 1,625) | single-window | single-window |
| `ts_strong_up_60` | +6.5 | +6.6 | -0.1 | -1.02 | +3.36 | 51.5% | 541,326 | 2,715 | +7.4 (338,878, 1,625) | single-window | UNSTABLE_SIGN_WITHIN |
| `ts_up_120` | +7.5 | +7.6 | -0.1 | -0.50 | +3.78 | 51.7% | 806,340 | 2,715 | +9.2 (507,685, 1,625) | STABLE_SIGN | single-window |

## Horizon 2d — TS/CS rule expectancy (sorted by |within bps|)

| Rule | mean bps | market bps | within bps | t_within | t_date | hit% | n | dates | purged mean bps (n, dates) | stability | stability (within) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |
| `ch52_low` | +28.3 | +20.3 | +8.0 | +3.16 | +5.03 | 51.7% | 177,245 | 2,714 | +32.1 (115,214, 1,620) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_20` | +21.2 | +17.1 | +4.1 | +2.13 | +4.67 | 51.8% | 328,713 | 2,714 | +24.2 (206,476, 1,620) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_60` | +20.8 | +17.1 | +3.7 | +1.82 | +4.46 | 51.6% | 327,557 | 2,714 | +23.7 (205,880, 1,620) | STABLE_SIGN | single-window |
| `ts_strong_down_60` | +26.7 | +23.1 | +3.6 | +1.71 | +4.89 | 52.6% | 290,361 | 2,711 | +31.3 (182,698, 1,617) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_120` | +20.6 | +17.1 | +3.5 | +1.64 | +4.33 | 51.3% | 325,817 | 2,714 | +23.0 (204,983, 1,620) | STABLE_SIGN | single-window |
| `cs_top_quartile_120` | +20.4 | +17.1 | +3.3 | +1.70 | +5.93 | 52.7% | 325,817 | 2,714 | +24.7 (204,983, 1,620) | STABLE_SIGN | single-window |
| `ts_strong_down_20` | +19.2 | +16.0 | +3.2 | +2.99 | +5.57 | 52.3% | 337,279 | 2,714 | +26.2 (212,703, 1,620) | STABLE_SIGN | single-window |
| `ts_strong_down_120` | +22.2 | +19.9 | +2.4 | +0.10 | +3.92 | 51.9% | 251,378 | 2,714 | +25.8 (161,700, 1,620) | STABLE_SIGN | single-window |
| `cs_top_quartile_60` | +18.9 | +17.1 | +1.8 | +0.96 | +5.60 | 52.2% | 327,557 | 2,714 | +22.3 (205,880, 1,620) | STABLE_SIGN | single-window |
| `cs_top_quartile_20` | +18.9 | +17.1 | +1.8 | +0.99 | +5.55 | 52.0% | 328,710 | 2,714 | +22.5 (206,475, 1,620) | STABLE_SIGN | single-window |
| `below_ma_50` | +20.4 | +19.2 | +1.2 | +1.77 | +5.07 | 52.5% | 555,395 | 2,714 | +24.1 (350,815, 1,620) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_down_20` | +18.5 | +17.4 | +1.1 | +1.36 | +5.01 | 52.4% | 574,420 | 2,714 | +23.3 (364,122, 1,620) | STABLE_SIGN | single-window |
| `above_ma_50` | +14.4 | +15.5 | -1.1 | -1.31 | +4.93 | 52.2% | 752,241 | 2,714 | +16.9 (470,875, 1,620) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_up_20` | +15.8 | +16.8 | -1.0 | -0.85 | +5.08 | 52.3% | 734,462 | 2,714 | +17.4 (458,262, 1,620) | STABLE_SIGN | single-window |
| `ts_down_60` | +22.1 | +21.3 | +0.9 | +0.43 | +4.63 | 52.4% | 531,256 | 2,714 | +26.4 (334,508, 1,620) | STABLE_SIGN | single-window |
| `cs_up_20` | +16.2 | +17.1 | -0.8 | -0.81 | +5.24 | 52.4% | 655,229 | 2,714 | +19.3 (411,699, 1,620) | STABLE_SIGN | single-window |
| `ts_up_60` | +13.4 | +14.2 | -0.8 | -1.46 | +5.08 | 52.3% | 774,519 | 2,714 | +15.6 (486,248, 1,620) | STABLE_SIGN | single-window |
| `ch52_high` | +12.8 | +13.6 | -0.8 | -1.85 | +4.38 | 52.8% | 432,118 | 2,712 | +15.3 (262,364, 1,620) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_up_60` | +16.3 | +17.1 | -0.8 | -0.69 | +5.32 | 52.6% | 652,903 | 2,714 | +19.1 (410,468, 1,620) | STABLE_SIGN | single-window |
| `mom_neg` | +20.4 | +21.1 | -0.8 | -1.49 | +3.73 | 51.6% | 454,509 | 2,714 | +21.8 (289,628, 1,620) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_down_20` | +17.8 | +17.1 | +0.7 | +0.71 | +4.64 | 52.2% | 655,230 | 2,714 | +20.8 (411,699, 1,620) | STABLE_SIGN | single-window |
| `ts_strong_up_20` | +15.4 | +16.1 | -0.6 | -0.62 | +4.31 | 52.2% | 494,117 | 2,713 | +16.9 (305,508, 1,620) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_up_120` | +17.7 | +17.1 | +0.6 | +0.47 | +5.76 | 52.9% | 649,364 | 2,714 | +21.1 (408,626, 1,620) | STABLE_SIGN | single-window |
| `cs_down_120` | +16.5 | +17.1 | -0.6 | -0.45 | +4.19 | 51.8% | 649,364 | 2,714 | +19.2 (408,626, 1,620) | STABLE_SIGN | single-window |
| `cs_down_60` | +17.6 | +17.1 | +0.5 | +0.48 | +4.51 | 52.0% | 652,902 | 2,714 | +20.8 (410,467, 1,620) | STABLE_SIGN | single-window |
| `ts_strong_up_120` | +15.0 | +14.6 | +0.4 | -0.07 | +5.66 | 52.6% | 574,476 | 2,714 | +17.6 (359,196, 1,620) | STABLE_SIGN | single-window |
| `mom_pos` | +15.3 | +15.0 | +0.3 | -0.18 | +5.53 | 52.8% | 828,325 | 2,714 | +19.3 (519,498, 1,620) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_up_60` | +12.9 | +13.2 | -0.3 | -1.85 | +4.55 | 52.2% | 541,134 | 2,714 | +14.7 (337,626, 1,620) | STABLE_SIGN | single-window |
| `ts_down_120` | +20.5 | +20.2 | +0.3 | +0.18 | +4.42 | 52.0% | 493,044 | 2,714 | +23.2 (311,335, 1,620) | STABLE_SIGN | single-window |
| `ts_up_120` | +15.1 | +15.2 | -0.1 | -0.57 | +5.56 | 52.6% | 805,991 | 2,714 | +18.3 (505,955, 1,620) | STABLE_SIGN | single-window |

## Horizon 5d — TS/CS rule expectancy (sorted by |within bps|)

| Rule | mean bps | market bps | within bps | t_within | t_date | hit% | n | dates | purged mean bps (n, dates) | stability | stability (within) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |
| `ch52_low` | +71.1 | +54.0 | +17.2 | +3.94 | +7.22 | 53.9% | 177,026 | 2,711 | +75.4 (114,359, 1,605) | STABLE_SIGN | single-window |
| `cs_top_quartile_120` | +52.8 | +42.7 | +10.1 | +3.39 | +9.66 | 54.1% | 325,415 | 2,711 | +63.0 (203,061, 1,605) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_20` | +52.3 | +42.7 | +9.5 | +3.35 | +7.27 | 53.2% | 328,311 | 2,711 | +59.0 (204,541, 1,605) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_60` | +51.6 | +42.7 | +8.8 | +2.84 | +6.94 | 53.1% | 327,155 | 2,711 | +58.3 (203,951, 1,605) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_down_60` | +68.2 | +60.2 | +8.0 | +1.98 | +7.26 | 54.6% | 289,955 | 2,708 | +77.9 (181,383, 1,602) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_120` | +49.4 | +42.7 | +6.7 | +2.06 | +6.55 | 52.8% | 325,415 | 2,711 | +54.0 (203,061, 1,605) | STABLE_SIGN | single-window |
| `ts_strong_down_20` | +51.2 | +46.0 | +5.2 | +3.70 | +8.13 | 54.3% | 336,784 | 2,711 | +65.5 (211,368, 1,605) | STABLE_SIGN | single-window |
| `ts_strong_down_120` | +53.6 | +48.9 | +4.7 | -0.45 | +5.83 | 53.6% | 251,074 | 2,711 | +59.2 (160,577, 1,605) | STABLE_SIGN | single-window |
| `cs_top_quartile_20` | +47.2 | +42.7 | +4.5 | +1.67 | +8.96 | 53.4% | 328,308 | 2,711 | +54.6 (204,540, 1,605) | STABLE_SIGN | single-window |
| `cs_top_quartile_60` | +46.6 | +42.7 | +3.9 | +1.36 | +8.80 | 53.6% | 327,155 | 2,711 | +53.7 (203,951, 1,605) | STABLE_SIGN | single-window |
| `ts_down_20` | +48.4 | +45.7 | +2.7 | +2.31 | +7.85 | 54.1% | 573,643 | 2,711 | +59.3 (361,637, 1,605) | STABLE_SIGN | single-window |
| `below_ma_50` | +51.6 | +49.2 | +2.4 | +1.99 | +7.68 | 54.2% | 554,513 | 2,711 | +59.7 (348,236, 1,605) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_up_120` | +45.0 | +42.7 | +2.3 | +1.19 | +9.19 | 54.3% | 648,566 | 2,711 | +53.2 (404,804, 1,605) | STABLE_SIGN | single-window |
| `ts_up_20` | +38.1 | +40.4 | -2.3 | -1.58 | +8.35 | 53.5% | 733,642 | 2,711 | +41.2 (453,046, 1,605) | STABLE_SIGN | single-window |
| `above_ma_50` | +35.7 | +38.0 | -2.2 | -2.03 | +8.20 | 53.4% | 751,524 | 2,711 | +41.1 (465,762, 1,605) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_down_120` | +40.7 | +42.7 | -2.0 | -1.05 | +6.49 | 53.2% | 648,566 | 2,711 | +45.9 (404,804, 1,605) | STABLE_SIGN | single-window |
| `ts_down_60` | +56.1 | +54.2 | +2.0 | +0.17 | +7.12 | 54.2% | 530,551 | 2,711 | +65.0 (331,757, 1,605) | STABLE_SIGN | single-window |
| `cs_up_20` | +40.9 | +42.7 | -1.8 | -1.25 | +8.38 | 53.8% | 654,431 | 2,711 | +47.6 (407,841, 1,605) | STABLE_SIGN | single-window |
| `ts_strong_up_120` | +38.5 | +36.7 | +1.8 | +0.48 | +9.20 | 53.8% | 573,813 | 2,711 | +45.9 (355,854, 1,605) | STABLE_SIGN | single-window |
| `cs_down_20` | +44.4 | +42.7 | +1.7 | +1.16 | +7.24 | 53.6% | 654,432 | 2,711 | +50.9 (407,841, 1,605) | STABLE_SIGN | single-window |
| `ts_up_60` | +33.2 | +34.9 | -1.7 | -2.34 | +8.12 | 53.4% | 773,625 | 2,711 | +38.2 (481,314, 1,605) | STABLE_SIGN | single-window |
| `cs_up_60` | +41.1 | +42.7 | -1.7 | -1.00 | +8.47 | 54.0% | 652,105 | 2,711 | +47.3 (406,623, 1,605) | STABLE_SIGN | single-window |
| `mom_neg` | +51.1 | +52.6 | -1.5 | -1.81 | +6.11 | 53.4% | 454,012 | 2,711 | +52.4 (286,906, 1,605) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_up_20` | +37.5 | +38.8 | -1.4 | -1.57 | +7.56 | 53.4% | 493,600 | 2,710 | +40.6 (301,829, 1,605) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_down_60` | +44.0 | +42.7 | +1.3 | +0.76 | +7.04 | 53.5% | 652,104 | 2,711 | +51.0 (406,622, 1,605) | STABLE_SIGN | single-window |
| `ch52_high` | +33.0 | +34.0 | -1.0 | -2.11 | +7.58 | 54.0% | 431,745 | 2,709 | +39.5 (259,728, 1,605) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_pos` | +38.4 | +37.6 | +0.7 | -0.24 | +8.63 | 54.0% | 827,223 | 2,711 | +48.0 (514,621, 1,605) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_up_120` | +38.3 | +37.8 | +0.5 | -0.44 | +8.92 | 53.8% | 804,987 | 2,711 | +46.6 (500,984, 1,605) | STABLE_SIGN | single-window |
| `ts_down_120` | +50.4 | +50.8 | -0.4 | -0.38 | +6.74 | 53.7% | 492,449 | 2,711 | +54.3 (308,654, 1,605) | STABLE_SIGN | single-window |
| `ts_strong_up_60` | +32.2 | +32.6 | -0.4 | -2.65 | +7.52 | 53.3% | 540,540 | 2,711 | +36.5 (334,216, 1,605) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |

## Horizon 10d — TS/CS rule expectancy (sorted by |within bps|)

| Rule | mean bps | market bps | within bps | t_within | t_date | hit% | n | dates | purged mean bps (n, dates) | stability | stability (within) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |
| `ch52_low` | +140.1 | +107.4 | +32.7 | +4.96 | +9.59 | 55.6% | 176,620 | 2,706 | +148.8 (112,831, 1,580) | STABLE_SIGN | single-window |
| `cs_top_quartile_120` | +107.4 | +85.7 | +21.7 | +5.64 | +13.94 | 55.4% | 324,745 | 2,706 | +126.0 (199,861, 1,580) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_60` | +101.5 | +85.7 | +15.8 | +3.98 | +10.18 | 54.2% | 326,485 | 2,706 | +115.8 (200,736, 1,580) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_20` | +99.0 | +85.7 | +13.2 | +3.93 | +10.46 | 54.4% | 327,641 | 2,706 | +113.2 (201,316, 1,580) | STABLE_SIGN | single-window |
| `ts_strong_down_60` | +132.7 | +119.5 | +13.2 | +2.53 | +10.37 | 56.5% | 289,242 | 2,703 | +150.6 (178,872, 1,577) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_120` | +97.3 | +85.7 | +11.6 | +2.86 | +9.69 | 54.0% | 324,745 | 2,706 | +107.0 (199,861, 1,580) | STABLE_SIGN | single-window |
| `cs_top_quartile_20` | +95.7 | +85.7 | +10.0 | +2.94 | +12.91 | 54.5% | 327,638 | 2,706 | +110.2 (201,315, 1,580) | STABLE_SIGN | single-window |
| `cs_top_quartile_60` | +92.5 | +85.7 | +6.9 | +1.90 | +12.55 | 54.7% | 326,485 | 2,706 | +104.0 (200,736, 1,580) | STABLE_SIGN | single-window |
| `ts_strong_down_120` | +104.3 | +97.9 | +6.3 | -0.78 | +8.36 | 55.1% | 250,473 | 2,706 | +111.6 (158,586, 1,580) | STABLE_SIGN | single-window |
| `ts_strong_down_20` | +101.7 | +95.6 | +6.2 | +3.39 | +10.93 | 56.1% | 335,837 | 2,706 | +126.1 (208,859, 1,580) | STABLE_SIGN | single-window |
| `cs_up_120` | +90.3 | +85.7 | +4.6 | +1.87 | +13.14 | 55.6% | 647,236 | 2,706 | +105.8 (398,437, 1,580) | STABLE_SIGN | single-window |
| `ts_down_60` | +112.6 | +108.5 | +4.1 | +0.07 | +10.22 | 55.8% | 529,321 | 2,706 | +127.1 (326,589, 1,580) | STABLE_SIGN | single-window |
| `cs_down_120` | +81.8 | +85.7 | -3.9 | -1.59 | +9.73 | 54.4% | 647,236 | 2,706 | +92.1 (398,437, 1,580) | STABLE_SIGN | single-window |
| `ts_strong_up_120` | +76.8 | +73.1 | +3.7 | +0.81 | +13.01 | 54.8% | 572,798 | 2,706 | +93.8 (350,412, 1,580) | STABLE_SIGN | single-window |
| `ts_up_60` | +66.6 | +70.0 | -3.4 | -4.05 | +11.60 | 54.4% | 772,190 | 2,706 | +78.3 (473,678, 1,580) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_down_20` | +97.4 | +94.0 | +3.4 | +2.33 | +11.13 | 55.7% | 572,169 | 2,706 | +116.0 (357,064, 1,580) | STABLE_SIGN | single-window |
| `above_ma_50` | +72.7 | +76.0 | -3.3 | -3.02 | +12.12 | 54.5% | 750,448 | 2,706 | +83.4 (457,625, 1,580) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `below_ma_50` | +102.0 | +98.8 | +3.2 | +1.51 | +10.74 | 55.6% | 552,924 | 2,706 | +117.7 (343,553, 1,580) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_up_20` | +76.2 | +79.2 | -2.9 | -2.24 | +12.26 | 54.4% | 732,453 | 2,706 | +84.1 (444,791, 1,580) | STABLE_SIGN | single-window |
| `cs_up_60` | +82.9 | +85.7 | -2.8 | -1.37 | +12.28 | 55.2% | 650,775 | 2,706 | +94.0 (400,218, 1,580) | STABLE_SIGN | single-window |
| `cs_down_60` | +87.8 | +85.7 | +2.1 | +1.03 | +10.41 | 54.7% | 650,774 | 2,706 | +102.4 (400,217, 1,580) | STABLE_SIGN | single-window |
| `cs_up_20` | +83.9 | +85.7 | -1.7 | -1.10 | +12.24 | 55.0% | 653,101 | 2,706 | +96.9 (401,411, 1,580) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_neg` | +103.4 | +105.0 | -1.7 | -2.47 | +8.83 | 54.8% | 453,240 | 2,706 | +107.3 (282,095, 1,580) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_up_20` | +74.0 | +75.6 | -1.7 | -2.03 | +11.77 | 54.3% | 492,909 | 2,705 | +82.6 (295,985, 1,580) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_down_20` | +87.2 | +85.7 | +1.5 | +0.98 | +10.62 | 54.8% | 653,102 | 2,706 | +99.7 (401,411, 1,580) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_up_120` | +76.2 | +75.3 | +0.9 | -0.15 | +12.77 | 54.9% | 803,417 | 2,706 | +94.7 (492,730, 1,580) | STABLE_SIGN | single-window |
| `mom_pos` | +76.5 | +75.7 | +0.8 | -0.84 | +12.52 | 55.1% | 825,330 | 2,706 | +94.6 (506,769, 1,580) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_up_60` | +66.0 | +66.7 | -0.7 | -4.23 | +11.07 | 54.3% | 539,592 | 2,706 | +75.9 (329,135, 1,580) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_down_120` | +102.1 | +102.8 | -0.6 | -0.96 | +9.56 | 55.2% | 491,354 | 2,706 | +106.0 (304,163, 1,580) | STABLE_SIGN | single-window |
| `ch52_high` | +69.1 | +69.7 | -0.6 | -3.02 | +11.85 | 55.2% | 431,136 | 2,704 | +81.4 (255,558, 1,580) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |

## Horizon 15d — TS/CS rule expectancy (sorted by |within bps|)

| Rule | mean bps | market bps | within bps | t_within | t_date | hit% | n | dates | purged mean bps (n, dates) | stability | stability (within) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |
| `ch52_low` | +222.8 | +172.9 | +49.9 | +5.24 | +10.42 | 56.4% | 176,168 | 2,701 | +219.1 (110,923, 1,555) | STABLE_SIGN | single-window |
| `cs_top_quartile_120` | +161.2 | +129.9 | +31.2 | +6.66 | +16.66 | 56.1% | 324,075 | 2,701 | +185.4 (196,661, 1,555) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_60` | +154.9 | +129.8 | +25.1 | +5.03 | +12.43 | 54.9% | 325,815 | 2,701 | +171.9 (197,521, 1,555) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_20` | +149.8 | +129.9 | +19.9 | +4.78 | +12.74 | 54.9% | 326,971 | 2,701 | +166.1 (198,091, 1,555) | STABLE_SIGN | single-window |
| `ts_strong_down_60` | +202.8 | +183.9 | +18.9 | +2.60 | +12.45 | 57.3% | 288,485 | 2,698 | +219.5 (175,709, 1,552) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_120` | +148.8 | +129.9 | +18.8 | +3.77 | +11.94 | 54.8% | 324,075 | 2,701 | +158.1 (196,661, 1,555) | STABLE_SIGN | single-window |
| `cs_top_quartile_20` | +144.5 | +129.9 | +14.6 | +3.46 | +15.49 | 55.4% | 326,968 | 2,701 | +164.3 (198,090, 1,555) | STABLE_SIGN | single-window |
| `ts_strong_down_120` | +167.8 | +157.2 | +10.6 | -0.75 | +10.19 | 56.3% | 249,877 | 2,701 | +170.6 (156,391, 1,555) | STABLE_SIGN | single-window |
| `cs_top_quartile_60` | +139.7 | +129.8 | +9.9 | +2.15 | +15.19 | 55.6% | 325,815 | 2,701 | +154.3 (197,521, 1,555) | STABLE_SIGN | single-window |
| `below_ma_50` | +159.7 | +154.3 | +5.4 | +1.63 | +13.02 | 56.4% | 551,174 | 2,701 | +178.8 (338,096, 1,555) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_up_120` | +135.3 | +129.9 | +5.4 | +1.77 | +15.75 | 56.4% | 645,906 | 2,701 | +155.3 (392,072, 1,555) | STABLE_SIGN | single-window |
| `ts_down_60` | +170.5 | +165.2 | +5.3 | -0.35 | +12.35 | 56.6% | 528,064 | 2,701 | +183.0 (320,818, 1,555) | STABLE_SIGN | single-window |
| `above_ma_50` | +106.6 | +111.8 | -5.2 | -3.65 | +14.78 | 55.3% | 749,533 | 2,701 | +119.7 (450,262, 1,555) | STABLE_SIGN | single-window |
| `ts_strong_down_20` | +159.7 | +154.5 | +5.2 | +3.49 | +13.03 | 56.9% | 334,422 | 2,701 | +184.3 (205,199, 1,555) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_up_60` | +125.1 | +129.8 | -4.7 | -1.82 | +14.94 | 56.1% | 649,445 | 2,701 | +139.0 (393,813, 1,555) | STABLE_SIGN | single-window |
| `ts_down_20` | +154.2 | +149.5 | +4.7 | +3.03 | +13.63 | 56.6% | 570,340 | 2,701 | +173.5 (351,160, 1,555) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_up_120` | +112.1 | +107.5 | +4.6 | +0.31 | +15.54 | 55.6% | 571,749 | 2,701 | +138.5 (344,909, 1,555) | STABLE_SIGN | single-window |
| `ts_up_60` | +101.1 | +105.5 | -4.4 | -4.78 | +14.25 | 55.2% | 770,782 | 2,701 | +119.2 (466,642, 1,555) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_down_120` | +125.5 | +129.9 | -4.4 | -1.45 | +12.07 | 55.2% | 645,906 | 2,701 | +137.1 (392,072, 1,555) | STABLE_SIGN | single-window |
| `ts_up_20` | +110.3 | +114.5 | -4.2 | -2.49 | +14.98 | 55.1% | 731,619 | 2,701 | +122.7 (437,860, 1,555) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_down_60` | +133.5 | +129.8 | +3.7 | +1.44 | +12.70 | 55.4% | 649,444 | 2,701 | +151.3 (393,812, 1,555) | STABLE_SIGN | single-window |
| `cs_up_20` | +126.7 | +129.8 | -3.2 | -1.59 | +14.78 | 55.9% | 651,771 | 2,701 | +144.4 (394,990, 1,555) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_up_20` | +104.5 | +107.4 | -2.9 | -2.59 | +14.42 | 54.9% | 492,419 | 2,700 | +116.6 (291,283, 1,555) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_down_20` | +132.5 | +129.8 | +2.7 | +1.39 | +13.03 | 55.5% | 651,772 | 2,701 | +146.3 (394,990, 1,555) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_up_60` | +100.3 | +101.6 | -1.3 | -4.98 | +13.62 | 55.2% | 538,649 | 2,701 | +117.3 (324,510, 1,555) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_up_120` | +112.0 | +111.2 | +0.8 | -0.60 | +15.41 | 55.6% | 801,827 | 2,701 | +139.3 (484,585, 1,555) | STABLE_SIGN | single-window |
| `mom_neg` | +157.6 | +158.4 | -0.8 | -3.02 | +10.70 | 55.9% | 452,501 | 2,701 | +159.9 (277,486, 1,555) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ch52_high` | +102.0 | +102.4 | -0.4 | -3.54 | +14.69 | 56.1% | 430,595 | 2,699 | +118.9 (251,636, 1,555) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_pos` | +115.4 | +115.1 | +0.2 | -1.57 | +15.23 | 55.8% | 823,404 | 2,701 | +139.1 (498,721, 1,555) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_down_120` | +160.6 | +160.6 | -0.0 | -1.21 | +11.57 | 56.1% | 490,281 | 2,701 | +157.7 (299,566, 1,555) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |

## Horizon 20d — TS/CS rule expectancy (sorted by |within bps|)

| Rule | mean bps | market bps | within bps | t_within | t_date | hit% | n | dates | purged mean bps (n, dates) | stability | stability (within) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |
| `ch52_low` | +299.0 | +233.7 | +65.3 | +5.86 | +11.61 | 57.3% | 175,744 | 2,696 | +281.2 (108,998, 1,530) | STABLE_SIGN | single-window |
| `cs_top_quartile_120` | +213.4 | +173.0 | +40.3 | +7.68 | +18.98 | 56.5% | 323,405 | 2,696 | +242.5 (193,461, 1,530) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_60` | +206.2 | +172.9 | +33.3 | +5.85 | +14.57 | 55.5% | 325,145 | 2,696 | +226.0 (194,306, 1,530) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_20` | +199.4 | +172.9 | +26.5 | +5.60 | +14.91 | 55.5% | 326,301 | 2,696 | +216.8 (194,871, 1,530) | STABLE_SIGN | single-window |
| `ts_strong_down_60` | +270.5 | +245.3 | +25.1 | +2.59 | +14.38 | 58.3% | 287,735 | 2,693 | +280.0 (172,811, 1,527) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_120` | +197.3 | +173.0 | +24.3 | +4.30 | +14.00 | 55.4% | 323,405 | 2,696 | +205.5 (193,461, 1,530) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_top_quartile_20` | +190.8 | +172.9 | +17.9 | +3.68 | +17.62 | 55.9% | 326,298 | 2,696 | +216.4 (194,870, 1,530) | STABLE_SIGN | single-window |
| `ts_strong_down_120` | +224.7 | +209.3 | +15.4 | +0.12 | +12.23 | 57.3% | 249,375 | 2,696 | +218.8 (154,188, 1,530) | STABLE_SIGN | single-window |
| `cs_top_quartile_60` | +187.9 | +172.9 | +15.0 | +2.86 | +17.65 | 56.0% | 325,145 | 2,696 | +206.4 (194,306, 1,530) | STABLE_SIGN | single-window |
| `ts_down_60` | +228.4 | +220.2 | +8.2 | -0.17 | +14.43 | 57.3% | 526,834 | 2,696 | +234.9 (315,433, 1,530) | STABLE_SIGN | single-window |
| `below_ma_50` | +216.4 | +208.5 | +7.9 | +1.65 | +15.10 | 57.1% | 549,428 | 2,696 | +232.5 (332,394, 1,530) | STABLE_SIGN | single-window |
| `above_ma_50` | +139.5 | +146.7 | -7.3 | -4.43 | +16.99 | 55.7% | 748,614 | 2,696 | +159.3 (443,150, 1,530) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_up_120` | +180.3 | +173.0 | +7.3 | +2.17 | +18.20 | 56.9% | 644,576 | 2,696 | +205.2 (385,707, 1,530) | STABLE_SIGN | single-window |
| `ts_up_60` | +133.7 | +140.4 | -6.7 | -6.04 | +16.34 | 55.6% | 769,347 | 2,696 | +160.5 (459,223, 1,530) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_down_20` | +216.7 | +210.1 | +6.6 | +3.28 | +14.79 | 57.6% | 332,959 | 2,696 | +234.1 (201,596, 1,530) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_up_60` | +166.8 | +172.8 | -6.1 | -2.06 | +17.29 | 56.6% | 648,115 | 2,696 | +183.2 (387,408, 1,530) | STABLE_SIGN | single-window |
| `cs_down_120` | +167.0 | +173.0 | -6.0 | -1.78 | +14.23 | 55.7% | 644,576 | 2,696 | +179.1 (385,707, 1,530) | STABLE_SIGN | single-window |
| `ts_down_20` | +206.3 | +200.6 | +5.7 | +3.34 | +15.79 | 57.1% | 568,433 | 2,696 | +224.0 (345,241, 1,530) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_up_20` | +167.4 | +172.9 | -5.5 | -2.34 | +16.97 | 56.4% | 650,441 | 2,696 | +188.9 (388,578, 1,530) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_up_120` | +148.5 | +143.0 | +5.4 | +0.41 | +17.63 | 56.2% | 570,610 | 2,696 | +188.0 (339,648, 1,530) | STABLE_SIGN | single-window |
| `ts_up_20` | +146.0 | +151.3 | -5.3 | -2.89 | +17.30 | 55.6% | 730,861 | 2,696 | +164.2 (430,956, 1,530) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_down_60` | +177.7 | +172.8 | +4.9 | +1.67 | +14.94 | 56.0% | 648,114 | 2,696 | +198.3 (387,407, 1,530) | STABLE_SIGN | single-window |
| `cs_down_20` | +177.5 | +172.9 | +4.6 | +2.01 | +15.40 | 56.1% | 650,442 | 2,696 | +192.9 (388,578, 1,530) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_up_20` | +138.1 | +142.2 | -4.1 | -2.84 | +16.68 | 55.4% | 492,023 | 2,695 | +156.9 (286,792, 1,530) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_up_120` | +148.6 | +147.7 | +0.9 | -0.57 | +17.69 | 56.1% | 800,161 | 2,696 | +187.1 (476,693, 1,530) | STABLE_SIGN | single-window |
| `ch52_high` | +135.5 | +134.7 | +0.9 | -4.09 | +17.10 | 56.7% | 430,049 | 2,694 | +164.2 (247,971, 1,530) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_up_60` | +134.9 | +135.6 | -0.7 | -5.80 | +15.85 | 55.8% | 537,665 | 2,696 | +162.8 (319,564, 1,530) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_pos` | +152.3 | +152.8 | -0.5 | -2.23 | +17.67 | 56.2% | 821,452 | 2,696 | +181.8 (490,825, 1,530) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_neg` | +212.2 | +211.9 | +0.4 | -3.53 | +12.44 | 56.7% | 451,789 | 2,696 | +212.0 (272,731, 1,530) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_down_120` | +214.7 | +214.5 | +0.3 | -1.08 | +13.56 | 56.8% | 489,282 | 2,696 | +200.6 (294,713, 1,530) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |

## Horizon 60d — TS/CS rule expectancy (sorted by |within bps|)

| Rule | mean bps | market bps | within bps | t_within | t_date | hit% | n | dates | purged mean bps (n, dates) | stability | stability (within) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |
| `cs_top_quartile_120` | +664.4 | +518.8 | +145.6 | +16.86 | +33.39 | 59.8% | 318,077 | 2,656 | +727.5 (167,927, 1,330) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ch52_low` | +789.5 | +658.1 | +131.3 | +6.38 | +19.56 | 60.4% | 173,779 | 2,656 | +536.0 (91,758, 1,330) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_60` | +608.4 | +517.9 | +90.6 | +9.05 | +25.58 | 59.2% | 319,817 | 2,656 | +561.4 (168,664, 1,330) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_bottom_quartile_20` | +599.1 | +517.9 | +81.3 | +8.66 | +26.12 | 58.7% | 320,973 | 2,656 | +590.4 (169,179, 1,330) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_top_quartile_60` | +594.5 | +517.9 | +76.6 | +8.19 | +30.82 | 58.9% | 319,817 | 2,656 | +657.7 (168,664, 1,330) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_top_quartile_20` | +575.4 | +517.9 | +57.5 | +6.51 | +29.16 | 59.1% | 320,970 | 2,656 | +610.6 (169,179, 1,330) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_down_60` | +713.1 | +666.9 | +46.2 | +0.21 | +24.64 | 62.0% | 284,583 | 2,653 | +568.8 (153,832, 1,327) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_120` | +558.5 | +518.8 | +39.7 | +4.53 | +24.38 | 58.3% | 318,077 | 2,656 | +513.0 (167,927, 1,330) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_up_120` | +552.7 | +518.4 | +34.3 | +6.92 | +32.56 | 60.6% | 633,936 | 2,656 | +598.6 (334,810, 1,330) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_up_120` | +493.9 | +464.0 | +29.9 | +5.80 | +30.56 | 60.0% | 560,416 | 2,656 | +644.9 (301,466, 1,330) | STABLE_SIGN | single-window |
| `cs_down_120` | +490.8 | +518.4 | -27.6 | -5.54 | +26.00 | 59.3% | 633,936 | 2,656 | +469.4 (334,810, 1,330) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_down_20` | +648.2 | +625.8 | +22.5 | +3.08 | +24.80 | 61.2% | 327,898 | 2,656 | +593.5 (173,165, 1,330) | STABLE_SIGN | single-window |
| `ts_down_60` | +651.2 | +629.2 | +21.9 | -0.97 | +26.78 | 61.6% | 519,803 | 2,656 | +537.4 (275,784, 1,330) | STABLE_SIGN | single-window |
| `below_ma_50` | +634.2 | +617.1 | +17.0 | -0.64 | +27.58 | 61.2% | 541,536 | 2,656 | +558.1 (287,937, 1,330) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_down_120` | +568.8 | +583.2 | -14.4 | -1.44 | +25.23 | 59.9% | 482,915 | 2,656 | +407.0 (250,510, 1,330) | STABLE_SIGN | single-window |
| `mom_neg` | +636.3 | +622.0 | +14.2 | -2.56 | +22.75 | 61.1% | 445,517 | 2,656 | +562.2 (235,835, 1,330) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_up_120` | +492.9 | +478.7 | +14.2 | +3.39 | +31.74 | 60.0% | 785,243 | 2,656 | +610.1 (419,065, 1,330) | STABLE_SIGN | single-window |
| `ts_up_60` | +427.9 | +441.4 | -13.5 | -5.48 | +29.22 | 58.7% | 755,091 | 2,656 | +526.7 (396,677, 1,330) | STABLE_SIGN | single-window |
| `cs_down_60` | +530.0 | +517.9 | +12.1 | +2.33 | +27.23 | 60.0% | 637,474 | 2,656 | +515.5 (336,284, 1,330) | STABLE_SIGN | single-window |
| `above_ma_50` | +432.8 | +444.7 | -11.9 | -6.33 | +29.51 | 58.8% | 735,218 | 2,656 | +509.3 (385,272, 1,330) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_up_20` | +507.1 | +517.9 | -10.8 | -2.12 | +29.82 | 59.9% | 639,801 | 2,656 | +530.2 (337,316, 1,330) | STABLE_SIGN | single-window |
| `ts_down_20` | +603.0 | +592.8 | +10.3 | +1.84 | +27.77 | 60.7% | 559,620 | 2,656 | +566.2 (296,993, 1,330) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_up_60` | +508.2 | +517.9 | -9.8 | -1.86 | +30.54 | 59.7% | 637,475 | 2,656 | +547.1 (336,285, 1,330) | STABLE_SIGN | single-window |
| `cs_down_20` | +527.5 | +517.9 | +9.7 | +1.90 | +27.73 | 59.7% | 639,802 | 2,656 | +527.6 (337,316, 1,330) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_up_20` | +450.1 | +459.6 | -9.4 | -4.72 | +29.60 | 59.1% | 718,397 | 2,656 | +498.5 (376,807, 1,330) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_down_120` | +535.7 | +544.3 | -8.5 | -0.93 | +22.28 | 58.8% | 246,596 | 2,656 | +379.7 (132,247, 1,330) | STABLE_SIGN | single-window |
| `mom_pos` | +458.7 | +464.7 | -6.0 | -3.21 | +32.03 | 59.4% | 806,469 | 2,656 | +521.2 (426,713, 1,330) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_up_60` | +421.8 | +416.8 | +5.0 | -2.42 | +27.82 | 58.5% | 527,833 | 2,656 | +545.0 (276,336, 1,330) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ch52_high` | +424.3 | +420.3 | +4.0 | -4.97 | +31.80 | 60.3% | 423,656 | 2,654 | +543.3 (217,284, 1,330) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_up_20` | +436.0 | +438.3 | -2.3 | -3.49 | +28.56 | 58.9% | 483,729 | 2,655 | +496.4 (250,963, 1,330) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |

## Horizon 120d — TS/CS rule expectancy (sorted by |within bps|)

| Rule | mean bps | market bps | within bps | t_within | t_date | hit% | n | dates | purged mean bps (n, dates) | stability | stability (within) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |
| `cs_top_quartile_120` | +1393.6 | +1032.2 | +361.4 | +30.17 | +48.18 | 63.5% | 310,097 | 2,596 | +1592.4 (129,775, 1,030) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_top_quartile_60` | +1302.6 | +1030.6 | +272.0 | +20.61 | +44.82 | 62.3% | 311,837 | 2,596 | +1632.4 (130,354, 1,030) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_top_quartile_20` | +1223.1 | +1030.0 | +193.0 | +14.83 | +41.79 | 61.6% | 312,990 | 2,596 | +1465.1 (130,761, 1,030) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ch52_low` | +1242.7 | +1127.2 | +115.5 | +6.88 | +25.36 | 60.6% | 168,398 | 2,596 | +954.1 (62,622, 1,030) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_bottom_quartile_20` | +1135.5 | +1030.0 | +105.5 | +8.00 | +36.10 | 61.2% | 312,993 | 2,596 | +1160.7 (130,761, 1,030) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `cs_up_120` | +1132.7 | +1031.9 | +100.8 | +16.49 | +46.37 | 63.8% | 617,976 | 2,596 | +1280.3 (258,705, 1,030) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_down_120` | +954.2 | +1053.4 | -99.3 | -5.60 | +30.01 | 60.4% | 239,720 | 2,596 | +865.0 (96,011, 1,030) | STABLE_SIGN | single-window |
| `cs_down_120` | +939.8 | +1031.9 | -92.1 | -14.82 | +37.51 | 61.7% | 617,976 | 2,596 | +980.9 (258,705, 1,030) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_up_120` | +1067.7 | +992.7 | +75.0 | +10.67 | +40.34 | 63.9% | 546,594 | 2,596 | +1336.9 (238,950, 1,030) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_down_120` | +1026.3 | +1092.1 | -65.8 | -4.02 | +34.14 | 61.6% | 470,459 | 2,596 | +904.2 (186,507, 1,030) | STABLE_SIGN | single-window |
| `cs_bottom_quartile_60` | +1095.6 | +1030.6 | +65.0 | +4.73 | +33.67 | 60.6% | 311,837 | 2,596 | +1035.2 (130,354, 1,030) | STABLE_SIGN | single-window |
| `cs_up_60` | +1090.2 | +1030.3 | +59.9 | +7.69 | +45.34 | 63.2% | 621,515 | 2,596 | +1285.2 (259,921, 1,030) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_strong_up_60` | +1034.5 | +981.9 | +52.6 | +6.34 | +37.17 | 63.0% | 515,663 | 2,596 | +1400.3 (226,346, 1,030) | STABLE_SIGN | single-window |
| `cs_down_60` | +979.0 | +1030.3 | -51.3 | -6.69 | +37.42 | 62.2% | 621,514 | 2,596 | +970.3 (259,920, 1,030) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ts_up_120` | +1042.1 | +995.2 | +46.9 | +10.69 | +44.31 | 63.5% | 765,781 | 2,596 | +1257.6 (330,849, 1,030) | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `mom_neg` | +1226.1 | +1187.5 | +38.5 | -1.85 | +33.57 | 64.0% | 436,008 | 2,596 | +1418.2 (182,993, 1,030) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_up_20` | +981.9 | +956.0 | +25.9 | +4.86 | +38.12 | 62.2% | 472,210 | 2,595 | +1241.7 (194,300, 1,030) | STABLE_SIGN | single-window |
| `mom_pos` | +926.8 | +951.9 | -25.1 | -7.26 | +45.23 | 62.2% | 784,253 | 2,596 | +970.1 (328,870, 1,030) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_up_20` | +1052.8 | +1030.1 | +22.7 | +3.12 | +43.26 | 62.8% | 623,841 | 2,596 | +1209.3 (260,725, 1,030) | STABLE_SIGN | single-window |
| `cs_down_20` | +1009.6 | +1030.1 | -20.5 | -2.82 | +39.23 | 62.4% | 623,842 | 2,596 | +1034.9 (260,725, 1,030) | STABLE_SIGN | single-window |
| `ts_up_60` | +1003.1 | +986.0 | +17.1 | +3.47 | +42.51 | 62.8% | 737,189 | 2,596 | +1300.3 (319,400, 1,030) | STABLE_SIGN | single-window |
| `ts_down_60` | +1079.9 | +1095.3 | -15.5 | -2.49 | +34.30 | 62.5% | 505,794 | 2,596 | +851.1 (200,294, 1,030) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_down_60` | +1105.6 | +1118.2 | -12.5 | -1.83 | +30.30 | 62.2% | 277,038 | 2,593 | +774.9 (109,810, 1,027) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `above_ma_50` | +983.5 | +972.7 | +10.8 | +1.39 | +42.23 | 62.5% | 717,274 | 2,596 | +1264.6 (303,519, 1,030) | STABLE_SIGN | single-window |
| `ts_down_20` | +1092.1 | +1101.1 | -9.1 | -0.86 | +40.28 | 63.0% | 545,447 | 2,596 | +1001.9 (227,859, 1,030) | STABLE_SIGN | single-window |
| `ch52_high` | +927.1 | +918.8 | +8.3 | -3.39 | +46.88 | 64.0% | 414,520 | 2,594 | +1163.1 (173,875, 1,030) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_strong_down_20` | +1125.1 | +1133.3 | -8.2 | -0.13 | +35.93 | 63.1% | 319,851 | 2,596 | +941.6 (132,020, 1,030) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ts_up_20` | +982.9 | +975.1 | +7.7 | +1.42 | +42.09 | 62.3% | 700,674 | 2,596 | +1213.2 (292,915, 1,030) | STABLE_SIGN | single-window |
| `below_ma_50` | +1101.8 | +1108.7 | -6.9 | -3.10 | +38.86 | 62.9% | 527,560 | 2,596 | +931.9 (216,792, 1,030) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `cs_bottom_quartile_120` | +1031.2 | +1032.2 | -1.0 | +0.38 | +34.57 | 60.3% | 310,097 | 2,596 | +1052.6 (129,775, 1,030) | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |

## Condition-level comparison with Step 4

Step 4's own-history *position* conditions re-evaluated through the identical machinery — these are the same numbers Step 4 reports, repeated here so the TS-vs-CS reading sits next to the condition-level one instead of requiring two documents.

| Condition | Horizon | mean bps | market bps | within bps | t_within | stability | stability (within) |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- | :--- |
| `above_ma_50` | 5d | +35.7 | +38.0 | -2.2 | -2.03 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `above_ma_50` | 20d | +139.5 | +146.7 | -7.3 | -4.43 | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `above_ma_50` | 60d | +432.8 | +444.7 | -11.9 | -6.33 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `above_ma_50` | 120d | +983.5 | +972.7 | +10.8 | +1.39 | STABLE_SIGN | single-window |
| `below_ma_50` | 5d | +51.6 | +49.2 | +2.4 | +1.99 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `below_ma_50` | 20d | +216.4 | +208.5 | +7.9 | +1.65 | STABLE_SIGN | single-window |
| `below_ma_50` | 60d | +634.2 | +617.1 | +17.0 | -0.64 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `below_ma_50` | 120d | +1101.8 | +1108.7 | -6.9 | -3.10 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ch52_high` | 5d | +33.0 | +34.0 | -1.0 | -2.11 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ch52_high` | 20d | +135.5 | +134.7 | +0.9 | -4.09 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ch52_high` | 60d | +424.3 | +420.3 | +4.0 | -4.97 | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ch52_high` | 120d | +927.1 | +918.8 | +8.3 | -3.39 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `ch52_low` | 5d | +71.1 | +54.0 | +17.2 | +3.94 | STABLE_SIGN | single-window |
| `ch52_low` | 20d | +299.0 | +233.7 | +65.3 | +5.86 | STABLE_SIGN | single-window |
| `ch52_low` | 60d | +789.5 | +658.1 | +131.3 | +6.38 | STABLE_SIGN | STABLE_SIGN_WITHIN |
| `ch52_low` | 120d | +1242.7 | +1127.2 | +115.5 | +6.88 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_pos` | 5d | +38.4 | +37.6 | +0.7 | -0.24 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_pos` | 20d | +152.3 | +152.8 | -0.5 | -2.23 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_pos` | 60d | +458.7 | +464.7 | -6.0 | -3.21 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_pos` | 120d | +926.8 | +951.9 | -25.1 | -7.26 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_neg` | 5d | +51.1 | +52.6 | -1.5 | -1.81 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_neg` | 20d | +212.2 | +211.9 | +0.4 | -3.53 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_neg` | 60d | +636.3 | +622.0 | +14.2 | -2.56 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |
| `mom_neg` | 120d | +1226.1 | +1187.5 | +38.5 | -1.85 | STABLE_SIGN | UNSTABLE_SIGN_WITHIN |

## Findings summary (TS vs CS)

- TS rule × horizon cells: 96; CS rule × horizon cells: 96.
- Cells whose *within-date* component passed the stable-sign clause: TS 5, CS 25.
- Mean |within bps| across TS cells: 9.2; across CS cells: 25.6 (cross-sectionally framed rules are, on this panel, the larger 'which name' effect).
- Raw `mean bps` is dominated by the market component for every rule and horizon: the own-history rules mostly identify *when*, not *which*, and the when is the CAD market drift shared by the whole equal-weight universe.
- Null and insufficient cases are recorded in each horizon table rather than dropped.

## Limits

- Descriptive only: no model, no threshold tuned on forward returns, no multiplicity correction across cells, no claim of causality and no cost/net-expectancy claim (that is Step 6).
- The TS rules use only a symbol's own trailing returns and trailing vol; the CS rules use the same trailing return ranked within date. Neither uses any forward information.
- Purge: `max(20td, horizon)` embargo and the label-end rule inside each validation block, identical to Step 4; the fold sets are the same, so TS/CS and Step 4 numbers are directly comparable.
