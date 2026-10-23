---
name: gate-brief
description: Turn a sprint/gate report into a one-page human briefing with thresholds-vs-actuals, self-check commands, and the decision requested. Mode 2: write an intervention brief when execution is stuck, so the admin chooses the escalation path.
---

# gate-brief

**Trigger:** whenever a sprint/gate report is generated or updated (`reports/sprintN_*.md`), or the admin asks for a gate briefing. One job: turn the gate evidence into a ≤1-page human briefing.

**Inputs:** the gate report + the plan file for the work item + the board row (goal trace) + any prior gate reports this one depends on.

**Output:** `docs/human/briefings/YYYY-MM-DD-gate<N>-<slug>.md` — human stream, never loaded into agent context. Then tell the admin the path and the decision requested, and STOP (gates are human decisions).

**Template (fill every section, expand all jargon once):**

```markdown
# Gate N Brief — <name> (WI-##, traceable to G-##)

**Verdict in one line:** <what the evidence says, e.g. "models failed 4/4 governance thresholds">
**Decision requested:** APPROVE to continue | HOLD (need X) | REJECT (redo sprint)

## What was supposed to happen
<1-3 sentences, plain language, from the plan file's GOAL>

## What actually happened
<2-5 sentences. Cite the report; do not paraphrase numbers — quote them.>

## The numbers that decide this
| Metric | Threshold (why) | Actual | Pass? |
<!-- every row from the gate report that carries a threshold; add a plain-language
     "why" column so the admin doesn't need Design/05 open -->

## Check it yourself (5 minutes)
<!-- exact commands/paths for manual review; the admin WANTS this -->
- `uv run pytest tests/test_leakage.py -k <name>` — expect: <outcome>
- `reports/sprintN_*.md` §<section> — look at: <what>
- <anything visual: which PDF pages, which chart>

## Risks & what could be wrong
<bullets; if a failure, the leading hypothesis for why>

## One thing worth learning
<the single concept this gate teaches (e.g., embargo, calibration), 2-3 sentences>

## How to respond
- "gate N approved" → agents continue to sprint N+1 (board row moves)
- "hold — <question>" → work stops, question lands in Deviations
- "reject" → back to PLAN with the evidence bundle
```

**Rules:**
- Never invent a verdict: the gate report is the source of truth; if it lacks a threshold table, say so and request the missing metric instead of approving.
- A FAILED gate brief always states the stop consequence explicitly (work halts, board row → QA/GATE held).
- Keep to one page. Evidence links over prose. Second person, no hype.
- After writing the brief, update the board row's evidence link to include the brief path.

---

## Mode 2 — Intervention Brief (stuck-state escalation)

**Trigger:** a plan step has failed twice, or the agent is about to escalate to a stronger model. Written by the executing agent BEFORE any escalation. One job: let the admin choose the path in under 2 minutes.

**Output:** `docs/human/interventions/YYYY-MM-DD-WI-##-step<N>.md`, then a ≤5-line chat summary pointing at it. Then STOP — no escalation happens until the admin chooses.

**Template:**

```markdown
# Intervention Brief — WI-## step N (escalation checkpoint)

**Situation (2 lines):** what this step was supposed to do, and what happened instead.

## What was tried (from ## EXECUTION LOG)
| Attempt | Change made | Result |
|---|---|---|

## Evidence
- Exact failing command + full error (verbatim, trimmed to the relevant part)
- Files/lines touched so far; git diff stat
- What still works vs what is broken

## Options
| Path | What happens | Est. cost | My recommendation |
|---|---|---|---|
| a. GLM troubleshooter (first tier) | evidence-bundle diagnosis → fix plan | ~$0.02 | |
| b. Sonnet planner redesign | plan revised for this blocker | ~$0.10–0.30 | |
| c. Opus 5.5 diagnosis | maximum-model diagnosis | ~$0.5–2 | |
| d. Admin takes over | agents stand down | your time | |

## What to check yourself (2 minutes)
- <exact commands/paths>

**Response format:** "a" / "b" / "c" / "d — I'll drive" (+ any redirection).
```

**Rules (mode 2):**
- Both failed attempts MUST be in the table — no hiding.
- The recommendation column is mandatory for every option, including "d".
- If the evidence is ambiguous, say what single additional experiment would disambiguate it before the admin chooses.
- After the admin responds, log their choice on the plan file's EXECUTION LOG line for this step.
