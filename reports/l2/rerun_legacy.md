# WI-043 — legacy L2 rerun under the D-024 harness (Layer 2)

- 2026-11-10T16:47:24Z · BH-FDR family `wi043_legacy_l2_rerun` (5 tested cells, alpha 0.05) — three questions, never pooled with WI-042's family; counts {'INERT': 37, 'REJECT': 5} · runtime 17.2s
- Harness `src/l2_overlay/harness.py` (WI-041): INERT precheck on CALIB, tau from CALIB edge only, one-shot EVAL, 5-seed placebo. **PROVISIONAL** until the admin ratifies the verdicts (WORKFLOW); a REJECT closes that question under D-024 §2
- Ports: wi012 = tau tuned on the USD CALIB edge, then judged on CAD edges only; wi018 = USD-only (D-018 Q2) and pays one extra 25 bps round trip on every event it takes; wi011 = that cost plus the WI-011 trigger envelope (100-400 firings/yr on CALIB) as an INERT gate
- Inputs: `manifest.parquet` (67 `xgboost`/`b_hold`/`exact_full_k0.8` fold pickles) -> fold-consistent OOF at the frozen at-bottom entries; horizons [5, 8, 13, 21, 34, 55, 89]; baseline = frozen fib-rule return (25 bps inside `r_frozen`)

## USD — 32,100 at-bottom entries, 40 design columns, horizons [5, 8, 13, 34, 55, 89] (partial [89])

### wi018 — first-touch h34 cost overlay vs the frozen baseline

`wi018_frozen_fib_w28entry_w30exit_t15_s10_d39_close`; score `1 - p(b_hold h34)`; sources raw/stack; judge market USD

| cell | verdict | tau | CALIB edge | EVAL edge | folds | placebo z | p | q | n_calib | n_eval | note |
| :--- | :---: | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| `wi018|raw|all` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 10,268 | 20,616 | INERT: mass min 0.9997 at/above tau range [0.10, 0.70] |
| `wi018|raw|chop_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,298 | 3,568 | INERT: mass min 0.9997 at/above tau range [0.10, 0.70] |
| `wi018|raw|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 32 | 613 | INERT: CALIB events 32 < floor 200 |
| `wi018|raw|down_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,744 | 2,972 | INERT: mass min 0.9997 at/above tau range [0.10, 0.70] |
| `wi018|raw|up_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 4,059 | 8,331 | INERT: mass min 0.9997 at/above tau range [0.10, 0.70] |
| `wi018|raw|up_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,135 | 5,050 | INERT: mass min 0.9997 at/above tau range [0.10, 0.70] |
| `wi018|stack|all` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 10,268 | 20,616 | INERT: mass min 0.7085 at/above tau range [0.10, 0.70] |
| `wi018|stack|chop_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,298 | 3,568 | INERT: mass min 0.9827 at/above tau range [0.10, 0.70] |
| `wi018|stack|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 32 | 613 | INERT: CALIB events 32 < floor 200 |
| `wi018|stack|down_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,744 | 2,972 | INERT: mass min 0.7790 at/above tau range [0.10, 0.70] |
| `wi018|stack|up_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 4,059 | 8,331 | INERT: mass min 0.7085 at/above tau range [0.10, 0.70] |
| `wi018|stack|up_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,135 | 5,050 | INERT: mass min 0.9763 at/above tau range [0.10, 0.70] |
| `wi011|raw|all` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 10,268 | 20,616 | INERT: mass min 0.8759 at/above tau range [0.10, 0.70] |
| `wi011|raw|chop_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,298 | 3,568 | INERT: mass min 0.9429 at/above tau range [0.10, 0.70] |
| `wi011|raw|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 32 | 613 | INERT: CALIB events 32 < floor 200 |
| `wi011|raw|down_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,744 | 2,972 | INERT: mass min 0.9094 at/above tau range [0.10, 0.70] |
| `wi011|raw|up_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 4,059 | 8,331 | INERT: mass min 0.8759 at/above tau range [0.10, 0.70] |
| `wi011|raw|up_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,135 | 5,050 | INERT: mass min 0.9590 at/above tau range [0.10, 0.70] |
| `wi011|stack|all` | **INERT** | 0.10 | n/a | n/a | — | n/a | n/a | n/a | 10,268 | 20,616 | INERT: cadence 4,596 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|stack|chop_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,298 | 3,568 | INERT: mass min 0.9571 at/above tau range [0.10, 0.70] |
| `wi011|stack|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 32 | 613 | INERT: CALIB events 32 < floor 200 |
| `wi011|stack|down_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,744 | 2,972 | INERT: mass min 0.7642 at/above tau range [0.10, 0.70] |
| `wi011|stack|up_high` | **INERT** | 0.10 | n/a | n/a | — | n/a | n/a | n/a | 4,059 | 8,331 | INERT: cadence 3,602 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|stack|up_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,135 | 5,050 | INERT: mass min 0.8922 at/above tau range [0.10, 0.70] |

### wi011 — condition-first overlay on the modern event base

`wi011_frozen_fib_w28entry_w30exit_t15_s10_d39_close`; score `1 - p(b_hold h13)`; sources raw/stack; judge market USD

| cell | verdict | tau | CALIB edge | EVAL edge | folds | placebo z | p | q | n_calib | n_eval | note |
| :--- | :---: | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| `wi018|raw|all` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 10,268 | 20,616 | INERT: mass min 0.9997 at/above tau range [0.10, 0.70] |
| `wi018|raw|chop_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,298 | 3,568 | INERT: mass min 0.9997 at/above tau range [0.10, 0.70] |
| `wi018|raw|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 32 | 613 | INERT: CALIB events 32 < floor 200 |
| `wi018|raw|down_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,744 | 2,972 | INERT: mass min 0.9997 at/above tau range [0.10, 0.70] |
| `wi018|raw|up_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 4,059 | 8,331 | INERT: mass min 0.9997 at/above tau range [0.10, 0.70] |
| `wi018|raw|up_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,135 | 5,050 | INERT: mass min 0.9997 at/above tau range [0.10, 0.70] |
| `wi018|stack|all` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 10,268 | 20,616 | INERT: mass min 0.7085 at/above tau range [0.10, 0.70] |
| `wi018|stack|chop_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,298 | 3,568 | INERT: mass min 0.9827 at/above tau range [0.10, 0.70] |
| `wi018|stack|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 32 | 613 | INERT: CALIB events 32 < floor 200 |
| `wi018|stack|down_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,744 | 2,972 | INERT: mass min 0.7790 at/above tau range [0.10, 0.70] |
| `wi018|stack|up_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 4,059 | 8,331 | INERT: mass min 0.7085 at/above tau range [0.10, 0.70] |
| `wi018|stack|up_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,135 | 5,050 | INERT: mass min 0.9763 at/above tau range [0.10, 0.70] |
| `wi011|raw|all` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 10,268 | 20,616 | INERT: mass min 0.8759 at/above tau range [0.10, 0.70] |
| `wi011|raw|chop_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,298 | 3,568 | INERT: mass min 0.9429 at/above tau range [0.10, 0.70] |
| `wi011|raw|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 32 | 613 | INERT: CALIB events 32 < floor 200 |
| `wi011|raw|down_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,744 | 2,972 | INERT: mass min 0.9094 at/above tau range [0.10, 0.70] |
| `wi011|raw|up_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 4,059 | 8,331 | INERT: mass min 0.8759 at/above tau range [0.10, 0.70] |
| `wi011|raw|up_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,135 | 5,050 | INERT: mass min 0.9590 at/above tau range [0.10, 0.70] |
| `wi011|stack|all` | **INERT** | 0.10 | n/a | n/a | — | n/a | n/a | n/a | 10,268 | 20,616 | INERT: cadence 4,596 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|stack|chop_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 1,298 | 3,568 | INERT: mass min 0.9571 at/above tau range [0.10, 0.70] |
| `wi011|stack|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 32 | 613 | INERT: CALIB events 32 < floor 200 |
| `wi011|stack|down_high` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,744 | 2,972 | INERT: mass min 0.7642 at/above tau range [0.10, 0.70] |
| `wi011|stack|up_high` | **INERT** | 0.10 | n/a | n/a | — | n/a | n/a | n/a | 4,059 | 8,331 | INERT: cadence 3,602 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|stack|up_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 2,135 | 5,050 | INERT: mass min 0.8922 at/above tau range [0.10, 0.70] |

## CAD — 17,256 at-bottom entries, 38 design columns, horizons [5, 8, 13, 21, 34, 55, 89] (partial none)

### wi012 — cross-market transfer gate (USD-tuned decision, judged on CAD)

`wi012_frozen_fib_w28entry_w30exit_t15_s10_d39_close`; score `1 - p(b_hold h5)`; sources raw; judge market CAD (tau tuned on USD)

| cell | verdict | tau | CALIB edge | EVAL edge | folds | placebo z | p | q | n_calib | n_eval | note |
| :--- | :---: | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| `wi012|raw|all` | **REJECT** | 0.50 | -0.00456 | +0.00001 | 0:-0.0092, 1:+0.0005, 2:+0.0000, 3:+0.0000, 4:+0.0000 | -54.42 | 1 | 1 | 5,315 | 11,237 | — |
| `wi012|raw|chop_high` | **REJECT** | 0.50 | -0.00048 | +0.00000 | 0:-0.0009, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | -54.42 | 1 | 1 | 1,076 | 1,013 | — |
| `wi012|raw|chop_normal` | **INERT** | 0.50 | n/a | n/a | — | n/a | n/a | n/a | 20 | 505 | INERT: CALIB events 20 < floor 200 |
| `wi012|raw|down_high` | **REJECT** | 0.50 | -0.00228 | +0.00000 | 0:-0.0044, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | -54.42 | 1 | 1 | 1,131 | 1,309 | — |
| `wi012|raw|up_high` | **REJECT** | 0.50 | -0.01030 | +0.00000 | 0:-0.0141, 1:+0.0009, 2:+0.0000, 3:+0.0000, 4:+0.0000 | -54.42 | 1 | 1 | 1,786 | 2,537 | — |
| `wi012|raw|up_normal` | **REJECT** | 0.50 | -0.00206 | +0.00002 | 0:-0.0090, 1:+0.0015, 2:+0.0000, 3:+0.0000, 4:+0.0000 | -54.42 | 1 | 1 | 1,302 | 5,835 | — |
| `wi011|raw|all` | **INERT** | 0.50 | n/a | n/a | — | n/a | n/a | n/a | 5,315 | 11,237 | INERT: cadence 2,405 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|raw|chop_high` | **INERT** | 0.10 | n/a | n/a | — | n/a | n/a | n/a | 1,076 | 1,013 | INERT: cadence 2,680 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|raw|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 20 | 505 | INERT: CALIB events 20 < floor 200 |
| `wi011|raw|down_high` | **INERT** | 0.10 | n/a | n/a | — | n/a | n/a | n/a | 1,131 | 1,309 | INERT: cadence 2,822 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|raw|up_high` | **INERT** | 0.50 | n/a | n/a | — | n/a | n/a | n/a | 1,786 | 2,537 | INERT: cadence 2,007 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|raw|up_normal` | **INERT** | 0.50 | n/a | n/a | — | n/a | n/a | n/a | 1,302 | 5,835 | INERT: cadence 2,555 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|stack|all` | **INERT** | 0.20 | n/a | n/a | — | n/a | n/a | n/a | 5,315 | 11,237 | INERT: cadence 2,406 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|stack|chop_high` | **INERT** | 0.10 | n/a | n/a | — | n/a | n/a | n/a | 1,076 | 1,013 | INERT: cadence 2,685 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|stack|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 20 | 505 | INERT: CALIB events 20 < floor 200 |
| `wi011|stack|down_high` | **INERT** | 0.10 | n/a | n/a | — | n/a | n/a | n/a | 1,131 | 1,309 | INERT: cadence 2,822 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|stack|up_high` | **INERT** | 0.20 | n/a | n/a | — | n/a | n/a | n/a | 1,786 | 2,537 | INERT: cadence 2,007 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|stack|up_normal` | **INERT** | 0.50 | n/a | n/a | — | n/a | n/a | n/a | 1,302 | 5,835 | INERT: cadence 2,553 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |

### wi011 — condition-first overlay on the modern event base

`wi011_frozen_fib_w28entry_w30exit_t15_s10_d39_close`; score `1 - p(b_hold h13)`; sources raw/stack; judge market CAD

| cell | verdict | tau | CALIB edge | EVAL edge | folds | placebo z | p | q | n_calib | n_eval | note |
| :--- | :---: | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| `wi012|raw|all` | **REJECT** | 0.50 | -0.00456 | +0.00001 | 0:-0.0092, 1:+0.0005, 2:+0.0000, 3:+0.0000, 4:+0.0000 | -54.42 | 1 | 1 | 5,315 | 11,237 | — |
| `wi012|raw|chop_high` | **REJECT** | 0.50 | -0.00048 | +0.00000 | 0:-0.0009, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | -54.42 | 1 | 1 | 1,076 | 1,013 | — |
| `wi012|raw|chop_normal` | **INERT** | 0.50 | n/a | n/a | — | n/a | n/a | n/a | 20 | 505 | INERT: CALIB events 20 < floor 200 |
| `wi012|raw|down_high` | **REJECT** | 0.50 | -0.00228 | +0.00000 | 0:-0.0044, 1:+0.0000, 2:+0.0000, 3:+0.0000, 4:+0.0000 | -54.42 | 1 | 1 | 1,131 | 1,309 | — |
| `wi012|raw|up_high` | **REJECT** | 0.50 | -0.01030 | +0.00000 | 0:-0.0141, 1:+0.0009, 2:+0.0000, 3:+0.0000, 4:+0.0000 | -54.42 | 1 | 1 | 1,786 | 2,537 | — |
| `wi012|raw|up_normal` | **REJECT** | 0.50 | -0.00206 | +0.00002 | 0:-0.0090, 1:+0.0015, 2:+0.0000, 3:+0.0000, 4:+0.0000 | -54.42 | 1 | 1 | 1,302 | 5,835 | — |
| `wi011|raw|all` | **INERT** | 0.50 | n/a | n/a | — | n/a | n/a | n/a | 5,315 | 11,237 | INERT: cadence 2,405 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|raw|chop_high` | **INERT** | 0.10 | n/a | n/a | — | n/a | n/a | n/a | 1,076 | 1,013 | INERT: cadence 2,680 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|raw|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 20 | 505 | INERT: CALIB events 20 < floor 200 |
| `wi011|raw|down_high` | **INERT** | 0.10 | n/a | n/a | — | n/a | n/a | n/a | 1,131 | 1,309 | INERT: cadence 2,822 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|raw|up_high` | **INERT** | 0.50 | n/a | n/a | — | n/a | n/a | n/a | 1,786 | 2,537 | INERT: cadence 2,007 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|raw|up_normal` | **INERT** | 0.50 | n/a | n/a | — | n/a | n/a | n/a | 1,302 | 5,835 | INERT: cadence 2,555 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|stack|all` | **INERT** | 0.20 | n/a | n/a | — | n/a | n/a | n/a | 5,315 | 11,237 | INERT: cadence 2,406 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|stack|chop_high` | **INERT** | 0.10 | n/a | n/a | — | n/a | n/a | n/a | 1,076 | 1,013 | INERT: cadence 2,685 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|stack|chop_normal` | **INERT** | n/a | n/a | n/a | — | n/a | n/a | n/a | 20 | 505 | INERT: CALIB events 20 < floor 200 |
| `wi011|stack|down_high` | **INERT** | 0.10 | n/a | n/a | — | n/a | n/a | n/a | 1,131 | 1,309 | INERT: cadence 2,822 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|stack|up_high` | **INERT** | 0.20 | n/a | n/a | — | n/a | n/a | n/a | 1,786 | 2,537 | INERT: cadence 2,007 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |
| `wi011|stack|up_normal` | **INERT** | 0.50 | n/a | n/a | — | n/a | n/a | n/a | 1,302 | 5,835 | INERT: cadence 2,553 firings/yr outside the WI-011 envelope 100-400 — a market state, not a trigger |

## BH-FDR family (every tested cell)

| cell | verdict | CALIB edge | EVAL edge | placebo z | p | q |
| :--- | :---: | ---: | ---: | ---: | ---: | ---: |
| `wi012|raw|all` | REJECT | -0.0046 | 0.0000 | -54.42 | 1 | 1 |
| `wi012|raw|chop_high` | REJECT | -0.0005 | 0.0000 | -54.42 | 1 | 1 |
| `wi012|raw|down_high` | REJECT | -0.0023 | 0.0000 | -54.42 | 1 | 1 |
| `wi012|raw|up_high` | REJECT | -0.0103 | 0.0000 | -54.42 | 1 | 1 |
| `wi012|raw|up_normal` | REJECT | -0.0021 | 0.0000 | -54.42 | 1 | 1 |

## Closure and deviations

- INERT cells are honest nulls (no feasible operating point, or a cadence outside the WI-011 envelope) and carry no p-value, hence no family membership; the family is every cell that reached a verdict across the three questions.
- Declared port choice: wi012's decision bar is h5 (the entry-gate horizon; the only USD library horizon whose mass spans the tau grid), fixed on CALIB feasibility before the CAD EVAL read; wi018 keeps its own h34 first-touch horizon and wi011 its 5-15d h13 bar, whose INERT outcomes are recorded, not skipped.
- Deviations from WI-042's shape: per-question judge markets (wi012 CAD-only, wi018 USD-only per D-018 Q2, wi011 both markets), wi012 carries no stack source (a stack is market-local and cannot be transferred), and the wi018/wi011 edges are net of one extra 25 bps round trip while the placebo z stays gross (a constant shift cannot move a permutation null; the tau argmax is invariant to it).
- Per-question verdict sets: {'wi012': ['INERT', 'REJECT'], 'wi018': ['INERT'], 'wi011': ['INERT']} — nothing is adopted, promoted or closed from a computed verdict alone; no learner refit (the WI-040 pickles score their own OOF block), no shortlist, no deployment, no live trading.

