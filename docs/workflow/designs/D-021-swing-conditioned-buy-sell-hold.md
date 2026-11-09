# D-021 — Swing-Conditioned Buy/Sell/Hold ML (3-Class)

**Goal:** G-001 (dual-market screener) · **Status:** drafted (admin direction in chat, 2026-11-09: "draft and proceed") · **Date:** 2026-11-09

## Context

- **Sprint-4 XGBoost (fixed 15/20d targets) failed Gate 4 on all 8 target×market combos** (`reports/sprint4_model_qa.md`): P@K lift 1.03–1.19 vs bar 1.5, BSS ≈ 0, IC ≈ 0. Placebos clean → labels/horizon are the bottleneck, not overfitting. Contrastive ranking also closed negative (WI-009 series).
- **The only live structure is swing-state conditioned**: WI-027 regime labels PASS (up_high/USD +22.75pp, chop_normal/ALL +3.89pp); WI-028 recommends at-bottom entry; WI-016 triple-barrier + meta-labeler ACCEPT (CAD, 133 TRADE / 15 NO_TRADE behind human gate); WI-030 frozen exit `t15_s10_d39_close` beats learned exits.
- **Admin direction (chat, 2026-11-09):** buy/sell/hold ML using peak/bottom detection, volatility, momentum, and other meta parameters on ticker data.
- **Gating regime (PM cycle 27):** ADOPT_LOOSE_4OF5 — learned artifacts beat baseline in ≥4/5 folds (synthetic-validated WI-031).

## Options considered

| Option | What | Verdict |
|---|---|---|
| A — Retrain sprint-4 XGB on all dates, 3-class | Replace binary targets with {buy,hold,sell} on same fixed horizons | Reject: same panel, same labels — Gate 4 failure predicts repeat |
| B — 3-class on swing-anchored events only | Train only at swing events (at-bottom/at-top from the fib swing detector), label = first-touch outcome | **Choose** — aligns with WI-028 at-bottom finding; concentrates model capacity where structure exists |
| C — Learned exit policy on top | Replace frozen `t15_s10_d39_close` | Defer — WI-030 just FAILED this; frozen exit is the baseline, not the model's job |

## Decision

1. **Events, not all dates:** training rows = fib-swing detection events (at-bottom, at-top) per ticker; all other dates are HOLD by construction and excluded from fitting (address class imbalance at the source, not via `scale_pos_weight`).
2. **Labels (3-class, first-touch):** from event date, side implied by swing state (at-bottom → long candidate, at-top → short/exit candidate): BUY = profit barrier `+k·ATR` touched before stop within vertical barrier; SELL = stop touched first; HOLD = vertical-barrier touch (fib {21,55} only — WI-030 showed t15..t39 family is where the edge lives; no 233 blowup). Neutral/vertical outcome → HOLD.
3. **Features (whitelist, existing families):** peak/bottom proximity (fib ladder distances, donchian position), volatility (atr_pct, yangzhang, bb_width at admitted windows), momentum (ts-momentum set from WI-011/012), meta parameters (WI-027 regime label, label-density / liquidity covariates from WI-016). Same uniqueness stage as D-016 §2 (|Spearman ρ|>0.7 cluster prune, ≥500 events/feature).
4. **Model + baseline:** `XGBClassifier(objective="multi:softprob", n_jobs=2)` inside the existing purged walk-forward harness (`embargo_td = max(20, horizon)`); **baseline = frozen fib rules** (WI-028 entry + WI-030 exit), not raw direction. Gate = ADOPT_LOOSE_4OF5 vs baseline + CB-05 placebo.
5. **Probe-first:** within-date rank-IC of features vs first-touch outcomes, BH-FDR, 5-seed placebo — no model spend until probe clears (D-016 §3 pattern).
6. **Output:** filtered shortlist into the WI-014 artifact stream behind the human gate; daily shortlist only, no auto-execution.

## Consequences

- Concentrates fitting on ~swing-event density (WI-016 label-density tables give the measured counts); risk: too few events → probe aborts cheaply.
- HOLD-by-construction outside events means the model never has to learn "do nothing on day N" — the fixed-horizon failure mode.
- 2 vertical barriers × 2 swing states × 2 markets = bounded grid; k ∈ {1.5, 2.0} carried from D-016.
- Constraints: n_jobs=2, float32, symbol-sequential, checkpointed; heavy runs get a core-hour cap in the WI spec.

## Open questions (answered by probe, not by admin)

- Event density per market (label-density CSVs suggest CAD is denser → dry-run market = CAD).
- Whether at-top events carry enough downside structure (WI-027 found it in up_high only) — probe gates at-top out if empty.
