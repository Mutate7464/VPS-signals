# MODE_PROMPTS.md — HITL operator cheat sheet (signals)

> Source: ML Screener prompt pack (attached 2026-11-07), adapted to this repo: WI files replace `batch_spec.md`, BOARD replaces `state_tracker.md`, and the dispatch command is the repo-verified form. Process rules: `WORKFLOW.md`. Design: `designs/D-020-*.md`.

**Always `/clear` (or start a new session) before switching model roles.** The incoming role reads files on disk only.

---

## 0. Bootstrap (once)
Model: architect (Sonnet; Opus for the initial ADR).
```
[MODE: ARCHITECT] Read docs/workflow/BOARD.md and docs/workflow/WORKFLOW.md.
Goal: <ONE SENTENCE>. Create G-## if missing. Add TODO rows for the first 3 WIs (flat format).
Draft WI-001 into docs/kanban/draft/ using _TEMPLATE_WI.md. Set BOARD row to [TODO]. Do not write code. Halt.
```
Halt: `=== HALT: ARCHITECT COMPLETE -> REVIEW BOARD + draft WI -> /clear -> SWAP TO [MODE: CONTROLLER] or [MODE: EXECUTOR] ===`

## 1. Architect (plan a WI)
Model: Sonnet (default); Opus for new ADRs.
```
[MODE: ARCHITECT] Read docs/workflow/BOARD.md (ACTIVE rows only) and docs/workflow/DATA_CONTRACT.md.
Move the top [TODO] WI to docs/kanban/draft/ if not already there. Fill WI sections 1–3 under the 400-token cap.
Name the exact paths, columns, dtypes, the dry-run subset, and the stdout rule. Do not write implementation code. Halt.
```
Halt: `=== HALT: ARCHITECT COMPLETE -> REVIEW WI FILE -> /clear -> SWAP TO [MODE: EXECUTOR] ===`

## 2. Controller (optional, verify + compress)
Use only when paths or schemas are unverified or the spec exceeds 400 tokens. Model: GLM or Hermes default.
```
[MODE: CONTROLLER] Read the draft WI file only. Verify each path in write_files and read_only_files exists.
For parquet inputs, run pyarrow.parquet.read_schema (metadata only, ≤15 lines stdout).
Compress the WI body to ≤400 tokens. Do not dump rows. Halt.
```
Halt: `=== HALT: CONTROLLER COMPLETE -> REVIEW WI FILE -> /clear -> SWAP TO [MODE: EXECUTOR] ===`

## 3. Executor (run one locked WI)
Model: surgical-builder (DeepSeek Flash) via opencode. Admin approves dispatch (gate).
```
[MODE: EXECUTOR] Read docs/kanban/ready/WI-###.md only. Lock write_files in .hermes/locks.json, move to in_progress/.
Run: /home/yycuser/.opencode/bin/opencode run --agent surgical-builder --auto --format json "Execute docs/kanban/in_progress/WI-###.md strictly within write_files. Stdout <=5 lines."
Then run the WI test_command (exit code only). Fill the telemetry footer. Update BOARD row. Release locks. Halt.
```
Halt: `=== HALT: EXECUTOR COMPLETE -> REVIEW BOARD row + WI footer -> /clear -> SWAP TO [MODE: ARCHITECT] ===`
On a second failed attempt: move to `blocked/`, set `[BLOCKED]` with a 1-line reason, and halt without retrying.

## 4. Recovery (a WI is [BLOCKED])
Model: GLM for schema and syntax fixes. Opus for logic flaws. `/clear` first.
```
[MODE: ARCHITECT] Read the WI file and the blocked row in BOARD only. Inspect the 1-line error. Do not dump data.
Write a corrective constraint into the WI, move it back to ready/, and halt for re-execution.
```
Halt: `=== HALT: RECOVERY COMPLETE -> REVIEW WI -> /clear -> SWAP TO [MODE: EXECUTOR] ===`

---

**Rule:** a turn runs one mode only. Each mode ends with its halt banner.
