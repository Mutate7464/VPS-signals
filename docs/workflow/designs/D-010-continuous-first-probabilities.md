# D-010 — Continuous-first band probabilities

## Context
WI-009c needs probabilities for up (forward dollar move ≥2×ATR), down (≤−2×ATR), and stay (forward return within ±5%) from one continuous 20td forecast. The units differ, events may overlap, and WI-002 found more evidence in continuous space than in binary labels. The CAD feature/target artifacts and 20td purge/embargo are fixed.

## Options considered
- Independent binary classifiers: rejected; conflict with the continuous-first direction and can produce inconsistent/overlapping outputs.
- Split-conformal prediction intervals: simple finite-sample interval coverage, but an interval alone does not give the required event probabilities.
- Quantile regression: directly estimates conditional quantiles, but multiplies model fits and cost for the initial 1–2h budget.
- Chronological held-out residual empirical CDF: one continuous regressor plus a reusable forecast residual distribution; inexpensive and supports row-specific thresholds, with weaker conditional calibration claims.

## Decision
Use a split-calibration residual empirical CDF from chronological out-of-fold predictions. Shift that distribution by each row's regressor forecast and integrate the three specified events after converting all thresholds into the continuous target's units. Preserve possible event overlap. Publish calibration diagnostics; describe the output as empirical forecast probabilities, not guaranteed conditionally calibrated class probabilities. If diagnostics fail, report the negative result rather than adding independent classifiers.

## Consequences
**Positive:** continuous-first route; one distribution produces all three event probabilities; bounded initial compute; threshold semantics are explicit.
**Negative:** residual distribution may be miscalibrated across regimes/rows; tails are data-limited; the band events are not necessarily mutually exclusive. The shortlist composite uses `P(up)-P(down)` and reports `P(stay)` separately.

## Status
Proposed — pending admin acceptance.
