# SESSION_HANDOVER.md — Live Context Ledger (agent → admin)

> **Update this file at the END of every working session.** Anyone (agent or admin) starting cold reads this first, then `docs/README.md` for the doc map. **For what-now/what-next, see `workflow/BOARD.md`** (the kanban); this file is state, the board is the queue.

- **Last Updated (UTC):** 2026-10-23 ~21:25 UTC (PM cycle 1)
- **Execution mode (from 2026-10-22):** admin drives work directly in VS Code + opencode; **Hermes verifies results and maintains the board/handover**. Phase 2 pacing deferred to next week by admin.
- **Current Phase:** **WI-002 E3–E5 in flight.** Admin fork approved 2026-10-23 (E3–E5, fib/range features, VIF 10 / MI pct 15). Steps 1–5 PASS and PM-verified: Hurst/entropy vectorized (4h10m → 4 min), 26 fib/range features added (raw = 89), trainer joins persisted parquet (no recompute), features rebuilt on FIXED 1,240,275-row data, whitelists 32/32/32/32, **E4 = H3 SUPPORTED** (continuous Spearman IC significant t +4.31/+3.27 on 15d targets while binary gates fail; ticker-prior AUC beats model → strong identity-signal component). Two bugs found & fixed en route (E3 OOM; E2-era index-misalignment truncation to 533k rows). Step 6 E3 ablation chain RUNNING detached (PID 644113, `logs/e3_runs.out`, ~2 h). Next: Step 7 (E5) + Step 8 (combined H2/H3/H4 verdict) → STOP for admin. Brief: `docs/workflow/briefs/2026-10-23-WI-002-e3-e5-verdict-brief.md`.

## Reconciled state (2026-10-23, supersedes the 2026-10-22 entry below)

| Item | Status | Evidence |
|---|---|---|
| WI-003 ingest Phase 1 + CAD | Done | `reports/sprint1_ingestion_audit.md` (546 USD + 350 CAD, ~97-98% coverage) |
| WI-002 Steps 1–9 (E2) | Done, committed through `f6f7c27` | plan EXECUTION LOG + `reports/diag_D002_e2.md` |
| Gate 4 | **FAIL** (all 4 targets, real universe) | `reports/sprint4_model_qa.md` |
| WI-008 quarantine triage | Analysis done 2026-10-23: of 72 dead-letter rows, 2 already clean (stale), ~44 show corp-action level-step signatures, ~26 flagged genuine-vol but several are actually restructuring artifacts (OVV/WES 2020-03-09) — per-case verification still needed | `reports/wi008_quarantine_triage.md` |
| BRK.B | **Resolved in data**: downloaded as `symbol=BRK B.parquet` (5,026 rows, 2006–2026, in the 508-ticker universe); audit CSV row stale | `IBKRDownload/data/audit_ingestion_usd.csv` (outdated) |
| ELE (CAD) | **Missing entirely** — empty response, no parquet, not in dead-letter list | `IBKRDownload/data/audit_ingestion_cad.csv` |
| Screener PDFs | Still structural demo only (WI-001 QA exception stands) | `reports/screener_*_20261021.pdf` |

## Open items (admin decisions / next actions)

1. **Pick the WI-002 fork: E3 / E4 / E5** (order optional; E4 cheapest — analysis on existing oof, no retraining). This gates all further model work.
2. **ELE re-download on M1 Mac** (IBKR Gateway side; empty response for 20Y TSE query — try different duration/barSize or conid route).
3. **WI-008 execution decision:** reinstate the 2 clean + how to handle the ~44 corp-action artifacts (split-adjust in loader vs keep quarantined). Needs a plan before next training run.
4. Phase 2 pacing restore (WI-004) — deferred to next week by admin; 3 clean runs prerequisite.

## Historical entry (2026-10-22) — kept for audit trail; facts above supersede it

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
