# AGENTS.md — Signals Project Rules

> Process: `docs/workflow/WORKFLOW.md` (goal → design → plan → execute → QA, v2) ·
> Board: `docs/workflow/BOARD.md` (single source for "what now / what next") ·
> Risks: `docs/workflow/RISKS.md`. Agents read the board at task start. Build executes
> only the plan named in the board's EXECUTING row; DONE requires a QA verdict and,
> where applicable, the human gate.

## Hard constraints (every task, every agent)

- Host: 2 vCPU / 8 GB / no swap. `n_jobs=2` everywhere (never -1). Cast feature
  DataFrames to `float32` immediately after calculation. No all-ticker uncompressed
  DataFrame — `pyarrow.dataset` or sequential symbol iteration. PDF charts: batch 10,
  `matplotlib.pyplot.close('all')` + `gc.collect()` per batch.
- Daily shortlist only. Human gate on every sprint gate. No auto-execution of orders.
  No secrets in git. (`.agents/rules/` — env-split, no-live-trading, quant-ml.)
- Commands: `uv sync`, `uv run pytest`.
- Docs & backlog live in `/docs/`; human-facing stream in `docs/human/GUIDE.md`
  (never loaded into agent context; refreshed by scribe).
