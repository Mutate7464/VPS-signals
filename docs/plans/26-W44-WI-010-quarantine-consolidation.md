# WI-010 — Quarantine classifier consolidation

## GOAL
Produce one evidence-backed quarantine report from the tested classifier, including a read-only CB-01 CLEAN_NOW check and anchor-case rule review, while leaving all quarantine state unchanged for the human gate.

## CONSTRAINTS
- Work from `src/quarantine_analysis.py`; remove the three duplicate classifier scripts only after preserving the 17/55 baseline for comparison.
- `data/dead_letter_tickers.csv` and all quarantine state are strictly read-only. No auto-reinstatement or per-row state changes; deliver a report and recommendation table only.
- Use sequential symbol iteration and bounded column reads; do not build an all-ticker uncompressed DataFrame. `n_jobs<=2`; no model work, secrets, live trading, or order execution.
- Run the persistence-guard-only anchor experiment before changing the classifier decision rule, and include its outcome before the rule rationale. Evaluate the 2020-03-09 cluster (OVV/WES/CVE/APA/OXY/MTDR), GME, and ICL individually.
- Preserve the WI-008 report as the 17/55 baseline; write the consolidated deliverable to `reports/wi010_quarantine_consolidated.md`. Disclose total verdict flips and symbols, plus per-symbol verdict and evidence.
- Stop at the human gate. Do not alter quarantine state based on report recommendations.

## STEPS
1. Initialize the WI log stub if absent; preserve any existing log. It must contain `STATUS: PLAN` before execution entries are appended.
   - Acceptance: `docs/plans/logs/WI-010-quarantine-consolidation.md` exists with the plan status marker and no prior contents were overwritten.
   - Verify: `test -e docs/plans/logs/WI-010-quarantine-consolidation.md || { mkdir -p docs/plans/logs && printf 'STATUS: PLAN\n' > docs/plans/logs/WI-010-quarantine-consolidation.md; }; grep -qx 'STATUS: PLAN' docs/plans/logs/WI-010-quarantine-consolidation.md`
2. Add an isolated read-only CB-01 CLEAN_NOW function in `src/verify_synced_data.py` and tests in `tests/test_verify_synced_data.py`. It must inspect on-disk parquet using the existing CB-01 thresholds (>+100% or <-50%), read dead-letter rows without writing them, and avoid calling the state/quarantine mutation path. Test clean, spike, missing/read-error cases and CSV byte preservation.
   - Acceptance: the helper reports CLEAN_NOW candidates from on-disk data without changing `data/dead_letter_tickers.csv` or any quarantine state; tests prove no mutator is called.
   - Verify: `uv run pytest tests/test_verify_synced_data.py -q`
3. Add `src/quarantine_triage_report.py` with an experiment-only mode. Before any decision-rule edit, run `level_step_test` (including its persistence guard) for the named anchors without using volume corroboration as a vote, and record spike/date, ratio, persistence outcome, and status in the WI-010 report. Capture the existing 17/55 per-symbol baseline first; if its report is absent, run the legacy report generator now, before removing it.
   - Acceptance: the experiment section records every available anchor separately, clearly marks missing data, precedes any final-rule rationale, and has no volume vote; baseline is verified as 17 REINSTATE / 55 KEEP_QUARANTINED.
   - Verify: `if ! grep -Fq '| REINSTATE | 17 |' reports/wi008_quarantine_percase_evidence.md 2>/dev/null || ! grep -Fq '| KEEP_QUARANTINED | 55 |' reports/wi008_quarantine_percase_evidence.md 2>/dev/null; then uv run python src/final_quarantine_triage.py; fi && grep -Fq '| REINSTATE | 17 |' reports/wi008_quarantine_percase_evidence.md && grep -Fq '| KEEP_QUARANTINED | 55 |' reports/wi008_quarantine_percase_evidence.md && uv run python -m src.quarantine_triage_report --experiment-only --output reports/wi010_quarantine_consolidated.md`
4. Only after Step 3, re-derive and implement the final combination rule in `src/quarantine_analysis.py`, with focused tests. A volume-only signal must not produce SPLIT_LOOKALIKE; require the persistent non-unity level-step evidence and an isolated multi-day path together. Confirm the 2020-03-09 crash cluster and GME are not misread as split-lookalikes; assess ICL from its recorded evidence without presuming a verdict. Wire the report entry point exclusively to the tested module and the read-only CB-01 function; remove `src/final_quarantine_triage.py`, `src/percase_quarantine_triage.py`, and `src/simple_quarantine_analysis.py`. Generate the final report at the chosen WI-010 path.
   - Acceptance: one entry point remains; report contains a per-symbol recommendation/evidence table, baseline flip count and symbol list, CB-01 CLEAN_NOW results, and experiment plus final-rule verdicts for each anchor. No quarantine input/state is rewritten.
   - Verify: `uv run python -m src.quarantine_triage_report --output reports/wi010_quarantine_consolidated.md`
5. Run the targeted tests and inspect the final deliverable; then stop for human review with the complete recommendation table. Do not reinstate or otherwise update any ticker.
   - Acceptance: original six quarantine-analysis tests remain and pass, new tests pass, the report is present, and the session ends at the human gate (not with state changes).
   - Verify: `test -s reports/wi010_quarantine_consolidated.md && uv run pytest tests/test_quarantine_analysis.py tests/test_verify_synced_data.py -q`

## OUT OF SCOPE
ELE re-download (admin-owned/Mac), upstream pipeline changes, WI-012 renaming, further three-way divergence-history work, and execution of any per-row reinstate/keep recommendation.

## EXECUTION LOG

**STOP FOR HUMAN REVIEW** — present the final decision table; no quarantine action is authorized by this plan.
