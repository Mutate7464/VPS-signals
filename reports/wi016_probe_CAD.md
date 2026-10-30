# WI-016 probe-first gate — CAD

- Generated (UTC): 2026-10-30T01:00:57Z
- Panel rows: 833,859 · features: 116 · targets: 10
- Tests: 1160 · BH-FDR alpha 0.05 · cost overlay 20.0 bps (NO_TRADE default)

## DECISION: **CLEAR**

A target clears only when it has a feature that is FDR-significant, same-sign,
placebo-clear and cost-tradeable.

| target | cleared | passing features | best feature | best IC |
| :--- | :---: | ---: | :--- | ---: |
| `tb_label_k15_h8` | yes | 22 | `yangzhang_21` | -0.0447 |
| `tb_label_k15_h21` | yes | 16 | `yangzhang_21` | -0.0389 |
| `tb_label_k15_h55` | yes | 9 | `vol_20` | -0.0375 |
| `tb_label_k15_h144` | yes | 8 | `vol_20` | -0.0363 |
| `tb_label_k15_h233` | yes | 11 | `yangzhang_21` | -0.0380 |
| `tb_label_k20_h8` | yes | 23 | `yangzhang_21` | -0.0481 |
| `tb_label_k20_h21` | yes | 11 | `vol_20` | -0.0379 |
| `tb_label_k20_h55` | no | 0 | - | - |
| `tb_label_k20_h144` | no | 0 | - | - |
| `tb_label_k20_h233` | no | 0 | - | - |

## Label class balance / density

| target | events | +1 | -1 | 0 |
| :--- | ---: | ---: | ---: | ---: |
| `tb_label_k15_h8` | 828944 | 439330 | 381555 | 8059 |
| `tb_label_k15_h21` | 824199 | 445377 | 377117 | 1705 |
| `tb_label_k15_h55` | 811789 | 442603 | 369032 | 154 |
| `tb_label_k15_h144` | 779309 | 424360 | 354948 | 1 |
| `tb_label_k15_h233` | 746988 | 405419 | 341569 | 0 |
| `tb_label_k20_h8` | 828944 | 440078 | 378257 | 10609 |
| `tb_label_k20_h21` | 824199 | 451250 | 369897 | 3052 |
| `tb_label_k20_h55` | 811789 | 453009 | 358451 | 329 |
| `tb_label_k20_h144` | 779309 | 434735 | 344562 | 12 |
| `tb_label_k20_h233` | 746988 | 415233 | 331755 | 0 |

## Events per purged fold (`embargo_td = max(20, horizon)`)

| target | h | folds (events) |
| :--- | ---: | :--- |
| `tb_label_k15_h8` | 8 | f0=93619, f1=102574, f2=107538, f3=113305, f4=115528 |
| `tb_label_k15_h21` | 21 | f0=93619, f1=102574, f2=107538, f3=113305, f4=110783 |
| `tb_label_k15_h55` | 55 | f0=93619, f1=102574, f2=107538, f3=113305, f4=98373 |
| `tb_label_k15_h144` | 144 | f0=93619, f1=102574, f2=107538, f3=113305, f4=65893 |
| `tb_label_k15_h233` | 233 | f0=93619, f1=102574, f2=107538, f3=113305, f4=33572 |
| `tb_label_k20_h8` | 8 | f0=93619, f1=102574, f2=107538, f3=113305, f4=115528 |
| `tb_label_k20_h21` | 21 | f0=93619, f1=102574, f2=107538, f3=113305, f4=110783 |
| `tb_label_k20_h55` | 55 | f0=93619, f1=102574, f2=107538, f3=113305, f4=98373 |
| `tb_label_k20_h144` | 144 | f0=93619, f1=102574, f2=107538, f3=113305, f4=65893 |
| `tb_label_k20_h233` | 233 | f0=93619, f1=102574, f2=107538, f3=113305, f4=33572 |

## Top FDR-significant tests

| target | feature | IC | t | q | same-sign | placebo-clear | tradeable |
| :--- | :--- | ---: | ---: | ---: | :---: | :---: | :---: |
| `tb_label_k20_h8` | `yangzhang_21` | -0.0481 | -14.41 | 0.0000 | Y | Y | Y |
| `tb_label_k20_h8` | `yangzhang_55` | -0.0475 | -14.02 | 0.0000 | Y | Y | Y |
| `tb_label_k20_h8` | `yangzhang_8` | -0.0469 | -14.44 | 0.0000 | Y | Y | Y |
| `tb_label_k20_h8` | `yangzhang_144` | -0.0461 | -13.40 | 0.0000 | Y | Y | Y |
| `tb_label_k20_h8` | `vol_20` | -0.0459 | -13.86 | 0.0000 | Y | Y | Y |
| `tb_label_k20_h8` | `atr_pct_233` | -0.0453 | -13.41 | 0.0000 | Y | Y | Y |
| `tb_label_k20_h8` | `yangzhang_233` | -0.0452 | -12.95 | 0.0000 | Y | Y | Y |
| `tb_label_k20_h8` | `atr_pct_144` | -0.0451 | -13.40 | 0.0000 | Y | Y | Y |
| `tb_label_k20_h8` | `atr_pct_55` | -0.0449 | -13.14 | 0.0000 | Y | Y | Y |
| `tb_label_k15_h8` | `yangzhang_21` | -0.0447 | -13.55 | 0.0000 | Y | Y | Y |
| `tb_label_k20_h8` | `atr_pct_21` | -0.0446 | -13.08 | 0.0000 | Y | Y | Y |
| `tb_label_k20_h8` | `atr_pct_8` | -0.0443 | -13.19 | 0.0000 | Y | Y | Y |
| `tb_label_k15_h8` | `yangzhang_55` | -0.0442 | -13.21 | 0.0000 | Y | Y | Y |
| `tb_label_k15_h8` | `yangzhang_8` | -0.0438 | -13.62 | 0.0000 | Y | Y | Y |
| `tb_label_k15_h8` | `vol_20` | -0.0427 | -13.08 | 0.0000 | Y | Y | Y |
| `tb_label_k15_h8` | `yangzhang_144` | -0.0425 | -12.57 | 0.0000 | Y | Y | Y |
| `tb_label_k20_h8` | `yangzhang_3` | -0.0424 | -13.56 | 0.0000 | Y | Y | Y |
| `tb_label_k20_h8` | `atr_pct_3` | -0.0420 | -12.96 | 0.0000 | Y | Y | Y |
| `tb_label_k15_h8` | `yangzhang_233` | -0.0417 | -12.18 | 0.0000 | Y | Y | Y |
| `tb_label_k20_h8` | `range_width_21` | -0.0413 | -13.22 | 0.0000 | Y | Y | Y |
| `tb_label_k15_h8` | `atr_pct_233` | -0.0409 | -12.37 | 0.0000 | Y | Y | Y |
| `tb_label_k15_h8` | `atr_pct_144` | -0.0407 | -12.32 | 0.0000 | Y | Y | Y |
| `tb_label_k15_h8` | `atr_pct_55` | -0.0406 | -12.09 | 0.0000 | Y | Y | Y |
| `tb_label_k15_h8` | `atr_pct_21` | -0.0405 | -12.05 | 0.0000 | Y | Y | Y |
| `tb_label_k15_h8` | `atr_pct_8` | -0.0405 | -12.22 | 0.0000 | Y | Y | Y |
