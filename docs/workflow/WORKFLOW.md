# WORKFLOW.md — Goal → Design → Plan → Execute → QA (v3, lean HITL)

> Supersedes v2 (2026-11-07). Rationale, measurements, and rejected options: `designs/D-020-lean-hitl-tri-role-workflow.md`.
> Binding rules are unchanged except where D-020 §4 states otherwise. Rules that lived only in v2 prose are in `archive/` (git history).

**Why:** intent lives in files, plans are auditable, gates gate. Hybrid of PMP (gates, change control), Scrum (DoR/DoD, retros), Kanban (pull, WIP limits). Artifacts, not ceremony.

## 1. Flow

```
GOAL ──► DESIGN ──► PLAN ──► EXECUTE ──► QA/GATE ──► DONE
              ▲                  │             │
              └─ plan invalid ───┘    QA fail ──┘──► PLAN (or DESIGN)
```

| Stage | Artifact | Owner | Exit |
|---|---|---|---|
| GOAL | `goals/G-##-<slug>.md` | Admin (agents may draft) | Intent, success criteria, non-goals. Never edited, only superseded. |
| DESIGN | `designs/D-##-<slug>.md` (ADR) | Architect | Context, options, decision, consequences, status |
| PLAN | `docs/kanban/draft/WI-###-<slug>.md` (single-session WI), or `docs/plans/YYYY-MM-DD-WI-##-<slug>.md` (multi-step plan) | Architect | Steps with acceptance + verify command. ≤400 tokens for WI specs. |
| EXECUTE | Code + telemetry footer in WI file; `STATUS:` in log | Executor (DeepSeek Flash) | Verify commands green; deviations in `## DEVIATIONS` |
| QA/GATE | Verdict + gate brief | Reviewer / Admin | APPROVE; failed gate = hard stop |
| DONE | Board row + evidence | Admin | QA passed and gate signed where applicable |

**Provisional-verdict rule (admin, in chat, 2026-11-09):** every gate verdict (ADOPT / REJECT / INCONCLUSIVE, incl. `evaluate.verdict()` output in reports) is **PROVISIONAL — advisory only** until the admin ratifies it in chat. Board rows record the computed verdict prefixed `PROVISIONAL`; no adoption, rule change, artifact promotion, or thread close is applied from a computed verdict without an explicit admin decision. QA still blocks DONE regardless.

**Two-layer ML gate (admin, in chat, 2026-11-09; `designs/D-023`):** ML work gates at exactly one of two layers. **Layer 1 (pickle library, predictive):** OOF AUC/IC + BH-FDR + calibration — stocks `data/models/`, licenses no trading claim. **Layer 2 (overlay, trading):** any ML bolted on top of frozen rules — decision parameters tuned on CALIB trading edge only, frozen before EVAL, judged by edge vs the named frozen baseline + fold stability + placebo on the edge. WI specs must state their layer (new `gate_layer` frontmatter key, `_TEMPLATE_WI.md`); Layer-1 stats never justify a Layer-2 adoption, and a Layer-2 REJECT never retro-doubts the Layer-1 artifact. **Coverage audit:** D-023 §4 holds the retroactive layer map of every WI and the Layer-1 attempted/not-attempted ledger; new Layer-1 WIs must check it before drafting (re-proposing an attempted direction without a structural change named against its failure mechanism is a spec defect).

**Iteration rules**
1. **Intent never changes silently.** Goals and designs are superseded (linked forward), never edited in place.
2. **Deviations append, never rewrite.** Execution appends to `## DEVIATIONS`, then continues only if safe.
3. **Two strikes = human decision.** After two failed attempts, write an intervention brief (options, costs, REC) and STOP. The admin picks the path.
4. **QA gates are blocking.** Nothing reaches DONE over a failed gate.
5. **WIP limits.** EXECUTING = 1. Architect (DESIGN + PLAN) = 2.
6. **Board matches disk.** Any "running (PID N)" or "done" claim is written with its evidence (log path, artifact mtime) and verified before acting.

## 2. Board (single source)

- `docs/workflow/BOARD.md` is the only board. Kanban dirs under `docs/kanban/` hold WI files and lock bookkeeping, never a second board.
- **Flat rows** (D-020 §5): `[TODO] | [WIP] | [BLOCKED] | [DONE]` · `WI-### | title | G-## | write_files or plan | evidence (1 line)`.
- **Target size ≤5 KB (working target ~3–6 KB).** Rows are **pointer-only**: a DONE row is one line — title, gate, verdict tag (e.g. `RATIFIED L1 2026-11-14`), evidence path. Verdict narratives, test counts, and ratification quotes live in the WI card and the cited report; `PM_LOG.md` stays the canonical decision record. Write the row one-line at close-out — do not wait for the weekly collapse.
- **Card compaction at close-out, not as a weekly chore:** when `docs/kanban/done/` exceeds 10 cards, append one summary row per card to `docs/execution/WI_AND_RUN_LEDGER.md` and `git mv` the oldest to `docs/archive/wi/` in the same close-out commit. (2026-11-14 retro-fix: the rule had never fired — `done/` reached 46 cards while the board grew to 22 KB.)
- **Pull:** the top TODO row is "do next". Expedite (`⚡`) max 1, reserved for breakage that blocks the daily shortlist.
- **Aging:** BLOCKED >7 days or EXECUTING >3 days is flagged at the weekly review.
- **File locks:** before a WI enters `in_progress/`, its `write_files` must be free in `.hermes/locks.json` (gitignored, Hermes-managed). Release on DONE or BLOCKED.

## 3. Definitions

**Definition of Ready (to TODO):** linked `G-##`; one-line observable outcome; blockers named; size S (one session), M, or L (decompose first); `write_files` line ranges set; `test_command` quiet (exit code only, ≤5 lines stdout).

**Definition of Done:** QA verdict APPROVE; gate signed where applicable; verify commands green; board row updated; WI telemetry footer filled; handover touched if project state changed.

**Sizing:** one WI = one executor session. Bigger work stays at GOAL level until decomposed.

## 4. Naming

| Thing | Convention | Example |
|---|---|---|
| Goals | `G-##-<slug>.md`, never renumbered | `G-001-dual_market_screener.md` |
| WIs | `WI-###` on the board; ID-only references | `WI-029` |
| Designs | `D-##-<slug>.md`; status `proposed / accepted / superseded-by-D-##` | `D-020-lean-hitl-tri-role-workflow.md` |
| Plans | `YYYY-MM-DD-WI-##-<slug>.md` | — |
| Logs | `docs/plans/logs/WI-##-<slug>.md` (append-only) | — |
| Briefs | `docs/workflow/briefs/YYYY-MM-DD-<slug>.md` | — |
| Retros | `retros/YYYY-WW.md` | `retros/2026-W44.md` |
| Data contract | `docs/workflow/DATA_CONTRACT.md` (single file) | — |

Kebab-case filenames. One topic per file. Mandatory header: `ID`, `Title`, `Goal:` (for D and plan), `Status`, `Date`.

## 5. Artifact sections

- **Goal:** Intent / Success criteria / Non-goals / Current state
- **Design (ADR):** Context / Options / Decision / Consequences / Status
- **Plan:** Goal / Constraints / Steps (change, acceptance, verify command, ≤6 steps) / Out of scope / Deviations. Frozen after the architect pass.
- **WI (batch spec):** `docs/kanban/_TEMPLATE_WI.md`. Blueprint, I/O contract, DoD, telemetry footer. **≤400 tokens for the spec body.**
- **Log:** one row per step, ≤50 words. Details go in the report, cited by path. `STATUS:` at the END.

## 6. Roles and model tiers (D-020 §4.1)

| Role | Who (default) | Job | Escalation |
|---|---|---|---|
| **Architect** | Hermes session on the planner model (Sonnet) | Decompose, design, write WI specs and the DATA_CONTRACT. Halts at its gate. | Opus for new ADRs and after a two-strike block |
| **Controller** (optional) | Hermes or GLM | Metadata-only verify of paths and schemas (≤15 lines stdout). Compress the spec when it exceeds 400 tokens. | Skip when paths are already verified |
| **Executor** | surgical-builder (DeepSeek Flash) via opencode | Execute ONE locked WI within `write_files`. Stdout ≤5 lines. | Two strikes → BLOCKED → human |
| **Reviewer** | reviewer agent (flash), read-only | APPROVE or FIX with `file:line` findings | — |
| **Human** | Admin | Goals, ordering, gate sign-off, unblocking | — |

**Swap rule:** one role per session. Hand off through files (WI file, BOARD row, log `STATUS:`), then `/clear` before the next role. Never carry architect reasoning into the executor session.

**Halt banners** (end the turn with the one for your role): see `MODE_PROMPTS.md`.

## 7. Tier map (D-025)

**Pipeline stages** — maps 1:1 onto the already-ratified gate layers (D-023/D-024). This section reorganizes the docs; it does not re-derive the protocol.

| Tier | Contents | Gate | License |
|---|---|---|---|
| T1 — Features + metafeatures | The causal panel at the detection bar; feature gap research; attribution | D-023 §2 (no model claim; attribution + alignment stats only) | Feeds T2 |
| T2 — Predictions | Target families × horizons × learners → FDR-gated pickle library | D-023 Layer 1 (OOF AUC/IC + BH-FDR + calibration) | Predictive only, NO trading claim |
| T3 — Trade action / strategy | Overlays, entry/exit rules, mechanisms vs frozen baseline + costs | D-024 Layer 2 (CALIB-only tuning, placebo, one-shot EVAL) | Deployment only via ratified ADOPT |

**T1/T2 predictive-only (admin direction, 2026-11-13):** gate evidence at Tier 1 and Tier 2 (Layer 1) is predictive statistics only — OOF AUC/IC + BH-FDR + calibration. No economic-magnitude or cost analysis is presented at T1/T2 (cost/edge analysis belongs to T3/Layer 2). Every FDR-surviving predictor is accepted into the L1 pickle library and integrated into the workflow — there is no effect-size floor at L1.

Cross-tier rules (carried unchanged): pre-committed closures; probe-first with core-hour caps; BH-FDR family = every tested cell; conditioning axes fold into the same family; two-strike breaker; computed verdicts PROVISIONAL until admin ratifies. Decisions and protocol detail: `designs/D-023-two-layer-ml-gate.md`, `designs/D-024-l2-overlay-rebuild.md`. Sprint brief: `docs/workflow/briefs/2026-11-10-D-025-tiered-sprint-brief.md`.

## 8. Ceremonies (light)

| Ceremony | Cadence | What |
|---|---|---|
| Gate review | per WI | Admin signs gate evidence. Failed gate blocks DONE. |
| Weekly review (Mon) | weekly, 15 min | Reorder TODO. Flag aging rows. Demote DONE >7 days to one line. Rotate PM_LOG to the last 2 cycles (older → `docs/workflow/archive/PM_LOG-YYYY-MM.md`). Lessons → `retros/`. |
| Change control | as needed | Goals and designs superseded by a linked doc, never edited in place |

Archives are append-only. Never rewrite archived content. Git is the audit trail, so no "kept for audit" blocks.

## 9. Risk

`RISKS.md` is a living register (P / I / owner / response), reviewed weekly. A realized risk gets an immediate response WI.

## 10. Decision memos

- **REC first (BLUF).** Routine, reversible: 3–5 lines (REC and why, 1–2 verified facts, the ask).
- **One-way or uncertain:** what happened (verified facts; unverified labelled) / what's next / 2–4 options (what, why, expected outcome, risk-cost; "do nothing" counts) / REC with assumptions and a review trigger.
- Tag domain (clear / complicated / complex / chaotic) and door (one-way / two-way).
- PM recommends; admin decides. No auto-execution past a gate.

## 11. Do not

- Start EXECUTE without a WI or plan file that is locked and on the board.
- Move a card to DONE without a QA verdict.
- Put discussion in goal, design, or plan docs. Decisions and facts only.
- Add a new artifact that does not answer "what now / what next / why".
- Create a second board or a parallel tracker.
- Commit without explicit paths. Never `git add -A`.

## 12. Read discipline (every agent, every session)

- **Grep before read.** Locate with search, then read ±40 lines. Never full-read a file over 150 lines when a grep or `STATUS:` marker answers the question.
- **Logs:** tail ~20 rows plus the final `STATUS:` line.
- **PM_LOG:** newest entry only.
- **Skills:** load the core SKILL.md. Load a reference section only when the situation matches.
- **Verify with a command,** not a re-read.
- **One canonical record per decision.** The PM_LOG entry is canonical. Board and handover cite it by pointer.
