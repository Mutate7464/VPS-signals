# D-15 — WI-015 research pipeline scope

## Context
WI-015 is a substantial research pipeline: build point-in-time run targets, extend normalized feature families to the confirmed Fibonacci grid, then measure held-out alignment. It complements shipped WI-014; trading applications are deferred.

## Options considered
1. Build targets, features, and alignment in one inseparable run.
2. Sequence target dataset (G-PA2), feature panel, then held-out alignment (G-PA1), retaining separate market-specific artifacts and verification points.
3. Integrate the output into WI-014 immediately.

## Decision
Choose option 2. Keep CAD and USD support, with BOTH defaulting to sequential CAD then USD processing. Use the brief's admin defaults and the existing target/E5 patterns; preserve the output as research artifacts.

## Consequences
- Positive: point-in-time targets and feature coverage can be independently verified; per-market artifacts are reproducible and bounded-memory; WI-014 remains frozen until a later explicit gate.
- Negative: separate datasets/report steps add intermediate artifacts; exact target thresholds and association methodology must remain documented and tested to prevent silent definition drift.

## Status
proposed
