# SESSION_HANDOVER.md — OpenCode Live Context Ledger

- **Last Updated (UTC):** 2026-10-21 23:40 UTC
- **Active Sprint & Gate Status:** Sprint 1 complete — all `ibkrdownload/` scripts made self-contained. **ibkr_ingest.py NOT run** — must execute on M1 Mac.
- **Latest Synced Market Date:** N/A (ingest not yet run)
- **Peak VPS Memory Observed:** N/A
- **Key Changes This Session:**
  - `opt.csv` renamed → `IBKRtemp.csv` across all code, docs, reports (6 files, 0 refs remaining)
  - `_parse_tc_csv()` rewritten with `csv.reader` — handles embedded commas in TC sector fields
  - `tc_rating` column preserved in watchlist + sector_map (TC Quantamental Rating® 0–100)
  - All 3 scripts made **self-contained**: reference/config files resolved from script's own directory, not hardcoded project layout
  - `build_watchlist.py`: reference CSVs + outputs resolved from `Path(__file__).parent`; auto-creates `config/` via `mkdir(parents=True)`
  - `ibkr_ingest.py`: `load_config()` now reads `settings.yaml` from script's own directory (was `config/settings.yaml` resolved from project root — broken on M1 Mac)
  - `sync_back.py`: already self-contained (no change needed)
  - FutureWarning fixed: benchmark row concat uses `pd.Series(..., index=df_merged.columns)`
  - Dry-run: USD 552 tickers (505 sectors), CAD 359 tickers (344 sectors)
- **M1 Mac Layout:** Copy all `ibkrdownload/` contents into a single folder (e.g. `~/Downloads/IBKR/`) and run scripts directly from there
- **Next Step (on M1 Mac):**
  1. `cd /Users/kamchow/Downloads/IBKR && python build_watchlist.py` — rebuild watchlists (auto-creates `config/`)
  2. `python ibkr_ingest.py --market USD --limit 5` — smoke test
  3. `python ibkr_ingest.py --market USD && python ibkr_ingest.py --market CAD` — full download
  4. `python sync_back.py` — rsync to VPS
- **Active Anomalies / Quarantined Tickers:** None.
