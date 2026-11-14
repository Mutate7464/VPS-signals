# FILE: WI-035 — three separate binary XGB models + two-threshold entry gate (D-022 §3)
---
wi_id: WI-035
title: Train 3 binary profit/stop/hold models per learner (xgboost, logistic_l2, hist_gbm, optional mlp_torch); two-threshold entry rule vs frozen baseline under ADOPT_LOOSE_4OF5
status: draft
agent: surgical-builder
depends_on: []
board_row: "D-022 thread (admin direction in chat 2026-11-09: skip probe, produce models directly, confirmatory no-edge run)"
write_files:
  - src/swing_bsh/binary_labels.py
  - src/swing_bsh/binary_train.py
  - src/swing_bsh/binary_evaluate.py
  - tests/test_swing_bsh_binary_labels.py
  - tests/test_swing_bsh_binary_gate.py
read_only_files:
  - src/swing_bsh/events.py
  - src/swing_bsh/train.py
  - src/swing_bsh/evaluate.py
  - reports/wi033_summary.md
test_command: uv run pytest tests/test_swing_bsh_binary_gate.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
- Learner grid (D-022 §3b), each on `b_profit/b_stop/b_hold`, feature grid = WI-034 kept set (ρ>0.4 prune) + state/k/horizon: `xgboost` (`XGBClassifier(binary:logistic, tree_method="hist", n_jobs=2)`), `logistic_l2` (sklearn, standardized features), `hist_gbm` (sklearn `HistGradientBoostingClassifier`), optional `mlp_torch` (CPU, early-stopped, only if budget remains). Per-fold isotonic per binary per learner, sigmoid fallback <25 positives (CB-04). n_jobs=2, float32, symbol-sequential.
- Learner + threshold pair selected on CALIB folds ONLY, frozen before EVAL; single placebo on the selected config. Do NOT renormalize the three probabilities; the entry rule is a threshold filter.

## 2. I/O contract and blueprint (literal)
- Input: labels from `binary_labels.py` (new; wraps `src/swing_bsh/events.py` geometry) + whitelisted feature frame with ρ>0.4 prune computed inline (WI-034 skipped per admin 2026-11-09); `PurgedWalkForwardSplit(embargo_td=max(20, h))`, 5 folds.
- Entry rule: at-bottom event taken iff `P̂_profit ≥ τ_p AND P̂_stop ≤ τ_s`; grid τ_p∈{0.40,0.50,0.60,0.70}, τ_s∈{0.20,0.30,0.40,0.50}, tuned on CALIB folds only, frozen before EVAL.
- Baseline: frozen fib rules (WI-028 at-bottom entry + WI-030 `t15_s10_d39_close`, 25 bps); placebo: CB-05 5-seed label permutation.
- Output: `reports/wi035_summary.md` — per-market fold table, pooled edge, placebo z, top TreeSHAP per binary model. **SAVE every fitted model as pickle** (admin override 2026-11-09, saved for future testing): `data/models/wi035/<MKT>_<learner>_<binary>_f<fold>.pkl` — all learners, all three binaries, all folds, both markets. Keep pickles out of git (`data/models/` is untracked).
- Dry-run: `WI035_SMOKE=5 symbols --out /tmp/wi035_smoke`.
- Tests (synthetic): two-threshold rule selects the intersection only; isotonic fallback triggers <25 positives; no leakage (fwd cols excluded from feature list).

## 3. Definition of Done (binary) — ADMIN OVERRIDE 2026-11-09
Purpose is CONFIRMATORY: run is expected to document no edge. Gate arithmetic (ADOPT_LOOSE_4OF5) still computed and reported for the record; placebo (CB-05) may be reduced to 3 seeds if runtime-tight — admin waived full check battery. **Pickles ARE saved regardless of verdict** (admin override 2026-11-09: every fitted model kept for future testing; nothing deployed, shortlist unchanged).
- [ ] No edits outside `write_files`.
- [ ] `test_command` exits 0.
- [ ] Stdout ≤5 lines. Core-hour cap: 1.0 (checkpoint per market; pause ≥30 min if Hostinger balance < 25%).

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 1/2 | **Commit:** PENDING (HEAD b77203b; no commit made) | **Status:** DONE
- **Notes:** smoke OK -> full both-market run in FOREGROUND twice (761s incl. panel build / 304s replay; 178% CPU, 1.4 GB RSS, ~0.15 core-h per replay << 1.0 cap); `test_command` 16/16 green (1fixture fix); pickles 96 = (3 learners x 3 binaries x 5 folds + 3 xgb-final) x 2 markets in `data/models/wi035/`, verdict-independent.
- **Notes / error tail:** USD REJECT (1/5, edge -0.0124, z -0.89); CAD ADOPT (4/5, edge +0.1787, z +4.10) is EXPLICITLY flagged record-only fat-tail (39/17,332 events selected, pooled IC +0.042, `r_frozen` |max|~8.0) — no edge claimed, no shortlist, nothing deployed; rule frozen on CALIB = logistic_l2 tp=0.40/ts=0.30 both markets.
