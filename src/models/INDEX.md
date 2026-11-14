# src/models/ — WI-009 series model library (research; screener is factor-based)
- `contrastive_ranking.py` pairwise ranker; `pair_sampler.py` pair sampling; `training_data.py` folds
- `continuous_targets.py`, `robustness_gates.py`, `skill_bar.py` (same-sign AND |IC| clause)
Invariant: purged walk-forward splits (tests/test_e5_split_no_leak.py); anti-correlated models never ship.