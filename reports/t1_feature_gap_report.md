# WI-047 — T1 feature/TA gap research: inventory, missing-family scan, ranked extension proposals

- Generated (UTC): 2026-11-10 · Agent: surgical-builder (D-025 §2, Tier 1)
- **License (D-023 §2, L1):** inventory + attribution + proposal list only. No model, no
  threshold, no trading claim; **nothing in §4/§5 is an adopted feature** — adoption needs its
  own grid WI, the L1 gate, and admin ratification (provisional-verdict rule).
- Evidence base: `src/swing_bsh/feature_inventory.py` (programmatic parse of
  `src/swing_bsh/binary_features_ext.py`, re-runnable when the panel grows) + WI-040
  winner-cell OOF permutation attribution (`reports/wi040_calibration.md`, cell
  `exact_full_k0.8` / `b_hold` / xgboost / h13, USD + CAD).

## 1. Inventory (programmatic, current panel)

Reproduce: `uv run python -m src.swing_bsh.feature_inventory` (exit 0 smoke) or
`uv run pytest tests/test_feature_inventory.py -q`.

- **249 panel columns, 249 classified, coverage 1.000** (WI bar ≥ 0.95); 0 unclaimed columns.
- Blocks (parsed from source, not hand-listed): WI-016 grid 111 · cross-sectional ranks 102 ·
  sector one-hots/ranks 18 · raw-ext (volume/VWAP/barCount) 6 · keys 5 · event-quality 3 ·
  calendar 2 · breadth 2.

| family | cols | aligned | best USD drop | best CAD drop | representative columns | attribution evidence (WI-040) |
| --- | --- | --- | --- | --- | --- | --- |
| cross_sectional | 102 | 2 | 0.0292 | 0.0001 | `cs_adx_3`, `cs_entropy_102` | top-1 USD `cs_entropy_102` (+0.0292); CAD `cs_di_spread_144` 0.0001 |
| volatility | 27 | 2 | 0.0094 | 0.0469 | `atr_pct_*`, `bb_width_*`, `yangzhang_*`, `range_compression_8_55` | `atr_pct_3` 0.0094 USD / **0.0469 CAD (rank 1 both)**; `range_compression_8_55` 0.0106 CAD |
| momentum | 26 | 5 | 0.0050 | 0.0163 | `adx_*`, `di_spread_*`, `macd_norm_*`, `donchian_break_*`, `fib_dist_*` | `adx_144` 0.0050 USD; `di_spread_3` 0.0163 CAD; `adx_21` both markets |
| volume_liquidity | 26 | **0** | — | — | `volume_z_*`, `obv_zscore_*`, `amihud_*`, `vwap_dist`, `bar_count_*` | no volume/liquidity column in either top-20 → **family carries ~0 evidence** |
| entropy_fractal | 21 | 6 | 0.0130 | 0.0059 | `entropy_*`, `hurst_*`, `kama_er_*`, `frac_diff_close` | `entropy_24` 0.0130, `hurst_15/39`, `kama_er_15`, `entropy_39` CAD |
| sector | 18 | **0** | — | — | `sec_<sector>`, `srel_{adx_21,di_spread_21,atr_pct_21,bb_pct_b_21,range_pos_21,rsi_14}` | all `sec_*` at 0.0000 (AUC drop) in both markets |
| mean_reversion | 17 | **0** | — | — | `rsi_14`, `rsi_14_slope_5`, `bb_pct_b_*`, `range_pos_*`, `kalman_spread_atr` | absent from both top-20 |
| keys | 5 | 0 | — | — | `symbol`, `date`, `state`, `close`, `atr` | `state_is_bottom` 0.0001 USD (identity column, not a feature family) |
| event_quality | 3 | 1 | — | 0.0002 | `swing_depth_atr`, `bars_since_opp`, `dd_age` | `swing_depth_atr` 0.0002 CAD; `bars_since_opp` TreeSHAP-listed in WI-042 join |
| calendar | 2 | 2 | 0.0017 | — | `dow`, `month` | `month` 0.0017 USD, `dow` 0.0001 USD |
| breadth | 2 | 0 | — | — | `breadth_bottom`, `breadth_top` | absent from both top-20 |

## 2. What today's signal actually rests on

18 of 249 columns carry measurable permutation evidence, concentrated in **three** families:
`entropy_fractal` (6), `momentum` (5), `volatility`/`cross_sectional`/`calendar` (2 each), plus one
`event_quality` column. The three largest blocks by column count — cross-sectional ranks (102),
volume/liquidity (26), sector (18) — contribute 2, **0**, **0** aligned columns respectively.

Reading for the gap scan: the aligned axis is *path-shape and range scaling at the detection bar*
(entropy/Hurst/kama efficiency, ATR% level, ADX/DI direction), i.e. **"is this bar a stretched,
low-efficiency extreme in a market-wide stretched regime?"**. Everything that would answer *how
much further the move can run* (volatility forecast horizon), *who else is in the trade*
(volume/liquidity), or *what the rest of the market is doing* (market-level context) is either
absent or unaligned. That is the target of §4.

## 3. Gap analysis — families missing or weak (≥3 required)

**G1 — Realized-volatility forecasters (family present in name only).** The panel has one range
estimator (`yangzhang_*`, 6 windows) plus `atr_pct_*`/`bb_width_*`. Yang-Zhang is absent from both
top-20s while its sibling `atr_pct_3` is rank 1 in CAD and rank 3 in USD: the *scaling* family is
aligned, the *forecasting* family is essentially undeveloped. Nothing in the panel expresses a
vol term structure (short vs long RV) or vol-of-vol, i.e. no forecast *direction*. Canonical
estimators/lineage: Parkinson (1980), Garman-Klass (1980), Rogers-Satchell (1991), Yang-Zhang
(2000), Andersen-Bollerslev (1998) realized variance, Corsi (2009) HAR-RV, CBOE VIX methodology.

**G2 — Volume/liquidity profile (26 columns, 0 aligned).** Present proxies are all
*self-referential* (volume z-score/trend, OBV z-score, `amihud_*` level, `bar_count_*`), none
*relative to the cross-section* or *in changes*. Missing: dollar-volume percentile, Amihud
percentile/Δ, turnover velocity, volume-clock, Kyle-lambda/spread proxies. Lineage: Amihud (2002),
Kyle (1985), Easley et al. VPIN (2012).

**G3 — Seasonality beyond month/dow (2 columns, both weakly aligned).** `dow` 0.0001 and `month`
0.0017 are the *only* calendar features, and both are high-cardinality-low-information dummies.
Missing: turn-of-month window, half-month, pre-/post-holiday, OpEx week, FOMC-day. Lineage:
Ariel (1987) / Lakonishok-Smidt turn-of-month, French (1980) weekend/holiday, Lucca-Moench (2015)
pre-FOMC drift. The two existing dummies do carry (small) evidence, which is why this family is
ranked as a *strengthen* rather than a pure fill.

**G4 — Cross-asset / market-level context (absent).** `sec_*`/`srel_*` (18 columns) are
same-date sector encodings with 0.0000 drop, and `breadth_*` is two static ratios — no
market-residual momentum, no rolling beta/correlation to a market proxy, no breadth *change*. The
existing panel has no notion of "the index did X while this symbol did Y". Lineage:
market-model residuals (Sharpe 1964 lineage), Asness et al. cross-sectional momentum,
sector-relative strength practice.

**G5 — Regime meta-features (raw level only, no percentiles).** `bb_width_21` exists as a raw
width and as a same-date cross-section rank, but there is no *time-series percentile* ("is today's
width in the top decile of the last N bars?"), no ATR%-percentile, no entropy/Hurst regime
percentile, no ATR-based VIX proxy. Given that the aligned families are exactly ATR%/entropy/Hurst,
this gap is the cheapest route to *strengthening* (not just filling). Lineage: Bollinger
band-width squeeze regime practice, Bollen-Whaley (2004) IV/BBW relation, VIX methodology.

**G6 — Options-implied features (blocked, no data).** Implied vol, put/call skew, IV term
slope are the natural "expected move" complement to G1, but no options chain is ingested and this
WI forbids new ingestion → recorded as out of scope, not proposed.

## 4. Ranked proposals

Ranking rule (as commissioned): **(i) fills a missing family > (ii) strengthens an already
aligned family (entropy/Hurst/ATR%) > (iii) computable from already-ingested OHLCV (no new
ingestion)**. `C` = criterion satisfied. All formulas use only `open/high/low/close/volume` at
bars ≤ t (causal; features are read at the detection bar), all outputs float32, windows from the
existing ladder (3/8/21/55/144/233; 9/15/24/39/63/102).

| # | proposal | family | formula (per bar, trailing window `w`) | data | C |
| --- | --- | --- | --- | --- | --- |
| 1 | `rv_parkinson_{w}` + 233-window percentile | volatility | `σ_P = sqrt( mean_w [ ln(H/L)² / (4 ln2) ] )`; then `rank_pct` over 233 | H,L | i,ii,iii |
| 2 | `atr_pct_pctile_{21,233}`, `bb_width_pctile_21` | volatility (regime) | rolling percentile of `atr_pct_21` and `bb_width_21` within a 233-bar window | C,H,L | ii,iii |
| 3 | `entropy_pctile_{39}`, `hurst_pctile_{39}` | entropy_fractal (regime) | rolling percentile of `entropy_39` / `hurst_39` over 233 bars | C,H,L | ii,iii |
| 4 | `rv_gk_{w}`, `rv_rs_{w}`, ratios | volatility | `σ²_GK = 0.5 ln(H/L)² − (2ln2−1) ln(C/O)²`; `RS = ln(H/C)ln(H/O) + ln(L/C)ln(L/O)`; `ratio = σ_GK/σ_P` | O,H,L,C | i,iii |
| 5 | `rv_har_{1,5,22}`, `rv_ratio_5_22` | volatility forecast | RV from `σ_GK²` aggregated over 1/5/22 bars; `RV_5/RV_22` (term-structure slope) | O,H,L,C | i,iii |
| 6 | `mkt_resid_mom_{w}`, `beta_mkt_{w}`, `corr_mkt_{w}` | cross-asset | `ret_i,w − ret_mkt,w` with `ret_mkt` = same-date cross-sectional mean return of the ingested universe (breadth machinery, no index series needed); rolling covariance/variance for β | panel (all symbols) | i,iii |
| 7 | `breadth_divergence_{w}`, `breadth_chg_{w}` | breadth / cross-asset | `breadth_top − breadth_bottom` and its `w`-bar change (derivative of the existing 2 raw columns) | panel | i,iii |
| 8 | `dv_pctile_21`, `amihud_pctile_21`, `amihud_delta_21` | volume_liquidity | same-date cross-sectional percentile of `log(close×volume)`; percentile + change of `amihud_21` | C,V | i,iii |
| 9 | `tom_dummy`, `half_month`, `pre_holiday`, `post_holiday` | calendar (seasonality) | turn-of-month = last 2 / first 3 trading days of month; half-month dummy; holiday = gap-to-previous-bar > 3 calendar days on a weekday | date index | i,iii |
| 10 | `fomc_day`, `pre_fomc` | calendar (event) | dummy around scheduled FOMC decisions | **external calendar** (static table) | i, **new data** |
| 11 | `turnover_velocity_{w}` | volume_liquidity | `volume / shares_outstanding` | **shares outstanding** not ingested | i, **new data** |
| 12 | implied-vol / skew features | options-implied | IV term slope, 25Δ skew | **no options chain** | − (G6) |

Notes on honesty of the ranking:

- #1–#3 are ranked above the "missing family" fills (#4, #6, #8) because criterion (ii) outranks a
  fill and because the evidence base *already points at them*: `atr_pct_3` is the single
  strongest CAD feature and the entropy/Hurst block is the strongest USD block. A regime
  percentile is a monotone transform of an aligned feature — it cannot manufacture new signal, but
  it converts a level (whose meaning drifts with the vol regime) into a regime-relative position,
  which is exactly the conditioning axis on which the winner cells were selected (`k=0.8` cell
  beat `k=1.0`).
- #4/#5 (Parkinson/GK/RS + HAR slope) fill the genuinely missing *forecast-shaped* subfamily and
  are pure OHLCV. #5 is included but flagged: HAR components are strongly collinear with the
  existing `atr_pct_*` ladder, so it must be tested as its own BH-FDR family and dropped if the
  AUC drop is absorbed by `atr_pct_3`.
- #6 uses the cross-sectional mean of the *ingested* universe as the market proxy — an honest
  approximation (equal-weighted, survivorship of the current universe), not a true index. No new
  ingestion; a real index series would be a separate data-adoption decision.
- #9's holiday rule is derivable from the existing date index (gap length), so it needs no
  calendar file; #10 does need one FOMC table, hence "new data" and excluded from the shortlist.
- #11 and #12 are recorded to close the checklist, not proposed: both violate criteria (iii).

## 5. Shortlist for the next feature-grid WI

Ordered, one BH-FDR family each; all computable from the current ingestion, all ≤ ~10 new columns:

1. **Regime percentiles** (#2, #3): `atr_pct_pctile_233`, `bb_width_pctile_233`,
   `entropy_pctile_233`, `hurst_pctile_233`. Cheapest, directly strengthens the three aligned
   families; risk = collinearity with the raw levels.
2. **Parkinson + GK/RS + ratio** (#1, #4): 6 windows × (level, percentile) plus estimator ratios.
   Fills G1 with a genuinely different estimator geometry (range vs open-gap vs close-path).
3. **Market-residual context** (#6, #7): `mkt_resid_mom_21/55`, `beta_mkt_55`, `corr_mkt_55`,
   `breadth_divergence_21`. Fills G4 and the single largest unaligned block (cross-sectional
   ranks / breadth) — note the market proxy caveat.
4. **Dollar-volume & Amihud percentiles** (#8): fills G2, the only 26-column family with zero
   evidence; also the most likely to fix the CAD/USD asymmetry if the signal is liquidity-driven.
5. **Seasonality dummies** (#9): fills G3 at near-zero cost; expect small effects (`month` 0.0017
   / `dow` 0.0001 set the prior) — run last and only with its own FDR family.

Explicitly **held / blocked**: HAR term structure (#5; collinearity — test only if 1–4 leave
budget), FOMC dummies (#10; needs an external calendar = new data), turnover velocity (#11; needs
shares outstanding), options-implied (#12; no chain ingested).

Carry-forward guardrails for whoever runs the grid: one BH-FDR family per axis, purged/embargoed
CV, CALIB-only selection later, float32 immediately, symbol-sequential `pyarrow.dataset` reads,
`n_jobs=2`, core-hour cap declared in the WI, and a fresh WI-040-style attribution run afterwards
to check whether the new columns absorb the entropy/ATR% drop or add to it. The Layer-1 verdict
stays PROVISIONAL until the admin ratifies it.
