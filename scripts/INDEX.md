# scripts/ — CLI drivers + long-run chains (entry points, not libraries)
- MVP: `wi014_screener.py` (daily shortlist), `rebuild_wi013_metadata.py`, `notify_gate.sh` (webhook watcher)
- Research: `train_wi009c.py` (1200L, split queued D-1), `wi011_*`, `wi017_run4_*`, `diag_signal.py`, `train_contrastive.py`
Invariant: reruns must NOT overwrite frozen reports (use validation prefix + git checkout --).