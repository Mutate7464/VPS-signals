# WI-012 — Cross-market validation run: full process on CAD + USD from the current version

- Generated (UTC): 2026-10-26 (PM-executed under admin order "iterate from this version, run both markets", scope confirmed via clarify: full depth incl. WI-011 on USD; reports to `reports/wi012_*`).
- All numbers below are PM-run live this cycle; frozen WI-009/009c/011 gate artifacts untouched (restored via `git checkout` after each stage).

## Headline results (both markets, current code)

| Stage | CAD | USD | Verdict |
| :--- | :--- | :--- | :--- |
| E5 factor baseline (h15) | mom +0.0271 t+7.33 · vol −0.0432 t−10.74 | mom +0.0209 t+6.00 · vol −0.0158 t−5.11 | **Factor signal generalizes to USD** (weaker ICs, same signs, both \|t\|>2) |
| E5 factor baseline (h20, post-fix) | mom +0.0275 t+7.49 · vol −0.0462 t−11.37 | mom +0.0202 t+5.89 · vol −0.0166 t−5.36 | Same conclusion at 20td |
| WI-009c probe (5 labels) | 0/5 clear bar (frozen) | **0/5 clear bar** (`wi012_probe_USD.md`) | Labels bottleneck **cross-market confirmed** |
| WI-009c continuous ridge | IC +0.0001, FAIL (frozen) | IC +0.0016 t+0.38, same-sign but \|IC\| < amihud_20 +0.0154 → FAIL | Route stays closed on both markets |
| Trainer smoke (metafeats + xgb) | AUC 0.535 | AUC 0.517 | Machinery works both markets (smoke only, no purge — not a skill claim) |
| WI-011 conditions scan | "none survive costs" (frozen) | **survivors=0 → "none survive costs at this universe size."** | NO_TRADE default **cross-market confirmed** |

## Errors found and fixed this iteration

| ID | Severity | Finding | Status |
| :--- | :--- | :--- | :--- |
| F-1 | **ERROR (fixed)** | `build_e5_panel` dropna'd on `fwd_atr_ret_15` only → at `--horizon 20`, ~5 dates per market carried NaN `fwd_atr_ret_20` (tail/delisting rows) and the non-NaN-aware mean NaN'd the **entire** single-factor IC table. Frozen evidence (h15 default) masked it. | **Fixed** `src/factors/e5_baseline.py:99` (dropna both fwd cols); regression-locked `tests/test_e5_baseline_horizon_nans.py` (real-data panel, both horizons finite); 6/6 pass |
| F-2 | cosmetic | USD report says "Compiled on CAD" — hardcoded string in `write_report`. | Open (next iteration) |
| F-3 | refactor need | WI-011 scripts not market-parametrized: `MARKET` constant in `src/wi011/__init__.py` + hardcoded CAD parquet paths in `scripts/wi011_preflight.py`. USD run required temporary sed patches (reverted after). | Open (next iteration: `--market` flag through the 6 scripts) |
| F-4 | **schema wart / leakage footgun** | BOTH metadata feature panels embed 4 label columns (`y_15d_high/low`, `y_20d_up/down`). No live leak (trainer selects explicit catalog cols), but any all-columns consumer would train on labels. | Open (next iteration: strip at build, or assert absence) |
| F-5 | process | Re-running pipeline stages **overwrites frozen gate reports in place** (`wi009_e5_baseline_{CAD}.md`, `wi009c_{regression,summary}.md`, `wi011_*.md` hardcode report paths). Cost PM 3 copy+`git checkout` cycles this run. | Open (next iteration: `--out`/market-suffixed report paths everywhere) |

## Performance profile (this host, n_jobs=2)

| Stage | Wall | Note |
| :--- | ---: | :--- |
| E5 baseline, full market (incl. multivariate) | ~25–60 s | cheap; no detach needed |
| `probe_wi009c` USD | ~3 min | logistic × 5 labels × 5 folds |
| `train_wi009c` USD (ridge, 5 folds) | **19.4 s** | fast |
| `evaluate_wi009c` USD | ~30 s | |
| WI-011 chain USD (6 scripts) | ~9 min | expectancy + ts_momentum dominate |
| Full pytest suite | 7–8 min (known) | not re-run this cycle; targeted 6/6 + 13/13 mask tests |

**Optimization conclusions:** nothing in the current route is hours-scale — the old "trainer stage ~96% feature recompute" warning applies to the legacy xgb trainer route, not this one. Future iterations can run the full route foreground per stage; keep the detach pattern only for the WI-011 chain.

## Universe drift note (next gate should re-baseline)

CAD universe is now **335 symbols** (was 313 at the WI-009 gate) and **USD 532** — the WI-010b reinstatements widened eligibility. CAD h15 re-run from this version vs frozen: mom +0.0271 vs +0.0243, vol −0.0432 vs −0.0454 — same signs, magnitudes shift ~0.002–0.003. Not drift alarm; the frozen baseline remains the gate record, `wi012_e5_baseline_CAD_h15.md` is the current-universe number.

## Carried decisions / rules (unchanged)

- Same-sign clause + probe-first on any future skill bar; no 89-feature spend (0/5 labels USD AND CAD).
- Robustness options remain gated NOT RUN.
- NO_TRADE default confirmed on both markets; commission params still admin-assumption.

## Reproduce (current version)

```bash
uv run python -m src.factors.e5_baseline --market USD --horizon 20 --multivariate
uv run python scripts/probe_wi009c.py --market USD
uv run python scripts/train_wi009c.py --market USD
uv run python scripts/evaluate_wi009c.py --market USD
# WI-011 on USD requires the F-3 parametrization (temp MARKET patch as done this cycle)
```