---
wi_id: WI-040
title: Layer-1 library consolidation of the winning b_hold family — calibration audit, feature attribution, pickle manifest, inference entrypoint
status: draft
gate_layer: L1
agent: surgical-builder
depends_on: [WI-038]
board_row: "D-022 thread phase 3 (admin direction in chat 2026-11-09: focus Layer 1, proceed with model development)"
write_files:
  - src/swing_bsh/library_audit.py
  - tests/test_swing_bsh_library_audit.py
read_only_files:
  - src/swing_bsh/binary_grid.py
  - src/swing_bsh/binary_features_ext.py
  - reports/wi036_summary.md
  - reports/wi038_summary.md
test_command: uv run pytest tests/test_swing_bsh_library_audit.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
- The Layer-1 pickle library now spans WI-036 (57 FDR survivors, 6838 pickles) + WI-035 + WI-038 (pending). Nothing indexes or audits it. This WI makes the library consumable: per-cell calibration (OOF reliability + Brier), feature attribution on the winner cell (`exact_full_k0.8` b_hold, best cross-market h), a manifest table (cell → market/variant/h/learner/binary → OOF AUC/IC → pickle path), and a single inference entrypoint that loads a manifest row and scores new bars end-to-end.
- Layer-1 only: NO thresholds, NO trading edge, NO entry filters — calibration and predictive stats only (D-023).
- Inference-only over existing OOF predictions/pickles where possible; re-fit only where OOF artifacts are absent, capped below.

## 2. I/O contract and blueprint (literal)
- Input: `data/models/wi036/` (+`wi035/`, `wi038/`) pickles; OOF prediction stores written by `binary_grid.py`.
- Output: `reports/wi040_library_manifest.md` + `data/models/wi040/manifest.parquet` (one row per pickle); `reports/wi040_calibration.md` (winner cell reliability curves + Brier, both markets); attribution table (top-20 features by OOF permutation importance on winner cell).
- Inference entrypoint: `python -m src.swing_bsh.library_audit --infer --cell <manifest_id>` scores the last N bars of named symbols end-to-end and writes nothing to frozen paths.
- Smoke: `WI040_SMOKE=5 --out /tmp/wi040_smoke`.
- Tests: manifest row count == pickle count for scanned dirs; winner-cell row resolves to an existing pickle path; `--infer` smoke exit 0; no edits outside `write_files`.

## 3. Definition of Done (binary)
- [ ] Manifest covers every pickle in wi035/wi036/wi038 dirs; spot-check 3 rows against `reports/wi036_summary.md` values.
- [ ] Calibration + Brier for winner cell both markets; honest report even if calibration is poor.
- [ ] Permutation attribution top-20 table; no SHAP dependency (not in manifest).
- [ ] Stdout ≤5 lines. Core-hour cap: 0.5 (permutation over a subset: ≤5 seeds × ≤2 markets winner cell only).

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 1/2 | **Commit:** PENDING (HEAD 5d080eb; no commit made) | **Status:** DONE — killed at session layer (EXIT 130) after completing artifacts; PM-verified 2026-11-10
- **Notes:** test_command exit 0 (7 passed); manifest 9,745 rows == 96+6,838+2,811 pickles, all paths resolve; calibration (USD Brier skill +0.327, ECE 0.0009) + CAD + top-20 permutation attribution both markets complete; `--infer` smoke exit 0 (test-covered); no SHAP dep; only manifest files touched.
- **PM close-out bullet (2026-11-10):** builder session killed by the runtime after artifacts landed (mtimes postdate log's last write); PM independently re-verified every DoD item above before closing — no re-dispatch needed.
