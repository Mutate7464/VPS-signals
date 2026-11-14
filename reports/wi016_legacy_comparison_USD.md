# WI-016 legacy vs triple-barrier label comparison — USD

- Generated (UTC): 2026-10-30T01:27:37Z
- Panel: 1,459,630 rows · 2721 dates · 593 symbols
- Identical rows/features for both label families; 116 features.

## Legacy five labels

| label | rows | dates | best feature | best |IC| | mean |IC| |
| :--- | ---: | ---: | :--- | ---: | ---: |
| `y_15d_high` | 1459630 | 2721 | `bb_width_144` | 0.0438 | 0.0147 |
| `y_15d_low` | 1459630 | 2721 | `atr_pct_8` | 0.0584 | 0.0207 |
| `y_20d_up` | 1459630 | 2721 | `atr_pct_8` | 0.0331 | 0.0118 |
| `y_20d_down` | 1459630 | 2721 | `atr_pct_233` | 0.0217 | 0.0076 |
| `y_20d_stay` | 1459630 | 2721 | `atr_pct_55` | 0.2056 | 0.0550 |

## Triple-barrier fib-ladder labels

| label | rows | dates | best feature | best |IC| | mean |IC| |
| :--- | ---: | ---: | :--- | ---: | ---: |
| `tb_label_k15_h8` | 1459630 | 2721 | `yangzhang_21` | 0.0145 | 0.0046 |
| `tb_label_k15_h21` | 1459630 | 2721 | `bb_width_144` | 0.0107 | 0.0043 |
| `tb_label_k15_h55` | 1459630 | 2721 | `bb_width_144` | 0.0119 | 0.0047 |
| `tb_label_k15_h144` | 1459630 | 2721 | `bb_width_144` | 0.0111 | 0.0045 |
| `tb_label_k15_h233` | 1459630 | 2721 | `bb_width_144` | 0.0118 | 0.0052 |
| `tb_label_k20_h8` | 1459630 | 2721 | `yangzhang_21` | 0.0179 | 0.0054 |
| `tb_label_k20_h21` | 1459630 | 2721 | `bb_width_144` | 0.0111 | 0.0043 |
| `tb_label_k20_h55` | 1459630 | 2721 | `frac_diff_close` | 0.0104 | 0.0045 |
| `tb_label_k20_h144` | 1459630 | 2721 | `frac_diff_close` | 0.0095 | 0.0042 |
| `tb_label_k20_h233` | 1459630 | 2721 | `rev_1m` | 0.0106 | 0.0050 |

- Legacy mean |IC| (all labels): 0.0220
- Triple-barrier mean |IC| (all k,h): 0.0047
- Verdict: legacy > triple-barrier (screening-scale, not a model claim).
