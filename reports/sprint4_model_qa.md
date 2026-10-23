# Sprint 4 — Model QA & Governance (Gate 4)

- Generated (UTC): 2026-10-23T13:06:50.887689+00:00
- Validation: 5-fold purged walk-forward, 20-day embargo, `tree_method='hist'`, `n_jobs=2`
- Precision@K: per-date top-K bucket, K = min(30, 10% of universe, >= 1)
- Deflated IC: t-stat divided by sqrt(horizon) to correct for overlapping labels
- CB-05: placebo ROC-AUC > 0.52 **and** z > 3.0 vs 0.5

## USD

- Universe: **508 symbols**, 1,240,275 rows, 2016-01-04 → 2026-09-23, source=`raw_ohlcv`

- Regime source: SPY benchmark

### Governance metrics

| Target | Base rate | P@K lift (>=1.5) | BSS (>0.05) | PR-AUC lift (>1.35) | IC / t-defl (>0.04 / >2.5) | ROC-AUC | Gate |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| `y_15d_high` | 30.8% | 1.19 FAIL | 0.006 FAIL | 1.09 FAIL | -0.012 / -1.11 FAIL | 0.539 | **FAIL** |
| `y_15d_low` | 33.4% | 1.11 FAIL | 0.004 FAIL | 1.08 FAIL | 0.009 / 0.85 FAIL | 0.537 | **FAIL** |
| `y_20d_up` | 18.9% | 1.03 FAIL | -0.006 FAIL | 1.01 FAIL | 0.001 / 0.13 FAIL | 0.506 | **FAIL** |
| `y_20d_down` | 11.7% | 1.06 FAIL | -0.023 FAIL | 0.99 FAIL | 0.001 / 0.10 FAIL | 0.483 | **FAIL** |

### Diagnostic 1 — Placebo permutation test (CB-05)

| Target | Mean placebo ROC-AUC | z vs 0.5 | Seeds | CB-05 |
| :--- | ---: | ---: | :--- | :---: |
| `y_15d_high` | 0.500 | 0.33 | 0.500 | clear |
| `y_15d_low` | 0.499 | -0.81 | 0.499 | clear |
| `y_20d_up` | 0.499 | -0.99 | 0.499 | clear |
| `y_20d_down` | 0.500 | -0.37 | 0.500 | clear |

### Diagnostic 2 — Generalization gap (train PR-AUC − val PR-AUC)

| Target | Mean gap | Calibration | Recommendation |
| :--- | ---: | :--- | :--- |
| `y_15d_high` | 0.000 | isotonic | ok |
| `y_15d_low` | 0.059 | isotonic | ok |
| `y_20d_up` | 0.075 | isotonic | ok |
| `y_20d_down` | 0.007 | isotonic | ok |

### Diagnostic 3 — Regime stability (P@K by regime)

| Target | Regime | Dates | Base rate | P@K | Lift |
| :--- | :--- | ---: | ---: | ---: | ---: |
| `y_15d_high` | Bear | 169 | 24.0% | 29.0% | 1.21 |
| `y_15d_high` | Bull | 676 | 32.3% | 38.7% | 1.20 |
| `y_15d_high` | Sideways | 773 | 31.0% | 36.4% | 1.17 |
| `y_15d_low` | Bear | 169 | 36.8% | 39.6% | 1.08 |
| `y_15d_low` | Bull | 676 | 32.5% | 37.3% | 1.15 |
| `y_15d_low` | Sideways | 773 | 33.5% | 36.4% | 1.09 |
| `y_20d_up` | Bear | 169 | 24.7% | 25.1% | 1.02 |
| `y_20d_up` | Bull | 676 | 18.3% | 19.6% | 1.07 |
| `y_20d_up` | Sideways | 773 | 18.1% | 18.0% | 0.99 |
| `y_20d_down` | Bear | 169 | 6.7% | 6.6% | 1.00 |
| `y_20d_down` | Bull | 676 | 11.4% | 11.5% | 1.01 |
| `y_20d_down` | Sideways | 773 | 13.1% | 14.6% | 1.11 |

### Diagnostic 4 — SHAP dominance (> 35% flag)

| Target | Top feature | Share of |SHAP| | Flag |
| :--- | :--- | ---: | :---: |
| `y_15d_high` | `yangzhang_100` | 27.3% | ok |
| `y_15d_low` | `bb_width_10_cs_pct` | 20.5% | ok |
| `y_20d_up` | `bb_width_5_cs_pct` | 17.0% | ok |
| `y_20d_down` | `atr_pct_100` | 22.8% | ok |

