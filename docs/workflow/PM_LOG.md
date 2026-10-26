# PM_LOG.md — cursor for the Hermes PM cycle

> One entry per PM cycle, newest first. The newest entry's cursor (`cursor:` line)
> defines which opencode sessions the next cycle ingests. Kam's trigger: tell Hermes
> "run PM cycle". Full procedure: `docs/human/PM-CYCLE.md`.

## 2026-10-26 — Cycle 15 (WI-013 gate ACCEPT → DONE; WI-014 brief GO → planner dispatched)
- **GATE DECISION (admin, in-chat 2026-10-26): WI-013 ACCEPT — SIMPLE rec approved, both deviations accepted.** Canonical record = this entry; human stream `docs/human/briefings/2026-10-26-gate-WI-013-pipeline-hygiene.md`; board row → DONE (collapsed). No state to execute beyond the record.
- **WI-014 GO (admin, same in-chat message): "proceed with brief b9fa22e".** Brief was committed cycle 14 (`b9fa22e`); planner dispatched detached headless (`opencode run --agent planner --auto`, title "WI-014 plan", log `logs/wi014_planner.out`).
- **PM contract check: PASS.** Plan `docs/plans/2026-10-26-WI-014-factor-screener-pdf.md` = GOAL/CONSTRAINTS/STEPS 4 (each with acceptance + deterministic verify)/OUT OF SCOPE, matching brief b9fa22e; all brief acceptance items carried; frozen-artifact + host-limit constraints intact. Design `docs/workflow/designs/D-014-wi014-factor-screener-pdf.md` written alongside (M-sized item).
- **Planner deviation:** no log stub (planner cited its handoff contract; plan file carries an embedded EXECUTION LOG section instead). PM created `docs/plans/logs/WI-014-factor-screener-pdf.md` STATUS: PLAN so Build isn't misled.
- Board: WI-014 row added ACTIVE at DESIGN/PLAN, awaiting admin plan review before Build dispatch.
- cursor: `ses_e85a141e0ffec` (WI-014 planner session; ingested this cycle via plan artifacts + `logs/wi014_planner.out` tail — not full ingest).

## 2026-10-26 — Cycle 14 (WI-013: admin plan approval in-chat → Build dispatched → PM close)
- Admin approved + ordered execution in-chat ("execute WI-013"). Board row PLAN→EXECUTING→QA/GATE. Build dispatched detached (`opencode --agent build --auto`), log `logs/wi013_build.out`, EXIT:0.
- **Delivered (steps 1–5):** `src/market_cli.py` (default BOTH = USD→CAD sequential; explicit single; invalid rejected pre-write), 6 `wi011_*` scripts + `src/wi011` market-parametrized (dropped `MARKET="CAD"`), probe/train/eval/rank_assets/train_contrastive/check_inputs/launcher all market-aware with suffixed writes, F-2 `write_report(market)`, F-4 metadata rebuild `scripts/rebuild_wi013_metadata.py` (USD 71→67, CAD 91→87 cols; every surviving column `assert_frame_equal(check_exact=True)`; backups retained; `y_*` labels gone), CAD regression/summary/shortlist backfilled suffixed, default preflight writes `wi011_preflight_{USD,CAD}.md`.
- **Verified (PM, independently):** 58-file frozen-hash baseline intact after PM restore of regenerated `wi009c_{regression,summary}_CAD.json` (frozen wins); targeted `tests/test_wi013_*.py` 126 passed; Build full-suite log `pytest_exit=0`, 360 passed (7:38).
- **Open for admin gate:** deviation 1 — USD Step-0 checker baseline undeclared (checker reports-observes, CAD assertions unchanged, exit 0); deviation 2 — `e5_baseline.py` CLI default left CAD (plan scoped it to F-2 only). PM rec: ACCEPT both. Untracked `data/` left untouched (pre-existing hygiene item).
- Commit `5642819` (cycle-scoped, explicit paths). cursor: `ses_e86ef4e26ffe40` (Build run ingested this cycle: log rows + step outs above).
- Admin order in-chat ("iterate from this version, run both CAD + USD, note errors/perf/optimizations"), scope confirmed via clarify: **full depth incl. WI-011 on USD**, artifacts to `reports/wi012_*`, cycle-scoped commits. PM executed directly (no opencode dispatch — admin-ordered PM run).
- **F-1 ERROR fixed live:** `--horizon 20` NaN'd the whole e5 single-factor table (dropna hardcoded to fwd_15; 5 contaminated dates → non-NaN-aware mean). Fixed `src/factors/e5_baseline.py:99`, regression `tests/test_e5_baseline_horizon_nans.py` 6/6.
- **Results:** USD factor signal generalizes (mom +0.0209 t+6.00 / vol −0.0158 t−5.11, h15); labels bottleneck cross-market (USD probe 0/5 bar); continuous ridge FAIL on USD; WI-011 USD chain EXIT:0 survivors=0 → NO_TRADE confirmed both markets. Frozen gate artifacts restored after every stage (3 overwrite incidents handled).
- Findings backlog F-2..F-5 + perf profile (nothing hours-scale in current route) in `reports/wi012_iteration_notes.md`; board WI-012 row DONE. CAD universe now 335 symbols (post-WI-010b reinstatements) — frozen baselines unchanged, current-universe numbers in wi012 reports.
- cursor: unchanged (`ses_e8ecc8dc`); no new opencode sessions this cycle.
- **GATE DECISION (admin, in-chat 2026-10-26): WI-012 ACCEPTED as DONE** with F-2..F-5 backlog carried forward; admin asked for the WI-013 explanation before deciding on it. Canonical record = this entry; board row cites it.
- **WI-013 GO (admin "proceed with a", same cycle; F-3 amended: default = BOTH USD+CAD unless specified):** brief written + committed; planner dispatched headless (`ses_e86f382b2ffe`, ~2 min) → plan + log stub STATUS: PLAN; PM contract check PASS. Board WI-013 → PLAN, awaiting admin plan approval before Build. PM rec adopted: Build executes in a fresh session.
