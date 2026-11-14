# src/factors/ — E5 factor baseline (THE MVP signal)
- `e5_baseline.py`: 5-factor continuous baseline (mom, vol, etc.), horizon-parametrized (h15/h20), `--market` aware.
Invariant: same-sign-vs-best-factor clause governs any comparison; fix history at e5_baseline.py:99 (WI-012).