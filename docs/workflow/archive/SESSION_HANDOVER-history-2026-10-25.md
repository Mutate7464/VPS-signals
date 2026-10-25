# SESSION_HANDOVER — archived historical sections (moved 2026-10-25 doc-hygiene pass)

> Superseded live-handover content. Git history is the audit trail; these blocks
> were removed from the live file per WORKFLOW.md §7 (doc hygiene: delete superseded
> sections, never keep 'for audit' history blocks in the live doc).

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
