---
wi_id: WI-043
title: Port and rerun the three legacy L2 questions (WI-012 cross-market gate, WI-018 first_touch_34 cost overlay, WI-011 condition-first meta) under the D-024 harness
status: done
verdict: RATIFIED (admin in chat 2026-11-10) — wi012 REJECT (cross-market transfer closed), wi018/wi011 INERT; legacy three closed permanently per D-024 pre-committed closure; no deployment
gate_layer: L2
agent: surgical-builder
depends_on: [WI-042]
board_row: "D-024 L2 rebuild (admin direction in chat 2026-11-10: rerun old L2s)"
write_files:
  - src/l2_overlay/rerun_legacy.py
  - tests/test_l2_rerun_legacy.py
read_only_files:
  - src/l2_overlay/harness.py
  - src/l2_overlay/rerun_modern.py
  - src/wi018/cost_overlay.py
  - src/wi011/conditions.py
  - scripts/wi011_tradeable_conditions.py
  - docs/workflow/designs/D-024-l2-overlay-rebuild.md
test_command: uv run pytest tests/test_l2_rerun_legacy.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
- Port the three legacy questions to current data via the harness: WI-012 (does a USD-tuned overlay transfer to CAD — run the harness-tuned USD decision on CAD, judged on CAD edge), WI-018 (first-touch h34 cost overlay vs frozen baseline), WI-011 (condition-first overlay on the modern event base).
- Same D-024 §2 protections; BH-FDR across these 3 as ONE family (separate from WI-042's family). Pre-committed closure: REJECT closes the question permanently.
- Dependency discipline: if WI-042's four modern reruns all REJECT/INERT with no ADOPT, this WI still runs (admin ordered the full rerun) but reports budget spent as its own cap.

## 2. I/O contract and blueprint (literal)
- Output: `reports/l2/rerun_legacy.md` + `.json`, same shape as WI-042.
- Smoke: `L2_SMOKE=5` to /tmp, stops at feasibility precheck (no EVAL burn).
- Tests: question→baseline mapping for all 3; FDR family = 3; cross-market WI-012 port judged on CAD edge only.

## 3. Definition of Done (binary)
- [ ] All three verdicts recorded honestly (INERT allowed); FDR table.
- [ ] No edits outside write_files; test_command exit 0; stdout <=5 lines. Core-hour cap: 1.5.

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 1/2 | **Commit:** cbf9022 | **Status:** DONE
- Evidence: `uv run pytest tests/test_l2_rerun_legacy.py -q --tb=short --maxfail=1` → 13 passed; `uv run python -m src.l2_overlay.rerun_legacy` → 42 cells, 5 tested, {'REJECT': 5, 'INERT': 37}, 16.8 s.
- **Result:** wi012 tuned on USD CALIB (tau 0.50) and judged on CAD → REJECT (CAD CALIB edge −0.46 bps); wi018 (h34 mass) and wi011 (cadence 2.0k–4.6k firings/yr) INERT. Reports: `reports/l2/rerun_legacy.{md,json}`.
- **PM full-run (2026-11-10):** credit 100% pre-run; `uv run python -m src.l2_overlay.rerun_legacy` EXIT:0, 17.2 s — reproduced builder numbers exactly (42 cells, 5 tested, {REJECT 5, INERT 37}); pytest 13 passed re-verified. Verdicts PROVISIONAL until admin ratifies.
