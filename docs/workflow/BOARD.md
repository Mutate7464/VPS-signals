# BOARD.md — flat queue (single source for "what now / what next")

> Rules: `WORKFLOW.md` §2. Row format: `designs/D-020` §5. Kanban dirs: `docs/kanban/{ready,in_progress,blocked,done}/`.
> Full pre-flat board (2026-11-07, 16 KB): `archive/BOARD-2026-11-07-pre-flat.md`.

**Last updated:** 2026-11-10 — D-025 tiered sprint IN PROGRESS (T1→T2→T3 per D-025 §1). Admin approved series 2026-11-10. WI-046 executing (T1 docs, 0 core-h). **Next:** WI-045 edge-decay probe (T3 prep, 0.3 core-h).

## ACTIVE
### D-025 SPRINT (Tiered workflow — T1→T2→T3, admin approved 2026-11-10)
- [WIP] WI-046 | tier map in WORKFLOW+BOARD | T1 | doc-only (0 core-h)
- [TODO] WI-045 | edge-decay probe on WI-042 artifacts (`reports/l2/rerun_modern.json`) | T3 prep | 0.3 core-h
- [TODO] WI-047 | feature gap inventory + research shortlist | T1 | 0.2 core-h
- [TODO] WI-048 | target families `up`/`high_low`/`vol_expand` × h ladder, BH-FDR, probe-first dry-run | T2 | 2.0 core-h (PM full grid)
- [TODO] WI-049 | mechanism survey doc (depends WI-045) | T3 | 0.1 core-h

### CLOSED (D-024 batch, all RATIFIED)
- [DONE] WI-039 | regime audit of b_hold (robust vs concentrated) | G-001 | **PASS** 2026-11-09 — **ROBUST both markets**: top-regime excess-AUC share 0.36 USD / 0.45 CAD (<0.60 bar), every populated regime cell AUC >0.5 (224K/165K joined OOF rows, 658/381 symbols); b_hold signal NOT regime-gated; inference/join only, 0.03 core-h total (`reports/wi039_summary.md`); RATIFIED 2026-11-09 (admin in chat): b_hold robust both markets; Layer-1 library artifact stands un-gated
- [DONE] WI-037 | P(hold) veto filter on frozen fib entries (tradeable downstream test) | G-001 | **REJECT** both markets 2026-11-09 — **RATIFIED 2026-11-09 (admin in chat) — Layer-2 trading verdict** (overlay gate vs frozen rules; τ tuned on CALIB edge; does not retro-doubt the Layer-1 b_hold pickles, which stand as library artifacts) — τ grid inert (calibrated P(hold) max ~0.011, prevalence ~0.4%); pooled edge +0.0001 USD (2/5 folds) / +0.0001 CAD (1/5); veto precision 0.96 USD / 0.63 CAD vs prevalence 0.004/0.005; no pickle, no shortlist (`reports/wi037_summary.md`); b_hold signal NOT tradeable as entry veto under frozen rules
- [DONE] WI-036 | target-variant ablation: 8 entry/exit defs × 9 horizons × 3 binaries × 4 learners × 2 markets, pure-signal AUC/IC + BH-FDR | G-001 | PASS 2026-11-09 — **57 FDR survivors, ALL `b_hold` short-horizon (h∈{5,8,13,21})**, winner `exact_full_k0.8` min cross-market AUC 0.7207 (USD 0.7836/CAD 0.7207); **profit/stop (entry/exit) targets show NO surviving signal in any variant**; 1158 high-h cells truncated under cap; 6838 pickles `data/models/wi036/`; core 2.55h vs 2.5 cap (`reports/wi036_summary.md`)
- [DONE] WI-035 | three-binary models, confirmatory no-edge run | G-001 | PASS 2026-11-09 — USD REJECT (1/5, −1.24pp, z −0.89); CAD ADOPT flagged record-only fat-tail (39/17,332 events, z +4.10); no-edge theory CONFIRMED; 96 pickles `data/models/wi035/`; tests 16/16
- [DONE] WI-033 | swing-conditioned 3-class XGB under ADOPT_LOOSE_4OF5 | G-001 | FAIL 2026-11-09; REJECT both markets — USD 4/5 folds but pooled edge −0.15pp vs frozen rules (placebo z −19.7); CAD 2/5, edge −0.07pp; frozen fib rules stand; no pickle/shortlist written (`reports/wi033_summary.md`)
- [DONE] WI-032 | swing-event sampling + 3-class first-touch labels + probe (D-021) | G-001 | PASS 2026-11-09; **probe CLEAR both markets** — USD 460,314 events / CAD 252,420, 13/19 FDR-sig features all same-sign + placebo clear (`reports/wi032_probe.md`)
- [DONE] WI-038 long-horizon gap fill | G-001 | closed 2026-11-10: full-universe run EXIT:0 (552 cells scored, 408 truncated by 2.0 core-h cap, h=233/144 dropped); report `reports/wi038_summary.md` + pickles `data/models/wi038/`; winner `tol2_full_k0.8` (best cell mlp_torch|b_hold|h34, min cross-market AUC 0.6962), 20 BH-FDR survivors (all b_hold, h∈{34,55,89}, both markets), zero starved folds — expectation (b_hold again, weaker) confirmed. **Verdict PASS — RATIFIED 2026-11-10 (admin in chat, "accept changes"): long-h b_hold survivors (h∈{34,55,89}) join the L1 pickle library.**
- [DONE] WI-040 | b_hold library consolidation: manifest + calibration/Brier + permutation attribution + inference entrypoint (L1) | G-001 | **DONE 2026-11-10, PM-verified** — builder session killed after artifacts landed (EXIT 130); PM re-verified every DoD item: manifest 9,745 rows == 96+6,838+2,811, all paths resolve; winner-cell calibration usable (USD Brier skill +0.327, ECE 0.0009; CAD in report); top-20 permutation attribution both markets; `--infer` smoke exit 0; tests 7/7 (`reports/wi040_library_manifest.md`, `reports/wi040_calibration.md`, `data/models/wi040/manifest.parquet`). Layer-1 infrastructure WI — no gate verdict to ratify.
- [DONE] WI-041 | L2 overlay harness (D-024) | G-001 | **BATCH APPROVED by admin in chat 2026-11-10** ("approve": 041→044→042→043, WIP limit 1); builder finished EXIT:0, PM-verified 2026-11-10: `uv run pytest tests/test_l2_overlay_harness.py -q --maxfail=1` → 14 passed (2.54s); smoke `L2_SMOKE=1 python -m src.l2_overlay.harness --question wi037 --out /tmp/l2_smoke` → ADOPT tau=0.70 calib_edge 0.0314 eval_edge 0.0357 placebo_z +38.90 (synthetic fixtures, no EVAL burn); locks released; card in `done/`. Smoke verdict is synthetic-fixture only — PROVISIONAL, no adoption claim. **Next:** WI-044 dispatched.
- [DONE] WI-044 | L1 learner extension — 6 learners incl. LightGBM/CatBoost | G-001 | APPROVED (same batch); builder finished EXIT:0, PM-verified 2026-11-10: pytest tests/test_swing_bsh_learner_ext.py → 19 passed; smoke WI044_SMOKE=5 → 96 cells, 4 stdout lines; full-universe run executed by the builder (footer records it): 80 cells scored / 16 truncated by cap, 6 placebo-tested, **6 BH-FDR survivors (m=96)** — best cross-market cell random_forest/b_hold/h21 (AUC USD 0.7985 / CAD 0.7341, min IC +0.0413); calibrated-wrapper Brier reported; 400 fold pickles + data/models/wi044/manifest.parquet (WI-040 schema); reports/wi044_summary.md; 1.80/2.0 core-h; locks released; card in `done/`. Layer-1 only (D-023). **RATIFIED (admin in chat 2026-11-10, Layer 1)** — 6 survivors join the L1 library; predictive license only, no trading claim. **Next:** WI-042 dispatched.
- [DONE] WI-042 | Rerun modern four L2s (037/033/030/028) + regime axis + stack input | G-001 | APPROVED (same batch); builder finished EXIT:0 (12 tests), PM full-run 2026-11-10 EXIT:0 (29.2s, 91 cells / 30 tested, family wi042_modern_l2_rerun α=0.05): {ADOPT 20, INCONCLUSIVE 1, INERT 49, REJECT 21}; report `reports/l2/rerun_modern.{md,json}`. **RATIFIED (admin in chat 2026-11-10 "proceed with recs")**: closures stand (REJECT/INERT per pre-committed D-024 closure); the 20 computed ADOPTs ratified as statistically real (placebo z to +5.88) but economically nil (EVAL edges ~0.00000 vs 25 bps) — NO deployment. Known gaps: wi033 raw h21 USD INERT (missing manifest cell); chop_normal untestable (<200 CALIB events). Layer-2 verdict does not retro-doubt the Layer-1 artifacts consumed (D-023). **Next:** WI-043 (queued, depends WI-042).
- [DONE] WI-043 | Port + rerun legacy three L2s (012/018/011) | G-001 | APPROVED (same batch); builder finished EXIT:0 2026-11-10; PM-verified: pytest 13 passed; locks released (registry emptied 2026-11-10); card in `done/`, commit cbf9022 (source+tests) + 97b61bb (close-out). Full-universe run: builder EXIT:0 (16.8 s) + PM re-run EXIT:0 (17.2 s, reproduced numbers exactly) — 42 cells / 5 tested, family wi043_legacy_l2_rerun α=0.05: {REJECT 5 (all wi012 cross-market: USD-tuned tau 0.50 judged on CAD — CALIB edge −0.46 bps, EVAL ~0, placebo z −54), INERT 37 (wi018 h34 mass infeasible; wi011 cadence 2.0k–4.6k firings/yr outside the 100–400 envelope)}; report `reports/l2/rerun_legacy.{md,json}`. **RATIFIED (admin in chat 2026-11-10, Layer 2)**: wi012/018/011 closed permanently per D-024 pre-committed closure — no deployment; does not retro-doubt the Layer-1 artifacts consumed (D-023). **No next WI — D-024 batch complete.**
- [TODO] WI-034 binary-decompose probe | G-001 | in `ready/` but DEFERRED by admin 2026-11-09 (superseded by WI-035/036 outcome; keep for the record only)
- [BLOCKED] none (`docs/kanban/blocked/` empty)

## DONE (last 7 days)
- [DONE] WI-031 | synthetic validation of fold-stability gate | G-001 | PASS 2026-11-08; **ADOPT_LOOSE_4OF5 adopted 2026-11-08 (admin in chat, cycle 27)** — bar for gating learned artifacts loosens 5/5→4/5 (chaotic detect 18/20 vs 17/20, FP 0/20); strict gate validated; prior verdicts not retroactive
- [DONE] WI-030 | fib conditional exit policy | G-001 | FAIL 2026-11-08; learned chooser 5/5 CALIB folds but below frozen cell on CALIB (+0.61% vs +1.07%) and EVAL (+0.80% vs +2.14%); frozen t15_s10_d39_close stands
- [DONE] WI-028 | fib entry-window (stage 2a) | G-001 | INCONCLUSIVE; k=0 dominates; **at-bottom entry recommended** (PM-verified)
- [DONE] WI-027b | fib regime unsupervised GMM | G-001 | FAIL; soft probs supplementary; rule-based labels chosen
- [DONE] WI-027 | fib regime labels | G-001 | PASS; up_high/USD +22.75pp; chop_normal/ALL +3.89pp
- [DONE] WI-021–025 | fib overnight chain | G-001 | ALL_DONE 2026-11-06; **PM review pending**; WI-024 research verdict BLOCKED_PRECONDITION (policy-null); report `reports/fib_swings/OVERNIGHT_REPORT.md`
- [DONE] WI-020 | kanban lock protocol | G-003 | merged into WORKFLOW §2/§9; commit `a5c1ead`

## DONE (older, one line each; evidence in git and `docs/human/briefings/`)
- [DONE] WI-019 | MVP closeout | G-001 | gate ACCEPT 2026-11-02; suite 662 EXIT:0
- [DONE] WI-018 | condition-first first_touch_34 USD | G-001 | ACCEPT; documented negative (G2 wall); NO_TRADE
- [DONE] WI-017 | brute-force target/feature confirmation | G-001 | ACCEPT; confirmation delivered
- [DONE] WI-016 | triple-barrier + meta shortlist (CAD) | G-001 | ACCEPT 2026-10-31; 133 TRADE / 15 NO_TRADE; paper-track behind human gate
- [DONE] WI-015 | performance analytics panel | G-001 | ACCEPT 2026-10-29
- [DONE] WI-014 | E5 factor screener CSV + PDF | G-001 | ACCEPT 2026-10-28
- [DONE] WI-013 | pipeline hygiene, market routing | G-003 | ACCEPT 2026-10-26
- [DONE] WI-012 | cross-market validation | G-001 | NO_TRADE cross-market confirmed; `reports/wi012_iteration_notes.md`
- [DONE] WI-011 | condition-first meta-analysis | G-001 | closed negative; NO_TRADE default
- [DONE] WI-010 | quarantine classifier consolidation | G-002 | ACCEPT 2026-10-26; 47 reinstated
- [DONE] WI-009c | classifier route | G-001 | closed NEGATIVE 2026-10-25 (no usable model)
- [DONE] WI-009b | beat E5 baseline | G-001 | closed NEGATIVE 2026-10-25; same-sign clause adopted
- [DONE] WI-009 | contrastive ranking (D-003 opt 2) | G-001 | APPROVED, continued as WI-009b
- [DONE] WI-008 | quarantine triage (72 tickers) | G-002 | DONE 2026-10-25; 17 reinstate / 55 keep
- [DONE] WI-007 | two-stream docs + guide agents | G-001 | DONE
- [DONE] WI-006 | blocking QA gates | G-003 | DONE
- [DONE] WI-003 | ingest Phase 1 validation + CAD download | G-002 | DONE 2026-10-22
- [DONE] WI-002 | diagnose model signal | G-001 | DONE 2026-10-24; pivot to WI-009
- [DONE] WI-001 | pipeline v1 end-to-end | G-001 | DONE 2026-10-22 with QA exception; Gate 4 FAILED (structural demo only)
- [DONE] WI-000 | adopt goal→design→plan→execute→QA | G-003 | DONE 2026-10-22

## BACKLOG
- [BACKLOG] WI-005 | Post-MVP: EP-06 index scraper, EP-07 Telegram digest, EP-08 regime tuning | G-001 | L (decompose). Superseded by `docs/governance/PHASE2_HANDOVER_RUNBOOK.md`.

## Column policies
- `[TODO]` = in `ready/`, meets DoR, admin-ordered. `[WIP]` = in `in_progress/`, locks registered, WIP limit 1.
- `[BLOCKED]` = in `blocked/`, two-strike tripped, owner and 1-line reason on the row.
- `[DONE]` = QA verdict and gate recorded. Rows older than 7 days are one line (WORKFLOW §2).
- Risks: `RISKS.md`. Data facts: `DATA_CONTRACT.md`. Decisions: `designs/`. Gate and cycle record: `PM_LOG.md` (newest 2 cycles).
