# docs/README.md — Documentation Router (start here)

**Purpose:** the single map of all project documentation — for the human admin (Kam) and for agents. If a doc contradicts this index, this index wins on *where things live*; the doc itself wins on *technical content*. Update this file whenever docs are added, moved, or superseded.

---

## 1. Canonical paths (reconciled — older docs disagree)

| What | Canonical | Notes |
|---|---|---|
| VPS project root | `~/projects/signals` | Some Design/ docs and prompt templates say `/opt/quant-screener/` — **stale**, treat as `~/projects/signals` everywhere |
| M1 Mac ingest kit | `ib4/` in repo (synced to Mac, e.g. `~/Downloads/IBKR/`) | Self-contained: run scripts from their own folder on the Mac |
| M1 Mac data store | Mac-local `data/raw_ohlcv/` (454 USD parquet as of 2026-10-22 baseline) | Synced to VPS via `sync_back.py` / rsync |
| Agent configs | `~/.config/opencode/` (global) — `opencode.jsonc`, `agents/*.md`, `instructions/workflow.md`, `prompts/plan.md` | Not in repo; backed up via dotfiles if ever needed |

## 2. Documentation map

### `Design/` — frozen baseline spec (v1.0 blueprint, do not edit; propose changes as new docs)
| Doc | What it is |
|---|---|
| `00 Workflow summary.md` | Executive blueprint: strategy, outputs, architecture, runbook (superset of 01) |
| `01 Master Handover and Workflow.md` | Split-node architecture + 5-gate HITL runbook with copy-paste gate prompts |
| `02 Project Plan.md` | PMP charter, WBS (EP-01…EP-05), backlog (EP-06…08), risk register |
| `03 Agents.md` | Original 4-role agent spec — **canonical version is root `AGENTS.md`** (Design copy is historical) |
| `03 System Architecture.md` | Module/data architecture |
| `04 Skills Specification.md` | Spec for `.agents/skills/` |
| `05 Model Governance and QA.md` | Anti-leakage test suite + governance metric thresholds (the Gate 4 bar) |
| `06 Sprint 1 and 2 Starter Code.md` | Starter code spec |

### `docs/` — living documentation (update freely, one topic per file)
| Doc | What it is | Status |
|---|---|---|
| `README.md` | This router | maintained |
| `SESSION_HANDOVER.md` | **Live context ledger** — current project state for any agent/admin starting cold. Update at the END of every working session | maintained |
| `workflow/WORKFLOW.md` | **The operating framework** — goal → design → plan → execute → QA, iteration rules, roles | maintained |
| `workflow/BOARD.md` | **The kanban board** — what now / what next; agents read it at task start | maintained |
| `workflow/goals/` | Goal docs (`G-##`) — the written intentions; superseded, never edited | on change |
| `workflow/RISKS.md` | Living risk register (PMP) — reviewed weekly; realized risks get response work items | weekly |
| `workflow/designs/` | Design decisions as ADRs (`D-##`: Context / Options / Decision / Consequences / Status) | per-item |
| `workflow/retros/` | Weekly retro notes (`YYYY-WW.md`) | weekly |
| `plans/` | Execution plans (`YYYY-MM-DD-WI-##-<slug>.md`); Build executes from the plan named on the board | per-task |
| `ingest/` | IBKR ingest kit docs: `ib4-changelog.md` (code audit trail), `ib4-optimization-plan.md` (phases + validation checklist), `ibkrdownload.md` (pacing engine deep-dive) | maintained |

### Generated evidence (not docs — never hand-edit)
- `reports/sprintN_*.md` — gate artifacts (agent-generated, timestamped)
- `reports/screener_*.pdf` — final tearsheets
- `data/audit_ingestion_*.csv` — ingest audits

### Human stream (`docs/human/` — for reading, NOT for agent context)
- `GUIDE.md` — narrated project + workflow guide, glossary, learning path. Agents never load it. Regenerate via the **scribe** subagent whenever the agent stream changes materially.
- Rule: agent-facing docs must stay terse (context cost); explanatory prose belongs here. If an ID appears in the human stream, it's expanded in plain language on first use.

### Agent operating system (how the agents themselves work)
- Root `AGENTS.md` — project guardrails, sprint pipeline, model escalation protocol (canonical)
- `.agents/rules/` — env-split, no-live-trading, quant-ml guardrails
- `.agents/skills/` — gate-brief (gate→human briefing template), discord-brief, quant-investigator, signal-evaluator (last three are unexpanded stubs — frontmatter added 2026-10-22 so they're discoverable; bodies still one line)
- Agent workforce (opencode): **Build** = DeepSeek V4 Pro (execute, 150-step cap) → **reviewer** = DeepSeek V4 Flash (pre-commit + leakage + gate-compliance review) → **Plan** = Claude Sonnet 5.5 (writes `docs/plans/` files) → **guide** = Sonnet 5.5 (mentor, read-only) → **scribe** = flash (maintains `docs/human/`) → **troubleshooter** = Claude Opus 5.5 (escalation-only, read-only, evidence-bundle required). Verify with `opencode debug agents`.

## 3. Known doc discrepancies (fixed points of confusion)
1. ~~SESSION_HANDOVER said "ingest NOT run" (2026-10-21 23:40) while Sprint 1–5 reports exist (2026-10-21) and the optimization plan shows a 454-file USD baseline~~ → **resolved 2026-10-22**, see SESSION_HANDOVER for the reconciled state.
2. Design/01 paths (`/opt/quant-screener`, `~/quant-screener-local`) → superseded by §1 above.
3. Design/03 Agents.md vs root AGENTS.md → root is canonical.

## 4. Conventions going forward
- **Work runs through the board** (`workflow/BOARD.md`): read at task start, update the row you touch. New work → new WI row + goal link.
- New working knowledge → new file in `docs/`, linked here. No new top-level dirs without updating this index.
- Every working session ends with a `SESSION_HANDOVER.md` refresh (agent-to-admin handover).
- Every code change gets a `ingest/ib4-changelog.md` entry (ingest) or a plan-file Deviations note (pipeline); optimization *decisions and gates* live in `ingest/ib4-optimization-plan.md`.
- Plan files are named `YYYY-MM-DD-WI-##-<slug>.md` and kept after execution (audit trail), including Deviations.
