"""WI-048a — T2 target-family label builders (`up` / `high_low` / `vol_expand`).

Three target families as explicit grid axes (never merged with the WI-036
label-geometry knobs). Every label is read against the event's **reference bar**
`t0`: the detected swing bar for the `exact` geometry, the +/-2 shoulder extreme
bar for `tol2` (the `_entry_bars` convention of :mod:`binary_features_ext`).
Features are always read at the detection bar only (causal); labels look forward.

    ``up(t0, h)``         ``close[t0+h] > close[t0]``
    ``high_low(t0, h)``   the event-window extreme (the low at an ``at_bottom``
                          event, the high at an ``at_top`` event) is touched
                          again inside ``[t0+1, t0+h]`` (re-test)
    ``vol_expand(t0, h)`` realized vol of the ``h`` log-returns ending at ``t0``
                          exceeds ``VOL_RATIO_THRESHOLD`` x the previous ``h``
                          (prior window of the same length)

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

FAMILIES: tuple[str, ...] = ("up", "high_low", "vol_expand")
HORIZONS: tuple[int, ...] = (5, 8, 13, 21, 34, 55)
EVENT_MODES: tuple[str, ...] = ext.EVENT_MODES
PINNED_EVENT: dict[str, str] = {"USD": "exact", "CAD": "tol2"}
"""Per-market label geometry pinned by WI-048c (variant `*_full_k0.8`)."""
VOL_RATIO_THRESHOLD = 1.0
MIN_POSITIVES = 25
"""Sparse-cell flag for the density probe (CB-04 calibration floor)."""

__all__ = ["DEFAULT_SMOKE_DIR", "EVENT_MODES", "FAMILIES", "HORIZONS", "MIN_POSITIVES",
           "PINNED_EVENT", "PROBE_NAME", "VOL_RATIO_THRESHOLD", "build_probe_report",
           "build_targets_panel", "high_low_labels", "iter_events", "label_key", "main",
           "probe_table", "target_labels", "up_labels", "vol_expand_labels"]


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


def vol_expand_labels(close, t0, h: int, threshold: float = VOL_RATIO_THRESHOLD) -> np.ndarray:
    """1 when realized vol of the `h` log-returns ending at `t0` beats the prior `h`."""
    close = np.asarray(close, dtype="float64")
    t0 = np.asarray(t0, dtype=np.int64)
    lr = np.zeros(close.size, dtype="float64")
    if close.size > 1:
        with np.errstate(divide="ignore", invalid="ignore"):
            lr[1:] = np.log(close[1:] / close[:-1])
    lr = np.nan_to_num(lr, nan=0.0, posinf=0.0, neginf=0.0)
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


def target_labels(high, low, close, idx, states, families=FAMILIES,
                  horizons=HORIZONS) -> dict:
    """`{label_key(family, event, h): int8 array}` for one symbol's events."""
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


def build_targets_panel(market: str, *, families=FAMILIES, horizons=HORIZONS,
                        min_date: str = train.MIN_DATE, allow_fixture: bool = False,
                        max_symbols: int | None = None):
    """Stream one market -> (feature panel, `{label_key: int8}`) for the T2 families.

    The panel is the WI-036 variant panel (features read at the detection bar only);
    the labels are the three T2 families, aligned row-for-row with the panel.
    """
    panel, _ = ext.build_variant_panel(
        market, min_date=min_date, allow_fixture=allow_fixture, max_symbols=max_symbols,
        variants=ext.variant_grid()[:1], horizons=(int(min(horizons)),),
    )
    if panel.empty:
        return panel, {}
    parts: dict = {}
    n_rows = 0
    for _symbol, g, idx, states, _atr in iter_events(
        market, min_date=min_date, allow_fixture=allow_fixture, max_symbols=max_symbols
    ):
        n_rows += int(idx.size)
        lab = target_labels(g["high"].to_numpy("float64"), g["low"].to_numpy("float64"),
                            g["close"].to_numpy("float64"), idx, states, families, horizons)
        for key, arr in lab.items():
            parts.setdefault(key, []).append(arr)
    if n_rows != len(panel):
        raise RuntimeError(f"label/panel row mismatch for {market}: {n_rows} != {len(panel)}")
    return panel, {k: np.concatenate(v).astype("int8") for k, v in parts.items()}


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
