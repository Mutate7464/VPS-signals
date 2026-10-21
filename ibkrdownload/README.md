# IBKR Download Kit (`ibkrdownload/`)

Self-contained toolkit for downloading OHLCV data from Interactive Brokers.
Runs on the **M1 MacBook Air** where IB Gateway is locally accessible.

## Quickstart

```bash
# 1. Install dependencies
cd ibkrdownload
pip install -r requirements.txt

# 2. (Optional) Rebuild watchlists from reference CSV files
python build_watchlist.py

# 3. Test connectivity with 5 tickers
python ibkr_ingest.py --market USD --limit 5

# 4. Full download
python ibkr_ingest.py --market USD
python ibkr_ingest.py --market CAD
python ibkr_ingest.py --market HOLDINGS

# 5. Push data back to the VPS
python sync_back.py --dry-run     # preview
python sync_back.py               # sync for real
```

## Files

| File | Purpose |
|---|---|
| `build_watchlist.py` | Merge `IV_CD_*.csv`, `TC_CD_*.csv`, `opt.csv` → canonical watchlists + sector map |
| `ibkr_ingest.py` | Download engine with adaptive pacing, calendar awareness, gap detection |
| `sync_back.py` | Rsync data + configs back to VPS via `ssh VPS` |
| `settings.yaml` | Local IBKR connection + pacing config |
| `requirements.txt` | Python dependencies |
| `_reference_01_download.py` | Original reference implementation (not runnable) |

## Reference CSV conventions

Place these files in `ibkrdownload/`:

| Pattern | Market | Description |
|---|---|---|
| `IV_CD_*.csv` | CAD | Implied Volatility screen (`.TO` suffix, Sector/Industry/Sub-group) |
| `IV_US_*.csv` | USD | Implied Volatility screen (US exchanges) |
| `TC_CD_*.csv` | CAD | TC Quantamental screen (`Sector & Industry` column) |
| `TC_US_*.csv` | USD | TC Quantamental screen |
| `opt.csv` | Mixed | IBKR API watchlist export (`DES,SYMBOL,STK,SMART/EXCHANGE`) |

## Pacing Profile

The download engine learns IBKR rate limits between runs. Profiles are stored at
`data/pacing_profile_usd.json` and `data/pacing_profile_cad.json`. These are
synced back to the VPS so the engine remembers the safe concurrency level.

- **First run**: discovery phase — probes the rate ceiling by starting fast
- **Subsequent runs**: starts at the learned safe rate (~80% of ceiling)
- **Stale (>7 days)**: re-runs discovery

## Parallel dual-market

```bash
# Two terminals, different client IDs:
python ibkr_ingest.py --market USD --client-id 101 &
python ibkr_ingest.py --market CAD --client-id 102 &
```

## CLI flags

| Flag | Description |
|---|---|
| `--market USD\|CAD\|HOLDINGS` | Which watchlist to process (required) |
| `--dry-run` | Validate CSV without connecting to IBKR |
| `--limit N` | Only download first N tickers |
| `--fixgap` | Re-download full history when calendar gaps are detected |
| `--client-id N` | IBKR client ID (for parallel runs) |