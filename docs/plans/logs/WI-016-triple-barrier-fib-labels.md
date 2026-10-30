# WI-016 execution log — triple-barrier fib-ladder labels + E5 meta-labeling

> One row per step, ≤50 words; details → step report artifact cited by path. Plan: `docs/plans/26-W44-WI-016-triple-barrier-fib-labels.md` (frozen after planner pass 2026-10-29).

| Step | Done (UTC) | Result | Evidence |
|---|---|---|---|
| — | 2026-10-29 | PLAN approved by PM contract check; awaiting admin plan review before Build dispatch | plan `docs/plans/26-W44-WI-016-triple-barrier-fib-labels.md` |
| 1 | 2026-10-29 23:12 | Horizon embargo added: `horizon_embargo`/`target_horizon`/`resolve_embargo`; per-target embargo wired to CV splitter + final `purged_holdout`. CLI default cannot weaken. Tests 14 pass. | `uv run pytest tests/test_xgb_trainer.py -k 'embargo or purged_holdout'` → 14 passed; regression set (leakage/e5_split/trainer_logging/wi009c) 29 passed |
| 2 | 2026-10-29 23:17 | `src/wi016/triple_barrier.py` + package: first-touch ±k·ATR (k=1.5/2.0) over h∈{8,21,55,144,233}, 3-class labels, NaN masks, streaming diagnostics. 17 tests pass. USD/CAD density reports written. | `uv run pytest tests/test_triple_barrier.py` → 17 passed; `reports/wi016_label_density_{USD,CAD}.{md,csv}` (USD 594 sym, CAD 365 sym) |
| 3 | 2026-10-29 23:26 | WI-016 unified grid added to `feature_engine.py` (`compute_features_wi016`, 111 cols: smooth ladder {3..233}, dense fib only for kama/hurst/entropy/vwap) + `wi016` config + new `src/wi016/admission.py` (VIF 8.0, relaxed MI, ρ>0.7 cluster reps, ≥500 events). 10 tests pass. | `uv run pytest tests/test_wi016_features.py` → 10 passed; regression: range_fib/feature_vectorized/stat_metadata_vif 20 passed |
| 4 | 2026-10-30 00:09 | `src/wi016/probe.py::legacy_comparison` compares legacy 5 labels vs triple-barrier on identical rows/features; writes `wi016_` report. Legacy generation not invoked after. | `uv run pytest tests/test_wi016_probe.py -k legacy_comparison` → 1 passed; `reports/wi016_legacy_comparison_{USD,CAD}.md` written |
| 5 | 2026-10-30 01:50 | Probe-first gate: within-date rank-IC, BH-FDR, 5-seed placebo, WI-009b same-sign, cost overlay (NO_TRADE default), fold counts. Full-market runs. **CAD = CLEAR; USD = NOT_CLEAR** (USD edge < cost). 9 tests pass. STOP for PM/admin. | `uv run pytest tests/test_wi016_probe.py` → 9 passed; `reports/wi016_probe_{CAD,USD}.md`; brief `docs/human/briefings/2026-10-30-gate-WI-016-probe.md` |

## DEVIATIONS

- Plan step 3 said "update `src/feature_engine.py`": done by **adding** the WI-016 unified grid (`compute_features_wi016`, `wi016_feature_names`) while leaving the legacy `compute_features` grid and its windows untouched — required to keep the shipped screener and frozen WI-014 artifacts working (OUT OF SCOPE: replacing the shipped screener before gate approval).
- Plan step 3 "rebuild the admission stage": implemented in the new `src/wi016/admission.py` (reusing `stat_metadata` ADF/MI and a now-parameterised VIF) rather than mutating `stat_metadata`, so frozen catalogs are unaffected. The real-data admission catalog itself is produced on demand by `admission.run_market` and is consumed by the step-5 probe panel; it was not materialised as a standalone step-3 artifact.
- Probe cost overlay is a documented proxy (|IC|·1000 bps − cost); the real overlay is WI-011's. The 5-seed placebo runs on the top-100 FDR survivors (host-time bound), noted in the report.
- Planned dependency `src.factors.e5_baseline:factor_frame` used as the sole E5 definition (no drift).

STATUS: DONE | evidence: steps 1–5 verified — `uv run pytest tests/test_xgb_trainer.py -k 'embargo or purged_holdout'` (14), `tests/test_triple_barrier.py` (17), `tests/test_wi016_features.py` (10), `tests/test_wi016_probe.py -k legacy_comparison` (1), `tests/test_wi016_probe.py` (9) all passed; full-market probe reports written: `reports/wi016_probe_CAD.md` (CLEAR), `reports/wi016_probe_USD.md` (NOT_CLEAR), `reports/wi016_legacy_comparison_{USD,CAD}.md`, `reports/wi016_label_density_{USD,CAD}.md`; gate brief `docs/human/briefings/2026-10-30-gate-WI-016-probe.md`. Step 6 NOT started (not dispatched); awaiting PM/admin gate decision.

## PM FINDING (2026-10-30, PM-set — decision-relevant, disclosed before gate)

Label-conflation discovered while confirming trade mechanics (PM-verified on 60 CAD symbols vs `compute_triple_barrier`): the Q3 "sign-of-return" spec means the ±1 labels **mix two different trades** — (a) true barrier first-touch (±k·ATR hit inside h bars; median 4 bars at h8) and (b) vertical-barrier drift sign (no barrier touched — ~45% of h8 events — exit at t+8 close with small drift). Class 0 is only ≈zero-return rows (~1%), so the density tables' ±1 columns are NOT profit/stop counts. Consequence: the probe IC partially measures short-horizon drift, not barrier capture; the |IC|·1000bps−cost proxy overstates the tradeable edge. Not a code bug — the label is exactly what D-016 Q3 specified — but gate interpretation must account for it. Recommended addendum before any step-6 monetization: re-run CAD probe with touch-restricted (barrier-resolved) labels or realized-return regression target, plus overlap-aware weights (h=8 daily events ⇒ 8× overlap).

## ADDENDUM (honest-edge probe, both markets — admin order 2026-10-30; reports + log only, no step 6)

| # | Done (UTC) | Result (≤50 words) | Concern (inline) |
|---|---|---|---|
| 1 | 2026-10-30 05:45 | Touch-restricted (barrier-resolved) + realized-return re-test, k∈{1.5,2.0} × h∈{8,21,55,144,233}, both markets. Barrier verdict: USD NOT_CLEAR all bands (0 flips vs step 5); CAD CLEAR with 2 flips (k15/k20 h21 → NOT_CLEAR). Reports `wi016_addendum_probe_{USD,CAD}.md`. | Realized-return targets CLEAR both markets — long-horizon regression diagnostic, not barrier capture; not gate evidence. |
| 2 | 2026-10-30 05:45 | Per-symbol average-uniqueness weights (AFML ch.4) on per-date IC t-stats. Overlap inflation visible: CAD h8 t −14.57→−5.13, h233 −11.64→−0.74; USD h8 −4.68→−1.63. Effective n ≈ n/h (h8 ≈ 339). | Uniqueness is per-symbol, not portfolio-level overlap; long-horizon t-stats are mostly pseudo-replication. |
| 3 | 2026-10-30 05:45 | E5-de-anchored primary bake-off (top-decile gate, long side, touch-restricted labels). CAD winner `tc_rating` (mean \|gated IC\| 0.0169); USD winner `mom_12_1` (0.0095). E5 composite does NOT win either market. `wi016_addendum_bakeoff_{USD,CAD}.md`. | `tc_rating` is a static watchlist column, not a price feature; winner picked by mean \|IC\| across targets. |
| 4 | 2026-10-30 05:45 | Cost bands 10/20/30 bps: no verdict flips. Barrier-resolved: USD NOT_CLEAR, CAD CLEAR at every band; realized-return CLEAR at every band. Per-band per-market CLEAR/NOT_CLEAR lines in the probe reports. | 20 bps remains an unconfirmed WI-011 assumption; the 10–30 bps bracket does not change this verdict. |
| 5 | 2026-10-30 05:45 | Duration columns `tb_duration_{k}_h{h}` (1-based bars to first touch; vertical = h) added to `label_columns`/`compute_triple_barrier`; regression test updated. k15 h8 barrier mean 3.9 bars (both markets). `wi016_addendum_duration_{USD,CAD}.md`. | Duration recorded going forward only; no labels rebuilt and no model trained. |

ADDENDUM CONCERNS: placebo bounded to top-100 FDR survivors; uniqueness approximated per symbol; realized-return CLEAR is a diagnostic and must not be read as barrier capture; frozen `wi016_probe_*` read-only; unrelated working-tree config edits (watchlists/sector_map) left untouched.

STATUS: DONE | evidence: `uv run pytest -q` → 515 passed; `uv run pytest tests/test_wi016_addendum.py` → 15 passed; both-market addendum runs (log `logs/wi016_addendum_run.out`) wrote `reports/wi016_addendum_probe_{USD,CAD}.md` (barrier-resolved: USD NOT_CLEAR, CAD CLEAR at 10/20/30 bps), `reports/wi016_addendum_bakeoff_{USD,CAD}.md` (winners `mom_12_1` / `tc_rating`; E5 composite loses), `reports/wi016_addendum_duration_{USD,CAD}.md`. Step 6 NOT started; frozen artifacts untouched.

## STEP 6 (conditional meta-labeler + actions — CAD only, admin pre-approval PM cycle 21)

Authoritative amendments applied (PM_LOG cycle 21): primary = `yangzhang_21` top-decile per date
(long side) NOT the E5 composite (`tc_rating` excluded — point-in-time violation; E5 lost the
de-anchored bake-off); targets = only the 4 addendum-cleared barrier targets; top-2-decile
training expansion with a per-event decile flag (D-016 Q5); embargo `max(20, h)` everywhere;
5-seed placebo; CB-04 calibration; 20 bps overlay with NO_TRADE default; new artifact
`reports/wi016_shortlist_CAD.parquet`; decisions evaluated on top-decile events only.

| # | Done (UTC) | Result (≤50 words) | Concern (inline) |
|---|---|---|---|
| 1 | 2026-10-30 20:52 | `src/wi016/meta_labeler.py`: `yangzhang_21` per-date top-decile long events; top-2-decile training expansion + `decile_flag`; barrier-resolved meta-label (bet P&L>0); per-target embargo `max(20,h)`; `run_cv`/`fit_calibrated`/`CalibratedXGB` reuse; 5-seed placebo. | Long-horizon folds train on short history by construction (h144 fold0 n_fit 30k) — expected, not a leak. |
| 2 | 2026-10-30 20:56 | `src/wi016/actions.py`: entry + symmetric barrier/time-stop exit + meta-probability size + abstain; NO_TRADE default under the 20 bps overlay; emits `wi016_shortlist_{market}.parquet` (WI-014 head columns + meta columns); addendum gate enforced in code. | Expected edge prices barrier distance only (`(2p−1)·k·ATR/close`); intra-horizon drift and slippage beyond the flat band unmodelled. |
| 3 | 2026-10-30 20:58 | 27 new tests: event/decile semantics, leakage-safe folds (h8/h55/h144 gaps ≥ embargo, fit/calib purged), cost-aware abstain (probability floor + cost flip), output schema/path, no-order-execution surface. | none |
| 4 | 2026-10-30 21:33 | CAD run (full universe): 4 targets, events 121k/163k/157k/87k; OOF AUC 0.507–0.528 vs placebo 0.499–0.500; calibration isotonic on all folds; shortlist 148 rows @ 2026-10-28 (147 TRADE / 1 NO_TRADE). | **Edge is thin** (AUC lift 0.008–0.036 over placebo); h144 folds 1–2 near base rate. **Cost band not binding** (99.3% trade) — the 20 bps overlay is dwarfed by the barrier payoff, so abstention is driven by the probability floor. |
| 5 | 2026-10-30 21:33 | Reports `wi016_meta_labeler_CAD.md` (OOF vs placebo, decile strata, fold geometry, auto-computed caveats) + `wi016_shortlist_CAD.parquet`. Frozen `wi014_*` (2026-10-26) and `perfanalytics/` (2026-10-28) untouched. | Artifact is mechanically tradeable but statistically marginal — gate interpretation is the admin's; no execution path exists. |
| 6 | 2026-10-30 21:34 | Full suite `uv run pytest -q` → 542 passed. Targeted `pytest tests/test_wi016_meta_labeler.py tests/test_wi016_actions.py` → 27 passed. | none |

STEP 6 CONCERNS: (a) trade share 99.3% — the cost overlay almost never binds at the barrier payoff
scale, so the abstain channel rests on the calibrated probability floor; (b) OOF AUC lift over the
5-seed placebo is 0.008–0.036 — real but thin, and h144 folds 1–2 sit at the base rate; (c) AP is
partly base-rate (pos rate 0.525–0.560); (d) the primary is `yangzhang_21`, a clean price feature —
`tc_rating` (bake-off winner) was excluded per PM adjudication, so the portfolio's clean-primary
edge is knowingly not the maximal bake-off number. No deviation from the amended step: the plan's
file paths and the amendment's target list/primary/expansion/embargo/cost all match the code.

STATUS: DONE | evidence: `uv run pytest tests/test_wi016_meta_labeler.py tests/test_wi016_actions.py` → 27 passed; `uv run pytest -q` → 542 passed; `uv run python -m src.wi016.meta_labeler --market CAD` → `reports/wi016_shortlist_CAD.parquet` (148 rows, 147 TRADE / 1 NO_TRADE @ 20 bps, scoring date 2026-10-28, schema verified) + `reports/wi016_meta_labeler_CAD.md`; frozen `reports/wi014_*` and `reports/perfanalytics/` unmodified (git status clean of tracked report changes). USD untouched (NOT_CLEAR → descriptive only).
