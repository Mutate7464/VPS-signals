# D-020 — Lean HITL tri-role workflow (token-optimized)

**ID:** D-020 · **Title:** Lean human-in-the-loop tri-role workflow · **Goal:** G-003 (process integrity) · **Status:** accepted 2026-11-08 (admin: "proceed with recommendations") · **Date:** 2026-11-07
**Extends:** WORKFLOW.md v2 (§2 board, §6 tiers, §11 read discipline). Supersedes nothing.

## 1. Context
Admin brief: keep human-in-the-middle and light kanban; reduce token use. The attached ML Screener pack proposes a tri-model HITL flow: Opus (architect) → GLM (compress/verify) → DeepSeek Flash (execute via opencode), flat state files, `/clear` between swaps, micro-batch specs ≤400 tokens.

**Measured current usage** (bytes; tokens ≈ bytes/4), 2026-11-07:

| Artifact | Bytes | Loaded when | Finding |
|---|---|---|---|
| `signals-workflow-execution` SKILL.md | 64,548 | any signals task (skill rule: load if partially relevant) | Largest single cost, ~16k tokens. **Slimmed 2026-11-07** (see §4.7). |
| `docs/workflow/BOARD.md` | 16,158 | every task start | 3.2× its own ≤5 KB budget (WORKFLOW §2). |
| `docs/workflow/PM_LOG.md` | 21,874 | PM cycles | 13 cycle entries. Rule keeps 2, so 11 are overdue for archive. |
| `docs/workflow/WORKFLOW.md` | 13,364 | planners, PM | Repeated in skills. **Rewritten lean 2026-11-07.** |
| opencode `instructions/workflow.md` + `escalation.md` | 5,018 + 5,792 | injected into every opencode run | ~2.7k tokens per run. `.tmp` and `.tmp2` copies present. Outside repo. |
| `AGENTS.md` + `.cursorrules` | 1,447 + 328 | every session | Acceptable. |
| `RISKS.md` | 3,888 | weekly | Acceptable. |

- Opencode sessions, last 14 days: 42 sessions, 2,253 messages. **24 of 42 sessions have a null model field** (observability gap).
- Conflict: WORKFLOW §6 names Opus as troubleshooter. `~/.config/opencode/agents/troubleshooter.md` pins `z-ai/glm-5.3`. One must change (decision 3 below).

## 2. Attachment-to-repo mapping

| Attachment artifact | Repo equivalent | Decision |
|---|---|---|
| `state_tracker.md` §2 flat board | `docs/workflow/BOARD.md` | **Keep BOARD.md.** A second board violates WORKFLOW §2 and the kanban-orchestrator "merge, not parallel system" rule. Flatten rows (§5). |
| `state_tracker.md` §1 data contract | `docs/workflow/DATA_CONTRACT.md` (new) | **Add.** Read on demand, not per task. |
| `state_tracker.md` §3 telemetry (overwrite) | Last 5 lines of the WI telemetry footer | **Merge.** No separate file. |
| `batch_spec.md` ≤400 tokens | `docs/kanban/_TEMPLATE_WI.md` | **Use the WI file as the batch spec.** Add I/O block, stdout ≤5 lines, 400-token cap. |
| `opencode run "…"` inline command | kanban-orchestrator dispatch: absolute binary, `--agent surgical-builder --auto --format json` | **Keep the repo-verified form.** |
| MODE prompts, halt banners | `docs/workflow/MODE_PROMPTS.md` (new) | **Add.** Banners kept verbatim. |
| Opus for every architecture step | WORKFLOW §6 Strategist: planner Sonnet, Opus escalation-only | **Reject Opus as default.** Per the §6 price table, Opus ($4/$20) is 2× Sonnet ($2/$10). Use Opus for new ADRs and after a two-strike block. |
| GLM compression phase | Controller verify step | **Make optional.** Run only when paths or schemas are unverified. |
| `/clear` between roles | Keep | **Adopt.** Gates are stateless because state lives in files. |
| "No Agile/PMP prose" | WORKFLOW §10 | **Adopt.** Enforced by the 400-token cap. |

## 3. Options considered
- **A. Adopt the attachments literally** (new `state_tracker.md` and `batch_spec.md` beside BOARD and kanban). Rejected: two boards, and locks and PM_LOG disconnected from the tracker.
- **B. Merge into repo artifacts with token caps.** **Chosen.** Same roles, fewer files, enforced budgets.
- **C. Status quo plus skill trim only.** Rejected: BOARD and PM_LOG overruns persist, and the per-run opencode injection is untouched.

## 4. Decision (proposed)
1. **Roles.** ARCHITECT (planner model: Sonnet default, Opus for ADRs and escalation) → CONTROLLER (optional verify) → EXECUTOR (surgical-builder, DeepSeek Flash) → HUMAN gate. **Default is two model swaps, not three.**
2. **Board.** `BOARD.md` is the only board. Flat one-line rows (§5). Evidence cell ≤1 line; detail lives in the WI log or report.
3. **Spec.** `docs/kanban/<state>/WI-###.md` is the batch spec. Hard cap **400 tokens (~1,600 bytes)** for the blueprint plus I/O block. Larger work splits into WIs.
4. **Data contract.** `DATA_CONTRACT.md`, read on demand by the architect. The executor reads only the WI file and its `read_only_files`.
5. **Executor output.** stdout ≤5 lines; WI telemetry footer; `STATUS:` line in the log.
6. **Opencode base instructions.** Trim `workflow.md` and `escalation.md` to ≤2 KB combined, and delete `.tmp`/`.tmp2` copies. **Admin action** (outside repo, one-way delete). Target ≤1.5k tokens injected per run.
7. **Skill.** `signals-workflow-execution` slimmed to a core file. Verbatim archive at `references/pm-cycle-lessons-archive.md`. **Done 2026-11-07.**
8. **Locks.** Keep the lock registry. It costs ~50 tokens per WI and protects parallel dispatch.
9. **Rotation (weekly, overdue).** PM_LOG keeps the last 2 cycles. BOARD DONE rows older than 7 days collapse to one line. Separate approved step; not executed in this pass.

## 5. Flat BOARD row format
`[STATE] WI-### | title | G-## | write_files or plan path | evidence (1 line)`

| Board token | Kanban dir | Meaning |
|---|---|---|
| `[TODO]` | `docs/kanban/ready/` | Meets DoR, admin-ordered |
| `[WIP]` | `docs/kanban/in_progress/` | Locked, dispatched (WIP limit 1 for EXECUTING) |
| `[BLOCKED]` | `docs/kanban/blocked/` | Two-strike breaker tripped; owner + 1-line reason |
| `[DONE]` | `docs/kanban/done/` | QA verdict and gate recorded |

## 6. Consequences
- **Expected savings (estimates, not yet measured on real runs):** signals skill ~16k → ~1k tokens per signals session. BOARD 16 KB → ≤5 KB after rotation. Opencode per-run injection ~2.7k → ≤1.5k after trim.
- **Costs:** each model swap still re-reads its inputs. `/clear` reduces this but does not remove it. Archived lessons are only found by search, which is why the archive is kept verbatim.

## 7. Falsification (what would change this)
- If session telemetry shows the skill is rarely loaded, the skill saving is smaller than estimated. Measure with `session_search` before claiming savings.
- If executor failures rise under the 400-token cap (more splits, more two-strike blocks), raise the cap to 600 for L-sized work.
- If the Sonnet architect misses framing that Opus caught in recent gates, move ADRs back to Opus.

## 8. Open decisions (REC first)

| # | Question | REC | Basis |
|---|---|---|---|
| 1 | Keep `BOARD.md` as the single board, or rename to `state_tracker.md`? | Keep `BOARD.md` | Avoids two boards. |
| 2 | Architect default: Sonnet or Opus? | Sonnet; Opus for ADRs and two-strike escalations | Price ratio from §6 table. Quality difference is unverified. |
| 3 | Troubleshooter: Opus (WORKFLOW §6) or GLM-5.3 (agent file)? | Opus, escalation only. Update the agent file to match. | Documented conflict. |
| 4 | Approve PM_LOG rotation and BOARD demotion now? | Yes | Overdue (11 cycles over the keep-2 rule). |
| 5 | Approve trim of opencode instructions, and delete `.tmp`/`.tmp2` and old config backups? | Yes, after diff review | Outside repo; one-way delete. |
| 6 | Investigate null `model` field on 24 of 42 sessions? | Yes | Blocks per-model cost accounting. |

## 9. Resolution (2026-11-08)
- **Decisions 1–6 applied.** 1: BOARD.md kept, flattened (16,158 → 3,895 bytes). 2: Sonnet architect default, Opus for ADRs and escalation. 3: `agents/troubleshooter.md` set to `openrouter/anthropic/claude-opus-5.5`; `escalation.md` state_drift route updated to match (Gemini A1 step dropped). 4: PM_LOG rotated to the newest 2 cycles (3 headings: cycle 25 and both cycle-24 entries). Archived verbatim to `archive/PM_LOG-2026-10-29-to-11-01-cycles-19-23.md`. 5: opencode `workflow.md` + `escalation.md` trimmed from 10,810 to 1,743 bytes. The four `.tmp`/`.tmp2` files are deleted. The three `opencode.jsonc.backup.*` rollback copies are kept (they are not temp; delete on admin request). 6: see §10.
- **Measured byte deltas:** signals skill 64,548 → 4,207 (core); WORKFLOW 13,364 → 8,168; BOARD 16,158 → 3,895; PM_LOG 21,874 → 3,743 (+18,305 archived); opencode per-run injection 10,810 → 1,743.

## 10. Null `model` field: definition and resolution
- **Finding:** `session_v2.model` is NULL in 39 of 84 sessions (all time). These are mostly `build` and `planner` agent sessions. The model is not lost: each `assistant` row in `session_message.data` carries `model` as an object (`id`, `providerID`). The 59 assistant messages sampled from the 12 most recent null-model sessions all carried it.
- **Definition (current need: per-model cost and PM ingest):** `model` = `session_v2.model.id` when set, else the `model.id` of the first `assistant` message in `session_message`. Provider = `providerID` from the same object.
- **Applied:** rule added to `signals-workflow-execution` core (session ingest). The old PM ingest query in the archive is superseded by this rule.
- **Still open:** the root cause (why `session_v2.model` is not written for those sessions) is an opencode-side behaviour, not verified. Capture it on the next opencode upgrade check.

## 11. Repo state
Committed on 2026-11-08 in one commit by explicit path (WORKFLOW §2): WORKFLOW.md, AGENTS.md, D-020, BOARD.md (flat), PM_LOG.md (rotated), MODE_PROMPTS.md, DATA_CONTRACT.md, `_TEMPLATE_WI.md`, and the two new archive files. Not pushed. Outside-repo changes (opencode config, skill) are not in git.
