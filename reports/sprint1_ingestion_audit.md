# Sprint 1 — Ingestion Audit (Gate 1)

- Generated (UTC): 2026-10-21T02:31:03.799747+00:00
- Base directory: `/home/yycuser/projects/signals`

## 1. Config CSV validation

| File | Rows | Required columns | Duplicate symbols |
| :--- | ---: | :---: | ---: |
| `config/watchlist_300_usd.csv` | 6 | YES | 0 |
| `config/watchlist_300_cad.csv` | 6 | YES | 0 |
| `config/holdings.csv` | 2 | YES | 0 |

## 2. OHLCV Parquet audit

`data/raw_ohlcv/` is empty (pre-sync dry run). Generated a deterministic 300-bar synthetic fixture (5 USD + 5 CAD) under `data/raw_ohlcv_test/`.

- Synthetic fixture written: **10** Parquet files.

### 2.1 Dry-run fixture audit

| Symbol | Market | Rows | Min date | Max date | Status | Reason |
| :--- | :---: | ---: | :---: | :---: | :---: | :--- |
| CNQ | CAD | 300 | 2025-08-28 | 2026-10-21 | OK |  |
| ENB | CAD | 300 | 2025-08-28 | 2026-10-21 | OK |  |
| RY | CAD | 300 | 2025-08-28 | 2026-10-21 | OK |  |
| SHOP | CAD | 300 | 2025-08-28 | 2026-10-21 | OK |  |
| TD | CAD | 300 | 2025-08-28 | 2026-10-21 | OK |  |
| AAPL | USD | 300 | 2025-08-28 | 2026-10-21 | OK |  |
| AMZN | USD | 300 | 2025-08-28 | 2026-10-21 | OK |  |
| JPM | USD | 300 | 2025-08-28 | 2026-10-21 | OK |  |
| MSFT | USD | 300 | 2025-08-28 | 2026-10-21 | OK |  |
| NVDA | USD | 300 | 2025-08-28 | 2026-10-21 | OK |  |

### 2.2 Summary

- Total files audited: **10**
- OK: **10** | Quarantined: **0** | Read errors: **0**
- CB-01 (corporate-action spike) quarantines: **0**
- CB-02 (insufficient lookback) quarantines: **0**

## 3. Sync manifest & freshness

- data/sync_manifest.json not found (expected after M1 Mac rsync).

## 4. Baseline anti-leakage harness (`pytest tests/test_leakage.py`)

- Result: **PASS** (exit code 0, 1.59s)

```
..                                                                       [100%]
2 passed in 0.39s
```

