# WI-016 step 6 meta-labeler — CAD

- Generated (UTC): 2026-10-30T21:33:20Z
- Primary: `yangzhang_21` per-date rank, long side, top-decile events (q=0.9)
- Training expansion: top-two deciles (second decile flag = 0); shipped decisions top-decile only
- Targets: `tb_label_k15_h8`, `tb_label_k15_h55`, `tb_label_k15_h144`, `tb_label_k20_h8`
- Embargo `max(20, h)` per target; CB-04 isotonic/sigmoid calibration; 5-seed label-permutation placebo
- Meta-label = bet P&L > 0 (profit barrier first touch = 1, stop first = 0); barrier-resolved rows only.

## Per-target OOF vs placebo

| target | h | embargo | events | top-decile | pos rate | OOF AP | OOF AUC | placebo AP | placebo AUC | calibration |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| `tb_label_k15_h8` | 8 | 20 | 121,156 | 58,761 | 0.530 | 0.5727 | 0.5276 | 0.5295 | 0.4997 | isotonic |
| `tb_label_k15_h55` | 55 | 55 | 163,293 | 82,003 | 0.525 | 0.5567 | 0.5137 | 0.5250 | 0.4994 | isotonic |
| `tb_label_k15_h144` | 144 | 144 | 157,381 | 79,260 | 0.525 | 0.5668 | 0.5244 | 0.5247 | 0.4996 | isotonic |
| `tb_label_k20_h8` | 8 | 20 | 86,691 | 41,790 | 0.560 | 0.5967 | 0.5066 | 0.5593 | 0.4989 | isotonic |

## Decile-stratified OOF (training expansion)

| target | stratum | n | OOF AP | OOF AUC |
| :--- | :--- | ---: | ---: | ---: |
| `tb_label_k15_h8` | top_decile | 58,761 | 0.5816 | 0.5407 |
| `tb_label_k15_h8` | second_decile | 62,395 | 0.5639 | 0.5170 |
| `tb_label_k15_h55` | top_decile | 82,003 | 0.5579 | 0.5216 |
| `tb_label_k15_h55` | second_decile | 81,290 | 0.5568 | 0.5084 |
| `tb_label_k15_h144` | top_decile | 79,260 | 0.5652 | 0.5321 |
| `tb_label_k15_h144` | second_decile | 78,121 | 0.5696 | 0.5179 |
| `tb_label_k20_h8` | top_decile | 41,790 | 0.6096 | 0.5202 |
| `tb_label_k20_h8` | second_decile | 44,901 | 0.5827 | 0.4956 |

## Purged walk-forward folds (`embargo_td = max(20, h)`)

| target | fold | n_fit | n_calib | n_val | max train date | min val date | gap (td) | val AP | calibration |
| :--- | ---: | ---: | ---: | ---: | :--- | :--- | ---: | ---: | :--- |
| `tb_label_k15_h8` | 0 | 31,751 | 8,771 | 12,962 | 2020-03-26 | 2020-04-27 | 21 | 0.5867 | isotonic |
| `tb_label_k15_h8` | 1 | 42,291 | 11,136 | 15,244 | 2021-07-13 | 2021-08-12 | 21 | 0.5477 | isotonic |
| `tb_label_k15_h8` | 2 | 52,677 | 15,860 | 15,223 | 2022-10-28 | 2022-11-28 | 21 | 0.5634 | isotonic |
| `tb_label_k15_h8` | 3 | 64,418 | 19,055 | 16,858 | 2024-02-14 | 2024-03-15 | 21 | 0.5926 | isotonic |
| `tb_label_k15_h8` | 4 | 76,570 | 23,899 | 18,809 | 2025-06-02 | 2025-07-02 | 21 | 0.5978 | isotonic |
| `tb_label_k15_h55` | 0 | 40,669 | 11,425 | 18,272 | 2020-01-09 | 2020-03-30 | 56 | 0.6254 | isotonic |
| `tb_label_k15_h55` | 1 | 55,056 | 15,174 | 20,003 | 2021-04-16 | 2021-07-07 | 56 | 0.5304 | isotonic |
| `tb_label_k15_h55` | 2 | 69,573 | 20,263 | 21,182 | 2022-07-25 | 2022-10-14 | 56 | 0.5292 | isotonic |
| `tb_label_k15_h55` | 3 | 84,704 | 25,799 | 22,159 | 2023-11-02 | 2024-01-24 | 56 | 0.5683 | isotonic |
| `tb_label_k15_h55` | 4 | 101,222 | 31,130 | 23,382 | 2025-02-10 | 2025-05-01 | 56 | 0.6241 | isotonic |
| `tb_label_k15_h144` | 0 | 30,309 | 9,975 | 17,733 | 2019-07-10 | 2020-02-06 | 145 | 0.6096 | isotonic |
| `tb_label_k15_h144` | 1 | 44,084 | 13,674 | 19,098 | 2020-09-30 | 2021-04-29 | 145 | 0.5050 | isotonic |
| `tb_label_k15_h144` | 2 | 58,152 | 17,711 | 20,365 | 2021-12-22 | 2022-07-22 | 145 | 0.5156 | isotonic |
| `tb_label_k15_h144` | 3 | 72,433 | 23,336 | 21,222 | 2023-03-20 | 2023-10-17 | 145 | 0.5695 | isotonic |
| `tb_label_k15_h144` | 4 | 87,298 | 28,309 | 22,407 | 2024-06-11 | 2025-01-09 | 145 | 0.6024 | isotonic |
| `tb_label_k20_h8` | 0 | 22,873 | 6,485 | 9,153 | 2020-03-26 | 2020-04-27 | 21 | 0.6251 | isotonic |
| `tb_label_k20_h8` | 1 | 30,555 | 7,905 | 10,671 | 2021-07-13 | 2021-08-12 | 21 | 0.5654 | isotonic |
| `tb_label_k20_h8` | 2 | 37,978 | 11,079 | 10,501 | 2022-10-28 | 2022-11-28 | 21 | 0.6041 | isotonic |
| `tb_label_k20_h8` | 3 | 46,287 | 12,977 | 12,183 | 2024-02-14 | 2024-03-15 | 21 | 0.6084 | isotonic |
| `tb_label_k20_h8` | 4 | 54,502 | 17,119 | 13,780 | 2025-06-02 | 2025-07-02 | 21 | 0.6330 | isotonic |

## Shortlist artifact

- Path: `/home/yycuser/projects/signals/reports/wi016_shortlist_CAD.parquet`
- Scoring date: 2026-10-28
- Rows: 148 (147 TRADE / 1 NO_TRADE at 20 bps)
- Schema: rank, symbol, mom_12_1, rev_1m, vol_20, amihud_20, log_dollar_vol_20, scoring_date, market, target, k, h, primary, primary_pct, decile_flag, p_meta, meta_calibration, entry_close, atr, barrier_upper, barrier_lower, time_stop_bars, expected_gross_bps, cost_bps, net_bps, size, decision, abstain_reason
- NO_TRADE is the default: a row is tradeable only when the calibrated meta-probability clears the coin-flip floor and the expected edge exceeds the cost band.
- No order execution exists; this artifact is research context for the human gate.

## Caveats (auto-computed — read before the gate)

- **The cost band is not the binding constraint.** 147/148 shortlist rows clear 20 bps (trade share 99.3%). The symmetric barrier payoff ``k·ATR/close`` is typically several percent, so a 20 bps round trip is dwarfed by the payoff scale: the abstain channel is driven by the probability floor, not the cost overlay.
- **The OOF edge is thin.** OOF AUC 0.5066–0.5276 vs placebo 0.4989–0.4997 (≈0.50 = no edge). OOF AP 0.5567–0.5967 on base rates 0.525–0.560, so part of the AP advantage is the base rate itself.
- The meta-label is a first-touch binary; entry is the scoring-date close and the exit is the barrier or the h-bar time stop. Intra-horizon drift and slippage beyond the flat cost band are not modelled.
- The cost band is the unconfirmed WI-011 assumption; the addendum showed no verdict flip across 10/20/30 bps, and this run uses the standing 20 bps.
