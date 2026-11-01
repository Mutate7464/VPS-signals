# WI-018 — condition-first directional study, `first_touch_34` (USD): memo

**Ship shape: memo only.** No trading integration, no order execution, no ranking/screener change and **no shortlist CSV** are produced by this work item (D-018 Q5, plan step 4).

Generated from the on-disk artifacts: `reports/wi018/{preflight_USD.json, atlas_USD.json, probe_USD.json, g3_USD.json}`. Market: **USD only** — CAD was skipped by design (D-018 Q2).

## G1 — condition atlas (delivered)

- `reports/wi018/atlas_USD.json` / `.md`: 704 state cells (88 features x 8 states), 702 estimable, 2 explicitly unevaluable.
- Universe: 593 USD symbols, 2340073 rows, 2006-10-26..2026-10-28 (5032 dates).
- Unconditional `first_touch_34` split (pooled): 0.3756 up / 0.2971 down / 0.3273 neither.
- G1 is descriptive: it spends no multiple-testing budget and assigns no pass/fail.

## G2 — falsification probe

- Verdict: **G2_PASS_WITH_RED_FLAG** (g2_pass=True, red flag=True).
- Family: 3658 hypotheses (1408 univariate + 2250 conjunctions), BH-FDR at 0.05 over the complete family; survivors 2506, density 0.6851.
- Folds: 5 chronological held-out blocks, embargo 34 sessions (max(20, horizon)); decision rule = CI excludes zero AND BH-FDR reject AND same-sign bar.
- G3 gate: not invoked — survivor density 0.685 > 0.1: a wall of survivors is a noise/leakage red flag, not a win, so G3 is not invoked.
- Secondary targets `first_touch_24`/`first_touch_39` were read as robustness only; decisions always used `first_touch_34`.

## G3 — cost overlay (conditional on G2)

**SKIPPED.** survivor density 0.685 > 0.1: a wall of survivors is a noise/leakage red flag, not a win, so G3 is not invoked

The standing default is `NO_TRADE`: a wall of survivors is not a condition set to trade, so nothing is costed out.

## Limitations

- The cost overlay's `|IC| x 1000` bps scale is a **screening proxy, not a P&L model**: it ignores turnover, borrow, market impact, and the 20+5 bps cost figures are **assumptions** carried from WI-011.
- Conditions are within-date cross-sectional states of the pruned WI-017 grid; features whose kept windows were not representative of their family (the G1 family check) are single-window evidence.
- Bootstrap margins use circular 20-date blocks (1,000 draws, seed 42) and the normal-approximation t-statistic; both are approximate, and a thin effect on a 5,000-date panel is easy to over-read.
- Ordinal 3-way target: 'up-first/down-first/neither' is a direction read, not a return, so lift and IC say nothing about magnitude or tradability of the move itself.
- USD-only universe: no cross-market confirmation exists by design (CAD deferred).
- **G2 raised the survivor-density red flag**: a wall of survivors is a noise/leakage symptom, so this memo does not treat the survivor set as a signal list and G3 was not invoked on it.

## Follow-up

**No follow-up is warranted on this evidence, and the survivor set must not be used as a signal list.** G2 delivered its pre-registered failure mode: a *wall* of survivors (2506 of 3658 hypotheses, density 0.6851 against a 0.1 red-flag bar). At this sample size the out-of-fold CI no longer separates a real condition from a generic cross-sectional rate effect, so the wall is a noise/leakage symptom rather than a result; G3 was therefore not invoked and the standing decision is **NO_TRADE**. Any follow-up must first tighten the G2 bar itself (effect-size floor, fold-wise stability, or a shrunk estimator) — costing out this survivor set would only launder the same problem.

---

Artifacts: `reports/wi018/atlas_USD.{json,md}`, `reports/wi018/probe_USD.{json,md}`, `reports/wi018/g3_USD.json`, this memo (`reports/wi018/summary_USD.md`), `reports/wi018/preflight_USD.json`. Descriptive research only; the human gate is unchanged.
