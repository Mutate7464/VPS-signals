---
wi_id: WI-064
title: Meta-label driver + synthetic tests (code+smoke only; full run is a PM gate)
status: draft
agent: surgical-builder
depends_on: []
gate_layer: "L1.5 input-prep (D-027; not an L1 refit, no trading claim)"
board_row: "D-027 Phase 1"
write_files:
  - src/l2_overlay/drivers/meta_label_full.py
  - tests/l2_overlay/test_meta_label_full.py
read_only_files:
  - src/swing_bsh/meta_label_ext.py
  - docs/workflow/designs/D-027-l2-rebuild.md
test_command: uv run pytest tests/l2_overlay/test_meta_label_full.py -q --tb=short --maxfail=1 && uv run python -m src.l2_overlay.drivers.meta_label_full --smoke
---

## 1. Objective and invariant
- Wire primary swing sides/outcomes from the frozen fib baseline plus features via `--infer`, run `meta_oof` (WI-062 machinery) on both markets, and write OOF probabilities as an L2 input artifact. Research delivers **code + synthetic tests + `--smoke` only**; the full-universe run is a separate PM go/no-go. Invariants: n_jobs=2, float32 immediately, purged/embargoed CV, symbol-sequential reads.
- Re-create the sitecustomize torch preload if `uv sync` ran before tests.

## 2. I/O contract and blueprint (literal)
- Input: frozen fib baseline entries (PM artifact path passed via `--baseline`), feature panel via existing `--infer` path; root is a named constant; never read from `--out`.
- Output (full PM run, not this WI): `data/models/l2_meta_oof/<MARKET>_oof.parquet` — columns `date:symbol:p_oof:fold`, float32; plus `manifest.json` with input hashes and CV fold bounds.
- Dry-run: `--smoke` writes to `data/models/l2_meta_oof_smoke/` and never overwrites frozen report names.
- `src/swing_bsh/meta_label_ext.py` (read-only): reuse its `meta_oof` entrypoint unchanged; the driver only wires inputs, runs it, and persists outputs.
- `tests/l2_overlay/test_meta_label_full.py`: synthetic panel proves (a) OOF is purged-CV only, (b) no EVAL-period rows touched (assert date bounds), (c) output schema/dtypes exact.

## 3. Definition of Done (binary)
- [ ] No edits outside `write_files`.
- [ ] `test_command` exits 0 (synthetic tests + smoke).
- [ ] Smoke output shape matches section 2; OOF columns float32; no EVAL rows in smoke OOF.
- [ ] `src/l2_overlay/INDEX.md` updated (new driver listed). (Allowed addition within manifest spirit; record in footer.)
- [ ] Stdout ≤5 lines: exit status, output shape, runtime.

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 1/2 | **Commit:** PENDING (HEAD eb43132; no commit made) | **Status:** DONE
- **Notes / error tail:** test_command exit 0 — `5 passed in 1.75s` + smoke `USD rows 161/259 auc 0.5539, CAD rows 48/133 auc 0.5430, 2.1s, EXIT:0`; smoke OOF `date:symbol:p_oof(float32):fold(int16)`, max date 2022-06-30 < EVAL_START 2022-07-01 (no EVAL rows); manifest.json carries input sha256 + fold bounds. Added `src/l2_overlay/INDEX.md` (DoD §3) — new driver listed; no other out-of-manifest edits.
