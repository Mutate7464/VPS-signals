# WI-016 addendum brief — honest-edge probe (both markets), PM finding 2026-10-30

## Mission

Run the addendum probe ordered by the admin (2026-10-30): re-test the step-5 edge under the PM finding's corrections, **for CAD and USD both**. Reuse ALL existing WI-016 machinery (`src/wi016/{triple_barrier,admission,probe}.py`, unified feature grid). This is analysis + reports + tests only — NO model training, NO shortlist changes, NO frozen-artifact writes.

## Why (PM finding, log `docs/plans/logs/WI-016-triple-barrier-fib-labels.md`)

The step-5 ±1 labels conflate barrier first-touch with vertical drift-sign (~45% of h8 events touch no barrier). The CLEAR/NOT_CLEAR verdicts rest on a proxy edge and an unconfirmed 20 bps cost. This addendum measures the tradeable edge honestly.

## Deliverables (all `reports/wi016_addendum_*`, `--market` parametrized, run BOTH USD and CAD)

1. **Touch-restricted probe:** within-date rank-IC of the unified features + E5 against (a) touch-restricted labels (rows where `tb_touch_*` ∈ {+1,−1} only — barrier-resolved trades) and (b) the realized-return regression target `tb_fret_h*`. Both k ∈ {1.5, 2.0}, all horizons {8,21,55,144,233}. Report per-target class counts and how the verdict changes vs step 5.
2. **Overlap-aware statistics:** average-uniqueness weights (AFML ch. 4 style) applied to per-date IC t-stats for overlapping windows (h=8 daily events ⇒ 8× overlap); report both weighted and unweighted so the inflation is visible.
3. **Primary bake-off (de-anchor E5):** candidate primaries — E5 composite rank, `mom_12_1`, `vol_20`, probe winner `yangzhang_21`, `tc_rating` — each used to gate events (top-decile per date/market, long side). Report event-gated vs ungated IC on touch-restricted labels, per market. The best primary wins on data; E5 is not assumed.
4. **Cost sensitivity:** the 20 bps overlay is an unconfirmed WI-011 assumption — report net-edge bands at 10 / 20 / 30 bps so the admin can see where each market's verdict flips.
5. **Duration columns (cheap, add to labels):** first-touch offset (bars) alongside `tb_touch_*` type, so duration is recordable going forward; regression test updated.

## Constraints (hard)

n_jobs=2 · float32 · symbol-sequential, no all-ticker uncompressed frame · trailing-only causality (existing tests must keep passing) · new artifacts `wi016_addendum_` prefix only · `uv run pytest` green (existing suites + new tests for touch-restriction, uniqueness weights, bake-off gating, duration column) · reports must end in an explicit per-market CLEAR / NOT_CLEAR line under each cost band.

## READ SCOPE

`docs/plans/26-W44-WI-016-triple-barrier-fib-labels.md` (steps 2,5), PM FINDING section of `docs/plans/logs/WI-016-triple-barrier-fib-labels.md`, `src/wi016/probe.py`, `src/wi016/triple_barrier.py`. Stop after writing reports + updating the log; PM verifies then takes the verdict to the admin gate.
