# AGENT.md — router for coding agents (repo rules: AGENTS.md; process: docs/workflow/WORKFLOW.md)

## Stack & constraints
Python >=3.11 via `uv` (pyproject: quant-screener). numpy/pandas/pyarrow/sklearn/xgboost-cpu/torch-cpu/matplotlib. Forbidden: n_jobs=-1 (use 2), float64 feature frames (cast float32), all-ticker uncompressed frames (pyarrow.dataset or symbol-sequential), secrets in git. Host: 2 vCPU / 8 GB.

## Canonical commands
- Sync: `uv sync` · Test single file: `uv run pytest tests/test_<name>.py -q` · Full suite: `uv run pytest` (~7-8 min, run detached, poll log)
- Daily shortlist: `uv run python scripts/wi014_screener.py --market CAD` (or USD)

## Context routing (read order)
1. `docs/workflow/BOARD.md` — what now / next
2. Local `INDEX.md` in any dir you touch (src/, src/<pkg>/, scripts/, tests/) BEFORE loading full sources
3. `docs/architecture/DECISIONS_AND_NEGATIVE_KNOWLEDGE.md` BEFORE proposing model/architecture changes (negative register — do not repeat failed approaches)
4. Governance: `docs/governance/MVP_CLOSURE_REPORT.md`, `PHASE2_HANDOVER_RUNBOOK.md`; ledger: `docs/execution/WI_AND_RUN_LEDGER.md`
5. Archived specs: `docs/archive/` (frozen Design baseline) — read-only history

## Role boundaries (kanban lock protocol)
- **Hermes (orchestrator/PM):** owns docs/, .hermes/locks.json, and opencode dispatch. Never edits application source or test files.
- **OpenCode (builder):** reads ONLY this AGENT.md, its assigned `docs/kanban/in_progress/WI-XXX.md`, and the exact files/line-ranges in that WI's `write_files`/`read_only_files` manifest. Edits outside `write_files` are reverted by the orchestrator.
- **Locks:** before any WI moves to in_progress, its `write_files` must be free in `.hermes/locks.json`; the orchestrator registers/releases them.

## Code style law
Max 250 lines per source file; domain-package placement (src/<wi> / src/perfanalytics), no new monolithic utils/. Split existing oversize files only under a WI plan with targeted tests (debt register D-1).
