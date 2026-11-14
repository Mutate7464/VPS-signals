# WI-016 legacy vs triple-barrier label comparison — CAD

- Generated (UTC): 2026-10-30T00:49:11Z
- Panel: 833,859 rows · 2716 dates · 365 symbols
- Identical rows/features for both label families; 116 features.

## Legacy five labels

| label | rows | dates | best feature | best |IC| | mean |IC| |
| :--- | ---: | ---: | :--- | ---: | ---: |
| `y_15d_high` | 833859 | 2716 | `yangzhang_144` | 0.0801 | 0.0299 |
| `y_15d_low` | 833859 | 2716 | `atr_pct_8` | 0.0665 | 0.0230 |
| `y_20d_up` | 833859 | 2716 | `yangzhang_21` | 0.0662 | 0.0240 |
| `y_20d_down` | 833859 | 2716 | `atr_pct_233` | 0.0316 | 0.0118 |
| `y_20d_stay` | 833859 | 2716 | `atr_pct_55` | 0.2641 | 0.0734 |

## Triple-barrier fib-ladder labels

| label | rows | dates | best feature | best |IC| | mean |IC| |
| :--- | ---: | ---: | :--- | ---: | ---: |
| `tb_label_k15_h8` | 833859 | 2716 | `yangzhang_21` | 0.0447 | 0.0173 |
| `tb_label_k15_h21` | 833859 | 2716 | `yangzhang_21` | 0.0389 | 0.0160 |
| `tb_label_k15_h55` | 833859 | 2716 | `vol_20` | 0.0375 | 0.0160 |
| `tb_label_k15_h144` | 833859 | 2716 | `vol_20` | 0.0363 | 0.0158 |
| `tb_label_k15_h233` | 833859 | 2716 | `yangzhang_21` | 0.0380 | 0.0164 |
| `tb_label_k20_h8` | 833859 | 2716 | `yangzhang_21` | 0.0481 | 0.0178 |
| `tb_label_k20_h21` | 833859 | 2716 | `vol_20` | 0.0379 | 0.0147 |
| `tb_label_k20_h55` | 833859 | 2716 | `vol_20` | 0.0322 | 0.0138 |
| `tb_label_k20_h144` | 833859 | 2716 | `vol_20` | 0.0303 | 0.0134 |
| `tb_label_k20_h233` | 833859 | 2716 | `bb_width_21` | 0.0323 | 0.0141 |

- Legacy mean |IC| (all labels): 0.0324
- Triple-barrier mean |IC| (all k,h): 0.0155
- Verdict: legacy > triple-barrier (screening-scale, not a model claim).
