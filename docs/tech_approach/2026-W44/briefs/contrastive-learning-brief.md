# Brief for Contrastive Learning Implementation (WI-009)

## Goal
Implement contrastive/pairwise learning for asset ranking with top-10 trade recommendations, using only IBKR technical (price/volume) data. First execution slice of D-003 Option 2 (hybrid technical-factor approach).

## Dataset — CAD (admin switch 2026-10-24)
- Train on **CAD** (350 tickers synced, `data/raw_ohlcv/market=CAD`), not USD. USD artifacts stay for diagnostics.
- **Stale-artifact warning:** `data/features/features_CAD.parquet` (432 KB) + `targets_CAD.parquet` (7 KB) + `data/metadata_catalog_CAD.json` date from 2026-10-21 — they predate BOTH the fib/range feature expansion (raw 63 → 89) and the iterator index-truncation fix (R-08, fixed 2026-10-23; USD features were rebuilt to 1,240,275 rows × 89; CAD was not). **Step 0 = rebuild CAD features + targets + metadata (VIF 10 / MI pct 15) before any training. Do not train on the existing CAD parquets.**
- ELE (TSE) is missing entirely (one ticker) — proceed without it, note in Deviations.

## Framework decision — PyTorch CPU (PM-verified 2026-10-24)
- Verified on this VPS: `torch 2.14.1+cpu` installs on Python 3.14 (CPU wheel); smoke test — 50 epochs × 4096 pairs × 89-dim in 0.40 s, peak RSS 0.33 GB, `torch.set_num_threads(2)`; ~810 MB disk. Usable for small tabular Siamese towers inside the guardrails (2 threads, float32, bounded batches).
- Optimization rules if torch is chosen: CPU-only wheel (no CUDA), `torch.set_num_threads(2)`, float32 tensors, per-date pair sampling streamed in batches (never materialize O(N²) pairs), embed dim ≤ 64.
- Alternative (no new framework): xgboost `rank:pairwise` on pairwise-difference features Δ(a,b) — xgboost-cpu is already a dependency. Cheaper, less flexible for embedding-based contrast. Planner picks; either passes guardrails.
- Dependency note: torch is NOT yet in `pyproject.toml` — add it pinned to the CPU index (`[[tool.uv.index]] name = "pytorch-cpu"`, url `https://download.pytorch.org/whl/cpu`, `explicit = true`, + `[tool.uv.sources]`), else uv pulls the CUDA wheel (~2.5 GB + nvidia deps) from PyPI. Smoke-verified equivalent: `uv pip install torch --index-url https://download.pytorch.org/whl/cpu` → torch 2.14.1+cpu, 810 MB.

## Reviewer pass (integrated into this run — not a separate item)
At QA, invoke the reviewer subagent via the Task tool twice:
1. Retro review of the WI-002 diagnostic commits `d957d43` + `d5c5441` (`scripts/diag_signal.py` run_e3/run_e5 changes — never reviewer-passed).
2. Pre-commit review of the WI-009 diff (guardrails, leakage, lookahead, no-live-trading).
Also fold in the one-line run_e5 fix under Deviations: evaluate the logit with `predict_proba` — class-label IC overstated the reported sign flip (probe: −0.0055, t −1.67 with proper scores vs −0.0080, t −2.78 reported).

## E5 context (why pairwise/relative is the right target)
PM probe (2026-10-24, replicates the report to ±0.0001): the ridge/logit sign flip is a **target-definition artifact, not a contradiction**. Ridge optimizes pooled continuous *magnitude* — its vol_20 loading (+0.066) is a between-date regime effect that within-date evaluation strips; the logit optimizes within-date *direction* (median split) and follows the within-date univariate directions. Their loadings disagree in sign on the liquidity/vol cluster (ridge: vol +0.066 / amihud −0.006 / logdv −0.007; logit: vol −0.037 / amihud −0.041 / logdv +0.016). Cleanest statements are the single-factor within-date ICs: mom_12_1 +5.54, vol_20 −4.72. Design implication: train and evaluate in RELATIVE (within-date pairwise/rank) space, with score-based rank-IC — never class-label IC.
Tooling caveat: `scripts/diag_signal.py` is USD-locked (`only --market USD is implemented`) — do NOT route the CAD factor baseline through `--exp e5 --market CAD`; compute the five E5 factors inside the new module (or extend the script) with within-date rank-IC on CAD. Note the E5 numbers cited above are USD — the CAD factor baseline must be recomputed and may differ.

## Acceptance Criteria
1. Pairwise framework ranks any two assets (relative outperformance), consistent ordering across the CAD universe
2. Top-10 recommendations extractable with confidence scores
3. Synthetic-data validation passes before real data (series with known relative performance)
4. Only IBKR price/volume data; float32; bounded memory; n_jobs≤2 (torch: threads=2)
5. Factor-controlled: E5's five factors as a mandatory baseline — evaluated against them on within-date rank-IC (they breached the floor: mom t +5.54, vol t −4.72)

## Non-goals
- Live trading / order execution; real-time processing (daily batch only); fundamental data; full trading strategy beyond ranking; hyper-parameter tuning of the legacy USD models

## Source Pointers
- `docs/workflow/BOARD.md` row WI-009; `docs/workflow/designs/D-003-technical-trading-approach.md`
- Reuse the 89 features in `src/feature_engine.py` — do NOT rebuild RSI/MACD/BB/ATR (draft-plan Step 2 does; drop that step)
- E3–E5 verdicts: `reports/diag_D002_*.md`; probe write-up in PM_LOG cycle-5 addendum
- Whitelist source: `stat_metadata` (CAD catalog to be regenerated — see Dataset warning)
