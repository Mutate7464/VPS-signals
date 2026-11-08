# BOARD.md — flat queue (single source for "what now / what next")

> Rules: `WORKFLOW.md` §2. Row format: `designs/D-020` §5. Kanban dirs: `docs/kanban/{ready,in_progress,blocked,done}/`.
> Full pre-flat board (2026-11-07, 16 KB): `archive/BOARD-2026-11-07-pre-flat.md`.

**Last updated:** 2026-11-08 — Lean HITL workflow (D-020) applied; DONE rows demoted; PM_LOG rotated to 2 cycles. **Next:** no WI staged. Conflict unresolved: cycle 25 header said "Next: WI-030 (exit policy)"; the WI-028 row said "WI-029 next". Admin to order.

## ACTIVE
- [WIP] none (EXECUTING = 0)
- [TODO] none (`docs/kanban/ready/` empty)
- [BLOCKED] none (`docs/kanban/blocked/` empty)

## DONE (last 7 days)
- [DONE] WI-028 | fib entry-window (stage 2a) | G-001 | INCONCLUSIVE; k=0 dominates; **at-bottom entry recommended** (PM-verified)
- [DONE] WI-027b | fib regime unsupervised GMM | G-001 | FAIL; soft probs supplementary; rule-based labels chosen
- [DONE] WI-027 | fib regime labels | G-001 | PASS; up_high/USD +22.75pp; chop_normal/ALL +3.89pp
- [DONE] WI-021–025 | fib overnight chain | G-001 | ALL_DONE 2026-11-06; **PM review pending**; WI-024 research verdict BLOCKED_PRECONDITION (policy-null); report `reports/fib_swings/OVERNIGHT_REPORT.md`
- [DONE] WI-020 | kanban lock protocol | G-003 | merged into WORKFLOW §2/§9; commit `a5c1ead`

## DONE (older, one line each; evidence in git and `docs/human/briefings/`)
- [DONE] WI-019 | MVP closeout | G-001 | gate ACCEPT 2026-11-02; suite 662 EXIT:0
- [DONE] WI-018 | condition-first first_touch_34 USD | G-001 | ACCEPT; documented negative (G2 wall); NO_TRADE
- [DONE] WI-017 | brute-force target/feature confirmation | G-001 | ACCEPT; confirmation delivered
- [DONE] WI-016 | triple-barrier + meta shortlist (CAD) | G-001 | ACCEPT 2026-10-31; 133 TRADE / 15 NO_TRADE; paper-track behind human gate
- [DONE] WI-015 | performance analytics panel | G-001 | ACCEPT 2026-10-29
- [DONE] WI-014 | E5 factor screener CSV + PDF | G-001 | ACCEPT 2026-10-28
- [DONE] WI-013 | pipeline hygiene, market routing | G-003 | ACCEPT 2026-10-26
- [DONE] WI-012 | cross-market validation | G-001 | NO_TRADE cross-market confirmed; `reports/wi012_iteration_notes.md`
- [DONE] WI-011 | condition-first meta-analysis | G-001 | closed negative; NO_TRADE default
- [DONE] WI-010 | quarantine classifier consolidation | G-002 | ACCEPT 2026-10-26; 47 reinstated
- [DONE] WI-009c | classifier route | G-001 | closed NEGATIVE 2026-10-25 (no usable model)
- [DONE] WI-009b | beat E5 baseline | G-001 | closed NEGATIVE 2026-10-25; same-sign clause adopted
- [DONE] WI-009 | contrastive ranking (D-003 opt 2) | G-001 | APPROVED, continued as WI-009b
- [DONE] WI-008 | quarantine triage (72 tickers) | G-002 | DONE 2026-10-25; 17 reinstate / 55 keep
- [DONE] WI-007 | two-stream docs + guide agents | G-001 | DONE
- [DONE] WI-006 | blocking QA gates | G-003 | DONE
- [DONE] WI-003 | ingest Phase 1 validation + CAD download | G-002 | DONE 2026-10-22
- [DONE] WI-002 | diagnose model signal | G-001 | DONE 2026-10-24; pivot to WI-009
- [DONE] WI-001 | pipeline v1 end-to-end | G-001 | DONE 2026-10-22 with QA exception; Gate 4 FAILED (structural demo only)
- [DONE] WI-000 | adopt goal→design→plan→execute→QA | G-003 | DONE 2026-10-22

## BACKLOG
- [BACKLOG] WI-005 | Post-MVP: EP-06 index scraper, EP-07 Telegram digest, EP-08 regime tuning | G-001 | L (decompose). Superseded by `docs/governance/PHASE2_HANDOVER_RUNBOOK.md`.

## Column policies
- `[TODO]` = in `ready/`, meets DoR, admin-ordered. `[WIP]` = in `in_progress/`, locks registered, WIP limit 1.
- `[BLOCKED]` = in `blocked/`, two-strike tripped, owner and 1-line reason on the row.
- `[DONE]` = QA verdict and gate recorded. Rows older than 7 days are one line (WORKFLOW §2).
- Risks: `RISKS.md`. Data facts: `DATA_CONTRACT.md`. Decisions: `designs/`. Gate and cycle record: `PM_LOG.md` (newest 2 cycles).
