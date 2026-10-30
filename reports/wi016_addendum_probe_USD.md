# WI-016 addendum honest-edge probe — USD

- Generated (UTC): 2026-10-30T05:22:21Z
- Panel rows: 1,459,630 · features: 116 · targets: 15
- BH-FDR alpha 0.05; cost bands [10.0, 20.0, 30.0] bps (unconfirmed WI-011 assumption)
- Touch-restricted labels = barrier-resolved rows only (`tb_touch_*` ∈ {+1,−1});
  realized-return targets are `tb_fret_h*`.

## DECISION @ 20 bps — barrier-resolved labels: **NOT_CLEAR**

## Diagnostic @ 20 bps — realized-return targets: **CLEAR**

The barrier-resolved verdict is the apples-to-apples re-test of step 5; the
realized-return targets are a separate long-horizon regression diagnostic and
must not be read as barrier capture.

| target | kind | cleared | passing | best feature | best IC |
| :--- | :--- | :---: | ---: | :--- | ---: |
| `tb_label_k15_h8` | touch_restricted | no | 0 | - | - |
| `tb_label_k15_h21` | touch_restricted | no | 0 | - | - |
| `tb_label_k15_h55` | touch_restricted | no | 0 | - | - |
| `tb_label_k15_h144` | touch_restricted | no | 0 | - | - |
| `tb_label_k15_h233` | touch_restricted | no | 0 | - | - |
| `tb_label_k20_h8` | touch_restricted | no | 0 | - | - |
| `tb_label_k20_h21` | touch_restricted | no | 0 | - | - |
| `tb_label_k20_h55` | touch_restricted | no | 0 | - | - |
| `tb_label_k20_h144` | touch_restricted | no | 0 | - | - |
| `tb_label_k20_h233` | touch_restricted | no | 0 | - | - |
| `tb_fret_h8` | realized_return | no | 0 | - | - |
| `tb_fret_h21` | realized_return | no | 0 | - | - |
| `tb_fret_h55` | realized_return | yes | 23 | `yangzhang_144` | +0.0462 |
| `tb_fret_h144` | realized_return | yes | 37 | `pct_from_low_233` | +0.0705 |
| `tb_fret_h233` | realized_return | yes | 37 | `frac_diff_close` | -0.0788 |

## Touch class counts (why the sample shrinks)

| target | defined | profit | stop | vertical | touch-restricted |
| :--- | ---: | ---: | ---: | ---: | ---: |
| `tb_label_k15_h8` | 1,452,324 | 612,103 | 518,857 | 321,364 | 1,130,960 |
| `tb_label_k15_h21` | 1,444,615 | 769,351 | 642,929 | 32,335 | 1,412,280 |
| `tb_label_k15_h55` | 1,424,453 | 778,630 | 644,226 | 1,597 | 1,422,856 |
| `tb_label_k15_h144` | 1,371,676 | 749,212 | 621,914 | 550 | 1,371,126 |
| `tb_label_k15_h233` | 1,318,899 | 720,980 | 597,460 | 459 | 1,318,440 |
| `tb_label_k20_h8` | 1,452,324 | 448,726 | 376,003 | 627,595 | 824,729 |
| `tb_label_k20_h21` | 1,444,615 | 724,485 | 584,520 | 135,610 | 1,309,005 |
| `tb_label_k20_h55` | 1,424,453 | 789,576 | 627,541 | 7,336 | 1,417,117 |
| `tb_label_k20_h144` | 1,371,676 | 762,020 | 608,928 | 728 | 1,370,948 |
| `tb_label_k20_h233` | 1,318,899 | 733,073 | 585,295 | 531 | 1,318,368 |

## Verdict change vs step 5 (touch-restricted labels)

Step-5 verdicts parsed from the frozen `wi016_probe_<market>.md`; addendum uses barrier-resolved samples.

| target | step 5 | addendum | changed |
| :--- | :---: | :---: | :---: |
| `tb_label_k15_h8` | NOT_CLEAR | NOT_CLEAR | no |
| `tb_label_k15_h21` | NOT_CLEAR | NOT_CLEAR | no |
| `tb_label_k15_h55` | NOT_CLEAR | NOT_CLEAR | no |
| `tb_label_k15_h144` | NOT_CLEAR | NOT_CLEAR | no |
| `tb_label_k15_h233` | NOT_CLEAR | NOT_CLEAR | no |
| `tb_label_k20_h8` | NOT_CLEAR | NOT_CLEAR | no |
| `tb_label_k20_h21` | NOT_CLEAR | NOT_CLEAR | no |
| `tb_label_k20_h55` | NOT_CLEAR | NOT_CLEAR | no |
| `tb_label_k20_h144` | NOT_CLEAR | NOT_CLEAR | no |
| `tb_label_k20_h233` | NOT_CLEAR | NOT_CLEAR | no |

- 0 target(s) flipped between step 5 and the addendum.

## Cost sensitivity (net edge = |IC|·1000 − band)

| band (bps) | barrier-resolved | realized-return | tradeable tests | best |IC| |
| :--- | :---: | :---: | ---: | ---: |
| 10 | NOT_CLEAR | CLEAR | 97 | 0.0788 |
| 20 | NOT_CLEAR | CLEAR | 97 | 0.0788 |
| 30 | NOT_CLEAR | CLEAR | 90 | 0.0788 |

### Per-band per-market verdict lines

- **USD @ 10 bps — barrier-resolved: NOT_CLEAR**
- **USD @ 10 bps — realized-return: CLEAR**
- **USD @ 20 bps — barrier-resolved: NOT_CLEAR**
- **USD @ 20 bps — realized-return: CLEAR**
- **USD @ 30 bps — barrier-resolved: NOT_CLEAR**
- **USD @ 30 bps — realized-return: CLEAR**

## Top FDR-significant tests (restricted sample)

| target | feature | IC | t | q | same-sign | placebo | tradeable@20 |
| :--- | :--- | ---: | ---: | ---: | :---: | :---: | :---: |
| `tb_fret_h233` | `frac_diff_close` | -0.0788 | -27.35 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `yangzhang_144` | +0.0766 | +21.16 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `bb_width_144` | +0.0763 | +24.49 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `bb_width_233` | +0.0754 | +23.65 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `yangzhang_55` | +0.0736 | +20.11 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `range_width_144` | +0.0736 | +21.44 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `yangzhang_233` | +0.0718 | +20.02 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `pct_from_low_233` | +0.0709 | +27.97 | 0.0000 | Y | Y | Y |
| `tb_fret_h144` | `pct_from_low_233` | +0.0705 | +28.05 | 0.0000 | Y | Y | Y |
| `tb_fret_h144` | `bb_width_233` | +0.0688 | +22.65 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `range_width_233` | +0.0671 | +18.78 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `range_width_55` | +0.0668 | +19.44 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `yangzhang_21` | +0.0659 | +18.20 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `vol_20` | +0.0645 | +18.15 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `bb_width_55` | +0.0623 | +19.74 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `atr_pct_21` | +0.0621 | +16.88 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `atr_pct_8` | +0.0619 | +17.27 | 0.0000 | Y | Y | Y |
| `tb_fret_h144` | `yangzhang_144` | +0.0614 | +17.10 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `yangzhang_8` | +0.0600 | +17.19 | 0.0000 | Y | Y | Y |
| `tb_fret_h144` | `frac_diff_close` | -0.0599 | -21.16 | 0.0000 | Y | Y | Y |
| `tb_fret_h144` | `yangzhang_55` | +0.0591 | +16.52 | 0.0000 | Y | Y | Y |
| `tb_fret_h144` | `range_width_233` | +0.0591 | +17.31 | 0.0000 | Y | Y | Y |
| `tb_fret_h144` | `bb_width_144` | +0.0590 | +20.07 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `atr_pct_55` | +0.0581 | +15.66 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `atr_pct_3` | +0.0580 | +17.05 | 0.0000 | Y | Y | Y |

## Overlap-aware statistics (average-uniqueness weights, AFML ch. 4)

Weighted vs unweighted per-date IC t-stat for the best restricted test per target;
weight = mean average-uniqueness of that date's events.

| target | feature | horizon | unweighted IC | unweighted t | weighted IC | weighted t | effective n | mean uniqueness |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `tb_label_k15_h8` | `rev_1m` | 8 | -0.0130 | -4.68 | -0.0128 | -1.63 | 339.6 | 0.125 |
| `tb_label_k15_h21` | `vwap_zscore_102` | 21 | -0.0103 | -4.27 | -0.0103 | -0.93 | 127.2 | 0.048 |
| `tb_label_k15_h55` | `bb_width_144` | 55 | -0.0122 | -4.96 | -0.0118 | -0.65 | 49.0 | 0.018 |
| `tb_label_k15_h144` | `bb_width_144` | 144 | -0.0114 | -4.62 | -0.0111 | -0.38 | 18.4 | 0.007 |
| `tb_label_k15_h233` | `bb_width_144` | 233 | -0.0120 | -4.76 | -0.0116 | -0.31 | 11.2 | 0.005 |
| `tb_label_k20_h8` | `frac_diff_close` | 8 | -0.0193 | -6.46 | -0.0192 | -2.28 | 339.4 | 0.125 |
| `tb_label_k20_h21` | `rev_1m` | 21 | -0.0126 | -5.14 | -0.0121 | -1.08 | 129.0 | 0.048 |
| `tb_label_k20_h55` | `frac_diff_close` | 55 | -0.0104 | -4.49 | -0.0107 | -0.63 | 49.0 | 0.018 |
| `tb_label_k20_h144` | `frac_diff_close` | 144 | -0.0094 | -4.00 | -0.0102 | -0.37 | 18.4 | 0.007 |
| `tb_label_k20_h233` | `rev_1m` | 233 | -0.0106 | -4.63 | -0.0094 | -0.28 | 11.2 | 0.005 |
| `tb_fret_h8` | `bb_width_233` | 8 | +0.0174 | +4.78 | +0.0174 | +1.69 | 332.0 | 0.125 |
| `tb_fret_h21` | `yangzhang_144` | 21 | +0.0274 | +6.90 | +0.0269 | +1.48 | 129.2 | 0.048 |
| `tb_fret_h55` | `yangzhang_144` | 55 | +0.0462 | +11.83 | +0.0474 | +1.65 | 49.1 | 0.018 |
| `tb_fret_h144` | `pct_from_low_233` | 144 | +0.0705 | +28.05 | +0.0703 | +2.35 | 17.7 | 0.007 |
| `tb_fret_h233` | `frac_diff_close` | 233 | -0.0788 | -27.35 | -0.0869 | -1.98 | 11.3 | 0.005 |

- **USD overlap check: weighted t-stats above; compare with the unweighted column.**
