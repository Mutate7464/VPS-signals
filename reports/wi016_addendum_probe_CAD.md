# WI-016 addendum honest-edge probe — CAD

- Generated (UTC): 2026-10-30T05:44:06Z
- Panel rows: 833,859 · features: 116 · targets: 15
- BH-FDR alpha 0.05; cost bands [10.0, 20.0, 30.0] bps (unconfirmed WI-011 assumption)
- Touch-restricted labels = barrier-resolved rows only (`tb_touch_*` ∈ {+1,−1});
  realized-return targets are `tb_fret_h*`.

## DECISION @ 20 bps — barrier-resolved labels: **CLEAR**

## Diagnostic @ 20 bps — realized-return targets: **CLEAR**

The barrier-resolved verdict is the apples-to-apples re-test of step 5; the
realized-return targets are a separate long-horizon regression diagnostic and
must not be read as barrier capture.

| target | kind | cleared | passing | best feature | best IC |
| :--- | :--- | :---: | ---: | :--- | ---: |
| `tb_label_k15_h8` | touch_restricted | yes | 8 | `range_pos_8` | -0.0416 |
| `tb_label_k15_h21` | touch_restricted | no | 0 | - | - |
| `tb_label_k15_h55` | touch_restricted | yes | 4 | `vol_20` | -0.0370 |
| `tb_label_k15_h144` | touch_restricted | yes | 2 | `vol_20` | -0.0362 |
| `tb_label_k15_h233` | touch_restricted | yes | 6 | `yangzhang_21` | -0.0380 |
| `tb_label_k20_h8` | touch_restricted | yes | 10 | `range_pos_21` | -0.0421 |
| `tb_label_k20_h21` | touch_restricted | no | 0 | - | - |
| `tb_label_k20_h55` | touch_restricted | no | 0 | - | - |
| `tb_label_k20_h144` | touch_restricted | no | 0 | - | - |
| `tb_label_k20_h233` | touch_restricted | no | 0 | - | - |
| `tb_fret_h8` | realized_return | no | 0 | - | - |
| `tb_fret_h21` | realized_return | no | 0 | - | - |
| `tb_fret_h55` | realized_return | yes | 5 | `frac_diff_close` | -0.0483 |
| `tb_fret_h144` | realized_return | yes | 21 | `pct_from_low_233` | +0.0774 |
| `tb_fret_h233` | realized_return | yes | 22 | `frac_diff_close` | -0.0970 |

## Touch class counts (why the sample shrinks)

| target | defined | profit | stop | vertical | touch-restricted |
| :--- | ---: | ---: | ---: | ---: | ---: |
| `tb_label_k15_h8` | 828,944 | 335,756 | 282,804 | 210,384 | 618,560 |
| `tb_label_k15_h21` | 824,199 | 431,662 | 363,109 | 29,428 | 794,771 |
| `tb_label_k15_h55` | 811,789 | 441,925 | 368,308 | 1,556 | 810,233 |
| `tb_label_k15_h144` | 779,309 | 424,210 | 354,829 | 270 | 779,039 |
| `tb_label_k15_h233` | 746,988 | 405,285 | 341,506 | 197 | 746,791 |
| `tb_label_k20_h8` | 828,944 | 246,009 | 198,535 | 384,400 | 444,544 |
| `tb_label_k20_h21` | 824,199 | 401,754 | 321,364 | 101,081 | 723,118 |
| `tb_label_k20_h55` | 811,789 | 449,052 | 354,413 | 8,324 | 803,465 |
| `tb_label_k20_h144` | 779,309 | 434,403 | 344,261 | 645 | 778,664 |
| `tb_label_k20_h233` | 746,988 | 415,019 | 331,648 | 321 | 746,667 |

## Verdict change vs step 5 (touch-restricted labels)

Step-5 verdicts parsed from the frozen `wi016_probe_<market>.md`; addendum uses barrier-resolved samples.

| target | step 5 | addendum | changed |
| :--- | :---: | :---: | :---: |
| `tb_label_k15_h8` | CLEAR | CLEAR | no |
| `tb_label_k15_h21` | CLEAR | NOT_CLEAR | YES |
| `tb_label_k15_h55` | CLEAR | CLEAR | no |
| `tb_label_k15_h144` | CLEAR | CLEAR | no |
| `tb_label_k15_h233` | CLEAR | CLEAR | no |
| `tb_label_k20_h8` | CLEAR | CLEAR | no |
| `tb_label_k20_h21` | CLEAR | NOT_CLEAR | YES |
| `tb_label_k20_h55` | NOT_CLEAR | NOT_CLEAR | no |
| `tb_label_k20_h144` | NOT_CLEAR | NOT_CLEAR | no |
| `tb_label_k20_h233` | NOT_CLEAR | NOT_CLEAR | no |

- 2 target(s) flipped between step 5 and the addendum.

## Cost sensitivity (net edge = |IC|·1000 − band)

| band (bps) | barrier-resolved | realized-return | tradeable tests | best |IC| |
| :--- | :---: | :---: | ---: | ---: |
| 10 | CLEAR | CLEAR | 78 | 0.0970 |
| 20 | CLEAR | CLEAR | 78 | 0.0970 |
| 30 | CLEAR | CLEAR | 78 | 0.0970 |

### Per-band per-market verdict lines

- **CAD @ 10 bps — barrier-resolved: CLEAR**
- **CAD @ 10 bps — realized-return: CLEAR**
- **CAD @ 20 bps — barrier-resolved: CLEAR**
- **CAD @ 20 bps — realized-return: CLEAR**
- **CAD @ 30 bps — barrier-resolved: CLEAR**
- **CAD @ 30 bps — realized-return: CLEAR**

## Top FDR-significant tests (restricted sample)

| target | feature | IC | t | q | same-sign | placebo | tradeable@20 |
| :--- | :--- | ---: | ---: | ---: | :---: | :---: | :---: |
| `tb_fret_h233` | `frac_diff_close` | -0.0970 | -25.96 | 0.0000 | Y | Y | Y |
| `tb_fret_h144` | `pct_from_low_233` | +0.0774 | +22.91 | 0.0000 | Y | Y | Y |
| `tb_fret_h144` | `frac_diff_close` | -0.0751 | -21.48 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `adx_55` | +0.0720 | +33.20 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `pct_from_low_233` | +0.0719 | +19.82 | 0.0000 | N | Y | Y |
| `tb_fret_h144` | `di_spread_144` | +0.0711 | +20.45 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `amihud_144` | +0.0698 | +24.65 | 0.0000 | Y | Y | Y |
| `tb_fret_h144` | `adx_55` | +0.0678 | +28.18 | 0.0000 | Y | Y | Y |
| `tb_fret_h144` | `adx_144` | +0.0673 | +34.60 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `amihud_233` | +0.0670 | +23.90 | 0.0000 | Y | Y | Y |
| `tb_fret_h144` | `di_spread_55` | +0.0666 | +21.69 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `di_spread_55` | +0.0652 | +19.92 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `bb_width_144` | +0.0634 | +14.40 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `amihud_55` | +0.0633 | +21.83 | 0.0000 | Y | Y | Y |
| `tb_fret_h144` | `bb_width_233` | +0.0600 | +14.68 | 0.0000 | N | Y | Y |
| `tb_fret_h233` | `adx_144` | +0.0596 | +33.65 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `bb_width_233` | +0.0587 | +13.45 | 0.0000 | N | Y | Y |
| `tb_fret_h233` | `yangzhang_144` | +0.0586 | +12.57 | 0.0000 | N | Y | Y |
| `tb_fret_h233` | `log_dollar_vol_20` | -0.0569 | -23.39 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `di_spread_144` | +0.0568 | +16.23 | 0.0000 | Y | Y | Y |
| `tb_fret_h144` | `bb_width_144` | +0.0567 | +14.18 | 0.0000 | N | Y | Y |
| `tb_fret_h144` | `di_spread_233` | +0.0564 | +15.81 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `amihud_21` | +0.0561 | +19.40 | 0.0000 | Y | Y | Y |
| `tb_fret_h144` | `bb_pct_b_233` | +0.0552 | +14.68 | 0.0000 | Y | Y | Y |
| `tb_fret_h233` | `amihud_20` | +0.0551 | +19.11 | 0.0000 | Y | Y | Y |

## Overlap-aware statistics (average-uniqueness weights, AFML ch. 4)

Weighted vs unweighted per-date IC t-stat for the best restricted test per target;
weight = mean average-uniqueness of that date's events.

| target | feature | horizon | unweighted IC | unweighted t | weighted IC | weighted t | effective n | mean uniqueness |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `tb_label_k15_h8` | `range_pos_8` | 8 | -0.0416 | -14.57 | -0.0415 | -5.13 | 338.9 | 0.125 |
| `tb_label_k15_h21` | `vol_20` | 21 | -0.0342 | -10.55 | -0.0340 | -2.29 | 128.8 | 0.048 |
| `tb_label_k15_h55` | `vol_20` | 55 | -0.0370 | -11.61 | -0.0366 | -1.56 | 48.9 | 0.018 |
| `tb_label_k15_h144` | `vol_20` | 144 | -0.0362 | -11.41 | -0.0352 | -0.94 | 18.4 | 0.007 |
| `tb_label_k15_h233` | `yangzhang_21` | 233 | -0.0380 | -11.64 | -0.0360 | -0.74 | 11.2 | 0.005 |
| `tb_label_k20_h8` | `range_pos_21` | 8 | -0.0421 | -13.04 | -0.0421 | -4.61 | 338.9 | 0.125 |
| `tb_label_k20_h21` | `rev_1m` | 21 | -0.0316 | -11.46 | -0.0316 | -2.50 | 128.8 | 0.048 |
| `tb_label_k20_h55` | `vol_20` | 55 | -0.0302 | -9.48 | -0.0298 | -1.27 | 48.9 | 0.018 |
| `tb_label_k20_h144` | `vol_20` | 144 | -0.0299 | -9.51 | -0.0288 | -0.78 | 18.4 | 0.007 |
| `tb_label_k20_h233` | `bb_width_21` | 233 | -0.0322 | -11.10 | -0.0303 | -0.71 | 11.2 | 0.005 |
| `tb_fret_h8` | `fib_dist_3` | 8 | -0.0329 | -11.83 | -0.0329 | -4.19 | 339.1 | 0.125 |
| `tb_fret_h21` | `adx_144` | 21 | +0.0283 | +12.19 | +0.0284 | +2.66 | 123.1 | 0.048 |
| `tb_fret_h55` | `frac_diff_close` | 55 | -0.0483 | -14.60 | -0.0510 | -2.08 | 49.0 | 0.018 |
| `tb_fret_h144` | `pct_from_low_233` | 144 | +0.0774 | +22.91 | +0.0779 | +1.93 | 17.7 | 0.007 |
| `tb_fret_h233` | `frac_diff_close` | 233 | -0.0970 | -25.96 | -0.1074 | -1.90 | 11.3 | 0.005 |

- **CAD overlap check: weighted t-stats above; compare with the unweighted column.**
