# G2 proposal — WI-084 L2-TB engine: new prereg + new split (drafted for admin ratification 2026-11-19)

**REC (BLUF):** dispatch the WI-084 engine BUILD now (machinery; touches no EVAL data);
hold the one-shot L2-TB EVAL burn until the virgin window has grown — refresh ingest
~end of Dec 2026, then freeze the prereg and burn. Draft prereg below, frozen at burn time.

## Situation
WI-084 (gap-aware triple-barrier engine, L2) is G2-gated: the D-027 EVAL split
(2022-07-01 → 2026-08-20 USD / 2026-08-19 CAD; evidence `data/models/l2_time_exit_eval/`,
family `l2_rebuild_eval_2026_11_16`) is SPENT. Standing ruling: any future L2 EVAL needs
a NEW prereg + NEW split (board, D-027 closure). Admin approved drafting the proposal 2026-11-19.

## Complication
Data ends 2026-09-23 (USD) / 2026-09-22 (CAD). The virgin post-burn window is therefore
only 2026-08-21 → 2026-09-23 ≈ 24 trading days → at the D-027 EVAL entry rate
(~4,800/yr USD, ~2,600/yr CAD) ≈ **~500 USD / ~240 CAD entries**. A 4-fold fold-ceiling
check on ~120/60-entry folds is statistically thin. Waiting grows the window (~+2 months
of virgin data by end of Dec 2026 → ~2.5× the pool).

## Draft prereg (to be frozen + hashed BEFORE any EVAL read; pre-burn amendments legitimate, post-burn never)
- **Entries:** fib-baseline swing events (same entry rule as D-027), unsized, one entry
  per event; entry artifacts materialized to NEW paths under `data/models/l2_tb_eval/`.
- **Constructions (candidate set):** `tb_s10`, `tb_s15`, `tb_s20` — triple-barrier exits with
  profit barrier +10% or k_tp·sigma_pre, stop k_sl·sigma_pre at the named σ profile
  (1.0/1.5/2.0), gap-aware stop fill at bar open (GAP_SL), T1 milestone (+5%/1.5σ),
  trailing ATR R-stop, SPY/XIU benchmark excess, forced TIMEOUT=0. Decision params
  (k_tp, k_sl within the profile, trail length) tuned on CALIB ONLY.
- **Baseline (paired):** frozen `fixed_h55` unsized (the ratified L2 overlay exit rule).
  Statistic = paired per-row delta net edge (arm − baseline), same cost model (25 bps).
- **Placebo:** 5-seed sign-flip on the paired per-row differences (paired recipe; never
  split-level flips), reported alongside observed net edge.
- **FDR family:** constructions × markets (m = 6), BH α = 0.05, full family never per-construction.
- **Materiality floor:** 10 bps net (D-027 §11); floor 25 bps cost model unchanged.
- **Verdict:** computed ADOPT requires FDR-pass + floor + fold ceiling; all labels PROVISIONAL
  until admin ratification (AGENTS provisional-verdict rule). No live trading; research shortlist only.
- **Fold leg (proposed change vs D-027):** 4 date-block folds at deterministic quantiles of
  entry dates (the D-027 2-fold partition knife-edged the ≤50% max-share rule at 0.533/0.597
  with both folds strongly positive — WI-071-EVAL). 4 blocks reduce the coarse-grid false REJECT risk.

## Numbered ratification asks (answer all in one line each)
1. **Split choice — (b) recommended:** virgin window = 2026-08-21 → data end, but BURN
   DEFERRED until ingest refresh (~end of Dec 2026) grows the pool; WI-084 build dispatched
   now. Alternative (a): burn now on the 24-trading-day window (thin); (c) re-partition the
   burned 2022-07→2026-08 history for the new family — DISFAVORED (reuses burned performance
   data; selection-bias risk; contradicts the standing G2 ruling).
2. **Candidate set:** ratify the 3-construction family `tb_s10/s15/s20` (each extra variant
   widens the FDR family).
3. **Fold leg:** ratify 4 date-block folds replacing the 2-fold partition.
4. **Decision rule:** ratify paired delta net edge vs frozen fixed_h55 + 5-seed paired
   sign-flip placebo + 10 bps floor + BH-FDR α=0.05 (m=6).

## If you reject
- Rejecting the deferred burn keeps (a): a thin-window verdict that risks an INCONCLUSIVE
  (underpowered folds) — an EVAL read on ~500 entries is a one-way door spent on weak evidence.
- Rejecting WI-084 build dispatch keeps the engine unbuilt; CALIB tuning and the burn stay
  blocked on machinery regardless of window size.
