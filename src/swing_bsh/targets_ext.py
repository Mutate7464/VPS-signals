"""WI-048a — T2 target-family label builders (`up` / `high_low` / `vol_expand` / `vol_expand_fwd`).

Four target families as explicit grid axes (never merged with the WI-036
label-geometry knobs). Every label is read against the event's **reference bar**
`t0`: the detected swing bar for the `exact` geometry, the +/-2 shoulder extreme
bar for `tol2` (the `_entry_bars` convention of :mod:`binary_features_ext`).
Features are always read at the detection bar only (causal); labels look forward.

    ``up(t0, h)``         ``close[t0+h] > close[t0]``
    ``high_low(t0, h)``   the event-window extreme (the low at an ``at_bottom``
                          event, the high at an ``at_top`` event) is touched
                          again inside ``[t0+1, t0+h]`` (re-test)
    ``vol_expand(t0, h)`` QUARANTINED / backward-looking — kept only for WI-048
                          reproducibility, never promoted: realized vol of the ``h``
                          log-returns ending at ``t0`` exceeds ``VOL_RATIO_THRESHOLD``
                          x the previous ``h`` (prior window of the same length)
    ``vol_expand_fwd(t0, h)`` FORWARD-looking: realized vol of ``[t0+1, t0+h]``
                          exceeds ``VOL_RATIO_THRESHOLD`` x the trailing
                          ``[t0-h+1, t0]``
    ``xsec_vol_rank_bin`` / ``xsec_vol_rank_cont(t0, h)`` WI-058 — forward realized
                          vol of ``[t0+1, t0+h]`` ranked at ``t0+h`` against the
                          same-date events of the market: top-tercile flag (binary)
                          or rank in ``[0, 1]`` (continuous). Market-wide, so it is
                          computed per market, never per symbol.

A window that does not exist (not enough forward / backward bars) is labelled 0,
mirroring the WI-035/036 first-touch convention. Symbol-sequential reads, float32,
``n_jobs=2``; this module trains nothing.

CLI::

    WI048_SMOKE=5 python -m src.swing_bsh.targets_ext --probe --out /tmp/wi048_smoke
    python -m src.swing_bsh.targets_ext --probe   # reports/t2_label_density_probe.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path

import numpy as np
import pandas as pd

from src.feature_engine import iter_market_symbols
from src.swing_bsh import binary_features_ext as ext
from src.swing_bsh import train
from src.swing_bsh.events import detect_swings
from src.targets import wilder_atr

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "reports"
PROBE_NAME = "t2_label_density_probe.md"
DEFAULT_SMOKE_DIR = "/tmp/wi048_smoke"

FAMILIES: tuple[str, ...] = ("up", "high_low", "vol_expand", "vol_expand_fwd")
XSEC_FAMILIES: tuple[str, ...] = ("xsec_vol_rank_bin", "xsec_vol_rank_cont")
"""WI-058 — same-date cross-sectional forward-vol-rank families (market-wide)."""
MFE_MAE_FAMILIES: tuple[str, ...] = ("mfe_mae_bin", "mfe_mae_cont")
"""WI-059 — payoff-ratio families (ATR-normalized MFE/MAE over `[t0+1, t0+h]`).

Built by :func:`mfe_mae_bin_labels` / :func:`mfe_mae_cont_labels`; kept outside
`FAMILIES` / `ALL_FAMILIES` because the full-panel wiring is the PM-owned grid WI."""
MFE_MAE_RATIO_THRESHOLD = 1.0
"""Cut of the `mfe_mae_bin` family: favourable / adverse excursion must exceed this."""
ALL_FAMILIES: tuple[str, ...] = FAMILIES + XSEC_FAMILIES
HORIZONS: tuple[int, ...] = (5, 8, 13, 21, 34, 55)
EVENT_MODES: tuple[str, ...] = ext.EVENT_MODES
PINNED_EVENT: dict[str, str] = {"USD": "exact", "CAD": "tol2"}
"""Per-market label geometry pinned by WI-048c (variant `*_full_k0.8`)."""
VOL_RATIO_THRESHOLD = 1.0
XSEC_TOP_FRAC = 2.0 / 3.0
"""Top-tercile cut of the same-date cross-sectional vol rank (WI-058 binary family)."""
MIN_POSITIVES = 25
"""Sparse-cell flag for the density probe (CB-04 calibration floor)."""

__all__ = ["ALL_FAMILIES", "DEFAULT_SMOKE_DIR", "EVENT_MODES", "FAMILIES", "HORIZONS",
           "MIN_POSITIVES", "PINNED_EVENT", "PROBE_NAME", "VOL_RATIO_THRESHOLD",
           "XSEC_FAMILIES", "XSEC_TOP_FRAC", "build_probe_report", "build_targets_panel",
           "high_low_labels", "iter_events", "label_key", "main", "probe_table",
           "target_labels", "up_labels", "vol_expand_fwd_labels", "vol_expand_labels",
           "xsec_vol_rank_bin_labels", "xsec_vol_rank_cont_labels"]


def label_key(family: str, event: str, h: int) -> tuple[str, str, int]:
    """Canonical label id: `(family, event_mode, horizon)`."""
    return (str(family), str(event), int(h))


# --------------------------------------------------------------------------- #
# The three families (one symbol's events at a time)
# --------------------------------------------------------------------------- #
def up_labels(close, t0, h: int) -> np.ndarray:
    """`close[t0+h] > close[t0]`; 0 when the forward bar does not exist yet."""
    close = np.asarray(close, dtype="float64")
    t0 = np.asarray(t0, dtype=np.int64)
    out = np.zeros(t0.size, dtype="int8")
    fwd = t0 + int(h)
    ok = fwd < close.size
    out[ok] = (close[fwd[ok]] > close[t0[ok]]).astype("int8")
    return out


def high_low_labels(high, low, states, t0, h: int) -> np.ndarray:
    """1 when the event-window extreme is re-touched inside `[t0+1, t0+h]`.

    The level is the side-implied extreme at the reference bar (`low[t0]` for an
    `at_bottom` event, `high[t0]` for an `at_top` event) — for `tol2` that bar is
    the shoulder extreme of the detection bar's +/-2 window.
    """
    high = np.asarray(high, dtype="float64")
    low = np.asarray(low, dtype="float64")
    t0 = np.asarray(t0, dtype=np.int64)
    bottom = np.asarray(states) == "at_bottom"
    level = np.where(bottom, low[t0], high[t0])
    pos = t0[:, None] + np.arange(1, int(h) + 1)[None, :]
    valid = pos < high.size
    pc = np.clip(pos, 0, max(high.size - 1, 0))
    hit = np.where(bottom[:, None], low[pc] <= level[:, None], high[pc] >= level[:, None])
    return (hit & valid).any(axis=1).astype("int8")


def _win_std(c1, c2, s, e):
    """Sample std of `x[s..e]` (inclusive) from cumulative sums of `x` and `x**2`."""
    cnt = e - s + 1
    s1 = c1[e + 1] - c1[s]
    s2 = c2[e + 1] - c2[s]
    mean = s1 / cnt
    var = (s2 - cnt * mean * mean) / (cnt - 1)
    return np.sqrt(np.maximum(var, 0.0))


def _log_returns(close: np.ndarray) -> np.ndarray:
    """Log-returns of `close`, first bar pinned to 0.0 (non-finite -> 0.0)."""
    lr = np.zeros(close.size, dtype="float64")
    if close.size > 1:
        with np.errstate(divide="ignore", invalid="ignore"):
            lr[1:] = np.log(close[1:] / close[:-1])
    return np.nan_to_num(lr, nan=0.0, posinf=0.0, neginf=0.0)


def vol_expand_labels(close, t0, h: int, threshold: float = VOL_RATIO_THRESHOLD) -> np.ndarray:
    """QUARANTINED (backward-looking) — realized vol of the `h` returns ending at `t0`.

    1 when that vol beats the prior `h`. Kept for WI-048 reproducibility only; use
    :func:`vol_expand_fwd_labels` (forward window) for any new work.
    """
    close = np.asarray(close, dtype="float64")
    t0 = np.asarray(t0, dtype=np.int64)
    lr = _log_returns(close)
    c1 = np.concatenate([[0.0], np.cumsum(lr)])
    c2 = np.concatenate([[0.0], np.cumsum(lr * lr)])
    out = np.zeros(t0.size, dtype="int8")
    h = int(h)
    s, e = t0 - h + 1, t0
    ps, pe = t0 - 2 * h + 1, t0 - h
    ok = ps >= 0
    if ok.any():
        cur = _win_std(c1, c2, s[ok], e[ok])
        prior = _win_std(c1, c2, ps[ok], pe[ok])
        good = prior > 0.0
        idx = np.flatnonzero(ok)[good]
        out[idx] = (cur[good] / prior[good] > float(threshold)).astype("int8")
    return out


def vol_expand_fwd_labels(close, t0, h: int, threshold: float = VOL_RATIO_THRESHOLD) -> np.ndarray:
    """1 when realized vol of `[t0+1, t0+h]` beats the trailing `[t0-h+1, t0]`.

    FORWARD-looking: the forward window reads bars `> t0` only. 0 where that window
    does not exist (`t0+h >= n`) or the trailing window has no prior vol.
    """
    close = np.asarray(close, dtype="float64")
    t0 = np.asarray(t0, dtype=np.int64)
    n, h = close.size, int(h)
    lr = _log_returns(close)
    c1 = np.concatenate([[0.0], np.cumsum(lr)])
    c2 = np.concatenate([[0.0], np.cumsum(lr * lr)])
    out = np.zeros(t0.size, dtype="int8")
    ok = (h > 0) & (t0 + h < n) & (t0 - h + 1 >= 0)
    if ok.any():
        i = np.flatnonzero(ok)
        fwd = _win_std(c1, c2, t0[i] + 1, t0[i] + h)
        prior = _win_std(c1, c2, t0[i] - h + 1, t0[i])
        good = prior > 0.0
        out[i[good]] = (fwd[good] / prior[good] > float(threshold)).astype("int8")
    return out


# --------------------------------------------------------------------------- #
# WI-059 — payoff ratio: ATR-normalized MFE/MAE over [t0+1, t0+h]
# --------------------------------------------------------------------------- #
def _forward_extremes(high, low, t0, h: int) -> tuple[np.ndarray, np.ndarray]:
    """Highest high / lowest low of `[t0+1, t0+h]`; NaN unless that window is complete."""
    high = np.asarray(high, dtype="float64")
    low = np.asarray(low, dtype="float64")
    t0 = np.asarray(t0, dtype=np.int64)
    n, h = high.size, int(h)
    if h <= 0 or t0.size == 0:
        nan = np.full(t0.size, np.nan)
        return nan.copy(), nan.copy()
    pos = t0[:, None] + np.arange(1, h + 1)[None, :]
    pc = np.clip(pos, 0, max(n - 1, 0))
    full = ((t0 + h) < n)[:, None]  # every window bar exists iff `t0 + h < n`
    hi = np.where(full, high[pc], -np.inf).max(axis=1)
    lo = np.where(full, low[pc], np.inf).min(axis=1)
    return np.where(full[:, 0], hi, np.nan), np.where(full[:, 0], lo, np.nan)


def _mfe_mae_excursions(high, low, close, atr, states, t0, h: int):
    """ATR-normalized `(favourable, adverse)` excursions over `[t0+1, t0+h]`.

    Both are measured against the reference close `close[t0]` and scaled by `atr[t0]`;
    the direction is the swing's own (`at_bottom` -> up, `at_top` -> down). NaN where
    the forward window does not exist or the ATR scale is not positive/finite.
    """
    close = np.asarray(close, dtype="float64")
    atr = np.asarray(atr, dtype="float64")
    t0 = np.asarray(t0, dtype=np.int64)
    bottom = np.asarray(states) == "at_bottom"
    hi, lo = _forward_extremes(high, low, t0, h)
    up, dn = hi - close[t0], close[t0] - lo
    fav = np.where(bottom, up, dn)
    adv = np.where(bottom, dn, up)
    a0 = atr[t0]
    scale = np.where(np.isfinite(a0) & (a0 > 0.0), a0, np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        return fav / scale, adv / scale


def mfe_mae_cont_labels(high, low, close, atr, states, t0, h: int) -> np.ndarray:
    """Continuous payoff label: `log(MFE / MAE)` in ATR units over `[t0+1, t0+h]`.

    float32; NaN where the forward window does not exist, the ATR scale is not
    positive/finite, or the adverse excursion is not positive (ratio undefined).
    """
    fav, adv = _mfe_mae_excursions(high, low, close, atr, states, t0, h)
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = np.where(adv > 0.0, fav / adv, np.nan)
        out = np.log(np.where(ratio > 0.0, ratio, np.nan))
    return out.astype("float32")


def mfe_mae_bin_labels(high, low, close, atr, states, t0, h: int,
                       threshold: float = MFE_MAE_RATIO_THRESHOLD) -> np.ndarray:
    """Binary payoff label: `MFE / MAE > threshold` (ATR units); 0 where undefined."""
    fav, adv = _mfe_mae_excursions(high, low, close, atr, states, t0, h)
    out = np.zeros(fav.size, dtype="int8")
    ok = np.isfinite(fav) & np.isfinite(adv) & (adv > 0.0)
    out[ok] = (fav[ok] > float(threshold) * adv[ok]).astype("int8")
    return out


# --------------------------------------------------------------------------- #
# WI-058 — forward cross-sectional vol rank (market-wide, same-date ranks)
# --------------------------------------------------------------------------- #
def _forward_vol(close, t0, h: int) -> np.ndarray:
    """Realized vol of `[t0+1, t0+h]`; NaN where that forward window does not exist."""
    close = np.asarray(close, dtype="float64")
    t0 = np.asarray(t0, dtype=np.int64)
    n, h = close.size, int(h)
    lr = _log_returns(close)
    c1 = np.concatenate([[0.0], np.cumsum(lr)])
    c2 = np.concatenate([[0.0], np.cumsum(lr * lr)])
    out = np.full(t0.size, np.nan)
    ok = (h >= 2) & (t0 >= 0) & (t0 + h < n)
    if ok.any():
        i = np.flatnonzero(ok)
        out[i] = _win_std(c1, c2, t0[i] + 1, t0[i] + h)
    return out


def _xsec_rank(values, dates) -> np.ndarray:
    """Same-date cross-sectional rank in `[0, 1]`: `(average_rank - 1) / (n_date - 1)`."""
    df = pd.DataFrame({"d": np.asarray(dates), "v": np.asarray(values, dtype="float64")})
    g = df.groupby("d")["v"]
    rk = g.rank(method="average").to_numpy("float64")
    den = g.transform("count").to_numpy("float64") - 1.0
    return (rk - 1.0) / np.where(den > 0.0, den, np.nan)


def _xsec_vol(panel: pd.DataFrame, closes, h: int) -> np.ndarray:
    """Per-row forward vol from `{symbol: close}` and each row's reference `bar`."""
    bars = np.asarray(panel["bar"], dtype=np.int64)
    syms = panel["symbol"].astype(str).to_numpy()
    vol = np.full(bars.size, np.nan)
    for sym in pd.unique(syms):
        sel = syms == sym
        vol[sel] = _forward_vol(closes[sym], bars[sel], h)
    return vol


def _bin_from_rank(rank, top_frac: float = XSEC_TOP_FRAC) -> np.ndarray:
    """Top-tercile flag of a rank array; 0 where the rank is NaN (no forward window)."""
    rank = np.asarray(rank, dtype="float64")
    out = np.zeros(rank.size, dtype="int8")
    ok = np.isfinite(rank)
    out[ok] = (rank[ok] >= float(top_frac)).astype("int8")
    return out


def xsec_vol_rank_cont_labels(panel: pd.DataFrame, closes, h: int) -> np.ndarray:
    """Continuous label: same-date cross-sectional rank of the forward realized vol.

    `panel` = one market's event rows (`symbol`, `bar` = the reference bar `t0`,
    `date`); `closes` maps symbol -> that symbol's close series. The vol is read from
    `[t0+1, t0+h]` only, so the label is forward-looking. NaN where that window does
    not exist or the date carries a single name (rank undefined).
    """
    return _xsec_rank(_xsec_vol(panel, closes, h), panel["date"].to_numpy()).astype("float32")


def xsec_vol_rank_bin_labels(panel: pd.DataFrame, closes, h: int,
                             top_frac: float = XSEC_TOP_FRAC) -> np.ndarray:
    """Binary label: the forward vol sits in its date's top tercile (0 if no window)."""
    return _bin_from_rank(xsec_vol_rank_cont_labels(panel, closes, h), top_frac)


def target_labels(high, low, close, idx, states, families=FAMILIES,
                  horizons=HORIZONS) -> dict:
    """`{label_key(family, event, h): int8 array}` for one symbol's events.

    Per-symbol families only; the `XSEC_FAMILIES` need the market's full event set and
    are built by :func:`build_targets_panel` (see :func:`xsec_vol_rank_cont_labels`).
    """
    idx = np.asarray(idx, dtype=np.int64)
    states = np.asarray(states)
    high = np.asarray(high, dtype="float64")
    low = np.asarray(low, dtype="float64")
    close = np.asarray(close, dtype="float64")
    bars = ext._entry_bars(high, low, idx, states == "at_bottom")
    out: dict = {}
    for event in EVENT_MODES:
        t0 = bars[event]
        for h in horizons:
            h = int(h)
            if "up" in families:
                out[label_key("up", event, h)] = up_labels(close, t0, h)
            if "high_low" in families:
                out[label_key("high_low", event, h)] = high_low_labels(high, low, states, t0, h)
            if "vol_expand" in families:
                out[label_key("vol_expand", event, h)] = vol_expand_labels(close, t0, h)
            if "vol_expand_fwd" in families:
                out[label_key("vol_expand_fwd", event, h)] = vol_expand_fwd_labels(close, t0, h)
    return out


# --------------------------------------------------------------------------- #
# Event stream + panel driver (rows identical to the WI-036 variant panel)
# --------------------------------------------------------------------------- #
def iter_events(market: str, *, min_date: str = train.MIN_DATE, allow_fixture: bool = False,
                max_symbols: int | None = None):
    """Yield `(symbol, frame, idx, states, atr)` for one market, symbol-sequential.

    The event filter (finite `atr`/`close` at the detected swing bar, symbols with
    no swing dropped) mirrors `binary_features_ext.build_variant_panel`.
    """
    for i, (symbol, raw) in enumerate(
        iter_market_symbols(market, min_date=min_date, allow_fixture=allow_fixture)
    ):
        if max_symbols is not None and i >= max_symbols:
            break
        g = raw.sort_values("date").reset_index(drop=True)
        swings = detect_swings(g)
        idx = np.array([t for t, _ in swings], dtype=np.int64)
        if idx.size == 0:
            continue
        states = np.array([s for _, s in swings])
        atr = wilder_atr(g).to_numpy("float64")
        finite = np.isfinite(atr[idx]) & np.isfinite(g["close"].to_numpy("float64")[idx])
        idx, states = idx[finite], states[finite]
        if idx.size == 0:
            continue
        yield symbol, g, idx, states, atr


def build_targets_panel(market: str, *, families=ALL_FAMILIES, horizons=HORIZONS,
                        min_date: str = train.MIN_DATE, allow_fixture: bool = False,
                        max_symbols: int | None = None):
    """Stream one market -> (feature panel, `{label_key: label array}`) for the T2 families.

    The panel is the WI-036 variant panel (features read at the detection bar only);
    the labels are the T2 families, aligned row-for-row with the panel. The
    `XSEC_FAMILIES` are ranked across the market's events on the same date, so they are
    built once per market from the collected event rows (never per symbol).
    """
    panel, _ = ext.build_variant_panel(
        market, min_date=min_date, allow_fixture=allow_fixture, max_symbols=max_symbols,
        variants=ext.variant_grid()[:1], horizons=(int(min(horizons)),),
    )
    if panel.empty:
        return panel, {}
    parts: dict = {}
    n_rows = 0
    xsec = tuple(f for f in families if f in XSEC_FAMILIES)
    per_symbol = tuple(f for f in families if f in FAMILIES)
    xrows: list[tuple] = []
    for symbol, g, idx, states, _atr in iter_events(
        market, min_date=min_date, allow_fixture=allow_fixture, max_symbols=max_symbols
    ):
        n_rows += int(idx.size)
        high = g["high"].to_numpy("float64")
        low = g["low"].to_numpy("float64")
        close = g["close"].to_numpy("float64")
        lab = target_labels(high, low, close, idx, states, per_symbol, horizons)
        for key, arr in lab.items():
            parts.setdefault(key, []).append(arr)
        if xsec:
            xrows.append((symbol, close, ext._entry_bars(high, low, idx, states == "at_bottom"),
                          g["date"].to_numpy()))
    if n_rows != len(panel):
        raise RuntimeError(f"label/panel row mismatch for {market}: {n_rows} != {len(panel)}")
    if xsec and xrows:
        closes = {row[0]: row[1] for row in xrows}
        for event in EVENT_MODES:
            frame = pd.DataFrame({
                "symbol": np.concatenate([[s] * bars[event].size
                                          for s, _c, bars, _d in xrows]),
                "bar": np.concatenate([bars[event] for _s, _c, bars, _d in xrows]),
                "date": np.concatenate([dates[bars[event]] for _s, _c, bars, dates in xrows])})
            for h in horizons:
                cont = xsec_vol_rank_cont_labels(frame, closes, int(h))
                for family in xsec:
                    arr = cont if family == "xsec_vol_rank_cont" else _bin_from_rank(cont)
                    parts.setdefault(label_key(family, event, int(h)), []).append(arr)
    return panel, {k: np.concatenate(v).astype(v[0].dtype) for k, v in parts.items()}


# --------------------------------------------------------------------------- #
# Label-density probe (WI-048b smoke gate — no training, no model files)
# --------------------------------------------------------------------------- #
def probe_table(markets, *, families=FAMILIES, horizons=HORIZONS, max_symbols: int | None = None,
                allow_fixture: bool = False) -> pd.DataFrame:
    """Prevalence per (market, family, horizon) on the market's pinned geometry."""
    rows: list[dict] = []
    for market in markets:
        event = PINNED_EVENT[market]
        parts: dict = {}
        for _symbol, g, idx, states, _atr in iter_events(
            market, allow_fixture=allow_fixture, max_symbols=max_symbols
        ):
            lab = target_labels(g["high"].to_numpy("float64"), g["low"].to_numpy("float64"),
                                g["close"].to_numpy("float64"), idx, states, families, horizons)
            for family in families:
                for h in horizons:
                    parts.setdefault((family, int(h)), []).append(lab[label_key(family, event, h)])
        for family in families:
            for h in horizons:
                arr = (np.concatenate(parts[(family, int(h))])
                       if parts.get((family, int(h))) else np.zeros(0, dtype="int8"))
                pos, n = int(arr.sum()), int(arr.size)
                rows.append({"market": market, "family": family, "h": int(h), "event": event,
                             "n_events": n, "n_pos": pos,
                             "prevalence": (pos / n) if n else float("nan"),
                             "sparse": bool(pos < MIN_POSITIVES)})
    return pd.DataFrame(rows)


def build_probe_report(table: pd.DataFrame, path: Path) -> Path:
    """`t2_label_density_probe.md` — prevalence, density ranking, sparse flags."""
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = ["# WI-048b — T2 label-density probe (D-025 tier 2)", "",
             f"- Generated (UTC): {now}",
             f"- Families: {', '.join(FAMILIES)}; horizons {', '.join(str(h) for h in HORIZONS)}; "
             f"pinned geometry per market {PINNED_EVENT}; sparse = < {MIN_POSITIVES} positives",
             "- Labels are computed from price paths only (no features, no training, no pickles).",
             "", "## 1. Prevalence per cell", "",
             "| market | family | h | event | events | positives | prevalence | flag |",
             "| :--- | :--- | ---: | :--- | ---: | ---: | ---: | :--- |"]
    for _, r in table.iterrows():
        lines.append(f"| {r['market']} | `{r['family']}` | {int(r['h'])} | {r['event']} | "
                     f"{int(r['n_events'])} | {int(r['n_pos'])} | {r['prevalence']:.4f} | "
                     f"{'sparse' if r['sparse'] else 'ok'} |")
    lines += ["", "## 2. Density ranking (mean prevalence per family x market)", "",
              "| family | denser market | mean prevalence |", "| :--- | :--- | ---: |"]
    for family in FAMILIES:
        g = table[table["family"] == family]
        if g.empty:
            continue
        m = g.groupby("market")["prevalence"].mean().sort_values(ascending=False)
        lines.append(f"| `{family}` | {m.index[0]} | {m.iloc[0]:.4f} |")
    sparse = table[table["sparse"]]
    lines += ["", "## 3. Sparse cells (reported, never dropped)", ""]
    if sparse.empty:
        lines.append("- none")
    else:
        for _, r in sparse.iterrows():
            lines.append(f"- `{r['family']}` h{int(r['h'])} {r['market']}: {int(r['n_pos'])} positives")
    lines += ["", "## Notes / deviations", "",
              "- This probe is the smoke gate for WI-048c/d/e: the denser market per family is the "
              "dry-run market named in the sprint brief.",
              "- Prevalence is measured on the pinned event geometry only (USD `exact`, CAD `tol2`); "
              "the other geometry stays available through `target_labels`.",
              ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="WI-048a T2 target-family label builders")
    parser.add_argument("--probe", action="store_true", help="Label-density probe (no training).")
    parser.add_argument("--market", default="ALL", help="USD | CAD | ALL (default ALL)")
    parser.add_argument("--limit", type=int, default=None, help="Max symbols per market (smoke).")
    parser.add_argument("--out", default=None, help="Output dir (smoke runs use /tmp).")
    parser.add_argument("--allow-fixture", action="store_true")
    args = parser.parse_args(argv)
    if not args.probe:
        print("[wi048.labels] use --probe (the grid lives in src.swing_bsh.grid_targets_ext)")
        return 2

    smoke = os.environ.get("WI048_SMOKE", "").strip()
    if args.limit is None and smoke.isdigit():
        args.limit = int(smoke)
    if args.out is None and smoke:
        args.out = DEFAULT_SMOKE_DIR

    from src.market_cli import cli_markets
    markets = cli_markets(args.market, prog="wi048.targets_ext")
    if markets is None:
        return 2
    table = probe_table(markets, max_symbols=args.limit, allow_fixture=args.allow_fixture)
    out_dir = Path(args.out) if args.out else REPORTS_DIR
    report = build_probe_report(table, out_dir / PROBE_NAME)
    print(f"[wi048.labels] probe -> {report} | markets={','.join(markets)} | cells={len(table)}")
    print("[wi048.labels] EXIT:0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
