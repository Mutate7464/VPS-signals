# D-026 — L0/L1 extension: sequencing and first-pursuit decision

- Source: `docs/plans/26-W46-L0L1-extension-review-v2.md` (Opus review, 11 sections). Input pack: `docs/workflow/briefs/2026-11-13-L0L1-batch-brief.md`.
- Governing rules: AGENTS.md (n_jobs≤2, float32, bounded memory, no new ingestion, no secrets, no live trading), D-023 (two-layer ML gate), D-025 (tiers).

## Context

- **L0 (T1):** 249 panel columns, coverage 1.000. Recount: 5 keys, `close` and `atr` are absolute levels (excluded by design) → 244 candidate predictors; 102 `cs_*` are same-date rank transforms; effective independent base signals ≈110. Attribution concentrates in volatility, path-shape and event-geometry columns. Volume, sector, mean-reversion and breadth families show zero permutation evidence.
- **L1 (T2, predictive-only):** 9,745-row manifest. Within three-binary, only `b_hold` survives (calm outcome; a negative-filter use). WI-048 T2 survivors are PROVISIONAL: `vol_expand` 24/24, `high_low` 24/24 (base rate 0.75–0.87, lift ceiling ≈1.25×), `up` 11/24 at AUC≈0.50 (no economic use; kept in library).
- **Open integrity question:** `vol_expand` may be computed on `[t-h+1, t]` (non-forward) rather than `[t+1, t+h]`. Unverified; every item referencing it depends on it.
- **L2 (T3):** closed. EVAL edge ≈0 vs 25 bps.
- **Locks:** WI-048 d/e/f still in `.hermes/locks.json`; clearing is a human pre-dispatch action.
- **Compute:** 2 vCPU / 8 GB, credit model; default cap 2.5 core-h per WI; ≥30 min idle after any ≥1 core-h burst.

## Options considered

**L0 feature blocks (6 net-new, reference grid R12 = 12 cells, m=12):**
- L0-1 Swing-structure history (~2.0 core-h) — extends the top-attributed event-geometry axis; payoff-relevant.
- L0-2 Realized asymmetry / semivariance / skew (1.5) — payoff-shape, distinct from WI-047 #2 range levels.
- L0-3 Regime age / run-length (1.5) — temporal duration; targets release-vs-just-released timing; soft dependency on WI-047 #1.
- L0-4 Jump intensity (1.5) — tail plausibility; adverse excursion risk.
- L0-5 Universe vol-regime dispersion (1.0, date-level) — may be a WI-047 #3 variant; needs admin net-new ruling.
- L0-6 Effort-vs-result / climax (1.5) — relational volume; low prior given volume silence.

**L1 targets (m=24 per family, 6 horizons × {lgbm, xgb} × 2 markets):**
- L1-1 Forward cross-sectional vol rank (2.0 per form) — removes `vol_expand` self-relative inversion risk; binary and continuous forms.
- L1-2 Payoff-ratio MFE/MAE target (2.0 per form) — the payoff half of EV as a label; unit-test label window starts at t+1.
- L1-3 Expansion-direction decomposition A·B as fixed product (1.5) — `up` is chance unconditionally; B may be near chance.
- L1-4 Sample-uniqueness weighting (1.0, method variant, m=12) — calibration bias from overlapping labels.

**L1-layer options (§9):** status quo per-cell (reference); horizon pooling (1.5, benchmark later); cross-market pooling (2.0, second-in-line); multi-task MLP (>2.5 on 2 vCPU, defer); **L1.5 meta-label, swing-side primary (2.0–2.5, highest precision@k potential)**; seed/bagging averaging (1.0, companion); stacking (≈2× compute, leakage-prone — do not build).

**Re-ranked, not counted:** WI-047 #1 regime percentiles (ratified, run first among WI-047); self-proposed magnitude/time-to-touch; WI-047 #2–#5; cross-feature interactions; vol terciles (likely redundant with L1-1); range-occupancy.

## Decision

1. **Phase 0 is mandatory and blocks all else** (≤0.5 core-h, no new training): clear/verify locks; verify `vol_expand` window in `src/swing_bsh/targets_ext.py`; verify `close`/`atr` excluded from every feature list; build the precision@k / top-decile harness on existing OOF; run the stratified `atr_pct_21` diagnostic (descriptive only); 0.25 core-h timing probe to rescale all estimates.
2. **If `vol_expand` is confirmed as computed at t:** quarantine its survivors and replace it in R12 with `b_hold` + L1-1 before any L0 block runs.
3. **L0 order:** L0-1 → L0-2 → L0-3 → L0-4 → L0-5 (after admin net-new ruling) → L0-6. Each block is one WI, one R12 family, truncation and label-lag unit tests mandatory.
4. **L1 targets:** L1-1 first (directly tests the product question), then L1-2, L1-3, L1-4. Split any 24-cell family by market if the timing probe exceeds 2.5 core-h; BH runs once over the full m=24.
5. **L1 layer:** pursue **L1.5 meta-label** after L1 targets (per §2d phase order), using the decomposed positive class P(not hold)·P(profit | touched) as a fixed product, with seed-averaging as the cheap companion benchmark. Do not stack.
6. **Ranking criterion:** EV-proxy is diagnostic at L1 (plan §11 default). No L1 verdict is economic (D-023).

## Consequences

**Positive**
- Phase 0 is cheap and removes the two largest integrity risks (vol_expand definition, level leakage) before ~20 core-h of dispatch.
- L1-1 and L1-2 directly target precision@small-k and payoff ratio, the EV terms the product cares about.
- Uniform protocol (R12 / m=24, BH per family, predictive header) keeps multiplicity bounded and comparable.

**Negative**
- Projected total ≈23 core-h across ~17 WIs, plus ≥30 min idle between bursts: wall-clock is days, not hours. Estimates are unmeasured until the timing probe.
- Phase order (L1.5 in Phase 3) conflicts with the plan's headline ("pursue meta-labeling first"). Admin must confirm sequencing.
- Meta-label `1 − b_hold` term uses another model's OOF output; the plan's own §9 forbids OOF-as-feature. Needs explicit ruling that a fixed product of separately fitted models is not stacking, plus a permuted-label leakage check.
- L0-5 may be a WI-047 #3 variant; L0-6 has low prior.
- Plan arithmetic: Phase 2 says "seven family runs" but the table yields six; reconcile before ledger registration.
- All literature citations are unverified recollections (*[verify]*) and must not be cited as fact.

## Status

`accepted` (admin in chat, 2026-11-13). Rulings:
1. Lock clearance (d/e/f) — **DONE** (`.hermes/locks.json` emptied this session).
2. `vol_expand` — **VERIFIED DEFECTIVE** (backward-looking, `src/swing_bsh/targets_ext.py:111-133`): quarantine its survivors; re-target forward (replace with `b_hold` + L1-1) before anything builds on it.
3. L0-5 — keep; the net-new check is a **precondition inside the WI** (drop to a WI-047 #3 variant if not net-new).
4. Meta-label — a fixed product of separately-fitted models is ruled **NOT stacking**; a **permuted-label leakage test is a mandatory DoD item**.
5. Sequencing — **ADR order adopted**: Phase 0 → L0 → L1 → L1.5.
6. fib-primary — **held**.
7. Plan six-vs-seven arithmetic reconciled before ledger registration.
