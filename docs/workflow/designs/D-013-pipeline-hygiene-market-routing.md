# D-013 — Market routing and artifact isolation

## Context
WI-013 fixes cross-market execution and report-overwrite hazards across WI-011/WI-009c stages. Default behavior must run USD then CAD, explicit selection must run one market, and existing unsuffixed reports are frozen gate records.

## Options considered
1. Keep per-script market parsing and path construction: minimal shared code, but inconsistent defaults and easy-to-miss unsuffixed writers.
2. Centralize market selection and market-suffixed output-path construction, with each script passing its output stem: consistent validation and testable artifact isolation, with a small shared abstraction.
3. Run a shell wrapper twice: leaves direct script invocations CAD-only and cannot guarantee every internal writer/input is routed consistently.

## Decision
Use a shared Python helper for market selection and output naming; scripts invoke markets sequentially in USD, CAD order by default and use a single selected market with `--market USD|CAD`. All generated artifacts use market-suffixed paths. Frozen unsuffixed inputs may be read where required but never written. Keep data math and model/split semantics unchanged.

## Consequences
- Positive: one validation/default contract, centralized path tests, and frozen report names cannot be overwritten by ordinary runs.
- Negative: scripts with multiple sidecars and cross-stage inputs need careful market-context threading; the BOTH default increases runtime versus a one-market invocation.

## Status
proposed
