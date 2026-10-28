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
- Amplitude measured close-to-close or low-to-high (wick-inclusive)?
  Recommend close-to-close (tradable), record low-high as diagnostic.
- Downside twins (peak-to-bottom) in MVP scope, or upside-only?

## Researched target families (2026-10-28, admin direction "additional tradable targets")

Grounding: López de Prado *AFML* ch.3 (triple-barrier + meta-labeling);
trend-scanning labeling (horizon-free t-stat argmax); smoothed-trend LTDC
(SVM on MA-smoothed trend direction — PLOS ONE 2022); spectral trend-following
theory (arXiv 2607.19497 — TF alpha = positive low-frequency spectral mass).

| Family | Mechanism | Fit here |
|---|---|---|
| **Triple-barrier** | First-touch of profit-take / stop-loss / max-hold, barriers in trailing-vol multiples | **Highest** — path-aware, mirrors position management, fixes the "band labels at fixed k" weakness WI-009c hit |
| **Meta-labeling** | Primary decides side (E5 factor screener already does), secondary model predicts P(bet profitable) → filter/size | Direct upgrade path for the WI-014 shortlist: predicts whether a ranked ticker's run pays |
| **Trend-scanning** | Per-event horizon = argmax |t-stat| of forward regression over a horizon grid | Converts T3 duration from fixed-k to event-adaptive; aligns with fib-window spirit |
| **Smoothed-trend (LTDC)** | Classify MA-smoothed trend direction, not raw daily direction | Directly addresses labels bottleneck: raw-direction was noise (WI-002); smoothing raises SNR |
| **Run hazard** (brainstorm #4) | P(run continues \| started) — survival framing | Conditional targets have richer base rates than unconditional labels; tradable as entry timing |
| **Spectral/autocorr targets** | Predict sign of vol-normalized return autocorrelation at window w | Theory-backed (TF profitability ⇔ positive spectral mass); overlaps Hurst features |

## Achievable goals — proposal (help set targets for ML, 2026-10-28)

Evidence base for what is achievable on THIS universe (not generic advice):

- Confirmed 4×: E5 factors themselves carry the only surviving signal
  (mom +0.0209 t+6.00 cross-market); **binary/three-class regime labels are the
  bottleneck** — model capacity and 89-feature spend added nothing.
- WI-011: no condition survived costs → NO_TRADE default stands.
- Implication: goals should **stop chasing direction-classification accuracy**
  and move to (a) ranking quality on the factor baseline, (b) bet-filtering
  precision (meta-labeling), (c) descriptive run analytics for humans.

Proposed goal ladder (each gate measurable, probe-first before any build):

| Goal | Metric bar | Achievability rationale |
|---|---|---|
| **G-PA1** Rank alignment: does any family×window feature add to E5 factor ranking IC, held-out, same-sign | Δ Spearman IC > noise margin (block bootstrap), both markets | Cheap probe first (~1 run); 4× negative precedent → expect null; falsifies quickly |
| **G-PA2** Run-descriptive analytics ship: T1–T4 + persistence baseline rendered per market (report, not model) | Coverage ≥ both markets, point-in-time verified, suite green | Near-certain achievable — pure computation, no learning risk |
| **G-PA3** Meta-label filter on WI-014 shortlist: P(top-10 entry pays) model beats "always act" precision, held-out, same-sign | Precision lift > cost hurdle from WI-011 params | Uncertain but the RIGHT uncertain bet — filters weak signals rather than inventing direction |
| **G-PA4** Event-adaptive horizon (trend-scanning style targets) beats fixed-k labels on persistence | Held-out IC vs T1@fixed-k | Second-order; only if G-PA1/PA3 show any life |

Order: **G-PA2 first** (guaranteed win, builds the target dataset the rest
consume), then G-PA1 probe (cheap falsification), then G-PA3 (the real ML bet).
G-PA4 conditional. No goal proposes auto-execution; all outputs remain
research-shortlist inputs with the human gate.