# opencode Build model escalation — consolidated record (2026-10-24)

> Replaces nine overlapping intervention variants (`*-update*`, `*-summary*`, `*-verification-report`, `*-implementation-summary`, `*-build-agent-qwen-removal`) written during the day's config churn. One record, kept for audit. Current model state is ALWAYS read from `opencode debug agents` + `~/.config/opencode/opencode.jsonc` on disk — dated docs are history, not state.

## What was requested
Establish the Build agent's tiered escalation path with human gating and cost discipline:
Base `deepseek-v4.1-flash` → Intermediate `deepseek-v4.1-pro` → A1 `google/gemini-4-argon` (discounted) → Frontier `anthropic/claude-opus-5.5`; Qwen removed from the Build role.

## What actually happened (drift, found and fixed by PM 2026-10-24 ~23:00 UTC)
- The day's intervention docs claimed Build had been moved to v4.1-flash, but the live config had `agent.build.model = openrouter/qwen/qwen3-coder` (the earlier "switch Build to Qwen3 Coder" direction had overwritten it) while the global default `model` field was already v4.1-flash — the agent override won, so Build ran Qwen and the docs were wrong.
- Fix: `agent.build.model` → `openrouter/deepseek/deepseek-v4.1-flash`; stale header/build-block comments in `opencode.jsonc` and model references in `prompts/triage.md` updated; `opencode reload` + TUI restart; verified via `opencode debug agents` (build = deepseek/deepseek-v4.1-flash, steps 150, escalation chain intact).

## Current state (verified 2026-10-24)
- Build base: `openrouter/deepseek/deepseek-v4.1-flash`; escalation_models: `deepseek-v4.1-pro` → `google/gemini-4-argon` → `anthropic/claude-opus-5.5` (human-gated per `~/.config/opencode/instructions/escalation.md`).
- Planner `qwen/qwen3-coder`; Triage `qwen/qwen3-coder-next` (long-context fallback `nvidia/nemotron-3.5-super-vl`); reviewer/scribe `deepseek-v4-flash`; guide Sonnet 5.5; troubleshooter `z-ai/glm-5.3`.
- `small_model` = `deepseek-v4-flash` (titles/summaries/compaction).

## Lessons
- Dated docs can contradict the config: verify with `opencode debug agents` before believing any model-state claim.
- The nine variants were a symptom of a process gap: each model-change cycle spawned new docs without reconciling the old ones.
