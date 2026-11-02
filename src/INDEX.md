# src/ — pipeline + research packages (MVP signal: E5 screener, scripts/wi014_screener.py)
- ingest: `ibkr_ingest.py` OHLCV fetch; `verify_synced_data.py` gate-1 verifier; `build_watchlist.py` universe build
- features/stats: `feature_engine.py` fib 3-233 panel; `stat_metadata.py` E5 metadata; `targets.py` labels
- models/reporting: `xgb_trainer.py` purged walk-forward; `model_qa.py` gate-4 QA; `pdf_compiler_factor.py` tearsheet
- state: `state_manager.py`, `run_logging.py`; quarantine: `quarantine_analysis.py`, `quarantine_triage_report.py`
- research packages: `wi011/ wi016/ wi017/ wi018/` (INDEX.md each), `perfanalytics/`, `factors/`, `models/`
Invariant: point-in-time only (no future data), n_jobs=2, float32, symbol-sequential. See ../docs/architecture/DECISIONS_AND_NEGATIVE_KNOWLEDGE.md before changes.
