# RISKS.md — Living Risk Register (PMP)

> Reviewed at the weekly ceremony. A risk that materializes gets an immediate response work item on the board. Probability: L/M/H · Impact: L/M/H · Response: avoid / mitigate / transfer / accept.

| ID | Risk | P | I | Owner | Response / mitigation | Status |
|---|---|---|---|---|---|---|
| R-01 | Look-ahead bias / serial-correlation leakage in targets | M | H | Plan agent | PurgedWalkForwardSplit embargo=20d + `tests/test_leakage.py` before any training (Design/05) | Mitigation in place |
| R-02 | VPS OOM (8 GB) during feature engineering / PDF compile | M | M | Build agent | n_jobs=2, float32, per-ticker streaming, batched charts + gc.collect (AGENTS.md) | Mitigation in place |
| R-03 | IBKR pacing violation → error-162 socket lock | H | M | Build agent | Phase 1 pacing + retry (implemented); Phase 2 only after 3 clean runs | Mitigated pending validation (WI-003) |
| R-04 | **Models carry no predictive signal** (realized 2026-10-21: all 4 targets ≈ random) | — | H | Admin | Response work item WI-002; do not trust 20261021 PDFs | **REALIZED — active.** E2 (2026-10-23, real 508-ticker universe, clean run) refuted H1: still null with healthy controls → verdict E2 NULL; ADR routes to E3/E4/E5 diagnostics |
| R-05 | Documentation drift (handover/board stale → agents act on wrong state) | M | M | All | Session-end handover refresh + board update contract in agent instructions | Mitigation strengthened 2026-10-23: WORKFLOW.md §1 rule 6 (state must match artifacts; verify PID claims) + `signals-workflow-execution` skill encodes verify-before-acting |
| R-06 | Gate protocol skipped under output pressure (Sprint 5 past failed Gate 4) | M | H | Admin | Blocking QA column + DONE requires verdict (WORKFLOW.md §1 rule 4) | Mitigation in place |
| R-07 | M1 Mac single point of failure for data acquisition (gateway + 2FA local-only) | M | M | Admin | `--delta-only` keeps re-runs cheap; ib4 kit is self-contained and restorable | Accepted |
