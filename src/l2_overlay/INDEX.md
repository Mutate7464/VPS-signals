# src/l2_overlay/ — Layer-2 overlay package (D-024 / D-027)

Layer 2 = decision/edge protocol, never an AUC claim (D-023 layering). Inputs arrive
pre-scored; nothing here re-fits an L1 learner unless the card says so.

- `harness.py` (WI-041, extended WI-065) — one overlay protocol: feasibility → CALIB-only tau → one-shot EVAL → placebo → per-fold edges → verdict. WI-065 adds `load_union()` (wi040 ∪ wi048, cell-key dedup + no-cell-twice assertion), `xsec_inert_precheck()`, `preregistration_template()` / `prereg_hash()` / `write_preregistration()` / `load_preregistration()` (sha256-verified), the EVAL lock (`EvalLockError`, `assert_eval_unlocked()`, `eval_read()`), and `calib_stop()`. `run_overlay` now carries a mandatory `fold_report`; CLI gains `--smoke`.
- `costs.py` (WI-065) — pure L2 cost model in bps: `single_leg_cost` 50, `pair_cost` 100, `turnover_cost(f)` 100·f, `resize_cost(Δ)` 25·|Δ|.
- `fold_report.py` (WI-065) — mandatory per-fold report: `fold_report(oof_edges) -> {per_fold_net_edge, max_fold_share, fold_ceiling_ok}`; raises `FoldReportMissing` when the rows are absent (fails closed).
- `rerun_legacy.py` (WI-043) / `rerun_modern.py` (WI-042) — the seven closed questions re-run under the harness.
- `edge_decay_probe.py` (WI-045) — CALIB→EVAL decay attribution.
- `drivers/meta_label_full.py` (WI-064) — L1.5 input-prep: frozen fib entries + feature panel → WI-062 `meta_oof` purged-CV OOF probabilities per market (`data/models/l2_meta_oof[_smoke]/<MARKET>_oof.parquet` + `manifest.json`). `--smoke` for research runs; `--full --infer --baseline <PM artifact>` is a PM go/no-go (EVAL never read).
