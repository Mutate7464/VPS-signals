# WI-017 — Brute-force target/feature confirmation study (USD)

Admin chat direction 2026-10-31. Status: **SPEC CONFIRMED** (definitions resolved
via admin clarify same day) — awaiting go/no-go on this charter before run 1.

## Intent

Brute-force confirmation of current assumptions on USD: sweep ALL fib windows
3–233 for both targets and features, with nothing window-pruned, to test whether
the standing verdicts (WI-016 USD NOT_CLEAR, WI-015 alignment positives, the
WI-009-series "E5 factors are the signal" triple-confirmation) survive a full
grid. Complements prior WIs — no change to shipped pipeline, frozen gate
artifacts untouched.

## Confirmed definitions (admin 2026-10-31)

- **Window grid** (targets AND features): full Fibonacci 3–233 = union of
  pure-fib (3,5,8,13,21,34,55,89,144,233) and the existing 3×fib ladder
  (3,6,9,15,24,39,63,102) → 17 windows, defined in `src/wi017/__init__.py`.
- **Base target semantics:** barriers evaluated over LOOKFORWARD horizons =
  each fib window: "within the next N trading days, did price touch +10% /
  −10% / stay within ±5% of entry", plus peak/bottom (swing extremes) per
  window. Swept across all 17 windows.
- **Run 2 derived targets (on top of base):** velocity (%/day from bottom to
  peak within the window); "triple point" = **technical-analysis pivot: three
  barriers/trendlines intersecting** (not the three-way simultaneous event
  reading, not the third-swing reading).
- **Feature scope:** ALL existing fib-windowed families at the full grid
  (range_pos, range_width, fib_dist, donchian_break, adx, di_spread, atr_pct,
  bb_pct_b, bb_width, obv_zscore, amihud, yangzhang, kama_er, hurst, entropy,
  vwap_zscore, WI-015 families).
- **Isolation:** everything under `src/wi017/`, `reports/wi017/`, this doc
  folder. No data copies, no writes to frozen paths, descriptive only.

## Constraints (carried standing bars by pointer)

n_jobs=2 / float32 / symbol-sequential (AGENTS.md hard constraints, no
all-ticker frame — ~608 USD parquet files read one symbol at a time);
point-in-time trailing features; lookforward targets with horizon-scaled
embargo (WI-016); same-sign skill bar (WI-009b cycle); no order execution,
human gate unchanged.

## Admin amendments (2026-10-31, in-chat)

- **Run 1 is the starting point** and must complete before run 2 / features are
  launched; runs are sequential, not batched.
- **Run 2 target family is triple-barrier in the WI-016 machinery sense**
  (velocity, and the barrier/stay family in general, built on run-1 outputs).
- **Redundancy policy relaxed:** dense grid deliberately OVER-retained — prune
  only highly-correlated columns that are also less useful (correlation AND
  usefulness both gate the cut; no pure |rho| pruning).
- **Edge cases modeled last:** per-target base rates first; sparse/edge-case
  targets go to the back of the queue, not the front.

## Steps (amended)

1. Probe: post-quarantine USD universe, per-symbol row spans, min history vs
   window 233 feasibility; per-target base rates (drives the run queue).
2. Run 1 — base targets (peak/bottom, +10%/−10% barrier touch, ±5% stay band)
   × 17 windows → report. **Gate: run 1 reviewed before anything else runs.**
3. Run 2 — derived triple-barrier/velocity family on top of run-1 outputs →
   report. Edge-case targets last.
4. Features — all families at full grid; redundancy report with relaxed-prune
   recommendations (correlation + usefulness).
5. Alignment matrix target × feature; verdicts vs standing assumptions.
6. Decision memo at gate.

## Open items for the gate

- Triple-point detector specifics (which barriers/trendlines) deferred to
  run-2 spec review after run-1 output.
