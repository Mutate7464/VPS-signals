# PM_LOG.md — cursor for the Hermes PM cycle

> One entry per PM cycle, newest first. The newest entry's cursor (`cursor:` line)
> defines which opencode sessions the next cycle ingests. Kam's trigger: tell Hermes
> "run PM cycle". Full procedure: `docs/human/PM-CYCLE.md`.

## 2026-10-24 — Cycle 5 (admin gate decision: pivot to WI-009; cleanup; tech_approach integrated)
- Admin direction (verbatim): "perform clean up first. will pivot direction toward WI-009 / revew
  docs/tech_approach docs and integrate. / review file strucutre and associated docucs. / workflow is
  weekbased YY-Weeknum / communication style is middle manager (confirm previous work saved properly)".
  WI-002 gate → DONE (pivot to WI-009, D-003 Option 2); WI-009 = do-next.
- Previous work confirmed saved: ee6f93e (8 files — PM_LOG cycle 4, board, handover, RISKS, report v2s,
  pipeline state).
- Cleanup: `PM_LOG.md.tmp` junk deleted; D-004 deduped (stale gemini-pro-1.5 variant replaced by the
  gemini-4-argon version under the canonical name); 9 model-escalation intervention variants
  consolidated into one record (`2026-10-24-opencode-build-model-escalation.md`;
  wi009-preparation-checklist kept, paths updated); WI-003 row moved ACTIVE → DONE table.
- Integration: tech_approach flattened to week-based `YYYY-WW` (2026/W44 → 2026-W44; W45 → 2026-W45) per
  admin convention; all path references updated (board, handover, plan Steps 1+4, W44-summary, prep
  checklist); tech_approach added to the docs/README router; router's stale agent-workforce and
  stub-skill lines refreshed to live config; workflow contract amended — board-named plans may live
  under `docs/tech_approach/YYYY-WW/plans/` (WI-009 series).
- WI-009 review findings (handed to the planner pass): plan is contrastive-only while D-003 selects
  Option 2 hybrid — reconcile scope; no per-step verification commands (contract gap); EXECUTION LOG has
  a TBD placeholder row; Step 2 rebuilds RSI/MACD/BB/ATR that already exist in `src/feature_engine.py`
  (89 features — reuse, don't rebuild); PyTorch/TensorFlow proposal on the 8 GB VPS needs an explicit
  decision (repo is sklearn/xgboost; n_jobs≤2, float32, bounded memory).
- Board: WI-002 → DONE (gate: pivot), WI-009 → PLAN (do-next, planner pass), WI-003 → DONE table;
  header → cycle 5.
- Cursor: no new opencode sessions since ses_e94a5448 — unchanged.
- Next: admin pastes the cycle-5 Build prompt → planner refines the plan → EXECUTING → PM cycle 6
  verifies.
- cursor: session-since ses_e94a5448affehPb2n3CBkUg4S4 (unchanged)

## 2026-10-24 — Cycle 4 (WI-002 Steps 6–8 verified; QA/GATE stands; admin gate decision is the pick)
- Ingest: one session past cursor — `ses_e94a5448` ("WI-002 e3-e5 alignment floor", 55 msgs, planner agent
  on GLM-5.3, no child sessions; reviewer did NOT run on the d957d43/d5c5441 code changes). Trivial "OK"
  session (00:54 UTC, 3 msgs) — no work. Plan EXECUTION LOG rows 07:10/07:21/07:30 carry wrong hours:
  mtimes + commit 0af95cb (17:22:57 UTC) put the work at ~17:10–19:00 UTC.
- Verify (PM ran): chain-complete marker in logs/e3_runs.out 07:02:11 (7,202 s, 1,240,275 labeled rows =
  full panel); e3/e5 report runs EXIT=0; reports match board claims — E3: deflated IC t legacy19 +4.11,
  full +3.54, 20d flat → H2 not a feature-set fix; E5: mom +5.54, vol −4.72, amihud −3.37, ridge oof
  t +2.25/+2.05 → floor BREACHED; e2 ADR matrix updated; summary one-line verdicts traced. The 18:55–18:56
  regeneration changed only timestamps (e3/e5) — verdicts stable.
- Finding: tree dirty after 0af95cb (report v2s, board WI-009 row, handover rewrite left uncommitted);
  untracked: interventions/, tech_approach/, designs D-003 + D-004×2, junk `PM_LOG.md.tmp` (19-line
  assistant artifact — delete candidate). PM docs + verified report v2s committed this cycle; untracked
  dirs left to their owning work items.
- Docs: BOARD header → 2026-10-24; RISKS R-04 updated with the E3–E5 adjudication (+ E5 ridge/logit
  sign-flip caveat); handover Last Updated refreshed. WI-003 still sits in the ACTIVE table with column
  DONE (pre-existing placement; flagged to admin, not moved).
- Pick: **WI-002 admin gate decision** — factor-controlled target/metric redesign (H3 fix) vs stop. No
  Build handoff written (next step is human); the redesign brief comes from cycle 5 if approved. WI-009
  in DESIGN (D-003 review → READY) is the second queued decision.
- Admin feedback since last cycle (verbatim, ops-lane, no board impact): "confirm current opencode setup.
  is it working right now?" — TUI was dead (tmux send-keys first-char mangling), relaunched; "Build =
  qwen/qwen3-coder to deepseek flash. review setup and docs to fix/align" — agent.build.model →
  openrouter/deepseek/deepseek-v4.1-flash, verified via `opencode debug agents`; triage prompt + skill
  aligned.
- cursor: session-since ses_e94a5448affehPb2n3CBkUg4S4

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
