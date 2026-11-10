---
wi_id: WI-049
title: T3 trade-mechanism survey — scoping doc for alternative action constructions (gated on WI-045)
status: draft
agent: surgical-builder
depends_on: [WI-045]
gate_layer: "N/A"
board_row: "D-025 tiered workflow (admin direction 2026-11-10)"
write_files:
  - docs/workflow/designs/D-026-trade-mechanisms-survey.md
read_only_files:
  - reports/l2/rerun_modern.json
  - reports/l2/rerun_legacy.json
  - reports/l2/edge_decay_probe.md
  - docs/workflow/designs/D-025-tiered-workflow.md
test_command: test -s docs/workflow/designs/D-026-trade-mechanisms-survey.md
---

## 1. Objective and invariant
- Scoping doc ONLY (the L2 pause policy stands: no overlay dispatch in this WI). Survey alternative trade-action mechanisms given the L1 library's strengths (ranking, calibration, regime-robust b_hold) and the named failure mechanism from WI-045's decomposition: (a) time-based exits vs event-based (bypasses thin-mass tau problem), (b) relative-value / cross-sectional ranking on L1 probabilities (long top-decile vs short bottom-decile — cost-amortizing), (c) volatility-target sizing on the frozen fib baseline, (d) hedged/long-short constructions on sector pairs. For each: cost-model math on the FROZEN baseline, expected tau-mass, and the specific decay mechanism it attacks (from WI-045). RE-proposing a closed overlay without a stated structural change is a defect.
- Output feeds a future D-0XX approval matrix; nothing is adopted here.

## 2. I/O contract and blueprint (literal)
- Output: `docs/workflow/designs/D-026-trade-mechanisms-survey.md` — per mechanism: construction, cost math at 25 bps, which named failure mechanism it attacks, data/feature prerequisites, and a go/no-go recommendation with the falsification condition.

## 3. Definition of Done (binary)
- [ ] Survey covers all four mechanisms, each with cost math + mechanism linkage; every recommendation cites WI-045's ranking.
- [ ] No edits outside write_files. Core-hour cap: 0.1.
