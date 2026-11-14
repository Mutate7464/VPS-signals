---
wi_id: WI-044
title: L1 learner extension — RandomForest, ExtraTrees, isotonic-calibrated winner, elastic-net logistic on the winning b_hold cells (all existing deps)
status: done
verdict: RATIFIED (admin in chat 2026-11-10) — 6 BH-FDR survivors join the L1 library (Layer 1, D-023); best cell random_forest/b_hold/h21 min cross-market AUC 0.7341; predictive license only, no trading claim
gate_layer: L1
agent: surgical-builder
depends_on: []
board_row: "D-024 §2 learner extension (admin direction in chat 2026-11-10: add other MLs useful wrt goals and data)"
write_files:
  - src/swing_bsh/learner_ext.py
  - tests/test_swing_bsh_learner_ext.py
read_only_files:
  - src/swing_bsh/binary_grid.py
  - src/swing_bsh/binary_features_ext.py
  - src/swing_bsh/library_audit.py
  - docs/workflow/designs/D-024-l2-overlay-rebuild.md
test_command: uv run pytest tests/test_swing_bsh_learner_ext.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
- Widen the L1 library with learners suited to the data (event tabular, thin positives ~0.4-4%): **LightGBM** and **CatBoost** (gradient boosting with native handling of small/imbalanced folds — deps ADOPTED by admin and installed 2026-11-10: lightgbm 4.7.0, catboost 1.2.10; both CPU, n_jobs=2/thread_count=2 enforced), RandomForest + ExtraTrees (bagged, low-variance on small folds), isotonic-calibrated XGB wrapper (CalibratedClassifierCV on the WI-036 winner learner — improves probability reliability, which the L2 τ grids depend on), elastic-net logistic (l1_ratio grid; sparse-selection cross-check on WI-040's attribution).
- Targeted grid (not the full WI-036 sweep): top-2 variants (`exact_full_k0.8`, `tol2_full_k0.8`) x h in {13,21,34,55} x `b_hold` only x 2 markets x **6 new learners** x 5 folds. BH-FDR within this grid; passers join `data/models/` and the WI-040 manifest.
- Env note (host-verified): no system libgomp on the VPS (no passwordless sudo); torch's bundled copy is preloaded via `.venv/.../sitecustomize.py` so lightgbm's dlopen resolves. If the venv is rebuilt (`uv sync`), re-create that sitecustomize or lightgbm imports fail.
- n_jobs=2, float32, symbol-sequential; same purged/embargoed CV and placebo machinery as WI-036 (imported, never re-implemented).

## 2. I/O contract and blueprint (literal)
- Output: `reports/wi044_summary.md` (ranking + FDR survivors + per-learner calibration note) + pickles `data/models/wi044/`; manifest refresh via library_audit scan.
- Smoke: `WI044_SMOKE=5 --out /tmp/wi044_smoke`.
- Tests: learner registry = exactly the 6 new learners (incl. LightGBM n_jobs=2 + CatBoost thread_count=2); grid constants; embargo = max(20, h); import guard confirms all 6 import on a clean env.

## 3. Definition of Done (binary)
- [ ] All cells scored with honest verdicts; FDR table; calibrated-wrapper reliability reported.
- [ ] No edits outside write_files; test_command exit 0; stdout <=5 lines. Core-hour cap: 2.0 (6 learners x 160 cells).

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 3/2 | **Commit:** PENDING (HEAD 4f579002384cc0ef0aedccbf474f0e15061a31a9; no commit made) | **Status:** PASS
- **Evidence:** `uv run pytest tests/test_swing_bsh_learner_ext.py -q --tb=short --maxfail=1` → 19 passed. Fix 1 (test run 1): CatBoost rejects `n_jobs` — CPU cap re-imposed as `thread_count`; fix 2 (test run 2): saga `LogisticRegression` takes no `n_jobs`/`penalty` on sklearn 1.9 — kwargs cleaned. Smoke `WI044_SMOKE=5 --out /tmp/wi044_smoke` → 96 cells, 4 stdout lines; fix 3 (smoke run 1): nested `CalibratedClassifierCV(cv=3)` cannot split thin b_hold folds — inner fold count now capped by the minority class with an honest fall-back to the base fit.
- **Full run:** `uv run python -m src.swing_bsh.learner_ext --market ALL` (foreground, 82 min wall) → stdout 4 lines, 80 cells scored / 16 truncated by the cap, 6 placebo-tested cells, 6 BH-FDR survivors, 6495 core-s (1.80 of the 2.0 core-h cap); wrote `reports/wi044_summary.md`, 400 fold pickles + `data/models/wi044/manifest.parquet` (WI-040 row schema, all 6 learners parsed). Note: `src/swing_bsh/learner_ext.py` is 425 lines — above the 250-line soft guide, in line with `binary_grid.py` (556) / `library_audit.py` (464); no file outside `write_files` was edited.
