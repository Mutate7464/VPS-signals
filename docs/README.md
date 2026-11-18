# docs/README.md — Documentation Router (start here)

**Purpose:** the single map of all project documentation — for the human admin (Kam) and for agents. If a doc contradicts this index, this index wins on *where things live*; the doc itself wins on *technical content*. Update this file whenever docs are added, moved, or superseded.

**Cold-start reading order (2026-11-18):** root `AGENTS.md` (constraints) → `workflow/BOARD.md` (what now; single source) → `workflow/designs/INDEX.md` (design registry) → `workflow/DATA_CONTRACT.md` (data facts) → only then the cited card/report/design. `SESSION_HANDOVER.md` is a stub — BOARD is the live source.

---

## 1. Canonical paths (reconciled — older docs disagree)

| What | Canonical | Notes |
|---|---|---|
| VPS project root | `~/projects/signals` | Some Design/ docs and prompt templates say `/opt/quant-screener/` — **stale**, treat as `~/projects/signals` everywhere |
| M1 Mac ingest kit | `ib4/` in repo (synced to Mac, e.g. `~/Downloads/IBKR/`) | Self-contained: run scripts from their own folder on the Mac |
| M1 Mac data store | Mac-local `data/raw_ohlcv/` (454 USD parquet as of 2026-10-22 baseline) | Synced to VPS via `sync_back.py` / rsync |
| Agent configs | `~/.config/opencode/` (global) — `opencode.jsonc`, `agents/*.md`, `instructions/workflow.md`, `prompts/plan.md` | Not in repo; backed up via dotfiles if ever needed |

## 2. Documentation map

### `archive/old-files/archive-design/` — frozen baseline spec (v1.0 blueprint; moved 2026-11-18 from `docs/archive/Design/`; deletion-staged; do not edit)
| Doc | What it is |
|---|---|
| `00 Workflow summary.md` | Executive blueprint: strategy, outputs, architecture, runbook (superset of 01) |
| `01 Master Handover and Workflow.md` | Split-node architecture + 5-gate HITL runbook with copy-paste gate prompts |
| `02 Project Plan.md` | PMP charter, WBS (EP-01…EP-05), backlog (EP-06…08), risk register |
| `03 Agents.md` | Original 4-role agent spec — **canonical version is root `AGENTS.md`** (archive copy is historical) |
| `03 System Architecture.md` | Module/data architecture |
| `04 Skills Specification.md` | Spec for `.agents/skills/` |
| `05 Model Governance and QA.md` | Anti-leakage test suite + governance metric thresholds (the Gate 4 bar) |
| `06 Sprint 1 and 2 Starter Code.md` | Starter code spec |

### `docs/` — living documentation (update freely, one topic per file)
| Doc | What it is | Status |
|---|---|---|
| `README.md` | This router | maintained |
| `SESSION_HANDOVER.md` | **Stub** (2026-11-18): the pre-lean ledger (2026-10-24…11-02 state) moved to `archive/old-files/SESSION_HANDOVER-history.md`; live state = `workflow/BOARD.md` | refresh at session end |
| `workflow/WORKFLOW.md` | **The operating framework** — goal → design → plan → execute → QA, iteration rules, roles | maintained |
| `workflow/BOARD.md` | **The kanban board** — what now / what next; agents read it at task start | maintained |
| `workflow/goals/` | Goal docs (`G-##`) — the written intentions; superseded, never edited | on change |
| `workflow/RISKS.md` | Living risk register (PMP) — reviewed weekly; realized risks get response work items | weekly |
| `workflow/designs/` | Design decisions as ADRs (`D-##`) — **read `designs/INDEX.md` first** (one-line registry; open the full design only for protocol detail) | per-item |
| `workflow/briefs/` | Current planner briefs (newest first = sprint entry points; older ones are in `archive/old-files/briefs/`) | sprint scoping |
| `workflow/PM_LOG.md` | Canonical decision record (newest 2 cycles; older → `workflow/archive/PM_LOG-*.md`) | per-cycle |
| `workflow/DATA_CONTRACT.md` | Data facts: universe, coverage, panel caches, invariants | before any data work |
| `workflow/MODE_PROMPTS.md` | Per-role mode prompts | role dispatch |
| `workflow/archive/` | Archived BOARD/PM_LOG snapshots (incl. `BOARD-2026-11-16-D027-active-detail.md`, the full ratified D-027/D-026 narrative) | provenance only |
| `kanban/{draft,ready,in_progress,blocked,done}/` | WI cards (board rows are pointers to these); compaction rule in WORKFLOW §2 | card detail |
| `workflow/retros/` | Weekly retro notes (`YYYY-WW.md`) | weekly |
| `governance/` | PMP/Agile human stream: `MVP_CLOSURE_REPORT.md`, `PHASE2_HANDOVER_RUNBOOK.md` (WI-019 closeout) | maintained |
| `architecture/` | `DECISIONS_AND_NEGATIVE_KNOWLEDGE.md` — ADR index + negative register (read before architecture changes) | maintained |
| `execution/` | `WI_AND_RUN_LEDGER.md` — compressed WI/run telemetry for the MVP cycle | maintained |
| `archive/` | `wi/` = archived WI cards (still linked from BOARD rows — do not delete) + `old-files/` = **staging for deletion** (superseded plans, briefs, execution logs, gate briefings, the pre-lean `Design/` baseline + `plan.md`; see `archive/old-files/README.md`) | read-only history |
| `plans/` | Execution plans (`YYYY-MM-DD-WI-##-<slug>.md`); Build executes from the plan named on the board | per-task |
| `tech_approach/` | Week-based technical-approach workspace (`YYYY-WW/briefs|plans|reports`, e.g. `2026-W44/`) — home of the WI-009+ contrastive/hybrid line; plans there are contract-valid when the board row names that path (workflow-contract exception 2026-10-24) | per-week |
| `ingest/` | IBKR ingest kit docs: `ib4-changelog.md` (code audit trail), `ib4-optimization-plan.md` (phases + validation checklist), `ibkrdownload.md` (pacing engine deep-dive) | maintained |

### Generated evidence (not docs — never hand-edit)
- `reports/sprintN_*.md` — gate artifacts (agent-generated, timestamped)
- `reports/screener_*.pdf` — final tearsheets
- `data/audit_ingestion_*.csv` — ingest audits

### Human stream (`docs/human/` — for reading, NOT for agent context)
- `GUIDE.md` — narrated project + workflow guide, glossary, learning path. Agents never load it. Regenerate via the **scribe** subagent whenever the agent stream changes materially.
- `human/interventions/` — dated intervention records; consolidated, one record per event (model-change saga consolidated 2026-10-24).
- Rule: agent-facing docs must stay terse (context cost); explanatory prose belongs here. If an ID appears in the human stream, it's expanded in plain language on first use.

### Agent operating system (how the agents themselves work)
- Root `AGENTS.md` — project guardrails, sprint pipeline, model escalation protocol (canonical)
- `.agents/rules/` — env-split, no-live-trading, quant-ml guardrails
- `.agents/skills/` — gate-brief (gate→human briefing template) is the only body-bearing project skill; the three former stubs (discord-brief, quant-investigator, signal-evaluator) were deleted 2026-10-23
- Agent workforce (opencode; verified against `~/.config/opencode/` 2026-11-18): **Build** (`surgical-builder`) = DeepSeek V4.1-Flash (escalation_models → V4.1-Pro → Gemini 4 Argon → Opus 5.5, human-gated) → **reviewer** = DeepSeek V4 Flash (pre-commit + leakage + gate-compliance review) → **planner** = Claude Haiku 5.5 (writes plan files; was GPT-6-Luna) → **triage** = Qwen3-Coder-Next (independent log diagnostician; escalation → Gemini 4 Argon → Opus 5.5) → **guide** = Sonnet 5.5 (mentor, read-only) → **scribe** = DeepSeek V4 Flash (maintains `docs/human/`) → **troubleshooter** = Opus 5.5 (was GLM-5.3; read-only, evidence-bundle required). Verify with `opencode debug agents`.

## 3. Known doc discrepancies (fixed points of confusion)
1. ~~SESSION_HANDOVER said "ingest NOT run" (2026-10-21 23:40) while Sprint 1–5 reports exist (2026-10-21) and the optimization plan shows a 454-file USD baseline~~ → **resolved 2026-10-22**, see SESSION_HANDOVER for the reconciled state.
2. `archive/old-files/archive-design/01` paths (`/opt/quant-screener`, `~/quant-screener-local`) → superseded by §1 above.
3. Design/03 Agents.md vs root AGENTS.md → root is canonical.

## 4. Conventions going forward
- **Work runs through the board** (`workflow/BOARD.md`): read at task start, update the row you touch. New work → new WI row + goal link.
- New working knowledge → new file in `docs/`, linked here. No new top-level dirs without updating this index.
- Every working session ends with a `SESSION_HANDOVER.md` refresh (agent-to-admin handover).
- Every code change gets a `ingest/ib4-changelog.md` entry (ingest) or a plan-file Deviations note (pipeline); optimization *decisions and gates* live in `ingest/ib4-optimization-plan.md`.
- Plan files are named `YYYY-MM-DD-WI-##-<slug>.md` and kept after execution (audit trail), including Deviations.
- Technical-approach work items (WI-009 series) keep briefs/plans/reports under `docs/tech_approach/YYYY-WW/`; the plan named in the board's EXECUTING row is the contract location. Conventional items keep using `docs/plans/`.
