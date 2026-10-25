# 2026-10-25 — WI-011 (proposed) — Condition-first meta-analysis: tradeable conditions → trading decisions

> Status: PROPOSED (post-WI-009c pivot, admin brainstorm 2026-10-25). Planner
> pass + admin approval required before Build. No ML in this item.

## Product goal this item serves (admin, 2026-10-25)

Decision-support screener. Usage spec (admin clarification 2026-10-25): **~200
trades/year ≈ one action (buy OR sell) per trading day on average — a
PREFERENCE qualifying intended use, not a hard cap.** The screener's output is
consumed daily: each day it should surface roughly one action candidate
(200/252 ≈ 0.8/day), drawn from a ranked shortlist. Derived concurrency
envelope (for sizing, preference-scaled):

| Avg hold | Concurrent positions |
|---|---|
| 5d | ~4 |
| 10d | ~8 |
| 15d | ~12 |

Filter on conditions: a "tradeable condition" must fire often enough to fill
~200 actions/yr across the ~315-name universe and few enough that the daily
shortlist stays consumable (a screen surfacing 50 names/day is not a
1-action/day screen). Frequency is part of the acceptance bar.

## Why this and not another model (from WI-009x findings)

- Elements DO carry signal (E5 factor t-stats 6–11) — CONFIRMED.
- Signal is condition-dependent: `vol_20` flips sign full-history → recent
  (−0.045 → +0.127). Any mapping learned from history inherits the regime.
  Nothing was ever conditioned.
- Binary labels (5 defs) unlearnable ×3 methods; continuous 5-factor forecast =
  noise. Label-first branch closed (WI-009c gate A).
- Untested branches: horizon sweep (all runs were 15–20d) and time-series
  momentum (all runs were cross-sectional). These are WI-011's core, not
  model tuning.

## Steps

### Step 1 — Condition definitions (trailing-only, from existing elements)
Define condition columns from `src/targets.py` / E5 primitives — no forward
data: trend presence (efficiency-ratio / OLS slope + R²), vol regime (ATR
percentile vs own trailing history), liquidity regime (amihud percentile),
TS momentum state (price vs own trailing MA / 52w channel position).
Acceptance: each condition is trailing, point-in-time, per-symbol; unit tests
assert no forward-window inputs.

### Step 1b — Indicator association analysis (admin direction 2026-10-25)
Descriptive correlation structure across the indicator panel: which indicators
co-associate (redundancy → drop), and which indicator values mark *extremes*
(local peaks/bottoms) vs *trends* (upward/downward states) — association only
(no forward-return claims here; that's Step 2's job). Output feeds the Step-1
condition vocabulary: conditions are built from the indicators that empirically
mark states, not from the full 89-feature pile.
Acceptance: `reports/wi011_indicator_association.md` — indicator × state
association table (extreme/trend), redundancy clusters, and the derived
candidate-condition list.

### Step 2 — Conditional expectancy tables (the meta-analysis core)
Walk-forward, purged 20td: per condition bucket × **horizon in {1, 2, 5, 10,
15, 20, 60, 120}d** → forward-return distribution stats (mean, std, hit rate,
5% tails), with per-condition t-stats and stability across 2 disjoint
sub-windows. **This IS the horizon sweep** — element signal measured at every
horizon before any model exists.
Acceptance: `reports/wi011_condition_expectancy.md`; stable-sign conditions
flagged; unstable ones flagged too (both are findings).

### Step 3 — Time-series momentum probe (never tested in this repo)
Per-symbol TS trend rules (own-past return signs, vol-scaled) at the same
horizons, evaluated as *conditions* (does this asset trend vs its own past?),
not cross-sectional ranks. Compare against the Step-2 tables: which elements
carry TS signal, which are purely cross-sectional?
Acceptance: TS vs CS decomposition per element in the report.

### Step 4 — Cost overlay + 200-trades/yr feasibility filter
Apply per-name cost estimates (spread/amihud-proportional, IBKR CAD commission
schedule) to each candidate condition's expectancy. Keep only conditions that
(a) survive costs net of expectancy, (b) fire 100–400×/yr total across the
universe, (c) hold within the 5–15d concurrency envelope (4–12 positions).
Acceptance: `reports/wi011_tradeable_conditions.md` — the shortlist of
conditions that are actually tradeable under the usage spec, or an explicit
"none survive costs at this universe size" (a valid, publishable answer).

### Step 5 — Decision rules distillation (→ handoff to screener MVP)
Each surviving condition → a decision rule (entry condition, hold window,
exit/invalidation condition), written as data, not as a model. Output feeds
the screener tearsheet: condition flags + factor tilts + "no-trade" default.
Acceptance: rule spec table + worked example on recent data; STOP at human
gate — rules are NOT backtested-optimized here (that's a separate gate if
admin wants it).

## Out of scope
- Any trained model. Any binary-target rebuild (closed branch).
- Position sizing / portfolio construction (human gate decides later).
- Live trading (MVP boundary: research shortlist, human gate).

## Verification
Every step verify command pattern:
`uv run python scripts/<step>.py && grep -E "<key markers>" reports/wi011_<step>.md`

## Execution log + status

Lives in the sibling file: `docs/plans/logs/WI-011-condition-first-meta-analysis.md`
(append-only, one row per step ≤50 words; `STATUS:` line at its end). This plan
file is frozen after the planner pass.