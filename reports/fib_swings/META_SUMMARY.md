# Meta-Feature Permutations: Cross-Window & Cross-Family Alignment Results

Run: 2026-11-06 (pass 3) · 420 meta-features = 252 within-family cross-window
(ratio / short−long / long−short for rsi_f, bbw_f, atrp_f over 3–102 bars) +
48 cross-family same-window (rsi↔bbw↔atrp) + 120 panel cross-window
(adx, kama_er, obv_zscore, vwap_zscore over 5–100).
Targets: fwd close-to-close returns {15,39,63,102d}; repo labels y_15d_high/low,
y_20d_up/down; swing-event AUC at w∈{15,39,63}. Per-ticker rank correlations
averaged over 820–977 tickers, both markets pooled.

## Headline findings

1. **The strongest meta-feature family is RSI/ATR% ratio (cross-family, same window):
   `rsi_f63/atrp_f63`, `rsi_f102/atrp_f102`, `rsi_f39/atrp_f39`.**
   - vs fwd returns: Spearman −0.088…−0.090 (strongest of all 420; matches the best raw
     feature atrp_f102 ≈ +0.095 but with a cleaner, scale-free formulation). Sign:
     momentum high relative to volatility → forward **mean reversion**.
   - vs y_15d_high (touch +5% in 15d): **+0.065…+0.075 positive** — the same combo
     predicts both-direction excursions. It is a *volatility-regime* feature, not a
     direction feature: high RSI/ATR = touch probability up, expected drift down.

2. **RSI term-structure difference (`rsi_f15−rsi_f39`, `rsi_f24−rsi_f39`) is the best
   turn detector that is not mechanically confounded:** event AUC 0.986–0.987 at
   w=39/63 (fast RSI minus slow RSI ≈ +7 to +9.5 at tops, −8 to −11 at bottoms).
   Its forward-return correlation is modest (|ρ|≈0.03), so it locates turns but does
   not itself predict drift — pair it with a drift/velocity feature.

3. **BB-width term-structure ratio (`bbw_f3/bbw_f39`, `bbw_f3/bbw_f102`) is the top
   y_20d_up signal** (biserial +0.049…+0.051): short-window volatility expanded
   relative to long-window (vol breakout / compression release) → higher P(20d up-move
   label). Absent from any single-window feature; this is a genuinely new screener axis.

4. **Panel families contribute little beyond VWAP-z term structure**: best is
   `vwap_zscore_5−vwap_zscore_100` vs fwd63 (ρ≈+0.040, mean-reversion of the z gap).
   ADX and KAMA cross-window combos were all |ρ|<0.03. OBV-z combos negligible.

5. **Ratios vs differences:** for RSI (bounded scale) diffs and ratios carry the same
   info (mirror pairs); for BB-width/ATR% (unbounded, per-ticker scale) **ratios are the
   right operator** — they dominate diffs on every target. Cross-family division is only
   meaningful for RSI/ATR and RSI/BBW; ATR/BBW adds nothing over raw ATR%.

## Practical screener meta-parameters (in-sample, upper bounds)

- **Bottom candidates (buy-side):** `rsi_f63/atrp_f63` in its low tail (momentum weak vs
  vol) AND `rsi_f15−rsi_f39` < −8 (fast RSI collapsing below slow) — combine with the
  pass-2 result (rsi_f63 < ~42 gave 3.7× lift, +0.77pp edge) for a two-factor screen.
- **Breakout/continuation candidates:** `bbw_f3/bbw_f39` in its high tail (short vol
  >> long vol) → elevated P(y_20d_up), i.e., feed the shortlist ranking.
- **Avoid/exhaustion:** `rsi_f15−rsi_f39` > +7 while `rsi_f63/atrp_f63` rich (momentum
  stretched vs vol) → matches the top-screen flag from pass 2.

## Files

- `meta_spearman.csv` — 420 combos × 6 targets (fwd15/39/63/102, y_15d_high/low)
- `meta_target_biserial.csv` — 420 combos × y_20d_up/down
- `meta_auc_summary.csv` — 420 combos × 3 event windows (AUC + medians at tops/bottoms)
- `meta_event_values.npz` — raw combo values at every event (for future threshold tuning)

## Data-quality notes / deviations

- Raw files are named `symbol=<T>.parquet`; pass-1/2 used the full stem as the symbol key,
  so **panel-indicator joins were silently empty in passes 1–2** (fib-family results were
  unaffected — computed from raw OHLCV). Fixed in pass 3; ~157/977 tickers still lack
  feature/target rows (excluded via NaN-safe accumulation, visible as n_tickers=820 vs 977).
- All results in-sample (full history, both markets pooled); walk-forward validation is
  the required next gate before any of this feeds the live shortlist.
