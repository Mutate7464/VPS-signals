---
wi_id: WI-084
title: Build gap-aware triple-barrier engine (L2-TB)
status: draft
agent: surgical-builder
depends_on: ["WI-082"]
gate_layer: "2"
board_row: "Track B (L0/L1/L2 research, UNFROZEN 2026-11-19) — plan 26-W47-visualizer-audit-workbench"
write_files:
  - src/l2_tb/barriers.py
  - tests/l2_tb/test_barriers.py
read_only_files:
  - docs/workflow/DATA_CONTRACT.md
  - data/models/wi048/up_cells.json
test_command: uv run pytest tests/l2_tb/test_barriers.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
Gap-aware triple-barrier labeling engine: profit barrier (+10% fixed or k_tp·sigma_pre), stop (k_sl·sigma_pre) with parallel 1.0/1.5/2.0σ profiles as columns, gap-aware stop fill at bar open (GAP_SL), T1 milestone (+5%/1.5σ), trailing ATR-stop R-multiple, benchmark excess (SPY/XIU), forced TIMEOUT=0.
- **G2 RATIFIED (admin in chat 2026-11-19, build-only):** dispatch unblocked. The EVAL burn is DEFERRED (never on the 24-trading-day virgin window); prereg draft + split proposal: `docs/workflow/briefs/2026-11-19-g2-l2tb-prereg-proposal.md` — freeze+hash at burn time. Builder smoke MUST NOT read any bar dated 2026-08-21 or later (virgin EVAL window preserved).
- Invariants: n_jobs=2, float32, symbol-sequential reads, checkpointed ≤2.5 core-h per human-confirmation interval, credit monitor before dispatch.

## 2. I/O contract and blueprint (literal)
- Input: `data/raw_ohlcv/market=<MKT>/symbol=<T>.parquet` (+ entry events from the OOF/targets key convention).
- Output: `data/features/l2_tb/labels_{MKT}.parquet` — cols `symbol str, date date32, l2_meta_hit int8, l2_exit_type str, l2_r_mult float32, l2_t1_hit int8, l2_trail_r float32, l2_excess_hit int8, l2_bars_held int16, l2_hit_s10/l2_hit_s15/l2_hit_s20 int8`.
- `barriers.py`: `run_barriers(events, ohlcv, params) -> table`; intrabar touch via high/low vs. levels; gap fill at open; benchmark excess from SPY/XIU rows in raw_ohlcv (verify presence first).
- `tests/l2_tb/test_barriers.py`: synthetic gap bars (open beyond stop → GAP_SL at open), timeout=0 forced, first-touch ordering TP>SL within bar, reproduces fixed_h55 first-touch behavior when new features are disabled.

## 3. Definition of Done (binary)
- [ ] No edits outside write_files.
- [ ] test_command exits 0 (synthetic gap + timeout + order cases).
- [ ] fixed_h55 reproduction check passes on one market smoke set.
- [ ] Stdout ≤5 lines.

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 0/2 | **Commit:** PENDING | **Status:** PENDING
- **Notes / error tail:** None
