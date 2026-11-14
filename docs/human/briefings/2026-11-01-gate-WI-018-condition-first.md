# Gate Brief — WI-018: condition-first directional study, `first_touch_34` (USD)

Date: 2026-11-01 · WI-018 (traceable to G-001) · Plan `docs/plans/26-W45-WI-018-condition-first-first-touch.md` · Log `docs/plans/logs/WI-018-condition-first-first-touch.md`
Domain: complicated · Door: two-way (research artifacts only; nothing shipped)

**Verdict in one line:** the study ran exactly as pre-registered and produced its own failure mode — the G2 probe found **2506 of 3658 condition "survivors"** (density 0.685) instead of a handful, which the plan calls a **wall of survivors = red flag, not a win**; G3 (cost overlay) was therefore **not invoked**, and the standing decision is **NO_TRADE**.

**Decision requested:** ACCEPT (close WI-018 as a documented negative, E5 screener stands) | HOLD (if you want the cost overlay run on the wall anyway) | REJECT (re-plan the G2 bar)

## What was supposed to happen

A condition-first study on our own USD universe: G1 describes every state of the pruned 88-column feature grid, G2 tests whether any state predicts *direction* (`first_touch_34`: up-first / down-first / neither) out of sample with a multiple-testing budget, and G3 (costs) runs **only** if G2 finds a small, explainable winner. Ship shape: a memo, no rules, no shortlist.

## What actually happened

G1 delivered the atlas (704 state cells, 702 estimable). G2 then tested 3658 hypotheses (1408 univariate states × 2 directions + 2250 conjunctions built from the 50 best univariate BH survivors) over 5 chronological folds with a 34-session embargo and 2850 held-out dates. **2933 hypotheses passed BH-FDR at 5%, and 2506 passed all three stated bars** (CI excludes zero, BH-FDR, same-sign clause) — a survivor density of **0.685 against a 0.10 red-flag bar**. The plan pre-registers that outcome as "not a win", so G3 was skipped and the memo records NO-GO with the reason. The whole ladder is reproducible: 100 WI-018 tests + the full repo suite (662 passed), and both the probe and atlas artifacts were regenerated from HEAD and diffed (`/tmp/opencode/probe_pre_gate.json`, breadth-only atlas diff).

## The numbers that decide this

| Metric | Threshold (why) | Actual | Pass? |
|---|---|---|---|
| G2 survivors | ≥1 with CI excluding zero + BH-FDR 5% + same-sign (the pass clause) | 2506 of 3658 | mechanically yes |
| Survivor density | ≤ 0.10 — above that a wall is noise/leakage, "not a win" (plan step 3) | **0.685** | **FAIL (red flag)** |
| G3 cost overlay | invoked only for a G2 win; 25 bps assumption; NO_TRADE unless net > 0 | **not invoked** (gate `g3_eligible=false`, reason recorded) | correct branch |
| G1 coverage | 704/704 cells represented or marked; rates sum to 1; CIs present | 704 cells, 702 estimable, 2 marked; checks PASS | PASS |
| Ship shape | memo only — no executable rules, no shortlist CSV | `summary_USD.md` + `g3_USD.json`; 0 CSV; `executable_output=false` | PASS |
| Evidence | WI-018 tests + repo suite pass | 100 passed; 662 passed | PASS |

## Check it yourself (5 minutes)

- `uv run pytest tests/test_wi018_*.py -q` — expect: **100 passed**
- `uv run python -m src.wi018.probe --market USD --check-report reports/wi018/probe_USD.json` — expect: **PROBE CHECK PASS** (the line `pass_and_gate_flags_consistent` shows survivors=2506, density 0.685, `g3_eligible=False`)
- `uv run python -m src.wi018.cost_overlay --market USD --check-report reports/wi018/g3_USD.json` — expect: **G3 CHECK PASS**, decision SKIPPED with the red-flag reason
- `reports/wi018/summary_USD.md` — read §G2 and §Follow-up (the one-page decision)
- `reports/wi018/probe_USD.md` — the survivor table and "closest to passing"; top hits are `amihud_102` quintiles (lift ±0.04–0.07, margin ~0.0075)

## Risks & what could be wrong

- **The red flag is a test-power symptom, not proof of "no signal".** Over 2850 held-out dates the CI half-width shrinks to ~0.006–0.009, so *almost any* nonzero cross-sectional rate difference looks significant; the bars no longer separate a real thin edge from a generic rate effect. The honest read is "not usable as a signal list", not "direction is provably zero".
- **The gate call is a Build interpretation (log DEVIATION 1).** The plan says a wall is "not a win" (step 3) while step 4 says invoke G3 "only for G2 survivors". If you intended G3 to run on the wall, say so: it is a new order (and needs a cheaper bulk-IC path — 2506 per-condition IC streams are not feasible as built).
- **G3's cost proxy is unvalidated on real data** this round (skip path); its cost math was only exercised on synthetic survivors. The 20+5 bps figures were always assumptions.
- **Two G1 families are single-window evidence** (`fib_dist`, `range_pos` failed the representativeness check) — carry that caveat into any follow-up.

## One thing worth learning

More data made this test *worse*, not better. A confidence interval's half-width falls like 1/√N, so on a 5,000-date panel any real-but-tiny cross-sectional difference becomes "significant" and significance stops being evidence — which is exactly why the plan pre-registered a *density* red flag alongside the significance bars. The fix is a bar that scales with the effect (an effect-size floor, fold-wise stability, or a shrunk estimator), not a bigger sample.

## How to respond

- **"gate WI-018 approved"** → close WI-018 as a documented negative (memo is the deliverable); E5 screener unchanged
- **"hold — run G3 on the wall"** → new order; I will first need a bulk-IC design (bounded, batched) before any cost numbers
- **"hold — tighten the G2 bar"** → re-plan G2 (effect-size floor / fold-wise stability) as the follow-up WI
- **"reject"** → back to PLAN with this evidence bundle

## DECISION (admin, 2026-11-01)

**ACCEPT — WI-018 closed as a documented negative** ("accept all", in-chat). The memo
is the deliverable; E5 factor screener stands unchanged as the MVP signal. DEVIATION 1
adjudicated: Build's fail-closed interpretation (`g3_eligible = g2_pass and not
red_flag`) is the correct reading and becomes the convention (D-019 R7 → WORKFLOW.md).

Also ordered same chat:
- **IBKR/ticker-download concerns dropped** (ELE re-download, HMMC/ICL repair,
  TRI/SPCX clearance, WI-004 ingest Phase 2 — removed from backlog/carry-forward).
- **D-019 G-gate recalibration accepted** (R1–R4, R6, R7; R5's IBKR-schedule
  validation dropped — 20+5 bps stays a labeled assumption).
- **WI-018 is the last research run before MVP publish.** Next work item: closeout —
  summarize prior work/spirit/conclusions, clean up and refactor existing
  data/structure for simplicity, and capture process learnings (token minimization,
  communication, expectations). → WI-019 (BACKLOG, awaiting admin ordering).
