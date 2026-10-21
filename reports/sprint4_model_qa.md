# Sprint 4 — Model QA & Governance (Gate 4)

- Generated (UTC): 2026-10-21T02:57:28.766238+00:00
- Validation: 5-fold purged walk-forward, 20-day embargo, `tree_method='hist'`, `n_jobs=2`
- Precision@K: per-date top-K bucket, K = min(30, 10% of universe, >= 1)
- Deflated IC: t-stat divided by sqrt(horizon) to correct for overlapping labels
- CB-05: placebo ROC-AUC > 0.52 **and** z > 3.0 vs 0.5

## USD

- Regime source: equal-weight universe proxy (benchmark not synced)

### Governance metrics

| Target | Base rate | P@K lift (>=1.5) | BSS (>0.05) | PR-AUC lift (>1.35) | IC / t-defl (>0.04 / >2.5) | ROC-AUC | Gate |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| `y_15d_high` | 37.7% | 0.96 FAIL | -0.008 FAIL | 0.99 FAIL | 0.113 / 0.70 FAIL | 0.498 | **FAIL** |
| `y_15d_low` | 33.5% | 0.96 FAIL | -0.064 FAIL | 1.03 FAIL | 0.243 / 1.10 FAIL | 0.489 | **FAIL** |
| `y_20d_up` | 16.5% | 1.08 FAIL | -0.066 FAIL | 1.04 FAIL | 0.151 / 0.75 FAIL | 0.512 | **FAIL** |
| `y_20d_down` | 14.4% | 0.79 FAIL | -0.117 FAIL | 0.81 FAIL | 0.019 / 0.11 FAIL | 0.426 | **FAIL** |

### Diagnostic 1 — Placebo permutation test (CB-05)

| Target | Mean placebo ROC-AUC | z vs 0.5 | Seeds | CB-05 |
| :--- | ---: | ---: | :--- | :---: |
| `y_15d_high` | 0.497 | -0.33 | 0.527, 0.477, 0.508, 0.503, 0.470 | clear |
| `y_15d_low` | 0.488 | -1.26 | 0.481, 0.488, 0.469, 0.505, 0.497 | clear |
| `y_20d_up` | 0.495 | -0.45 | 0.499, 0.506, 0.478, 0.489, 0.501 | clear |
| `y_20d_down` | 0.489 | -0.83 | 0.502, 0.518, 0.449, 0.473, 0.505 | clear |

### Diagnostic 2 — Generalization gap (train PR-AUC − val PR-AUC)

| Target | Mean gap | Calibration | Recommendation |
| :--- | ---: | :--- | :--- |
| `y_15d_high` | 0.104 | isotonic | ok |
| `y_15d_low` | 0.029 | isotonic | ok |
| `y_20d_up` | 0.192 | isotonic, sigmoid | tighten: max_depth 4→3, min_child_weight 20→40, colsample_bytree 0.7→0.5 |
| `y_20d_down` | 0.062 | isotonic, sigmoid | ok |

### Diagnostic 3 — Regime stability (P@K by regime)

| Target | Regime | Dates | Base rate | P@K | Lift |
| :--- | :--- | ---: | ---: | ---: | ---: |
| `y_15d_high` | Bear | 10 | 24.0% | 30.0% | 1.25 |
| `y_15d_high` | Bull | 69 | 38.3% | 36.2% | 0.95 |
| `y_15d_high` | Sideways | 89 | 38.9% | 37.1% | 0.95 |
| `y_15d_low` | Bear | 10 | 56.0% | 50.0% | 0.89 |
| `y_15d_low` | Bull | 69 | 30.4% | 39.1% | 1.29 |
| `y_15d_low` | Sideways | 89 | 33.3% | 24.7% | 0.74 |
| `y_20d_up` | Bear | 10 | 34.0% | 0.0% | 0.00 |
| `y_20d_up` | Bull | 69 | 15.7% | 17.4% | 1.11 |
| `y_20d_up` | Sideways | 89 | 15.3% | 20.2% | 1.32 |
| `y_20d_down` | Bear | 10 | 0.0% | 0.0% | n/a |
| `y_20d_down` | Bull | 69 | 15.4% | 10.1% | 0.66 |
| `y_20d_down` | Sideways | 89 | 15.3% | 13.5% | 0.88 |

### Diagnostic 4 — SHAP dominance (> 35% flag)

| Target | Top feature | Share of |SHAP| | Flag |
| :--- | :--- | ---: | :---: |
| `y_15d_high` | `amihud_10_cs_pct` | 36.8% | **DOMINANT** |
| `y_15d_low` | `amihud_10` | 22.8% | ok |
| `y_20d_up` | `amihud_50` | 24.6% | ok |
| `y_20d_down` | `amihud_10` | 15.9% | ok |

## CAD

- Regime source: equal-weight universe proxy (benchmark not synced)

### Governance metrics

| Target | Base rate | P@K lift (>=1.5) | BSS (>0.05) | PR-AUC lift (>1.35) | IC / t-defl (>0.04 / >2.5) | ROC-AUC | Gate |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| `y_15d_high` | 38.7% | 1.08 FAIL | 0.029 FAIL | 0.93 FAIL | -0.059 / -0.34 FAIL | 0.460 | **FAIL** |
| `y_15d_low` | 32.1% | 0.57 FAIL | -0.038 FAIL | 0.98 FAIL | 0.006 / 0.03 FAIL | 0.508 | **FAIL** |
| `y_20d_up` | 20.4% | 0.99 FAIL | -0.050 FAIL | 1.15 FAIL | -0.035 / -0.18 FAIL | 0.540 | **FAIL** |
| `y_20d_down` | 18.6% | 0.45 FAIL | 0.035 FAIL | 0.86 FAIL | -0.087 / -0.40 FAIL | 0.442 | **FAIL** |

### Diagnostic 1 — Placebo permutation test (CB-05)

| Target | Mean placebo ROC-AUC | z vs 0.5 | Seeds | CB-05 |
| :--- | ---: | ---: | :--- | :---: |
| `y_15d_high` | 0.506 | 0.61 | 0.538, 0.501, 0.475, 0.481, 0.533 | clear |
| `y_15d_low` | 0.492 | -0.89 | 0.510, 0.504, 0.505, 0.505, 0.434 | clear |
| `y_20d_up` | 0.496 | -0.37 | 0.506, 0.510, 0.503, 0.490, 0.470 | clear |
| `y_20d_down` | 0.502 | 0.19 | 0.534, 0.552, 0.499, 0.460, 0.465 | clear |

### Diagnostic 2 — Generalization gap (train PR-AUC − val PR-AUC)

| Target | Mean gap | Calibration | Recommendation |
| :--- | ---: | :--- | :--- |
| `y_15d_high` | -0.020 | isotonic | ok |
| `y_15d_low` | 0.085 | isotonic | ok |
| `y_20d_up` | 0.115 | isotonic | ok |
| `y_20d_down` | -0.075 | isotonic, sigmoid | ok |

### Diagnostic 3 — Regime stability (P@K by regime)

| Target | Regime | Dates | Base rate | P@K | Lift |
| :--- | :--- | ---: | ---: | ---: | ---: |
| `y_15d_high` | Bull | 28 | 44.3% | 60.7% | 1.37 |
| `y_15d_high` | Sideways | 140 | 37.6% | 37.9% | 1.01 |
| `y_15d_low` | Bull | 28 | 24.3% | 0.0% | 0.00 |
| `y_15d_low` | Sideways | 140 | 33.7% | 22.1% | 0.66 |
| `y_20d_up` | Bull | 28 | 24.3% | 21.4% | 0.88 |
| `y_20d_up` | Sideways | 140 | 19.6% | 20.0% | 1.02 |
| `y_20d_down` | Bull | 28 | 33.6% | 32.1% | 0.96 |
| `y_20d_down` | Sideways | 140 | 15.6% | 3.6% | 0.23 |

### Diagnostic 4 — SHAP dominance (> 35% flag)

| Target | Top feature | Share of |SHAP| | Flag |
| :--- | :--- | ---: | :---: |
| `y_15d_high` | `hurst_50` | 52.3% | **DOMINANT** |
| `y_15d_low` | `amihud_5` | 21.1% | ok |
| `y_20d_up` | `hurst_50` | 24.2% | ok |
| `y_20d_down` | `bb_width_50` | 29.7% | ok |

