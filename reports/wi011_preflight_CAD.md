# WI-011 Step 1 — preflight (CAD inputs, read-only)

- Generated (UTC): 2026-10-26T17:01:37Z
- Feature input: `data/features/features_CAD.parquet`
- Target input: `data/features/targets_CAD.parquet`
- Method: inspect existing parquets only; no feature/target regeneration, no all-ticker uncompressed frame (key columns are read, not the 89-column panel).

## Observed inputs

| Input | Rows | Columns | Symbols | Unique dates | Date range |
| :--- | ---: | ---: | ---: | ---: | :--- |
| features_CAD.parquet | 701,599 | 92 | 315 | 2691 | 2016-01-04T00:00:00.000000000 → 2026-09-22T00:00:00.000000000 |
| targets_CAD.parquet | 701,599 | 8 | 315 | 2691 | 2016-01-04T00:00:00.000000000 → 2026-09-22T00:00:00.000000000 |

FEATURE_ROWS: 701599
TARGET_ROWS: 701599
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
| 2016 | 55,650 | 224 |
| 2017 | 56,789 | 231 |
| 2018 | 58,482 | 234 |
| 2019 | 59,383 | 239 |
| 2020 | 60,434 | 242 |
| 2021 | 62,425 | 267 |
| 2022 | 68,612 | 278 |
| 2023 | 70,366 | 288 |
| 2024 | 74,115 | 302 |
| 2025 | 78,044 | 314 |
| 2026 | 57,299 | 315 |

## Verdict

PASS — inputs present, no duplicate keys, feature/target key sets and key order align; Step 2 may proceed.
- Row counts are reported as observed (not hard-coded) and match exactly.
