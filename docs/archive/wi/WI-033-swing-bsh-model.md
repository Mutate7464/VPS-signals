# FILE: docs/kanban/draft/WI-033-swing-bsh-model.md
---
wi_id: WI-033
title: Swing-conditioned 3-class buy/sell/hold model under ADOPT_LOOSE_4OF5
status: draft
agent: build
depends_on: [WI-032]
board_row: "(new thread — admin direction in chat 2026-11-09; design D-021)"
write_files:
  - src/swing_bsh/train.py:1-260
  - src/swing_bsh/evaluate.py:1-180
  - tests/swing_bsh/test_train.py:1-90
  - reports/wi033_summary.md:1-60
read_only_files:
  - docs/kanban/draft/WI-032-swing-bsh-probe.md
  - reports/wi032_probe.md
  - src/xgb_trainer.py
  - src/model_qa.py
  - docs/workflow/designs/D-021-swing-conditioned-buy-sell-hold.md
test_command: uv run pytest tests/swing_bsh/test_train.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
- Only if WI-032 probe clears: train `XGBClassifier(objective="multi:softprob", tree_method="hist", n_jobs=2)` on swing-event rows (WI-032 `sample_events` output) inside 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, horizon))`; gate = **ADOPT_LOOSE_4OF5 vs the frozen fib-rule baseline** (WI-028 entry + WI-030 exit `t15_s10_d39_close`) + CB-05 placebo. Invariants: n_jobs=2, float32, symbol-sequential, checkpointed.

## 2. I/O contract and blueprint (literal)
- Input: WI-032 event frame (`symbol, date, state, y, horizon` + whitelisted features) — read via pyarrow.dataset, symbol-sequential.
- `src/swing_bsh/train.py` (Lines 1–260): fold loop from `src/xgb_trainer.py:581-644` pattern — per-fold isotonic calibration (sigmoid fallback <25 positives, CB-04); final model pickled to `models/swing_bsh/{market}.pkl` with provenance metadata; TreeSHAP `pred_contribs` top drivers.
- `src/swing_bsh/evaluate.py` (Lines 1–180): ADOPT_LOOSE_4OF5 gate (fold-wise expectancy/IC of model-filtered events vs frozen-rule events, ≥4/5 folds), placebo z, shortlist emit into WI-014 artifact schema behind human gate.
- Output: `reports/wi033_summary.md` (gate verdict table), `models/swing_bsh/{USD,CAD}.pkl`, shortlist CSV. Dry-run: `--market CAD --limit 20 --out /tmp/wi033_smoke`. Core-hour cap: ≤2 h @ n_jobs=2, per-fold checkpoint JSON.
- `tests/swing_bsh/test_train.py`: synthetic events → assert fold count, calibration fallback path, gate verdict math (4/5 adopt vs 3/5 reject).

## 3. Definition of Done (binary)
- [ ] No edits outside `write_files`.
- [ ] `test_command` exits 0.
- [ ] Gate verdict (ADOPT/REJECT/INCONCLUSIVE) recorded with per-fold table in `reports/wi033_summary.md`.
- [ ] No model pickle written unless gate = ADOPT (smoke runs write to /tmp only).
- [ ] Stdout ≤5 lines: exit status, verdict, fold wins, runtime.

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 1/2 | **Commit:** (this commit) | **Status:** DONE (gate REJECT — negative result recorded)
- **Notes / error tail:** `uv run pytest tests/swing_bsh/test_train.py -q --tb=short --maxfail=1` → 8 passed (exit 0). Full run `python -m src.swing_bsh.evaluate --market ALL` (878 s @ n_jobs=2, ≤2 h cap): USD 460,314 / CAD 252,420 events → gate **REJECT both markets** (USD 4/5 folds but pooled edge −0.0015, placebo z −19.7; CAD 2/5 folds, edge −0.0007, z −8.0); no pickle/shortlist written (DoD §3); checkpoints `reports/wi033_checkpoint_{USD,CAD}.json`.
