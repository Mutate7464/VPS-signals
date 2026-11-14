
# Fib overnight chain — started 2026-11-06T22:49:41Z, model openrouter/z-ai/glm-5.3

## WI-021 — acceptance ACCEPT
- [x] EVAL bottom n_events == 20990 (got 20990)
- [x] EVAL bottom n_screened == 1056 (got 1056)
- [x] EVAL bottom screen_rate ≈ 0.2959 (got 0.2959)
- [x] EVAL bottom base_rate ≈ 0.2619 (got 0.2619)
- [x] 2026 bottom screen_rate ≈ 0.2436 (got 0.2436)
- [x] EVAL top drop-outcome rates ≈ 0.1034 / 0.1147
- [x] events file has screen_bottom, screen_top, market
- [x] events rows == 186729 (got 186729)
- [x] unresolved bottoms have empty grade
- [x] priors 903 unique symbols (got 903)
- result: EVAL bottom edge = 3.4pp; 2026 screen 0.2436 vs base 0.3084

## WI-023 — acceptance ACCEPT
- [x] 32 policies (got 32)
- [x] t10_s8_d39_close EVAL screened n == 1007 (got 1007)
- [x] screened hit_rate in [0.403, 0.712] (got 0.4777)
- [x] all-bottoms hit_rate in [0.378, 0.705] (got 0.44)
- [x] exit_policy_choice.json has 'policy'
- result: chosen policy = None (NO_POLICY_CLEARS), CALIB mean ret None
- [x] trade_labels rows == 76049*32 (got 2433568)

## WI-022 — acceptance ACCEPT
- [x] regime_daily has CAD/USD/ALL
- [x] r2 within [0,1]; > 4500 dates
- [x] UNGATED EVAL ALL screen_rate ≈ 0.2959 (got [0.2959285004965243])
- [x] REGIME_OVERLAY.md has a VERDICT line (got PASS)
- result: VERDICT PASS
- result: UNGATED: gated_rate 0.2959, keep 1.0, base 0.2619
- result: R1: gated_rate 0.3262, keep 0.491, base 0.2619
- result: R2: gated_rate 0.3289, keep 0.614, base 0.2619
- result: R1R2: gated_rate 0.352, keep 0.343, base 0.2619

## WI-024 — acceptance ACCEPT
- [x] event_features rows == 76049 (got 76049)
- [x] all 16 features present (missing [])
- [x] each feature NaN share < 25% (max mom_12_1 0.062)
- [x] META_MODEL.md has a VERDICT line (got BLOCKED_PRECONDITION (no exit policy cleared))
- result: VERDICT BLOCKED_PRECONDITION (no exit policy cleared)

## WI-025 — acceptance ACCEPT
- [x] quantile_results rows > 0 (got 30)
- [x] QUANTILE_MODEL.md has a VERDICT line (got PASS)
- result: VERDICT PASS
```
     target market     alpha  model_pinball  baseline_pinball
fwd_mfe_pct    CAD       0.1       1.495338          1.540308
fwd_mfe_pct    CAD       0.5       4.915980          5.332133
fwd_mfe_pct    CAD       0.9       3.375825          4.202275
fwd_mfe_pct    CAD  coverage       0.805219               NaN
fwd_mfe_pct    CAD width_med      22.648387               NaN
fwd_mfe_pct    USD       0.1       1.536357          1.625564
fwd_mfe_pct    USD       0.5       5.088951          5.510724
fwd_mfe_pct    USD       0.9       3.580521          4.242484
fwd_mfe_pct    USD  coverage       0.780952               NaN
fwd_mfe_pct    USD width_med      22.061147               NaN
fwd_mfe_pct    ALL       0.1       1.521425          1.558820
fwd_mfe_pct    ALL       0.5       5.025986          5.477918
```

**Chain finished 2026-11-06T23:35:11Z: ALL_DONE** — local commits only, no pushes, no BOARD edits; PM review pending.
