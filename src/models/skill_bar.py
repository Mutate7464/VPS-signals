"""Explicit skill bar for WI-009b: contrastive ranker vs the E5 factor baseline.

Why this module exists
----------------------
WI-009 evaluated the model against the five E5 factors on a 10-date slice but
the gate brief set **no numeric bar**, so the result could not be judged by an
agent. WI-009b fixes the bar in the plan and enforces it here, on a *widened*
purged validation window:

* clause (a) — the model's within-date val rank-IC must exceed the |IC| of the
  best single E5 factor **on the same rows and the same dates**;
* clause (b) — the model's `|t| > 2` **and** every one of at least two disjoint
  contiguous sub-windows of the val set has `|t| > 2` with the same sign as the
  full-window model IC (guards against single-regime luck).

The metric is always `within_date_rank_ic` from `src.models.pair_sampler` — the
same score-based within-date Spearman rank-IC used to train/evaluate WI-009.
Class-label IC and pooled magnitude IC are never used (WI-002 lesson).

This module deliberately has no torch dependency: it is pure numpy/pandas so it
can be unit-tested on synthetic IC vectors without touching the host budget.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

from src.factors.e5_baseline import E5_FACTORS
from src.models.pair_sampler import within_date_rank_ic

__all__ = [
    "EMBARGO_TD",
    "E5_FACTORS",
    "purged_date_split",
    "sub_window_split",
    "factor_ics_from_panel",
    "stats_for_rows",
    "skill_bar_verdict",
    "write_comparison_report",
]

# Purge gap between the last training date and the first validation date. The
# forward label is a 15-trading-day return, so 20td of separation keeps every
# training label from reaching into the validation window.
EMBARGO_TD = 20

# Minimum number of held-out dates for the widened window (WI-009b goal).
MIN_VAL_DATES = 60

# |t| floor for an IC to count as established (both clauses).
T_FLOOR = 2.0


def purged_date_split(
    dates,
    val_dates: int,
    embargo_td: int = EMBARGO_TD,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Chronological purged split of an arbitrary date column.

    Validation is the last `val_dates` unique dates; training is everything
    before it, minus a purge gap of `embargo_td` dates. The purge gap is
    therefore *excluded from both folds* — no row from it is trained or scored.

    Args:
        dates: per-row dates (any dtype sortable/normalisable by pandas).
        val_dates: exact number of held-out dates (not a fraction).
        embargo_td: purge gap in trading days.

    Returns:
        (train_dates, val_dates_sorted, purge_gap) where `purge_gap` is the
        number of unique dates strictly between the last train date and the
        first val date (equals `embargo_td` by construction).

    Raises:
        ValueError: if the panel cannot supply the requested window + purge.
    """
    if val_dates < 1:
        raise ValueError(f"val_dates must be >= 1, got {val_dates}")
    if embargo_td < 0:
        raise ValueError(f"embargo_td must be >= 0, got {embargo_td}")

    uniq = np.sort(pd.unique(np.asarray(dates)))
    needed = val_dates + embargo_td + 1
    if len(uniq) < needed:
        raise ValueError(
            f"need >= {needed} dates for val_dates={val_dates} + embargo={embargo_td}, got {len(uniq)}"
        )

    val = uniq[-val_dates:]
    cut = len(uniq) - val_dates - embargo_td
    train = uniq[:cut]

    # Positional gap between the folds (positions, never `pd.factorize` codes —
    # the WI-009 leak: codes are assignment-order, not chronological order).
    last_train_pos = int(np.searchsorted(uniq, train[-1]))
    first_val_pos = int(np.searchsorted(uniq, val[0]))
    purge_gap = first_val_pos - last_train_pos - 1
    if purge_gap < embargo_td:
        raise AssertionError(f"purge gap {purge_gap} < embargo {embargo_td}")
    return train, val, purge_gap


def sub_window_split(val_dates, n_windows: int = 2) -> list[np.ndarray]:
    """Split the ordered val dates into `n_windows` disjoint contiguous blocks.

    Blocks are as equal as `np.array_split` allows and cover the window exactly
    (no date in two blocks, no val date omitted). Used for the clause-(b)
    sign/stability guard against a single-regime fluke.
    """
    if n_windows < 2:
        raise ValueError(f"need >= 2 sub-windows for the stability guard, got {n_windows}")
    v = np.sort(pd.unique(np.asarray(val_dates)))
    if len(v) < n_windows:
        raise ValueError(f"cannot split {len(v)} dates into {n_windows} non-empty blocks")
    blocks = [np.asarray(b) for b in np.array_split(v, n_windows)]
    if any(len(b) == 0 for b in blocks):
        raise ValueError(f"empty sub-window for {len(v)} dates / {n_windows} blocks")
    return blocks


def stats_for_rows(
    panel: pd.DataFrame,
    score_col: str,
    target_col: str = "fwd_atr_ret_15",
) -> tuple[float, float, int]:
    """Within-date rank-IC (+t, n_dates) for one score column over `panel` rows."""
    return within_date_rank_ic(
        panel[score_col].to_numpy(dtype="float64"),
        panel[target_col].to_numpy(dtype="float64"),
        panel["date"].to_numpy(),
    )


def factor_ics_from_panel(
    panel: pd.DataFrame,
    factors=E5_FACTORS,
    prefix: str = "e5_",
    target_col: str = "fwd_atr_ret_15",
) -> dict[str, tuple[float, float, int]]:
    """Per-factor within-date rank-IC on exactly the rows handed in."""
    out: dict[str, tuple[float, float, int]] = {}
    for fac in factors:
        col = f"{prefix}{fac}"
        if col not in panel.columns:
            raise KeyError(f"factor column {col} missing from panel")
        out[fac] = stats_for_rows(panel, col, target_col)
    return out


def _finite(x) -> bool:
    return x is not None and bool(np.isfinite(x))


def skill_bar_verdict(
    model_ic: float,
    model_t: float,
    factor_stats: dict[str, tuple[float, float, int]],
    sub_stats: list[tuple[float, float, int]],
) -> dict:
    """Evaluate both skill-bar clauses and return a JSON-serialisable verdict.

    Clause (a): `|model_ic| > |best factor ic|` on the same rows/dates.
    Clause (b): `|model_t| > 2` and >= 2 sub-windows each with `|t| > 2` and the
    same IC sign as the model's full-window IC.

    A non-finite model IC or t fails the bar (no credit for undefined skill).
    """
    finite_factors = {k: v for k, v in factor_stats.items() if _finite(v[0])}
    if not finite_factors:
        raise ValueError("no finite factor ICs to compare against")

    best_name, best = max(finite_factors.items(), key=lambda kv: abs(kv[1][0]))
    best_abs = float(abs(best[0]))

    a_pass = _finite(model_ic) and abs(model_ic) > best_abs
    clause_a = {
        "passed": bool(a_pass),
        "model_abs_ic": float(abs(model_ic)) if _finite(model_ic) else None,
        "best_factor": best_name,
        "best_factor_abs_ic": best_abs,
        "margin": (float(abs(model_ic)) - best_abs) if _finite(model_ic) else None,
        "factor_table": {k: {"ic": float(v[0]), "t": float(v[1]), "n_dates": int(v[2])}
                         for k, v in factor_stats.items()},
    }

    same_sign = True
    all_t = True
    sub_detail = []
    for i, (ic, t, n) in enumerate(sub_stats):
        sign_ok = _finite(ic) and _finite(model_ic) and np.sign(ic) == np.sign(model_ic)
        t_ok = _finite(t) and abs(t) > T_FLOOR
        same_sign = same_sign and bool(sign_ok)
        all_t = all_t and bool(t_ok)
        sub_detail.append({"window": i + 1, "ic": float(ic) if _finite(ic) else None,
                           "t": float(t) if _finite(t) else None, "n_dates": int(n),
                           "sign_matches_model": bool(sign_ok), "abs_t_gt_2": bool(t_ok)})

    b_pass = (
        _finite(model_t)
        and abs(model_t) > T_FLOOR
        and len(sub_stats) >= 2
        and same_sign
        and all_t
    )
    clause_b = {
        "passed": bool(b_pass),
        "model_t": float(model_t) if _finite(model_t) else None,
        "model_passes_t_floor": bool(_finite(model_t) and abs(model_t) > T_FLOOR),
        "n_sub_windows": len(sub_stats),
        "all_windows_same_sign": bool(same_sign),
        "all_windows_abs_t_gt_2": bool(all_t),
        "sub_windows": sub_detail,
    }

    caveats: list[str] = []
    sign_agrees = bool(_finite(model_ic) and np.sign(model_ic) == np.sign(best[0]))
    if _finite(model_ic) and not sign_agrees:
        caveats.append(
            "SIGN INVERTED — the model's val IC has the opposite sign to the best factor "
            f"({model_ic:+.4f} vs `{best_name}` {best[0]:+.4f}). Clause (a) is a |IC| comparison, "
            "so it is met in MAGNITUDE only: the model is anti-correlated with forward returns "
            "on this window, and a sign flip (which would make the sign positive) is not claimed "
            "here because it would be chosen on this same window."
        )
    if _finite(model_ic) and best_abs > 0:
        rel = (abs(model_ic) - best_abs) / best_abs
        if 0 <= rel < 0.10:
            caveats.append(
                f"THIN MARGIN — |IC| exceeds the best factor by only {rel * 100:.1f}% relative; "
                "a margin this small is not robust to a different window or seed."
            )

    return {
        "passed": bool(a_pass and b_pass),
        "sign_agrees_with_best_factor": sign_agrees,
        "caveats": caveats,
        "clause_a": clause_a,
        "clause_b": clause_b,
        "criteria": {
            "clause_a": "model |val rank-IC| > best single E5 factor |IC| on the same dates/rows",
            "clause_b": f"model |t| > {T_FLOOR} and >=2 disjoint sub-windows with |t| > {T_FLOOR} "
                        "and the same IC sign",
        },
    }


def _fmt_ic(x, scale: float = 1.0):
    if not _finite(x):
        return "n/a"
    return f"{x / scale:+.4f}"


def write_comparison_report(path: str | Path, ctx: dict) -> Path:
    """Write the WI-009b model-vs-factors markdown comparison + verdict."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    verdict = ctx["skill_bar"]
    a = verdict["clause_a"]
    b = verdict["clause_b"]

    val_dates = ctx["val_dates"]
    n_val = len(val_dates)
    lines = [
        f"# WI-009b — contrastive ranker vs E5 factor baseline ({ctx['market']})",
        "",
        f"- Generated (UTC): {ctx.get('generated_utc') or dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Dataset: `{ctx['market']}` feature panel, {ctx['n_rows']:,} rows · "
        f"{ctx['n_features']} float32 features · {ctx['n_symbols']} symbols",
        f"- Validation window: **{n_val} held-out dates** ({ctx['val_start']} → {ctx['val_end']}), "
        f"purged chronological split, {ctx['embargo_td']}td purge gap",
        "- Identical rows and dates for the model and every factor (same-row harness: "
        "`src/models/pair_sampler.within_date_rank_ic`).",
        f"- Training: {ctx['n_train_dates']} dates ({ctx['train_start']} → {ctx['train_end']}), "
        f"{ctx['epochs_run']} epochs"
        + (f", early-stopped (patience {ctx['patience']})" if ctx.get("early_stopped") else "")
        + f", {ctx['train_minutes']:.1f} min wall clock, selected epoch {ctx['best_epoch']}",
        "- Metric: score-based within-date Spearman rank-IC vs `fwd_atr_ret_15` "
        "(never class-label IC).",
        "",
        "## Model vs the five E5 factors — same val rows, same val dates",
        "",
        "| Ranker | mean IC | \\|IC\\| | t | dates |",
        "| :--- | ---: | ---: | ---: | ---: |",
        f"| **contrastive ranker (selected epoch {ctx['best_epoch']})** | "
        f"{_fmt_ic(ctx['model_ic'])} | {_fmt_ic(abs(ctx['model_ic']) if _finite(ctx['model_ic']) else float('nan'))} | "
        f"{_fmt_ic(ctx['model_t'])} | {n_val} |",
    ]
    for fac, st in sorted(a["factor_table"].items(), key=lambda kv: -abs(kv[1]["ic"])):
        lines.append(f"| `e5_{fac}` (factor) | {st['ic']:+.4f} | {abs(st['ic']):.4f} | "
                     f"{st['t']:+.2f} | {st['n_dates']} |")

    final_note = ""
    if ctx.get("final_epoch_ic") is not None:
        final_note = (
            f"Final epoch ({ctx.get('epochs_run')}) scored IC {_fmt_ic(ctx['final_epoch_ic'])} "
            f"(t {_fmt_ic(ctx.get('final_epoch_t'))}); the model above is the epoch selected on "
            "the val rank-IC, so this row is optimistically selected — compare the two to gauge "
            "the selection effect."
        )

    lines += [
        "",
        "## Verdict against the skill bar",
        "",
        f"- **Clause (a)** — model beats the best single factor on the same dates: "
        f"**{'PASS' if a['passed'] else 'FAIL'}** "
        f"(model |IC| {_fmt_ic(a['model_abs_ic'])} vs `e5_{a['best_factor']}` "
        f"|IC| {_fmt_ic(a['best_factor_abs_ic'])}, margin {_fmt_ic(a['margin'])})",
        f"- **Clause (b)** — |t| > {T_FLOOR} with stable sign in >= 2 disjoint sub-windows: "
        f"**{'PASS' if b['passed'] else 'FAIL'}** "
        f"(model t {_fmt_ic(b['model_t'])}, {b['n_sub_windows']} sub-windows, "
        f"same sign in all: {b['all_windows_same_sign']}, |t|>2 in all: {b['all_windows_abs_t_gt_2']})",
        f"- **SKILL BAR: {'PASS' if verdict['passed'] else 'FAIL'}"
        + (" (with caveats — see below)**" if verdict.get("caveats") and verdict["passed"] else "**"),
        "",
    ]
    if verdict.get("caveats"):
        lines += ["**Caveats — read before acting on the verdict:**", ""]
        lines += [f"- {c}" for c in verdict["caveats"]]
        lines += [""]
    if final_note:
        lines += [final_note, ""]

    if b.get("sub_windows"):
        lines += [
            "### Sub-window stability (disjoint contiguous blocks of the val window)",
            "",
            "| Sub-window | dates | model mean IC | model t | best factor on that block | best \\|IC\\| |",
            "| :--- | ---: | ---: | ---: | :--- | ---: |",
        ]
        for w in b["sub_windows"]:
            fb = (ctx.get("sub_window_best_factor") or {}).get(w["window"], {})
            lines.append(
                f"| {w['window']} | {w['n_dates']} | {_fmt_ic(w['ic'])} | {_fmt_ic(w['t'])} | "
                f"`{fb.get('name', 'n/a')}` | {_fmt_ic(fb.get('abs_ic'))} |"
            )
        lines.append("")

    lines += [
        "## Reading notes",
        "",
        "- The baseline moves with the window: `rev_1m` was -0.0094 over the full CAD sample but "
        "-0.157 on the 10 recent dates WI-009 used, so the widened window's factor numbers are "
        "part of the deliverable, not a constant.",
        "- The ~20-trading-day shortlist lag (feature rows require all four forward targets) is "
        "**out of scope** for WI-009b and is unchanged by this work item.",
        "- Sub-window factor ICs are reported as information; clause (b) is a stability guard on "
        "the model's own IC, as fixed in the plan.",
        "",
    ]
    path.write_text("\n".join(lines) + "\n")
    return path