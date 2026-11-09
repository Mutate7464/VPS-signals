"""WI-032 step 1 — swing-event sampling + 3-class first-touch labels (D-021 §1/§2).

Trailing (causal) fib-swing extremes:
* ``at_bottom`` — bar low is the trailing ``SWING_WINDOW``-bar minimum;
* ``at_top``    — bar high is the trailing ``SWING_WINDOW``-bar maximum;
kept with a ``CLUSTER_GAP``-bar spacing per side (no lookahead anywhere).

Each event is labelled by the first touch of ``close_t ± k·ATR_t`` within the
vertical barrier (geometry from `src.wi016.triple_barrier`):

* at_bottom (implied long):  profit ``+k·ATR`` → BUY, stop ``−k·ATR`` → SELL;
* at_top   (implied short): profit ``−k·ATR`` → SELL, stop ``+k·ATR`` → BUY;
* vertical-barrier touch (survives the horizon) → HOLD.

Symbol-sequential, float32, no all-ticker uncompressed frame (2 vCPU host).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.feature_engine import iter_market_symbols
from src.targets import wilder_atr

SWING_WINDOW = 21
CLUSTER_GAP = 10
BARRIERS: tuple[int, int] = (21, 55)
K_VALUES: tuple[float, ...] = (1.5, 2.0)
HOLD, BUY, SELL = 0, 1, 2
STATES: tuple[str, ...] = ("at_bottom", "at_top")

__all__ = [
    "BARRIERS", "BUY", "CLUSTER_GAP", "HOLD", "K_VALUES", "SELL", "STATES",
    "SWING_WINDOW", "detect_swings", "first_touch_label", "label_symbol", "sample_events",
]


def detect_swings(df, window=SWING_WINDOW, gap=CLUSTER_GAP):
    """Trailing swing events as a date-ordered list of ``(index, state)``.

    A bar is ``at_bottom`` when its low is the trailing ``window``-bar minimum,
    ``at_top`` when its high is the trailing maximum. Same-side events closer
    than ``gap`` bars collapse to the first (confirmable same day).
    """
    low = df["low"].to_numpy(dtype="float64")
    high = df["high"].to_numpy(dtype="float64")
    if low.size < window:
        return []
    tmin = pd.Series(low).rolling(window).min().to_numpy()
    tmax = pd.Series(high).rolling(window).max().to_numpy()
    bot = np.flatnonzero((low == tmin) & np.isfinite(tmin))
    top = np.flatnonzero((high == tmax) & np.isfinite(tmax))
    events: list[tuple[int, str]] = []
    for side, idxs in (("at_bottom", bot), ("at_top", top)):
        last = -gap
        for i in idxs:
            if int(i) - last >= gap:
                events.append((int(i), side))
                last = int(i)
    events.sort(key=lambda e: e[0])
    return events


def _first_touch(close, high, low, atr, t, state, k, horizon):
    """First-touch class + 1-based offset for one event; ``(-1, -1)`` if undefined."""
    n = close.size
    if t < 0 or t + horizon >= n or not np.isfinite(atr[t]):
        return -1, -1
    up = close[t] + k * atr[t]
    dn = close[t] - k * atr[t]
    hu = np.flatnonzero(high[t + 1 : t + horizon + 1] >= up)
    hl = np.flatnonzero(low[t + 1 : t + horizon + 1] <= dn)
    ou = int(hu[0]) if hu.size else horizon + 1
    ol = int(hl[0]) if hl.size else horizon + 1
    if ou > horizon and ol > horizon:
        return HOLD, horizon
    profit_up = state == "at_bottom"
    if ou == ol:  # same-bar tie → stop side wins (pessimistic, D-016)
        win_up, off = not profit_up, ou
    elif ou < ol:
        win_up, off = True, ou
    else:
        win_up, off = False, ol
    won = win_up == profit_up
    if state == "at_bottom":
        y = BUY if won else SELL
    else:
        y = SELL if won else BUY
    return y, off + 1


def first_touch_label(df, t, state, k, horizon, atr=None):
    """Public wrapper: label one event from a raw OHLCV frame (ATR computed if None)."""
    if atr is None:
        atr = wilder_atr(df).to_numpy(dtype="float64")
    return _first_touch(
        df["close"].to_numpy(dtype="float64"), df["high"].to_numpy(dtype="float64"),
        df["low"].to_numpy(dtype="float64"), atr, t, state, k, horizon,
    )


def label_symbol(df, symbol, k_atr, barriers=BARRIERS, window=SWING_WINDOW, gap=CLUSTER_GAP):
    """All labelled events for one symbol (schema of :func:`sample_events`)."""
    cols = ["symbol", "date", "state", "y", "horizon"]
    events = detect_swings(df, window=window, gap=gap)
    if not events:
        return pd.DataFrame(columns=cols)
    close = df["close"].to_numpy(dtype="float64")
    high = df["high"].to_numpy(dtype="float64")
    low = df["low"].to_numpy(dtype="float64")
    atr = wilder_atr(df).to_numpy(dtype="float64")
    dates = df["date"].to_numpy()
    rows = []
    for t, state in events:
        for h in barriers:
            y, _off = _first_touch(close, high, low, atr, t, state, k_atr, h)
            if y >= 0:
                rows.append((symbol, dates[t], state, y, h))
    if not rows:
        return pd.DataFrame(columns=cols)
    out = pd.DataFrame(rows, columns=cols)
    out["date"] = pd.to_datetime(out["date"]).astype("datetime64[ns]")
    out["y"] = out["y"].astype("int8")
    out["horizon"] = out["horizon"].astype("int16")
    return out


def sample_events(market, k_atr, barriers=BARRIERS, window=SWING_WINDOW, gap=CLUSTER_GAP,
                  min_date=None, allow_fixture=False, max_symbols=None):
    """Stream one market and return the labelled swing-event frame.

    Schema: ``symbol(str), date(datetime64[ns]), state{at_bottom,at_top},
    y{0=HOLD,1=BUY,2=SELL}, horizon(int)``. An empty frame (same columns) when
    no event carries a defined forward window.
    """
    cols = ["symbol", "date", "state", "y", "horizon"]
    parts = []
    for i, (symbol, raw) in enumerate(
        iter_market_symbols(market, min_date=min_date, allow_fixture=allow_fixture)
    ):
        if max_symbols is not None and i >= max_symbols:
            break
        g = raw.sort_values("date").reset_index(drop=True)
        lab = label_symbol(g, symbol, k_atr, barriers=barriers, window=window, gap=gap)
        if not lab.empty:
            parts.append(lab)
    if not parts:
        return pd.DataFrame(columns=cols)
    return pd.concat(parts, ignore_index=True)
