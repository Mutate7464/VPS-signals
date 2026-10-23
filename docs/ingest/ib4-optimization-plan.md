# IB4 Workflow Optimization Plan

**Date:** 2026-10-22
**Status:** Phase 1 implemented — awaiting validation runs

## User Directive
- Implement all 5 optimization priorities (Phase 1 — conservative pacing)
- Return to more aggressive Phase 2 targets only after error rates are proven stable
- Save plans/working files in `./signals/doc/` for easy access

---

## Phase 1: Stability & Error Reduction (IMPLEMENTED 2026-10-22)

### P1 — Add Missing Error 162 Handler ✅
**File:** `ib4/ibkr_ingest.py` — `_on_ib_error()`

Error code 162 "Historical Market Data Service error message:API historical data query cancelled"
was unhandled — 96 errors fell through silently per run. Added handler that flags as `transient_fail`
so retry logic can act on it.

### P2 — Reduce Discovery Phase Aggression ✅
**Files:** `ib4/ibkr_ingest.py` + `ib4/settings.yaml`

Gateway was hitting 44/50 msg/sec warning. Backed off:

| Setting | Before | After (Phase 1) |
|---|---|---|
| Discovery concurrency | `min(c*2, 8)` | `min(c+2, 5)` |
| Discovery rate limiter | `100/min` | `60/min` |
| `download_concurrency` | `3` | `2` |
| `requests_per_window` | `45` | `30` |
| `global_pause_sleep` | `120s` | `90s` |

### P3 — Add Retry Logic for Transient Failures ✅
**File:** `ib4/ibkr_ingest.py` — `_download_ticker()`

- Max 2 retries with 30s backoff for:
  - Empty responses (no bars returned)
  - Transient 162 errors (query cancelled by IBKR)
  - General exceptions
- Permanent permission failures (162 "no market data permissions") skip retry
- Constants: `MAX_RETRIES = 2`, `RETRY_DELAY_SEC = 30.0`

### P4 — HMDS Farm Health Check ✅
**File:** `ib4/ibkr_ingest.py` — `run()`, step 5

- 5-second wait after IBKR connection to allow HMDS farm to transition from inactive → OK
- Prevents early queries from being cancelled due to inactive historical data farm
- Constant: `HMDS_WARMUP_SEC = 5.0`

### P5 — Delta-Only Mode ✅
**File:** `ib4/ibkr_ingest.py` — new `--delta-only` CLI flag

- Skips Bulk (20Y) and Mid (month-scale) queries
- Only downloads Delta ticks (<15 days missing)
- Reduces daily re-run from ~550 to ~10-20 tickers
- Usage: `python ibkr_ingest.py --market USD --delta-only`

---

## Phase 2: Return to Aggressive Targets (PLANNED)

**Gate:** Run at least 3 full USD+CAD downloads with Phase 1 changes.
**Success criteria:** Failure rate <5%, zero "approaching max rate" warnings, no unhandled 162 errors.

Target settings to restore:

| Setting | Phase 1 (Now) | Phase 2 (Target) |
|---|---|---|
| Discovery concurrency | `min(c+2, 5)` | `min(c*2, 8)` |
| Discovery rate limiter | `60/min` | `90/min` |
| `download_concurrency` | `2` | `3` |
| `requests_per_window` | `30` | `45` |

---

## Baseline Metrics (Pre-Optimization)

| Metric | Value |
|---|---|
| USD parquet files | 454 |
| Total data size | 74 MB |
| Success rate | 82.5% (454/550) |
| Failed rate | 17.5% (96/550) |
| Gateway 162 cancellations | 96 |
| Gateway msg/sec warning | Yes (44/50) |
| CAD data | Not yet downloaded |

## Post-Implementation Validation Checklist

- [ ] Run `python ibkr_ingest.py --market USD --limit 20` — verify no unhandled 162 errors
- [ ] Run `python ibkr_ingest.py --market USD` — full USD run
- [ ] Run `python ibkr_ingest.py --market CAD` — full CAD run
- [ ] Run `python ibkr_ingest.py --market USD --delta-only` — fast daily update
- [ ] Check failure rate in `data/audit_ingestion_*.csv`
- [ ] Check gateway log for msg/sec warnings
- [ ] Verify retry messages in console log