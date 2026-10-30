"""WI-016 Step 3 — rebuilt feature admission (D-016 §2).

The legacy Sprint-3 admission (`src.stat_metadata`, VIF 5.0 / MI p30) is kept
untouched for frozen WI-014 artifacts. WI-016 adds the accepted rebuild on the
unified grid (`src.feature_engine.compute_features_wi016`):

1. **ADF** — reuse `stat_metadata.adf_analysis` (trailing rolling Z-score flag).
2. **MI** — reuse `stat_metadata.compute_mi`, admitted at the *relaxed* MI
   percentile (`config/settings.yaml → wi016.mi_min_percentile`).
3. **VIF** — `stat_metadata.compute_vif_pruning` at the relaxed **8.0**.
4. **Uniqueness** — per target, cluster surviving features at absolute Spearman
   ``|rho| > 0.7`` and keep one representative per cluster, the member with the
   highest *same-sign* IC (the WI-009b clause: the IC must carry the same sign in
   both chronological sub-windows).
5. **Event floor** — admit a feature only if it has at least `500` labeled events.

The clustering / representative logic is pure and unit-tested in
``tests/test_wi016_features.py``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = BASE_DIR / "config" / "settings.yaml"

DEFAULTS = {
    "smooth_windows": [3, 8, 21, 55, 144, 233],
    "fast_fib_windows": [3, 6, 9, 15, 24, 39, 63, 102],
    "vif_threshold": 8.0,
    "mi_min_percentile": 20.0,
    "cluster_rho": 0.7,
    "min_labeled_events": 500,
}

__all__ = [
    "DEFAULTS",
    "admit_features",
    "cluster_features",
    "load_wi016_config",
    "min_events_ok",
    "run_market",
    "same_sign_ic",
    "select_representatives",
    "within_date_rank_ic",
]


def load_wi016_config(path: Path | str = CONFIG_PATH) -> dict:
    """The `wi016:` block of settings.yaml, filled with defaults."""
    cfg = dict(DEFAULTS)
    try:
        loaded = yaml.safe_load(Path(path).read_text()) or {}
    except FileNotFoundError:
        return cfg
    cfg.update(loaded.get("wi016", {}) or {})
    return cfg


# --------------------------------------------------------------------------- #
# Information coefficient (same-sign clause)
# --------------------------------------------------------------------------- #
def _rank_ic(feature: np.ndarray, target: np.ndarray) -> float:
    rf = pd.Series(feature).rank().to_numpy()
    rt = pd.Series(target).rank().to_numpy()
    if rf.std() == 0.0 or rt.std() == 0.0:
        return float("nan")
    return float(np.corrcoef(rf, rt)[0, 1])


def within_date_rank_ic(feature, target, dates) -> float:
    """Mean per-date rank correlation (the within-date IC used by the probe)."""
    df = pd.DataFrame(
        {"f": np.asarray(feature, dtype="float64"), "t": np.asarray(target, dtype="float64"),
         "d": np.asarray(dates)}
    ).replace([np.inf, -np.inf], np.nan).dropna()
    if df.empty or df["d"].nunique() < 2:
        return float("nan")

    def _ic(g: pd.DataFrame) -> float:
        if len(g) < 3:
            return float("nan")
        return _rank_ic(g["f"].to_numpy(), g["t"].to_numpy())

    ics = df.groupby("d", sort=False).apply(_ic)
    return float(ics.mean()) if ics.notna().any() else float("nan")


def same_sign_ic(feature, target, dates, n_windows: int = 2) -> dict:
    """IC plus the WI-009b same-sign flag across `n_windows` chronological halves."""
    f = np.asarray(feature, dtype="float64")
    t = np.asarray(target, dtype="float64")
    d = np.asarray(dates)
    ic = within_date_rank_ic(f, t, d)

    uniq = np.sort(pd.unique(d[np.isfinite(f) & np.isfinite(t)])) if len(d) else np.array([])
    win_ic: list[float] = []
    if uniq.size >= n_windows:
        bounds = np.linspace(0, uniq.size, n_windows + 1).astype(int)
        for i in range(n_windows):
            lo, hi = uniq[bounds[i]], uniq[max(bounds[i + 1] - 1, bounds[i])]
            m = (d >= lo) & (d <= hi)
            win_ic.append(within_date_rank_ic(f[m], t[m], d[m]))
    finite = [x for x in win_ic if np.isfinite(x)]
    same_sign = bool(
        len(finite) == n_windows and any(x != 0.0 for x in finite) and len({np.sign(x) for x in finite}) == 1
    )
    return {"ic": ic, "window_ic": win_ic, "same_sign": same_sign}


# --------------------------------------------------------------------------- #
# Correlation clustering + representatives
# --------------------------------------------------------------------------- #
def cluster_features(corr: pd.DataFrame, rho: float = 0.7) -> list[list[str]]:
    """Connected components of the feature graph with ``|Spearman rho| > rho``."""
    names = list(corr.columns)
    parent = {n: n for n in names}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i, a in enumerate(names):
        for b in names[i + 1:]:
            v = corr.at[a, b]
            if np.isfinite(v) and abs(v) > rho:
                union(a, b)

    clusters: dict[str, list[str]] = {}
    for n in names:
        clusters.setdefault(find(n), []).append(n)
    return [sorted(v) for v in clusters.values()]


def select_representatives(clusters: list[list[str]], ic_info: dict[str, dict]) -> list[str]:
    """One representative per cluster: highest same-sign |IC|, alphabetical tie-break.

    A feature whose IC is not same-sign ranks below every same-sign member; if no
    member is same-sign, the highest |IC| still represents the cluster so the
    cluster is never silently dropped.
    """

    def score(name: str) -> tuple[int, float]:
        info = ic_info.get(name, {})
        ic = info.get("ic", float("nan"))
        mag = abs(ic) if np.isfinite(ic) else -1.0
        return (1 if info.get("same_sign", False) else 0, mag)

    reps = [max(sorted(members), key=score) for members in clusters]
    return sorted(reps)


def min_events_ok(feature, target, min_events: int = 500) -> bool:
    """True when the feature has at least `min_events` labeled (finite) events."""
    f = np.asarray(feature, dtype="float64")
    t = np.asarray(target, dtype="float64")
    return int((np.isfinite(f) & np.isfinite(t)).sum()) >= int(min_events)


# --------------------------------------------------------------------------- #
# Per-target admission
# --------------------------------------------------------------------------- #
def admit_features(
    feature_frame: pd.DataFrame,
    target,
    feature_cols: list[str],
    dates=None,
    rho: float = 0.7,
    min_events: int = 500,
) -> dict:
    """Event floor + uniqueness admission for one target.

    Returns `admitted` (the per-cluster representatives that clear the event
    floor), the `clusters`, the `ic` evidence and the event-floor `dropped`.
    """
    t = np.asarray(target, dtype="float64")
    d = np.asarray(dates) if dates is not None else np.arange(len(t))

    kept, dropped_events = [], []
    for f in feature_cols:
        (kept if min_events_ok(feature_frame[f].to_numpy(), t, min_events) else dropped_events).append(f)

    if not kept:
        return {"admitted": [], "clusters": [], "ic": {}, "dropped_events": dropped_events}

    ic_info = {f: same_sign_ic(feature_frame[f].to_numpy(), t, d) for f in kept}
    corr = feature_frame[kept].corr(method="spearman")
    clusters = cluster_features(corr, rho=rho)
    reps = select_representatives(clusters, ic_info)
    return {
        "admitted": reps,
        "clusters": clusters,
        "ic": ic_info,
        "dropped_events": dropped_events,
    }


def run_market(feature_frame: pd.DataFrame, targets_frame: pd.DataFrame, market: str) -> dict:
    """Full WI-016 admission for one market: ADF/MI/VIF then uniqueness + event floor.

    `feature_frame` carries the unified grid + `[date, symbol, market]`;
    `targets_frame` carries `[date, symbol, market]` + the label columns.
    Returns the per-target admitted feature list plus the ADF/MI/VIF evidence.
    """
    from src import stat_metadata as sm
    from src.targets import TARGET_COLUMNS

    cfg = load_wi016_config()
    ids = [c for c in ("date", "symbol", "market") if c in feature_frame.columns and c in targets_frame.columns]
    df = feature_frame.merge(targets_frame, on=ids, how="inner")
    feature_cols = [c for c in feature_frame.columns if c not in ("date", "symbol", "market")]

    train, cutoff = sm.train_split(df)
    adf = sm.adf_analysis(train, feature_cols)
    mi = sm.compute_mi(train, feature_cols)
    mean_mi = {f: float(np.mean([mi[t][f] for t in TARGET_COLUMNS])) for f in feature_cols}
    surviving, dropped = sm.compute_vif_pruning(
        train, feature_cols, mean_mi, vif_threshold=cfg["vif_threshold"]
    )
    wl = sm.whitelist_per_target(surviving, mi, cfg["mi_min_percentile"])

    admitted = {}
    for t in TARGET_COLUMNS:
        res = admit_features(
            df, df[t].to_numpy(), wl[t], dates=df["date"].to_numpy(),
            rho=cfg["cluster_rho"], min_events=cfg["min_labeled_events"],
        )
        admitted[t] = res["admitted"]
    return {
        "market": market,
        "train_cutoff_date": str(cutoff.date()),
        "vif_threshold": cfg["vif_threshold"],
        "mi_min_percentile": cfg["mi_min_percentile"],
        "cluster_rho": cfg["cluster_rho"],
        "min_labeled_events": cfg["min_labeled_events"],
        "stationarity": adf,
        "dropped_features": dropped,
        "surviving_features": surviving,
        "whitelist_per_target": wl,
        "admitted_per_target": admitted,
    }

