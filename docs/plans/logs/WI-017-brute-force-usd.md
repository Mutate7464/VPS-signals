# WI-017 — Brute-force target/feature confirmation study (USD)

Admin chat direction 2026-10-31, PM-executed. Charter: `docs/tech_approach/wi017-brute-force-usd/README.md` (spec CONFIRMED).

## EXECUTION LOG

### Run 1 — base targets ×17 windows (delivered `170e1e4`)
- Lookforward peak/bottom, ±10% touch, ±5% stay per window; 593 symbols; base-rate report (admin rule: base rates first). Fwd-window anchoring bug caught by independent recompute, fixed + regression-locked (4 tests).

### Run 2 — derived triple-barrier family (delivered `8c7b7e3`)
- first_touch / days_to_up / days_to_dn / rung / velocity ×17; recompute-verified 0/300 mismatches; 5 regression tests.

### Run 3 — full feature grid (delivered `68f48dd`)
- 264 cols (16 families × 17 windows, hurst w≥12), streaming moment-accumulation corr; 558 high-ρ pairs; matches WI-016 engine on 99 shared cols; found WI-016's hurst_9 all-NaN wart.

### Run 4 — target×feature alignment matrix (2026-11-01, PM-executed)
- Method reuses WI-015 machinery by import (folds_val 20-session embargo, per-date cross-sectional Spearman ≥3 names, 1000-draw block bootstrap seed 42, same-sign vs best E5 factor). Degenerate screen per admin rule: stay5_{63..233} skipped (base rate >99% at long windows).
- First full attempt died in fold-5 assembly: SKHY (78-row short-history symbol) derived parquet carries only windows ≤63 → fixed-column read KeyErrors. Fixed: schema-filtered read + NaN pad for missing target cols; smoke-verified A+SKHY; relaunched clean (attempt1 log archived).
- Result: 20,004/43,560 cells clear the bar (46%) — but the mass is **mechanical alignment, not alpha**: rung/stay5/days_to scale with current vol (atr_pct@34 IC +0.71 on rung_63; stay5 −0.48). WI-015 positives all survive on USD full grid (bb_width_233/range_width_233 162/165, yangzhang_144/atr_pct_233 163/165). Fib-grid beats best-E5 |IC| on 5,757 cells.
- PM-verify: independent recompute of rung_63~atr_pct_34 = 0.7091, n_dates 2957 — exact match vs `run4_alignment.csv`.
- Artifacts: `reports/wi017/run4_alignment.{csv,json,md}`; script `src/wi017/run4_alignment.py`; chain `scripts/wi017_run4_chain.sh`; e5 cache `reports/wi017/e5/` (generated, regenerable in ~15s); run log `logs/wi017_run4.out` (attempt1 archived).

STATUS: RUN 4 DELIVERED — awaiting admin gate (run 5 prune recommendations + decision memo are the next step per charter step 6)