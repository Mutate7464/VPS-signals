# D-002 / E2 — Fixture vs real-universe diagnostics

- Generated (UTC): 2026-10-23T18:53:09Z
- Sources: `reports/sprint4_model_qa.md` (E2 run, read-only), fixture Gate 4 report from git history,
  `xgb_trainer_USD_20261023_084905.log`, `data/train_meta_USD.json`, `data/oof_USD.parquet`

## Universe (E2 run)

- **508 symbols / 1,240,275 rows**, 2016-01-04 → 2026-09-23, source=`raw_ohlcv`, `min_date`=2016-01-01, quarantined excluded=37
- `oof_USD.parquet`: 1,240,275 rows, 508 symbols, 2016-01-04 → 2026-09-23
- Fixture comparison baseline: 5-ticker test fixture, 1,400 rows (2025-08-28 → 2026-09-23)

## Fixture vs real — governance metrics

| Target | Run | ROC-AUC | BSS | P@K lift | PR-AUC lift | IC t-defl | Gate |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :---: |
| `y_15d_high` | fixture | 0.498 | -0.008 | 0.96 | 0.99 | 0.70 | **FAIL** |
| `y_15d_high` | real (E2) | 0.539 | 0.006 | 1.19 | 1.09 | -1.11 | **FAIL** |
| `y_15d_low` | fixture | 0.489 | -0.064 | 0.96 | 1.03 | 1.10 | **FAIL** |
| `y_15d_low` | real (E2) | 0.537 | 0.004 | 1.11 | 1.08 | 0.85 | **FAIL** |
| `y_20d_up` | fixture | 0.512 | -0.066 | 1.08 | 1.04 | 0.75 | **FAIL** |
| `y_20d_up` | real (E2) | 0.506 | -0.006 | 1.03 | 1.01 | 0.13 | **FAIL** |
| `y_20d_down` | fixture | 0.426 | -0.117 | 0.79 | 0.81 | 0.11 | **FAIL** |
| `y_20d_down` | real (E2) | 0.483 | -0.023 | 1.06 | 0.99 | 0.10 | **FAIL** |

Placebo (CB-05) clear on all targets in both runs (fixture: clear, clear, clear, clear; E2: clear, clear, clear, clear) — the pipeline is not leaking in either configuration.

## Training health (E2 run)

- `y_15d_high` real folds: best_iter min=13, median=123, max=154 (0 fold(s) at -1)
- `y_15d_low` real folds: best_iter min=64, median=132, max=213 (0 fold(s) at -1)
- `y_20d_up` real folds: best_iter min=14, median=303, max=399 (0 fold(s) at -1)
- `y_20d_down` real folds: best_iter min=21, median=39, max=398 (2 fold(s) at -1)
- NO_LEARNING warnings: 2 on placebo folds, 2 on real folds (placebo early-stop is expected on permuted labels)
- 2 real fold(s) early-stopped with best_iter=-1 (2/20 real folds ≤ 25% acceptance); both on `y_20d_down`, the weakest target — consistent with no learnable signal, not a trainer fault
- MI_EXCEEDS_ENTROPY warnings: 0

## SHAP dominance (E2 run)

| Target | Top feature | Share of \|SHAP\| | Flag |
| :--- | :--- | ---: | :---: |
| `y_15d_high` | `yangzhang_100` | 27.3% | ok |
| `y_15d_low` | `bb_width_10_cs_pct` | 20.5% | ok |
| `y_20d_up` | `bb_width_5_cs_pct` | 17.0% | ok |
| `y_20d_down` | `atr_pct_100` | 22.8% | ok |

## ADR decision-matrix row

Verdict: **E2 NULL — H1 NOT CONFIRMED** (0/4 targets pass ≥3/5 gates on the real 508-ticker universe). The fixture was not the cause: with a clean, leak-free, adequately-sized run the model is still ≈ random at 15–20d horizons (ROC-AUC 0.48–0.54). Per the matrix: proceed to **E3** (feature-set ablation / corrected MI), **E4** (metric/target alignment) and **E5** (unpredictability floor); H2/H3/H4 adjudication is theirs.

| ADR row | Applies? | Basis |
| :--- | :--- | :--- |
| E2 passes → H1 (tune) | no | best target has 0/4 governance gates passing |
| E3 → H2 (replace MI/VIF selection) | next | real whitelist is 19 features/target (vs 7 in fixture); MI now sane; still no signal |
| E4 → H3 (target/metric redesign) | next | regime stability and calibration look healthy; identity-signal concern untested on real data |
| E5 → H4 (little signal in OHLCV @ 15–20d) | next | placebo-clean null on 1.24M rows is consistent with H4 |

## Caveats and deviations

- **Survivorship caveat:** watchlists are current constituents; full-universe results may overstate signal (per D-002 Consequences).
- Deviations from plan (all admin-approved): train window `2016-01-01` (not full history), quarantine list honored (37 tickers excluded within window), MI/VIF computed on subsamples with corr-once VIF, placebo seeds = 1, oof acceptance amended to ≥400K rows / ≥500 symbols (2026-10-23 04:29 UTC).
- E2 ran faithful hyper-parameters; no tuning was done (per plan constraint).

