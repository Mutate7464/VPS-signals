# Run-target taxonomy — research & brainstorm (WI-015)

Status: RESEARCH (brainstorm). Nothing below is implemented yet; definitions
are proposals for the next plan step. Data source: `data/raw_ohlcv/` (per-symbol
OHLCV, CAD ~350 + USD ~546 tickers). Existing labels (`data/features/targets_*.parquet`,
5 binary/three-class regime cols) stay untouched — new continuous targets get
their own dataset under a `perfanalytics` prefix.

## Core targets (admin-named, 2026-10-28)

For each, evaluation strictly over forward window [t+1, t+k] (k = 15 and 20
to match existing horizons); thresholds use trailing (≤ t) data only.

| # | Target | Definition (draft) | Unit | Frequency/intensity reading |
|---|---|---|---|---|
| T1 | Run amplitude | Max bottom-to-peak run in window: `max(high[t+1..t+k]) / close[t] − 1`, where "bottom" = min low in window preceding that peak | % return | Intensity |
| T2 | Run velocity | Amplitude ÷ days from bottom to peak (annualized or %/day) | %/day | Intensity per unit time |
| T3 | Upward momentum duration | Longest consecutive-up-close streak in window (or count of up days ÷ k) | days / share | Duration |
| T4 | Run frequency | P(≥1 qualifying run in window): fraction of windows containing a run ≥ trailing-ATR multiple | binary → rate | Frequency |

Intensity targets T1/T2 need a "run" trigger definition — brainstorm below.

## Brainstorm — additional tradable targets

Ranked by fit to the frequency×intensity framing and tradability (asymmetric
upside focus):

1. **Time-to-peak / time-to-bottom** — days until window max (min). Downside
   twin of T3; tradable as "how quickly can I exit at size."
2. **Drawdown-to-recovery (D2R) path stats** — from last trough, days to recover
   prior peak + trough depth in ATR units. Direct "bottom to peak" formalization.
3. **Path efficiency (fractal dimension of the run)** — net displacement ÷
   path length over window (Kaufman ER exists at `kama_er_*` windows already —
   reuse). High ER + positive drift = clean tradable run.
4. **Run persistence / hazard** — conditional: given a run has started (2
   consecutive up days ≥ threshold), P(it continues m more days). Convertible to
   a trailing entry signal, more tradable than unconditional labels.
5. **Peak sharpness (exhaustion)** — peak day's return ÷ run amplitude; high
   sharpness = fade candidate, overlaps existing `y_15d_high` intent but continuous.
6. **Weekly run distribution stats** — median/90th percentile of daily returns
   in window (skew of the up-days), robust to single outlier day.
7. **Run quality vs. breadth** — run amplitude conditional on range_pos/donchian
   state (does the breakout precede the run?) — bridges to feature side.
8. **Fib-retracement-respect score** — does the run retrace <38.2% before
   extending? (Feature-flavored; park under features if it needs past-window data.)

Down-side symmetry (bottom-to-peak implies peak-to-bottom): keep short-list
upside-only for MVP per admin framing ("bottom to peak"); add downside twins
only if the daily shortlist needs exit/avoid signals.

## Open questions for the admin / next gate

- Qualifying-run trigger: fixed % vs trailing-ATR multiple (recommend ATR —
  matches existing label style, self-normalizing cross-ticker)?
- Windows: reuse k=15/20 (comparable to existing labels) or add longer k=60
  for "momentum duration" to breathe?
- Amplitude measured close-to-close or low-to-high (wick-inclusive)?
  Recommend close-to-close (tradable), record low-high as diagnostic.
- Does any T1–T4 combo become the daily-shortlist ranking key (replacing
  expected-return style score in WI-014)? Not decided — this is a research item,
  not a shipping change.