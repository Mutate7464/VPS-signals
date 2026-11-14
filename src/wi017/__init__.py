"""WI-017: Brute-force target/feature confirmation study (USD only).

Admin chat direction 2026-10-31. Isolation ground rules for this package:

- USD market only. Read-only on `data/raw_ohlcv/market=USD/` — no data copies.
- Everything lands under `reports/wi017/` and `docs/tech_approach/wi017-brute-force-usd/`;
  frozen gate artifacts of prior WIs are never written or regenerated.
- Hard constraints (AGENTS.md): n_jobs=2, float32 immediately after calc,
  symbol-sequential iteration (no all-ticker uncompressed DataFrame).
- Point-in-time only: trailing windows for features; lookforward horizons for
  targets with horizon-scaled embargo (carried from WI-016).
- Descriptive research only: no order-execution path, human gate unchanged.
- Window grid: full Fibonacci 3-233 (union of pure-fib 3,5,8,...,233 and the
  existing 3x-fib ladder 3,6,9,...,102), confirmed by admin 2026-10-31.
"""

WI017_WINDOWS = (3, 5, 6, 8, 9, 13, 15, 21, 24, 34, 39, 55, 63, 89, 102, 144, 233)
MARKET = "USD"
