# Sprint 1 — Ingestion Audit (Gate 1)

- Generated (UTC): 2026-10-21T06:12:00.000000+00:00
- Base directory: `/home/yycuser/projects/signals`

## 1. Config CSV validation

| File | Rows | Required columns | Duplicate symbols |
| :--- | ---: | :---: | ---: |
| `config/watchlist_300_usd.csv` | 97 | YES | 0 |
| `config/watchlist_300_cad.csv` | 214 | YES | 0 |
| `config/holdings.csv` | 2 | YES | 0 |

### 1.1 Watchlist sources

| Market | IBKRtemp.csv | IV_CD_V37.csv | TC_CD_D38.csv | Total unique | Benchmarks |
| :--- | ---: | ---: | ---: | ---: | :--- |
| USD | 95 | — | — | 97 | SPY, QQQ |
| CAD | 41 | 119 | 103 | 214 | XIU, XIC, XDIV |

### 1.2 Exchange distribution (USD)

| Exchange | Count |
| :--- | ---: |
| NASDAQ | 48 |
| NYSE | 48 |
| ARCA | 1 |

### 1.3 Sector coverage

| Market | Total | With sector |
| :--- | ---: | ---: |
| CAD | 214 | 189 |
| USD | 97 | 2 (benchmarks only — awaiting `IV_US_*.csv` / `TC_US_*.csv`) |

## 2. OHLCV Parquet audit

`data/raw_ohlcv/` is empty (pre-sync dry run). A synthetic fixture exists under `data/raw_ohlcv_test/` for pipeline testing.

- Synthetic fixture written: **10** Parquet files (5 USD + 5 CAD, 300 bars each).

### 2.1 Dry-run fixture audit

| Symbol | Market | Rows | Min date | Max date | Status |
| :--- | :---: | ---: | :---: | :---: | :---: |
| CNQ | CAD | 300 | 2025-08-28 | 2026-10-21 | OK |
| ENB | CAD | 300 | 2025-08-28 | 2026-10-21 | OK |
| RY | CAD | 300 | 2025-08-28 | 2026-10-21 | OK |
| SHOP | CAD | 300 | 2025-08-28 | 2026-10-21 | OK |
| TD | CAD | 300 | 2025-08-28 | 2026-10-21 | OK |
| AAPL | USD | 300 | 2025-08-28 | 2026-10-21 | OK |
| AMZN | USD | 300 | 2025-08-28 | 2026-10-21 | OK |
| JPM | USD | 300 | 2025-08-28 | 2026-10-21 | OK |
| MSFT | USD | 300 | 2025-08-28 | 2026-10-21 | OK |
| NVDA | USD | 300 | 2025-08-28 | 2026-10-21 | OK |

### 2.2 Summary

- Total files audited: **10**
- OK: **10** | Quarantined: **0** | Read errors: **0**
- CB-01 (corporate-action spike) quarantines: **0**
- CB-02 (insufficient lookback) quarantines: **0**

## 3. Sync manifest & freshness

- `data/sync_manifest.json` not found (expected after M1 Mac rsync via `sync_back.py`).
- `data/pacing_profile_*.json` not found (created after first live IBKR run on M1 Mac).

## 4. Ingest engine v2 features

| Feature | Status |
| :--- | :---: |
| Adaptive pacing (surge-and-settle) | ✅ |
| Exchange translation map | ✅ |
| Trading calendar (NYSE/TSX) | ✅ (M1 Mac only; needs `pandas_market_calendars`) |
| Download plan: Bulk/Mid/Delta/Skip | ✅ |
| Gap detection + `--fixgap` | ✅ |
| Batch contract qualification | ✅ |
| Permission error flagging | ✅ |
| Incremental progress saves | ✅ |
| Pacing profile learning (EMA) | ✅ |
| Sort by duration (Delta→Mid→Bulk) | ✅ |
| Variable timeouts by query type | ✅ |
| Connection warm-up probe | ✅ |
| Per-market parallelism (`--client-id`) | ✅ |
| `--limit N` for testing | ✅ |

## 5. Baseline anti-leakage harness (`pytest tests/test_leakage.py`)

- Result: **PASS** (exit code 0, 1.59s)

```
..                                                                       [100%]
2 passed in 0.39s
```

## 6. M1 Mac workflow (next step)

```bash
cd ibkrdownload
pip install -r requirements.txt
python build_watchlist.py                      # rebuild if reference files changed
python ibkr_ingest.py --market USD --limit 5   # test connectivity
python ibkr_ingest.py --market USD             # full USD download (97 tickers)
python ibkr_ingest.py --market CAD             # full CAD download (214 tickers)
python sync_back.py                            # push data → VPS
```

## 7. Sector map

Sector/industry data exported to `config/sector_map.csv` (311 rows) for use by `pdf_compiler.py` in Sprint 5. Columns: `symbol, market, sector, industry, sub_group, company_name`. 189/214 CAD tickers have sector populated.