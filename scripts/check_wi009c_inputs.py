#!/usr/bin/env python3
"""WI-009c Step 0 — verify the CAD inputs and the target/threshold definitions.

Fail-closed checker for the artifacts the WI-009c route reads. It asserts:

  * ``features_{MKT}.parquet``: 701,599 rows and exactly 89 ``float32``
    feature columns (identifiers: date/symbol/market);
  * ``targets_{MKT}.parquet``: 701,599 rows with all five ``int8`` binary
    labels (``y_15d_high``, ``y_15d_low``, ``y_20d_up``, ``y_20d_down``,
    ``y_20d_stay``);
  * row alignment between the two artifacts on ``(date, symbol)``;
  * ``y_20d_stay`` base rate within 0.5 percentage points of 44.8%.

It then *names* the continuous 20d target and the ATR/price columns the route
uses (Step 2 trains the continuous regressor on that target and converts the
event thresholds into its units), so later steps cannot silently substitute a
different definition. Source data is read-only; nothing is written except
``reports/wi009c_inputs.txt``.

CLI::

    uv run python scripts/check_wi009c_inputs.py [--market CAD]
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pyarrow.parquet as pq  # noqa: E402

from src.targets import (  # noqa: E402
    ATR_WINDOW,
    STAY_RET_MAX,
    TARGET_COLUMNS,
    TREND_ATR_MULT,
    TREND_HORIZON,
)

REPORTS = ROOT / "reports"
FEATURES_DIR = ROOT / "data" / "features"
ID_COLUMNS = ("date", "symbol", "market")

EXPECTED_ROWS = 701_599
EXPECTED_FEATURES = 89
STAY_BASE_RATE = 0.448
STAY_TOLERANCE_PP = 0.5  # percentage points
CONTINUOUS_TARGET = "fwd_atr_ret_20"
ATR_PRICE_COLUMN = "atr_pct_20"


def _schema(path: Path):
    pf = pq.ParquetFile(str(path))
    return pf, pf.schema_arrow, int(pf.metadata.num_rows)


def _arrow_rows(path: Path, columns: list[str]) -> pd.DataFrame:
    return pq.read_table(str(path), columns=columns).to_pandas()


def check_market(market: str) -> tuple[list[str], list[str]]:
    """Run every Step-0 assertion for one market.

    Returns:
        (report_lines, failures). ``failures`` is empty when the checker passes.
    """
    mkt = market.upper()
    f_path = FEATURES_DIR / f"features_{mkt}.parquet"
    t_path = FEATURES_DIR / f"targets_{mkt}.parquet"
    failures: list[str] = []
    lines: list[str] = [
        f"# WI-009c Step 0 — input verification ({mkt})",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Features: `{f_path.relative_to(ROOT)}`",
        f"- Targets:  `{t_path.relative_to(ROOT)}`",
        "",
    ]

    for p in (f_path, t_path):
        if not p.exists():
            failures.append(f"missing artifact: {p}")
    if failures:
        return lines + [f"FAIL: {f}" for f in failures], failures

    _, f_schema, f_rows = _schema(f_path)
    _, t_schema, t_rows = _schema(t_path)
    f_names = [str(f.name) for f in f_schema]
    t_names = [str(f.name) for f in t_schema]
    f_id = [c for c in f_names if c in ID_COLUMNS]
    f_feats = [c for c in f_names if c not in ID_COLUMNS]

    # --- row counts -------------------------------------------------------- #
    if f_rows != EXPECTED_ROWS:
        failures.append(f"features rows {f_rows} != {EXPECTED_ROWS}")
    if t_rows != EXPECTED_ROWS:
        failures.append(f"targets rows {t_rows} != {EXPECTED_ROWS}")

    # --- feature columns / dtype ------------------------------------------ #
    non_f32 = sorted({str(f.type) for f in f_schema if str(f.name) in f_feats})
    if len(f_feats) != EXPECTED_FEATURES:
        failures.append(f"feature columns {len(f_feats)} != {EXPECTED_FEATURES}")
    if non_f32 != ["float"]:
        failures.append(f"feature dtypes {non_f32} != ['float'] (float32)")

    # --- target columns / dtype ------------------------------------------- #
    missing_t = [c for c in TARGET_COLUMNS if c not in t_names]
    if missing_t:
        failures.append(f"targets missing columns {missing_t}")
    t_types = {str(f.type) for f in t_schema if str(f.name) in TARGET_COLUMNS}
    if t_types not in ({}, {"int8"}):
        failures.append(f"target dtypes {sorted(t_types)} != ['int8']")

    # --- alignment on (date, symbol) -------------------------------------- #
    f_ids = _arrow_rows(f_path, ["date", "symbol"])
    t_ids = _arrow_rows(t_path, ["date", "symbol"])
    if len(f_ids) != len(t_ids):
        failures.append(f"alignment: {len(f_ids)} feature rows vs {len(t_ids)} target rows")
    key_f = f_ids.sort_values(["date", "symbol"], kind="stable").reset_index(drop=True)
    key_t = t_ids.sort_values(["date", "symbol"], kind="stable").reset_index(drop=True)
    if len(key_f) == len(key_t):
        same_date = bool((key_f["date"].to_numpy() == key_t["date"].to_numpy()).all())
        same_sym = bool((key_f["symbol"].to_numpy() == key_t["symbol"].to_numpy()).all())
        n_dup = int(len(key_f) - key_f.drop_duplicates(["date", "symbol"]).shape[0])
        if not (same_date and same_sym):
            failures.append("alignment: (date, symbol) key sets differ between features and targets")
        if n_dup:
            failures.append(f"alignment: {n_dup} duplicate (date, symbol) keys in features")
    else:
        same_date = same_sym = False
        n_dup = -1

    # --- base rates -------------------------------------------------------- #
    labels = _arrow_rows(t_path, list(TARGET_COLUMNS))
    rates = {c: float(labels[c].mean()) for c in TARGET_COLUMNS}
    stay_pp = abs(rates["y_20d_stay"] - STAY_BASE_RATE) * 100.0
    if stay_pp > STAY_TOLERANCE_PP:
        failures.append(
            f"y_20d_stay base rate {rates['y_20d_stay'] * 100:.2f}% outside "
            f"{STAY_TOLERANCE_PP}pp of {STAY_BASE_RATE * 100:.1f}%"
        )

    # --- named route inputs ------------------------------------------------ #
    probe_cols = _arrow_rows(f_path, [ATR_PRICE_COLUMN])
    atr_finite = float(np.isfinite(probe_cols[ATR_PRICE_COLUMN].to_numpy(dtype="float64")).mean())
    if ATR_PRICE_COLUMN not in f_feats:
        failures.append(f"route ATR/price column {ATR_PRICE_COLUMN} absent from features")
    if TREND_HORIZON != 20 or ATR_WINDOW != 20:
        failures.append(f"target definitions moved: TREND_HORIZON={TREND_HORIZON} ATR_WINDOW={ATR_WINDOW}")

    # --- report ------------------------------------------------------------ #
    lines += [
        "## Row counts and alignment",
        "",
        f"- features_{mkt}.parquet: **{f_rows}** rows · {len(f_id)} identifiers · "
        f"**{len(f_feats)} float32 feature columns** (dtypes: {sorted(non_f32)})",
        f"- targets_{mkt}.parquet: **{t_rows}** rows · {len(t_names)} columns · "
        f"target dtypes: {sorted(t_types) or ['n/a']}",
        f"- expected target rows: **{EXPECTED_ROWS}** (matches: {t_rows == EXPECTED_ROWS})",
        f"- (date, symbol) alignment: dates identical={same_date}, symbols identical={same_sym}, "
        f"duplicate keys={n_dup}",
        "",
        "## Binary target base rates",
        "",
        "| Target | base rate |",
        "| :--- | ---: |",
    ]
    for c in TARGET_COLUMNS:
        lines.append(f"| `{c}` | {rates[c] * 100:.2f}% |")
    lines += [
        "",
        f"- `y_20d_stay` base rate {rates['y_20d_stay'] * 100:.2f}% vs expected "
        f"{STAY_BASE_RATE * 100:.1f}% (tolerance {STAY_TOLERANCE_PP}pp) → "
        f"**{'OK' if stay_pp <= STAY_TOLERANCE_PP else 'MISMATCH'}** ({stay_pp:.2f}pp)",
        "",
        "## Continuous target and threshold inputs named by the route",
        "",
        f"- **continuous target** (the 20-trading-day continuous move): "
        f"`{CONTINUOUS_TARGET} = (close.shift(-{TREND_HORIZON}) - close) / wilder_atr_{ATR_WINDOW}`",
        f"- definition source: `src/targets.wilder_atr` (trailing, causal). It is *derived* per symbol "
        "from raw OHLCV by `src/xgb_trainer.build_panel` and `src/factors.e5_baseline.build_e5_panel`; "
        f"it is not a column of features_{mkt}.parquet, and it is not rebuilt here.",
        f"- target units: trailing-ATR multiple (dimensionless). Horizon {TREND_HORIZON}td, "
        f"ATR window {ATR_WINDOW}td.",
        "",
        "ATR / price columns used by the route:",
        "",
        f"- `{ATR_PRICE_COLUMN}` (in features_{mkt}.parquet, {atr_finite * 100:.2f}% finite) "
        "= `wilder_atr(df, 20) / close` — the ATR/price ratio that converts the ATR-unit "
        "continuous target into a *relative* move (needed by the ±5% stay event).",
        f"- `atr_pct_{{5,10,20,50,100}}` are present in the feature schema; only "
        f"`{ATR_PRICE_COLUMN}` is named here as ATR/price.",
        "- Up/down event thresholds live in the continuous target's own units: "
        f"`TREND_ATR_MULT = {TREND_ATR_MULT}` ATR (dollar-based, ±2×ATR).",
        f"- Stay event threshold: `STAY_RET_MAX = {STAY_RET_MAX}` (relative, ±5%), mutually exclusive "
        "of up/down in `src/targets.compute_targets`.",
        "",
        f"- Event-unit note: up/down are ATR-dollar based while stay is relative; the two unit "
        f"systems stay distinct and are converted (via `{ATR_PRICE_COLUMN}`), never silently pooled.",
        "",
    ]

    if failures:
        lines += ["## FAILURES", ""] + [f"- {f}" for f in failures] + [""]
    else:
        lines += [f"STEP 0 CHECKER: PASS — {mkt} inputs match the stated CAD artifacts.", ""]
    return lines, failures


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--market", default="CAD")
    ap.add_argument("--out", default=str(REPORTS / "wi009c_inputs.txt"))
    args = ap.parse_args()

    lines, failures = check_market(args.market)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    if failures:
        print(f"[check_wi009c_inputs] {len(failures)} failure(s) — see {out}", file=sys.stderr)
        return 1
    print(f"[check_wi009c_inputs] PASS — wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
