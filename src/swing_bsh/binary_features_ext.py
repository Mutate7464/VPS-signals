"""WI-036 — target-variant label families + causal feature expansion (D-022 §3c).

Extends (never rewrites) the WI-035 modules: labels reuse the `events` first-touch
geometry, features extend the WI-016 grid with trailing raw-column, cross-sectional,
sector, event-quality, calendar and breadth blocks. The eight target variants are

    event   in {exact, tol2}    (detected extreme bar vs +/-2 shoulder extreme bar)
    window  in {full, mid60}    (touch window [t+1, t+h] vs [t+ceil(.2h), t+floor(.8h)])
    barrier in {k1.0, k0.8}     (profit amplitude in ATRs)

crossed with the horizon ladder ``HORIZONS``. Features are always read at the
**detection bar** `t` (causal); only the target moves. Symbol-sequential, float32.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from src.feature_engine import compute_features_wi016, iter_market_symbols, wi016_feature_names
from src.swing_bsh import train
from src.swing_bsh.binary_labels import binary_targets
from src.swing_bsh.events import BUY, HOLD, SELL, detect_swings
from src.targets import wilder_atr

BASE_DIR = Path(__file__).resolve().parents[2]
SECTOR_MAP_PATH = BASE_DIR / "config" / "sector_map.csv"

EVENT_MODES: tuple[str, ...] = ("exact", "tol2")
WINDOW_MODES: tuple[str, ...] = ("full", "mid60")
K_GRID: tuple[float, ...] = (1.0, 0.8)
HORIZONS: tuple[int, ...] = (5, 8, 13, 21, 34, 55, 89, 144, 233)
TOL_BARS = 2
HMAX = max(HORIZONS)
MAX_SECTORS = 12
BINARY_COLUMNS = ("b_profit", "b_stop", "b_hold")
SMOOTH_PREFIXES = (
    "adx_", "di_spread_", "atr_pct_", "bb_pct_b_", "bb_width_", "obv_zscore_", "amihud_",
    "yangzhang_", "range_pos_", "range_width_", "donchian_break_", "fib_dist_",
    "range_compression_", "kama_er_", "hurst_", "entropy_", "vwap_zscore_",
)
SECTOR_RANK_FEATURES = ("adx_21", "di_spread_21", "atr_pct_21", "bb_pct_b_21",
                        "range_pos_21", "rsi_14")

__all__ = [
    "BINARY_COLUMNS", "EVENT_MODES", "HMAX", "HORIZONS", "K_GRID", "SECTOR_MAP_PATH",
    "WINDOW_MODES", "build_variant_panel", "candidate_features", "first_touch_labels",
    "load_sector_map", "load_variant_panel", "save_variant_panel", "variant_grid",
    "variant_name",
]


def variant_name(event: str, window: str, k: float) -> str:
    """Canonical variant id, e.g. ``tol2_mid60_k0.8``."""
    return f"{event}_{window}_k{k:.1f}"


def variant_grid() -> list[tuple[str, str, str, float]]:
    """The 2x2x2 target-family grid as ``(name, event_mode, window_mode, k)``."""
    return [(variant_name(e, w, k), e, w, k)
            for e in EVENT_MODES for w in WINDOW_MODES for k in K_GRID]


def candidate_features(panel: pd.DataFrame) -> list[str]:
    """WI-016 grid + the WI-036 expansion columns present in `panel`."""
    ext = [c for c in panel.columns if c.startswith(("volume_", "vwap_dist", "bar_count_",
                                                     "swing_", "bars_since_", "dd_age",
                                                     "dow", "month", "cs_", "sec_", "srel_",
                                                     "breadth_"))]
    return [f for f in wi016_feature_names() + ext if f in panel.columns]


# --------------------------------------------------------------------------- #
# Target variants — first-touch labels on a moved entry bar / window
# --------------------------------------------------------------------------- #
def _entry_bars(high, low, idx, bottom) -> dict[str, np.ndarray]:
    """Entry reference bar per event mode (`exact` = detected bar, `tol2` = shoulder)."""
    n = low.size
    lo = np.clip(idx - TOL_BARS, 0, n - 1)
    hi = np.clip(idx + TOL_BARS, 0, n - 1)
    shoulder = np.empty_like(idx)
    for i in range(idx.size):
        seg = slice(int(lo[i]), int(hi[i]) + 1)
        shoulder[i] = int(lo[i]) + (int(np.argmin(low[seg])) if bottom[i]
                                    else int(np.argmax(high[seg])))
    return {"exact": idx.copy(), "tol2": shoulder}


def _touch_offsets(high, low, close, atr, t0, k, hmax=HMAX):
    """First up/down barrier touch offsets (1-based) from each entry bar; `hmax+1` = none."""
    n = close.size
    up = close[t0] + k * atr[t0]
    dn = close[t0] - k * atr[t0]
    pos = t0[:, None] + np.arange(1, hmax + 1)[None, :]
    valid = pos < n
    pc = np.clip(pos, 0, n - 1)
    hi_a = np.where(valid, high[pc], -np.inf)
    lo_a = np.where(valid, low[pc], np.inf)
    up_t, dn_t = hi_a >= up[:, None], lo_a <= dn[:, None]
    ou = np.where(up_t.any(1), up_t.argmax(1) + 1, hmax + 1)
    ol = np.where(dn_t.any(1), dn_t.argmax(1) + 1, hmax + 1)
    return ou, ol


def _resolve(ou, ol, bottom) -> np.ndarray:
    """First-touch 3-class label from windowed offsets (pessimistic same-bar tie)."""
    none = (ou >= HMAX + 1) & (ol >= HMAX + 1)
    win_up = np.where(ou < ol, True, np.where(ol < ou, False, ~bottom))
    won = win_up == bottom
    y = np.where(bottom, np.where(won, BUY, SELL), np.where(won, SELL, BUY))
    return np.where(none, HOLD, y).astype("int8")


def first_touch_labels(high, low, close, atr, idx, states, variants, horizons=HORIZONS) -> dict:
    """`{(variant, h): {b_profit, b_stop, b_hold}}` int8 arrays for one symbol's events."""
    idx = np.asarray(idx, dtype=np.int64)
    states = np.asarray(states)
    bottom = states == "at_bottom"
    bars = _entry_bars(high, low, idx, bottom)
    out: dict = {}
    for name, event, window, k in variants:
        t0 = bars[event]
        ou, ol = _touch_offsets(high, low, close, atr, t0, k)
        for h in horizons:
            s, e = (1, h) if window == "full" else (math.ceil(0.2 * h), math.floor(0.8 * h))
            ouw = np.where((ou >= s) & (ou <= e), ou, HMAX + 1)
            olw = np.where((ol >= s) & (ol <= e), ol, HMAX + 1)
            out[(name, int(h))] = binary_targets(_resolve(ouw, olw, bottom), states)
    return out


# --------------------------------------------------------------------------- #
# Causal feature expansion
# --------------------------------------------------------------------------- #
def _ext_raw_features(df: pd.DataFrame) -> pd.DataFrame:
    """Trailing volume / VWAP / barCount block (unused raw columns)."""
    close = df["close"].astype("float64")
    out: dict[str, pd.Series] = {}
    if "volume" in df.columns:
        vol = df["volume"].astype("float64")
        for w in (21, 55):
            m = vol.rolling(w, min_periods=w).mean()
            s = vol.rolling(w, min_periods=w).std(ddof=1)
            out[f"volume_z_{w}"] = ((vol - m) / (s + 1e-12)).astype("float32")
        out["volume_trend_21"] = (vol / (vol.rolling(21, min_periods=21).mean() + 1e-12)
                                  - 1.0).astype("float32")
    if "average" in df.columns:
        avg = df["average"].astype("float64")
        out["vwap_dist"] = ((close - avg) / (avg + 1e-12)).astype("float32")
    if "barCount" in df.columns:
        bc = df["barCount"].astype("float64")
        m = bc.rolling(55, min_periods=55).mean()
        s = bc.rolling(55, min_periods=55).std(ddof=1)
        out["bar_count_z_55"] = ((bc - m) / (s + 1e-12)).astype("float32")
        out["bar_count_trend_21"] = (bc / (bc.rolling(21, min_periods=21).mean() + 1e-12)
                                     - 1.0).astype("float32")
    return pd.DataFrame(out, index=df.index)


def _event_quality(high, low, close, atr, idx, bottom, swings) -> pd.DataFrame:
    """Swing depth (ATRs), bars since the opposite swing, drawdown age — per event."""
    n = close.size
    run_max = np.maximum.accumulate(high)
    last_top = np.full(n, -1, dtype=np.int64)
    last_bot = np.full(n, -1, dtype=np.int64)
    cur_t = cur_b = -1
    tops = {t for t, s in swings if s == "at_top"}
    bots = {t for t, s in swings if s == "at_bottom"}
    for t in range(n):
        if t in tops:
            cur_t = t
        if t in bots:
            cur_b = t
        last_top[t], last_bot[t] = cur_t, cur_b
    depth = np.empty(idx.size, dtype="float32")
    since_opp = np.empty(idx.size, dtype="float32")
    dd_age = np.empty(idx.size, dtype="float32")
    for i, t in enumerate(idx):
        t = int(t)
        lo_win = low[max(0, t - 20): t + 1].min()
        hi_win = high[max(0, t - 20): t + 1].max()
        depth[i] = (close[t] - lo_win) / (atr[t] + 1e-12) if bottom[i] else (hi_win - close[t]) / (atr[t] + 1e-12)
        opp = last_top[t] if bottom[i] else last_bot[t]
        since_opp[i] = t - opp if opp >= 0 else np.nan
        hi_age = int(np.argmax(high[: t + 1]))
        dd_age[i] = t - hi_age
    return pd.DataFrame({"swing_depth_atr": depth, "bars_since_opp": since_opp,
                         "dd_age": dd_age}, index=np.arange(idx.size))


def load_sector_map(path: Path = SECTOR_MAP_PATH) -> dict[str, str]:
    """`symbol -> sector` from `config/sector_map.csv` (empty map when absent)."""
    if not Path(path).exists():
        return {}
    df = pd.read_csv(path, usecols=["symbol", "sector"])
    return dict(zip(df["symbol"].astype(str), df["sector"].fillna("UNKNOWN").astype(str)))


def _sector_block(panel: pd.DataFrame, sectors: dict[str, str]) -> pd.DataFrame:
    """Sector one-hots + same-date same-sector percentile ranks (causal)."""
    sec = panel["symbol"].map(sectors).fillna("UNKNOWN")
    top = [s for s in sec.value_counts().index[:MAX_SECTORS]]
    out = {f"sec_{s}": (sec == s).astype("float32") for s in top}
    keys = [panel["date"].to_numpy(), sec.to_numpy()]
    for f in SECTOR_RANK_FEATURES:
        if f in panel.columns:
            out[f"srel_{f}"] = (panel.groupby(keys)[f].rank(pct=True).astype("float32"))
    return pd.DataFrame(out, index=panel.index)


def _cross_sectional(panel: pd.DataFrame) -> pd.DataFrame:
    """Same-date percentile rank of every smooth-family feature."""
    cols = [c for c in panel.columns if c.startswith(SMOOTH_PREFIXES)]
    if not cols:
        return pd.DataFrame(index=panel.index)
    r = panel.groupby("date")[cols].rank(pct=True)
    return r.add_prefix("cs_").astype("float32")


SWING_LEG_KS: tuple[int, ...] = (1, 3)
"""Leg ranks reported by `_swing_structure` (rank 1 = the detection swing itself)."""


def _swing_structure(high, low, close, atr, idx, swings, ks=SWING_LEG_KS) -> pd.DataFrame:
    """Trailing swing-leg geometry at each detection bar (causal, ATR-normalized).

    `swings` is the `detect_swings` list (each leg is confirmed at its own bar, so
    every read is `<= t`). Ranks count newest-first among the swings at or before
    `t`, so `k=1` is the detection swing itself and `k=3` three swings back. Per
    rank `k`: `swing_leg_len_{k}` = |extreme_k - extreme_{k+1}| / ATR_t (impulse
    amplitude, ATRs) and `swing_leg_dur_{k}` = bars between the two extremes (a
    unitless count, like `bars_since_opp`). `swing_depth_atr_prev` = |close_t -
    extreme_prev| / ATR_t, the distance to the previous swing level. NaN until the
    required prior swing exists; float32 throughout.
    """
    t = np.asarray(idx, dtype=np.int64)
    m, n = len(swings), t.size
    bars = np.array([int(b) for b, _ in swings], dtype=np.int64)
    ext = np.zeros(0, dtype="float64")
    if m:
        pos = np.clip(bars, 0, max(np.size(low) - 1, 0))
        sides = np.array([s for _, s in swings])
        ext = np.where(sides == "at_bottom", low[pos], high[pos]).astype("float64")
    rank = np.searchsorted(bars, t, side="right") - 1  # newest swing at/before t
    denom = np.asarray(atr, dtype="float64")[t] + 1e-12
    leg_abs = np.abs(np.diff(ext)) if m > 1 else np.zeros(0)
    dur_gap = np.diff(bars).astype("float64") if m > 1 else np.zeros(0)
    out: dict[str, np.ndarray] = {}
    for k in ks:
        j = rank - (int(k) - 1)
        ok = (j >= 1) & (j < m)
        prior = np.clip(j, 1, max(m - 1, 1)) - 1
        leg = np.where(ok, leg_abs[prior] / denom, np.nan) if leg_abs.size else np.full(n, np.nan)
        dur = np.where(ok, dur_gap[prior], np.nan) if dur_gap.size else np.full(n, np.nan)
        out[f"swing_leg_len_{k}"] = leg.astype("float32")
        out[f"swing_leg_dur_{k}"] = dur.astype("float32")
    jp = rank - 1
    okp = (jp >= 0) & (jp < m)
    depth = np.full(n, np.nan)
    if m:
        depth = np.abs(close[t] - ext[np.clip(jp, 0, max(m - 1, 0))]) / denom
    out["swing_depth_atr_prev"] = np.where(okp, depth, np.nan).astype("float32")
    return pd.DataFrame(out, index=np.arange(n))


# --------------------------------------------------------------------------- #
# Panel driver
# --------------------------------------------------------------------------- #
def build_variant_panel(market: str, *, min_date: str = train.MIN_DATE,
                        allow_fixture: bool = False, max_symbols: int | None = None,
                        variants=None, horizons=HORIZONS, with_sector: bool = True):
    """Stream one market -> (feature panel, labels) for the full target-variant grid.

    Returns `(panel, labels)` with one row per detected swing event (`symbol, date,
    state, close, atr`, the WI-016 grid, the WI-036 expansion) and
    `labels[(variant, h)][binary]` int8 arrays aligned to the panel rows.
    """
    variants = variants or variant_grid()
    parts: list[pd.DataFrame] = []
    label_parts: dict = {}
    breadth: dict = {}
    for i, (symbol, raw) in enumerate(
        iter_market_symbols(market, min_date=min_date, allow_fixture=allow_fixture)
    ):
        if max_symbols is not None and i >= max_symbols:
            break
        g = raw.sort_values("date").reset_index(drop=True)
        fdf = compute_features_wi016(g)
        ext = _ext_raw_features(g)
        close = g["close"].to_numpy("float64")
        high = g["high"].to_numpy("float64")
        low = g["low"].to_numpy("float64")
        atr = wilder_atr(g).to_numpy("float64")
        dates = g["date"].to_numpy()
        swings = detect_swings(g)
        idx = np.array([t for t, _ in swings], dtype=np.int64)
        if idx.size == 0:
            continue
        states = np.array([s for _, s in swings])
        bottom = states == "at_bottom"
        finite = np.isfinite(atr[idx]) & np.isfinite(close[idx])
        idx, states, bottom = idx[finite], states[finite], bottom[finite]
        swings = [(int(t), s) for t, s in swings if np.isfinite(atr[t])]
        if idx.size == 0:
            continue
        # market breadth: raw trailing-min/max flags over the universe, per date
        w = 21
        tmin = pd.Series(low).rolling(w).min().to_numpy()
        tmax = pd.Series(high).rolling(w).max().to_numpy()
        for j, d in enumerate(dates):
            nb, nt, nn = breadth.get(d, (0, 0, 0))
            breadth[d] = (nb + int(np.isfinite(tmin[j]) and low[j] == tmin[j]),
                          nt + int(np.isfinite(tmax[j]) and high[j] == tmax[j]), nn + 1)
        keep = fdf.iloc[idx].reset_index(drop=True).drop(columns=["date"], errors="ignore")
        keep = keep.astype("float32")
        keep["symbol"] = symbol
        keep["date"] = dates[idx]
        keep["state"] = states
        keep["close"] = close[idx].astype("float32")
        keep["atr"] = atr[idx].astype("float32")
        ext = ext.iloc[idx].reset_index(drop=True)
        eq = _event_quality(high, low, close, atr, idx, bottom, swings)
        ss = _swing_structure(high, low, close, atr, idx, swings)
        cal = pd.DataFrame({
            "dow": pd.Series(pd.DatetimeIndex(dates[idx]).dayofweek, dtype="float32"),
            "month": pd.Series(pd.DatetimeIndex(dates[idx]).month, dtype="float32")})
        parts.append(pd.concat([keep, ext, eq, ss, cal], axis=1))
        lab = first_touch_labels(high, low, close, atr, idx, states, variants, horizons)
        for key, targets in lab.items():
            slot = label_parts.setdefault(key, {b: [] for b in BINARY_COLUMNS})
            for b in BINARY_COLUMNS:
                slot[b].append(targets[b])
        del g, fdf, ext
    if not parts:
        return pd.DataFrame(), {}
    panel = pd.concat(parts, ignore_index=True)
    bd = pd.DataFrame([(d, v[0] / max(v[2], 1), v[1] / max(v[2], 1)) for d, v in breadth.items()],
                      columns=["date", "breadth_bottom", "breadth_top"]).astype(
        {"breadth_bottom": "float32", "breadth_top": "float32"})
    panel = panel.merge(bd, on="date", how="left")
    if with_sector:
        panel = pd.concat([panel, _sector_block(panel, load_sector_map())], axis=1)
    panel = pd.concat([panel, _cross_sectional(panel)], axis=1)
    labels = {key: {b: np.concatenate(v[b]).astype("int8") for b in BINARY_COLUMNS}
              for key, v in label_parts.items()}
    return panel, labels


def _paths(out_dir, market: str):
    d = Path(out_dir)
    return d / f"wi036_panel_{market}.parquet", d / f"wi036_labels_{market}.npz"


def save_variant_panel(panel: pd.DataFrame, labels: dict, out_dir, market: str):
    """Cache one market's feature panel (parquet) + label matrix (npz)."""
    pp, lp = _paths(out_dir, market)
    pp.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(pp, index=False)
    np.savez_compressed(lp, **{f"{v}|{h}|{b}": labels[(v, h)][b]
                               for (v, h) in labels for b in BINARY_COLUMNS})
    return pp, lp


def load_variant_panel(out_dir, market: str, keys):
    """Load the cached `(panel, labels)` pair, or `(None, None)` when absent."""
    pp, lp = _paths(out_dir, market)
    if not pp.exists() or not lp.exists():
        return None, None
    panel = pd.read_parquet(pp)
    blob = np.load(lp)
    labels = {(v, int(h)): {b: blob[f"{v}|{h}|{b}"] for b in BINARY_COLUMNS}
              for (v, h) in keys}
    return panel, labels
