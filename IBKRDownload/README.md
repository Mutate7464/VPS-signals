# IBKR Download Kit (`ib4/`)

Self-contained toolkit for downloading OHLCV data from Interactive Brokers.
Runs on the **M1 MacBook Air** where IB Gateway is locally accessible.

## Design: 3-Source Union Watchlist Builder

`build_watchlist.py` unions tickers from three source types into canonical watchlists:

| Source | Pattern | Provides |
|---|---|---|
| **IBKRtemp.csv** | `IBKRtemp.csv` | Curated TWS watchlist export (`DES,SYMBOL,STK,SMART/EXCHANGE`). Primary ticker universe. |
| **IV_*.csv** | `IV_US_*.csv`, `IV_CD_*.csv` | Implied Volatility screen — Sector, Industry, Sub-group metadata |
| **TC_*.csv** | `TC_US_*.csv`, `TC_CD_*.csv` | TC Quantamental screen — Sector & Industry metadata + **TC Quantamental Rating®** for downstream XGBoost prioritization |

All three sources are **unioned** — new IV/TC file drops automatically expand the watchlist.
The **`tc_rating`** column (0 = no rating) is preserved in watchlists and sector_map for
downstream memory-constrained ticker sorting (highest rating first).

Outputs are written to **both** `config/` (VPS canonical) and `ib4/` (M1 Mac ingest).

## Quickstart

```bash
# 1. Install dependencies
cd ib4
pip install -r requirements.txt

# 2. All-in-one pipeline (build watchlists → download → sync to VPS)
python build_all.py                # full: USD + CAD + HOLDINGS
python build_all.py --dry-run      # preview without connecting
python build_all.py --delta-only   # fast daily delta update
python build_all.py --limit 5      # test with 5 tickers per market

# 3. Or run steps individually:
python build_watchlist.py          # rebuild watchlists from IV/TC sources
python ibkr_ingest.py --market USD --limit 5   # test connectivity
python ibkr_ingest.py --market USD             # full USD download
python ibkr_ingest.py --market CAD             # full CAD download
python ibkr_ingest.py --market HOLDINGS        # holdings download
python sync_back.py                # push data to VPS
```

## Files

| File | Purpose |
|---|---|
| `build_all.py` | **New** — single-command orchestrator: build → download → sync |
| `build_watchlist.py` | Union `IBKRtemp.csv` + `IV_*.csv` + `TC_*.csv` → watchlists (with `tc_rating`) + sector map |
| `ibkr_ingest.py` | Download engine with adaptive pacing, calendar awareness, gap detection, index, source-scanning |
| `sync_back.py` | Rsync data + configs back to VPS via `ssh VPS` |
| `settings.yaml` | Local IBKR connection + pacing config |
| `requirements.txt` | Python dependencies |
| `_reference_01_download.py` | Original reference implementation (not runnable) |

## Source-file auto-discovery (NEW)

`ibkr_ingest.py` now **defaults to scanning** `IV_*/TC_*/IBKRtemp.csv` for tickers
not yet in the watchlist.  Drop a new `IV_US_99.csv` into `ib4/` and the next
`ibkr_ingest.py --market USD` run automatically downloads those tickers.

Disable with `--no-scan-sources`.

## OHLCV Index (NEW)

A metadata index at `data/ohlcv_index.parquet` replaces per-file Parquet scans.
One row per ticker — min/max dates, row counts, currency, exchange.

- **Fresh (<60 min):** loaded directly → O(1) plan building
- **Stale or missing:** rebuilt from disk in one pass → saved for next run
- **After each download:** entry updated in-memory, flushed every `save_every` tickers
- **Integrity check:** cross-validates index vs disk on each run; flags mismatches

## Aggressive Pacing (UPDATED)

The engine now starts **aggressive** and lets IBKR errors define the ceiling:

| Setting | Old | New | Rationale |
|---|---|---|---|
| `requests_per_window` | 30/min | **90/min** | 1.5 req/s — still well below 50 msg/s gateway limit |
| `download_concurrency` | 2 | **6** | 6 parallel HMDS requests |
| `pacing_hit_threshold` | 3 | **6** | Tolerate more hits before global pause |
| `global_pause_sleep` | 90s | **45s** | Faster recovery |
| Discovery concurrency | 4 | **10** | Surge to find real ceiling |
| Discovery rate limiter | 60/min | **150/min** | 2.5 req/s initial burst |

**Surge-and-settle:** start at 10 concurrent + 150 req/min → hit pacing errors →
auto-throttle → learn sustainable rate → cruise at 80%.

## Pacing Event Log (NEW)

All pacing hits, throttles, restores, and global pauses are logged to
`data/pacing_events.jsonl` (one JSON line per event):

```json
{"ts": "2026-10-22T14:31:05", "market": "USD", "event": "pacing_error", "symbol": "AAPL", "error_code": 420, ...}
{"ts": "2026-10-22T14:31:06", "market": "USD", "event": "throttle", "concurrency_before": 6, "concurrency_after": 3, ...}
```

A **Pacing Report** is printed at the end of every run summarizing hits, throughput,
latency, and the learned concurrency/rate profile.

## Proactive Batch Planning (NEW)

Before starting downloads, the engine sums total bars needed. If the workload
exceeds `batch_bars_threshold` (default: 5000), downloads are split with
`batch_cooldown_sec` cooldowns between batches to avoid sustained IBKR throttling.

## `build_all.py` CLI flags

| Flag | Description |
|---|---|
| `--market USD\|CAD\|HOLDINGS\|both` | Markets to process (default: `both` = USD + CAD + HOLDINGS) |
| `--dry-run` | Preview all steps without side effects |
| `--delta-only` | Daily fast mode — skip Bulk/Mid downloads |
| `--skip-sync` | Run build + download but skip VPS rsync |
| `--limit N` | Limit IBKR download to N tickers per market (testing) |
| `--no-scan-sources` | Disable auto-discovery from IV/TC/IBKRtemp files |

## `ibkr_ingest.py` CLI flags

| Flag | Description |
|---|---|
| `--market USD\|CAD\|HOLDINGS` | Which watchlist to process (required) |
| `--dry-run` | Validate CSV without connecting to IBKR |
| `--limit N` | Only download first N tickers |
| `--fixgap` | Re-download full history when calendar gaps are detected |
| `--delta-only` | Skip Bulk/Mid queries; only Delta updates (<15 days) |
| `--client-id N` | IBKR client ID (for parallel runs) |
| `--no-scan-sources` | Disable auto-discovery of new tickers from IV/TC/IBKRtemp files |
| `--config PATH` | Path to settings YAML (default: `settings.yaml`) |

## Reference CSV conventions

Place these files in `ib4/`:

| Pattern | Market | Description |
|---|---|---|
| `IBKRtemp.csv` | Mixed | IBKR TWS watchlist export (`DES,SYMBOL,STK,SMART/EXCHANGE`). Curated master list. |
| `IV_CD_*.csv` | CAD | Implied Volatility screen (`.TO` suffix, Sector/Industry/Sub-group) |
| `IV_US_*.csv` | USD | Implied Volatility screen (US exchanges, Sector/Industry/Sub-group) |
| `TC_CD_*.csv` | CAD | TC Quantamental screen (`Sector & Industry` column, TC Quantamental Rating®) |
| `TC_US_*.csv` | USD | TC Quantamental screen (`Sector & Industry` column, TC Quantamental Rating®) |

## Watchlist Output Columns

| Column | Description |
|---|---|
| `symbol` | Ticker symbol (no suffix) |
| `sec_type` | Always `STK` |
| `exchange` | Always `SMART` (IBKR smart-routing) |
| `primary_exchange` | `NYSE`, `NASDAQ`, `ARCA`, `AMEX`, or `TSE` |
| `currency` | `USD` or `CAD` |
| `tc_rating` | TC Quantamental Rating® (0–100, 0 = no TC rating available). For downstream XGBoost sorting. |

## Pacing Profile

The download engine learns IBKR rate limits between runs. Profiles are stored at
`data/pacing_profile_usd.json` and `data/pacing_profile_cad.json`. These are
synced back to the VPS so the engine remembers the safe concurrency level.

- **First run**: aggressive discovery phase — starts at 10 concurrent, 150 req/min, probes ceiling
- **Subsequent runs**: starts at the learned safe rate (~80% of ceiling)
- **Stale (>7 days)**: re-runs discovery

## Parallel dual-market

```bash
# Two terminals, different client IDs:
python ibkr_ingest.py --market USD --client-id 101 &
python ibkr_ingest.py --market CAD --client-id 102 &
```