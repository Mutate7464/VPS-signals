# WI-016 probe-first gate — USD

- Generated (UTC): 2026-10-30T01:50:07Z
- Panel rows: 1,459,630 · features: 116 · targets: 10
- Tests: 1160 · BH-FDR alpha 0.05 · cost overlay 20.0 bps (NO_TRADE default)

## DECISION: **NOT_CLEAR**

A target clears only when it has a feature that is FDR-significant, same-sign,
placebo-clear and cost-tradeable.

| target | cleared | passing features | best feature | best IC |
| :--- | :---: | ---: | :--- | ---: |
| `tb_label_k15_h8` | no | 0 | - | - |
| `tb_label_k15_h21` | no | 0 | - | - |
| `tb_label_k15_h55` | no | 0 | - | - |
| `tb_label_k15_h144` | no | 0 | - | - |
| `tb_label_k15_h233` | no | 0 | - | - |
| `tb_label_k20_h8` | no | 0 | - | - |
| `tb_label_k20_h21` | no | 0 | - | - |
| `tb_label_k20_h55` | no | 0 | - | - |
| `tb_label_k20_h144` | no | 0 | - | - |
| `tb_label_k20_h233` | no | 0 | - | - |

## Label class balance / density

| target | events | +1 | -1 | 0 |
| :--- | ---: | ---: | ---: | ---: |
| `tb_label_k15_h8` | 1452324 | 783255 | 665535 | 3534 |
| `tb_label_k15_h21` | 1444615 | 786020 | 657498 | 1097 |
| `tb_label_k15_h55` | 1424453 | 779204 | 644644 | 605 |
| `tb_label_k15_h144` | 1371676 | 749260 | 621917 | 499 |
| `tb_label_k15_h233` | 1318899 | 721022 | 597467 | 410 |
| `tb_label_k20_h8` | 1452324 | 788318 | 659458 | 4548 |
| `tb_label_k20_h21` | 1444615 | 796532 | 646590 | 1493 |
| `tb_label_k20_h55` | 1424453 | 793032 | 630799 | 622 |
| `tb_label_k20_h144` | 1371676 | 762153 | 609024 | 499 |
| `tb_label_k20_h233` | 1318899 | 733141 | 585348 | 410 |

## Events per purged fold (`embargo_td = max(20, horizon)`)

| target | h | folds (events) |
| :--- | ---: | :--- |
| `tb_label_k15_h8` | 8 | f0=174192, f1=182515, f2=184085, f3=189663, f4=188819 |
| `tb_label_k15_h21` | 21 | f0=174192, f1=182515, f2=184085, f3=189663, f4=181110 |
| `tb_label_k15_h55` | 55 | f0=174192, f1=182515, f2=184085, f3=189663, f4=160948 |
| `tb_label_k15_h144` | 144 | f0=174192, f1=182515, f2=184085, f3=189663, f4=108171 |
| `tb_label_k15_h233` | 233 | f0=174192, f1=182515, f2=184085, f3=189663, f4=55394 |
| `tb_label_k20_h8` | 8 | f0=174192, f1=182515, f2=184085, f3=189663, f4=188819 |
| `tb_label_k20_h21` | 21 | f0=174192, f1=182515, f2=184085, f3=189663, f4=181110 |
| `tb_label_k20_h55` | 55 | f0=174192, f1=182515, f2=184085, f3=189663, f4=160948 |
| `tb_label_k20_h144` | 144 | f0=174192, f1=182515, f2=184085, f3=189663, f4=108171 |
| `tb_label_k20_h233` | 233 | f0=174192, f1=182515, f2=184085, f3=189663, f4=55394 |

## Top FDR-significant tests

| target | feature | IC | t | q | same-sign | placebo-clear | tradeable |
| :--- | :--- | ---: | ---: | ---: | :---: | :---: | :---: |
| `tb_label_k20_h8` | `yangzhang_21` | -0.0179 | -6.52 | 0.0000 | Y | Y | N |
| `tb_label_k20_h8` | `yangzhang_8` | -0.0179 | -6.64 | 0.0000 | Y | Y | N |
| `tb_label_k20_h8` | `atr_pct_144` | -0.0176 | -6.21 | 0.0000 | Y | Y | N |
| `tb_label_k20_h8` | `atr_pct_233` | -0.0176 | -6.16 | 0.0000 | Y | Y | N |
| `tb_label_k20_h8` | `yangzhang_233` | -0.0174 | -6.00 | 0.0000 | Y | Y | N |
| `tb_label_k20_h8` | `atr_pct_8` | -0.0173 | -6.27 | 0.0000 | Y | Y | N |
| `tb_label_k20_h8` | `atr_pct_55` | -0.0173 | -6.07 | 0.0000 | Y | Y | N |
| `tb_label_k20_h8` | `atr_pct_21` | -0.0172 | -6.10 | 0.0000 | Y | Y | N |
| `tb_label_k20_h8` | `yangzhang_55` | -0.0172 | -6.09 | 0.0000 | Y | Y | N |
| `tb_label_k20_h8` | `yangzhang_3` | -0.0170 | -6.64 | 0.0000 | Y | Y | N |
| `tb_label_k20_h8` | `yangzhang_144` | -0.0170 | -5.97 | 0.0000 | Y | Y | N |
| `tb_label_k20_h8` | `vol_20` | -0.0167 | -6.30 | 0.0000 | Y | Y | N |
| `tb_label_k20_h8` | `atr_pct_3` | -0.0166 | -6.30 | 0.0000 | Y | Y | N |
| `tb_label_k20_h8` | `range_width_144` | -0.0151 | -5.67 | 0.0000 | Y | Y | N |
| `tb_label_k20_h8` | `range_width_21` | -0.0150 | -5.92 | 0.0000 | Y | Y | N |
| `tb_label_k15_h8` | `yangzhang_21` | -0.0145 | -5.24 | 0.0000 | Y | Y | N |
| `tb_label_k15_h8` | `yangzhang_8` | -0.0143 | -5.29 | 0.0000 | Y | Y | N |
| `tb_label_k15_h8` | `yangzhang_55` | -0.0143 | -5.02 | 0.0000 | Y | Y | N |
| `tb_label_k20_h8` | `bb_width_144` | -0.0143 | -5.70 | 0.0000 | Y | Y | N |
| `tb_label_k15_h8` | `yangzhang_233` | -0.0142 | -4.88 | 0.0000 | Y | Y | N |
| `tb_label_k15_h8` | `yangzhang_144` | -0.0140 | -4.89 | 0.0000 | Y | Y | N |
| `tb_label_k20_h8` | `range_width_55` | -0.0139 | -5.36 | 0.0000 | Y | Y | N |
| `tb_label_k15_h8` | `atr_pct_144` | -0.0138 | -4.86 | 0.0000 | Y | Y | N |
| `tb_label_k15_h8` | `atr_pct_8` | -0.0138 | -4.95 | 0.0000 | Y | Y | N |
| `tb_label_k20_h8` | `range_width_8` | -0.0138 | -5.58 | 0.0000 | Y | Y | N |
