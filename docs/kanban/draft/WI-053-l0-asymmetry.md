---
wi_id: WI-053
title: L0-2 realized asymmetry / semivariance / skew block
status: draft
agent: surgical-builder
depends_on: [WI-051]
gate_layer: "1"
board_row: "D-026 SPRINT — L0-2 (admin-accepted 2026-11-13)"
write_files:
  - src/swing_bsh/binary_features_ext.py:190-302
  - tests/test_l0_asymmetry.py
read_only_files:
  - src/swing_bsh/binary_features_ext.py:60-90
test_command: uv run pytest tests/test_l0_asymmetry.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
Add a payoff-shape block distinct from the WI-047 range levels: up/down realized semivariance, their ratio, and realized skew of log returns over trailing windows. Trailing-only, float32, dimensionless.

## 2. I/O contract and blueprint
- Input: per-symbol `close`.
- Output: `_realized_asymmetry(...)` block wired into `build_variant_panel`: `semivar_up_{w}`, `semivar_dn_{w}`, `semivar_ratio_{w}`, `rv_skew_{w}` for `w in (21, 55)`; float32; guard `w` on prior-mean returns.
- Prefixes added to `candidate_features`.
- Tests `tests/test_l0_asymmetry.py`: monotone-up series -> skew>0, up-semivar >> dn; flat series -> ratio 1; NaN warmup.
- Smoke: `WI048_SMOKE=3 uv run python -m src.swing_bsh.targets_ext --probe --out /tmp/wi053_smoke` exit 0.

## 3. Definition of Done
- [ ] No edits outside write_files. [ ] test_command exits 0. [ ] cols float32, dimensionless, causal. [ ] candidate_features gains the prefix. [ ] Stdout ≤5 lines.

## 4. Telemetry footer
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes:** None
