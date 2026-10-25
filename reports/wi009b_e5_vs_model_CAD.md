# WI-009b — contrastive ranker vs E5 factor baseline (CAD)

- Generated (UTC): 2026-10-25T04:58:12.682512+00:00
- Dataset: `CAD` feature panel, 671,440 rows · 89 float32 features · 313 symbols
- Validation window: **60 held-out dates** (2026-06-26 → 2026-09-22), purged chronological split, 20td purge gap
- Identical rows and dates for the model and every factor (same-row harness: `src/models/pair_sampler.within_date_rank_ic`).
- Training: 2585 dates (2016-02-09 → 2026-05-28), 9 epochs, early-stopped (patience 4), 1.4 min wall clock, selected epoch 5
- Metric: score-based within-date Spearman rank-IC vs `fwd_atr_ret_15` (never class-label IC).

## Model vs the five E5 factors — same val rows, same val dates

| Ranker | mean IC | \|IC\| | t | dates |
| :--- | ---: | ---: | ---: | ---: |
| **contrastive ranker (selected epoch 5)** | -0.1478 | +0.1478 | -6.0289 | 60 |
| `e5_vol_20` (factor) | +0.1274 | 0.1274 | +3.48 | 60 |
| `e5_mom_12_1` (factor) | +0.0677 | 0.0677 | +3.13 | 60 |
| `e5_rev_1m` (factor) | -0.0555 | 0.0555 | -1.82 | 60 |
| `e5_amihud_20` (factor) | +0.0546 | 0.0546 | +4.08 | 60 |
| `e5_log_dollar_vol_20` (factor) | -0.0242 | 0.0242 | -3.04 | 60 |

## Verdict against the skill bar

- **Clause (a)** — model beats the best single factor on the same dates: **PASS** (model |IC| +0.1478 vs `e5_vol_20` |IC| +0.1274, margin +0.0204)
- **Clause (b)** — |t| > 2.0 with stable sign in >= 2 disjoint sub-windows: **PASS** (model t -6.0289, 2 sub-windows, same sign in all: True, |t|>2 in all: True)
- **SKILL BAR: PASS (with caveats — see below)**

**Caveats — read before acting on the verdict:**

- SIGN INVERTED — the model's val IC has the opposite sign to the best factor (-0.1478 vs `vol_20` +0.1274). Clause (a) is a |IC| comparison, so it is met in MAGNITUDE only: the model is anti-correlated with forward returns on this window, and a sign flip (which would make the sign positive) is not claimed here because it would be chosen on this same window.

Final epoch (9) scored IC -0.1009 (t -4.9219); the model above is the epoch selected on the val rank-IC, so this row is optimistically selected — compare the two to gauge the selection effect.

### Sub-window stability (disjoint contiguous blocks of the val window)

| Sub-window | dates | model mean IC | model t | best factor on that block | best \|IC\| |
| :--- | ---: | ---: | ---: | :--- | ---: |
| 1 | 30 | -0.2172 | -5.5319 | `vol_20` | +0.1418 |
| 2 | 30 | -0.0784 | -3.2798 | `mom_12_1` | +0.1388 |

## Reading notes

- The baseline moves with the window: `rev_1m` was -0.0094 over the full CAD sample but -0.157 on the 10 recent dates WI-009 used, so the widened window's factor numbers are part of the deliverable, not a constant.
- The ~20-trading-day shortlist lag (feature rows require all four forward targets) is **out of scope** for WI-009b and is unchanged by this work item.
- Sub-window factor ICs are reported as information; clause (b) is a stability guard on the model's own IC, as fixed in the plan.

