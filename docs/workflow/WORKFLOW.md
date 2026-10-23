# WORKFLOW.md — Goal → Design → Plan → Execute → QA (v2, PM-aligned)

**Why this exists:** intention must live in files, plans must be auditable, and gates must actually gate. This framework hybridizes three proven systems, scaled down for a solo admin + agent workforce:
- **PMP** → stage gates, charter, living risk register, change control (supersession)
- **Agile/Scrum** → Definition of Ready/Done, sprint reviews (= your gates), retrospectives
- **Kanban** → pull-based board, WIP limits, explicit policies, flow awareness

Not a methodology transplant — a simple project needs the *artifacts*, not the ceremony.

---

## 1. The flow

```
GOAL ──► DESIGN ──► PLAN ──► EXECUTE ──► QA/GATE ──► DONE
              ▲                      │             │
              └── plan invalid ──────┘             │
                  (loop with evidence)             │
                                   QA fail ───────┘──► back to PLAN (or DESIGN)
```

| Stage | Artifact & naming | Owner | Exit criterion |
|---|---|---|---|
| **GOAL** | `goals/G-##-<slug>.md` | Admin (agents may draft) | Intention + success criteria + non-goals written; never edited, only superseded |
| **DESIGN** | `designs/D-##-<slug>.md` (ADR format, §5) | Plan agent (Sonnet) | Context, options, decision, consequences recorded |
| **PLAN** | `plans/YYYY-MM-DD-WI-##-<slug>.md` | Plan agent | Numbered steps, each with acceptance criterion + verification command |
| **EXECUTE** | code + checkboxes in plan file | Build agent (DeepSeek) | Every verification command green; deviations appended in-plan |
| **QA/GATE** | reviewer verdict + gate report | Reviewer (flash) / admin | APPROVE verdict; failed gate = hard stop |
| **DONE** | board row + evidence link | Admin | QA passed **and** gate signed (where applicable) |

**The iteration rules (the core):**
1. **Intention never changes silently.** Goals are only *superseded* (linked forward), never edited in place. If execution reveals the goal was wrong, that's a new goal or an explicit supersession.
2. **Deviations append, never rewrite.** Build appends to the plan file's `## DEVIATIONS` section and continues only if safe. Plan history is preserved.
3. **A step failing twice is a signal for the human, not another guess.** → Build writes an intervention brief (options + costs + recommendation) and STOPS; the admin chooses the escalation path (cheap troubleshooter / Sonnet / Opus / personal takeover). One faithful application of any agent's fix plan; if it fails again → STOP and report.
4. **QA gates are blocking.** Nothing reaches DONE over a failed gate (this rule exists because Sprint 5 shipped PDFs past a failed Gate 4 — see G-003).
5. **One execute at a time.** EXECUTING WIP limit = 1, matching the one-task-one-session agent rule.
6. **Board/handover state must match artifacts on disk.** A "running in background (PID N)" claim is written only alongside its evidence (log path, artifact mtime) and cleared as soon as the run ends. Before acting on any process/status claim, verify it (`ps -p N`, log tail, output mtime) — the plan EXECUTION LOG and the run's own artifacts are the truth, not the board row. Every session ends with board + handover reflecting the verified end state (DoD already requires this; this rule makes the failure mode explicit).

## 2. Board policies (Kanban)

- **Pull, don't push:** work is pulled from the top of READY. The top row *is* "do next."
- **WIP limits:** EXECUTING = 1. DESIGN+PLAN combined = 2.
- **Classes of service:** normal (FIFO by admin order) and **EXPEDITE** (max 1) — reserved for breakage blocking the daily shortlist. Expedite rows are marked `⚡` and jump the queue.
- **Flow awareness, minimal:** every row leaving BACKLOG gets a `since` date; anything sitting >7 days in BLOCKED or >3 days in EXECUTING is flagged at the weekly review. No story points, no velocity — plan steps *are* the estimate; budget is tracked via opencode spend.

## 3. Definitions (Scrum)

**Definition of Ready** — a WI enters READY only with: (a) linked `G-##` goal, (b) one-line observable outcome, (c) dependencies/blockers named, (d) size S/M/L (S = one session, M = a few, L = decompose first).

**Definition of Done** — QA verdict APPROVE + gate signed where applicable + verification commands green + board row updated + SESSION_HANDOVER touched if project state changed.

**Sizing rule:** a WI is sized to *one execute session* (≈ Build's 150-step cap). Bigger ideas stay at GOAL level until decomposed. This keeps plan→execute 1:1 and makes "what can be done now" literal.

## 4. Naming conventions

| Thing | Convention | Example |
|---|---|---|
| Goals | `G-##-<kebab-slug>.md`, zero-padded, never renumbered | `G-001-dual_market_screener.md` |
| Work items | `WI-##` on the board; referenced everywhere by ID only | `WI-002` |
| Designs (ADRs) | `D-##-<kebab-slug>.md`; status field: `proposed / accepted / superseded-by-D-##` | `D-002-model-signal-diagnostics.md` |
| Plans | `YYYY-MM-DD-WI-##-<kebab-slug>.md` (date-first = sortable; WI = traceable) | `2026-10-22-WI-002-model-signal.md` |
| Retros | `retros/YYYY-WW.md` (ISO year-week) | `retros/2026-W43.md` |
| File style | kebab-case filenames; doc title = human phrase; IDs = uppercase | — |

**Mandatory doc headers:** every artifact opens with `ID`, `Title`, `Goal:` (for D/P), `Status`, `Date`. A row or design that can't be traced to a goal is noise — delete it or promote it.

## 5. Standard artifact sections

- **Goals:** Intention / Success criteria / Non-goals / Current state
- **Designs (ADR):** Context / Options considered / Decision / Consequences (positive & negative) / Status
- **Plans:** GOAL / CONSTRAINTS / STEPS (change + acceptance criterion + verification command) / OUT OF SCOPE / DEVIATIONS

## 6. Operating loop (three tiers)

| Tier | Who | Job | Tokens |
|---|---|---|---|
| **Interface / middle manager** | Hermes (GLM, cheapest) | Reads EXECUTION LOGs + board + handover → determines problems, what's next; verifies results; maintains board/handover; issues targeted execution tickets. Does NOT design. | ~$0.01/$0.20 per M |
| **Strategist** | Planner (Sonnet, brief-fed) + troubleshooter (Opus, stuck-only) + guide (Sonnet, on-demand learning) | Design decisions, root-cause diagnosis, teaching. Always brief-fed; never explores. | $2/$10 · $4/$20 |
| **Workhorse** | Build (DeepSeek V4 Pro) + reviewer/scribe (flash) | Executes plans, appends the EXECUTION LOG, records concerns; reviews; writes briefs + human docs. | ~$0.44/$0.89 · $0.09/$0.18 |

**Execution ticket format** (the Interface's output — paste into opencode, or Hermes submits via tmux):

```
EXECUTE WI-002 per docs/plans/<plan-file>.md, steps <range> only.
Do not improvise beyond the plan; verify each step with the plan's commands.
Append one line per step to ## EXECUTION LOG in the plan file; flag concerns inline.
Stop conditions per the workflow contract (2 fails → intervention brief + STOP for admin; tradeoff → flag).
Constraints: n_jobs<=2, float32, bounded memory, no secrets, no live trading.
```

**Division of judgment:** the Interface triages and routes — it must not design (two planning brains diverge). The Strategist decides *how*; the Workhorse decides *nothing* beyond its plan steps; the human decides *gates and priorities*.

## 7. Ceremonies (the light version)

| Ceremony | Origin | Here | Cadence |
|---|---|---|---|
| Gate review | PMP stage gate / sprint review | Admin approves gate evidence in `reports/`; failed gate blocks DONE | per sprint/WI |
| Weekly review | Scrum retro + refinement | 15 min: reorder READY, flag aging rows, lessons → `retros/YYYY-WW.md` | weekly (Mon) |
| Doc hygiene | PMP records mgmt | Router + handover freshness check, archive superseded docs | monthly |
| Change control | PMP ICC | Goals/designs superseded via linked doc, never edited | as needed |

## 8. Risk & change

- **`RISKS.md` is a living register** (PMP): probability / impact / owner / response per risk; reviewed weekly; a realized risk gets an immediate response work item.
- **Supersession = change control:** goals and designs are never edited in place; a new version links back. Intention history is always reconstructible.

## 9. Roles

- **Admin (you):** goals, READY ordering, gate sign-off, unblocking. Operating surface = BOARD.md + SESSION_HANDOVER.md only.
- **Plan agent:** designs (ADRs) and plans. Writes nothing else.
- **Build agent:** executes only the plan named in the board's EXECUTING row.
- **Reviewer:** read-only QA; verdict APPROVE / FIX BEFORE COMMIT with file:line findings.
- **Troubleshooter (Opus):** escalation-only; BLOCKED is an acceptable output, guessing is not.

## 10. What NOT to do
- Don't start Execute without a plan file path on the board.
- Don't move a card to DONE without a QA verdict.
- Don't put discussion in goal/design/plan docs — decisions and facts only.
- Don't add process: if a new artifact doesn't answer "what now / what next / why", it doesn't get created.
