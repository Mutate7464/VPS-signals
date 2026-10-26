"""WI-011 Step 2 — trailing, point-in-time per-symbol condition definitions.

Why this module exists
----------------------
WI-011 is a condition-first meta-analysis: instead of asking "does a model rank
tickers", it asks "is there a *state* a name can be observed to be in, at time t,
using only data at or before t, whose forward return distribution has measurable
net expectancy?" Everything that turns raw OHLCV into those states lives here so
the point-in-time property can be unit-tested on synthetic bars without touching
the CAD parquets.

Causality contract (enforced by `tests/test_wi011_conditions.py`)
----------------------------------------------------------------
* Every primitive is trailing: OLS over `[t-w+1 .. t]`, rolling percentile of the
  value at `t` within `[t-251 .. t]`, moving averages through `t`, i.e. nothing
  reads `t+1` or later.
* Conditions are three-valued `float32`: ``1.0`` fires, ``0.0`` is defined and
  does not fire, ``NaN`` means *undefined* — warm-up or insufficient history.
  Warm-up rows are preserved, never silently coerced to 0.
* Recomputing on a truncated frame (data up to t only) reproduces the same row
  at t: future observations can never change an earlier condition.

Primitive sources
-----------------
* E5 primitives, byte-for-byte the definitions in `src.factors.e5_baseline`
  (`mom_12_1`, `rev_1m`, `vol_20`, `amihud_20`, `log_dollar_vol_20`).
* `src.targets.wilder_atr` for the ATR-based volatility state.
* `src.feature_engine._efficiency_ratio` semantics for the KAMA efficiency ratio
  (re-implemented here on numpy so this module has no feature-engine side
  effects; `tests/test_wi011_conditions.py` pins the equivalence).
* Trailing OLS slope/R^2 on log close and the 52-week channel from daily
  high/low, mirroring the `src.targets` trend primitive.

The Step 3 hook
---------------
`compute_conditions(..., indicator_states=...)` accepts the compact indicator
subset selected empirically in Step 3
(`reports/wi011_selected_indicators_{market}.json`; WI-013 made the selection
market-specific) and adds one `ind_<name>_low` / `ind_<name>_high` own-history-percentile
condition per selected indicator. The E5 primitives and OHLCV-derived states are
always present; the 89-feature panel is never used wholesale.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

from src.feature_engine import _efficiency_ratio
from src.targets import ATR_WINDOW, wilder_atr

__all__ = [
    "ATOMIC_SPECS",
    "CONDITION_SPECS",
    "CROSS_SPECS",
    "DEFAULT_SELECTION_PATH",
    "INDICATOR_PCTILE_LOOKBACK",
    "INDICATOR_PCTILE_MIN_PERIODS",
    "LOAD_INDICATOR_COLUMNS",
    "PCTILE_LOOKBACK",
    "PCTILE_MIN_PERIODS",
    "ConditionSpec",
    "TREND_MIN_R2",
    "add_e5_primitives",
    "add_state_columns",
    "compute_conditions",
    "efficiency_ratio_20",
    "indicator_condition_names",
    "load_selected_indicators",
    "rolling_percentile_last",
    "selection_path",
    "trailing_ols_slope_r2",
]

# --------------------------------------------------------------------------- #
# Fixed thresholds (declared a priori — never tuned against forward returns)
# --------------------------------------------------------------------------- #
TREND_MIN_R2 = 0.30
"""Trailing-OLS R^2 floor that separates a directional trend from chop."""

ER_TRENDING = 0.50
ER_CHOPPY = 0.30

PCTILE_LOOKBACK = 252
"""Own-history percentile window (one trading year) for volatility/liquidity."""

PCTILE_MIN_PERIODS = 60
"""Minimum finite observations before an own-history percentile is defined."""

VOL_LOW_Q = 0.33
VOL_HIGH_Q = 0.67
LIQ_LOW_Q = 0.33
LIQ_HIGH_Q = 0.67

CHANNEL_LOOKBACK = 252
CHANNEL_HIGH = 0.80
CHANNEL_LOW = 0.20

MA_WINDOW = 50
OLS_WINDOW = 20
ER_WINDOW = 20

INDICATOR_PCTILE_LOOKBACK = 252
INDICATOR_PCTILE_MIN_PERIODS = 60
INDICATOR_EXTREME_LOW = 0.20
INDICATOR_EXTREME_HIGH = 0.80

REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"
DEFAULT_SELECTION_STEM = "wi011_selected_indicators"
DEFAULT_SELECTION_PATH = REPORTS_DIR / f"{DEFAULT_SELECTION_STEM}.json"
"""Legacy market-less selection path — read-only, never written by WI-013 code."""


def selection_path(market: str) -> Path:
    """The Step 3 selection JSON for one market (`reports/wi011_selected_indicators_{market}.json`)."""
    return REPORTS_DIR / f"{DEFAULT_SELECTION_STEM}_{str(market).upper()}.json"

LOAD_INDICATOR_COLUMNS: tuple[str, ...] = ("close", "high", "low", "volume")


# --------------------------------------------------------------------------- #
# Condition vocabulary (declared before any expectancy is computed)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ConditionSpec:
    """One declared condition: name, family, formula text, lookback text."""

    name: str
    family: str
    formula: str
    lookback: str


ATOMIC_SPECS: tuple[ConditionSpec, ...] = (
    ConditionSpec("trend_up", "trend", "trailing OLS slope of log close > 0 and R^2 >= 0.30", f"{OLS_WINDOW}d"),
    ConditionSpec("trend_down", "trend", "trailing OLS slope of log close < 0 and R^2 >= 0.30", f"{OLS_WINDOW}d"),
    ConditionSpec("trend_chop", "trend", "trailing OLS R^2 < 0.30 (no explained direction)", f"{OLS_WINDOW}d"),
    ConditionSpec("er_trending", "trend", "KAMA efficiency ratio >= 0.50", f"{ER_WINDOW}d"),
    ConditionSpec("er_choppy", "trend", "KAMA efficiency ratio < 0.30", f"{ER_WINDOW}d"),
    ConditionSpec("vol_low", "volatility", f"trailing percentile of ATR% <= {VOL_LOW_Q:.2f}", f"{PCTILE_LOOKBACK}d"),
    ConditionSpec("vol_high", "volatility", f"trailing percentile of ATR% >= {VOL_HIGH_Q:.2f}", f"{PCTILE_LOOKBACK}d"),
    ConditionSpec("liq_illiquid", "liquidity", f"trailing percentile of E5 amihud_20 >= {LIQ_HIGH_Q:.2f}", f"{PCTILE_LOOKBACK}d"),
    ConditionSpec("liq_liquid", "liquidity", f"trailing percentile of E5 amihud_20 <= {LIQ_LOW_Q:.2f}", f"{PCTILE_LOOKBACK}d"),
    ConditionSpec("dollarvol_high", "liquidity", "trailing percentile of E5 log_dollar_vol_20 >= 0.67", f"{PCTILE_LOOKBACK}d"),
    ConditionSpec("above_ma_50", "position", f"close > trailing {MA_WINDOW}d simple moving average", f"{MA_WINDOW}d"),
    ConditionSpec("below_ma_50", "position", f"close < trailing {MA_WINDOW}d simple moving average", f"{MA_WINDOW}d"),
    ConditionSpec("ch52_high", "position", "position in 52-week high/low channel >= 0.80", f"{CHANNEL_LOOKBACK}d"),
    ConditionSpec("ch52_low", "position", "position in 52-week high/low channel <= 0.20", f"{CHANNEL_LOOKBACK}d"),
    ConditionSpec("mom_pos", "position", "E5 mom_12_1 > 0 (252d/21d trailing momentum)", "252d"),
    ConditionSpec("mom_neg", "position", "E5 mom_12_1 < 0", "252d"),
    ConditionSpec("rev1m_pos", "position", "E5 rev_1m > 0 (21d trailing return)", "21d"),
    ConditionSpec("rev1m_neg", "position", "E5 rev_1m < 0", "21d"),
)

CROSS_SPECS: tuple[ConditionSpec, ...] = (
    ConditionSpec("trend_up_vol_high", "cross", "trend_up AND vol_high", "20d + 252d"),
    ConditionSpec("trend_up_vol_low", "cross", "trend_up AND vol_low", "20d + 252d"),
    ConditionSpec("trend_down_vol_high", "cross", "trend_down AND vol_high", "20d + 252d"),
    ConditionSpec("trend_down_vol_low", "cross", "trend_down AND vol_low", "20d + 252d"),
    ConditionSpec("ch52_high_vol_low", "cross", "ch52_high AND vol_low", "252d"),
    ConditionSpec("ch52_low_vol_high", "cross", "ch52_low AND vol_high", "252d"),
    ConditionSpec("above_ma_50_liq_illiquid", "cross", "above_ma_50 AND liq_illiquid", "50d + 252d"),
    ConditionSpec("mom_pos_liq_illiquid", "cross", "mom_pos AND liq_illiquid", "252d"),
)

CONDITION_SPECS: tuple[ConditionSpec, ...] = ATOMIC_SPECS + CROSS_SPECS
"""The full declared vocabulary before the Step 3 indicator subset is applied."""


# --------------------------------------------------------------------------- #
# Trailing primitives
# --------------------------------------------------------------------------- #
def trailing_ols_slope_r2(log_close: np.ndarray, window: int = OLS_WINDOW) -> tuple[np.ndarray, np.ndarray]:
    """Causal OLS slope and R^2 of `x` regressed on time over `[t-w+1 .. t]`.

    Mirrors `src.targets._ols_forward_slope_r2` but on the *trailing* window: row
    `t` (>= window-1) carries the fit of the window ending at `t`. Rows with an
    incomplete window are NaN. Degenerate windows (zero variance) give NaN R^2.
    """
    a = np.asarray(log_close, dtype="float64")
    n = a.size
    slope = np.full(n, np.nan)
    r2 = np.full(n, np.nan)
    if n < window:
        return slope, r2

    sw = sliding_window_view(a, window)  # sw[i] = a[i .. i+window-1]
    x = np.arange(window, dtype="float64")
    xc = x - x.mean()
    denom = float((xc ** 2).sum())

    ybar = sw.mean(axis=1)
    yc = sw - ybar[:, None]
    s = (yc @ xc) / denom

    yhat = ybar[:, None] + s[:, None] * xc[None, :]
    sse = ((sw - yhat) ** 2).sum(axis=1)
    sst = (yc ** 2).sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = 1.0 - sse / sst
    r = np.where(sst == 0.0, np.nan, r)

    slope[window - 1 :] = s
    r2[window - 1 :] = r
    return slope, r2


def rolling_percentile_last(
    x: np.ndarray,
    window: int = PCTILE_LOOKBACK,
    min_periods: int = PCTILE_MIN_PERIODS,
) -> np.ndarray:
    """Causal percentile rank of `x[t]` inside the trailing window `[t-w+1 .. t]`.

    Returns ``mean(window <= x[t])`` over the finite values of that window — 1.0
    means the current value is at/above every trailing observation. Defined only
    when `t` has a full window and at least `min_periods` finite values; NaN
    otherwise (warm-up preserved). The current value is part of its own window,
    so the minimum defined percentile is `1/min_periods`.
    """
    a = np.asarray(x, dtype="float64")
    n = a.size
    out = np.full(n, np.nan)
    if n == 0:
        return out
    w = min(int(window), n)
    if w < min_periods:
        return out

    sw = sliding_window_view(a, w)
    last = sw[:, -1]
    finite = np.isfinite(sw)
    nfin = finite.sum(axis=1)
    le = (finite & (sw <= last[:, None])).sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        pct = le / nfin
    ok = (nfin >= min_periods) & np.isfinite(last)
    pct = np.where(ok, pct, np.nan)

    out[w - 1 :] = pct
    return out


def efficiency_ratio_20(close: pd.Series, window: int = ER_WINDOW) -> pd.Series:
    """KAMA efficiency ratio, identical in form to `src.feature_engine._efficiency_ratio`."""
    return _efficiency_ratio(close.astype("float64"), window)


def add_e5_primitives(df: pd.DataFrame) -> pd.DataFrame:
    """Add the five E5 factor primitives, byte-for-byte as `src.factors.e5_baseline`.

    `df` must be one symbol, sorted by date, on a clean RangeIndex.
    """
    close = df["close"].astype("float64")
    ret = close.pct_change()
    dollar_vol = (close * df["volume"].astype("float64")) + 1e-12
    out = df.copy()
    out["mom_12_1"] = close.shift(21) / close.shift(252) - 1.0
    out["rev_1m"] = close / close.shift(21) - 1.0
    out["vol_20"] = ret.rolling(20, min_periods=20).std(ddof=1)
    out["amihud_20"] = (ret.abs() / dollar_vol).rolling(20, min_periods=20).mean()
    out["log_dollar_vol_20"] = np.log(dollar_vol).rolling(20, min_periods=20).mean()
    return out


def add_state_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add every trailing primitive the declared conditions are built from.

    Adds (all causal, all float32 after `cast_state_frame`): `atr_pct_20`,
    `er_20`, `ols_slope_20`, `ols_r2_20`, `ma_50`, `ch52_pos`, the three
    own-history percentiles and the five E5 primitives.
    """
    out = add_e5_primitives(df)
    close = out["close"].astype("float64")
    high = out["high"].astype("float64")
    low = out["low"].astype("float64")

    atr = wilder_atr(out, ATR_WINDOW).astype("float64")
    out["atr_pct_20"] = atr / (close + 1e-12)

    out["er_20"] = efficiency_ratio_20(close, ER_WINDOW)
    slope, r2 = trailing_ols_slope_r2(np.log(close.to_numpy()), OLS_WINDOW)
    out["ols_slope_20"] = slope
    out["ols_r2_20"] = r2

    out["ma_50"] = close.rolling(MA_WINDOW, min_periods=MA_WINDOW).mean()

    hh = high.rolling(CHANNEL_LOOKBACK, min_periods=CHANNEL_LOOKBACK).max()
    ll = low.rolling(CHANNEL_LOOKBACK, min_periods=CHANNEL_LOOKBACK).min()
    out["ch52_pos"] = (close - ll) / (hh - ll + 1e-12)

    out["atr_pct_pctile_252"] = rolling_percentile_last(out["atr_pct_20"].to_numpy())
    out["amihud_pctile_252"] = rolling_percentile_last(out["amihud_20"].to_numpy())
    out["dollarvol_pctile_252"] = rolling_percentile_last(out["log_dollar_vol_20"].to_numpy())
    return out


# --------------------------------------------------------------------------- #
# Three-valued condition construction
# --------------------------------------------------------------------------- #
def _tri(mask: np.ndarray, defined: np.ndarray) -> np.ndarray:
    """1.0 where `mask`, 0.0 where `defined and not mask`, NaN where not defined."""
    m = np.asarray(mask, dtype=bool)
    d = np.asarray(defined, dtype=bool)
    out = np.where(d, np.where(m, 1.0, 0.0), np.nan)
    return out.astype("float32")


def _and(*conds: np.ndarray) -> np.ndarray:
    """Conjunction over three-valued conditions; NaN if any component is NaN."""
    arrs = [np.asarray(c, dtype="float64") for c in conds]
    defined = np.ones(arrs[0].shape, dtype=bool)
    for a in arrs:
        defined &= np.isfinite(a)
    all_fire = np.ones(arrs[0].shape, dtype=bool)
    for a in arrs:
        all_fire &= np.nan_to_num(a, nan=0.0) > 0.5
    return _tri(all_fire, defined)


def _finite(*series: pd.Series) -> np.ndarray:
    """Element-wise finiteness across one or more Series."""
    out = np.ones(len(series[0]), dtype=bool)
    for s in series:
        out &= np.isfinite(np.asarray(s, dtype="float64"))
    return out


def compute_conditions(
    state: pd.DataFrame,
    indicator_states: dict[str, pd.Series] | None = None,
) -> pd.DataFrame:
    """Build every declared condition for one symbol's state frame.

    Args:
        state: output of `add_state_columns` for one symbol (sorted by date).
        indicator_states: optional mapping `indicator -> trailing percentile`
            Series (Step 3 selected subset); each adds `ind_<name>_low` and
            `ind_<name>_high` conditions.

    Returns:
        float32 DataFrame of 1.0/0.0/NaN conditions, one row per input row.
    """
    close = state["close"].astype("float64")
    ma50 = state["ma_50"].astype("float64")
    slope = state["ols_slope_20"].astype("float64")
    r2 = state["ols_r2_20"].astype("float64")
    er = state["er_20"].astype("float64")

    trend_def = _finite(slope, r2)
    trend_up = _tri((slope > 0.0) & (r2 >= TREND_MIN_R2), trend_def)
    trend_down = _tri((slope < 0.0) & (r2 >= TREND_MIN_R2), trend_def)
    trend_chop = _tri(r2 < TREND_MIN_R2, trend_def)

    er_def = _finite(er)
    er_trending = _tri(er >= ER_TRENDING, er_def)
    er_choppy = _tri(er < ER_CHOPPY, er_def)

    atr_pct_pct = state["atr_pct_pctile_252"].astype("float64")
    vol_def = _finite(atr_pct_pct)
    vol_low = _tri(atr_pct_pct <= VOL_LOW_Q, vol_def)
    vol_high = _tri(atr_pct_pct >= VOL_HIGH_Q, vol_def)

    amihud_pct = state["amihud_pctile_252"].astype("float64")
    liq_def = _finite(amihud_pct)
    liq_illiquid = _tri(amihud_pct >= LIQ_HIGH_Q, liq_def)
    liq_liquid = _tri(amihud_pct <= LIQ_LOW_Q, liq_def)

    dvol_pct = state["dollarvol_pctile_252"].astype("float64")
    dollarvol_high = _tri(dvol_pct >= VOL_HIGH_Q, _finite(dvol_pct))

    px_def = _finite(close, ma50)
    above_ma_50 = _tri(close > ma50, px_def)
    below_ma_50 = _tri(close < ma50, px_def)

    ch = state["ch52_pos"].astype("float64")
    ch_def = _finite(ch)
    ch52_high = _tri(ch >= CHANNEL_HIGH, ch_def)
    ch52_low = _tri(ch <= CHANNEL_LOW, ch_def)

    mom = state["mom_12_1"].astype("float64")
    mom_def = _finite(mom)
    mom_pos = _tri(mom > 0.0, mom_def)
    mom_neg = _tri(mom < 0.0, mom_def)

    rev = state["rev_1m"].astype("float64")
    rev_def = _finite(rev)
    rev1m_pos = _tri(rev > 0.0, rev_def)
    rev1m_neg = _tri(rev < 0.0, rev_def)

    cols = {
        "trend_up": trend_up,
        "trend_down": trend_down,
        "trend_chop": trend_chop,
        "er_trending": er_trending,
        "er_choppy": er_choppy,
        "vol_low": vol_low,
        "vol_high": vol_high,
        "liq_illiquid": liq_illiquid,
        "liq_liquid": liq_liquid,
        "dollarvol_high": dollarvol_high,
        "above_ma_50": above_ma_50,
        "below_ma_50": below_ma_50,
        "ch52_high": ch52_high,
        "ch52_low": ch52_low,
        "mom_pos": mom_pos,
        "mom_neg": mom_neg,
        "rev1m_pos": rev1m_pos,
        "rev1m_neg": rev1m_neg,
    }
    cols["trend_up_vol_high"] = _and(cols["trend_up"], cols["vol_high"])
    cols["trend_up_vol_low"] = _and(cols["trend_up"], cols["vol_low"])
    cols["trend_down_vol_high"] = _and(cols["trend_down"], cols["vol_high"])
    cols["trend_down_vol_low"] = _and(cols["trend_down"], cols["vol_low"])
    cols["ch52_high_vol_low"] = _and(cols["ch52_high"], cols["vol_low"])
    cols["ch52_low_vol_high"] = _and(cols["ch52_low"], cols["vol_high"])
    cols["above_ma_50_liq_illiquid"] = _and(cols["above_ma_50"], cols["liq_illiquid"])
    cols["mom_pos_liq_illiquid"] = _and(cols["mom_pos"], cols["liq_illiquid"])

    specs = {s.name for s in CONDITION_SPECS}
    if set(cols) != specs:
        raise AssertionError(f"condition vocabulary drifted from CONDITION_SPECS: {set(cols) ^ specs}")

    for name, series in (indicator_states or {}).items():
        pct = np.asarray(series, dtype="float64")
        pct_def = np.isfinite(pct)
        cols[f"ind_{name}_low"] = _tri(pct <= INDICATOR_EXTREME_LOW, pct_def)
        cols[f"ind_{name}_high"] = _tri(pct >= INDICATOR_EXTREME_HIGH, pct_def)

    return pd.DataFrame(cols, index=state.index).astype("float32")


def indicator_condition_names(indicators) -> list[str]:
    """The two condition names each selected indicator contributes."""
    out: list[str] = []
    for name in indicators:
        out += [f"ind_{name}_low", f"ind_{name}_high"]
    return out


# --------------------------------------------------------------------------- #
# Step 3 selection hook
# --------------------------------------------------------------------------- #
def load_selected_indicators(
    market: str | None = None,
    path: Path | str | None = None,
) -> list[str]:
    """Read the Step 3 indicator subset; empty list when Step 3 has not run yet.

    Step 3 (`scripts/wi011_indicator_association.py`) writes the JSON with a
    `selected_indicators` list. Before that file exists, Step 2 runs on the E5
    primitives + OHLCV-derived state vocabulary only — which is exactly what the
    plan's ordering (Step 2 draft, then Step 1b subset) implies.

    Args:
        market: market code; the selection is read from that market's suffixed
            JSON (`reports/wi011_selected_indicators_{market}.json`). WI-013: the
            selection is market-specific, so a CAD run never reads a USD subset.
        path: explicit path override (wins over `market`).

    Raises:
        ValueError: when neither `market` nor `path` is given (the market-less
            default would resolve an ambiguous selection).
    """
    if path is None and market is None:
        raise ValueError("load_selected_indicators() needs a market (or an explicit path)")
    p = Path(path) if path is not None else selection_path(market)
    if not p.exists():
        return []
    payload = json.loads(p.read_text())
    sel = payload.get("selected_indicators", [])
    if not isinstance(sel, list):
        raise ValueError(f"{p}: selected_indicators must be a list, got {type(sel).__name__}")
    return [str(s) for s in sel]