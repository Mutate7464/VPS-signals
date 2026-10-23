# PM Cycle — how the loop works (human guide)

> Kam runs opencode Build in the tmux TUI (VS Code Remote-SSH). Hermes acts as PM:
> it verifies finished work, updates the docs, figures out what's next, and hands
> you a ready-to-paste prompt. You never relay status by hand — the loop reads it
> from the artifacts.

## The loop

```
┌─────────────────────────────────────────────────────────────┐
│  1. You run Build in opencode tmux (paste the prompt PM gave)│
│  2. Build finishes, writes STATUS: DONE|BLOCKED|ERROR line   │
│  3. You tell Hermes: "run PM cycle"                          │
│  4. PM: ingest → verify → update docs → pick next →          │
│     write brief + prompt → hand back to you                  │
│  5. GOTO 1                                                   │
└─────────────────────────────────────────────────────────────┘
```

## What the PM does on each cycle

1. **Ingest** — reads new opencode sessions (since the last PM_LOG cursor), the
   plan file's EXECUTION LOG, and the final STATUS line. Does not trust chat claims.
2. **Verify** — runs deterministic verifiers where they exist (e.g.
   `uv run python -m src.verify_synced_data`); otherwise reviews the evidence
   Build logged. A "done" claim without a QA-verdict reference does not move a row to DONE.
3. **Update docs** — board rows (evidence cell), `SESSION_HANDOVER.md`, `RISKS.md`.
   QA exceptions are marked ⚠ inline, never silently.
4. **Figure out what's next** — proposes the next work item from the board
   (admin-ordered READY top-down) plus anything from your feedback. You confirm the choice.
5. **Prepare the handoff** — writes a ≤60-line context brief for the opencode
   planner (so the planner reads a brief instead of exploring the repo — cheap
   flash input), and gives you the exact prompt to paste into opencode.
6. **Log the cycle** — appends to `docs/workflow/PM_LOG.md` with the session cursor.

## What you do

- Run Build with the prompt the PM gives you (paste into opencode TUI).
- Feed feedback into the PM cycle ("the VIF threshold is too loose, cap it at 5")
  — the PM folds it into the brief and the board row.
- Decide at gates and at each "what's next" confirmation — the PM proposes, you order.

## Where things live

| Artifact | Path |
|---|---|
| Board (queue / what now) | `docs/workflow/BOARD.md` |
| Framework | `docs/workflow/WORKFLOW.md` |
| Cycle log (cursor) | `docs/workflow/PM_LOG.md` |
| Planner briefs | `docs/workflow/briefs/` |
| Plans | `docs/plans/YYYY-MM-DD-WI-##-<slug>.md` |
| Intervention briefs | `docs/human/interventions/` |
| Risk register | `docs/workflow/RISKS.md` |
| Weekly retros | `retros/YYYY-WW.md` |

## Cost expectations

The PM cycle itself runs on Hermes (GLM-5.3) — reading logs and writing briefs,
not exploring the repo. The brief discipline keeps opencode planner input cheap
(flash-brief ≈ $0.09/M tokens vs Sonnet exploring at $2/M). Escalations stay on
the existing ladder (GLM troubleshooter → Sonnet redesign → Opus → you).
