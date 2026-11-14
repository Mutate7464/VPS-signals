# WI_AND_RUN_LEDGER.md — MVP cycle ledger (WI-000…WI-019)

> Compressed 2026-11-02 (WI-019 closeout) from BOARD.md, PM_LOG (cycles 0–23), git history (158 commits), and WI logs. Source docs remain canonical evidence; this ledger is the index, not a replacement.

## Executive run telemetry

| Metric | Value | Source |
|---|---|---|
| Work Items planned/completed | 19 WI opened; 18 closed DONE (WI-004 dropped, WI-019 in flight) | BOARD.md |
| Final suite | **662 passed, 0 failed** (EXIT:0) at WI-018 close; 47 test files | `logs/wi018_*`, WI-018 log |
| Coverage | Not instrumented (no pytest-cov dependency) — debt D-3 | pyproject.toml |
| Build status | Green; `uv sync` + `uv run pytest` on Python ≥3.11, 2 vCPU/8 GB host | pyproject.toml |
| Research verdicts | 6 WI closed as documented **negatives** (WI-002/009b/009c/011/016-USD/018); E5 factor screener (WI-014) = **MVP signal** | BOARD.md DONE rows |
| Cycle span | 2026-10-17 → 2026-11-01; 23 PM cycles; 158 commits | git log |

## Work Item reconciliation

| WI | Objective | Triage | Key modules / commits | Verification | Notes & variance |
|---|---|---|---|---|---|
| WI-000 | Adopt goal→design→plan→execute→QA workflow | Accepted MVP | `docs/workflow/WORKFLOW.md`, `RISKS.md` | review | Framework held for entire cycle |
| WI-001 | Pipeline v1 end-to-end (Sprints 1–5) | Accepted MVP (partial) | `src/{ibkr_ingest,feature_engine,stat_metadata,xgb_trainer,pdf_compiler}.py` | `reports/sprint1..4_*` | ⚠ Gate 4 FAIL; PDFs structural demo only (QA exception) |
| WI-002 | Diagnose model signal | Attempted & Rejected | `scripts/diag_signal.py`, `reports/diag_D002_*` | e2–e5 reports | All 4 USD targets ≈ random → admin pivot to WI-009 |
| WI-003 | Ingest Phase 1 + CAD download | Accepted MVP | `src/ibkr_ingest.py`, `verify_synced_data.py` | `reports/sprint1_ingestion_audit.md` | 546 USD + 350 CAD, ~97–98% coverage, 72 quarantined |
| WI-004 | IBKR pacing / ticker-download repairs | Dropped (admin 2026-11-01) | — | — | ELE re-download, HMMC/ICL, TRI/SPCX all dropped |
| WI-005 | Post-MVP EP-06/07/08 | Necessary Carryover | — | — | Backlog; signal direction superseded by WI-009 series |
| WI-006 | Blocking QA gates in workflow | Accepted MVP | reviewer prompt gate, WORKFLOW §1 | review | — |
| WI-007 | Two-stream docs + human guide | Accepted MVP | `docs/human/*`, `.agents/` | `opencode debug agents` | — |
| WI-008 | Quarantine triage (72 dead letters) | Accepted MVP | `src/quarantine_triage_report.py` | `reports/wi008_*` | Build + repair under admin option b |
| WI-009 | Contrastive pairwise ranking (CAD) | Accepted MVP | `src/models/contrastive_ranking.py`, `pair_sampler.py` | 11/11 leak tests, 56 suite | E5 split-leak found by reviewer, fixed + locked (`test_e5_split_no_leak.py`) |
| WI-009b | Beat E5 baseline | Attempted & Rejected | `src/models/skill_bar.py` | `reports/wi009b_*` | IC −0.1478 vs vol_20 +0.1274 (anti-correlated); skill bar re-specified same-sign+|IC| |
| WI-009c | Classifier route to usable targets | Attempted & Rejected | `scripts/train_wi009c.py`, `evaluate_wi009c.py`, `src/models/{continuous_targets,robustness_gates}.py` | 0/5 targets pass bar; 176 tests | Labels bottleneck; 89-feature spend gated; triple-confirmed factors-are-the-signal |
| WI-010/010b | Quarantine classifier consolidation + reinstate execution | Accepted MVP | `src/quarantine_analysis.py`, `data/adjudicated_tickers.csv` | 47 targeted + 232 suite | 36 flips accepted; 47 REINSTATE executed; CSV 72→25; skip-list prevents bounce-back |
| WI-011 | Condition-first meta-analysis | Attempted & Rejected | `src/wi011/*`, `scripts/wi011_*` | 15/15 + suite 191 | "None survive costs at this universe size" → NO_TRADE default |
| WI-012 | Cross-market validation (full process, CAD+USD) | Accepted MVP | fix `src/factors/e5_baseline.py:99` | `reports/wi012_*` | Factor signal generalizes (mom +0.0209 t+6.00); labels bottleneck cross-market confirmed |
| WI-013 | Pipeline hygiene, `--market` parametrization | Accepted MVP | `src/state_manager.py`, `rebuild_wi013_metadata` | 223→232 suite | F-2..F-5 land; report-path overwrite warts logged |
| WI-014 | E5 factor screener → daily shortlist CSV+PDF | **Accepted MVP — the MVP signal** | `scripts/wi014_screener.py`, `src/pdf_compiler_factor.py` | suite 396; both markets | CSV+PDF frozen artifacts clean |
| WI-015 | Perfanalytics panel + alignment matrix | Accepted MVP | `src/perfanalytics/*` | suite 444 | First positive alignment (bb_width/range_width@233, yangzhang@144, atr_pct@233) |
| WI-016 | Triple-barrier meta-labeled shortlist (CAD) | Accepted MVP | `src/wi016/*` | 550 suite, PM-verified | 133 TRADE/15 NO_TRADE @ 20+5 bps; OOF floor 0.5303; discrimination ceiling → WI-017 |
| WI-017 | Brute-force target/feature confirmation (USD) | Accepted MVP (confirmation) | `src/wi017/*` | 12 tests, recompute-verified | WI-015 positives real (amplitude); first_touch thin (|IC|≤0.06); hurst_9 all-NaN wart |
| WI-018 | Condition-first directional, first_touch_34 (USD) | Attempted & Rejected | `src/wi018/*` | 100 tests + suite 662 | G2 wall: 2,506/3,658 survivors, density 0.685 ⇒ G3 skipped ⇒ NO-GO; last research run pre-publish |
| WI-019 | MVP closeout (this ledger, governance docs, repo refactor) | In flight | `docs/{governance,architecture,execution}/` | see log | Steps 1–3; code splits deferred to debt register |

## Triage definitions

- **Accepted MVP** — verified against acceptance criteria, tested, merged to main (all on `main`; gate decisions in `docs/human/briefings/`).
- **Necessary Carryover** — deferred capability with documented entry point (see backlog in `PHASE2_HANDOVER_RUNBOOK.md`).
- **Attempted & Rejected** — failed/rejected approach; root causes extracted into `docs/architecture/DECISIONS_AND_NEGATIVE_KNOWLEDGE.md`.

## Kanban card archive (2026-11-14 compaction — cards moved from `docs/kanban/done/` to `docs/archive/wi/`; full narratives in the pre-lean board `docs/workflow/archive/BOARD-2026-11-14-pre-lean.md` and in each card)

| Card | Verdict (one line) |
|---|---|
| WI-021-fib-pass4-accounting-fix | fib overnight chain stage, DONE |
| WI-022-fib-regime-overlay | fib overnight chain stage, DONE |
| WI-023-fib-trade-labels-exit-grid | fib overnight chain stage, DONE |
| WI-024-fib-meta-label | BLOCKED_PRECONDITION (policy-null) |
| WI-025-fib-quantile-magnitude | fib overnight chain stage, DONE; chain report `reports/fib_swings/OVERNIGHT_REPORT.md` |
| WI-027-fib-regime-labels | PASS — up_high/USD +22.75pp; chop_normal/ALL +3.89pp |
| WI-027b-fib-regime-unsupervised | FAIL — rule-based labels chosen |
| WI-028-fib-entry-window | INCONCLUSIVE; at-bottom entry recommended |
| WI-030-fib-exit-policy | FAIL — frozen t15_s10_d39_close stands |
| WI-031-synthetic-validation | PASS — ADOPT_LOOSE_4OF5 adopted (cycle 27) |
| WI-032-swing-bsh-probe | PASS — probe CLEAR both markets (`reports/wi032_probe.md`) |
| WI-033-swing-bsh-model | REJECT both markets; frozen fib rules stand |
| WI-035-three-binary-xgb-gate | PASS — no-edge theory confirmed |
| WI-036-extended-run-loosened | PASS — 57 FDR survivors, all b_hold short-h (`reports/wi036_summary.md`) |
| WI-036-ESCALATION | archived with WI-036 |
| WI-037-hold-filter-tradeable-gate | REJECT both markets, RATIFIED Layer-2 (`reports/wi037_summary.md`) |
| WI-037-ESCALATION | archived with WI-037 |
| WI-038-long-horizon-gap-fill | PASS RATIFIED — long-h b_hold survivors h∈{34,55,89} join L1 (`reports/wi038_summary.md`) |
| WI-039-regime-audit-hold | PASS — b_hold robust both markets (`reports/wi039_summary.md`) |
| WI-040-bhold-library-consolidation | DONE — manifest 9,745 rows (`reports/wi040_library_manifest.md`) |
| WI-041-l2-harness | DONE — batch approved; synthetic smoke only, PROVISIONAL |
| WI-042-rerun-modern-l2s | RATIFIED — {ADOPT 20 econ-nil, INERT 49, REJECT 21}; no deployment (`reports/l2/rerun_modern.md`) |
| WI-043-rerun-legacy-l2s | RATIFIED — wi012/018/011 closed permanently (`reports/l2/rerun_legacy.md`) |
| WI-044-learner-extension | RATIFIED — 6 survivors join L1 (`reports/wi044_summary.md`) |
| WI-045-edge-decay-probe | DONE — T3 prep |
| WI-046-tiered-workflow-docs | DONE — doc-only |
| WI-047-feature-gap-research | DONE — shortlist delivered |
| WI-048a-target-labels | DONE — label builders + tests + smoke |
| WI-048b-label-density-probe | DONE — denser market USD; geometry pinned |
| WI-048c-grid-directional | RATIFIED — 11 `up` survivors join L1 (`reports/t2_grid_up_summary.md`) |
| WI-048d-grid-highlow | RATIFIED — 24/24 survivors join L1 (`reports/t2_grid_highlow_summary.md`) |
| WI-048e-grid-volexpand | RATIFIED — 24/24 join L1; label QUARANTINED per D-026 ruling 2 (`reports/t2_grid_volexpand_summary.md`) |
| WI-048f-fdr-summary | RATIFIED — cross-family ranking recorded (`reports/t2_targets_ext_summary.md`) |
| WI-050 | DONE PM-verified — precision@k harness |
| WI-051 | DONE PM-verified — forward `vol_expand_fwd` label |
| WI-052 | DONE PM-verified — L0-1 swing-structure block |
| WI-053 | DONE PM-verified — L0-2 realized asymmetry; R12: absorbed |
| WI-054 | DONE PM-verified — L0-3 regime age/run-length; R12: 0/12 |
| WI-055 | DONE PM-verified — L0-4 jump intensity; R12: absorbed |
| WI-056 | DONE PM-verified — L0-5 vol-dispersion; **L0-5 survives (`disp_entropy_39`)** — card kept in `done/` |
| WI-057 | DONE PM-verified — L0-6 effort-vs-result; R12: 0/12 — card kept in `done/` |