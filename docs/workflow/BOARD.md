# BOARD.md — flat queue (single source for "what now / what next")

> Rules: `WORKFLOW.md` §2. **Rows are pointer-only:** one line per row — title, gate, verdict tag, evidence path. Verdict narratives, test counts and ratification quotes live in the WI card and the cited report; `PM_LOG.md` is the canonical decision record.
> Kanban dirs: `docs/kanban/{ready,in_progress,blocked,done}/` (cards hold detail); archived cards: `docs/archive/wi/` (indexed in `docs/execution/WI_AND_RUN_LEDGER.md`).
> Full pre-lean board (2026-11-14, all per-WI narratives preserved): `docs/workflow/archive/BOARD-2026-11-14-pre-lean.md`; older: `docs/workflow/archive/BOARD-2026-11-07-pre-flat.md`.

**Last updated:** 2026-11-14 — D-026 Phase 1 DONE + RATIFIED (admin in chat, Layer 1): L0 R12 grid (L0-5 survives; `disp_entropy_39` joins the L1 candidate set), WI-058 bin 24/24 survivors (library best, min AUC 0.8226), WI-059a 24/24 (weak), WI-048d/e/f ratified with the `vol_expand` quarantine upheld. Admin direction recorded, NOT dispatched: larger variant at a lower rho-prune threshold for L1/L2 parameter-max (new pre-registered family). Locks registry EMPTY; nothing in `in_progress/`. Next dispatch: WI-060 after the ≥30-min idle window (WI-059b gated on a regression read-out WI).

## ACTIVE
### D-026 SPRINT (L0/L1 extension — T1/T2; plan `docs/plans/26-W46-L0L1-extension-review-v2.md`, design `docs/workflow/designs/D-026-l0l1-extension.md`; order Phase 0 → L0 → L1 → L1.5)
- Integrity ruling (PM-verified 2026-11-13): `vol_expand` label is BACKWARD-looking (`src/swing_bsh/targets_ext.py:111-133`) — survivors quarantined; forward use only via `vol_expand_fwd` (WI-051). `close`/`atr` levels confirmed excluded from feature lists (PASS).
- [DONE] WI-059b | L1-2/1-1 continuous families on the regression read-out — PM-run full-universe | T2 | **PM-verified 2026-11-14** — `cell_cv(regression=True)` path (float32 labels, `model.predict` OOF, `fit_regressor`, no calibration; WI-044 wrapper forwards + guards); xsec_vol_rank_cont: 24 cells, 0 truncated, 24/24 BH survivors, best min cross-market rank-IC **+0.6475** (xgboost/h55; CAD +0.7135) — supersedes the quarantined binarized numbers; mfe_mae_cont: 24 cells, 24/24 survivors, best min IC **+0.1665** (xgboost/h55) — moderate payoff-ratio signal; reports `reports/l1_ext_cont/` (quarantined sidecar retained as `*_quarantined.json`), 240 pickles; manifest superset **1015 rows** via consolidate; cont p from the date-block t-stat (per-date ICs, plan §7; p underflows to 0 at ~4k dates), placebo skipped for cont by design; verdict PROVISIONAL until admin ratifies
- [DONE] WI-060 | L1-3 `move_occur` + `move_dir_up` grids — PM-run full-universe | T2 | **PM-verified 2026-11-14** — chain EXIT:0; move_occur: 24 cells, 0 truncated, 24/24 BH-FDR survivors (placebo 24), best min cross-market AUC **0.6033** (xgboost/h5; min IC +0.1782), 0.54 core-h; move_dir_up: 24 cells, 0 truncated, 24/24 survivors (placebo 24), best min cross-market AUC **0.6407** (xgboost/h5; min IC +0.2230), 0.50 core-h — conditional direction B is better than chance (vs `up`'s 0.5038 unconditional), consistent with the plan's decomposition hypothesis; reports `reports/t2_grid_move{occur,dirup}_summary.md`, 240 pickles; verdict PROVISIONAL until admin ratifies; note: the A·B fixed-product screener score is a Phase-3/L2 read-out, not part of this verdict
- [TODO] WI-061 | L1-4 average-uniqueness weighting variant grid (b_hold + vol_expand reference cells) | T2 | method variant, own driver pass; awaiting dispatch
- [DONE] WI-050 | Phase 0 precision@k / top-decile diagnostic harness | N/A | card `docs/archive/wi/`
- [DONE] WI-051 | forward `vol_expand_fwd` label + `vol_expand` quarantine note | N/A | card `docs/archive/wi/`
- [DONE] WI-052 | L0-1 swing-structure history block | T1 | card `docs/archive/wi/`
- [DONE] WI-053…057 | L0-2…L0-6 blocks — R12 verdict: L0-5 survives (`disp_entropy_39`), L0-2/L0-4 absorbed (Q1), L0-1/L0-3/L0-6 0/12; 21 of 27 block cols flagged not-kept | T1 | `reports/l0_r12_v2/l0_r12_consolidated.md`; cards `docs/archive/wi/`
- [DONE] WI-058 | L1-1 xsec vol-rank grids — bin 24/24 survivors RATIFIED L1 (library best, min AUC 0.8226; manifest superset 535 rows); cont QUARANTINED (int8-cast top-of-date indicator retained under predictive license, admin "not unuseful for later use"; proper re-run = WI-059b) | T2 | `reports/t2_grid_xsecvolrankbin_summary.md`, `reports/t2_grid_xsecvolrankcont_summary.md`, `reports/l1_ext/`; card `done/`
- [DONE] WI-059a | L1-2 `mfe_mae_bin` grid — 24/24 survivors RATIFIED L1 (weak lift, min AUC 0.5515) | T2 | `reports/t2_grid_mfemaebin_summary.md`; card `done/`
- [DONE] WI-062 | L1.5 meta-label (swing-side primary) + permuted-label leakage test — not-stacking per D-026 | T2 | card `done/`

### D-025 SPRINT (tiered workflow T1→T2→T3, admin approved 2026-11-10) — complete except WI-049
- [TODO] WI-049 | mechanism survey doc (depends WI-045) | T3 | 0.1 core-h
- [DONE] WI-045…048f | tier map · edge-decay probe · feature-gap inventory · label builders + density probe · grids `up`/`high_low`/`vol_expand` + cross-family FDR consolidation — all PM-verified; survivors RATIFIED into the L1 library (`vol_expand` quarantined per D-026 ruling 2; re-integration carried by `vol_expand_fwd` + the admin's larger-scale lower-threshold variant) | T2 | `reports/t2_grid_up_summary.md`, `reports/t2_grid_highlow_summary.md`, `reports/t2_grid_volexpand_summary.md`, `reports/t2_targets_ext_summary.md`; cards `docs/archive/wi/`

### CLOSED
- D-024 batch (WI-032…044) — all DONE + RATIFIED 2026-11-09/10: L2 reruns closed per D-024 pre-committed closure (REJECT/INERT permanent; 20 ADOPTs statistically real, economically nil — NO deployment); L1 library consolidated (WI-040 manifest 9,745 rows) | `reports/l2/rerun_modern.md`, `reports/l2/rerun_legacy.md`, `reports/wi040_library_manifest.md`; cards `docs/archive/wi/`
- D-023 and earlier (WI-001…031) — closed; cards `docs/archive/wi/`, briefs `docs/human/briefings/`, per-WI one-liners in this file's git history
- [DONE] WI-034 | binary-decompose probe | DEFERRED by admin 2026-11-09 (superseded by WI-035/036 outcome; kept for the record only) — card in `ready/`
- [BLOCKED] none (`docs/kanban/blocked/` empty)

## BACKLOG
- [BACKLOG] WI-005 | Post-MVP: EP-06 index scraper, EP-07 Telegram digest, EP-08 regime tuning | superseded by `docs/governance/PHASE2_HANDOVER_RUNBOOK.md`

## Column policies
- `[TODO]` = in `ready/`, meets DoR, admin-ordered. `[WIP]` = in `in_progress/`, locks registered, WIP limit 1.
- `[BLOCKED]` = in `blocked/`, two-strike tripped, owner and 1-line reason on the row.
- `[DONE]` = QA verdict and gate recorded. Rows are pointer-only (WORKFLOW §2): narrative lives in the card + cited report; PM_LOG is canonical.
- Risks: `RISKS.md`. Data facts: `DATA_CONTRACT.md`. Decisions: `designs/`. Gate and cycle record: `PM_LOG.md` (newest 2 cycles).
