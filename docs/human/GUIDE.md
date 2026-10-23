# GUIDE — The Signals Project & How It Runs

> **Human stream.** This document is for you (Kam) to read. Agents never load it — they work from the terse docs listed in `docs/README.md`. If this guide ever feels stale, tell any agent: *"Use the scribe subagent to refresh docs/human/GUIDE.md."*
>
> **Last refreshed:** 2026-10-22 · **Status:** pipeline built; models need signal work; ingest hardening awaiting your Mac runs.

---

## 1. What this project is

You are building an **institutional-style quantitative stock screener and portfolio-exit monitor**. Every day it should tell you two things:

1. **Defense** — for the stocks you actually hold (`config/holdings.csv`): which ones show signs of a local top or a breaking downtrend, ranked by *exit urgency*.
2. **Discovery** — for a 300-stock US universe and a 300-stock Canadian universe: the top-30 candidates for a bottom inflection (buy-the-dip) and the top-30 for sustained upward momentum.

The output is two annotated PDF "tearsheets" per market per day — candlestick charts with Bollinger Bands, volume, RSI, and the model's most important indicator marked on the chart — plus ranked tables with calibrated probabilities.

The non-negotiable design principle is **zero look-ahead bias**: no model decision may ever use information that wasn't available at decision time. This is enforced by a dedicated test suite, not by good intentions (`Design/05 Model Governance and QA.md`).

## 2. How it runs (the two-node architecture)

| Node | Machine | Does what |
|---|---|---|
| **A — Data acquisition** | Your M1 MacBook Air | Runs IB Gateway (because IBKR login needs 2FA and a GUI — never exposed on the VPS). Downloads OHLCV price history into Parquet files. |
| **B — Computation** | Hostinger VPS (2 vCPU, 8 GB — the same box this chat runs on) | Receives data via rsync, runs feature engineering, statistical filtering, model training, and PDF generation via the opencode agent system. |

Your daily loop on the Mac: rebuild watchlists → `ibkr_ingest.py --market USD --delta-only` (fast daily update) → same for CAD → `sync_back.py` (rsync to VPS). The VPS side is the agents' job. Hardware guardrails (2-core CPU limits, float32 memory discipline) exist because the VPS is small — see `AGENTS.md`.

## 3. The pipeline (five sprints, five human gates)

The build followed a strict sequence, each ending at a **gate** where you review evidence before anything continues:

1. **Sprint 1 — Ingestion:** download price data, audit it (row counts, date continuity, corporate-action adjustments). *Done 2026-10-21.*
2. **Sprint 2 — Features & targets:** compute ~dozens of technical indicators per stock (classic: RSI, Bollinger Bands, MACD, ADX, OBV; frontier: Hurst exponent, Kalman filter spread, Shannon entropy…), plus the four prediction targets (will the high be hit in 15 days? the low? upward trend over 20 days? down?). *Done.*
3. **Sprint 3 — Statistical pruning:** keep only features that are stationary, informative (Mutual Information), and not redundant (VIF < 5). *Done.*
4. **Sprint 4 — Model training & QA:** train 8 calibrated XGBoost classifiers (4 targets × 2 markets) with purged walk-forward validation, then grade them against governance thresholds. **This gate FAILED on all four US targets — the models are currently no better than coin flips.**
5. **Sprint 5 — PDF compilation:** score today's data and render the tearsheets. *Mechanically done, but the 2026-10-21 PDFs are structural demos only — do not trade on them.*

**Where the project actually stands:** the machine works end-to-end; the intelligence inside it doesn't yet. The open problem is **WI-002 on the board: diagnose and fix the model signal.**

## 4. The agent workforce (who does the work)

The coding agents run in **opencode** (a terminal AI coding tool) inside tmux session `signals`. Each role has a fixed model, chosen for value — cheap models do the volume, expensive ones only think:

| Agent | Model | Role | Approx. cost |
|---|---|---|---|
| **Build** | DeepSeek V4 Pro | Writes code, runs tests, executes plans. Capped at 150 steps/run. | ~$0.44/$0.89 per M tokens |
| **Reviewer** | DeepSeek V4 Flash | Read-only pre-commit QA: guardrails, look-ahead bias, bugs. Also enforces gate compliance. | ~$0.09/$0.18 |
| **Plan** | Claude Sonnet 5.5 | Turns goals into design docs and step-by-step plans with verification commands. | ~$2/$10 |
| **Guide** (mentor) | Claude Sonnet 5.5 | **Your learning companion** — explains code, quant concepts, and results pedagogically, grounded in this repo. Ask in chat: *"explain the embargo in purged cross-validation"* and it will teach with real examples from the repo. | same as Plan |
| **Troubleshooter** | Claude Opus 5.5 | Escalation-only root-cause debugging. Must be handed an evidence bundle; must *reproduce* before theorizing; says BLOCKED rather than guessing. | ~$4/$20 |
| **Scribe** | DeepSeek V4 Flash | Regenerates this human stream (`docs/human/`) from the agent docs on request. | ~$0.09/$0.18 |

Total spend so far: ≈ $6.64 over 3 active days (~$2/day). The expensive models (Opus) have fired rarely — that's by design.

**How the agents know what to do:** a global instruction file (`~/.config/opencode/instructions/workflow.md`) is injected into every session. It tells them: read the board first, execute only from the plan file named on the board, escalate with evidence, never mark DONE over a failed gate.

## 5. The workflow framework (how work flows)

Full rules: `docs/workflow/WORKFLOW.md`. The shape:

```
GOAL → DESIGN → PLAN → EXECUTE → QA/GATE → DONE
            ▲                   │           │
            └── plan invalid ───┘           │
                              QA fail ──────┘ → back to PLAN
```

- **GOAL** (`workflow/goals/G-##`): *why* we're doing something — intention, success criteria, non-goals. Never edited, only superseded. This is where the original intention lives, permanently.
- **DESIGN** (`workflow/designs/D-##`): *how* — written as an ADR (Architecture Decision Record): context, options considered, decision, consequences. This is the format the industry uses to remember *why* a choice was made.
- **PLAN** (`docs/plans/YYYY-MM-DD-WI-##-<slug>.md`): *what exactly* — numbered steps, each with an acceptance criterion and the exact command that proves it. The plan file is the contract: Build works from the file, checks off steps as verifications pass, and appends a Deviations section when reality disagrees — history is never rewritten.
- **EXECUTE**: one work item at a time (WIP limit 1), one task = one session.
- **QA/GATE**: the reviewer agent + your sign-off. Failed gate = hard stop.
- **DONE**: only when QA passed. The one exception on record (WI-001, Sprint 5 past failed Gate 4) is marked on the board as a QA exception — deliberately visible, never hidden.

**Your operating surface is two files:** `workflow/BOARD.md` (what now / what next — kanban with Backlog/Ready/Executing/QA/Done/Blocked) and `docs/SESSION_HANDOVER.md` (current state, written by agents at the end of every session). If you read nothing else on a given morning, read those two.

## 6. The two documentation streams (and why)

| Stream | Where | Style | Who reads it |
|---|---|---|---|
| **Agent stream** | `docs/README.md`, `workflow/`, `plans/`, `ingest/`, `SESSION_HANDOVER.md` | Terse, ID-dense, tables — optimized to be loaded into model context cheaply | Agents (every session) |
| **Human stream** | `docs/human/` (this guide) | Narrated, explanatory, jargon expanded | You |

The split exists because agent context costs money and attention: every token of narrative prose in the agent stream gets re-paid on every model call. So the agent stream stays skeletal, and the *same facts* get a readable, explained version over here. The scribe agent regenerates this stream from the agent stream — the agent stream is always the source of truth.

**Suggested reading order for learning:** this guide → `workflow/WORKFLOW.md` (short) → `Design/01` (the original vision) → `Design/05` (what "valid" means — the most conceptually rich doc) → the Sprint 4 QA report (see the failure honestly) → ask the guide agent about anything that snagged you.

## 7. What's on the board right now (2026-10-22)

- **WI-002 (top of READY): diagnose & fix model signal.** Needs a design doc first. This is the highest-value work in the project — candidates include fresh validated data, different target horizons, richer regime features, and investigating why `hurst_50` alone drove 52% of one model's decisions.
- **WI-003 (BLOCKED on you):** run the Phase-1 ingest validation on your Mac (smoke test → full USD → full CAD → delta-only). Checklist: `docs/ingest/ib4-optimization-plan.md`. Fresh, reliable data is also a likely ingredient for fixing the models — so these two connect.
- **WI-004, WI-005 (BACKLOG):** faster ingest pacing (gated on 3 clean runs) and the post-MVP ideas (index scraper, Telegram digest, regime-conditional tuning).

## 8. Glossary (the ten terms you'll meet first)

- **OHLCV** — Open/High/Low/Close/Volume, the raw price record per day.
- **Parquet** — columnar file format; the data store for price history.
- **Feature** — a computed per-day characteristic of a stock (e.g., 14-day RSI).
- **Target (Y)** — the thing we predict, e.g. `Y_15d_Low` = "the 15-day low gets touched" (binary).
- **Look-ahead bias** — accidentally letting the model see future information; the cardinal sin of backtesting.
- **Purged walk-forward validation** — train on the past, validate on the future, with an **embargo** gap (20 trading days) between them so overlapping windows can't leak.
- **Isotonic calibration** — rescaling raw model outputs so "0.7" genuinely means ~70% probability.
- **Brier Skill Score** — did the probabilities beat a naive baseline? (Currently negative: no.)
- **VIF** — Variance Inflation Factor; how much a feature is redundant with others. VIF < 5 = keep.
- **SHAP** — attribution of each model decision to features; a feature taking >35% of total credit signals brittleness.

## 9. If you only remember five things

1. The board (`workflow/BOARD.md`) and the handover (`docs/SESSION_HANDOVER.md`) are the whole operating surface.
2. Plans are files; execution works from the file, not from chat.
3. A failed gate stops everything — that rule exists because it was once violated.
4. The 2026-10-21 PDFs are demos; the models aren't trustworthy yet (WI-002).
5. When you want to *understand* something, ask the guide agent — that's what it's for.
