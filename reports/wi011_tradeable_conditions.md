# WI-011 Step 6 — costs, frequency, concurrency (CAD)

- Generated (UTC): 2026-10-25T21:41:55Z
- Panel: 707,899 rows · 315 symbols · 2711 dates (10.76 years at 252 trading days/yr)
- Candidates carried in from Steps 4–5: 73 rule × horizon cells with a stable, positive *within-date* component and sufficient sample (direction pre-declared with each rule).

COST_ASSUMPTIONS: spread = per-name Corwin-Schultz 60d median (causal, lagged) falling back to the Amihud-proportional proxy `2*sqrt(amihud_20)*1e4`, counted once per round trip; commission = IBKR Canada fixed schedule (CAD 0.01/share, CAD 1.00 minimum per order, max 0.5% of trade value) on a CAD 5,000 position, charged on both sides; no separate slippage term — the spread estimate is assumed to contain it, and the 1.5x/2.0x scenarios bound that assumption.

- per-name spread inputs: Corwin-Schultz usable on 99.5% of rows (mean 37.9 bps where defined), Amihud proxy on 99.7% (mean 4.3 bps) — the fallback is used where CS is undefined; both are disclosed.
- cost sensitivity: spread x1.5 and x2.0, commission x1.0–x2.0 (the x1.0 numbers are the headline; the stress column is the robustness check a survivor must also pass).
- the *within-date* component is the criterion, not the raw mean: a long-only rule that fires on strong-market days inherits CAD market drift, and crediting that drift as edge would be wrong. The raw-mean net column is shown for transparency.

ANNUAL_FIRINGS envelope: 100–400 firings/year across the universe (a preference, per the plan, never a cap).
CONCURRENCY envelope: 4–12 positions for 5–15 trading-day holds; concurrency = mean simultaneous firing names × hold days, evaluated at the hold horizon.

## Candidate table (all candidates, sorted by net within-date expectancy)

| Rule | Hold | n | gross mean bps | market bps | within bps | t_within | spread bps | comm bps | round-trip cost bps | NET within bps | NET within @1.5x spread | NET raw bps | firings/yr | fires/day | concurrency (p90) | net | freq | conc |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |
| `cs_top_quartile_120` | 120d | 165,822 | +1491.9 | +1105.6 | +386.4 | +22.58 | 43.8 | 26.6 | 70.4 | +316.0 | +294.1 | +1421.6 | 15,414 | 64.0 | 7680 (9120) | pass | fail | fail |
| `cs_top_quartile_60` | 120d | 167,223 | +1397.3 | +1103.0 | +294.3 | +16.79 | 43.4 | 26.8 | 70.2 | +224.1 | +202.4 | +1327.1 | 15,544 | 64.5 | 7745 (9120) | pass | fail | fail |
| `cs_top_quartile_20` | 120d | 168,127 | +1286.7 | +1101.5 | +185.2 | +10.36 | 43.1 | 27.2 | 70.3 | +114.9 | +93.4 | +1216.4 | 15,628 | 64.9 | 7787 (9240) | pass | fail | fail |
| `liq_liquid` | 120d | 288,161 | +1198.7 | +1037.1 | +161.6 | +11.81 | 39.7 | 22.1 | 61.8 | +99.7 | +79.9 | +1136.8 | 26,786 | 111.2 | 13346 (21600) | pass | fail | fail |
| `cs_top_quartile_120` | 60d | 170,562 | +712.3 | +548.5 | +163.8 | +14.98 | 43.4 | 26.2 | 69.5 | +94.2 | +72.5 | +642.8 | 15,855 | 64.3 | 3860 (4560) | pass | fail | fail |
| `ch52_low` | 120d | 92,990 | +1340.7 | +1173.8 | +166.9 | +5.08 | 50.1 | 37.8 | 87.9 | +79.0 | +54.0 | +1252.8 | 8,644 | 35.9 | 4307 (7920) | pass | fail | fail |
| `cs_bottom_quartile_20` | 120d | 168,143 | +1251.4 | +1101.4 | +150.0 | +9.32 | 45.5 | 30.2 | 75.7 | +74.3 | +51.5 | +1175.7 | 15,630 | 64.9 | 7787 (9240) | pass | fail | fail |
| `cs_up_120` | 120d | 328,643 | +1238.5 | +1106.1 | +132.4 | +13.46 | 39.3 | 22.3 | 61.5 | +70.9 | +51.2 | +1177.0 | 30,549 | 126.8 | 15221 (18000) | pass | fail | fail |
| `ind_atr_pct_100_low` | 120d | 218,503 | +890.8 | +783.0 | +107.8 | +13.07 | 37.6 | 22.5 | 60.1 | +47.8 | +29.0 | +830.7 | 20,311 | 86.9 | 10430 (17880) | pass | fail | fail |
| `cs_top_quartile_60` | 60d | 171,963 | +649.8 | +546.7 | +103.2 | +8.54 | 43.0 | 26.3 | 69.4 | +33.8 | +12.3 | +580.5 | 15,985 | 64.9 | 3892 (4620) | pass | fail | fail |
| `ind_vwap_zscore_100_low` | 60d | 138,472 | +652.2 | +571.8 | +80.4 | +8.58 | 39.5 | 24.0 | 63.5 | +16.9 | -2.9 | +588.7 | 12,872 | 54.9 | 3294 (6060) | fail | fail | fail |
| `cs_bottom_quartile_20` | 60d | 172,883 | +637.6 | +546.7 | +90.9 | +8.87 | 45.0 | 29.8 | 74.8 | +16.1 | -6.4 | +562.8 | 16,070 | 65.2 | 3913 (4740) | fail | fail | fail |
| `liq_liquid` | 60d | 295,982 | +577.9 | +501.4 | +76.5 | +10.52 | 39.5 | 21.8 | 61.3 | +15.2 | -4.6 | +516.6 | 27,513 | 111.6 | 6699 (10800) | fail | fail | fail |
| `cs_bottom_quartile_60` | 60d | 171,967 | +635.8 | +546.6 | +89.2 | +7.81 | 45.6 | 30.3 | 75.9 | +13.2 | -9.6 | +559.9 | 15,985 | 64.9 | 3892 (4620) | fail | fail | fail |
| `ts_up_120` | 120d | 409,787 | +1128.0 | +1062.0 | +66.0 | +5.56 | 38.7 | 21.0 | 59.7 | +6.3 | -13.0 | +1068.3 | 38,092 | 158.2 | 18979 (27000) | fail | fail | fail |
| `cs_bottom_quartile_60` | 120d | 167,227 | +1179.9 | +1103.0 | +76.9 | +4.37 | 46.2 | 30.7 | 76.9 | +0.0 | -23.0 | +1103.0 | 15,545 | 64.5 | 7745 (9120) | fail | fail | fail |
| `cs_up_60` | 120d | 331,476 | +1161.1 | +1103.7 | +57.5 | +5.14 | 39.3 | 22.6 | 61.9 | -4.5 | -24.1 | +1099.2 | 30,812 | 127.9 | 15352 (18120) | fail | fail | fail |
| `cs_top_quartile_20` | 60d | 172,867 | +607.7 | +546.7 | +60.9 | +5.38 | 42.7 | 26.7 | 69.4 | -8.5 | -29.8 | +538.2 | 16,069 | 65.2 | 3912 (4740) | fail | fail | fail |
| `cs_up_120` | 60d | 338,063 | +598.7 | +548.7 | +50.0 | +7.96 | 39.0 | 21.9 | 60.9 | -10.9 | -30.4 | +537.8 | 31,425 | 127.5 | 7651 (9060) | fail | fail | fail |
| `cs_top_quartile_120` | 20d | 173,722 | +231.9 | +181.7 | +50.2 | +7.67 | 43.1 | 25.9 | 69.0 | -18.8 | -40.3 | +162.9 | 16,148 | 64.6 | 1291 (1540) | fail | fail | fail |
| `trend_up_vol_low` | 120d | 119,145 | +909.7 | +877.7 | +32.0 | +8.47 | 37.6 | 21.1 | 58.7 | -26.7 | -45.5 | +851.0 | 11,075 | 46.9 | 5629 (11040) | fail | fail | fail |
| `cs_top_quartile_120` | 15d | 174,117 | +172.8 | +136.1 | +36.6 | +6.24 | 43.1 | 25.9 | 68.9 | -32.3 | -53.8 | +103.9 | 16,185 | 64.6 | 969 (1155) | fail | fail | fail |
| `trend_down_vol_high` | 10d | 82,107 | +137.2 | +103.1 | +34.1 | +5.74 | 41.0 | 25.5 | 66.5 | -32.4 | -52.8 | +70.7 | 7,632 | 30.5 | 305 (700) | fail | fail | fail |
| `ind_fib_dist_f102_high` | 120d | 151,821 | +1066.0 | +1033.6 | +32.4 | +0.06 | 40.8 | 24.0 | 64.8 | -32.5 | -52.9 | +1001.2 | 14,112 | 60.2 | 7224 (12840) | fail | fail | fail |
| `ts_strong_down_60` | 15d | 153,418 | +195.0 | +159.1 | +35.8 | +4.34 | 41.5 | 27.1 | 68.6 | -32.7 | -53.5 | +126.4 | 14,261 | 56.9 | 854 (1485) | fail | fail | fail |
| `ind_fib_dist_f102_low` | 15d | 151,528 | +160.6 | +132.9 | +27.8 | +5.15 | 38.4 | 23.1 | 61.5 | -33.7 | -52.9 | +99.2 | 14,085 | 57.7 | 865 (1605) | fail | fail | fail |
| `ind_pct_from_high_f102_low` | 10d | 152,602 | +128.3 | +101.3 | +27.0 | +4.94 | 38.3 | 23.3 | 61.6 | -34.6 | -53.7 | +66.7 | 14,185 | 58.0 | 580 (1170) | fail | fail | fail |
| `cs_bottom_quartile_60` | 20d | 175,127 | +221.3 | +181.5 | +39.9 | +6.55 | 45.4 | 30.0 | 75.4 | -35.5 | -58.2 | +146.0 | 16,279 | 65.1 | 1302 (1580) | fail | fail | fail |
| `liq_liquid` | 20d | 300,852 | +189.2 | +165.7 | +23.4 | +3.79 | 39.4 | 21.6 | 61.0 | -37.6 | -57.3 | +128.1 | 27,966 | 111.8 | 2236 (3580) | fail | fail | fail |
| `cs_top_quartile_60` | 20d | 175,123 | +210.8 | +181.5 | +29.3 | +4.58 | 42.7 | 26.1 | 68.7 | -39.4 | -60.8 | +142.0 | 16,278 | 65.1 | 1302 (1580) | fail | fail | fail |
| `ind_fib_dist_f102_low` | 10d | 151,528 | +106.0 | +84.0 | +22.0 | +5.26 | 38.4 | 23.1 | 61.5 | -39.5 | -58.7 | +44.5 | 14,085 | 57.7 | 577 (1070) | fail | fail | fail |
| `cs_bottom_quartile_60` | 15d | 175,522 | +170.0 | +136.1 | +34.0 | +6.28 | 45.3 | 30.0 | 75.3 | -41.3 | -64.0 | +94.8 | 16,316 | 65.1 | 977 (1185) | fail | fail | fail |
| `ts_strong_down_60` | 10d | 153,872 | +127.6 | +100.6 | +26.9 | +4.23 | 41.4 | 27.1 | 68.5 | -41.5 | -62.3 | +59.1 | 14,303 | 57.0 | 570 (990) | fail | fail | fail |
| `trend_down_vol_high` | 5d | 82,262 | +66.8 | +42.4 | +24.4 | +5.68 | 40.9 | 25.5 | 66.4 | -42.1 | -62.5 | +0.3 | 7,647 | 30.5 | 152 (350) | fail | fail | fail |
| `liq_liquid` | 15d | 301,493 | +144.1 | +125.9 | +18.2 | +3.82 | 39.3 | 21.6 | 61.0 | -42.7 | -62.4 | +83.2 | 28,025 | 111.8 | 1677 (2685) | fail | fail | fail |
| `dollarvol_high` | 20d | 296,407 | +213.3 | +196.5 | +16.9 | +4.14 | 38.0 | 21.7 | 59.7 | -42.8 | -61.8 | +153.7 | 27,552 | 110.1 | 2203 (3520) | fail | fail | fail |
| `ind_pct_from_high_f102_low` | 5d | 152,602 | +67.9 | +49.6 | +18.2 | +5.40 | 38.3 | 23.3 | 61.6 | -43.3 | -62.5 | +6.3 | 14,185 | 58.0 | 290 (585) | fail | fail | fail |
| `ind_vwap_zscore_100_low` | 20d | 141,311 | +207.0 | +188.1 | +18.9 | +4.98 | 39.4 | 23.7 | 63.1 | -44.2 | -63.9 | +143.9 | 13,136 | 55.2 | 1103 (2020) | fail | fail | fail |
| `cs_top_quartile_120` | 10d | 174,512 | +113.9 | +89.6 | +24.2 | +5.06 | 43.0 | 25.8 | 68.9 | -44.6 | -66.1 | +45.0 | 16,222 | 64.6 | 646 (770) | fail | fail | fail |
| `cs_bottom_quartile_20` | 15d | 176,438 | +164.4 | +136.0 | +28.5 | +5.90 | 44.8 | 29.4 | 74.2 | -45.7 | -68.1 | +90.3 | 16,401 | 65.4 | 982 (1185) | fail | fail | fail |
| `dollarvol_high` | 15d | 297,035 | +161.6 | +147.9 | +13.7 | +4.06 | 37.9 | 21.7 | 59.6 | -45.9 | -64.9 | +102.0 | 27,611 | 110.2 | 1653 (2640) | fail | fail | fail |
| `ind_atr_pct_100_high` | 10d | 147,220 | +136.5 | +118.1 | +18.5 | +3.40 | 40.7 | 23.7 | 64.5 | -46.0 | -66.4 | +72.1 | 13,685 | 55.9 | 559 (1470) | fail | fail | fail |
| `ind_fib_dist_f102_low` | 5d | 151,528 | +56.1 | +40.9 | +15.3 | +5.40 | 38.4 | 23.1 | 61.5 | -46.2 | -65.4 | -5.4 | 14,085 | 57.7 | 288 (535) | fail | fail | fail |
| `cs_up_120` | 20d | 344,343 | +195.6 | +182.0 | +13.6 | +3.45 | 38.8 | 21.7 | 60.5 | -46.9 | -66.3 | +135.1 | 32,008 | 128.0 | 2559 (3080) | fail | fail | fail |
| `dollarvol_high` | 10d | 297,614 | +108.5 | +97.2 | +11.2 | +4.37 | 37.9 | 21.7 | 59.6 | -48.3 | -67.3 | +48.9 | 27,665 | 110.2 | 1102 (1760) | fail | fail | fail |
| `cs_bottom_quartile_20` | 10d | 176,833 | +114.1 | +89.6 | +24.5 | +6.19 | 44.7 | 29.4 | 74.1 | -49.5 | -71.9 | +40.0 | 16,437 | 65.5 | 655 (790) | fail | fail | fail |
| `ind_atr_pct_100_high` | 5d | 147,220 | +71.2 | +57.2 | +14.0 | +3.62 | 40.7 | 23.7 | 64.5 | -50.5 | -70.8 | +6.7 | 13,685 | 55.9 | 280 (735) | fail | fail | fail |
| `ind_vwap_zscore_100_low` | 5d | 141,311 | +53.6 | +41.2 | +12.5 | +5.16 | 39.4 | 23.7 | 63.1 | -50.7 | -70.4 | -9.5 | 13,136 | 55.2 | 276 (505) | fail | fail | fail |
| `cs_bottom_quartile_60` | 10d | 175,917 | +114.1 | +89.7 | +24.4 | +5.60 | 45.3 | 29.9 | 75.2 | -50.8 | -73.4 | +38.9 | 16,352 | 65.1 | 651 (790) | fail | fail | fail |
| `vol_high` | 15d | 223,751 | +181.6 | +170.8 | +10.8 | +5.16 | 39.1 | 23.3 | 62.4 | -51.6 | -71.2 | +119.2 | 20,799 | 83.0 | 1245 (3030) | fail | fail | fail |
| `ts_strong_down_60` | 5d | 154,317 | +64.2 | +48.4 | +15.8 | +4.00 | 41.4 | 27.0 | 68.4 | -52.6 | -73.3 | -4.2 | 14,344 | 57.0 | 285 (495) | fail | fail | fail |
| `ind_pct_from_high_f102_low` | 2d | 152,602 | +27.8 | +18.8 | +9.0 | +4.81 | 38.3 | 23.3 | 61.6 | -52.6 | -71.8 | -33.8 | 14,185 | 58.0 | 116 (234) | fail | fail | fail |
| `dollarvol_high` | 5d | 298,213 | +54.7 | +47.8 | +6.9 | +3.88 | 37.9 | 21.6 | 59.5 | -52.6 | -71.6 | -4.9 | 27,720 | 110.2 | 551 (878) | fail | fail | fail |
| `ind_fib_dist_f102_low` | 2d | 151,528 | +23.5 | +15.2 | +8.2 | +4.97 | 38.4 | 23.1 | 61.5 | -53.3 | -72.5 | -38.0 | 14,085 | 57.7 | 115 (214) | fail | fail | fail |
| `vol_high` | 10d | 224,027 | +117.0 | +108.5 | +8.5 | +5.12 | 39.1 | 23.3 | 62.3 | -53.8 | -73.4 | +54.6 | 20,824 | 82.9 | 829 (2020) | fail | fail | fail |
| `cs_bottom_quartile_20` | 5d | 177,228 | +64.6 | +44.4 | +20.1 | +6.55 | 44.6 | 29.3 | 74.0 | -53.8 | -76.2 | -9.4 | 16,474 | 65.5 | 327 (395) | fail | fail | fail |
| `trend_down_vol_high` | 2d | 82,367 | +27.4 | +14.9 | +12.5 | +4.40 | 40.9 | 25.5 | 66.4 | -53.9 | -74.3 | -39.0 | 7,656 | 30.5 | 61 (140) | fail | fail | fail |
| `vol_high` | 5d | 224,344 | +61.2 | +54.5 | +6.7 | +5.04 | 39.1 | 23.2 | 62.3 | -55.6 | -75.2 | -1.1 | 20,854 | 82.9 | 415 (1008) | fail | fail | fail |
| `dollarvol_high` | 2d | 298,581 | +22.4 | +19.1 | +3.3 | +2.98 | 37.9 | 21.6 | 59.5 | -56.2 | -75.1 | -37.1 | 27,754 | 110.2 | 220 (350) | fail | fail | fail |
| `ind_pct_from_high_f102_low` | 1d | 152,602 | +14.4 | +9.2 | +5.1 | +4.15 | 38.3 | 23.3 | 61.6 | -56.5 | -75.6 | -47.2 | 14,185 | 58.0 | 58 (117) | fail | fail | fail |
| `ind_fib_dist_f102_low` | 1d | 151,528 | +12.4 | +7.5 | +4.9 | +4.63 | 38.4 | 23.1 | 61.5 | -56.6 | -75.8 | -49.1 | 14,085 | 57.7 | 58 (107) | fail | fail | fail |
| `trend_chop` | 20d | 267,167 | +183.3 | +175.4 | +7.9 | +3.88 | 40.5 | 24.1 | 64.6 | -56.7 | -77.0 | +118.7 | 24,834 | 99.3 | 1986 (2660) | fail | fail | fail |
| `ind_atr_pct_100_high` | 2d | 147,220 | +29.4 | +22.0 | +7.4 | +4.01 | 40.7 | 23.7 | 64.5 | -57.0 | -77.4 | -35.0 | 13,685 | 55.9 | 112 (294) | fail | fail | fail |
| `cs_down_20` | 5d | 351,418 | +52.0 | +44.5 | +7.6 | +4.51 | 40.5 | 24.2 | 64.7 | -57.1 | -77.3 | -12.6 | 32,666 | 129.9 | 649 (780) | fail | fail | fail |
| `vol_high` | 2d | 224,568 | +24.9 | +21.3 | +3.6 | +4.06 | 39.1 | 23.2 | 62.3 | -58.7 | -78.3 | -37.4 | 20,875 | 82.9 | 166 (402) | fail | fail | fail |
| `cs_bottom_quartile_120` | 20d | 173,727 | +200.8 | +181.7 | +19.1 | +3.06 | 46.7 | 31.3 | 78.0 | -58.9 | -82.2 | +122.8 | 16,149 | 64.6 | 1291 (1540) | fail | fail | fail |
| `vol_high` | 1d | 224,637 | +12.8 | +10.5 | +2.3 | +3.71 | 39.1 | 23.2 | 62.3 | -59.9 | -79.5 | -49.4 | 20,881 | 82.9 | 83 (201) | fail | fail | fail |
| `ind_atr_pct_100_high` | 1d | 147,220 | +15.3 | +11.0 | +4.3 | +3.62 | 40.7 | 23.7 | 64.5 | -60.1 | -80.5 | -49.2 | 13,685 | 55.9 | 56 (147) | fail | fail | fail |
| `cs_bottom_quartile_60` | 5d | 176,312 | +58.9 | +44.5 | +14.4 | +4.35 | 45.3 | 29.9 | 75.1 | -60.7 | -83.4 | -16.2 | 16,389 | 65.2 | 326 (395) | fail | fail | fail |
| `ts_strong_down_60` | 2d | 154,566 | +25.4 | +17.9 | +7.5 | +3.24 | 41.4 | 27.0 | 68.3 | -60.8 | -81.5 | -42.9 | 14,368 | 57.1 | 114 (198) | fail | fail | fail |
| `cs_bottom_quartile_20` | 2d | 177,465 | +27.5 | +17.8 | +9.7 | +4.84 | 44.6 | 29.3 | 73.9 | -64.3 | -86.6 | -46.5 | 16,496 | 65.5 | 131 (158) | fail | fail | fail |
| `cs_bottom_quartile_60` | 2d | 176,549 | +25.3 | +17.8 | +7.5 | +3.68 | 45.2 | 29.9 | 75.1 | -67.6 | -90.2 | -49.8 | 16,411 | 65.2 | 130 (158) | fail | fail | fail |
| `cs_bottom_quartile_20` | 1d | 177,544 | +14.5 | +9.0 | +5.6 | +4.04 | 44.6 | 29.3 | 73.9 | -68.3 | -90.6 | -59.4 | 16,504 | 65.5 | 66 (79) | fail | fail | fail |

## Criterion outcomes

- candidates: 73
- pass net expectancy (within-date, positive under the 1.5x-spread stress, |t_within| > 2): 10
- pass frequency (100–400 firings/yr): 0
- pass concurrency (4–12 positions at 5–15d holds): 0
- pass all three with an eligible 5–15d hold: **0**

## Survivors

none survive costs at this universe size.

Explicit valid conclusion (the plan pre-authorises it). The binding constraints, in order:

1. **Concurrency / frequency.** The candidate rules fire on hundreds of names per day (median 65 fires/day), so a 5–15d hold implies concurrency far above the 12-position envelope and annual firings far above 400. They are *market states*, not triggers with a daily cadence — the plan's 100–400/yr preference describes a trigger, and a state that describes a third of the universe every day cannot be one.

2. **Net expectancy.** Even ignoring cadence, the within-date edge is comparable to or smaller than the round-trip cost: median within-date effect +23.4 bps against a median round-trip cost of 64.5 bps (spread + commission). Under the 1.5x-spread stress, 10 of 73 candidates would still show a positive *within-date* net effect, but none of those combine it with a tradeable cadence.


## What would have to change (for the human gate, not executed here)

- A **narrower trigger**: require the rule AND a further selection (e.g. only the highest-ranked names each day) to reach 0.4–1.6 fires/day. That is *screener design / portfolio construction*, explicitly out of scope for WI-011 and requiring a new plan.
- A **cheaper execution assumption**: only the CAD commission schedule and the spread estimate are modelled; a queue-following/limit-order assumption would lower the spread term, and the report shows how much (1.5x/2.0x columns).
- A **longer hold**: 5–15d is the plan's envelope; the raw within-date effects at 60/120d are larger, but the hold envelope and cost amortisation are then outside this step's stated criteria.

## Limits

- No optimisation, no backtest, no position sizing, no screener implementation: costs and frequency are applied to already-descriptive cells, and nothing here is tuned to make a survivor appear.
- The IBKR schedule parameters are assumptions recorded as constants in `scripts/wi011_tradeable_conditions.py` and must be confirmed by the admin; the notional assumption (CAD 5,000) drives the commission-in-bps conversion.
- The spread proxy is an estimate from daily bars (Corwin-Schultz, lagged causal) with an Amihud-proportional fallback; it is not a quote, and the stress columns carry that uncertainty.
