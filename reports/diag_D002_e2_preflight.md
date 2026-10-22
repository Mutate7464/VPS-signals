# E2 Pre-flight Audit (USD)

Generated: 2026-10-22T22:19:33.311338+00:00

- source: `/home/yycuser/projects/signals/data/raw_ohlcv/market=USD`
- tickers: 509 (quarantined excluded: 37)
- total rows: 2027315  median: 5025  min: 280  max: 5027
- < 125 bars: 0  < 500 bars: 11
- date range: 2006-10-26 → 2026-10-21
- window: read from 2015-04-26 (min_date=2016-01-01 - 250d warmup)
- tickers with labeled rows after window: 509
- projected labeled rows: 1308470
- projected feature-only RAM: 314 MB
- projected full panel RAM: 679 MB
- MemAvailable: 4825 MB / 7941 MB
- budget 4.5 GB: OK

## Quarantine list (USD)

37 tickers excluded from `data/dead_letter_tickers.csv`.
