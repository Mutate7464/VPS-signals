# D-026 Phase 1 — L0 R12 consolidated summary (RATIFIED, admin in chat 2026-11-14)

- Generated (UTC): 2026-11-14T01:05Z · **RATIFIED 2026-11-14 (admin in chat, Layer 1)** —
  verdicts stand as computed: L0-5 survives, L0-2/L0-4 absorbed, L0-1/L0-3/L0-6 no delta.
- Scope: the six net-new L0 feature blocks (WI-052…057) on the R12 reference grid
  (2 targets `b_hold` + `xsec_vol_rank_bin` × horizons {8,13,21} × lightgbm × 2 markets
  = 12 cells per block, one BH-FDR family per block, m=12, α=0.05).
- Verdict: **RATIFIED (admin in chat, 2026-11-14, Layer 1)**. PREDICTIVE DIAGNOSTIC —
  no economic claim (D-023).
- Supersedes nothing on disk: the first (contaminated) report and checkpoint are retained
  as provenance (see §2).

## 1. Verdict

**Theory is sound; the first run was an implementation bug, now fixed and re-run.**

| block | net-new cols (post-prune) | ΔAUC (best cell) | BH survivors (m=12) | verdict (provisional) |
|---|---|---|---|---|
| L0-1 swing structure | 2/5 (`swing_leg_len_3`, `swing_leg_dur_3`) | +0.0012 (USD xsec h13) | 0/12 | no standalone delta |
| L0-2 realized asymmetry | 0/8 — fully absorbed | ≡0 by construction | n/a (absorbed) | redundant (Q1 rule fires) |
| L0-3 regime age | 3/3 | +0.0241 (CAD b_hold h21, p=0.245) | 0/12 | no standalone delta |
| L0-4 jump intensity | 0/4 — fully absorbed | ≡0 by construction | n/a (absorbed) | redundant (Q1 rule fires) |
| L0-5 universe dispersion | 1/2 (`disp_entropy_39`) | +0.0043 (CAD xsec h21) | **4/12** | **survives** |
| L0-6 effort/result | 1/4 (`effort_result_21` rep.) | +0.0052 (USD b_hold h21, p=0.394) | 0/12 | no standalone delta |

- **L0-5 is the only surviving block** — all four survivors are `xsec_vol_rank_bin`
  (CAD h8/h13/h21, USD h21), ΔAUC +0.002–0.004 on base AUC 0.79–0.85, p 0.005–0.012,
  cross-market consistent, horizon-monotone in the same band as the union test.
  The delta comes from `disp_entropy_39` (cross-sectional dispersion of `entropy_39`),
  the date-level market-regime axis the plan predicted (`cs_entropy_102` attribution).
- L0-2 and L0-4 need no refit: every one of their columns correlates |ρ|>0.3 with a
  surviving baseline column (absorption table §3), so their pruned feature set equals
  the baseline's and the fold-paired delta is exactly zero. This is the plan's Q1
  change-my-mind rule firing with per-column evidence.
- The union test (§4) bounds all six blocks: aggregate lift is ΔAUC ≈ +0.002–0.005,
  so no single block could show more than that standalone — consistent with the
  per-block results.

## 2. What went wrong in the first run (provenance, retained on disk)

- **Bug:** `_features_for` defined the base as *candidates minus this block's cols*,
  so every block run silently included the other five blocks' surviving columns.
  The delta therefore measured "the block + all other blocks" (the union), not the block.
- **Smoking guns:** all six block runs converged to the same 44-col kept set with the
  same 7-col symmetric diff vs baseline; L0-2 and L0-4 (own cols fully pruned) produced
  byte-identical fold AUCs (L0-2 = L0-6 CAD b_hold h21 = `[0.923336, 0.904383, 0.91961,
  0.589881]`).
- **Retained artifacts (nothing deleted):**
  - Contaminated run: `reports/l0_r12_summary.md`, ckpt `/tmp/l0_r12_ckpt/` (84 cells) —
    reinterpreted in §4 as the union test, which is exactly what it measured.
  - Corrected run: `reports/l0_r12_v2/l0_r12_summary.md`, ckpt `/tmp/l0_r12_ckpt_v2/`
    (12 baseline cells copied, not moved).
- **Fix:** base = candidates excluding all six blocks' cols; block run = base + that
  block's cols. Estimand unchanged from D-026 §2a; no theory change.

## 3. Absorption table (max |Spearman ρ| vs the 37 baseline kept cols, USD panel)

| block col | vs | ρ | status |
|---|---|---:|---|
| `swing_leg_len_1` | `bars_since_opp` | 0.445 | absorbed |
| `swing_leg_dur_1` | `bars_since_opp` | 0.418 | absorbed |
| `swing_depth_atr_prev` | `bars_since_opp` | 0.417 | absorbed |
| `swing_leg_len_3` / `swing_leg_dur_3` | `hurst_63` / `adx_21` | 0.075 / 0.071 | net-new |
| `semivar_*_21/55` (6) | `atr_pct_3` | 0.69–0.80 | absorbed |
| `semivar_ratio_*` (2) | `di_spread_3/233` | 0.49–0.67 | absorbed |
| `rv_skew_21/55` | `di_spread_3/233` | 0.40–0.60 | absorbed |
| `regime_age_vol` | `atr_pct_3` | 0.120 | net-new |
| `regime_prev_dur_vol` | `cs_entropy_102` | 0.068 | net-new |
| `regime_age_hurst` | `hurst_63` | 0.067 | net-new |
| `jump_var_ratio_21/55` | `entropy_24` / `cs_entropy_102` | 0.41–0.49 | absorbed |
| `jump_count_21/55` | `entropy_24` / `cs_entropy_102` | 0.41–0.51 | absorbed |
| `disp_atr_pct_21` | `atr_pct_3` | 0.315 | absorbed |
| `disp_entropy_39` | `month` | 0.147 | net-new |
| `effort_result_*` (4) | `kama_er_3` / `atr_pct_3` | 0.11–0.14 | net-new |

## 4. Union test (from the contaminated run — valid as relabeled)

Because all six contaminated kept sets were identical, that run's delta is exactly the
test of the **union of net-new cols** (`swing_leg_len_3`, `swing_leg_dur_3`,
`regime_age_vol`, `regime_prev_dur_vol`, `regime_age_hurst`, `disp_entropy_39`,
`effort_result_21`) vs baseline — one BH family, m=12:

- 3/12 survivors, all `xsec_vol_rank_bin` (USD h8 p=0.043; USD h13 p=0.044; CAD h21
  p=0.006), ΔAUC +0.002–0.005.
- L0-5's per-block survivors are a subset of the same band — the union adds nothing
  the single block doesn't already give.

## 5. Actions (pending admin ratification)

1. **Keep** `disp_entropy_39` in the L1 candidate feature set (L0-5 survivors).
2. **Record** L0-2 / L0-4 as fully absorbed (Q1 rule, evidence §3) — no library entry.
3. **Record** L0-1 / L0-3 / L0-6 as no-delta negatives with retained artifacts.
4. Board row + PM_LOG cycle entry for the R12 runs (WI-052…057 build cards were already
   done; the grid runs are the outstanding item this doc closes).
5. Next: L1 full grid runs (WI-058…061, caps 1.5–2.0/family) — `ALL_FAMILIES` still lacks
   the `mfe_mae_*` and `move_*` wiring (WI-059/060 left panel/grid wiring to PM).

## 6. Flags — anything NOT kept (recorded per admin direction, 2026-11-14)

None of the following enters the L1/L2 candidate feature set under this verdict. All
columns remain in the panel and are re-admissible under a lower prune threshold.

| block | not kept | why |
|---|---|---|
| L0-1 | `swing_leg_len_1`, `swing_leg_dur_1`, `swing_depth_atr_prev` | absorbed (ρ>0.3 vs `bars_since_opp`) |
| L0-1 | `swing_leg_len_3`, `swing_leg_dur_3` | net-new but 0/12 BH survivors (no standalone delta) |
| L0-2 | all 8 (`semivar_up/dn/ratio_{21,55}`, `rv_skew_{21,55}`) | fully absorbed (ρ 0.40–0.80 vs `atr_pct_3`/`di_spread_3/233`) — Q1 rule |
| L0-3 | `regime_age_vol`, `regime_prev_dur_vol`, `regime_age_hurst` | net-new but 0/12 BH survivors |
| L0-4 | all 4 (`jump_var_ratio_{21,55}`, `jump_count_{21,55}`) | fully absorbed (ρ 0.40–0.51 vs `entropy_24`/`cs_entropy_102`) — Q1 rule |
| L0-5 | `disp_atr_pct_21` | absorbed (ρ=0.315 vs `atr_pct_3`) |
| L0-6 | all 4 (`effort_result_{21,55}`, `effort_result_z_{21,55}`) | net-new but 0/12 BH survivors |

Kept (the only addition): **`disp_entropy_39`** (L0-5, 4/12 BH survivors, all
`xsec_vol_rank_bin`).

## 7. Admin direction recorded (2026-11-14, not yet dispatched)

Admin will run a **larger variant with a lower rho-prune threshold to maximize the
parameter count** for the L1/L2 grid runs. Implication: the absorbed/not-kept columns
above (21 of the 27 block cols) are the population this variant re-admits. Design note
for that run: a lower threshold changes the pruned feature set, so it is a NEW
pre-registered family/variant — never merged into the ρ=0.3 verdicts above; BH runs
once over its own m. Not dispatched yet.

## Footer

- Corrected run: START 2026-11-14T00:50:24Z, END 00:58:42Z, core 888.6s (0.25 core-h),
  NEXT_ALLOWED_RUN_UTC 2026-11-14T01:28Z (burst < 1 core-h).
- Test statistic: fold-paired OOF AUC delta vs baseline; paired t (df=4); BH α=0.05,
  m=12 per block. n_jobs=2, float32, symbol-sequential, purged/embargoed CV.
- Verdict RATIFIED (admin in chat, 2026-11-14, Layer 1).
- PREDICTIVE DIAGNOSTIC — no economic claim (D-023).
