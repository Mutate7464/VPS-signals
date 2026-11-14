# FILE: docs/kanban/draft/WI-032-swing-bsh-probe.md
---
wi_id: WI-032
title: Probe swing-anchored buy/sell/hold first-touch labels (D-021)
status: draft
agent: surgical-builder
depends_on: []
board_row: "(new thread — admin direction in chat 2026-11-09; design docs/workflow/designs/D-021-swing-conditioned-buy-sell-hold.md)"
write_files:
  - src/swing_bsh/__init__.py:1-10
  - src/swing_bsh/events.py:1-120
  - src/swing_bsh/probe.py:1-200
  - tests/swing_bsh/test_probe.py:1-80
  - reports/wi032_probe.md:1-60
read_only_files:
  - docs/workflow/designs/D-021-swing-conditioned-buy-sell-hold.md
  - src/fib_swings/INDEX.md
  - src/wi016/triple_barrier.py
  - src/wi016/probe.py
  - src/wi016/meta_labeler.py
  - reports/wi016_label_density_CAD.csv
  - docs/workflow/DATA_CONTRACT.md
test_command: uv run pytest tests/swing_bsh/test_probe.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
- Build swing-event sampling (at-bottom/at-top from the fib swing detector) + 3-class first-touch labels {BUY, SELL, HOLD} and run the D-021 §5 probe (within-date rank-IC vs outcomes, BH-FDR, 5-seed placebo) per market. Invariants: n_jobs=2, float32 after calc, symbol-sequential reads, no all-ticker uncompressed DataFrame.

## 2. I/O contract and blueprint (literal)
- Input: `data/raw_ohlcv/market={USD,CAD}/` (cols: date, open, high, low, close, volume, average, barCount) + feature whitelist via existing feature pipeline (`src/feature_engine.py`); regime labels per WI-027 (`reports/fib_swings/`).
- `src/swing_bsh/events.py` (Lines 1–120): `sample_events(market: str, k_atr: float, barriers: tuple[int,int]=(21,55)) -> pd.DataFrame` — schema `symbol:str, date:datetime64, state:str{'at_bottom','at_top'}, y:int{0=HOLD,1=BUY,2=SELL}, horizon:int`; first-touch via `src/wi016/triple_barrier.py` barrier logic (k ∈ {1.5, 2.0}·ATR); side: at_bottom→long (stop=−k·ATR), at-top→short/exit (profit=−k·ATR move); vertical touch → HOLD.
- `src/swing_bsh/probe.py` (Lines 1–200): reuse `src/wi016/probe.py` probe pattern — per-feature within-date rank-IC vs y (BUY vs SELL split by implied side), BH-FDR across grid, 5-seed label permutation placebo; uniqueness prune |Spearman ρ|>0.7, ≥500 events/feature.
- Output: `reports/wi032_probe.md` + CSV; dry-run: `--market CAD --limit 20 --out /tmp/wi032_smoke` (never overwrite frozen report names). Runtime cap ~0.5 core-hours (n_jobs=2, checkpointed per symbol).
- `tests/swing_bsh/test_probe.py`: synthetic OHLCV (hand-built swing + known first-touch) → assert exact label per barrier geometry; empty-events ticker → 0 rows, no crash.

## 3. Definition of Done (binary)
- [ ] No edits outside `write_files`.
- [ ] `test_command` exits 0.
- [ ] Dry-run output row/null counts match section 2; probe report written for both markets (or explicit ABORT with measured event density).
- [ ] `INDEX.md` updated if an exported signature changed.
- [ ] Stdout ≤5 lines: exit status, output shape, null count, runtime.

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 1/2 (builder exited early; probe daemon finished clean) | **Commit:** (this commit) | **Status:** DONE
- **Notes / error tail:** `pytest tests/swing_bsh/test_probe.py` 9 passed; probe CAD+USD both CLEAR (USD 13 / CAD 19 FDR-significant); smoke `/tmp/wi032_smoke` ok.
