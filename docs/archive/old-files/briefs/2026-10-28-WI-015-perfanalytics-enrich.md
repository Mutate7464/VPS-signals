# Brief — WI-015: performance analytics (enrich features → correlation)

Admin GO 2026-10-28 (in-chat "proceed", after intent clarification: WI-015
**complements** WI-014 — 014 stays shipped; no changes to shortlist CSV/PDF).
Sequence re-anchored: enrich features → establish correlation → trading goals
LATER (G-PA3/PA5 deferred, out of scope).

## Context files (read these, ~only these)

- `docs/tech_approach/perfanalytics/README.md` — charter, ground rules
- `docs/tech_approach/perfanalytics/targets-research.md` — target drafts T1–T4 + open questions + goal ladder
- `docs/tech_approach/perfanalytics/features-research.md` — CONFIRMED fib-window spec (grid 3→233) + alignment method
- `src/targets.py` — point-in-time labeler pattern to follow (trailing thresholds, forward eval window)
- `src/factors/e5_baseline.py` — factor-screener machinery shape for the alignment probe

## Goal

Build the run-target dataset (G-PA2) and the enriched fib-window feature panel
with a per-target alignment matrix (G-PA1) on **CAD first**, both markets in
scope, as RESEARCH artifacts. No model ships; no trading logic changes.

## Confirmed spec (admin, 2026-10-28 — do not re-litigate)

- Feature windows = Fibonacci grid **3, 5, 8, 13, 21, 34, 55, 89, 144, 233**,
  applied to the EXISTING normalized families (rsi, bb_pct_b/bb_width, adx/
  di_spread, atr_pct, obv_zscore, hurst, kama_er, vwap_zscore, amihud,
  yangzhang, range_pos/range_width/donchian).
- Targets T1–T4: T1 run amplitude (max bottom-to-peak in window, close-to-close),
  T2 velocity (amplitude ÷ bottom-to-peak days), T3 up-momentum duration
  (longest consecutive up-close streak), T4 run frequency (P(≥1 qualifying run)).
- Admin-defaulted decisions (carry as assumptions, state in plan): qualifying
  run trigger = trailing-ATR multiple; amplitude = close-to-close (low-high as
  diagnostic column); forward windows k = 15 and 20 (match existing horizons).

## Constraints

- Point-in-time: evaluation strictly over [t+1, t+k]; thresholds trailing-only.
- Host: n_jobs=2, float32 immediately after calc, symbol-sequential iteration,
  no all-ticker uncompressed frames.
- `--market {CAD,USD,BOTH}` parametrized, default BOTH; market-suffixed report
  paths under `reports/perfanalytics/` (new dir, nothing overwrites frozen
  reports).
- Warm-up: check per-symbol history coverage before computing 144/233 windows;
  NaN where insufficient (no partial windows).
- Same-sign skill bar carried from WI-009b for any association verdict.
- New code under `src/perfanalytics/{targets,features,correlation}/`; stubs exist.
- No changes to `scripts/wi014_screener.py`, `src/pdf_compiler_factor.py`, or
  anything in the shipped WI-014 path.

## Acceptance (summary — full detail in plan)

1. Run-target parquet per market (T1–T4 + diagnostics), point-in-time verified
   by test (shift-1 sanity: no future leakage; trailing-threshold test).
2. Enriched feature panel parquet per market: existing families × fib grid,
   float32, schema documented; alignment matrix report `reports/perfanalytics/`
   (one row per target: top family×window by |Spearman IC|, held-out, with
   block-bootstrap noise margin).
3. Tests for labelers + panel builder; targeted suite green; full suite green.
4. STOP at PM verification / admin gate. BOARD.md untouched by Build.

## Out of scope

- G-PA3/G-PA5 trading applications (meta-label filter, shortlist integration,
  any ranking change) — deferred until correlation picture known.
- New model training, composite scores, cost overlays.
- Any edit to shipped WI-014 artifacts.