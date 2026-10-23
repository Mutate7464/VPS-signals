# PM_LOG.md — cursor for the Hermes PM cycle

> One entry per PM cycle, newest first. The newest entry's cursor (`cursor:` line)
> defines which opencode sessions the next cycle ingests. Kam's trigger: tell Hermes
> "run PM cycle". Full procedure: `docs/human/PM-CYCLE.md`.

## 2026-10-23 — Cycle 0 (role adopted)
- Change: PM role added to the workflow. Build contract now requires a final
  `STATUS: DONE|BLOCKED|ERROR` line in the plan file (`~/.config/opencode/instructions/workflow.md`).
- cursor: session-since 2026-10-23 (all sessions before this line predate the PM cycle)
- Note: WI-002 was EXECUTING at adoption; its completion was tracked manually, not via a PM cycle.
