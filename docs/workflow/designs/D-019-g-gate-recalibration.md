# D-019 — G-gate recalibration: enabling more development without lowering the truth bar

Status: **ACCEPTED (admin "accept all" 2026-11-01)** — R1–R4, R6, R7 adopted as the
G-gate recalibration direction; R5's IBKR-schedule validation **dropped by admin**
(20+5 bps stays a labeled assumption in every G3 memo; no ticker-download work).
Planner folds R1+R2 into the next G2-touching plan; R7 goes to WORKFLOW.md §1.
Evidence parent: WI-018 gate brief + memo
(`docs/archive/old-files/human-briefings/2026-11-01-gate-WI-018-condition-first.md`,
`reports/wi018/summary_USD.md`). Context: WI-018 was the last research run before
MVP publish — this recalibration governs any *post-MVP* research WI.

## 1. What the G-series gates are and why they exist

The G-ladder is the study-side instantiation of the project's hard constraints
(`.agents/rules/`: no live trading, human gate on ship decisions). Its history is
incident-driven, not theoretical:

- **G-003 origin (WI-001, 2026-10-21)**: Sprint 5 shipped demo PDFs past a *failed*
  Gate 4. The lesson — "gates must actually gate" — became WORKFLOW.md §1 rule 4 and
  the blocking-QA design.
- **WI-009b (2026-10-25)**: a contrastive ranker "beat" the factor baseline by being
  *anti-correlated* (−0.148 vs +0.127). The model had learned a full-history vol tilt
  and the eval window inverted the regime. Lesson → **same-sign clause** added to every
  skill bar.
- **WI-009c (2026-10-25)**: 0/5 targets cleared the bar; 89-feature pool added nothing.
  Lesson → **probe-first gating**: never spend on a model route before a cheap probe
  clears.
- **WI-011 (2026-10-25)**: no condition survived costs. Lesson → **cost overlay as a
  gate (G3)**, NO_TRADE the default.
- **WI-018 (2026-11-01)**: 2,506/3,658 "survivors" — the wall-of-survivors failure mode
  the plan pre-registered. Lesson → **survivor-density red flag**, and the recognition
  that CI/BH significance bars carry zero discriminating power at N≈5,000 dates
  (half-width ~0.006–0.009).

**G1/G2/G3 as implemented in WI-018:**

| Gate | Job | Failure mode it exists to catch | Cost |
|---|---|---|---|
| **G1** atlas | Descriptive conditional base rates, per state, with CIs. Always delivers. | Nothing — spends no testing budget. | ~9 min run |
| **G2** probe | Cheap falsification: OOF lift + BH-FDR + same-sign + density red flag. | Curve-fit conditions; noise masquerading as signal. | ~1 h run |
| **G3** cost overlay | Costs (20+5 bps proxy) on a *small, explainable* G2 winner set. | Thin edges that die on costs. | Only runs on a G2 win |

Why so strict: every prior "positive" that reached a human gate without this stack
was either regime-inverted (WI-009b), noise-level (WI-009c/WI-002), or died on costs
(WI-011). The gates are the accumulated scar tissue of those results, and the E5
factor screener survived them — the stack demonstrably passes real signal.

## 2. The problem to fix (what WI-018 exposed)

The gates are **strict in the wrong dimension**. They filter hard on *statistical
significance*, which is free at this N, and have no lever for *effect size*, which is
what actually matters. Consequences:

1. G2 can only produce two outcomes — a handful of survivors (proceed) or a wall
   (stop). There is no "thin but interesting, keep researching" tier, so the study
   ladder dead-ends instead of feeding the backlog.
2. G3's structure (per-condition IC streams) only scales to ~dozens of conditions;
   there is no cheap path to cost-screen a large candidate set, so "run G3 on the
   wall" is infeasible as built.
3. The survivor-density red flag is a *flag*, not a calibrated measurement — 0.685
   tells us the bars are broken, not where the real rate effect ends.

## 3. Recommendations — loosen *capacity*, never the truth bar

Admin intent ("enable additional testing") is met by adding tiers and cheaper
machinery, not by relaxing pass criteria. Lowering the bars would only re-produce
WI-009b-class false positives with extra steps. Specifically:

**R1 — Effect-size floor as the primary G2 bar** (replaces significance as the binding
filter). Minimum |lift| scaled to costs (e.g., lift ≥ 2× the 25 bps round-trip
assumption), plus fold-wise sign stability (sign holds in 5/5 folds). CIs and BH-FDR
become secondary checks. This makes G2's verdict monotone in effect size instead of
in N.

**R2 — Two-tier gate outcomes (the "optimism" lever).** G2 verdicts become:
- **GREEN**: small, explainable survivor set clears the effect floor → G3 as today.
- **AMBER**: 1–k conditions clear effect floor but fail stability → does NOT trigger
  G3, but *auto-opens a follow-up WI* with the survivors recorded as ranked
  hypotheses, not discarded. This is the change that lets development continue past a
  negative — today a red flag means everything stops.
- **RED**: wall of survivors under the floor → NO-GO as today, memo documents why.
The truth bar for *shipping* (GREEN + G3 + human gate) is unchanged.

**R3 — Bulk-IC cost screen for large candidate sets.** A batched, bounded approximation
of the G3 overlay (vectorized pooled-IC per condition family, batch 10-style, n_jobs=2)
so "cost-screen the wall" becomes a bounded job instead of 2,506 per-condition streams.
Still proxy-labeled; never a ship decision by itself.

**R4 — Calibrate the density bar with a permutation null.** One cheap run: permute
`first_touch_34` within date, re-run G2, record survivor density under the null. That
turns the 0.10 red-flag constant into a measured threshold and converts the wall from
"symptom" into "quantified gate power". Cheap (~1 probe run) and should be done before
any G2 redesign.

**R5 — Cost-proxy caveat convention (amended by admin 2026-11-01).** IBKR-schedule
confirmation and any ticker-download-based validation are **dropped** by admin.
The 20+5 bps figures stay explicitly labeled assumptions in every G3/cost memo
(convention already in the WI-018 memo). If paper-track realized costs are ever
compared to the proxy, that is a memo addendum, not a gate input.

**R6 — Family representativeness as a gate input.** Non-representative families
(`fib_dist`, `range_pos` in WI-018) are tagged in the artifact; any WI citing them must
first re-test the family's other kept windows. Longer term, replace "pick best window
per family" in the WI-017 prune method with a stability-across-windows score.

**R7 — Process rule (from DEVIATION 1):** pre-registered failure modes mechanically
gate downstream plan steps (fail-closed wording wins when plan steps conflict). Belongs
in WORKFLOW.md §1 at the next Planner pass; no agent should resolve a plan
contradiction on a gate-interpretation question again.

## 4. What would falsify this proposal

- If R4's permutation null shows the wall disappears under permuted labels, then the
  wall was leakage, not bar-power — the fix is then leak-hunting, not recalibration.
- If R1's cost-scaled floor is set so high that even the E5 screener's validated factors
  fail it, the floor is miscalibrated (sanity-check any floor against E5's IC first).
- If the paper-track shows realized costs materially below 25 bps, several historical
  NO-GOs deserve one re-cost under R5 before being treated as final.

## 5. Suggested sequencing (if accepted)

1. R4 permutation null (one probe run) — cheap, decides whether R1 needs calibration
   data or a leak hunt. Post-MVP only (WI-018 was the last research run pre-publish).
2. R1+R2 as one WI (G2 v2: effect floor + tiered verdicts) — re-run on the existing
   WI-018 artifacts, no new data needed. Post-MVP.
3. R3 bulk-IC path only if a future wall needs costing.
4. R7 (fail-closed plan rule) — Planner folds into WORKFLOW.md §1 at the next pass;
   applies immediately as a drafting convention in new plans.
