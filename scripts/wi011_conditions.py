"""WI-011 Step 2 — build the condition panel and write its definitions report.

Streams the CAD symbols one at a time (never an all-ticker uncompressed frame),
computes the trailing conditions declared in `src/wi011/conditions.py`, and writes
`reports/wi011_condition_definitions.md` with the formulas, lookbacks, warm-up
handling and firing counts.

Markers the plan's verify command greps for:

    POINT_IN_TIME: PASS
    CONDITION_COUNT: <n>

`POINT_IN_TIME` is only written PASS after a *runtime* causality spot-check on
real CAD bars (5 symbols, truncated-frame recomputation) on top of the unit
tests in `tests/test_wi011_conditions.py` — the marker is evidence, not policy.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.feature_engine import iter_market_symbols  # noqa: E402
from src.wi011 import HORIZONS, MARKET  # noqa: E402
from src.wi011.conditions import (  # noqa: E402
    CONDITION_SPECS,
    PCTILE_MIN_PERIODS,
    add_state_columns,
    compute_conditions,
    load_selected_indicators,
)
from src.wi011.panel import ANALYSIS_START, build_condition_panel, panel_coverage  # noqa: E402

REPORT = BASE_DIR / "reports" / "wi011_condition_definitions.md"
SPOT_CHECK_SYMBOLS = 5
SPOT_CHECK_TAIL = 3  # bars truncated away in the recomputation check


def point_in_time_spot_check(market: str = MARKET, n_symbols: int = SPOT_CHECK_SYMBOLS) -> tuple[bool, list[str]]:
    """Truncated-frame recomputation on real bars: does row t survive losing t+1..?

    For each of the first `n_symbols` symbols, the condition row at the cut is
    recomputed from data up to the cut only and compared element-wise with the
    row from the full-history computation. Any difference is a lookahead bug.
    """
    notes: list[str] = []
    ok = True
    checked = 0
    for symbol, raw in iter_market_symbols(market, min_date=None, allow_fixture=False):
        g = raw.sort_values("date").reset_index(drop=True)
        if len(g) < 300:
            continue
        full_state = add_state_columns(g)
        full = compute_conditions(full_state)
        cut = len(g) - SPOT_CHECK_TAIL
        trunc_state = add_state_columns(g.iloc[:cut].reset_index(drop=True))
        trunc = compute_conditions(trunc_state)

        cols = [s.name for s in CONDITION_SPECS]
        a = full[cols].iloc[cut - 1].to_numpy(dtype="float64")
        b = trunc[cols].iloc[cut - 1].to_numpy(dtype="float64")
        same = np.array_equal(np.isnan(a), np.isnan(b)) and np.array_equal(np.nan_to_num(a), np.nan_to_num(b))
        state_cols = ["mom_12_1", "rev_1m", "vol_20", "amihud_20", "atr_pct_20", "er_20", "ols_slope_20", "ch52_pos"]
        sa = full_state[state_cols].iloc[cut - 1].to_numpy(dtype="float64")
        sb = trunc_state[state_cols].iloc[cut - 1].to_numpy(dtype="float64")
        state_same = np.allclose(sa, sb, rtol=0, atol=0, equal_nan=True)
        ok = ok and same and state_same
        notes.append(f"- `{symbol}` @ {str(g['date'].iloc[cut - 1].date())}: conditions {'match' if same else 'DIFFER'}, "
                     f"state columns {'match' if state_same else 'DIFFER'}")
        checked += 1
        if checked >= n_symbols:
            break
    if checked == 0:
        return False, ["- no symbol long enough for the spot check"]
    return ok, notes


def _condition_table(panel: pd.DataFrame) -> tuple[list[str], int]:
    specs = {s.name: s for s in CONDITION_SPECS}
    extra = [c for c in panel.columns if c.startswith("ind_")]
    rows = []
    total = 0
    for name in [s.name for s in CONDITION_SPECS] + sorted(extra):
        v = panel[name].to_numpy(dtype="float64")
        defined = np.isfinite(v)
        fires = (v > 0.5) & defined
        n_fire = int(fires.sum())
        total += n_fire
        spec = specs.get(name)
        formula = spec.formula if spec else "Step 3-selected indicator in its own-history extreme tail"
        lookback = spec.lookback if spec else "252d"
        rows.append(
            f"| `{name}` | {formula} | {lookback} | {n_fire:,} | {int(defined.sum()):,} | "
            f"{100.0 * n_fire / max(int(defined.sum()), 1):.1f}% |"
        )
    return rows, total


def main() -> int:
    indicators = load_selected_indicators()
    panel = build_condition_panel(MARKET)
    cov = panel_coverage(panel)

    cond_cols = [c for c in panel.columns if not c.startswith(("fwd_", "tret", "spread", "dollar_vol", "close"))]
    cond_cols = [
        c
        for c in panel.columns
        if c in {s.name for s in CONDITION_SPECS} or c.startswith("ind_")
    ]
    dtypes_ok = all(str(panel[c].dtype) == "float32" for c in cond_cols)
    float32_ok = dtypes_ok and all(
        str(panel[c].dtype) == "float32"
        for c in panel.columns
        if c.startswith(("fwd_", "spread_", "tret_")) or c in ("atr_pct_20", "er_20", "ols_slope_20", "ols_r2_20")
    )

    ok_pit, pit_notes = point_in_time_spot_check(MARKET)
    cond_rows, total_fires = _condition_table(panel)

    lines = [
        "# WI-011 Step 2 — trailing condition definitions (CAD)",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Panel: {cov['rows']:,} rows · {cov['symbols']} symbols · {cov['dates']} dates "
        f"({cov['first_date']} → {cov['last_date']})",
        f"- Analysis window: `date >= {ANALYSIS_START}` (the CAD feature/target panel start, "
        "`reports/wi011_preflight.md`); raw history is read in full so long lookbacks warm up first.",
        "- Built by sequential per-symbol iteration (`src/wi011/panel.py`); no all-ticker "
        "uncompressed frame; calculated columns cast to float32 immediately.",
        "",
        "## Condition vocabulary",
        "",
        f"CONDITION_COUNT: {len(cond_cols)}",
        f"- declared atomic conditions: {len([s for s in CONDITION_SPECS if s.family != 'cross'])}",
        f"- declared cross conditions: {len([s for s in CONDITION_SPECS if s.family == 'cross'])}",
        f"- Step-3-selected indicator conditions: {len([c for c in cond_cols if c.startswith('ind_')])}"
        + (f" (from `reports/wi011_selected_indicators.json`: {', '.join(indicators)})" if indicators else " (no selection file yet)"),
        f"- total condition firings in the panel: {total_fires:,}",
        "",
        "Three-valued semantics: `1.0` fires, `0.0` defined and does not fire, **`NaN` = undefined** "
        "(warm-up / insufficient history). Warm-up rows are preserved — never coerced to 0 — and "
        "every downstream step masks on `isfinite` per condition.",
        "",
        "| Condition | Formula (all trailing, point-in-time) | Lookback | Firings | Defined rows | Fire rate |",
        "| :--- | :--- | ---: | ---: | ---: | ---: |",
    ]
    lines += cond_rows

    lines += [
        "",
        "## Inputs",
        "",
        "- E5 primitives, byte-for-byte the `src/factors/e5_baseline` definitions: `mom_12_1`, "
        "`rev_1m`, `vol_20`, `amihud_20`, `log_dollar_vol_20`.",
        "- `src/targets.wilder_atr(20)` for ATR% and the ATR-multiple forward label.",
        "- Trailing OLS slope/R² of log close over 20d, KAMA efficiency ratio over 20d "
        "(`src/feature_engine._efficiency_ratio` semantics), trailing 50d MA, 52-week "
        "(252d) high/low channel from daily high/low.",
        f"- Own-history percentiles (`vol_low`, `vol_high`, `liq_*`, `dollarvol_high`): percentile rank "
        f"of the current value inside its trailing 252-day window, requiring a full window and at "
        f"least {PCTILE_MIN_PERIODS} finite observations inside it.",
        "- Fixed thresholds declared before evaluation (never tuned on forward returns): "
        "R² floor 0.30, efficiency ratio 0.50/0.30, percentile thirds 0.33/0.67, channel 0.20/0.80.",
        "",
        "## Warm-up handling",
        "",
        "- Conditions depending on a 252-day window are undefined for a symbol's first 251 bars; "
        "`mom_12_1` needs 252 bars + 21 for its skip, so momentum conditions warm up later still.",
        "- Effects are visible in the `Defined rows` column above and are reported, not imputed. "
        "Symbols whose raw history starts in 2021 contribute their first usable condition rows only "
        "from ~2022 onward.",
        "- Forward labels (`fwd_ret_h`, `fwd_atr_ret_h`) are NaN for the last h bars of each symbol; "
        "they are labels measured by the expectancy step and are never an input to any condition.",
        "",
        "## Causality evidence",
        "",
        f"POINT_IN_TIME: {'PASS' if ok_pit else 'FAIL'}",
        "",
        "Runtime spot-check — recompute each symbol's conditions from a frame truncated "
        f"{SPOT_CHECK_TAIL} bars early and compare the cut row element-wise:",
        "",
    ]
    lines += pit_notes
    lines += [
        "",
        "Plus `tests/test_wi011_conditions.py` (15 tests): future-bar perturbation leaves earlier "
        "conditions bit-identical; truncated recomputation reproduces the live row; the last bar is "
        "condition-defined from history alone; forward labels *do* change when the future changes "
        "(harness sanity); the Corwin-Schultz cost input is lagged to bars (t-1, t).",
        "",
        "## Dtypes / build discipline",
        "",
        f"- every condition column float32: **{'PASS' if dtypes_ok else 'FAIL'}**",
        f"- every calculated label/state/cost column float32: **{'PASS' if float32_ok else 'FAIL'}**",
        "- horizons available as labels: " + ", ".join(f"`{h}d`" for h in HORIZONS),
        "",
        "## Status",
        "",
        "Data-only condition definitions — no trade labels, no model, no threshold tuned against "
        "forward returns. Step 3 consumes this vocabulary for the indicator-association pass.",
    ]

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")
    print(f"[wi011_conditions] wrote {REPORT} (conditions={len(cond_cols)}, pit={'PASS' if ok_pit else 'FAIL'})")
    return 0 if (ok_pit and dtypes_ok and float32_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())