# G-002 — Ingest reliability & data freshness

**Intention (one line):** daily incremental OHLCV ingestion for all 600+ tickers that is reliable (<5% failure), IBKR-compliant, and boring to operate — because model signal (G-001) is downstream of data quality and coverage.

**Success criteria:**
- Full USD + CAD downloads complete with <5% failure rate and zero unhandled error-162s.
- Daily `--delta-only` refresh completes in minutes, not the full re-pull.
- CAD universe populated (currently absent).

**Non-goals:** throughput maximization at the cost of gateway stability (Phase 2 pacing only after 3 clean full runs).

**Current state:** Phase 1 stability changes implemented 2026-10-22 (`ingest/ib4-changelog.md`); validation runs pending on M1 Mac → WI-003 (blocked on admin). Phase 2 = WI-004, gated.
