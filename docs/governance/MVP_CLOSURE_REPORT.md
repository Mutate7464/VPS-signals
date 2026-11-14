# MVP_CLOSURE_REPORT.md — MVP closeout (WI-019, 2026-11-02)

> PMP/Agile closure for the dual-market quantitative screener MVP. Evidence: `docs/execution/WI_AND_RUN_LEDGER.md`, `docs/workflow/BOARD.md`, `docs/workflow/PM_LOG.md`, `docs/human/briefings/` (gate decisions).

## 1. Scope baseline & sign-off matrix (G-001 dual-market screener · G-002 ingest reliability · G-003 process integrity)

| Requirement (baseline) | Delivered | DoD verification | Sign-off |
|---|---|---|---|
| Ingest ~300 USD + ~300 CAD OHLCV via IBKR | 546 USD + 350 CAD parquet, ~97–98% coverage | `reports/sprint1_ingestion_audit.md`; verifier 824/896 ok | WI-003 gate 2026-10-22 |
| Feature engine, leak-free | Fib 3→233 window panel, float32, point-in-time | `tests/test_leakage.py`, `test_e5_split_no_leak.py` | WI-009 gate 2026-10-25 |
| Quarantine + dead-letter handling | Per-case triage, 47 reinstated, skip-list lock | `test_adjudicated_reinstate.py`; CSV 72→25 | WI-010/010b gate 2026-10-26 |
| Dual-market parametrization | `--market` both markets, suffixed reports | `test_wi013_*` | WI-013 gate 2026-10-26 |
| Daily shortlist CSV + PDF tearsheet | WI-014 screener, both markets, frozen artifacts | 396 suite; PDFs in `reports/` | WI-014 gate 2026-10-28 |
| Alignment analytics | 264-col panel + target×feature alignment matrix | 444 suite | WI-015 gate 2026-10-29 |
| Meta-labeled shortlist (CAD) | 133 TRADE/15 NO_TRADE @ 20+5 bps, rule v2 | 550 suite, PM-verified | WI-016 gate 2026-10-31 |
| Confirmation study (USD) | Brute-force grid, recompute-verified | 12 tests + recompute | WI-017 gate 2026-11-01 |
| Directional condition probe | first_touch_34: G2 wall ⇒ NO-GO, G3 skipped | 100 tests + suite 662 | WI-018 gate 2026-11-01 |

**Product verdict:** E5 factor screener (WI-014) = the MVP signal; meta-labeled shortlist (WI-016) ships as research context; NO_TRADE default stands. No automated order execution (MVP boundary, human gate on everything).

## 2. Schedule, velocity & effort variance

| Item | Plan | Actual | Variance driver |
|---|---|---|---|
| Cycle span | open-ended | 2026-10-17 → 2026-11-01, 23 PM cycles, 158 commits | — |
| WIs closed | — | 18 DONE (6 as documented negatives) | Negative results were the schedule's main cost — each consumed a full probe→gate cycle before being retired |
| Bottleneck #1 | — | labels/targets (WI-002→009c→011→018 chain) | Binary labels blind to continuous signal; 3 separate WIs re-probed it |
| Bottleneck #2 | — | reviewer/Build rework (E5 split leak, WI-016 abstention rule v2) | One HOLD+fix re-gate per incident |
| Scope creep contained | — | 5 backlog items never opened (WI-004, EP-06/07/08); admin dropped IBKR concerns 2026-11-01 | Gate discipline held |

## 3. Technical debt & risk register (ranked)

| # | Debt / risk | Sev | Affected files | Remediation trigger |
|---|---|---|---|---|
| D-1 | **Oversized modules — 34 source files >250 lines** (top: `scripts/train_wi009c.py` 1200, `src/feature_engine.py` 955, `src/wi018/probe.py` 938, `src/wi016/addendum.py` 782, `src/wi018/cost_overlay.py` 759, `src/xgb_trainer.py` 727, `src/wi016/actions.py` 706). Decomposition blueprint: scripts → cli/train/eval/report modules per WI package; `feature_engine.py` → per-family feature modules; `xgb_trainer.py` → split/purged-train/eval. | **High** | see `wc -l` audit 2026-11-02 | **First Phase 2 task** — split under dedicated WI plan w/ targeted tests per module; MVP code-frozen post-ACCEPT, so no split now |
| D-2 | Hardcoded market constants (`MARKET="CAD"` module constants; hardcoded parquet paths in scripts) | Med | `src/wi016/__init__.py`, `src/wi018/*`, `scripts/wi011_*` | Any 2nd-market rerun of a research package |
| D-3 | No coverage instrumentation (pytest-cov absent) | Med | `pyproject.toml` | Before first Phase 2 code WI |
| D-4 | Frozen-report overwrite: stage scripts hardcode report paths | Med | `scripts/rebuild_wi013_metadata.py`, wi011/wi017 scripts | Any pipeline rerun (use validation prefix + `git checkout --`) |
| D-5 | `tc_rating` static snapshot — no point-in-time history | Med | `src/wi016/addendum.py` | Any live/backtest use of tc_rating |
| D-6 | Costs/slippage are assumptions, not realized fills | Med | cost overlays (WI-011, WI-016, WI-018) | Before any tradable claim; validate vs paper-track round-trip |
| D-7 | `state/PIPELINE_STATE.json` gates 2–5 legacy fields | Low | `src/state_manager.py` | Touch state schema |
| D-8 | `hurst_9` all-NaN wart shipped in WI-016 grid | Low | `src/wi016/` feature grid | Next grid rebuild (needs w≥12) |
| D-9 | Verifier blind-appends kept rows (no dedupe) | Low | `scripts/rebuild_wi013_metadata.py` audit path | Next verifier run |
| D-10 | Meta-labeler discrimination ceiling (OOF precision 0.568 vs 0.545) | High (product) | `src/wi016/meta_labeler.py` | WI-005-class new-data iteration, not rule tuning |
| R-01 | Look-ahead leakage | H→contained | leak tests + purged splits | standing (RISKS.md) |
| R-02 | Overfitting to single regime/window | H→contained | same-sign clause, fold stability | D-019 bars govern |

## 4. Process retro (spirit: token discipline, communication, expectations)

- **Worked:** goal→design→plan→execute→QA with human gate per WI; fail-closed red flags; PM-verify-everything; negative results recorded as durable directives (now in `docs/architecture/DECISIONS_AND_NEGATIVE_KNOWLEDGE.md`); lean detached-run polling (~bytes, not transcripts).
- **Needs improvement:** labels bottleneck cost 3+ WIs — a probe-first target spec (D-019 style) should precede any model spend; plan files self-contradicted once (WI-018 DEVIATION 1) — contract check now includes fail-closed semantics; docs sprawled across 4 locations pre-closeout — now routed (AGENT.md + INDEX.md).
- **Expectations going forward:** Phase 2 starts from `PHASE2_HANDOVER_RUNBOOK.md`; D-019 recalibration governs any post-MVP research; no research run before Phase 2 backlog grooming.