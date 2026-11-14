"""WI-011 Step 5 — per-symbol time-series (TS) momentum rules and their
cross-sectional (CS) counterparts, with the TS-vs-CS decomposition.

The question this answers
------------------------
Every prior CAD run ranked *names against each other* (`rev_1m`, `mom_12_1`
within-date rank-IC). WI-011 asks the never-tested question: does a symbol's
**own past** say anything about its own forward return — and if so, is the
expectancy really the *level* (TS: "this name has gone up") or only the
*relative rank* (CS: "this name has gone up more than its peers today")?

Rule vocabulary (declared before evaluation, fixed thresholds)
--------------------------------------------------------------
TS rules (own past only):
    ts_up_{w}             own trailing return over w > 0
    ts_down_{w}           own trailing return over w < 0
    ts_strong_up_{w}      own trailing return normalised by vol*sqrt(w) >= +0.5
    ts_strong_down_{w}    ... <= -0.5   (the volatility-scaled variant)
CS counterparts (same trailing return, ranked within date):
    cs_up_{w}             own trailing return above the same-date median
    cs_top_quartile_{w}   within-date top quartile
    cs_bottom_quartile_{w} within-date bottom quartile

The CS flags are the *same input* viewed cross-sectionally, so a TS-vs-CS
comparison holds the information content fixed and varies only the framing. No
cross-sectional ranking of the *model score* is involved, no model is trained,
and every input is a trailing own-history quantity (plan Step 5 "do NOT" clause).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

__all__ = [
    "TS_STRONG_Z",
    "TS_WINDOWS",
    "TS_RULE_SPECS",
    "TSCRule",
    "compute_ts_cs_conditions",
    "ts_cs_pairs",
]

TS_WINDOWS: tuple[int, ...] = (20, 60, 120)
"""Own-past return windows for the TS probe (1, 3 and 6 trading months)."""

TS_STRONG_Z: float = 0.5
"""Volatility-scaled strength threshold: tret_w / (vol_20 * sqrt(w)) >= 0.5."""


@dataclass(frozen=True)
class TSCRule:
    """One TS or CS rule: name, side, formula text, framing."""

    name: str
    side: str      # up | down
    framing: str   # TS | CS
    formula: str
    window: int


TS_RULE_SPECS: tuple[TSCRule, ...] = tuple(
    rule
    for w in TS_WINDOWS
    for rule in (
        TSCRule(f"ts_up_{w}", "up", "TS", f"own trailing {w}d return > 0", w),
        TSCRule(f"ts_down_{w}", "down", "TS", f"own trailing {w}d return < 0", w),
        TSCRule(
            f"ts_strong_up_{w}",
            "up",
            "TS",
            f"own trailing {w}d return / (vol_20*sqrt({w})) >= +{TS_STRONG_Z}",
            w,
        ),
        TSCRule(
            f"ts_strong_down_{w}",
            "down",
            "TS",
            f"own trailing {w}d return / (vol_20*sqrt({w})) <= -{TS_STRONG_Z}",
            w,
        ),
        TSCRule(f"cs_up_{w}", "up", "CS", f"own trailing {w}d return above the same-date median", w),
        TSCRule(f"cs_down_{w}", "down", "CS", f"own trailing {w}d return below the same-date median", w),
        TSCRule(f"cs_top_quartile_{w}", "up", "CS", f"within-date top quartile of the trailing {w}d return", w),
        TSCRule(f"cs_bottom_quartile_{w}", "down", "CS", f"within-date bottom quartile of the trailing {w}d return", w),
    )
)


def ts_cs_pairs() -> list[tuple[str, str, int, str]]:
    """Matched (TS rule, CS rule, window, element) pairs for the decomposition.

    'Element' names the shared information content: the own trailing return over
    `w` days (sign for the level rules, rank for the cross-sectional rules).
    """
    pairs: list[tuple[str, str, int, str]] = []
    for w in TS_WINDOWS:
        pairs.append((f"ts_up_{w}", f"cs_up_{w}", w, f"trailing {w}d return"))
        pairs.append((f"ts_strong_up_{w}", f"cs_top_quartile_{w}", w, f"vol-scaled trailing {w}d return"))
        pairs.append((f"ts_down_{w}", f"cs_bottom_quartile_{w}", w, f"trailing {w}d return (down side)"))
    return pairs


def _tri(mask: np.ndarray, defined: np.ndarray) -> np.ndarray:
    return np.where(np.asarray(defined, dtype=bool), np.where(np.asarray(mask, dtype=bool), 1.0, 0.0), np.nan).astype(
        "float32"
    )


def compute_ts_cs_conditions(panel: pd.DataFrame, windows=TS_WINDOWS) -> pd.DataFrame:
    """Build the TS + CS condition columns for an already-built analysis panel.

    `panel` must carry `tret_{w}` and `tret_z_{w}` (from `src.wi011.panel`) and a
    `date` column; the CS flags are per-date statistics over the symbols present
    that day, which is exactly the cross-sectional framing under test. A date
    with fewer than 5 symbols contributes NaN (undefined), never a guessed rank.
    """
    out: dict[str, np.ndarray] = {}
    dates = panel["date"]
    min_names = 5
    for w in windows:
        r = panel[f"tret_{w}"].to_numpy(dtype="float64")
        z = panel[f"tret_z_{w}"].to_numpy(dtype="float64")
        out[f"ts_up_{w}"] = _tri(r > 0.0, np.isfinite(r))
        out[f"ts_down_{w}"] = _tri(r < 0.0, np.isfinite(r))
        out[f"ts_strong_up_{w}"] = _tri(z >= TS_STRONG_Z, np.isfinite(z))
        out[f"ts_strong_down_{w}"] = _tri(z <= -TS_STRONG_Z, np.isfinite(z))

        grp = pd.Series(r, index=panel.index).groupby(dates)
        med = grp.transform("median").to_numpy(dtype="float64")
        q25 = grp.transform(lambda s: s.quantile(0.25)).to_numpy(dtype="float64")
        q75 = grp.transform(lambda s: s.quantile(0.75)).to_numpy(dtype="float64")
        n_names = grp.transform("size").to_numpy(dtype="float64")
        defined = np.isfinite(r) & np.isfinite(med) & (n_names >= min_names)
        out[f"cs_up_{w}"] = _tri(r > med, defined)
        out[f"cs_down_{w}"] = _tri(r < med, defined)
        out[f"cs_top_quartile_{w}"] = _tri(r >= q75, defined & np.isfinite(q75))
        out[f"cs_bottom_quartile_{w}"] = _tri(r <= q25, defined & np.isfinite(q25))
    return pd.DataFrame(out, index=panel.index).astype("float32")