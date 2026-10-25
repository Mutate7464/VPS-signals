# PM_LOG.md — cursor for the Hermes PM cycle

> One entry per PM cycle, newest first. The newest entry's cursor (`cursor:` line)
> defines which opencode sessions the next cycle ingests. Kam's trigger: tell Hermes
> "run PM cycle". Full procedure: `docs/human/PM-CYCLE.md`.

## 2026-10-25 — Cycle 8 (WI-008 Build + repair verified; human reinstate/keep gate open)
- Ingest: one work session past cursor — `ses_e8f2423d` ("WI-008 per-case quarantine
  verification", deepseek-v4.1-flash, 161 msgs) covering BOTH the initial Build (02:2x,
  8 steps, report 72 rows) and the admin-supervised repair pass (03:5x–04:00). Plus one
  trivial PM smoke test (`ses_e8f0ea4d`, "Reply with exactly OK" on new planner model
  openai/gpt-6-luna — config validation, no repo work).
- PM verification (ran, not trusted from log): `uv run pytest tests/test_quarantine_analysis.py -q`
  → 6 passed; full suite re-run independently → **62 passed** (453.86s, exit 0) — matches
  Build's claim. Report integrity: 72 data rows, verdict summary 17 REINSTATE /
  55 KEEP_QUARANTINED, size unchanged from 02:30 baseline → byte-identical claim holds.
- Cycle-7 finding (2/6 unit tests failing, STATUS DONE dishonest) resolved: Build fixed
  both implementation bugs (level-step unity guard; multi-day event window), assertions
  untouched, under admin decision **option b** — tests-green fix kept, report NOT rewired
  (wiring flips 22/72 recommendations → over the 5-verdict human gate, correctly escalated).
  3-way classifier divergence logged by Build as WI-010 (backlog).
- Commit-hash hygiene: Build amended its pre-push commit `6e004df` → `459ee44`; plan files
  cited the stale hash — PM patched both plan STATUS lines to `459ee44`.
- Config (outside repo): opencode planner model → `openrouter/openai/gpt-6-luna`
  (was qwen/qwen3-coder, admin direction 2026-10-25); `docs/README.md` workforce line
  synced in this cycle's commit. Verified: JSONC parses, model resolves, live smoke OK.
- Board: already updated by Build — WI-008 → **QA/GATE** (owner: admin, human
  reinstate/keep gate on the report); WI-010 (classifier consolidation) added to BACKLOG;
  WI-009b next in queue after the gate.
- cursor: session-since `ses_e8f0ea4d` (2026-10-25 02:43 UTC; cycle 8 consumed the
  WI-008 Build+repair session `ses_e8f2423d` and the gpt-6-luna smoke test `ses_e8f0ea4d`).
- Gate outcome: admin APPROVED WI-008 completion later in cycle ("run pm cycle. approve
  completion") — board row moved to DONE. Per-row reinstate/keep EXECUTION remains a
  human gate (no auto-reinstatement); classifier consolidation = WI-010 (BACKLOG).
- Next: WI-009b Build (top READY row) — contrastive ranking vs E5 factor baseline,
  seed = gate-brief APPROVE branch.

## 2026-10-25 — Cycle 7 (admin gate decision: WI-009 APPROVED; WI-008 do-next; WI-009b queued)
- Admin direction: "approved 009, move to next item" (2026-10-25). WI-009 gate → DONE
  (APPROVED; continuation boarded as WI-009b). Next item per PM's proposed order: WI-008.
- Brief written: `docs/workflow/briefs/2026-10-25-WI-008-quarantine-percase-brief.md` —
  per-case evidence report (level-step test + volume corroboration), 72 rows, recommended
  action per row; human gate on reinstate/keep; no quarantine mutation; ELE owner-action.
- Brief folds in the classifier's known defects: 2020-03-09 COVID cluster classified
  inconsistently across the two classes (OVV/WES vs CVE/APA/OXY/MTDR/PR/SM same date);
  GME genuine; GOOG 2014-04 likely artifact; ICL negative prices = FIX_DATA.
- Board: WI-009 → DONE table (gate: approved, commit 19795ac + cycle-6 verification);
  WI-008 → ACTIVE/PLAN do-next; WI-009b → ACTIVE/READY queued after WI-008; header cycle 7.
  (Backlog-row delete fused with the WI-005 row mid-patch — the known table-fuse pitfall;
  repaired immediately, verified in diff.)
- cursor: no new opencode sessions since ses_e8f8c752dffejE7GTKy5IcSDFk (2026-10-25 00:26 UTC) — unchanged.
- Next: admin pastes the WI-008 Build prompt (below) into opencode → planner/Build run →
  PM cycle 8 verifies → reinstate/keep human gate on the evidence report.

## 2026-10-25 — Cycle 6 (WI-009 verified at gate; human decision pending)
- Ingest: 5 sessions past cursor — ses_e8fb0881 (WI-009 Build, deepseek-v4.1-flash, the tmux session),
  ses_e8f8c752f (retro review WI-002 diag commits) + ses_e8f8c752d (pre-commit review WI-009 diff),
  plus 2 trivial (10-24 "OK"/"Conversation title", no work). Commit 19795ac.
- Verify (PM ran, not trusted from log): `uv run pytest -q tests/test_e5_split_no_leak.py
  tests/test_pair_sampler.py` → 11/11 green (leak regression + sampler);
  reports/wi009_top10_CAD.csv → 10 rows + header, ranks 1..10, no NaNs, 7/10 REITs;
  reports/wi009_e5_baseline_CAD.md carries the POST-leak-fix numbers (ridge −0.0046 t−1.26,
  logit +0.0226 t+4.44) matching the plan log; gate brief exists (6.3 KB, 00:34).
- Key finding (sample, gate-relevant): the E5 split leak — reviewer #1 cleared the
  pd.factorize-codes mask as "internally consistent", reviewer #2 called it a blocker;
  Build adjudicated by experiment (codes ≠ positions for 100% of CAD rows, max gap 1839;
  staggered fixture pulled 40 held-out rows into train). Reviewer #1 was wrong. Fix is
  regression-locked in tests/test_e5_split_no_leak.py; contaminated CAD multivariate
  numbers corrected in-report; USD report regenerated for truth-in-reporting.
- Verdict: WI-009 build DONE, all stated acceptance criteria pass, BUT model val rank-IC
  +0.043 (t+2.63) < rev_1m |IC| 0.157 (t−4.26) on the same 10 held-out dates → GATE
  stands (APPROVE WI-009b / HOLD / REJECT), per docs/human/briefings/2026-10-25-gate-WI-009-contrastive-ranking.md.
- Board: already at GATE (Build updated it correctly); no PM correction needed.
  tech_approach/2026-W44/plans/contrastive-learning-plan.md is STALE (STATUS: PLAN, TBD
  log row) — docs/plans/2026-10-24-WI-009-contrastive-learning.md is the executed plan;
  flagged, not deleted.
- cursor: session-since ses_e8f8c752dffejE7GTKy5IcSDFk (2026-10-25 00:26 UTC)

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
- Addendum (same cycle; admin: "expand on open risks, integrate before wunning 009 / is pytorch usable
  wrt VPS, options/optimization? alt? / integrate review pass into current run / expand on E5 / switch
  CAD dataset for next sprint/build"). Executed and verified by PM probes:
  (1) PyTorch usable on this VPS — torch 2.14.1+cpu installs on Python 3.14 (CPU wheel); smoke test 50
  epochs × 4096 pairs × 89-dim = 0.40 s, peak RSS 0.33 GB, threads capped at 2, 810 MB disk. Alt offered:
  xgboost rank:pairwise on pairwise-difference features (existing dependency). (2) E5 sign flip
  root-caused — probe reproduces the report exactly (ridge +0.0083/t+2.25, logit −0.0080/t−2.78; no
  keying bug); driver is target definition: ridge = pooled continuous magnitude (vol_20 +0.066 loading
  is a between-date regime effect), logit = within-date direction; loadings flip sign on the
  liquidity/vol cluster; with predict_proba the logit is −0.0055 (t −1.67, ns) — class-label eval
  overstated it. run_e5 one-line predict_proba fix folded into WI-009 Deviations. (3) Reviewer pass
  integrated into the WI-009 run (retro d957d43/d5c5441 + pre-commit). (4) Dataset switched to CAD —
  stale 2026-10-21 CAD features/targets/catalog (432 KB vs USD 503 MB; predates fib expansion AND the
  R-08 index fix) flagged for rebuild as plan Step 0; ELE missing. Brief rewritten with all constraints
  (dataset, framework, reviewer, E5); Build prompt v2 issued.
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
