# Overnight brief — fib-swing Phase 2 chain (WI-021 → 023 → 022 → 024 → 025)

> Created 2026-11-06 by Hermes (PM) on admin direction in chat ("prompt to optimize the next few
> runs, unattended overnight, weaker GLM agent"). Launching `chain.sh` = admin approval to execute
> these 5 research WIs. Local commits only; no push, no BOARD edits, no shortlist/order changes.

## Design: take judgment away from the weak model
A weak model fails by improvising (own formulas, extra features, tuned thresholds), scope-creeping
into unlisted files, claiming success it didn't verify, and drowning in context. So:

| Concern | Who handles it |
|---|---|
| Write code + synthetic tests for ONE WI | GLM via `opencode run --agent surgical-builder` (fresh session per WI; reads only the WI + its listed files) |
| Every formula, constant, column, threshold, date | Fixed in the WI's Section 2 — the prompt forbids substitution |
| Staging, locks, `git mv`, commits | `chain.sh` (shell) |
| Out-of-manifest edits | `chain_util.py audit` — any changed file outside `write_files` → BLOCKED, no retry |
| Did it actually work? | `chain.sh` runs tests, a 10-symbol smoke run, the full run, then `checks.py` golden values |
| Retries | Max 2 builder sessions per WI; session 2 receives only the failure tail |
| Morning summary | `checks.py` writes numbers read from the output files into `reports/fib_swings/OVERNIGHT_REPORT.md` |

Golden values come from the PM's independent recompute (2026-11-06) — e.g. WI-021 must reproduce
EVAL bottom screen 0.2959 vs base 0.2619 and 2026 0.2436; WI-023's +10/−8/39d hit rate must fall
inside the bounds [0.403, 0.712] that daily MFE/MAE already imply. Checks were verified to REJECT
the current (buggy) pass-4 outputs.

## The per-WI prompt (what GLM receives)
```
Execute docs/kanban/in_progress/<WI>.md strictly within its locked file manifest (write_files).
Read ONLY that WI file and the files listed under read_only_files. Implement Section 2 literally:
every formula, constant, column name, file name, threshold and date in it is fixed - never
substitute your own, never add features, never tune parameters, never change thresholds. Tests use
synthetic data only. Do NOT run the full-universe job and do NOT read files under data/ or large
files under reports/. Run the exact test_command until it exits 0 (max one fix attempt after a
failure), append the Execution Telemetry footer to the WI file, then stop with a 2-line summary.
[attempt 2 only] PREVIOUS ATTEMPT FAILED. Your code is still on disk. Fix ONLY this failure,
change nothing else: <last ~25 lines of the failing test / smoke / full run / check>
```

## Stop rules
- Code/test/smoke/full-run/acceptance failure twice → WI moves to `docs/kanban/blocked/` with the trace; chain stops (later WIs depend on it). Code stays on disk uncommitted.
- Manifest violation → blocked immediately.
- Research verdicts (`VERDICT: FAIL`, `BLOCKED_PRECONDITION`) are results, not failures — chain continues.
- Discord ping (webhook, `scripts/notify_gate.sh --once`) on finish.

## Launch
From a shell on the VPS (survives logout):
```bash
cd ~/projects/signals
DRY_RUN=1 bash docs/workflow/briefs/2026-11-06-fib-overnight/chain.sh   # optional, ~10 s
setsid nohup bash docs/workflow/briefs/2026-11-06-fib-overnight/chain.sh > logs/fib_overnight/launch.out 2>&1 < /dev/null &
```
Resume after a fix: `START_AT=WI-023 bash .../chain.sh`. Different model: `MODEL=openrouter/<id> bash .../chain.sh`.
Progress: `tail -5 logs/fib_overnight/chain.out` (never tail the `*.jsonl` builder logs).

## Expected cost/time
5 builder sessions (+ up to 5 retries), GLM-5.3. Compute ≤ 25 min total; wall time ~2–5 h,
dominated by builder sessions (90-min cap each). Peak RAM per run logged (`/usr/bin/time -v`).

## Morning PM review (Hermes, not GLM)
Read `OVERNIGHT_REPORT.md` + `chain.out`; diff-audit each `feat(WI-0XX)` commit; adjudicate
verdicts; apply the doc corrections (LEARNINGS/WF_VALIDATION/DATA_INDEX) with regenerated numbers;
insert BOARD row; decision memo to admin. WI-026 (calibration + intervals) is NOT in this chain.
