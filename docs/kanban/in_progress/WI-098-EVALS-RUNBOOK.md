# WI-098-EVALS-RUNBOOK — watchdog close-out procedure (chain of 7 family evals)

Chain: `logs/wi098_chain.sh` runs `family_eval_ext.py --family <f> --resume` for
nr_flags, clv, cusum_flag, stoch_rsi, connors_rsi, fail_count, swing_levels with a
900 s idle gap between stages; per-stage markers `EXIT_<family>:<rc>` in
`logs/wi098_chain.log`; chain-level markers `CHAIN_DONE` / `CHAIN_STOP(CREDIT_STOP:<bal>)`.
Per-stage logs: `logs/wi098_run_<family>.out`. Checkpoints: `data/models/l0ext_eval/`.
Reports: `reports/l0ext_eval/`. Monitor: `~/.hermes/scripts/wi098_eval_watch.sh`
outputs RUNNING while the chain lives, FINISHED_* once, when it ends.

## Monitor semantics (the cron prompt fires only on output CHANGE)
- `RUNNING` → hard no-op: reply one line, do nothing, touch nothing.
- Any `FINISHED_*` → run the close-out below, conditioned on the variant.

## Close-out (FINISHED_DONE path)
1. Read `logs/wi098_chain.log`. For each stage with `EXIT_<f>:0`, verify
   `reports/l0ext_eval/<f>_summary.md` exists and its prune-probe section says
   family-only=OK; note survivors counts. Stages skipped by the pre-stage credit
   guard have no marker — they are NOT failures.
2. Families whose prune probe shows an empty symmetric diff (delta ≡ 0 by
   construction) need no fits — record that, do not re-run.
3. Non-zero `EXIT_<f>`: read `logs/wi098_run_<f>.out` tail (never dump full json),
   diagnose; if it is a transient kill, re-run that family detached and re-arm.
4. CREDIT_STOP / partial chain: DO NOT relaunch automatically. Report the remaining
   families + current credit balance and stop for admin pacing.
5. Bookkeeping in ONE doc-only commit (explicit paths only): BOARD — update the
   WI-098 row/ACTIVE block with per-family eval status (m, survivors, min
   cross-market delta, PROVISIONAL tag); PM_LOG — append bullets to the newest
   cycle (cycle 45) merging, do not create a duplicate cycle header; stage
   `reports/l0ext_eval/` is UNTRACKED — leave it out unless the WI names it.
6. Remove the cron job `wi098-eval-watchdog` AND both script copies
   (`~/.hermes/scripts/wi098_eval_watch.sh` + `logs/wi098_chain.sh`). Leave
   `logs/wi098_run_*.out` on disk as provenance.

## FINISHED_DEAD path
Chain died without a marker: check the last `STAGE_START` line and that stage's
run log; re-run ONLY that family detached (same launcher pattern) after verifying
its checkpoint state; re-arm nothing else.

## FINISHED_STOPPED path (credit guard tripped)
Report CREDIT_STOP balance, which stages completed (markers present + reports),
which remain; ask admin for pacing. Do not auto-relaunch.

## Never
- Never tail a full json-format opencode log or dump whole report files into context.
- Never `git add -A`; commit by explicit path only.
- Never edit frozen gate reports in place; new findings go to new paths.
