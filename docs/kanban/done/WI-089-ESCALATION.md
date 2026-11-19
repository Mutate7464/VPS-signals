# WI-089-ESCALATION — Strike-1 resume in flight

## §A Verified current state (tool-checked this session, 2026-11-19 ~04:20 UTC)
| Item | State | How verified |
|---|---|---|
| Builder process | Original builder DEAD (step ceiling); resume builder dispatched detached, PID tracked in `logs/wi089_watch.pid`, watchdog `wi089_watch.sh` RUNNING | `pgrep -af 'opencode run'`; `bash ~/.hermes/scripts/wi089_watch.sh` |
| `src/visualizer/views/v2_sweep.py` | EXISTS, ~254 lines (target <250, trim interrupted) | `ls -la`, builder final report in `logs/wi089.out` |
| `tests/visualizer/test_v2_sweep.py` | EXISTS, 13 tests passed **before** final edits | builder report; suite NOT re-run since `years_in_range` + `compute_view` rewire + `_clean` trim + figures inlining |
| Test suite (`uv run pytest tests/visualizer -q --tb=short --maxfail=1`) | PASSED 75/75 earlier; STALE now (code changed after) | builder final message |
| USD panel probe | 0 mismatches vs pandas reference earlier; budget re-measure pending after `years_in_range` fix | builder final message |
| Telemetry footer | Still `PENDING` (no commit made) | `docs/kanban/in_progress/WI-089.md` read this session |
| git status | Only manifest files + pre-existing untracked `reports/`, `state/` — no unauthorized files | `git status --short` |
| git log | HEAD `86f1fd2` (dispatch commit); no builder commit | `git log --oneline -3` |
| Locks | `.hermes/locks.json` WI-089 entries in place | not yet re-read this session; release deferred to close-out |

## §B Acceptance criteria (from WI-089 DoD)
- Sweep matches reference pandas implementation (tested).
- 200/yr line labeled ILLUSTRATIVE.
- Watermark present.
- Test command exit 0 on CURRENT code; `v2_sweep.py` < 250 lines; telemetry footer filled with real numbers.

## §C Ranked concerns
1. **Stale test evidence** — code changed after the last green run. VERIFY: resume builder re-runs the WI test command in foreground; close-out requires exit 0 this run.
2. **`years_in_range` equivalence** — vectorised copy of the kpi definition must be numerically identical; VERIFY: new `pytest.approx(..., rel=1e-12)` equivalence test (builder task 2).
3. **Budget compliance** — compute ≤400 ms was the motivation for the fix; VERIFY: USD budget re-measure (builder task 4), numbers in the footer.
4. **Cross-view perf finding (out of manifest)** — `kpi.years_in_range` costs ~1 s on the full panel, affecting any view pricing trades/yr. NOT fixable in WI-089 (outside write manifest). Candidate follow-up WI on `src/visualizer/kpi.py`.

## §D Repro commands
```
cd ~/projects/signals
bash ~/.hermes/scripts/wi089_watch.sh            # RUNNING / FINISHED
uv run pytest tests/visualizer -q --tb=short --maxfail=1
git status --short
tail -c 2000 logs/wi089_resume.out               # resume log tail (never dump full json)
```

## §E Escalation path
- Resume completes green → PM close-out per kanban-orchestrator Stage 3 (footer patch, commit, git mv to done/, lock release, BOARD row, PM_LOG) then next draft WI or cron teardown.
- Resume dies incomplete again → Strike 2: revert uncommitted source changes, archive untracked artifacts to `logs/`, move card to `blocked/`, release locks, expert-synthesizer check, decision memo.

## §F Change log
- 2026-11-19 04:20 UTC: Strike-1 identified (builder step ceiling with 5 remaining tasks enumerated in its final message in `logs/wi089.out`); scoped resume dispatched detached (`logs/wi089_resume.out`, prompt names the 5 tasks and the keep/extend instruction); watchdog re-armed on new PID; cron `wi089-watchdog` left active.
