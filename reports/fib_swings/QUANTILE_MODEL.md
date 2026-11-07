# WI-025 quantile model of rally (MFE) and drawdown (MAE)

CALIB date < 2022-05-02; EVAL date >= 2022-07-01; XGB reg:quantileerror q10/q50/q90 vs per-symbol empirical baseline (global fallback < 20 CALIB events).

fwd_mfe_pct | CAD: model_pin 3.262 vs base_pin 3.692 (better=True) coverage=0.805 (in-range=True)
fwd_mfe_pct | USD: model_pin 3.402 vs base_pin 3.793 (better=True) coverage=0.781 (in-range=True)
fwd_mae_pct | CAD: model_pin 1.890 vs base_pin 2.146 (better=True) coverage=0.849 (in-range=True)
fwd_mae_pct | USD: model_pin 2.024 vs base_pin 2.178 (better=True) coverage=0.827 (in-range=True)

VERDICT: PASS
