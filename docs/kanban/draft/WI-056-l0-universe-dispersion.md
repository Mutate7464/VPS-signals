---
wi_id: WI-056
title: L0-5 universe vol-regime dispersion (net-new check)
status: draft
agent: surgical-builder
depends_on: [WI-051]
gate_layer: "1"
board_row: "D-026 SPRINT — L0-5 (admin-accepted 2026-11-13; net-new precondition)"
write_files:
  - src/swing_bsh/binary_features_ext.py:190-302
  - tests/test_l0_universe_dispersion.py
read_only_files:
  - src/swing_bsh/binary_features_ext.py:60-90
test_command: uv run pytest tests/test_l0_universe_dispersion.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
Add a date-level cross-sectional block: dispersion (IQR / std) of `atr_pct_21` and `entropy_39` across the universe on each date — a market-wide vol-regime spread. **Precondition:** first confirm this is net-new vs WI-047 #3 (market-residual context); if it is a variant, STOP and return a one-line finding instead of building. Trailing/point-in-time, float32.

## 2. I/O contract and blueprint
- Input: the panel (all symbols, same date).
- Output: date-keyed `_universe_dispersion(panel)` merged like the breadth block: `disp_atr_pct_21`, `disp_entropy_39`. float32. No future-symbol leakage (only same-date rows).
- Prefixes added to `candidate_features`.
- Tests `tests/test_l0_universe_dispersion.py`: crafted two-symbol dates -> known dispersion; single-symbol date -> 0; net-new check documented.
- Smoke: `WI048_SMOKE=3 uv run python -m src.swing_bsh.targets_ext --probe --out /tmp/wi056_smoke` exit 0.

## 3. Definition of Done
- [ ] No edits outside write_files. [ ] test_command exits 0. [ ] net-new precondition resolved (built OR returned as a variant finding). [ ] candidate_features gains the prefix. [ ] Stdout ≤5 lines.

## 4. Telemetry footer
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes:** None
