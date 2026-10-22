# IB4 Changelog

## 2026-10-22 — Phase 1 Optimization Sprint

### `ib4/ibkr_ingest.py`
- **P1:** Added error 162 handler for "Historical Market Data Service" cancellations (was silently dropped, causing 17.5% failure rate)
- **P2:** Reduced discovery phase concurrency from `min(c*2, 8)` → `min(c+2, 5)` and rate limiter from 100/min → 60/min to stay under IBKR gateway 50 msg/sec ceiling
- **P3:** Added retry loop (2 attempts, 30s backoff) for transient failures: empty responses, cancelled queries, exceptions. Permanent permission failures skip retry.
- **P4:** Added 5s HMDS farm warm-up wait after connection to prevent early-query cancellations
- **P5:** Added `--delta-only` CLI flag to skip Bulk/Mid queries for fast daily updates
- Added constants: `MAX_RETRIES=2`, `RETRY_DELAY_SEC=30`, `HMDS_WARMUP_SEC=5`
- Renumbered run() steps 5-13 to accommodate new HMDS warm-up step

### `ib4/settings.yaml`
- `requests_per_window`: 45 → 30
- `download_concurrency`: 3 → 2
- `global_pause_sleep`: 120 → 90
- Added Phase 1 / Phase 2 notation in comments