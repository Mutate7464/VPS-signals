# WI-042 — modern L2 rerun under the D-024 harness (Layer 2)

- 2026-11-10T16:14:11Z · BH-FDR family `wi042_modern_l2_rerun` (30 tested cells, alpha 0.05) — never pooled with WI-043's; counts {'ADOPT': 20, 'INCONCLUSIVE': 1, 'INERT': 49, 'REJECT': 21} · runtime 29.2s
- Harness `src/l2_overlay/harness.py` (WI-041): INERT precheck on CALIB, tau from CALIB edge only, one-shot EVAL, 5-seed placebo. **PROVISIONAL** until the admin ratifies the verdicts (WORKFLOW); a REJECT closes that question under D-024 §2
- Inputs: `manifest.parquet` (67 `xgboost`/`b_hold`/`exact_full_k0.8` fold pickles) -> fold-consistent OOF at the frozen at-bottom entries; horizons [5, 8, 13, 21, 34, 55, 89]; baseline = frozen fib-rule return (25 bps inside `r_frozen`); stack = CALIB elastic-net logistic over the horizon vector

## USD — 32,100 at-bottom entries, 40 design columns, horizons [5, 8, 13, 34, 55, 89] (partial [89]), 0 rows without a WI-027 regime label

### wi037 — b_hold veto on frozen fib entries

`wi037_frozen_fib_w28entry_w30exit_t15_s10_d39_close`; score `1 - p(b_hold h13)`; sources raw + stack

| cell | verdict | tau | CALIB edge | EVAL edge | folds | placebo z | p | q | n_calib | n_eval | note |
| :--- | :---: | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| `wi037|raw|all` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 10,268 | 20,616 | INERT: mass min 0.8759 at/above tau range [0.10, 0.70] |
| `wi037|raw|chop_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,298 | 3,568 | INERT: mass min 0.9429 at/above tau range [0.10, 0.70] |
| `wi037|raw|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 32 | 613 | INERT: CALIB events 32 < floor 200 |
| `wi037|raw|down_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,744 | 2,972 | INERT: mass min 0.9094 at/above tau range [0.10, 0.70] |
| `wi037|raw|up_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 4,059 | 8,331 | INERT: mass min 0.8759 at/above tau range [0.10, 0.70] |
| `wi037|raw|up_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,135 | 5,050 | INERT: mass min 0.9590 at/above tau range [0.10, 0.70] |
| `wi037|stack|all` | **REJECT** | 0.10 | +0.00000 | +0.00000 | 0:+0.0000, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | n/a | n/a | n/a | 10,268 | 20,616 | — |
| `wi037|stack|chop_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,298 | 3,568 | INERT: mass min 0.9571 at/above tau range [0.10, 0.70] |
| `wi037|stack|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 32 | 613 | INERT: CALIB events 32 < floor 200 |
| `wi037|stack|down_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,744 | 2,972 | INERT: mass min 0.7642 at/above tau range [0.10, 0.70] |
| `wi037|stack|up_high` | **REJECT** | 0.10 | +0.00000 | +0.00000 | 0:+0.0000, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | n/a | n/a | n/a | 4,059 | 8,331 | — |
| `wi037|stack|up_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,135 | 5,050 | INERT: mass min 0.8922 at/above tau range [0.10, 0.70] |

### wi033 — 3-class swing-conditioned overlay (HOLD <-> b_hold)

`wi033_frozen_fib_w28entry_w30exit_t15_s10_d39_close`; score `1 - p(b_hold h21)`; sources raw + stack

| cell | verdict | tau | CALIB edge | EVAL edge | folds | placebo z | p | q | n_calib | n_eval | note |
| :--- | :---: | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| `wi033|raw|all` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 10,268 | 0 | INERT: no WI-040 library cell for exact_full_k0.8/b_hold/h21 |
| `wi033|stack|all` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 10,268 | 20,616 | INERT: mass min 0.7056 at/above tau range [0.10, 0.70] |
| `wi033|stack|chop_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,298 | 3,568 | INERT: mass min 0.9847 at/above tau range [0.10, 0.70] |
| `wi033|stack|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 32 | 613 | INERT: CALIB events 32 < floor 200 |
| `wi033|stack|down_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,744 | 2,972 | INERT: mass min 0.7881 at/above tau range [0.10, 0.70] |
| `wi033|stack|up_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 4,059 | 8,331 | INERT: mass min 0.7056 at/above tau range [0.10, 0.70] |
| `wi033|stack|up_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,135 | 5,050 | INERT: mass min 0.9789 at/above tau range [0.10, 0.70] |

### wi030 — learned exit chooser vs the frozen exit cell

`wi030_frozen_fib_w28entry_w30exit_t15_s10_d39_close`; score `1 - p(b_hold h34)`; sources raw + stack

| cell | verdict | tau | CALIB edge | EVAL edge | folds | placebo z | p | q | n_calib | n_eval | note |
| :--- | :---: | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| `wi030|raw|all` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 10,268 | 20,616 | INERT: mass min 0.9997 at/above tau range [0.10, 0.70] |
| `wi030|raw|chop_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,298 | 3,568 | INERT: mass min 0.9997 at/above tau range [0.10, 0.70] |
| `wi030|raw|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 32 | 613 | INERT: CALIB events 32 < floor 200 |
| `wi030|raw|down_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,744 | 2,972 | INERT: mass min 0.9997 at/above tau range [0.10, 0.70] |
| `wi030|raw|up_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 4,059 | 8,331 | INERT: mass min 0.9997 at/above tau range [0.10, 0.70] |
| `wi030|raw|up_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,135 | 5,050 | INERT: mass min 0.9997 at/above tau range [0.10, 0.70] |
| `wi030|stack|all` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 10,268 | 20,616 | INERT: mass min 0.7085 at/above tau range [0.10, 0.70] |
| `wi030|stack|chop_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,298 | 3,568 | INERT: mass min 0.9827 at/above tau range [0.10, 0.70] |
| `wi030|stack|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 32 | 613 | INERT: CALIB events 32 < floor 200 |
| `wi030|stack|down_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,744 | 2,972 | INERT: mass min 0.7790 at/above tau range [0.10, 0.70] |
| `wi030|stack|up_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 4,059 | 8,331 | INERT: mass min 0.7085 at/above tau range [0.10, 0.70] |
| `wi030|stack|up_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,135 | 5,050 | INERT: mass min 0.9763 at/above tau range [0.10, 0.70] |

### wi028 — entry-window chooser (k=0 vs k=3/k=5)

`wi028_frozen_fib_w28entry_w30exit_t15_s10_d39_close`; score `1 - p(b_hold h5)`; sources raw + stack

| cell | verdict | tau | CALIB edge | EVAL edge | folds | placebo z | p | q | n_calib | n_eval | note |
| :--- | :---: | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| `wi028|raw|all` | **ADOPT** | 0.50 | +0.00002 | +0.00009 | 0:+0.0000, 1:+0.0000, 2:+0.0001, 3:+0.0002, 4:+0.0000 | +2.20 | 0.0138 | 0.0197 | 10,268 | 20,616 | — |
| `wi028|raw|chop_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,298 | 3,568 | INERT: mass min 0.7047 at/above tau range [0.10, 0.70] |
| `wi028|raw|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 32 | 613 | INERT: CALIB events 32 < floor 200 |
| `wi028|raw|down_high` | **REJECT** | 0.10 | +0.00000 | +0.00006 | 0:+0.0000, 1:+0.0000, 2:+0.0002, 3:+0.0000, 4:+0.0000 | +1.78 | 0.0372 | 0.0485 | 2,744 | 2,972 | — |
| `wi028|raw|up_high` | **ADOPT** | 0.50 | +0.00006 | +0.00010 | 0:+0.0001, 1:+0.0000, 2:+0.0001, 3:+0.0004, 4:+0.0000 | +2.20 | 0.0138 | 0.0197 | 4,059 | 8,331 | — |
| `wi028|raw|up_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,135 | 5,050 | INERT: mass min 0.7059 at/above tau range [0.10, 0.70] |
| `wi028|stack|all` | **REJECT** | 0.10 | +0.00000 | +0.00000 | 0:+0.0000, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | n/a | n/a | n/a | 10,268 | 20,616 | — |
| `wi028|stack|chop_high` | **REJECT** | 0.10 | +0.00000 | +0.00000 | 0:+0.0000, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | n/a | n/a | n/a | 1,298 | 3,568 | — |
| `wi028|stack|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 32 | 613 | INERT: CALIB events 32 < floor 200 |
| `wi028|stack|down_high` | **REJECT** | 0.10 | +0.00000 | +0.00000 | 0:+0.0000, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | n/a | n/a | n/a | 2,744 | 2,972 | — |
| `wi028|stack|up_high` | **REJECT** | 0.10 | +0.00000 | +0.00000 | 0:+0.0000, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | n/a | n/a | n/a | 4,059 | 8,331 | — |
| `wi028|stack|up_normal` | **REJECT** | 0.10 | +0.00000 | +0.00000 | 0:+0.0000, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | n/a | n/a | n/a | 2,135 | 5,050 | — |

## CAD — 17,256 at-bottom entries, 38 design columns, horizons [5, 8, 13, 21, 34, 55, 89] (partial none), 0 rows without a WI-027 regime label

### wi037 — b_hold veto on frozen fib entries

`wi037_frozen_fib_w28entry_w30exit_t15_s10_d39_close`; score `1 - p(b_hold h13)`; sources raw + stack

| cell | verdict | tau | CALIB edge | EVAL edge | folds | placebo z | p | q | n_calib | n_eval | note |
| :--- | :---: | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| `wi037|raw|all` | **ADOPT** | 0.50 | +0.00026 | +0.00000 | 0:-0.0001, 1:+0.0005, 2:+0.0000, 3:+0.0000, 4:+0.0000 | +2.35 | 0.00936 | 0.0148 | 5,315 | 11,237 | — |
| `wi037|raw|chop_high` | **REJECT** | 0.10 | -0.00035 | +0.00000 | 0:-0.0007, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | -1.62 | 0.947 | 0.947 | 1,076 | 1,013 | — |
| `wi037|raw|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 20 | 505 | INERT: CALIB events 20 < floor 200 |
| `wi037|raw|down_high` | **REJECT** | 0.10 | +0.00000 | +0.00000 | 0:+0.0000, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | -1.62 | 0.947 | 0.947 | 1,131 | 1,309 | — |
| `wi037|raw|up_high` | **ADOPT** | 0.50 | +0.00028 | +0.00000 | 0:+0.0000, 1:+0.0009, 2:+0.0000, 3:+0.0000, 4:+0.0000 | +2.35 | 0.00936 | 0.0148 | 1,786 | 2,537 | — |
| `wi037|raw|up_normal` | **ADOPT** | 0.50 | +0.00089 | +0.00000 | 0:+0.0000, 1:+0.0015, 2:+0.0000, 3:+0.0000, 4:+0.0000 | +2.35 | 0.00936 | 0.0148 | 1,302 | 5,835 | — |
| `wi037|stack|all` | **ADOPT** | 0.20 | +0.00029 | +0.00000 | 0:-0.0001, 1:+0.0005, 2:+0.0000, 3:+0.0000, 4:+0.0000 | +3.50 | 0.000232 | 0.000434 | 5,315 | 11,237 | — |
| `wi037|stack|chop_high` | **REJECT** | 0.10 | +0.00000 | +0.00000 | 0:+0.0000, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | n/a | n/a | n/a | 1,076 | 1,013 | — |
| `wi037|stack|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 20 | 505 | INERT: CALIB events 20 < floor 200 |
| `wi037|stack|down_high` | **REJECT** | 0.10 | +0.00000 | +0.00000 | 0:+0.0000, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | n/a | n/a | n/a | 1,131 | 1,309 | — |
| `wi037|stack|up_high` | **ADOPT** | 0.20 | +0.00028 | +0.00000 | 0:+0.0000, 1:+0.0009, 2:+0.0000, 3:+0.0000, 4:+0.0000 | +3.50 | 0.000232 | 0.000434 | 1,786 | 2,537 | — |
| `wi037|stack|up_normal` | **ADOPT** | 0.50 | +0.00098 | +0.00000 | 0:+0.0002, 1:+0.0015, 2:+0.0000, 3:+0.0000, 4:+0.0000 | +1.84 | 0.0329 | 0.0449 | 1,302 | 5,835 | — |

### wi033 — 3-class swing-conditioned overlay (HOLD <-> b_hold)

`wi033_frozen_fib_w28entry_w30exit_t15_s10_d39_close`; score `1 - p(b_hold h21)`; sources raw + stack

| cell | verdict | tau | CALIB edge | EVAL edge | folds | placebo z | p | q | n_calib | n_eval | note |
| :--- | :---: | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| `wi033|raw|all` | **ADOPT** | 0.50 | +0.00033 | +0.00000 | 0:+0.0000, 1:+0.0005, 2:+0.0000, 3:+0.0000, 4:+0.0000 | +3.62 | 0.000146 | 0.000313 | 5,315 | 11,237 | — |
| `wi033|raw|chop_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,076 | 1,013 | INERT: mass min 0.7958 at/above tau range [0.10, 0.70] |
| `wi033|raw|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 20 | 505 | INERT: CALIB events 20 < floor 200 |
| `wi033|raw|down_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,131 | 1,309 | INERT: mass min 0.7958 at/above tau range [0.10, 0.70] |
| `wi033|raw|up_high` | **ADOPT** | 0.50 | +0.00028 | +0.00000 | 0:+0.0000, 1:+0.0009, 2:+0.0000, 3:+0.0000, 4:+0.0000 | +3.62 | 0.000146 | 0.000313 | 1,786 | 2,537 | — |
| `wi033|raw|up_normal` | **ADOPT** | 0.50 | +0.00089 | +0.00000 | 0:+0.0000, 1:+0.0015, 2:+0.0000, 3:+0.0000, 4:+0.0000 | +3.62 | 0.000146 | 0.000313 | 1,302 | 5,835 | — |
| `wi033|stack|all` | **ADOPT** | 0.50 | +0.00023 | +0.00000 | 0:-0.0002, 1:+0.0005, 2:+0.0000, 3:+0.0000, 4:+0.0000 | +3.90 | 4.76e-05 | 0.000143 | 5,315 | 11,237 | — |
| `wi033|stack|chop_high` | **REJECT** | 0.10 | +0.00000 | +0.00000 | 0:+0.0000, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | n/a | n/a | n/a | 1,076 | 1,013 | — |
| `wi033|stack|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 20 | 505 | INERT: CALIB events 20 < floor 200 |
| `wi033|stack|down_high` | **REJECT** | 0.10 | +0.00000 | +0.00000 | 0:+0.0000, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | n/a | n/a | n/a | 1,131 | 1,309 | — |
| `wi033|stack|up_high` | **ADOPT** | 0.70 | +0.00016 | +0.00000 | 0:-0.0001, 1:+0.0009, 2:+0.0000, 3:+0.0000, 4:+0.0000 | +3.67 | 0.000121 | 0.000313 | 1,786 | 2,537 | — |
| `wi033|stack|up_normal` | **ADOPT** | 0.50 | +0.00098 | +0.00000 | 0:+0.0002, 1:+0.0015, 2:+0.0000, 3:+0.0000, 4:+0.0000 | +3.90 | 4.76e-05 | 0.000143 | 1,302 | 5,835 | — |

### wi030 — learned exit chooser vs the frozen exit cell

`wi030_frozen_fib_w28entry_w30exit_t15_s10_d39_close`; score `1 - p(b_hold h34)`; sources raw + stack

| cell | verdict | tau | CALIB edge | EVAL edge | folds | placebo z | p | q | n_calib | n_eval | note |
| :--- | :---: | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| `wi030|raw|all` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 5,315 | 11,237 | INERT: mass min 0.9977 at/above tau range [0.10, 0.70] |
| `wi030|raw|chop_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,076 | 1,013 | INERT: mass min 0.9977 at/above tau range [0.10, 0.70] |
| `wi030|raw|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 20 | 505 | INERT: CALIB events 20 < floor 200 |
| `wi030|raw|down_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,131 | 1,309 | INERT: mass min 0.9977 at/above tau range [0.10, 0.70] |
| `wi030|raw|up_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,786 | 2,537 | INERT: mass min 0.9977 at/above tau range [0.10, 0.70] |
| `wi030|raw|up_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,302 | 5,835 | INERT: mass min 0.9977 at/above tau range [0.10, 0.70] |
| `wi030|stack|all` | **ADOPT** | 0.70 | +0.00034 | +0.00000 | 0:+0.0000, 1:+0.0005, 2:+0.0000, 3:+0.0000, 4:+0.0000 | +5.88 | 2.08e-09 | 2.08e-08 | 5,315 | 11,237 | — |
| `wi030|stack|chop_high` | **REJECT** | 0.10 | +0.00000 | +0.00000 | 0:+0.0000, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | n/a | n/a | n/a | 1,076 | 1,013 | — |
| `wi030|stack|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 20 | 505 | INERT: CALIB events 20 < floor 200 |
| `wi030|stack|down_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,131 | 1,309 | INERT: mass min 0.8214 at/above tau range [0.10, 0.70] |
| `wi030|stack|up_high` | **ADOPT** | 0.70 | +0.00037 | +0.00000 | 0:+0.0002, 1:+0.0009, 2:+0.0000, 3:+0.0000, 4:+0.0000 | +5.88 | 2.08e-09 | 2.08e-08 | 1,786 | 2,537 | — |
| `wi030|stack|up_normal` | **ADOPT** | 0.70 | +0.00098 | +0.00000 | 0:+0.0002, 1:+0.0015, 2:+0.0000, 3:+0.0000, 4:+0.0000 | +5.88 | 2.08e-09 | 2.08e-08 | 1,302 | 5,835 | — |

### wi028 — entry-window chooser (k=0 vs k=3/k=5)

`wi028_frozen_fib_w28entry_w30exit_t15_s10_d39_close`; score `1 - p(b_hold h5)`; sources raw + stack

| cell | verdict | tau | CALIB edge | EVAL edge | folds | placebo z | p | q | n_calib | n_eval | note |
| :--- | :---: | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| `wi028|raw|all` | **REJECT** | 0.10 | -0.00013 | +0.00001 | 0:-0.0002, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | -1.23 | 0.891 | 0.947 | 5,315 | 11,237 | — |
| `wi028|raw|chop_high` | **REJECT** | 0.10 | -0.00048 | +0.00000 | 0:-0.0009, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | -1.23 | 0.891 | 0.947 | 1,076 | 1,013 | — |
| `wi028|raw|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 20 | 505 | INERT: CALIB events 20 < floor 200 |
| `wi028|raw|down_high` | **REJECT** | 0.10 | -0.00017 | +0.00000 | 0:-0.0003, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | -1.23 | 0.891 | 0.947 | 1,131 | 1,309 | — |
| `wi028|raw|up_high` | **REJECT** | 0.10 | -0.00006 | +0.00000 | 0:-0.0001, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | -1.23 | 0.891 | 0.947 | 1,786 | 2,537 | — |
| `wi028|raw|up_normal` | **INCONCLUSIVE** | 0.10 | +0.00009 | +0.00002 | 0:+0.0002, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | -1.23 | 0.891 | 0.947 | 1,302 | 5,835 | — |
| `wi028|stack|all` | **ADOPT** | 0.10 | +0.00014 | +0.00000 | 0:-0.0003, 1:+0.0005, 2:+0.0000, 3:+0.0000, 4:+0.0000 | +4.50 | 3.35e-06 | 1.26e-05 | 5,315 | 11,237 | — |
| `wi028|stack|chop_high` | **REJECT** | 0.10 | -0.00048 | +0.00000 | 0:-0.0009, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | +4.50 | 3.35e-06 | 1.26e-05 | 1,076 | 1,013 | — |
| `wi028|stack|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 20 | 505 | INERT: CALIB events 20 < floor 200 |
| `wi028|stack|down_high` | **REJECT** | 0.10 | -0.00017 | +0.00000 | 0:-0.0003, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | +4.50 | 3.35e-06 | 1.26e-05 | 1,131 | 1,309 | — |
| `wi028|stack|up_high` | **ADOPT** | 0.10 | +0.00005 | +0.00000 | 0:-0.0003, 1:+0.0009, 2:+0.0000, 3:+0.0000, 4:+0.0000 | +4.50 | 3.35e-06 | 1.26e-05 | 1,786 | 2,537 | — |
| `wi028|stack|up_normal` | **ADOPT** | 0.10 | +0.00098 | +0.00000 | 0:+0.0002, 1:+0.0015, 2:+0.0000, 3:+0.0000, 4:+0.0000 | +4.50 | 3.35e-06 | 1.26e-05 | 1,302 | 5,835 | — |

## BH-FDR family (every tested cell)

| cell | verdict | CALIB edge | EVAL edge | placebo z | p | q |
| :--- | :---: | ---: | ---: | ---: | ---: | ---: |
| `wi030|stack|all` | ADOPT | +0.00034 | +0.00000 | +5.88 | 2.08e-09 | 2.08e-08 |
| `wi030|stack|up_high` | ADOPT | +0.00037 | +0.00000 | +5.88 | 2.08e-09 | 2.08e-08 |
| `wi030|stack|up_normal` | ADOPT | +0.00098 | +0.00000 | +5.88 | 2.08e-09 | 2.08e-08 |
| `wi028|stack|all` | ADOPT | +0.00014 | +0.00000 | +4.50 | 3.35e-06 | 1.26e-05 |
| `wi028|stack|chop_high` | REJECT | -0.00048 | +0.00000 | +4.50 | 3.35e-06 | 1.26e-05 |
| `wi028|stack|down_high` | REJECT | -0.00017 | +0.00000 | +4.50 | 3.35e-06 | 1.26e-05 |
| `wi028|stack|up_high` | ADOPT | +0.00005 | +0.00000 | +4.50 | 3.35e-06 | 1.26e-05 |
| `wi028|stack|up_normal` | ADOPT | +0.00098 | +0.00000 | +4.50 | 3.35e-06 | 1.26e-05 |
| `wi033|stack|all` | ADOPT | +0.00023 | +0.00000 | +3.90 | 4.76e-05 | 0.000143 |
| `wi033|stack|up_normal` | ADOPT | +0.00098 | +0.00000 | +3.90 | 4.76e-05 | 0.000143 |
| `wi033|stack|up_high` | ADOPT | +0.00016 | +0.00000 | +3.67 | 0.000121 | 0.000313 |
| `wi033|raw|all` | ADOPT | +0.00033 | +0.00000 | +3.62 | 0.000146 | 0.000313 |
| `wi033|raw|up_high` | ADOPT | +0.00028 | +0.00000 | +3.62 | 0.000146 | 0.000313 |
| `wi033|raw|up_normal` | ADOPT | +0.00089 | +0.00000 | +3.62 | 0.000146 | 0.000313 |
| `wi037|stack|all` | ADOPT | +0.00029 | +0.00000 | +3.50 | 0.000232 | 0.000434 |
| `wi037|stack|up_high` | ADOPT | +0.00028 | +0.00000 | +3.50 | 0.000232 | 0.000434 |
| `wi037|raw|all` | ADOPT | +0.00026 | +0.00000 | +2.35 | 0.00936 | 0.0148 |
| `wi037|raw|up_high` | ADOPT | +0.00028 | +0.00000 | +2.35 | 0.00936 | 0.0148 |
| `wi037|raw|up_normal` | ADOPT | +0.00089 | +0.00000 | +2.35 | 0.00936 | 0.0148 |
| `wi028|raw|all` | ADOPT | +0.00002 | +0.00009 | +2.20 | 0.0138 | 0.0197 |
| `wi028|raw|up_high` | ADOPT | +0.00006 | +0.00010 | +2.20 | 0.0138 | 0.0197 |
| `wi037|stack|up_normal` | ADOPT | +0.00098 | +0.00000 | +1.84 | 0.0329 | 0.0449 |
| `wi028|raw|down_high` | REJECT | +0.00000 | +0.00006 | +1.78 | 0.0372 | 0.0485 |
| `wi028|raw|all` | REJECT | -0.00013 | +0.00001 | -1.23 | 0.891 | 0.947 |
| `wi028|raw|chop_high` | REJECT | -0.00048 | +0.00000 | -1.23 | 0.891 | 0.947 |
| `wi028|raw|down_high` | REJECT | -0.00017 | +0.00000 | -1.23 | 0.891 | 0.947 |
| `wi028|raw|up_high` | REJECT | -0.00006 | +0.00000 | -1.23 | 0.891 | 0.947 |
| `wi028|raw|up_normal` | INCONCLUSIVE | +0.00009 | +0.00002 | -1.23 | 0.891 | 0.947 |
| `wi037|raw|chop_high` | REJECT | -0.00035 | +0.00000 | -1.62 | 0.947 | 0.947 |
| `wi037|raw|down_high` | REJECT | +0.00000 | +0.00000 | -1.62 | 0.947 | 0.947 |

## Closure and deviations

- INERT cells are honest nulls (no feasible operating point in the pre-registered tau grid) and carry no p-value, hence no family membership; the family is every cell that reached a verdict across the four questions, both sources and every conditioning level.
- Per-question verdict sets: {'wi037': ['ADOPT', 'INERT', 'REJECT'], 'wi033': ['ADOPT', 'INERT', 'REJECT'], 'wi030': ['ADOPT', 'INERT', 'REJECT'], 'wi028': ['ADOPT', 'INCONCLUSIVE', 'INERT', 'REJECT']} — nothing is adopted, promoted or closed from a computed verdict alone; no learner refit (the WI-040 pickles score their own OOF block), no shortlist, no deployment, no live trading.

