"""WI-011 — purged walk-forward evaluation helpers and conditional expectancy.

Why this module exists
----------------------
Steps 4, 5 and 6 all measure forward-return distributions conditional on a
trailing condition, and all of them must obey the plan's evaluation discipline:

* **chronological walk-forward folds** with the WI-009 `PurgedWalkForwardSplit`
  (positions into the *sorted unique date array*, never `pd.factorize` codes);
* **purge at least 20 trading days and at least the evaluated horizon**, so an
  overlapping forward label cannot straddle a fold boundary — a 120-day label
  therefore gets a 120-day embargo, not the flat 20-day one;
* **two disjoint chronological sub-windows** for the stable-sign test, and a
  finding is only "stable" when both windows are evaluable, agree in sign, and
  each clears |t| > 2 (the WI-009b/c standing clause);
* **insufficient samples are reported, never papered over**.

No model is fitted anywhere: the folds exist to bound label overlap, not to
train. Nothing in this module reads a condition column to *define* a threshold —
thresholds live in `src/wi011/conditions.py` and were fixed before evaluation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = [
    "MIN_N",
    "MIN_DATES",
    "MIN_PURGE_TD",
    "T_FLOOR",
    "condition_rows",
    "evaluate_condition",
    "fold_blocks",
    "insufficient",
    "sub_windows",
    "window_stats",
]

MIN_PURGE_TD = 20
"""WI-009's flat embargo floor (trading days)."""

T_FLOOR = 2.0
"""|t| floor for a finding to count as established (both sub-windows)."""

MIN_N = 30
"""Below this many fired observations a statistic is reported as insufficient."""

MIN_DATES = 3
"""Below this many dated cross-sections the clustered t-stat is undefined."""


# --------------------------------------------------------------------------- #
# Fold / window geometry
# --------------------------------------------------------------------------- #
def fold_blocks(
    uniq_dates,
    horizon: int,
    n_splits: int = 5,
    initial_train_fraction: float = 0.40,
    min_purge_td: int = MIN_PURGE_TD,
) -> list[dict]:
    """Purged walk-forward validation blocks for one horizon.

    `embargo_td = max(min_purge_td, horizon)` — the plan's "purge at least 20
    trading days and at least the evaluated horizon". Each record keeps the
    validation window's date positions and the last position whose forward
    window still ends inside the block (`label_end_pos`), which is the second
    boundary rule: rows whose label window would spill into the next block are
    dropped rather than silently counted twice.
    """
    from src.xgb_trainer import PurgedWalkForwardSplit

    uniq = np.sort(pd.unique(np.asarray(uniq_dates)))
    embargo = int(max(min_purge_td, horizon))
    splitter = PurgedWalkForwardSplit(
        n_splits=n_splits, embargo_td=embargo, initial_train_fraction=initial_train_fraction
    )
    out: list[dict] = []
    for k, (tr_pos, va_pos) in enumerate(splitter.split(uniq)):
        if va_pos.size == 0:
            continue
        v0, v1 = int(va_pos.min()), int(va_pos.max())
        out.append(
            {
                "fold": int(k),
                "embargo_td": embargo,
                "val_pos_min": v0,
                "val_pos_max": v1,
                "train_n": int(tr_pos.size),
                "val_n": int(va_pos.size),
                "label_end_pos": v1 - horizon,
                "val_min": str(pd.Timestamp(uniq[v0]).date()),
                "val_max": str(pd.Timestamp(uniq[v1]).date()),
            }
        )
    return out


def sub_windows(uniq_dates, n: int = 2) -> list[tuple[str, str]]:
    """`n` disjoint contiguous chronological sub-windows, as (first, last) date strings."""
    uniq = np.sort(pd.unique(np.asarray(uniq_dates)))
    if uniq.size < n:
        raise ValueError(f"need >= {n} unique dates for {n} sub-windows, got {uniq.size}")
    bounds = np.linspace(0, uniq.size, n + 1).astype(int)
    out = []
    for i in range(n):
        lo, hi = bounds[i], max(bounds[i + 1] - 1, bounds[i])
        out.append((str(pd.Timestamp(uniq[lo]).date()), str(pd.Timestamp(uniq[hi]).date())))
    return out


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #
def insufficient(n: int, n_dates: int) -> bool:
    """True when a statistic must be reported as insufficient rather than quoted."""
    return int(n) < MIN_N or int(n_dates) < MIN_DATES


def date_overall_mean(values_bps: np.ndarray, dates: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The all-rows mean forward label for each unique date (the market component).

    Returns `(uniq_dates, means)`; the mean over a date's rows is the equal-weight
    'market' forward return for that date, i.e. the component a condition inherits
    when it fires on a strong-market day rather than on a strong *name*.
    """
    v = np.asarray(values_bps, dtype="float64")
    frame = pd.DataFrame({"v": v, "d": np.asarray(dates)})
    g = frame.groupby("d", sort=True)["v"].mean()
    return g.index.to_numpy(), g.to_numpy()


def within_stats(
    values_bps: np.ndarray,
    values_atr: np.ndarray,
    dates: np.ndarray,
    uniq_dates: np.ndarray,
    overall_mean: np.ndarray,
) -> dict:
    """Split a condition's mean forward return into market and within-date parts.

    `market_bps` = mean over firing rows of that date's all-name mean;
    `within_bps`  = mean over firing rows of (row − its date's all-name mean),
    i.e. the pure cross-sectional deviation — "is this name rich or cheap today
    relative to its peers", stripped of the day's market move;
    `t_within`    = t across dates on the per-date mean deviation.
    """
    v = np.asarray(values_bps, dtype="float64")
    a = np.asarray(values_atr, dtype="float64")
    d = np.asarray(dates)
    mask = np.isfinite(v)
    v, a, d = v[mask], a[mask], d[mask]
    out = {
        "n": int(v.size),
        "n_dates": 0,
        "market_bps": float("nan"),
        "within_bps": float("nan"),
        "t_within": float("nan"),
        "insufficient": True,
    }
    if v.size == 0:
        return out
    pos = np.searchsorted(uniq_dates, d)
    day_mean = overall_mean[pos]
    dev = v - day_mean
    frame = pd.DataFrame({"dv": dev, "d": d})
    per_date = frame.groupby("d", sort=False)["dv"].mean().to_numpy()
    t_within = (
        float(per_date.mean() / (per_date.std(ddof=1) / np.sqrt(per_date.size)))
        if per_date.size > 2 and per_date.std(ddof=1) > 0
        else float("nan")
    )
    out.update(
        {
            "n": int(v.size),
            "n_dates": int(per_date.size),
            "market_bps": float(np.nanmean(day_mean)),
            "within_bps": float(dev.mean()),
            "t_within": t_within,
            "insufficient": insufficient(int(v.size), int(per_date.size)),
        }
    )
    return out


def window_stats(values_bps: np.ndarray, values_atr: np.ndarray, dates: np.ndarray) -> dict:
    """Distribution and t-statistics of a forward label over a set of rows.

    Args:
        values_bps: forward *relative* return in bps.
        values_atr: forward ATR-multiple return (scale-free cross-check).
        dates: the observation date of each row.

    Returns:
        dict with `n`, `n_dates`, `mean_bps`, `std_bps`, `hit_rate`, `p05_bps`,
        `p95_bps`, `mean_atr`, `t_pooled` (naive, all rows) and `t_date`
        (per-date mean then t across dates — the cross-sectionally clustered
        statistic, which is the one to read when a condition fires on many names
        on the same day), plus `insufficient`.
    """
    v = np.asarray(values_bps, dtype="float64")
    a = np.asarray(values_atr, dtype="float64")
    d = np.asarray(dates)
    mask = np.isfinite(v)
    v, a, d = v[mask], a[mask], d[mask]
    n = int(v.size)
    out = {
        "n": n,
        "n_dates": 0,
        "mean_bps": float("nan"),
        "std_bps": float("nan"),
        "hit_rate": float("nan"),
        "p05_bps": float("nan"),
        "p95_bps": float("nan"),
        "mean_atr": float("nan"),
        "t_pooled": float("nan"),
        "t_date": float("nan"),
        "insufficient": True,
    }
    if n == 0:
        return out

    frame = pd.DataFrame({"v": v, "d": d})
    grp = frame.groupby("d", sort=False)["v"]
    per_date = grp.mean().to_numpy()
    out.update(
        {
            "n": n,
            "n_dates": int(per_date.size),
            "mean_bps": float(v.mean()),
            "std_bps": float(v.std(ddof=1)) if n > 1 else float("nan"),
            "hit_rate": float((v > 0.0).mean()),
            "p05_bps": float(np.quantile(v, 0.05)),
            "p95_bps": float(np.quantile(v, 0.95)),
            "mean_atr": float(a.mean()) if np.isfinite(a).any() else float("nan"),
            "t_pooled": float(v.mean() / (v.std(ddof=1) / np.sqrt(n))) if n > 2 and v.std(ddof=1) > 0 else float("nan"),
            "t_date": (
                float(per_date.mean() / (per_date.std(ddof=1) / np.sqrt(per_date.size)))
                if per_date.size > 2 and per_date.std(ddof=1) > 0
                else float("nan")
            ),
            "insufficient": insufficient(n, int(per_date.size)),
        }
    )
    return out


def condition_rows(panel: pd.DataFrame, cond_col: str, horizon: int) -> np.ndarray:
    """Boolean mask of rows where `cond_col` is defined and fires (NaN never fires)."""
    v = panel[cond_col].to_numpy(dtype="float64")
    return np.isfinite(v) & (v > 0.5)


def evaluate_condition(
    panel: pd.DataFrame,
    cond_col: str,
    horizon: int,
    date_positions: np.ndarray,
    folds: list[dict],
    windows: list[tuple[str, str]],
    baseline_mean_bps: float,
    uniq_dates: np.ndarray | None = None,
    overall_mean: np.ndarray | None = None,
) -> dict:
    """Full-sample, purged-fold and two-sub-window expectancy for one condition.

    Returns a dict with the three levels of statistics plus the derived flags:
    `stable_sign` (both sub-windows evaluable, same sign, both |t| > 2),
    `sign_disagreement` (both evaluable, opposite signs), `folds_used`, and the
    market/within-date decomposition with its own stability flag
    `stable_within_sign` (same construction, applied to the within-date
    deviation — the market-drift-controlled version of the same test).
    """
    ret_col, atr_col = f"fwd_ret_{horizon}", f"fwd_atr_ret_{horizon}"
    dates = panel["date"].to_numpy()
    fired = condition_rows(panel, cond_col, horizon)
    v_all = panel[ret_col].to_numpy(dtype="float64") * 1e4
    a_all = panel[atr_col].to_numpy(dtype="float64")

    if uniq_dates is None or overall_mean is None:
        uniq_dates, overall_mean = date_overall_mean(v_all, dates)

    full = window_stats(v_all[fired], a_all[fired], dates[fired])
    full_within = within_stats(v_all[fired], a_all[fired], dates[fired], uniq_dates, overall_mean)

    fold_rows = np.zeros(len(panel), dtype=bool)
    per_fold: list[dict] = []
    for f in folds:
        lo, hi_end = f["val_pos_min"], f["label_end_pos"]
        in_block = fired & (date_positions >= lo) & (date_positions <= hi_end)
        fold_rows |= in_block
        st = window_stats(v_all[in_block], a_all[in_block], dates[in_block])
        st["fold"] = f["fold"]
        st["val_min"] = f["val_min"]
        st["val_max"] = f["val_max"]
        per_fold.append(st)
    folded = window_stats(v_all[fold_rows], a_all[fold_rows], dates[fold_rows])

    win_stats = []
    win_within = []
    for lo, hi in windows:
        in_win = fired & (dates >= np.datetime64(lo)) & (dates <= np.datetime64(hi))
        st = window_stats(v_all[in_win], a_all[in_win], dates[in_win])
        st["window"] = f"{lo}→{hi}"
        win_stats.append(st)
        wt = within_stats(v_all[in_win], a_all[in_win], dates[in_win], uniq_dates, overall_mean)
        wt["window"] = f"{lo}→{hi}"
        win_within.append(wt)

    evaluable = [not s["insufficient"] for s in win_stats]
    both = all(evaluable) and len(win_stats) == 2
    same_sign = both and (np.sign(win_stats[0]["mean_bps"]) == np.sign(win_stats[1]["mean_bps"]))
    both_strong = both and all(abs(s["t_date"]) > T_FLOOR for s in win_stats)
    stable = bool(same_sign and both_strong)

    w_evaluable = [not s["insufficient"] for s in win_within]
    both_w = all(w_evaluable) and len(win_within) == 2
    same_sign_w = both_w and (
        np.sign(win_within[0]["within_bps"]) == np.sign(win_within[1]["within_bps"])
    )
    strong_w = both_w and all(abs(s["t_within"]) > T_FLOOR for s in win_within)

    return {
        "condition": cond_col,
        "horizon": horizon,
        "full": full,
        "full_within": full_within,
        "purged": folded,
        "folds": per_fold,
        "folds_used": int(folded["n_dates"] > 0),
        "subwindows": win_stats,
        "subwindows_within": win_within,
        "evaluable_subwindows": int(sum(evaluable)),
        "same_sign": bool(same_sign),
        "stable_sign": stable,
        "sign_disagreement": bool(both and not same_sign),
        "stable_within_sign": bool(same_sign_w and strong_w),
        "within_sign_disagreement": bool(both_w and not same_sign_w),
        "excess_bps": float(full["mean_bps"] - baseline_mean_bps) if np.isfinite(full["mean_bps"]) else float("nan"),
    }