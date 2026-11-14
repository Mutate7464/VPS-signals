# WI-011 Step 6 — costs, frequency, concurrency (CAD)

- Generated (UTC): 2026-10-26T06:51:30Z
- Panel: 1,314,936 rows · 533 symbols · 2716 dates (10.78 years at 252 trading days/yr)
- Candidates carried in from Steps 4–5: 48 rule × horizon cells with a stable, positive *within-date* component and sufficient sample (direction pre-declared with each rule).

COST_ASSUMPTIONS: spread = per-name Corwin-Schultz 60d median (causal, lagged) falling back to the Amihud-proportional proxy `2*sqrt(amihud_20)*1e4`, counted once per round trip; commission = IBKR Canada fixed schedule (CAD 0.01/share, CAD 1.00 minimum per order, max 0.5% of trade value) on a CAD 5,000 position, charged on both sides; no separate slippage term — the spread estimate is assumed to contain it, and the 1.5x/2.0x scenarios bound that assumption.

- per-name spread inputs: Corwin-Schultz usable on 99.7% of rows (mean 24.2 bps where defined), Amihud proxy on 99.8% (mean 0.8 bps) — the fallback is used where CS is undefined; both are disclosed.
- cost sensitivity: spread x1.5 and x2.0, commission x1.0–x2.0 (the x1.0 numbers are the headline; the stress column is the robustness check a survivor must also pass).
- the *within-date* component is the criterion, not the raw mean: a long-only rule that fires on strong-market days inherits CAD market drift, and crediting that drift as edge would be wrong. The raw-mean net column is shown for transparency.

ANNUAL_FIRINGS envelope: 100–400 firings/year across the universe (a preference, per the plan, never a cap).
CONCURRENCY envelope: 4–12 positions for 5–15 trading-day holds; concurrency = mean simultaneous firing names × hold days, evaluated at the hold horizon.

## Candidate table (all candidates, sorted by net within-date expectancy)

| Rule | Hold | n | gross mean bps | market bps | within bps | t_within | spread bps | comm bps | round-trip cost bps | NET within bps | NET within @1.5x spread | NET raw bps | firings/yr | fires/day | concurrency (p90) | net | freq | conc |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |
| `cs_top_quartile_120` | 120d | 310,097 | +1393.6 | +1032.2 | +361.4 | +30.17 | 26.7 | 10.9 | 37.6 | +323.8 | +310.4 | +1356.0 | 28,772 | 119.5 | 14334 (15720) | pass | fail | fail |
| `cs_top_quartile_60` | 120d | 311,837 | +1302.6 | +1030.6 | +272.0 | +20.61 | 26.4 | 11.6 | 38.0 | +234.0 | +220.8 | +1264.6 | 28,933 | 120.1 | 14415 (15720) | pass | fail | fail |
| `cs_top_quartile_20` | 120d | 312,990 | +1223.1 | +1030.0 | +193.0 | +14.83 | 26.2 | 12.1 | 38.3 | +154.7 | +141.6 | +1184.8 | 29,040 | 120.6 | 14468 (15840) | pass | fail | fail |
| `cs_top_quartile_120` | 60d | 318,077 | +664.4 | +518.8 | +145.6 | +16.86 | 26.6 | 10.8 | 37.4 | +108.3 | +95.0 | +627.0 | 29,512 | 119.8 | 7185 (7860) | pass | fail | fail |
| `ch52_low` | 60d | 173,779 | +789.5 | +658.1 | +131.3 | +6.38 | 28.5 | 16.5 | 45.0 | +86.4 | +72.1 | +744.5 | 16,124 | 65.4 | 3926 (7680) | pass | fail | fail |
| `er_trending` | 120d | 109,735 | +1119.3 | +1016.8 | +102.5 | +6.89 | 23.4 | 11.7 | 35.1 | +67.4 | +55.7 | +1084.2 | 10,182 | 42.3 | 5074 (8880) | pass | fail | fail |
| `cs_up_120` | 120d | 617,976 | +1132.7 | +1031.9 | +100.8 | +16.49 | 24.1 | 10.2 | 34.3 | +66.5 | +54.4 | +1098.4 | 57,338 | 238.0 | 28566 (31200) | pass | fail | fail |
| `cs_bottom_quartile_20` | 120d | 312,993 | +1135.5 | +1030.0 | +105.5 | +8.00 | 27.3 | 13.8 | 41.1 | +64.4 | +50.8 | +1094.4 | 29,041 | 120.6 | 14468 (15840) | pass | fail | fail |
| `er_trending` | 60d | 111,846 | +592.4 | +498.8 | +93.6 | +7.28 | 23.4 | 11.6 | 35.0 | +58.5 | +46.8 | +557.3 | 10,377 | 42.1 | 2528 (4440) | pass | fail | fail |
| `liq_liquid` | 120d | 506,238 | +1039.9 | +945.9 | +94.0 | +14.44 | 25.2 | 10.9 | 36.1 | +57.9 | +45.3 | +1003.8 | 46,971 | 195.0 | 23401 (38760) | pass | fail | fail |
| `cs_bottom_quartile_60` | 60d | 319,817 | +608.4 | +517.9 | +90.6 | +9.05 | 28.0 | 14.2 | 42.2 | +48.4 | +34.4 | +566.2 | 29,674 | 120.4 | 7225 (7920) | pass | fail | fail |
| `dollarvol_high` | 120d | 490,804 | +1209.6 | +1128.9 | +80.7 | +18.76 | 24.0 | 11.1 | 35.1 | +45.6 | +33.6 | +1174.5 | 45,539 | 189.1 | 22687 (35580) | pass | fail | fail |
| `ts_strong_up_120` | 120d | 546,594 | +1067.7 | +992.7 | +75.0 | +10.67 | 24.2 | 9.7 | 33.9 | +41.1 | +29.0 | +1033.8 | 50,715 | 210.6 | 25266 (38040) | pass | fail | fail |
| `cs_bottom_quartile_20` | 60d | 320,973 | +599.1 | +517.9 | +81.3 | +8.66 | 27.2 | 13.6 | 40.8 | +40.4 | +26.8 | +558.3 | 29,781 | 120.8 | 7251 (7980) | pass | fail | fail |
| `cs_top_quartile_60` | 60d | 319,817 | +594.5 | +517.9 | +76.6 | +8.19 | 26.4 | 11.4 | 37.8 | +38.8 | +25.6 | +556.7 | 29,674 | 120.4 | 7225 (7920) | pass | fail | fail |
| `trend_down_vol_high` | 60d | 156,417 | +817.7 | +745.2 | +72.5 | +7.19 | 24.7 | 12.6 | 37.3 | +35.2 | +22.8 | +780.3 | 14,513 | 59.0 | 3540 (9180) | pass | fail | fail |
| `ch52_low_vol_high` | 15d | 105,460 | +277.1 | +202.8 | +74.2 | +4.29 | 27.7 | 16.3 | 44.0 | +30.3 | +16.4 | +233.1 | 9,785 | 40.1 | 602 (1428) | pass | fail | fail |
| `cs_up_60` | 120d | 621,515 | +1090.2 | +1030.3 | +59.9 | +7.69 | 24.2 | 10.6 | 34.7 | +25.2 | +13.1 | +1055.5 | 57,666 | 239.4 | 28730 (31320) | pass | fail | fail |
| `trend_down_vol_high` | 120d | 149,622 | +1319.8 | +1257.1 | +62.7 | +6.88 | 24.8 | 12.9 | 37.6 | +25.1 | +12.7 | +1282.1 | 13,882 | 57.7 | 6930 (18240) | pass | fail | fail |
| `cs_top_quartile_20` | 60d | 320,970 | +575.4 | +517.9 | +57.5 | +6.51 | 26.2 | 11.9 | 38.1 | +19.4 | +6.3 | +537.3 | 29,781 | 120.8 | 7251 (7980) | pass | fail | fail |
| `liq_liquid` | 60d | 515,776 | +490.3 | +435.2 | +55.0 | +8.88 | 25.2 | 10.9 | 36.1 | +19.0 | +6.4 | +454.2 | 47,856 | 194.2 | 11652 (19320) | pass | fail | fail |
| `ts_up_120` | 120d | 765,781 | +1042.1 | +995.2 | +46.9 | +10.69 | 23.9 | 10.2 | 34.1 | +12.8 | +0.8 | +1008.0 | 71,052 | 295.0 | 35398 (47400) | pass | fail | fail |
| `ch52_low_vol_high` | 10d | 105,581 | +171.7 | +122.2 | +49.5 | +4.08 | 27.7 | 16.3 | 44.0 | +5.6 | -8.3 | +127.7 | 9,796 | 40.1 | 401 (950) | fail | fail | fail |
| `cs_top_quartile_120` | 20d | 323,405 | +213.4 | +173.0 | +40.3 | +7.68 | 26.5 | 10.7 | 37.2 | +3.1 | -10.2 | +176.1 | 30,007 | 120.0 | 2399 (2640) | fail | fail | fail |
| `cs_up_120` | 60d | 633,936 | +552.7 | +518.4 | +34.3 | +6.92 | 24.1 | 10.1 | 34.2 | +0.1 | -11.9 | +518.6 | 58,819 | 238.7 | 14321 (15660) | fail | fail | fail |
| `cs_bottom_quartile_120` | 60d | 318,077 | +558.5 | +518.8 | +39.7 | +4.53 | 28.1 | 14.6 | 42.7 | -3.0 | -17.0 | +515.8 | 29,512 | 119.8 | 7185 (7860) | fail | fail | fail |
| `dollarvol_high` | 60d | 506,433 | +616.2 | +587.2 | +29.0 | +10.17 | 24.0 | 11.0 | 34.9 | -6.0 | -18.0 | +581.3 | 46,989 | 190.7 | 11441 (17670) | fail | fail | fail |
| `cs_top_quartile_120` | 15d | 324,075 | +161.2 | +129.9 | +31.2 | +6.66 | 26.5 | 10.7 | 37.2 | -6.0 | -19.3 | +123.9 | 30,069 | 120.0 | 1800 (1980) | fail | fail | fail |
| `trend_down_vol_high` | 15d | 158,897 | +216.7 | +186.6 | +30.1 | +6.25 | 24.7 | 12.5 | 37.2 | -7.1 | -19.5 | +179.5 | 14,743 | 58.9 | 884 (2258) | fail | fail | fail |
| `cs_bottom_quartile_60` | 20d | 325,145 | +206.2 | +172.9 | +33.3 | +5.85 | 27.8 | 14.1 | 41.9 | -8.6 | -22.6 | +164.2 | 30,168 | 120.6 | 2412 (2640) | fail | fail | fail |
| `er_trending` | 20d | 113,369 | +177.4 | +155.1 | +22.3 | +3.24 | 23.4 | 11.5 | 34.9 | -12.6 | -24.3 | +142.5 | 10,519 | 42.1 | 841 (1480) | fail | fail | fail |
| `trend_down_vol_high` | 10d | 159,147 | +134.0 | +112.3 | +21.7 | +6.07 | 24.7 | 12.5 | 37.2 | -15.5 | -27.8 | +96.8 | 14,766 | 58.9 | 589 (1500) | fail | fail | fail |
| `cs_top_quartile_120` | 10d | 324,745 | +107.4 | +85.7 | +21.7 | +5.64 | 26.5 | 10.7 | 37.2 | -15.5 | -28.8 | +70.2 | 30,131 | 120.0 | 1200 (1320) | fail | fail | fail |
| `cs_bottom_quartile_60` | 15d | 325,815 | +154.9 | +129.8 | +25.1 | +5.03 | 27.8 | 14.1 | 41.9 | -16.8 | -30.7 | +113.0 | 30,230 | 120.6 | 1809 (1995) | fail | fail | fail |
| `ch52_low_vol_high` | 5d | 105,648 | +89.8 | +62.7 | +27.1 | +3.56 | 27.7 | 16.3 | 43.9 | -16.9 | -30.7 | +45.9 | 9,802 | 40.0 | 200 (475) | fail | fail | fail |
| `cs_bottom_quartile_120` | 20d | 323,405 | +197.3 | +173.0 | +24.3 | +4.30 | 27.9 | 14.5 | 42.4 | -18.1 | -32.1 | +154.9 | 30,007 | 120.0 | 2399 (2640) | fail | fail | fail |
| `vol_high` | 60d | 411,891 | +695.8 | +681.5 | +14.3 | +6.65 | 23.7 | 11.4 | 35.1 | -20.8 | -32.7 | +660.7 | 38,217 | 155.1 | 9305 (24060) | fail | fail | fail |
| `trend_up_vol_low` | 120d | 234,497 | +817.5 | +804.3 | +13.1 | +5.71 | 23.3 | 10.8 | 34.1 | -21.0 | -32.7 | +783.3 | 21,757 | 93.7 | 11247 (23028) | fail | fail | fail |
| `vol_high` | 120d | 391,278 | +1207.0 | +1194.2 | +12.8 | +9.16 | 23.7 | 11.7 | 35.4 | -22.6 | -34.5 | +1171.6 | 36,304 | 150.7 | 18087 (48420) | fail | fail | fail |
| `cs_bottom_quartile_60` | 10d | 326,485 | +101.5 | +85.7 | +15.8 | +3.98 | 27.8 | 14.1 | 41.9 | -26.1 | -40.0 | +59.6 | 30,292 | 120.7 | 1207 (1330) | fail | fail | fail |
| `cs_top_quartile_120` | 5d | 325,415 | +52.8 | +42.7 | +10.1 | +3.39 | 26.5 | 10.7 | 37.2 | -27.1 | -40.4 | +15.6 | 30,193 | 120.0 | 600 (660) | fail | fail | fail |
| `ch52_high` | 60d | 423,656 | +424.3 | +420.3 | +4.0 | -4.97 | 22.7 | 8.6 | 31.3 | -27.3 | -38.7 | +393.0 | 39,308 | 159.6 | 9578 (14862) | fail | fail | fail |
| `ch52_low_vol_high` | 2d | 105,684 | +36.7 | +23.3 | +13.5 | +3.14 | 27.7 | 16.3 | 43.9 | -30.5 | -44.3 | -7.2 | 9,806 | 40.0 | 80 (190) | fail | fail | fail |
| `vol_high` | 20d | 419,206 | +235.3 | +232.2 | +3.1 | +5.58 | 23.6 | 11.4 | 35.0 | -31.9 | -43.7 | +200.4 | 38,895 | 155.5 | 3110 (8000) | fail | fail | fail |
| `vol_high` | 15d | 419,751 | +172.2 | +169.3 | +2.9 | +5.39 | 23.6 | 11.3 | 35.0 | -32.0 | -43.8 | +137.2 | 38,946 | 155.4 | 2331 (6000) | fail | fail | fail |
| `vol_high` | 10d | 420,183 | +109.9 | +107.0 | +2.9 | +4.76 | 23.6 | 11.3 | 35.0 | -32.1 | -43.9 | +74.9 | 38,986 | 155.3 | 1553 (4000) | fail | fail | fail |
| `below_ma_50` | 15d | 551,174 | +159.7 | +154.3 | +5.4 | +1.63 | 25.7 | 12.4 | 38.0 | -32.6 | -45.5 | +121.7 | 51,140 | 204.1 | 3061 (5085) | fail | fail | fail |
| `cs_bottom_quartile_60` | 5d | 327,155 | +51.6 | +42.7 | +8.8 | +2.84 | 27.8 | 14.1 | 41.9 | -33.0 | -46.9 | +9.7 | 30,355 | 120.7 | 603 (665) | fail | fail | fail |

## Criterion outcomes

- candidates: 48
- pass net expectancy (within-date, positive under the 1.5x-spread stress, |t_within| > 2): 22
- pass frequency (100–400 firings/yr): 0
- pass concurrency (4–12 positions at 5–15d holds): 0
- pass all three with an eligible 5–15d hold: **0**

## Survivors

none survive costs at this universe size.

Explicit valid conclusion (the plan pre-authorises it). The binding constraints, in order:

1. **Concurrency / frequency.** The candidate rules fire on hundreds of names per day (median 120 fires/day), so a 5–15d hold implies concurrency far above the 12-position envelope and annual firings far above 400. They are *market states*, not triggers with a daily cadence — the plan's 100–400/yr preference describes a trigger, and a state that describes a third of the universe every day cannot be one.

2. **Net expectancy.** Even ignoring cadence, the within-date edge is comparable to or smaller than the round-trip cost: median within-date effect +40.0 bps against a median round-trip cost of 37.2 bps (spread + commission). Under the 1.5x-spread stress, 22 of 48 candidates would still show a positive *within-date* net effect, but none of those combine it with a tradeable cadence.


## What would have to change (for the human gate, not executed here)

- A **narrower trigger**: require the rule AND a further selection (e.g. only the highest-ranked names each day) to reach 0.4–1.6 fires/day. That is *screener design / portfolio construction*, explicitly out of scope for WI-011 and requiring a new plan.
- A **cheaper execution assumption**: only the CAD commission schedule and the spread estimate are modelled; a queue-following/limit-order assumption would lower the spread term, and the report shows how much (1.5x/2.0x columns).
- A **longer hold**: 5–15d is the plan's envelope; the raw within-date effects at 60/120d are larger, but the hold envelope and cost amortisation are then outside this step's stated criteria.

## Limits

- No optimisation, no backtest, no position sizing, no screener implementation: costs and frequency are applied to already-descriptive cells, and nothing here is tuned to make a survivor appear.
- The IBKR schedule parameters are assumptions recorded as constants in `scripts/wi011_tradeable_conditions.py` and must be confirmed by the admin; the notional assumption (CAD 5,000) drives the commission-in-bps conversion.
- The spread proxy is an estimate from daily bars (Corwin-Schultz, lagged causal) with an Amihud-proportional fallback; it is not a quote, and the stress columns carry that uncertainty.
