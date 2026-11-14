---
wi_id: WI-063
title: L1.5 meta-label full-universe driver (`run_meta_label.py`) + smoke
status: draft
agent: surgical-builder
depends_on: [WI-062]
gate_layer: "1"
board_row: "L2 rebuild input-prep (admin 2026-11-14: meta-label run is the first input-prep WI)"
write_files:
  - scripts/run_meta_label.py
  - tests/test_run_meta_label.py
read_only_files:
  - src/swing_bsh/train.py
  - src/swing_bsh/meta_label_ext.py
test_command: uv run pytest tests/test_run_meta_label.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
Driver that runs the ratified WI-062 meta-label machinery on the full universe per
market: build the event panel via `train.build_event_panel`, derive primary sides
with `meta_label_ext.primary_sides(panel['state'])`, label `y_meta =
build_meta_labels(side, panel['r_frozen'])` with **cost=0.0** (the 25 bps per-side
floor is already inside `r_frozen` — document this in the module docstring), features
via `meta_label_ext.feature_names(panel.columns)` on detection-bar geometry only,
then `meta_oof(y_meta, primary_oof, X, dates)`. Layer-1 predictive output ONLY:
pooled OOF AUC, per-fold AUCs, n_scored, feature-guard status, primary-side
prevalence. No threshold, no entry rule, no EV.

## 2. I/O contract and blueprint
- CLI: `uv run python scripts/run_meta_label.py --market USD|CAD [--smoke]`.
  `--smoke` uses a tiny synthetic fixture (or a small symbol subset) writing to a
  /tmp prefix and must NOT touch any real output path.
- Output (full run, PM-owned, NOT run by the builder):
  `reports/l15_meta_label/meta_label_<MKT>.json` + `.md` summary (pooled AUC,
  fold table, n rows/scored, positive rate, feature-guard result,
  `primary_oof_used_as_feature` must be False).
- `primary_oof`: pass a same-length aligned placeholder (e.g. the side itself or
  NaN-padded zeros) — it is alignment/diagnostic only and is excluded from
  features by the WI-062 guard; assert `primary_oof_used_as_feature is False` in
  tests.
- Invariants: float32 X, `n_jobs=2`, purge sentinels (`-1`) excluded, stdout ≤5
  lines, no edits outside write_files.

## 3. Definition of Done
- [ ] test_command exits 0 (synthetic separation AUC>0.5; permuted labels ≈ 0.5;
      guard asserts; smoke CLI runs end-to-end).
- [ ] No edits outside write_files. [ ] Stdout ≤5 lines. [ ] No real output path
      written by smoke.

## 4. Telemetry footer
- **Attempts:** 1/2 (first attempt passed) | **Commit:** PENDING (HEAD d6efa8c6ed2964eee36d7b8d30604f4a036a00df; no commit made) | **Status:** DONE
- **START_UTC:** 2026-11-14T19:26:00Z | **END_UTC:** 2026-11-14T19:35:00Z | **Core-h:** 0.01 | **NEXT_ALLOWED_RUN_UTC:** none (< 1 core-h burst)
- **Notes:** `uv run pytest tests/test_run_meta_label.py -q --tb=short --maxfail=1` -> 7 passed in 1.92s;
  smoke CLI (`--market USD --smoke`) prints 3 lines and writes only `/tmp/wi063_meta_label_smoke`;
  `reports/l15_meta_label/` untouched. Wrote only `scripts/run_meta_label.py` (249 lines) and
  `tests/test_run_meta_label.py` (124 lines); no INDEX.md update needed (new module, no changed signatures).
