---
wi_id: WI-046
title: Update WORKFLOW.md + BOARD.md to the three-tier pipeline (D-025)
status: draft
agent: surgical-builder
depends_on: []
gate_layer: "N/A"
board_row: "D-025 tiered workflow (admin direction 2026-11-10)"
write_files:
  - docs/workflow/WORKFLOW.md
  - docs/workflow/BOARD.md
read_only_files:
  - docs/workflow/designs/D-025-tiered-workflow.md
  - docs/workflow/designs/D-023-two-layer-ml-gate.md
  - docs/workflow/designs/D-024-l2-overlay-rebuild.md
  - reports/tiered_workflow_status_2026-11-10.md
test_command: grep -n "Tier" docs/workflow/WORKFLOW.md | head -3
---

## 1. Objective and invariant
- Merge D-025's tier map into the SINGLE-SOURCE workflow docs: WORKFLOW.md gains the T1/T2/T3 table (contents, gate, license per tier, mapping to D-023/D-024 layers); BOARD header cites the current sprint tier. No parallel system — extend the established docs only; every existing rule (pre-committed closure, probe-first, FDR families, PROVISIONAL ratification) carries unchanged and is cross-linked, not restated differently.

## 2. I/O contract and blueprint (literal)
- WORKFLOW.md: new "Tiers" section right after the roles/modes section, table lifted verbatim from D-025 §1.
- BOARD.md: header refreshed to cite tiers; each sprint row names its tier(s). AGENTS.md gets a one-line pointer to the tier map if not present.

## 3. Definition of Done (binary)
- [ ] Tier table present in WORKFLOW.md; BOARD header cites tiers; no rule text contradicts D-023/D-024.
- [ ] No edits outside write_files. Core-hour cap: 0.
