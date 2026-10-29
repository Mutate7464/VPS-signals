# D-016 — Triple-Barrier Fib-Ladder Labeling + Meta-Labeled E5 Screener

**Goal:** G-001 (dual-market screener) · **Status:** proposed (awaiting admin definition gate) · **Date:** 2026-10-29

## Context

- **Labels are the proven bottleneck, not features.** WI-009b/009c/012/011 (all gated negatives): XGB on the 89-feature pool adds nothing at the current label definitions; "the E5 factors themselves are the signal."
- **WI-015 (first positive alignment):** long-horizon vol/range features align with band targets — CAD `bb_width@233`/`range_width@233` (T1–T2), `amihud@89` (T3); USD `yangzhang@144`, `atr_pct@233`. The current feature pool's fib windows top out at 102 — the aligned family is *out of pool*.
- **Live data probe (2026-10-29):** `data/raw_ohlcv/market=USD/` = 608 parquet, `market=CAD/` = 378; cols `date, open, high, low, close, volume, average, barCount`; per-ticker coverage varies (sampled file: USD 5,030 rows 2006→2026-10-28; CAD 1,299 rows 2021→2026-10-28). `features_CAD.parquet` = 701,599 × 92 (90 feature cols, 315 symbols).
- **Admin direction (chat, 2026-10-29):** extend target horizons along the fib ladder 3→233; re-evaluate features seeded with fib windows; add trading models that distill targets+features into actions; adopt (1) triple-barrier re-spec / drop R² gate, (2) admit long-horizon fib features, (5) meta-labeling on E5 as the model's job.
- **Method grounding:** López de Prado AFML ch. 3 — fixed-horizon labels describe a path you would have been stopped out of; triple-barrier labels the *first-touch* outcome of a vol-scaled trade; meta-labeling separates side (primary) from bet/size (secondary), converting a high-recall low-precision primary into a tradeable filter. Trend-scanning (t-sign over a horizon band) is a fallback for direction labels. Fixed-horizon acknowledgment: the label omits intra-horizon path — acceptable for screening, not execution.

## Options considered

| Option | What | Verdict |
|---|---|---|
| A — Full fib ladder | 13 horizons × 5 current-style labels ≈ 65 targets | Reject: pure multiple-testing blowup; the WI-009 series shows label *quality* gates, more labels ≠ more signal |
| B — Triple-barrier, fib vertical barriers | Barriers k·ATR, vertical ∈ fib ladder; **replaces** current 5 labels as primary | **Choose** — one coherent label spec that *is* the trade, covers 3→233 span |
| C — Continuous targets | Predict fwd ATR-normalized return directly | Keep as secondary evidence (rank-IC probe metric); regression adds no screening action |
| D — Features-only | Admit @144/@233 fib features, keep current labels | Reject alone: labels stay the bottleneck; but feature admission is part of the decision |

## Decision

1. **Labels (replaces `y_15d_high/low`, `y_20d_up/down/stay` as primary):** per event (ticker, date):
   - profit barrier `+k·ATR_t`, stop `−k·ATR_t`, symmetric k ∈ {1.5, 2.0} (side unknown at label time);
   - vertical barrier = fib ladder **{8, 21, 55, 144, 233}** (curated, not full 13 — see open Q1);
   - label = which barrier touched first; vertical-barrier win → sign of realized return (or neutral — Q3);
   - "stay" is no longer a separate target: it is the vertical-barrier/neutral outcome.
   - Legacy 5 labels retire to legacy-baseline (rebuildable), not deleted (Q2 confirms).
2. **Features (confirmed admin 2026-10-29):** extend range/vol fib windows to 233 (seed grid = fib sequence ≤ 233 × existing families: bb_width, atr_pct, amihud, yangzhang, range_pos/width/compression, donchian_break); **looser admission** (relaxed MI percentile, VIF 5.0→8.0) — **plus explicit uniqueness stage**: within per-target whitelist, cluster by |Spearman ρ|>0.7, keep one representative per cluster (highest same-sign IC), cap by events-per-feature (≥500 labeled events). Measured basis (2026-10-29 live read): USD 32-feat whitelist mean pairwise |ρ| 0.11 but 14 redundant pairs (amihud_* windows 0.95–0.99); CAD 42-feat mean 0.18, 68 pairs > 0.7 (bb_width×yangzhang×range_width family) → effective unique count ~25–30. Longer training / looser criteria acceptable because probe gate (same-sign bar, BH-FDR) does the real filtering.
3. **Probe-first gate (no model spend until cleared):** per-horizon within-date rank-IC of features + E5 vs barrier outcomes; Benjamini–Hochberg FDR across the target×feature grid; 5-seed placebo; same-sign clause bar (WI-009b re-spec). Cost overlay applied at probe stage (WI-011: NO_TRADE default, ~200 trades/yr ≈ 1 action/day).
4. **Model:** meta-labeling on E5 primary — primary = E5 top-decile rank at the cleared horizon defines events/side; XGB (existing trainer machinery) predicts bet P&L>0; output filters/sizes the shortlist.
5. **Actions (decision-rule synthesis):** cleared signal → entry (rank decile), exit (barrier touch / time stop), size (meta-prob), abstain (NO_TRADE default) — evaluated under the cost overlay and emitted into the existing WI-014 shortlist artifact the human gate consumes.
6. **Precondition fix:** `PurgedWalkForwardSplit` gains per-target `embargo_td = max(20, horizon)` — 20 is insufficient at h≥55 and leaks across folds.

## Consequences

- **Positive:** labels describe tradeable outcomes; horizon span 3→233 covered in one spec; feature admission is WI-015-evidenced; multiple-testing controlled by curated ladder + BH-FDR + probe gating; actions path closes end-to-end into the existing shortlist+human-gate pipeline.
- **Negative / risks:** long-horizon overlap (233-bar windows ≈ 10 non-overlapping per ticker → overlap-inflated t-stats; mitigate with date-sparse evaluation or block bootstrap, registered in RISKS.md); probe grid still ~5 horizons × ~40 whitelist features × 2 markets — bounded but real; ~65-target blowup avoided by curation only if Q1 answered "curated".
- **Constraints carried:** n_jobs=2, float32, symbol-sequential (2 vCPU/8 GB), market parametrization (`--market`), point-in-time trailing-only features, daily shortlist + human gate, no auto-execution.

## Open definition questions (admin gate)

| # | Question | REC |
|---|---|---|
| 1 | Fib ladder: full 13 horizons {3,5,8,13,21,34,55,89,144,233…} vs curated {8,21,55,144,233}? | **Curated** — span with ~40% of the test count; add 89 if probe budget allows |
| 2 | Old 5 labels: retire-as-legacy-baseline (rebuildable) vs delete? | **Retire as legacy baseline** — one comparative probe run (old vs new labels) is cheap insurance |
| 3 | Vertical-barrier outcome: sign-of-return 3-class vs neutral binary? | **Sign-of-return** — keeps label informative at 8–21d; neutral collapses too much |
| 4 | k (ATR multiple): both {1.5, 2.0} as grid, or fix 2.0 (matches current TREND_ATR_MULT)? | **Both in probe, one ships** — pick per horizon by cleared-bar density |
| 5 | E5 primary event: top-decile rank (per market, per date) as entry event? | **Yes** — matches WI-014 shortlist semantics |