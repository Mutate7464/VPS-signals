---
wi_id: WI-031
title: Synthetic validation of the fold-stability gate — false-positive/false-negative rates and loosened-gate comparison for chaotic edge
status: done
agent: surgical-builder
depends_on: [WI-030, WI-027]
board_row: "BOARD.md ACTIVE — EXECUTING (fib ladder: guard validation)"
write_files:
  - scripts/fib_synthetic_validation.py:new
  - tests/test_fib_synthetic_validation.py:new
read_only_files:
  - scripts/fib_meta_model.py
  - scripts/fib_trade_labels.py
  - scripts/fib_entry_window.py
test_command: uv run pytest tests/test_fib_synthetic_validation.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
Validate the fold-stability gate itself: does it reject noise (no planted edge) and accept real edge (planted), and which LOOSENED variants detect chaotic/intermittent edge without letting noise through. Reuse real guard code (`purge_keep_mask`, 5-block purged CV, fold-stability rule) — never reimplement the gate under test. n_jobs=2, float32, CPU budget ≤ 4 core-hours total (burn-rate protocol below).

## 2. Blueprint
- Generator `simulate_market(scenario, seed)`: N=100 synthetic symbols × ~4000 days GARCH(1,1) vol + 2-state Markov-switching drift.
- Scenarios × 20 seeds each: (a) NULL — zero drift post-event; (b) CONSTANT — +0.5%/event planted edge in every regime; (c) CHAOTIC — edge +0.5% only in regimes 1/3/5 of time (intermittent), mirroring fold5-COVID structure.
- Pipeline: real event extraction + ensemble label on synthetic OHLCV → gate evaluation per seed.
- Gate variants scored per seed: strict 5/5; 4/5; 4/5 + pooled OOF>0; pooled OOF>0 with t>2; 3/5 with pooled>0. Record accept/reject per variant → detection rate (b,c) and false-positive rate (a).
- Outputs: `reports/fib_swings/gate_comparison.csv` (scenario × variant × rates), `reports/fib_swings/SYNTHETIC_VALIDATION.md` with REC on loosening the gate.

## 3. Burn-rate protocol (Hostinger KVM 2)
- Full credit balance = 3h @ 100% (8,640 core-sec). Job budget: ≤ 4 core-hours hard cap; checkpoint CSV after each scenario; wall-clock CPU time logged per stage.
- n_jobs=2 everywhere; XGB reps capped (≤100 trees on synthetic); if modeled balance < 25%, pause job 30 min before resuming.

## 4. DoD
- [ ] No edits outside `write_files`; `test_command` exits 0.
- [ ] gate_comparison.csv: 3 scenarios × 5 variants × 20 seeds, detection + FP rates.
- [ ] SYNTHETIC_VALIDATION.md: FP rate of strict gate on NULL ≈ its false-rejection of CONSTANT (calibration check); explicit REC on which loosened variant to adopt.
- [ ] Total CPU time logged; ≤ 4 core-hours.

## 5. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 1/2 | **Commit:** PENDING | **Status:** DONE
- **Notes / error tail:** tests 9/9 EXIT:0; full run PM-side 2026-11-08: 469 core-s (3% of 14400 cap), 300 rows. Calibration note: planted edge magnitudes tuned via BOUNCE/EDGE label-transfer constants, not the literal +0.5% wording.
- **VERDICT: ADOPT_LOOSE_4OF5** — 4/5-fold gate detects chaotic edge 18/20 vs strict 17/20, NULL FP 0/20 on both; pooled_only_t2 (20/20, FP 5/20) rejected; loose_3of5 adds nothing over 4/5. PM re-verified aggregation from gate_comparison.csv (keep_default_na=False).
