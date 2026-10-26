# WI-011 Step 1 — preflight (USD inputs, read-only)

- Generated (UTC): 2026-10-26T17:01:26Z
- Feature input: `data/features/features_USD.parquet`
- Target input: `data/features/targets_USD.parquet`
- Method: inspect existing parquets only; no feature/target regeneration, no all-ticker uncompressed frame (key columns are read, not the 89-column panel).

## Observed inputs

| Input | Rows | Columns | Symbols | Unique dates | Date range |
| :--- | ---: | ---: | ---: | ---: | :--- |
| features_USD.parquet | 1,240,275 | 92 | 508 | 2696 | 2016-01-04T00:00:00.000000000 → 2026-09-23T00:00:00.000000000 |
| targets_USD.parquet | 1,240,275 | 8 | 508 | 2696 | 2016-01-04T00:00:00.000000000 → 2026-09-23T00:00:00.000000000 |

FEATURE_ROWS: 1240275
TARGET_ROWS: 1240275
FEATURE_COLUMNS: 92
TARGET_COLUMNS: 8

Target label columns: `y_15d_high`, `y_15d_low`, `y_20d_up`, `y_20d_down`, `y_20d_stay`

Feature panel is the 89-indicator set defined by WI-002 E3 (63 classical + 26 fib/range); key columns plus identifiers only are read here.

## Key integrity

DUPLICATE_KEYS: 0
- duplicated feature keys: 0
- duplicated target keys: 0
KEY_ALIGNMENT: PASS
- aligned `(date, symbol, market)` coverage: exact key-set match
KEY_ORDER_ALIGNMENT: PASS
- key-order equality matters because the analysis scripts read the feature panel in row order and align the condition-state table positionally (no join).

## Per-year coverage (feature panel)

| Year | Rows | Symbols |
| ---: | ---: | ---: |
| 2016 | 100,969 | 405 |
| 2017 | 103,237 | 418 |
| 2018 | 107,657 | 436 |
| 2019 | 111,549 | 447 |
| 2020 | 113,967 | 460 |
| 2021 | 118,325 | 478 |
| 2022 | 120,360 | 482 |
| 2023 | 120,876 | 486 |
| 2024 | 124,619 | 499 |
| 2025 | 126,260 | 508 |
| 2026 | 92,456 | 508 |

## Verdict

PASS — inputs present, no duplicate keys, feature/target key sets and key order align; Step 2 may proceed.
- Row counts are reported as observed (not hard-coded) and match exactly.
