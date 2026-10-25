# WI-008 repair — quarantine analysis tests and report wiring

## GOAL
Fix both quarantine-analysis misclassifications, have report generation use the repaired implementation, and verify the report and full test suite before a scoped commit.

## CONSTRAINTS
- Preserve signatures of `level_step_test`, `multi_day_path_analysis`, and existing assertions.
- Do not mutate quarantine state, `data/dead_letter_tickers.csv`, or verifier config; do not perform reinstatement.
- `n_jobs ≤ 2`, `float32` for calculated feature frames, bounded memory <2 GB; process symbols sequentially and use Arrow column scans for parquet data.
- No web lookups, secrets, live trading, or all-ticker frame loads.
- Stop for the human if an assertion appears wrong or if more than 5 of 72 recommendations flip from the baseline (17 REINSTATE / 55 KEEP_QUARANTINED). Do not commit in either case.
- Commit only the five explicitly scoped paths listed in step 4; never stage with `git add -A`.

## DIAGNOSIS
- Reproduced: `uv run pytest tests/test_quarantine_analysis.py -q` gives 2 failed, 4 passed.
- `level_step_test` includes ratio `1.0` as a “clean” step; the reversal fixture has pre/post medians 10 and 9 (ratio 0.9), so it is incorrectly called SPLIT_LOOKALIKE. Near-unity is no persistent level shift. Require a non-identity simple-ratio shift and persistence evidence; retain clean persistent step behavior.
- `multi_day_path_analysis` treats up to two large returns anywhere in its window as isolated. The continuation fixture has two large moves separated by 10 bars and is incorrectly isolated; the isolated fixture’s spike and reversal are within 2 bars. Distinguish a nearby one/two-day round trip from separated subsequent movement.
- Caller discrepancy: `src/percase_quarantine_triage.py` currently imports `analyze_ticker_simple` from `src.simple_quarantine_analysis`, not the functions in `src.quarantine_analysis`. Wire report analysis to the repaired helper implementation; otherwise the report cannot reflect the repair.

## STEPS

1. **Repair the analysis helpers** — In `src/quarantine_analysis.py`, correct `level_step_test` so a near-1 ratio is not considered a step and only a persistent non-identity simple-ratio shift is SPLIT_LOOKALIKE. Correct `multi_day_path_analysis` so a nearby spike/reversal can remain isolated while significant returns separated by multiple sessions indicate a non-isolated path. Keep signatures unchanged and do not edit tests.
   - Acceptance: original step and isolated-spike fixtures still pass; reversal and separated-continuation fixtures return GENUINE_VOL / `is_isolated=False`.
   - Verify: `uv run pytest tests/test_quarantine_analysis.py -v`

2. **Wire report generation to the repaired implementation** — Update `src/percase_quarantine_triage.py` to use `src.quarantine_analysis` evidence rather than the disconnected `src.simple_quarantine_analysis` path. Preserve special-case handling, human-gate recommendations, and sequential per-symbol processing. Before replacing the report, retain a baseline copy outside the repository, compare old/new recommendations by unique symbol/market, and stop without committing if >5 flips.
   - Acceptance: candidate report has exactly 72 data rows; every row has an action and cited evidence; ambiguity remains explicit. Record every flip and old/new action in the execution log. If >5 flips, stop for human review.
   - Verify: `uv run python -m src.percase_quarantine_triage` followed by `uv run python -c "from pathlib import Path; p=Path('reports/wi008_quarantine_percase_evidence.md'); lines=p.read_text().splitlines(); rows=[x for x in lines if x.startswith('| ') and not x.startswith('| :') and 'Symbol | Market |' not in x and 'Recommendation | Count |' not in x]; assert len(rows)==72, len(rows); print(f'{len(rows)} report rows')"`

3. **Verify full suite** — Run the complete suite after the report change; allow the stated ~7 minutes.
   - Acceptance: all tests pass (including all 6 quarantine-analysis tests); no quarantine/dead-letter/verifier configuration changes.
   - Verify: `uv run pytest -q`

4. **Commit only after gates pass** — Check the diff and stage exactly the paths below; commit only if steps 1–3 pass and recommendation flips are ≤5.
   - Acceptance: commit contains only these explicit paths and reports the commit hash; otherwise stop for the human.
   - Verify: `git diff --check && git status --short && git add src/quarantine_analysis.py tests/test_quarantine_analysis.py src/percase_quarantine_triage.py reports/wi008_quarantine_percase_evidence.md docs/plans/2026-10-25-WI-008-quarantine-percase.md && git commit -m 'Fix WI-008 quarantine per-case analysis'`

## OUT OF SCOPE
Quarantine/dead-letter mutation, reinstatement, verifier changes, ELE download, unrelated cleanup, and changing test assertions.

## EXECUTION LOG
03:05 | 1 | Reproduced 2 failures (2 failed, 4 passed) | concern: triage script calls `simple_quarantine_analysis`, not the module under test
03:10 | 1 | Fixed `level_step_test` + `multi_day_path_analysis`; assertions untouched | 
03:12 | 1 | `uv run pytest tests/test_quarantine_analysis.py -v` → 6 passed | 
03:25 | 2 | Wired triage script to `src.quarantine_analysis`; regenerated report; 72 rows; 13 REINSTATE / 59 KEEP | concern: 22 flips vs baseline 17/55 → exceeds ≤5 STOP
03:28 | 2 | Decomposition: wiring-only 10 flips, logic-fix-only 12 flips | concern: both exceed the gate independently
03:40 | 3 | `uv run pytest -q` → 62 passed in 474.10s | 
03:45 | 4 | STOPPED before commit — human gate open | brief: `docs/human/interventions/2026-10-25-WI-008-step5.md`

03:50 | 4 | ADMIN DECISION: option **b** — commit the tests-green fix only; leave the report at baseline | 
03:52 | 4 | Wiring reverted in `src/percase_quarantine_triage.py`; unused `cb01_spike_readonly` removed | 
03:56 | 4 | Report restored byte-identical to baseline → 0 verdict flips | 
04:00 | 4 | Committed explicit paths only (source fix + tests + docs); report and duplicate classifier scripts left untracked | concern: 3-way classifier divergence deferred to WI-010

STATUS: DONE | evidence: `uv run pytest tests/test_quarantine_analysis.py -q` → 6 passed; `uv run pytest -q` → 62 passed; report byte-identical to baseline (0 flips); no quarantine/dead-letter/verifier mutation; assertions untouched | admin decision: option b | follow-up: WI-010 (classifier consolidation)
