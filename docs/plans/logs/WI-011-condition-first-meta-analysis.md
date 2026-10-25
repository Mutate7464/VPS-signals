# WI-011 — Condition-first meta-analysis — EXECUTION LOG

Plan: `docs/plans/2026-10-25-WI-011-condition-first-meta-analysis.md` (frozen after planner pass).
Append-only: one row per step, ≤50 words; full output → step report artifact, cited by path.

| Time | Step | Outcome | Concern? |
|---|---|---|---|
| 21:17 | 1 | Preflight PASS: features/targets both 701,599 rows, 315 symbols, 2691 dates (2016-01-04→2026-09-22), 0 duplicate keys, key-set+key-order alignment PASS. Report `reports/wi011_preflight.md`. | none |
| 21:22 | 2 | Conditions built + defined: 26 conditions (18 atomic, 8 cross), 707,899 rows/315 symbols, all float32, warm-up held as NaN. Tests 15/15 PASS; runtime truncation spot-check on 5 real tickers PASS. Report `reports/wi011_condition_definitions.md`. | Step 3 indicator subset not yet applied — Step 2 re-run follows it per plan 1b |
| 21:26 | 3 | Indicator association done (89 indicators × 4 states, within-date z, no forward returns). 6 redundancy clusters; selected 6: pct_from_high_f102, fib_dist_f102, di_spread_100, vwap_zscore_50, atr_pct_100, vwap_zscore_100. Reports `wi011_indicator_association.md` + `wi011_selected_indicators.json`. | Near-mechanical overlap of 4 selected indicators with the channel state — disclosed in report, not re-selected (rule fixed pre-results) |
| 21:28 | 2b | Step 2 config updated per Step 3(a): re-ran `wi011_conditions.py`, now 38 conditions (26 declared + 12 ind_* extremes), POINT_IN_TIME PASS, tests 15/15. | none |
| 21:39 | 4 | Horizon sweep over 8 horizons × 38 conditions = 304 cells, purged folds (embargo max(20,h)) + 2 disjoint sub-windows. Report `reports/wi011_condition_expectancy.md`. | Only 26 of 38 conditions were evaluated on the first run — `keep_only` dropped the ind_* columns; fixed in-script (DEVIATIONS note), re-run gives 304 cells |
| 21:47 | 4b | Sign stability was nearly universal (283/304), so added the market-drift control: same clause applied to the within-date component → 82 stable / 96 unstable. Both verdicts reported; raw verdict kept primary. | Added diagnostic mid-step (not a re-selection); disclosed in report as added within Step 4 |
| 21:52 | 5 | TS probe: 24 TS/CS rules × 8 horizons + 6 Step-4 position conditions = 240 cells, same purge and sub-windows. Report `reports/wi011_ts_momentum.md`. Found: CS framing carries the larger within-date effect (mean |within| 29.7 bps vs TS 14.1); raw means are market-drift dominated. | none |
| 22:04 | 6 | Cost/frequency/concurrency filter: 73 candidate cells (stable positive within-date), 10 pass net expectancy, 0 pass frequency (100–400/yr) and 0 pass concurrency (4–12) → 0 survivors. Verdict: none survive costs at this universe size. `reports/wi011_tradeable_conditions.md` + `reports/wi011_decision_rules.md` (rules N/A, NO_TRADE_DEFAULT, HUMAN_GATE: STOP). | Within the 5–15d hold envelope every candidate's within-date effect (+22…+37 bps) is below its round-trip cost (−32…−42 bps net); the 10 net-positive cells are 60/120d holds, outside the envelope. Agent stopped at the human gate |

## DEVIATIONS

1. **Step 4 first run evaluated only 26 of 38 conditions.** `build_condition_panel(..., keep_only=...)`
   was passed the declared vocabulary but not the Step 3 `ind_*` names, so the 12 indicator conditions
   were dropped before stacking; the run reported 208 cells instead of 304. Fixed inside
   `scripts/wi011_condition_expectancy.py` (add `indicator_condition_names(selected)` to the keep set)
   and re-run: 304 cells. The publishable numbers come from the fixed run; no threshold or rule changed.
2. **Market-drift control added within Step 4 (`STABLE_SIGN_WITHIN`).** The plan-specified stable-sign
   clause (same sign in both sub-windows, |t| > 2) was satisfied by 283 of 304 cells, because the
   equal-weight CAD universe drifts up and nearly every condition fires on some positive-drift days. The
   same clause was therefore applied a second time to the *within-date* component (each firing row's
   return minus its own date's all-name mean). Both verdicts are reported side by side, the plan's raw
   verdict remains the primary marker, and the addition is disclosed in the report. This adds a
   diagnostic; it does not re-select a sign or a threshold.
3. **No separate slippage term (documented, not silent).** The Step 6 cost model charges the Corwin-Schultz
   spread estimate (or the Amihud fallback) once per round trip plus the IBKR CAD commission on both
   sides, and carries 1.5x/2.0x spread scenarios instead of an additive slippage constant. Disclosed in
   `reports/wi011_tradeable_conditions.md`, with the commission parameters flagged for admin confirmation.
4. **IBKR commission parameters are assumptions.** The repo contains no Canadian commission schedule;
   CAD 0.01/share, CAD 1.00 minimum per order, 0.5% of trade value cap, and a CAD 5,000 position notional
   are recorded as constants in `scripts/wi011_tradeable_conditions.py` and must be confirmed at the gate.
   No web lookup was possible in this session, so they are presented as assumptions rather than citations.

STATUS: DONE (steps 1–6, PM-set — Build session exited before updating; chain re-run finished 21:44, tests 15/15 PM-verified, step greps verified)
