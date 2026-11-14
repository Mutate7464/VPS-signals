"""WI-018: condition-first directional study of `first_touch` @ w≈34 (USD only).

Admin-approved plan: `docs/plans/26-W45-WI-018-condition-first-first-touch.md`
(accepted ADR `docs/workflow/designs/D-018-condition-first-first-touch.md`).

Isolation ground rules for this package:

- USD market only. CAD is skipped entirely (D-018 Q2) — there is no CAD code path.
- Read-only on the frozen WI-017 inputs: `reports/wi017/derived/<SYM>.parquet`,
  `reports/wi017/features/<SYM>.parquet` and the run-5 prune list
  `reports/wi017/run5_prune_recs.json` (88 `keep_columns`). No WI-017 recompute,
  no writes to any WI-014/016/017 artifact.
- Writes land under `reports/wi018/`, `src/wi018/`, `docs/`, `tests/` only.
- Hard constraints (AGENTS.md): `n_jobs<=2`, `float32` immediately after
  calculation, symbol-sequential iteration over date blocks (no all-ticker
  uncompressed frame), bounded memory.
- Descriptive research only: no order execution, no shortlist CSV, human gate
  unchanged. Ship shape is a memo (D-018 Q5).
- Ladder: G1 atlas (guaranteed) → G2 falsification probe → G3 cost overlay only
  if G2 clears.
"""

from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

MARKET = "USD"
"""The only evaluated market in WI-018 (CAD explicitly skipped, D-018 Q2)."""

PRIMARY_TARGET = "first_touch_34"
"""Decision target: the only balanced 3-way directional split from WI-017 run 2."""

SECONDARY_TARGETS = ("first_touch_24", "first_touch_39")
"""Robustness reads only — never alternate selection targets (plan CONSTRAINTS)."""

HORIZON = 34
"""Target horizon used for the fold embargo: `max(20, w)` = 34 sessions."""

BINNINGS = {"quintile": 5, "tercile": 3}
"""Both binnings are reported (D-018 Q1); states are within-date cross-sectional."""

TARGET_VALUES = (1.0, 0.0, -1.0)
"""Documented WI-017 encoding: +1 up-first, 0 neither, -1 down-first (checked, not assumed)."""

FDR_ALPHA = 0.05
"""BH-FDR level for the single G2 hypothesis family (D-018 Q4)."""

BOOTSTRAP_BLOCK_DATES = 20
BOOTSTRAP_DRAWS = 1000
BOOTSTRAP_SEED = 42

MIN_GROUP_N = 30
"""Below this many condition rows a rate is reported insufficient (WI-011 MIN_N)."""

MIN_GROUP_DATES = 3
"""Below this many dated cross-sections a rate carries no usable CI."""

COST_BPS_TOTAL = 25.0
"""G3 cost assumption: WI-011 20 bps + 5 bps slippage, explicitly an assumption."""

EXPECTED_USD_SYMBOLS = 593
EXPECTED_FEATURE_COLUMNS = 264
"""Feature columns per symbol in the WI-017 run-3 grid (`date` excluded)."""

DERIVED_DIR = BASE_DIR / "reports" / "wi017" / "derived"
FEATURES_DIR = BASE_DIR / "reports" / "wi017" / "features"
PRUNE_RECS = BASE_DIR / "reports" / "wi017" / "run5_prune_recs.json"

REPORTS_DIR = BASE_DIR / "reports" / "wi018"
PREFLIGHT_JSON = REPORTS_DIR / "preflight_USD.json"
ATLAS_JSON = REPORTS_DIR / "atlas_USD.json"
ATLAS_MD = REPORTS_DIR / "atlas_USD.md"
PROBE_JSON = REPORTS_DIR / "probe_USD.json"
PROBE_MD = REPORTS_DIR / "probe_USD.md"
G3_JSON = REPORTS_DIR / "g3_USD.json"
"""G3 cost-overlay payload (written only when G2 clears; skipped otherwise)."""
SUMMARY_MD = REPORTS_DIR / "summary_USD.md"

DATES_PER_BLOCK = 300
"""Date-block size for the streaming passes: keeps one block frame <= ~100 MB."""

DATE_COLUMN = "date"

__all__ = [
    "ATLAS_JSON",
    "ATLAS_MD",
    "BASE_DIR",
    "BINNINGS",
    "BOOTSTRAP_BLOCK_DATES",
    "BOOTSTRAP_DRAWS",
    "BOOTSTRAP_SEED",
    "COST_BPS_TOTAL",
    "DATES_PER_BLOCK",
    "DATE_COLUMN",
    "DERIVED_DIR",
    "EXPECTED_FEATURE_COLUMNS",
    "EXPECTED_USD_SYMBOLS",
    "FDR_ALPHA",
    "FEATURES_DIR",
    "G3_JSON",
    "HORIZON",
    "MARKET",
    "MIN_GROUP_DATES",
    "MIN_GROUP_N",
    "PREFLIGHT_JSON",
    "PRIMARY_TARGET",
    "PROBE_JSON",
    "PROBE_MD",
    "PRUNE_RECS",
    "REPORTS_DIR",
    "SECONDARY_TARGETS",
    "SUMMARY_MD",
    "TARGET_VALUES",
]
