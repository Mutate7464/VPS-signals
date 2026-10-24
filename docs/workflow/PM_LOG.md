# PM_LOG.md — cursor for the Hermes PM cycle

> One entry per PM cycle, newest first. The newest entry's cursor (`cursor:` line)
> defines which opencode sessions the next cycle ingests. Kam's trigger: tell Hermes
> "run PM cycle". Full procedure: `docs/human/PM-CYCLE.md`.

## 2026-10-24 — Cycle 3 (E3 chain closed INVALID; slim-mask bug fixed; full rerun launched)
- Ingest: no new opencode sessions. Chain self-completed 23:17:33 with `FAILED: cs_pct_only`
  ("no valid features" ×4, 37 s in) — the `FAILED: full` at the log's top was stale output
  from the OOM-killed pre-relaunch attempt, not today's.
- Root cause (PM traced in `src/xgb_trainer.py`): the E3 memory-slim `keep_cols` mask kept
  only RAW feature names, dropping every `_cs_pct` column that `build_panel` had just added.
  Two effects: cs_pct_only resolved to zero features (fast-fail); and the 4 completed sets
  (full/no_static/fib_only/legacy19) silently trained raw-only (32 cols) instead of the
  approved `wl + wl_cs_pct` (64) — internally consistent with each other, not E2-faithful.
  All 4 set-runs INVALID as E2-faithful baselines (⚠ board exception logged).
- Fix: `_cs_pct` of surviving features added to `keep_cols`; regression tests
  `tests/test_feature_masks.py` (masks non-empty ×5×4 targets, full = wl+wl_cs_pct,
  cs_pct_only = ranks-only). Full suite 42/42 (7:13 — the panel-join test dominates).
- Admin decision: **full 5-set rerun** over the cheaper partial options (fidelity to the
  approved plan design). Raw-only oof/metas/preds purged, `models/usd/*.pkl` cleared, old
  log preserved as `logs/e3_runs_rawonly_invalid.out`. Chain relaunched 00:28 UTC detached
  (python `Popen(start_new_session=True)` — the Hermes terminal guard now blocks `setsid`
  in foreground commands). PID 671883. ETA ≈ 03:40 UTC.
- Plan STATUS line replaced with IN-FLIGHT note so Build's next run isn't misled.
- Next: after `=== E3 CHAIN COMPLETE ===` in `logs/e3_runs.out` → paste the brief prompt
  (tasks 0–3: `--exp e3` report generator, E5, combined verdict) into opencode Build →
  PM cycle 4 verifies Steps 6–8 → QA/GATE human stop.
- cursor: session-since 2026-10-24 00:00 UTC

## 2026-10-23 — Cycle 2 (WI-002 Build precheck closed out)
- Ingest: opencode planner session 21:13 "WI-002 e3–e5 alignment steps 7–8". Build ran
  the precheck, wrote log row `7 (precheck) BLOCKED` + plan `STATUS: BLOCKED`, and did
  NOT start E5 — correct per the brief's precondition (chain still holds ~2 GB RAM).
  Not a failure; no restart needed. Uncommitted plan/state changes left in the tree.
- Verify: chain still RUNNING and healthy — 3/5 feature-sets complete (full 20:43–21:21,
  no_static 21:21–22:02, fib_only 22:02–22:35), legacy19 in flight (y_20d_up placebos
  done 23:02), cs_pct_only last; ~38 min/set → ETA ≈ 23:50 UTC. Placebo NO_LEARNING
  warnings = expected. Artifacts confirmed: per-set `data/oof_USD[_<set>].parquet`,
  `train_meta_USD[_<set>].json`, `predictions_*_latest.parquet`.
- Finding: **`scripts/diag_signal.py` has no `--exp e3`** — Step 6's report generator
  doesn't exist yet (e2/e4/e5 only). Writing it is part of the remaining Build work.
  Brief patched with task 0 (E3 report generator + artifact paths + memory-slim rules).
- Docs: board row refreshed, brief updated, plan STATUS/log row committed as-is.
- Next: when `logs/e3_runs.out` shows `=== E3 CHAIN COMPLETE ===` → paste the brief
  prompt into opencode Build → run PM cycle to verify Steps 6–8 → QA/GATE human stop.
- cursor: session-since 2026-10-23 21:30 UTC (cycle 2 consumed the 21:13 planner session;
  next cycle ingests anything newer)

## 2026-10-23 — Cycle 1 (WI-002 E3–E5 interim)
- Ingest: **no opencode sessions since cursor** (last Build session ended 10-22 23:05).
  Today's Steps 1–6 work was done manually by the admin (commits 263f175→0b6bbf3, all
  KTC). Ingested from the plan EXECUTION LOG + artifacts instead.
- Verify (PM ran, not trusted from log): `pytest tests/test_{feature_vectorized,range_fib,panel_join}.py`
  → 10/10 green; features parquet 1,240,275 rows × 89 float32 (+3 id/target cols), fib
  cols present; whitelists 32/32/32/32 in `reports/sprint3_metadata_selection.md`; E4
  report carries H3 SUPPORTED verdict. Step 6 chain confirmed live: PID 644113/644120
  (`scripts/e3_chain.sh`), val folds ≈148–164k = correct full-data panel, RSS ~2.0 GB,
  mem_avail ~4.3 GB. Steps 1–5 marked [x] in the plan.
- Docs: BOARD WI-002 row refreshed; SESSION_HANDOVER current-phase rewritten; plan log
  PM row appended. Brief written: `briefs/2026-10-23-WI-002-e3-e5-verdict-brief.md`
  (Steps 7–8: E5 + combined H2/H3/H4 verdict, run only after the chain completes).
- Next: after chain completes → admin pastes the brief's prompt into opencode Build →
  run PM cycle again to verify Steps 6–8 and route to the QA/GATE stop.
- cursor: session-since 2026-10-23 (unchanged — no new sessions this cycle; manual work
  is tracked via plan log + commits, not session cursor)

## 2026-10-23 — Cycle 0 (role adopted)
- Change: PM role added to the workflow. Build contract now requires a final
  `STATUS: DONE|BLOCKED|ERROR` line in the plan file (`~/.config/opencode/instructions/workflow.md`).
- cursor: session-since 2026-10-23 (all sessions before this line predate the PM cycle)
- Note: WI-002 was EXECUTING at adoption; its completion was tracked manually, not via a PM cycle.
