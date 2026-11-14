# quant-screener — dual-market leak-free quantitative screener (MVP closed 2026-11-01)

Setup, how to run, how to reproduce, limitations.

- **Run:** `uv sync` · full suite `uv run pytest` (~7–8 min) · daily shortlist `uv run python scripts/wi014_screener.py --market CAD|USD`
- **Start here (agents):** `AGENT.md` (router) → per-dir `INDEX.md` → `docs/workflow/BOARD.md` (queue)
- **Humans:** `docs/governance/MVP_CLOSURE_REPORT.md` (closure), `docs/governance/PHASE2_HANDOVER_RUNBOOK.md` (Phase 2 setup/backlog/rollback)
- **Doc map:** `docs/README.md` · **Negative results (do not repeat):** `docs/architecture/DECISIONS_AND_NEGATIVE_KNOWLEDGE.md` · **WI ledger:** `docs/execution/WI_AND_RUN_LEDGER.md`
- **Product verdict:** E5 factor screener (WI-014) is the MVP signal; NO_TRADE default; no automated order execution (research shortlist only, human gate).
- **Limitations:** costs/slippage are assumptions (not realized fills); coverage not instrumented; 34 source files exceed the 250-line law (debt register D-1, first Phase 2 task).