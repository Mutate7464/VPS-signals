# Data Index — what to load for which question (token-optimized)

All files in `reports/fib_swings/`. Load ONLY what the question needs; each row
lists the exact filter/rows to read. Sizes are approximate.

## Reports (read instead of raw data)
| File | Size | Read when |
|---|---|---|
| LEARNINGS.md | 3 KB | First — one-page reconfirmation of all findings |
| SUMMARY.md | 5 KB | Pass 1–2: anatomy + in-sample screens (centered windows) |
| META_SUMMARY.md | 4 KB | Pass 3: 420 meta-feature permutations |
| WF_VALIDATION.md | 3 KB | Pass 4: out-of-time verdicts (trailing windows) |
| IMPROVEMENT_PLAN.md | 4 KB | Prioritized next steps: regime overlay, relabeling, models, features, frozen thresholds, CV practices |

## Data tables (load with filters, not whole)
| File | Rows × Cols | Question it answers | Efficient access |
|---|---|---|---|
| window_summary.csv | 8 × 14 | Magnitude/velocity/frequency by Fib window | read all (1 KB) |
| ticker_swing_metadata.csv | 7,788 × 8 | Per-ticker swing stats (centered) | filter `symbol==X`; 8 windows per ticker |
| rally_grade_priors.csv | 903 × 6 | Per-ticker realistic rally expectations (P(med+), P(strong), median rally) | filter `symbol==X`; or top-N by p_medplus |
| indicator_alignment.csv | 480 × 5 | Raw/panel indicator medians at tops/bottoms + AUC by window | filter `w==39` or `indicator==X` |
| meta_spearman.csv | 2,520 × 5 | 420 meta-features vs fwd15/39/63/102 + y_15d labels | filter `y=='fwd63'`, sort by abs(spearman_mean) |
| meta_target_biserial.csv | 840 × 4 | meta-features vs y_20d_up/down | filter `target==` |
| meta_auc_summary.csv | 1,260 × 5 | meta-feature event AUC at w∈{15,39,63} | filter `w==39`, sort by abs(auc−0.5) |
| screener_hit_rates.csv | 128 × 11 | In-sample threshold hit-rates (flag rate, precision, edge vs base) | filter `side=='bottom'`, sort by edge |
| walkforward_validation.csv | 44 × 10 | Out-of-time + per-year screen performance | read all |
| precision_at10.csv | 2 × 8 | Does ranking flagged bottoms help? | read all |
| _rand_precision.csv | 8 × 2 | Random-baseline precision per window (for lift) | read all |
| trailing_events_w39.csv | 186,729 × 11 | Tradable trailing events + grades + fwd outcomes | ALWAYS filter (symbol, year, or screen flags) before reading |
| events_all.csv.gz | 1.45M × 9 | Centered-window raw events (research only, w-bar lag) | never load whole; filter `w==63` etc. |
| meta_event_values.npz | 2,520 arrays | Raw combo values at events (threshold tuning) | load specific keys `w|side|combo` |
| _ind_store.npz | ~120 arrays | Raw indicator values at pass-1 events | load specific keys |

## Column glossary (non-obvious)
- `pop_low` = max rally off the daily-low bottom within w days (%); `drop_high` = analog from peak.
- `fwd_mfe_pct` / `fwd_mae_pct` = max favorable/adverse excursion of close over next 39 days.
- `grade` = rally tercile: weak <19.5 ≤ med <33.9 ≤ strong (% MFE, w=39 fixed).
- `screen_bottom` = rsi_f63<42 & rsi_f15−rsi_f39<−8; `screen_top` = mirror (rsi_f63>58, spread>+7).
- `auc_top_vs_bottom` = P(indicator higher at tops than bottoms); 0.5 = no separation.

## Known data caveats (do not re-derive)
- Symbol extraction: raw files are `symbol=<T>.parquet` — strip prefix or joins come back empty.
- ~157/977 tickers lack feature/target rows (stale feature panel) — check n_tickers columns.
- Centered-window numbers (SUMMARY.md, events_all) carry a w-bar confirmation lag;
  trailing-window numbers (WF_VALIDATION.md, trailing_events_w39.csv) are tradable.
- Both markets pooled everywhere; no CAD/USD split run yet.
