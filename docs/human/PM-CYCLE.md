# PM Cycle — how the loop works (human guide)

> Kam runs opencode Build in the tmux TUI (VS Code Remote-SSH). Hermes acts as PM:
> it verifies finished work, updates the docs, figures out what's next, and hands
> you a ready-to-paste prompt. You never relay status by hand — the loop reads it
> from the artifacts.

## The loop (v2, 2026-10-25 — direct handoff, scoped auto)

```
┌──────────────────────────────────────────────────────────────────────┐
│  1. Hermes writes the brief + dispatches it DIRECTLY:                 │
│       opencode run --agent planner --auto "<prompt>"  → plan file     │
│     (detached, log to logs/, poll artifacts — never transcripts)      │
│  2. Hermes verifies the plan (contract: per-step verify commands),    │
│     then dispatches Build the same way (--agent build --auto)         │
│  3. Build finishes → STATUS: DONE|BLOCKED|ERROR line in the plan      │
│  4. Hermes PM cycle: ingest → verify → update docs → pick next →       │
│     write brief → STOP at every human gate (admin decides)           │
│  5. GOTO 1 (after your gate word)                                     │
└──────────────────────────────────────────────────────────────────────┘
```

**Scoped auto (admin decision 2026-10-25):** Build/planner run headless with
`--auto`, which approves everything NOT explicitly denied in
`~/.config/opencode/opencode.jsonc` → `agent.build.permission` (deny precedence
verified live 2026-10-25: `git push` blocked, `git status` passes). Denied:
push/remote/filter-branch, `rm`/`rmdir`, sudo, curl/wget/webfetch, ssh/scp/
rsync, nc/ping. Escalation tiers stay human-gated via escalation.md.

**TUI fallback:** any cycle can still run the old way — paste the brief into
the tmux TUI and watch. Hermes then ingests from `opencode.db` as before
(`session_v2` / `session_message.data`, see the Hermes skill).

**Token discipline (why this is cheap):** heavy generation stays on opencode's
flash models either way. Hermes overhead is bounded by the same brief rule —
poll artifacts/STATUS lines/logs with completion markers (`EXIT:0`), sleep in
10-minute steps, never ingest full transcripts.

**Completion/human-attention notifications (2026-10-25):**
- `scripts/notify_gate.sh` — zero-model-token watcher. Detach it alongside any
  long run: it polls a log/plan file for a marker (`EXIT:0`, `STATUS: DONE`)
  and posts ONE Discord ping via `DISCORD_WEBHOOK_URL` from `signals/.env`
  (gitignored; create the webhook in Discord: #general → Integrations →
  Webhooks). State file prevents re-notify. `--once` posts immediately.
- Hermes (PM) also posts gate pings to #general at cycle close via the Hermes
  Discord connector (verified live 2026-10-25, message `1563790860699570241`)
  — this path needs no webhook and works today.
- Polling costs NO model tokens by design: the watcher is shell+curl; Hermes
  enters only after the marker (PM verification), and gate decisions stay
  with the admin either way.

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
