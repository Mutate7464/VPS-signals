# AGENTS.md — Signals Project Rules

> Process: `docs/workflow/WORKFLOW.md` (goal → design → plan → execute → QA, v2) ·
> Board: `docs/workflow/BOARD.md` (single source for "what now / what next") ·
> Risks: `docs/workflow/RISKS.md`. Agents read the board at task start. Build executes
> only the plan named in the board's EXECUTING row; DONE requires a QA verdict and,
> where applicable, the human gate.

## Hard constraints (every task, every agent)

- Host: 2 vCPU / 8 GB / no swap — Hostinger KVM 2 with CPU credits. `n_jobs=2` everywhere (never -1). Cast feature
  DataFrames to `float32` immediately after calculation. No all-ticker uncompressed
  DataFrame — `pyarrow.dataset` or sequential symbol iteration. PDF charts: batch 10,
  `matplotlib.pyplot.close('all')` + `gc.collect()` per batch. **Burn rate (Hostinger
  credit model, details in Hermes skill `hostinger-vps-cpu-credits`):** full balance =
  3 h @ 100% CPU; sustained steady-state < 60% of vCPUs; heavy jobs get an explicit
  core-hour cap in the WI spec, `n_jobs=2`, checkpointed; pause ≥ 30 min if modeled
  balance < 25%.
- Daily shortlist only. Human gate on every sprint gate. No auto-execution of orders.
  No secrets in git. (`.agents/rules/` — env-split, no-live-trading, quant-ml.)
- File-lock protocol (2026-11-02): surgical WIs staged in `docs/kanban/` with `write_files` manifests; locks in `.hermes/locks.json`; technique in WORKFLOW.md §2 + Hermes skills `kanban-orchestrator`/`expert-synthesizer`. Hermes never edits source; OpenCode surgical-builder reads only the WI + its locked line ranges.
- Commands: `uv sync`, `uv run pytest`.
- Docs & backlog live in `/docs/`; human-facing stream in `docs/human/GUIDE.md`
  (never loaded into agent context; refreshed by scribe).
- Roles, mode gates, token caps (WI spec ≤400 tokens, BOARD ≤5 KB, PM_LOG keep 2):
  `docs/workflow/designs/D-020-lean-hitl-tri-role-workflow.md`. Mode prompts:
  `docs/workflow/MODE_PROMPTS.md`. Data facts: `docs/workflow/DATA_CONTRACT.md`.
  One role per session; hand off through files; `/clear` between roles.
