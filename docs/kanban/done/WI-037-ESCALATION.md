# WI-037 ESCALATION — Strike 1 (builder exit incomplete)

## §A Verified current state (tool-checked 2026-11-09, this session)
- `logs/wi037.out` (builder log, 138 KB) last write 17:24; ends mid-run, no STATUS/EXIT marker, telemetry footer unfilled.
- No builder process alive: `pgrep -af opencode` shows only the 15-day interactive session (PID 910445, started Oct 25) and `opencode serve`.
- `src/swing_bsh/hold_filter_gate.py` EXISTS, 18,889 bytes, mtime 2026-11-09 17:38 — written after the log stopped (partial artifact, builder state unverified).
- `tests/test_swing_bsh_hold_filter.py` DOES NOT exist.
- `reports/wi037_summary.md` DOES NOT exist; no `/tmp/wi037_smoke`; no `data/models/wi037/`.
- Locks: WI-037 holds both write_files in `.hermes/locks.json` (acquired 2026-11-09).
- CPU credits: 8636/8640 (100%), burst 3.0 h — cap 0.5 core-h safe.

## §B Acceptance criteria
Per WI file §3: edits only in write_files; test_command exit 0; ADOPT/REJECT both markets under ADOPT_LOOSE_4OF5 + CB-05 5-seed placebo; `reports/wi037_summary.md` with fold tables, pooled edge, τ, verdict; no pickle unless ADOPT.

## §C Ranked concerns
1. Source written after log stopped — provenance unclear. HOW TO VERIFY: builder re-reads `hold_filter_gate.py`, checks against WI §2 I/O contract (fold-matched pickle inference, τ grid on CALIB only, veto = P(hold)≥τ intersection); fix/extend, do not blind-rewrite.
2. Tests never written. HOW TO VERIFY: `uv run pytest tests/test_swing_bsh_hold_filter.py -q` exit 0 (synthetic veto/fold-mapping/leakage tests per WI §2).
3. Full run not executed. HOW TO VERIFY: PM runs full job after diff audit; report exists with both-market verdicts.

## §D Repro
- Resume dispatch: `opencode run --agent surgical-builder --auto --format json "Resume WI-037..."` (see logs/wi037_resume.out)
- Full job: `uv run python -m src.swing_bsh.hold_filter_gate --market ALL` (cap 0.5 core-h)

## §E Escalation path
Resume pass → diff audit → full run → close-out (done/, commit, locks released). Second incomplete exit → strike 2: revert, blocked/, expert-synthesizer, admin memo.

## §F Change log
- 2026-11-09 ~19:35 UTC: escalation doc written; strike-1 resume dispatched.
