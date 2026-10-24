# D-002 / E3 — Feature-set ablation matrix (USD)

- Generated (UTC): 2026-10-24T17:14:23Z
- Source: per-set `data/oof_{MKT}[_<set>].parquet` (1 real + 3 placebo seeds), E2-frozen hyper-parameters
- PR-AUC lift = PR-AUC / pos-rate; P@K lift = within-date top-10% precision / base rate;
  deflated IC t = (real mean per-date Spearman IC − mean placebo IC) / se(real IC);
  placebo z = (real ROC-AUC − mean placebo AUC) / std(placebo AUC)

| Set | Target | ROC-AUC | PR-AUC lift | P@K lift | Deflated IC t | Placebo z |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| `full` | `y_15d_high` | 0.546 | 1.109 | 1.222 | +1.98 | +26.7 |
| `full` | `y_15d_low` | 0.539 | 1.088 | 1.132 | +3.54 | +52.2 |
| `full` | `y_20d_up` | 0.497 | 0.989 | 1.028 | +1.41 | -0.2 |
| `full` | `y_20d_down` | 0.483 | 0.990 | 1.154 | -1.58 | -0.6 |
| `no_static` | `y_15d_high` | 0.543 | 1.105 | 1.219 | +3.33 | +32.8 |
| `no_static` | `y_15d_low` | 0.537 | 1.088 | 1.124 | +3.23 | +49.8 |
| `no_static` | `y_20d_up` | 0.494 | 0.980 | 0.979 | -1.44 | +1.0 |
| `no_static` | `y_20d_down` | 0.479 | 0.981 | 1.158 | +2.25 | -1.9 |
| `fib_only` | `y_15d_high` | 0.536 | 1.094 | 1.200 | +2.73 | +3.5 |
| `fib_only` | `y_15d_low` | 0.526 | 1.062 | 1.064 | +0.36 | +6.2 |
| `fib_only` | `y_20d_up` | 0.495 | 0.992 | 1.077 | -0.20 | +0.2 |
| `fib_only` | `y_20d_down` | 0.480 | 0.974 | 1.143 | -2.19 | -0.8 |
| `legacy19` | `y_15d_high` | 0.541 | 1.096 | 1.199 | +4.11 | +5.5 |
| `legacy19` | `y_15d_low` | 0.534 | 1.068 | 1.121 | +3.78 | +11.4 |
| `legacy19` | `y_20d_up` | 0.501 | 1.000 | 1.082 | -1.13 | +3.7 |
| `legacy19` | `y_20d_down` | 0.478 | 0.956 | 1.160 | +2.06 | -1.3 |
| `cs_pct_only` | `y_15d_high` | 0.539 | 1.089 | 1.229 | +4.64 | +136.7 |
| `cs_pct_only` | `y_15d_low` | 0.527 | 1.058 | 1.122 | +1.56 | +6.2 |
| `cs_pct_only` | `y_20d_up` | 0.498 | 0.993 | 1.032 | -0.23 | +20.1 |
| `cs_pct_only` | `y_20d_down` | 0.480 | 0.951 | 1.119 | +3.63 | -1.0 |

## Verdict

Verdict: **H2 PARTIALLY OBSERVED.** Deflated IC t > 2.5 on: full/y_15d_low, legacy19/y_15d_high, legacy19/y_15d_low, no_static/y_15d_high, no_static/y_15d_low, fib_only/y_15d_high, cs_pct_only/y_15d_high, cs_pct_only/y_20d_down — signal exists but is not exclusive to a new feature set (baseline reaches it too); the ablation does not isolate a feature-set fix.

| ADR row | Applies? | Basis |
| :--- | :--- | :--- |
| E3 → H2 (feature-set redesign) | no | non-baseline t>2.5: no_static/y_15d_high, no_static/y_15d_low, fib_only/y_15d_high, cs_pct_only/y_15d_high, cs_pct_only/y_20d_down; baseline t>2.5: full/y_15d_low, legacy19/y_15d_high, legacy19/y_15d_low |
| E4 → H3 | adjudicated | see `reports/diag_D002_e4.md` |
| E5 → H4 | adjudicated next | see `reports/diag_D002_e5.md` |
