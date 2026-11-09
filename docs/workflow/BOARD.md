# BOARD.md — flat queue (single source for "what now / what next")

> Rules: `WORKFLOW.md` §2. Row format: `designs/D-020` §5. Kanban dirs: `docs/kanban/{ready,in_progress,blocked,done}/`.
> Full pre-flat board (2026-11-07, 16 KB): `archive/BOARD-2026-11-07-pre-flat.md`.

**Last updated:** 2026-11-09 — D-022 thread: WI-035 + WI-036 both DONE and committed (`feb155a`, `93cdc48`). **Next:** admin decision — WI-036 result is decision-grade (see ACTIVE rows).

## ACTIVE
- [DONE] WI-037 | P(hold) veto filter on frozen fib entries (tradeable downstream test) | G-001 | REJECT both markets 2026-11-09 — τ grid inert (calibrated P(hold) max ~0.011, prevalence ~0.4%); pooled edge +0.0001 USD (2/5 folds) / +0.0001 CAD (1/5); veto precision 0.96 USD / 0.63 CAD vs prevalence 0.004/0.005; no pickle, no shortlist (`reports/wi037_summary.md`); b_hold signal NOT tradeable as entry veto under frozen rules
- [DONE] WI-036 | target-variant ablation: 8 entry/exit defs × 9 horizons × 3 binaries × 4 learners × 2 markets, pure-signal AUC/IC + BH-FDR | G-001 | PASS 2026-11-09 — **57 FDR survivors, ALL `b_hold` short-horizon (h∈{5,8,13,21})**, winner `exact_full_k0.8` min cross-market AUC 0.7207 (USD 0.7836/CAD 0.7207); **profit/stop (entry/exit) targets show NO surviving signal in any variant**; 1158 high-h cells truncated under cap; 6838 pickles `data/models/wi036/`; core 2.55h vs 2.5 cap (`reports/wi036_summary.md`)
- [DONE] WI-035 | three-binary models, confirmatory no-edge run | G-001 | PASS 2026-11-09 — USD REJECT (1/5, −1.24pp, z −0.89); CAD ADOPT flagged record-only fat-tail (39/17,332 events, z +4.10); no-edge theory CONFIRMED; 96 pickles `data/models/wi035/`; tests 16/16
- [DONE] WI-033 | swing-conditioned 3-class XGB under ADOPT_LOOSE_4OF5 | G-001 | FAIL 2026-11-09; REJECT both markets — USD 4/5 folds but pooled edge −0.15pp vs frozen rules (placebo z −19.7); CAD 2/5, edge −0.07pp; frozen fib rules stand; no pickle/shortlist written (`reports/wi033_summary.md`)
- [DONE] WI-032 | swing-event sampling + 3-class first-touch labels + probe (D-021) | G-001 | PASS 2026-11-09; **probe CLEAR both markets** — USD 460,314 events / CAD 252,420, 13/19 FDR-sig features all same-sign + placebo clear (`reports/wi032_probe.md`)
- [TODO] WI-037 hold-filter tradeable gate | G-001 | staged `docs/kanban/draft/WI-037-hold-filter-tradeable-gate.md`; run order 1 of phase-2 batch; admin-approved in chat 2026-11-09 (cap 0.5 core-h)
- [TODO] WI-039 regime audit of b_hold | G-001 | staged `docs/kanban/draft/WI-039-regime-audit-hold.md`; run order 2 (cap 0.3)
- [TODO] WI-038 long-horizon gap fill | G-001 | staged `docs/kanban/draft/WI-038-long-horizon-gap-fill.md`; run order 3 after ≥30 min idle (cap 2.0)
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
