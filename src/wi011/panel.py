"""WI-011 — sequential per-symbol analysis panel (conditions + forward returns).

Why this module exists
----------------------
Steps 2–6 all need the same object: for every CAD symbol, the trailing condition
states at each date, the forward returns at the eight fixed horizons, the Step 3
indicator subset states, and the cost proxies. Building it four times from raw
per-symbol parquets is cheap (minutes) and keeps every step reproducible from
source, with no cached artifact to go stale.

Host rules honoured here
------------------------
* Symbols are iterated **one at a time** and each symbol's frame is reduced to
  the analysis columns before being appended: no all-ticker uncompressed frame,
  no O(N x 89) feature read. Total panel is ~450k rows x ~60 float32 columns.
* Calculated columns are cast to `float32` immediately after computation.
* Rolling/percentile work is done per symbol on numpy sliding windows
  (`n_jobs` is irrelevant: single-threaded numpy, no joblib parallelism).

Causality
---------
Every column carried by the panel is either trailing (states, cost proxies,
trailing returns) or a *forward label* named `fwd_ret_h` / `fwd_atr_ret_h`. The
forward columns are labels only: they enter the expectancy step as the thing
being measured, never as an input to any condition (plan Step 2 "do NOT" clause).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.feature_engine import iter_market_symbols
from src.wi011 import HORIZONS
from src.wi011.conditions import (
    INDICATOR_PCTILE_LOOKBACK,
    INDICATOR_PCTILE_MIN_PERIODS,
    add_state_columns,
    compute_conditions,
    load_selected_indicators,
    rolling_percentile_last,
)

__all__ = [
    "ANALYSIS_START",
    "COST_COLUMNS",
    "TRALING_RET_WINDOWS",
    "attach_forward_returns",
    "build_condition_panel",
    "build_state_panel",
    "corwin_schultz_daily_spread",
    "load_indicator_map",
    "panel_coverage",
]

ANALYSIS_START = "2016-01-04"
"""First date of the feature/target panel (see `reports/wi011_preflight_{market}.md`).

Raw history is read in full so the 252-trading-day warm-ups complete before this
date; the panel is then trimmed here so Steps 2–6 share one timeline.
"""

TRALING_RET_WINDOWS: tuple[int, ...] = (5, 20, 60, 120)
"""Trailing own-return windows used by the Step 5 TS-momentum probe."""

COST_COLUMNS = (
    "close",
    "atr_pct_20",
    "dollar_vol_med_20",
    "spread_cs_bps_60",
    "spread_amihud_bps",
    "spread_bps_used",
)

STATE_COLUMNS = (
    "atr_pct_20",
    "er_20",
    "ols_slope_20",
    "ols_r2_20",
    "ma_50",
    "ch52_pos",
    "atr_pct_pctile_252",
    "amihud_pctile_252",
    "dollarvol_pctile_252",
    "mom_12_1",
    "rev_1m",
    "vol_20",
    "amihud_20",
    "log_dollar_vol_20",
)


# --------------------------------------------------------------------------- #
# Forward labels
# --------------------------------------------------------------------------- #
def attach_forward_returns(df: pd.DataFrame, horizons=HORIZONS) -> pd.DataFrame:
    """Add `fwd_ret_h` (relative) and `fwd_atr_ret_h` (ATR-multiple) label columns.

    `fwd_ret_h` = close.shift(-h)/close - 1 over the forward path [t+1 .. t+h];
    `fwd_atr_ret_h` divides the dollar move by the trailing Wilder ATR(20), the
    same units the E5 baseline and WI-009c use. Left as NaN where the forward
    window is incomplete (the last h rows of each symbol).
    """
    out = df.copy()
    close = out["close"].astype("float64").to_numpy()
    atr = (out["atr_pct_20"].astype("float64") * out["close"].astype("float64")).to_numpy()
    n = close.size
    for h in horizons:
        fwd = np.full(n, np.nan)
        if n > h:
            fwd[:-h] = close[h:]
        out[f"fwd_ret_{h}"] = ((fwd / close) - 1.0).astype("float32")
        out[f"fwd_atr_ret_{h}"] = ((fwd - close) / (atr + 1e-12)).astype("float32")
    return out


def attach_trailing_returns(df: pd.DataFrame, windows=TRALING_RET_WINDOWS) -> pd.DataFrame:
    """Add `tret_w` (own trailing return) and `tret_z_w` (vol-scaled, sqrt-time)."""
    out = df.copy()
    close = out["close"].astype("float64")
    vol = out["vol_20"].astype("float64")
    for w in windows:
        r = close / close.shift(w) - 1.0
        out[f"tret_{w}"] = r.astype("float32")
        scale = vol * np.sqrt(float(w))
        out[f"tret_z_{w}"] = (r / (scale + 1e-12)).astype("float32")
    return out


# --------------------------------------------------------------------------- #
# Cost proxies
# --------------------------------------------------------------------------- #
def corwin_schultz_daily_spread(high: pd.Series, low: pd.Series) -> np.ndarray:
    """Daily Corwin-Schultz (2012) high-low proportional spread estimate.

    Uses the two-day pair (t, t+1) to form the estimate for the *pair*, then the
    caller lags it by one bar so the value stored at row t is formed from bars
    (t-1, t) only — the causal correction the CS estimator needs to be usable as
    a point-in-time cost input. Negative alpha estimates are floored at 0 (the
    estimator's own lower bound, i.e. "no measurable spread").
    """
    h = np.asarray(high, dtype="float64")
    l = np.asarray(low, dtype="float64")
    n = h.size
    out = np.full(n, np.nan)
    if n < 2:
        return out
    with np.errstate(divide="ignore", invalid="ignore"):
        hl = np.log(h / l)
        h1, l1 = h[1:], l[1:]
        beta = hl[:-1] ** 2 + hl[1:] ** 2
        gamma = np.log(np.maximum(h[:-1], h1) / np.minimum(l[:-1], l1)) ** 2
        k = 3.0 - 2.0 * np.sqrt(2.0)
        alpha = (np.sqrt(2.0 * beta) - np.sqrt(beta)) / k - np.sqrt(gamma / k)
        s = 2.0 * (np.exp(alpha) - 1.0) / (1.0 + np.exp(alpha))
    s = np.where(np.isfinite(s), np.maximum(s, 0.0), np.nan)
    out[: n - 1] = s
    return out


def add_cost_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add the disclosed cost proxies (no forward data enters any of them).

    * `spread_cs_bps_60` — 60-day rolling median of the *lagged* Corwin-Schultz
      proportional spread, in bps. NaN when the estimator is undefined for the
      whole window (common for very illiquid or gap-heavy names).
    * `spread_amihud_bps` — Amihud-proportional fallback/cross-check,
      `2 * sqrt(amihud_20) * 1e4`, clipped to [0.5, 200] bps.
    * `spread_bps_used` — CS median where usable (> 0), else the Amihud proxy.
    * `dollar_vol_med_20` — median daily dollar volume, used only to convert the
      per-order IBKR commission into bps of a fixed notional.
    """
    out = df.copy()
    cs_daily = corwin_schultz_daily_spread(out["high"], out["low"])
    cs_lagged = np.concatenate([[np.nan], cs_daily[:-1]])  # causal: uses bars (t-1, t)
    cs_series = pd.Series(cs_lagged, index=out.index)
    out["spread_cs_bps_60"] = (cs_series.rolling(60, min_periods=40).median() * 1e4).astype("float32")

    amihud = out["amihud_20"].astype("float64")
    prx = np.clip(2.0 * np.sqrt(np.maximum(amihud.to_numpy(), 0.0)) * 1e4, 0.5, 200.0)
    out["spread_amihud_bps"] = np.where(np.isfinite(amihud.to_numpy()), prx, np.nan).astype("float32")

    cs = out["spread_cs_bps_60"].to_numpy(dtype="float64")
    used = np.where(np.isfinite(cs) & (cs > 0.0), cs, out["spread_amihud_bps"].to_numpy(dtype="float64"))
    out["spread_bps_used"] = used.astype("float32")

    dv = (out["close"].astype("float64") * out["volume"].astype("float64"))
    out["dollar_vol_med_20"] = dv.rolling(20, min_periods=20).median().astype("float32")
    return out


# --------------------------------------------------------------------------- #
# Step 3 indicator subset (attached only when the selection exists)
# --------------------------------------------------------------------------- #
def load_indicator_map(columns, market: str) -> dict[str, pd.DataFrame]:
    """Read the selected indicator columns once, keyed by symbol.

    A handful of columns (the Step 3 subset), not the 89-column panel: the
    per-date cross-sectional percentiles are already stored in the parquet, and
    only the *own-history* percentile is recomputed here, causally.
    """
    if not columns:
        return {}
    path = f"data/features/features_{market}.parquet"
    frame = pd.read_parquet(path, columns=["date", "symbol", *columns])
    frame["date"] = pd.to_datetime(frame["date"])
    return {sym: g.reset_index(drop=True) for sym, g in frame.groupby("symbol", sort=False)}


def _attach_indicator_states(df: pd.DataFrame, ind_df: pd.DataFrame, columns) -> tuple[pd.DataFrame, dict]:
    """Left-join the indicator values on date and compute their trailing percentiles."""
    merged = df.merge(ind_df, on="date", how="left", suffixes=("", "_ind"))
    states: dict[str, pd.Series] = {}
    for c in columns:
        vals = merged[c].astype("float64")
        states[c] = pd.Series(
            rolling_percentile_last(
                vals.to_numpy(),
                INDICATOR_PCTILE_LOOKBACK,
                INDICATOR_PCTILE_MIN_PERIODS,
            ),
            index=merged.index,
        )
        merged[c] = vals.astype("float32")
    return merged, states


# --------------------------------------------------------------------------- #
# Panel builders
# --------------------------------------------------------------------------- #
def _symbol_frame(
    symbol: str,
    raw: pd.DataFrame,
    indicator_map: dict[str, pd.DataFrame],
    indicator_columns,
    keep_conditions: bool,
    market: str,
    keep_only: set[str] | None = None,
) -> pd.DataFrame | None:
    """Build one symbol's panel rows (state + conditions + labels + costs)."""
    g = raw.sort_values("date").reset_index(drop=True)
    state = add_state_columns(g)

    ind_states: dict[str, pd.Series] = {}
    if indicator_columns:
        ind_df = indicator_map.get(symbol)
        if ind_df is not None and not ind_df.empty:
            state, ind_states = _attach_indicator_states(state, ind_df, indicator_columns)
        else:
            for c in indicator_columns:
                state[c] = np.float32(np.nan)
            ind_states = {c: pd.Series(np.full(len(state), np.nan)) for c in indicator_columns}

    conds = compute_conditions(state, ind_states)
    out = pd.concat([state, conds], axis=1) if keep_conditions else state
    out = attach_forward_returns(out)
    out = attach_trailing_returns(out)
    out = add_cost_columns(out)
    out["symbol"] = symbol
    out["market"] = market

    keep = ["date", "symbol", "market"] + list(STATE_COLUMNS) + list(COST_COLUMNS)
    keep += list(TRALING_RET_WINDOWS and [f"tret_{w}" for w in TRALING_RET_WINDOWS])
    keep += [f"tret_z_{w}" for w in TRALING_RET_WINDOWS]
    if keep_conditions:
        keep += [c for c in conds.columns]
    keep += list(indicator_columns)
    keep += [f"fwd_ret_{h}" for h in HORIZONS] + [f"fwd_atr_ret_{h}" for h in HORIZONS]
    keep = [c for c in dict.fromkeys(keep) if c in out.columns]
    if keep_only is not None:
        keep = [c for c in keep if c in keep_only or c in ("date", "symbol", "market")]
    out = out[keep]

    # Plan discipline: every calculated column is float32 *immediately* (the raw
    # primitives come out of float64 pandas/numpy math, the conditions out of
    # `compute_conditions` are already float32).
    for c in out.columns:
        if c not in ("date", "symbol", "market"):
            out[c] = out[c].astype("float32")

    out = out[out["date"] >= pd.Timestamp(ANALYSIS_START)]
    if out.empty:
        return None
    return out.reset_index(drop=True)


def build_condition_panel(
    market: str,
    selected_indicators: list[str] | None = None,
    keep_only: set[str] | None = None,
) -> pd.DataFrame:
    """Stream every symbol of one market and return the stacked analysis panel.

    Args:
        market: market code (`USD` or `CAD`) — required since WI-013; the panel
            carries it in its `market` column and reads only that market's raw
            bars and indicator columns.
        selected_indicators: Step 3 indicator subset; `None` reads
            `reports/wi011_selected_indicators_{market}.json` when it exists
            (and uses no panel indicators otherwise).
        keep_only: optional column allow-list (plus keys) applied per symbol
            before stacking, so a step that needs a handful of columns never
            materialises the full panel.
    """
    indicators = load_selected_indicators(market) if selected_indicators is None else list(selected_indicators)
    indicator_map = load_indicator_map(indicators, market)
    parts: list[pd.DataFrame] = []
    for symbol, raw in iter_market_symbols(str(market).upper(), min_date=None, allow_fixture=False):
        frame = _symbol_frame(
            symbol, raw, indicator_map, indicators, keep_conditions=True, market=str(market).upper(),
            keep_only=keep_only,
        )
        if frame is not None:
            parts.append(frame)
    if not parts:
        raise RuntimeError(f"no {market} symbols survived the panel build")
    panel = pd.concat(parts, ignore_index=True)
    panel["date"] = pd.to_datetime(panel["date"])
    return panel


def build_state_panel(market: str, selected_indicators: list[str] | None = None) -> pd.DataFrame:
    """Panel without the forward labels: states + conditions only (Step 3 use)."""
    indicators = load_selected_indicators(market) if selected_indicators is None else list(selected_indicators)
    indicator_map = load_indicator_map(indicators, market)
    parts: list[pd.DataFrame] = []
    for symbol, raw in iter_market_symbols(str(market).upper(), min_date=None, allow_fixture=False):
        frame = _symbol_frame(
            symbol, raw, indicator_map, indicators, keep_conditions=True, market=str(market).upper(),
        )
        if frame is not None:
            parts.append(frame)
    if not parts:
        raise RuntimeError(f"no {market} symbols survived the panel build")
    panel = pd.concat(parts, ignore_index=True)
    panel["date"] = pd.to_datetime(panel["date"])
    return panel


def panel_coverage(panel: pd.DataFrame) -> dict:
    """Rows / symbols / dates for the report headers."""
    return {
        "rows": int(len(panel)),
        "symbols": int(panel["symbol"].nunique()),
        "dates": int(panel["date"].nunique()),
        "first_date": str(panel["date"].min().date()),
        "last_date": str(panel["date"].max().date()),
    }