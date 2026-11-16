---
wi_id: WI-071
title: One-shot EVAL gate across surviving constructions (PM-owned; admin ratifies)
status: draft
agent: surgical-builder
depends_on: ["WI-066", "WI-067", "WI-068"]
gate_layer: "2 (overlay/trading; pre-registered one-shot EVAL)"
board_row: "D-027 Phase 5"
write_files:
  - src/l2_overlay/constructions/eval_gate.py
  - tests/l2_overlay/test_eval_gate.py
read_only_files:
  - src/l2_overlay/harness.py
  - src/l2_overlay/fold_report.py
  - docs/workflow/designs/D-027-l2-rebuild.md
test_command: uv run pytest tests/l2_overlay/test_eval_gate.py -q --tb=short --maxfail=1
---

## 1. Objective and invariant
- One-shot EVAL: (1) freeze the pre-registration file (constructions, parameters, FDR family list, materiality floor) — hashed and committed BEFORE any EVAL read; (2) score EVAL **once**; (3) apply BH-FDR across the pre-registered rebuild family (constructions × markets × signals); (4) fold report on EVAL; (5) provisional verdict per construction — **PROVISIONAL until admin ratifies in chat** (AGENTS.md provisional-verdict rule). No deployment without ratification. Any EVAL subset look before this WI is a burn.
- Code+tests only in this WI; the actual EVAL scoring run is PM-owned.

## 2. I/O contract and blueprint (literal)
- Input: pre-registration file (WI-065 template, filled), frozen CALIB artifacts, EVAL panel. Root named constant.
- Output: `reports/l2_eval/verdicts.md` + `verdicts.json` (per construction: net edge, fold report, BH-FDR q, ADOPT/REJECT/INCONCLUSIVE label tagged PROVISIONAL); smoke path for tests.
- `eval_gate.py`: `verify_prereg_hash()`, `score_eval_once()`, `bh_fdr_across_family()`, `emit_verdicts()` — refuses to run if prereg hash mismatches or EVAL lock not released by the harness.
- Tests: hash mismatch refuses; double-scoring attempt raises; FDR applied across the full listed family (not per-construction); verdict labels always carry the provisional tag.

## 3. Definition of Done (binary)
- [ ] No edits outside `write_files`.
- [ ] `test_command` exits 0; all guard tests pass.
- [ ] No EVAL data read during smoke (test proves).
- [ ] Stdout ≤5 lines.

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 2/2 | **Commit:** 4e3e125 (close-out commit; footer patched by PM) | **Status:** DONE — `uv run pytest tests/l2_overlay/test_eval_gate.py -q --tb=short --maxfail=1` → 10 passed, exit 0
- **Notes / error tail:** fix cycle 1 = test-helper default-family bug (DID NOT RAISE); cycle 2 = missing `verdicts` payload keys (`family_size`/`n_tested`/`n_untested`) + None-safe cell formatting. Final smoke: 1 stdout line, `verdicts.md`/`verdicts.json` + frozen prereg under /tmp only; no-EVAL-read proven by traps on `Path.read_text`/`read_bytes` + `pandas.read_parquet` (no `data/` path touched).
- **Files:** `src/l2_overlay/constructions/eval_gate.py` (249 lines), `tests/l2_overlay/test_eval_gate.py` (159 lines); `src/l2_overlay/INDEX.md` NOT updated (outside `write_files` — new module left for the next lock holder).
