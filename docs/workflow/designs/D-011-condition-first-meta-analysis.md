# D-011 — Condition-first meta-analysis

## Context
WI-009b/c found regime-dependent factor signs, weak binary/continuous model routes, and no tested horizon sweep or per-symbol time-series momentum probe. WI-011 must decide whether any point-in-time condition is descriptive, stable across time, frequent enough, and still viable after CAD costs. Admin direction fixes the scope: descriptive analysis, no ML, and a human stop before optimized backtesting.

## Options considered
1. Continue model/label work over the existing feature panel.
2. Run a condition-first, per-symbol descriptive analysis, then derive unoptimized rule specifications only for cost/frequency-qualified conditions.
3. Stop research because previous model routes were negative.

## Decision
Choose option 2. Use trailing conditions from `src/targets.py`/E5 primitives and an empirically selected compact indicator subset; evaluate eight fixed horizons with chronological purging and a same-sign test across two disjoint sub-windows. Include the previously untested TS-momentum probe, disclose CAD cost assumptions, and allow “none survive costs at this universe size” as a valid conclusion. Deliver data-only rules and stop at the human gate.

## Consequences
**Positive:** Tests the unconditioned-horizon and TS branches directly; prevents full-panel fishing and sign selection after evaluation; produces an honest negative result if costs/frequency defeat candidates; avoids model and training cost.

**Negative:** Descriptive associations do not establish causal effects or guarantee forward performance. Purging at least the tested horizon reduces usable observations, especially at 60/120 days. Cost and frequency estimates depend on documented assumptions; no execution or optimized-backtest claim follows.

## Status
proposed — pending admin acceptance.
