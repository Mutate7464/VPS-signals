# SESSION_HANDOVER.md — Live Context Ledger (agent → admin)

> **Update this file at the END of every working session.** Anyone (agent or admin) starting cold reads this first, then `docs/README.md` for the doc map. **For what-now/what-next, see `workflow/BOARD.md`** (the kanban); this file is state, the board is the queue.

- **Last Updated (UTC):** 2026-10-25 ~00:25 UTC (PM cycle 5 + addendum: WI-002 closed — pivot to WI-009; CAD dataset switch; torch verified; E5 root-caused; repo cleanup + tech_approach integrated week-based)
- **Execution mode (from 2026-10-22):** admin drives work directly in VS Code + opencode; **Hermes verifies results and maintains the board/handover**. Phase 2 pacing deferred to next week by admin.
- **Current Phase:** **WI-009 in PLAN (do-next); WI-002 closed 2026-10-24 by admin gate decision: pivot to WI-009.** E3–E5 verdicts stand (H3 yes / H2 no / H4 no): signal exists in continuous fwd-ATR-return space; binary labels/within-date gates are blind to it; classic factors are present — so the pivot goes to D-003 Option 2 (hybrid technical-factor, contrastive pairwise ranking for top-10 recommendations, IBKR technical data only), with E5's factors as mandatory baselines. **Dataset switched to CAD (admin 2026-10-24):** stale 2026-10-21 CAD features/targets/catalog must be rebuilt as plan Step 0 (they predate the fib expansion and the R-08 index fix); ELE missing. Framework: PyTorch CPU PM-verified usable on this VPS (torch 2.14.1+cpu, 0.40 s smoke, 0.33 GB, 2 threads); E5 sign flip root-caused (target-definition artifact — see RISKS R-04). tech_approach docs restructured to week-based `YYYY-WW` (2026-W44); the draft WI-009 plan needs a planner pass (per-step verification commands, D-003 scope reconciliation, reuse of the 89 existing features) before Build.

## Reconciled state (2026-10-24, supersedes the 2026-10-23 entry below)

| Item | Status | Evidence |
|---|---|---|
| WI-002 E3-E5 diagnostic cycle | Closed 2026-10-24 — gate decision: pivot to WI-009 | `reports/diag_D002_summary.md`, e2–e5 reports; PM cycle 4 verification (ee6f93e) |
| WI-003 ingest Phase 1 + CAD | Done | `reports/sprint1_ingestion_audit.md` (546 USD + 350 CAD, ~97-98% coverage) |
| Gate 4 | **Still FAIL** (all 4 targets, real universe) | `reports/sprint4_model_qa.md` |
| WI-008 quarantine triage | Analysis done 2026-10-23: of 72 dead-letter rows, 2 already clean (stale), ~44 show corp-action level-step signatures, ~26 flagged genuine-vol but several are actually restructuring artifacts (OVV/WES 2020-03-09) — per-case verification still needed | `reports/wi008_quarantine_triage.md` |
| BRK.B | **Resolved in data**: downloaded as `symbol=BRK B.parquet` (5,026 rows, 2006–2026, in the 508-ticker universe); audit CSV row stale | `IBKRDownload/data/audit_ingestion_usd.csv` (outdated) |
| ELE (CAD) | **Missing entirely** — empty response, no parquet, not in dead-letter list | `IBKRDownload/data/audit_ingestion_cad.csv` |
| Screener PDFs | Still structural demo only (WI-001 QA exception stands) | `reports/screener_*_20261021.pdf` |
| WI-009 Technical Approach | Design accepted (admin pivot 2026-10-24); draft plan awaiting planner pass | `docs/workflow/designs/D-003-technical-trading-approach.md`, `docs/tech_approach/2026-W44/briefs/contrastive-learning-brief.md`, `docs/tech_approach/2026-W44/plans/contrastive-learning-plan.md` |
| Model Escalation Config | Final state verified via `opencode debug agents`: Build base `deepseek-v4.1-flash`; escalation v4.1-pro → gemini-4-argon → opus-5.5 (human-gated) | `~/.config/opencode/opencode.jsonc`, `~/.config/opencode/instructions/escalation.md`, consolidated record `docs/human/interventions/2026-10-24-opencode-build-model-escalation.md` |

## Open items (admin decisions / next actions)

1. **WI-009 planner pass → EXECUTING** — paste the cycle-5 Build prompt v2 (PM cycle report) into opencode; refine the draft plan to workflow-contract format on **CAD** (admin switch 2026-10-24 — stale 2026-10-21 CAD features/targets/catalog must be rebuilt as plan Step 0), then execute.

2. **Framework: PyTorch CPU verified usable** (PM probe 2026-10-24: torch 2.14.1+cpu on Python 3.14; 0.40 s smoke, 0.33 GB RSS, 2 threads, 810 MB disk) — planner picks torch (Siamese pairwise) or xgboost `rank:pairwise`; either fits guardrails. E5 sign flip root-caused (target-definition artifact; class-label eval overstated it — logit −0.0055/t−1.67 with proper scores); one-line `predict_proba` fix folded into WI-009 Deviations.

3. **ELE re-download on M1 Mac** (IBKR Gateway side; empty response for 20Y TSE query — try different duration/barSize or conid route).

4. **WI-008 execution decision:** Reinstate the 2 clean + how to handle the ~44 corp-action artifacts (split-adjust in loader vs keep quarantined). Needs a plan before next training run.

5. Phase 2 pacing restore (WI-004) — deferred to next week by admin; 3 clean runs prerequisite.

## Historical entry (2026-10-23) — kept for audit trail; facts above supersede it

## Agent system (since 2026-10-22)
- Model tiers: Build=DeepSeek V4 Pro · Plan=Sonnet 5.5 (writes `docs/plans/`) · reviewer=flash (incl. gate-compliance check) · guide=Sonnet 5.5 (mentor, read-only, repo-grounded teaching) · scribe=flash (maintains `docs/human/` human stream) · troubleshooter=Opus 5.5 (evidence-bundle escalation, BLOCKED instead of guessing).
- Workflow contract in `~/.config/opencode/instructions/workflow.md`: plans are files; Build executes from the board-named plan; one task = one session; board protocol enforced.
- **Two doc streams:** agent stream (terse, `docs/` root) vs human stream (`docs/human/GUIDE.md`, narrated — never loaded into agent context; regenerate via scribe).
- Spend to date ≈ $6.75 (3 active days). Verify agents: `opencode debug agents`. Note: `opencode run --agent X` ignores per-agent model config (runs default) — TUI Task-tool delegations honor it (verified for reviewer/troubleshooter; guide/scribe assumed by mechanism, verify via child-session export on first real use).

## Active anomalies / quarantined tickers
- None known. Historical (2026-10-22 baseline): 96 IBKR error-162 cancellations — Phase 1 retry logic targets these.

---

# Historical entry (2026-10-21 23:40 UTC) — kept for audit trail; facts above supersede it

- **Active Sprint & Gate Status (then):** Sprint 1 complete — all `ibkrdownload/` scripts made self-contained. ibkr_ingest.py not yet run at time of writing.
- **Key changes that session:** `opt.csv` → `IBKRtemp.csv` rename (0 refs remaining); `_parse_tc_csv()` rewritten with `csv.reader` (embedded commas); `tc_rating` preserved in watchlist + sector_map; all 3 scripts self-contained (paths resolved from `Path(__file__).parent`); FutureWarning fix in benchmark row concat; dry-run: USD 552 tickers (505 sectors), CAD 359 (344 sectors).
- **M1 Mac layout:** copy `ibkrdownload/` contents into one folder (e.g. `~/Downloads/IBKR/`), run scripts from there.