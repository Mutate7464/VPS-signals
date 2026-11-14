---
wi_id: WI-047
title: T1 feature/TA gap research — inventory, missing-family scan, extension proposal
status: done
verdict: PASS (research inventory — PROVISIONAL, proposals not adopted yet)
agent: surgical-builder
depends_on: []
gate_layer: "1"
board_row: "D-025 tiered workflow (admin direction 2026-11-10)"
write_files:
  - reports/t1_feature_gap_report.md
  - src/swing_bsh/feature_inventory.py
  - tests/test_feature_inventory.py
read_only_files:
  - reports/tiered_workflow_status_2026-11-10.md
  - reports/wi040_calibration.md
  - src/swing_bsh/binary_features_ext.py
  - docs/workflow/designs/D-025-tiered-workflow.md
test_command: uv run pytest tests/test_feature_inventory.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
- Build a category inventory of the current ~100+ feature panel (programmatically from `binary_features_ext.py`: momentum, mean-reversion, volatility, entropy/fractal, volume/liquidity, cross-sectional, sector, event-quality, calendar, breadth) with the WI-040 attribution attached per family.
- Scan literature/web (agent-side research) for feature families MISSING or WEAK vs the aligned signal (entropy/Hurst/ATR%): realized-vol forecasters (Parkman/Yang-Zhang), volume/liquidity profile (dollar-volume percentile, Amihud), seasonality beyond month/dow (turn-of-month, pre-holiday), cross-asset context (SPX/sector relative), regime meta-features (BB width percentile). Rank proposals by (i) fills a missing family, (ii) strengthens an already-aligned family, (iii) computable from existing ingested data (no new ingestion in this WI).
- L1 license: no model claim; output is a proposal list, not adopted features.

## 2. I/O contract and blueprint (literal)
- Output: `reports/t1_feature_gap_report.md` — inventory table (family, columns, attribution evidence), gap analysis, ranked proposal list with formulas + data-source feasibility, and a shortlist for the next grid WI. `feature_inventory.py` emits the inventory programmatically (so it can be re-run when the panel grows); tests cover the inventory parser on the current panel.
- Smoke: N/A (research WI); inventory run must exit 0 and cover ≥95% of panel columns.

## 3. Definition of Done (binary)
- [x] Inventory covers the full panel; ≥3 missing families analyzed; ranked shortlist with formulas; no new deps, no new ingestion.
- [x] No edits outside write_files; test_command exit 0. Core-hour cap: 0.2.

## EXECUTION TELEMETRY
- **Attempts:** 1/2 (step ceiling hit — builder wrote all 3 artifacts, PM filled footer) | **Commit:** PENDING (no commit made) | **Status:** DONE
- `test_command`: `uv run pytest tests/test_feature_inventory.py -q --tb=short --maxfail=1` → **8 passed in 0.50s**
- Inventory smoke: `uv run python -m src.swing_bsh.feature_inventory` → exit 0, 249/249 classified, coverage 1.000 (bar 0.95)
- Report `reports/t1_feature_gap_report.md`: 5 gaps (G1–G5) + G6 (blocked/no-data), 12 proposals ranked, 5-item shortlist (§5)
- Read-only: no new deps (stdlib ast/itertools + pandas), no new ingestion, no edits outside manifest
- L1 only (D-023 §2): proposals are not adopted features — PROVISIONAL until ratified
