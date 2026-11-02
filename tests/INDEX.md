# tests/ — 47 files, 662 tests green at MVP close
- Per-WI: test_wi009c/011/013/014/016/017/018_*, test_e5_split_no_leak (leak lock), test_adjudicated_reinstate (skip-list lock)
- Pipeline: test_leakage, test_targets_stay, test_xgb_trainer, test_pdf_compiler_factor
Run: uv run pytest (7-8 min, detached); targeted: uv run pytest tests/test_<wi>_*.py -q.