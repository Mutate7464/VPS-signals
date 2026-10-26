# PM_LOG.md — cursor for the Hermes PM cycle

> One entry per PM cycle, newest first. The newest entry's cursor (`cursor:` line)
> defines which opencode sessions the next cycle ingests. Kam's trigger: tell Hermes
> "run PM cycle". Full procedure: `docs/human/PM-CYCLE.md`.

## 2026-10-26 — Cycle 13 (WI-012: PM-executed cross-market validation run, admin-ordered in-chat)
- Admin order in-chat ("iterate from this version, run both CAD + USD, note errors/perf/optimizations"), scope confirmed via clarify: **full depth incl. WI-011 on USD**, artifacts to `reports/wi012_*`, cycle-scoped commits. PM executed directly (no opencode dispatch — admin-ordered PM run).
- **F-1 ERROR fixed live:** `--horizon 20` NaN'd the whole e5 single-factor table (dropna hardcoded to fwd_15; 5 contaminated dates → non-NaN-aware mean). Fixed `src/factors/e5_baseline.py:99`, regression `tests/test_e5_baseline_horizon_nans.py` 6/6.
- **Results:** USD factor signal generalizes (mom +0.0209 t+6.00 / vol −0.0158 t−5.11, h15); labels bottleneck cross-market (USD probe 0/5 bar); continuous ridge FAIL on USD; WI-011 USD chain EXIT:0 survivors=0 → NO_TRADE confirmed both markets. Frozen gate artifacts restored after every stage (3 overwrite incidents handled).
- Findings backlog F-2..F-5 + perf profile (nothing hours-scale in current route) in `reports/wi012_iteration_notes.md`; board WI-012 row DONE. CAD universe now 335 symbols (post-WI-010b reinstatements) — frozen baselines unchanged, current-universe numbers in wi012 reports.
- cursor: unchanged (`ses_e8ecc8dc`); no new opencode sessions this cycle.

## 2026-10-26 — Cycle 12 (quiescent close — post-commit Build residue only)
- Ingest: 0 new opencode sessions past cursor `ses_e8ecc8dc` (newest session remains the WI-011 Build 21:16, already ingested cycle 11). No manual admin work found in git.
- Residue handled: WI-011 Build's post-commit chain re-run had left timestamp-only churn in 3 `reports/wi011_*` files (restored to committed state — frozen gate record wins) and a second STATUS line in the log claiming "nothing committed"; superseded — gate decided ACCEPT, committed `ce59331`/`f59287c` (board/log updated with a PM-set line).
- Untracked WI-008 quarantine scripts + per-case report left untouched (deliberate, pending WI-010 consolidation per board).
- Rotation duty done this cycle: cycles 9–11 archived to `docs/workflow/archive/PM_LOG-2026-10-cycles-9-11.md`.
- **Admin GO "WI-010" (same cycle):** brief written + committed (`docs/workflow/briefs/2026-10-26-WI-010-quarantine-consolidation.md`), planner dispatched headless (`ses_e8972ffc`, ~2.5 min) → plan `docs/plans/26-W44-WI-010-quarantine-consolidation.md` + ADR `docs/workflow/designs/D-010-quarantine-consolidation.md`. PM contract-check PASS (5 steps, acceptance + deterministic verify each, read-only constraints, STOP at human gate; baseline anchors `| REINSTATE | 17 |` / `| KEEP_QUARANTINED | 55 |` verified present). Note: planner could NOT read `docs/human/**` (path rule) — plan relies on the brief's summary of the escalation evidence and mandates the persistence-guard-only anchor experiment BEFORE any rule change. Board: WI-010 → PLAN (awaiting admin plan approval before Build).
- **WI-010 Build DONE (same cycle, admin "build"):** headless Build `ses_e89700997ffeKBvVD2fV2YyHGF` executed steps 1–5 → STATUS: DONE. Deliverable `reports/wi010_quarantine_consolidated.md`: 36 flips vs 17/55 baseline (symbols in §6), anchors re-derived (GME + 7/8 crash cluster → REINSTATE; OXY/USD residual SPLIT_LOOKALIKE, disclosed + characterization test; ICL/USD → FIX_DATA from non-positive closes), read-only CB-01 CLEAN_NOW check added (2 candidates, TRI/SPCX flagged as CB-02 — CLEAN_NOW can't clear CB-02). DEVIATIONS: duplicate scripts stubbed not deleted (rm denied to agents — admin action listed on board); board left in PLAN during exec (admin instruction), PM moved it to QA/GATE post-hoc. PM re-verified: targeted 38 passed (own run), full suite 223 passed EXIT:0 (own detached run `logs/wi010_full_suite.out`), CSV + WI-008 baseline sha256 unchanged.
- **WI-010 gate: DECIDED — ACCEPT ALL** (admin "accept all", same day). Report recommendations stand (36 flips); OXY/USD residual accepted (no rule tightening); stub `rm` executed by PM (rm denied to opencode agents, not to PM under admin authorization) + verified: report regen exit 0, 38 targeted tests pass, CSV sha unchanged. Recorded BOTH streams: gate decision `docs/human/briefings/2026-10-26-gate-WI-010-quarantine-consolidation.md`; board row DONE. **Decision is a record, not execution** — quarantine CSV untouched; applying reinstatements awaits explicit admin order (candidate small follow-up WI).
- **WI-010b reinstate EXECUTION (admin "apply reinstatements", same cycle):** 47 REINSTATE rows removed from `data/dead_letter_tickers.csv` (72→25; kept rows byte-identical, CRLF preserved; backup `data/dead_letter_tickers.backup-20261026.csv`). New `data/adjudicated_tickers.csv` (72 verdicts, cited) + `is_adjudicated_reinstate` skip in `state_manager.quarantine_ticker` — reinstated tickers cannot bounce back on later audits. `tests/test_adjudicated_reinstate.py` 9 tests incl. LIVE no-append proof. PM-verified: targeted 47 passed; consumers CAD 12/USD 13 excluded (GME in, OXY out); full suite **232 passed EXIT:0** (`logs/wi010b_full_suite.out`). Data CSVs stay untracked per repo convention. Records: WI-010b log + gate-brief execution section (both streams).
- cursor: `ses_e89700997` (WI-010 Build). Gate closed + executed.

## 2026-10-25 — Cycle 11 gate close (admin: WI-011 ACCEPT — documented negative)
- **WI-011 gate: DECIDED — ACCEPT** (admin "accept results", same day). Closed
  DONE as documented negative: "none survive costs at this universe size" →
  screener NO_TRADE default; conditions = descriptive context only. Full
  suite re-run by PM: **191 passed, EXIT:0** (detached, logs/wi011_full_suite.out).
- Recorded in BOTH streams: gate brief + admin doc directives
  `docs/human/briefings/2026-10-25-gate-WI-011-condition-first.md`; board row
  WI-011 → DONE (moved to ACTIVE table, BACKLOG row removed).
- **Doc conventions adopted (admin, WORKFLOW.md §4):** plans + tech files →
  `YY-WW-…` naming (26-W43-WI-011-…); tech_approach keeps `YYYY-Www` week
  dirs; `docs/ingest/CHANGELOG.md` absorbs `ib4-changelog.md`; files small +
  flat (token discipline). Existing files NOT mass-renamed yet — pointer
  breaks; migration = WI-012 proposal.
- **Ingestion workflow (admin question, answered from repo):** Mac (M1, IB
  Gateway) runs `IBKRDownload/ibkr_ingest.py` (ib_async, Mac-only) → data →
  `IBKRDownload/sync_back.py` rsyncs Mac → VPS `data/raw_ohlcv/market=<CAD|
  USD>/` (gitignored, latest 2026-10-22) → VPS pipeline builds
  `data/features/*.parquet`. IBKRDownload COPIES via rsync; Mac stays the
  download host. `docs/ingest/ibkrdownload.md` is a stray 45-line fragment of
  the 686-line `IBKRDownload/IBKR_Download_Optimization_Plan.md` — delete or
  merge candidate (WI-012).
- WI-011 artifacts frozen at `ce59331`; PR branch
  `sync/wi011-condition-first-meta-analysis` (compare URL handed to admin).
- cursor: unchanged `ses_e8ecc8dc`; cycle's opencode sessions (planner, Build)
  ingested directly via artifacts.

---

> **Archive pointers:** cycles 0–8 → `docs/workflow/archive/PM_LOG-2026-10-cycles-0-8.md`;
> cycles 9–11 → `docs/workflow/archive/PM_LOG-2026-10-cycles-9-11.md`.
> Rotation rule (WORKFLOW.md §7): keep the last 2 cycles here; older entries move to the
> archive at the weekly review. Read only the newest entry + its `cursor:` line (WORKFLOW.md §11).
