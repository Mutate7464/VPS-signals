# BOARD.md — Kanban (single source for "what now / what next")

> Rules & policies: `WORKFLOW.md` §2. Agents read this board at task start and update rows they touch. Admin orders READY top-down; the top row is "do next". Expedite rows (⚡) jump the queue.

**Last updated:** 2026-10-25 PM cycle 9 (WI-009b at QA/GATE — Build verified 37/37 new tests; reviewer pass ses_e8ecc8dc verdict FIX BEFORE COMMIT: F1 early-stop raw-IC vs |IC| metric mismatch CONFIRMED live in `c4fc27c` (fix widens margin 3.1%→~16%, sign unchanged); F3/F5/F6 warns/nits. Admin gate decision pending)

## ACTIVE

| WI | Title | Goal | Column | Since | Blocker / owner | Evidence |
|---|---|---|---|---|---|---|
| WI-008 | Quarantine triage execution (72 dead-letter tickers: per-case verification + reinstate/keep decisions) | G-002 | **DONE** (gate: admin APPROVED completion 2026-10-25, PM cycle 8) — Build done + repair pass under admin option **b**; PM re-verified independently (6/6 unit tests, 62 full suite, report byte-identical baseline 17 REINSTATE / 55 KEEP_QUARANTINED); commit `459ee44`, PM cycle `cc631b9` | 2026-10-25 | Follow-ups (owner: admin / WI-010): per-row reinstate/keep execution remains human-gated — no auto-reinstatement; ELE re-download admin-owned (Mac/IBKR Gateway); 3-way classifier divergence + 2020-03-09 cluster / GME / ICL re-derivation → WI-010 (BACKLOG). Report and duplicate classifier scripts deliberately untracked until WI-010 consolidation. | `reports/wi008_quarantine_percase_evidence.md`; plan `docs/plans/2026-10-25-WI-008-quarantine-percase.md`; decision brief `docs/human/interventions/2026-10-25-WI-008-step5.md` |
| WI-009b | Make contrastive ranking beat the E5 factor baseline (WI-009 follow-up, admin APPROVED 2026-10-25) | G-001 | **DONE** (gate decision 2026-10-25: **HOLD + re-spec** — closed as a documented NEGATIVE result) — skill bar re-specified: clause (a) now requires **same sign as best factor AND |IC| ≥**; this run **fails** that bar (model anti-correlated: −0.1478 vs `vol_20` +0.1274). Not a model bug: the model learned the full-history vol tilt; the recent window inverted the regime. | 2026-10-25 | F1 fix landed + honest rerun (epoch 1→5 selected, IC −0.1478 t−6.03, clause-a |IC|-margin 16.0% — thin-margin caveat retired, sign inversion unchanged). Same-sign clause adopted for all future skill bars (folded into WI-009c scope). Inverse signal stays exploitable-as-a-candidate-feature, never as a shipped ranker (negation chosen on eval window = curve-fit). | Build `c4fc27c`; F1 fix + rerun `6541830`; PM cycle 9 `c2fc9c5`; report `reports/wi009b_e5_vs_model_CAD.md` + `reports/wi009b_train_CAD.json`; gate brief + addendum `docs/human/briefings/2026-10-25-gate-WI-009b-skill-bar.md`; plan `docs/plans/2026-10-25-WI-009b-beat-e5-baseline.md`; 104 tests passed |
| WI-009c | Classifier route to usable targets (up/down/stay band shortlist; admin direction 2026-10-25) | G-001 | **READY — research doc written, admin scope decision pending** (not yet EXECUTING) | 2026-10-25 | `y_20d_stay` (±5% band, exclusive of up/down) landed in `src/targets.py`; targets USD+CAD rebuilt (legacy labels row-for-row identical; stay base rates USD 43.1% / CAD 44.8%). xgb_trainer stays runnable (whitelist fallback + exit_urgency event-only fix). Open before Build: label-vs-feature question (Gate 4 USD FAIL prior vs WI-002 continuous-space signal), target design (independent binaries vs 3-class vs continuous regression), Gate-4 bar vs skill bar. | Research doc `docs/plans/2026-10-25-WI-009c-classifier-research.md`; `tests/test_targets_stay.py` (5 green); `scripts/rebuild_targets.py` |

## DONE

| WI | Title | Goal | Done | Evidence |
|---|---|---|---|---|
| WI-009 | Implement Technical Trading Approach (D-003 Option 2 — contrastive pairwise ranking on CAD) | G-001 | 2026-10-25 — gate decision: **APPROVED**, continue as WI-009b | Build commit 19795ac; PM cycle 6 verification (4acae0b): 11/11 leak+sampler tests, 56 full suite, top-10 CSV verified; gate brief `docs/human/briefings/2026-10-25-gate-WI-009-contrastive-ranking.md`; E5 split-leak found by reviewer #2, fixed and regression-locked (`tests/test_e5_split_no_leak.py`) |
| WI-002 | Diagnose & fix model signal (Gate 4 FAIL: all 4 USD targets ≈ random) | G-001 | 2026-10-24 — gate decision: **pivot to WI-009** (hybrid technical-factor, D-003); no separate target/metric redesign item | E3–E5 verdicts (H3 yes / H2 no / H4 no) in `reports/diag_D002_summary.md` + e2–e5 reports; PM cycle 4 verification (ee6f93e); `logs/e3_runs.out` |
| WI-003 | Ingest Phase 1 validation runs + CAD download | G-002 | 2026-10-22 | 546 USD + 350 CAD synced (~97-98% coverage); verifier PASS (824/896 ok, leakage PASS, 72 quarantined) — `reports/sprint1_ingestion_audit.md` |
| WI-001 | Build & run pipeline v1 end-to-end (Sprints 1–5) | G-001 | 2026-10-22 ⚠ QA exception | Gate 4 FAILED; PDFs = structural demo only (`reports/`, `screener_*_20261021.pdf`) |
| WI-000 | Adopt goal→design→plan→execute→QA workflow framework | G-003 | 2026-10-22 | `workflow/WORKFLOW.md`, `RISKS.md` |
| WI-007 | Two-stream docs + human guide + guide/scribe agents | G-001 | DONE | `docs/human/GUIDE.md`; agents verified loaded (`debug agents`) |
| WI-006 | Enforce blocking QA gates in agent workflow | G-003 | DONE | reviewer prompt gate check + WORKFLOW.md §1 rule 4 |

## BACKLOG

| WI | Title | Goal | Size | Gate |
|---|---|---|---|---|
| WI-010 | Consolidate the quarantine classifier — three divergent claim paths exist (2026-10-25 repair pass) | G-002 | M | human gate. Report generator `src/final_quarantine_triage.py` → 17/55; `src/percase_quarantine_triage.py` + `src/simple_quarantine_analysis.py` → 11/61; tested+repaired `src/quarantine_analysis.py` → 13/59. All three are untracked except the repaired module. Must: wire the report to the unit-tested module, delete the duplicates, add the read-only CB-01 CLEAN_NOW check (runs `verify_synced_data` without mutating `dead_letter_tickers.csv`), and re-derive the decision rule for the 2020-03-09 cluster / GME / ICL. See `docs/human/interventions/2026-10-25-WI-008-step5.md`. |
| WI-004 | Ingest Phase 2 pacing restore (aggressive targets) | G-002 | S | deferred to next week by admin (2026-10-22); gate 1/3 clean runs |
| WI-005 | Post-MVP: EP-06 index scraper · EP-07 Telegram digest · EP-08 regime-conditional tuning | G-001 | L — decompose | signal direction pivoted to WI-009 (2026-10-24) |

## Column policies
BACKLOG → unprioritized ideas, size-tagged · READY → meets Definition of Ready, admin-ordered · DESIGN/PLAN → Plan agent working (WIP 2) · EXECUTING → Build active (WIP 1) · QA/GATE → reviewer + human gate · DONE → DoD met · BLOCKED → named owner + reason; aging >7d flagged weekly.

**Risks:** `RISKS.md` (reviewed weekly). **Retros:** `retros/YYYY-WW.md`.
