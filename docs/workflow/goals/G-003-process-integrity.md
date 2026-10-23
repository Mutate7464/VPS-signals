# G-003 — Process integrity (gates actually gate)

**Intention (one line):** the HITL gate protocol in AGENTS.md is enforced in practice, not just written — a failed gate stops the pipeline until explicitly cleared by the admin.

**Why it exists:** on 2026-10-21, Sprint 5 compiled and shipped screener PDFs even though Gate 4 model QA FAILED on all targets. The gate existed on paper and was skipped in practice. Untrustworthy output almost entered the decision loop.

**Success criteria:**
- Workflow makes QA a blocking column (WORKFLOW.md — done 2026-10-22).
- Reviewer agent prompt checks gate compliance for sprint-type work.
- Any future "DONE with QA exception" requires a named admin decision recorded on the board row.

**Work items:** WI-006 (READY — residual: reviewer prompt gate check).
