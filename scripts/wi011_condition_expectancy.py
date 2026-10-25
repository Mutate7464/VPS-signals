"""WI-011 Step 4 — conditional expectancy and the eight-horizon sweep.

For every declared condition (the 26 Step 2 conditions plus the 12 Step 3
`ind_*` extremes) and every fixed horizon {1,2,5,10,15,20,60,120} trading days,
this script reports the forward-return distribution of the rows where the
condition fires:

    mean (bps and ATR multiples), standard deviation, hit rate, 5% tails,
    observation counts, naive t and date-clustered t;

evaluated three ways, each with its own discipline:

1. **full sample** — descriptive baseline over all firing rows;
2. **purged walk-forward folds** — WI-009 `PurgedWalkForwardSplit` with
   `embargo_td = max(20, horizon)` *and* firing rows whose forward window would
   spill past the fold's last date dropped (`label_end_pos`), so overlapping
   labels never cross a fold boundary;
3. **two disjoint chronological sub-windows** — the stable-sign test: a finding
   is `STABLE_SIGN` only when both windows are evaluable, agree in sign and each
   clears |t| > 2. Sign disagreement is marked `UNSTABLE_SIGN`; a window that
   cannot be evaluated is marked not-evaluable and never called stable.

Markers the plan's verify command greps for:
    HORIZONS: 1,2,5,10,15,20,60,120 / PURGE_TD: ... / SUBWINDOWS: 2
    STABLE_SIGN_COUNT / UNSTABLE_SIGN_COUNT
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.wi011 import HORIZONS, MARKET  # noqa: E402
from src.wi011.conditions import CONDITION_SPECS, indicator_condition_names, load_selected_indicators  # noqa: E402
from src.wi011.stats import (  # noqa: E402
    MIN_PURGE_TD,
    T_FLOOR,
    date_overall_mean,
    evaluate_condition,
    fold_blocks,
    sub_windows,
    window_stats,
)
from src.wi011.panel import build_condition_panel  # noqa: E402

REPORT = BASE_DIR / "reports" / "wi011_condition_expectancy.md"

SHADOW_PAIRS = {
    "ind_pct_from_high_f102_high": "ch52_high",
    "ind_pct_from_high_f102_low": "ch52_low",
    "ind_fib_dist_f102_high": "ch52_high",
    "ind_fib_dist_f102_low": "ch52_low",
    "ind_di_spread_100_high": "ch52_high",
    "ind_di_spread_100_low": "ch52_low",
    "ind_atr_pct_100_high": "vol_high",
    "ind_atr_pct_100_low": "vol_low",
    "ind_vwap_zscore_50_high": "trend_up",
    "ind_vwap_zscore_50_low": "trend_down",
    "ind_vwap_zscore_100_high": "trend_up",
    "ind_vwap_zscore_100_low": "trend_down",
}
"""Step 3's `ind_*` extremes vs the base state they shadow (disclosed in Step 3);
the report shows the joint firing rate so the reader can see how much of an
`ind_*` finding is already carried by a Step 2 condition."""


def _fmt(st: dict) -> str:
    if np.isnan(st["mean_bps"]):
        return "n/a"
    flag = "insuf" if st.get("insufficient") else ""
    return (
        f"{st['mean_bps']:+.1f} | {st['std_bps']:.0f} | {st['hit_rate'] * 100:.1f}% | "
        f"{st['p05_bps']:+.0f} / {st['p95_bps']:+.0f} | {st['t_date']:+.2f} | {st['n']:,} | {st['n_dates']:,}{(' ' + flag) if flag else ''}"
    )


def _shadow_overlap(panel: pd.DataFrame) -> list[tuple[str, str, float, int, int]]:
    """Joint firing rate between each `ind_*` condition and its base state."""
    rows: list[tuple[str, str, float, int, int]] = []
    for ind_col, base_col in SHADOW_PAIRS.items():
        if ind_col not in panel.columns or base_col not in panel.columns:
            rows.append((ind_col, base_col, float("nan"), 0, 0))
            continue
        a = panel[ind_col].to_numpy(dtype="float64")
        b = panel[base_col].to_numpy(dtype="float64")
        fa = np.isfinite(a) & (a > 0.5)
        fb = np.isfinite(b) & (b > 0.5)
        tot = int(fa.sum())
        rows.append((ind_col, base_col, (int((fa & fb).sum()) / tot) if tot else float("nan"), int((fa & fb).sum()), tot))
    return rows


def main() -> int:
    keep = set()
    keep |= {f"fwd_ret_{h}" for h in HORIZONS} | {f"fwd_atr_ret_{h}" for h in HORIZONS}
    keep |= {"atr_pct_20", "mom_12_1", "amihud_20", "close"}
    selected = load_selected_indicators()
    condition_cols = [s.name for s in CONDITION_SPECS] + indicator_condition_names(selected)
    panel = build_condition_panel(MARKET, keep_only=keep | set(condition_cols))
    condition_cols = [c for c in panel.columns if c in set(condition_cols)]

    uniq_dates = np.sort(panel["date"].unique())
    date_positions = np.searchsorted(uniq_dates, panel["date"].to_numpy())
    windows = sub_windows(uniq_dates, 2)

    lines = [
        "# WI-011 Step 4 — conditional expectancy and horizon sweep (CAD)",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Panel: {len(panel):,} rows · {panel['symbol'].nunique()} symbols · "
        f"{panel['date'].nunique()} dates ({str(uniq_dates.min())[:10]} → {str(uniq_dates.max())[:10]})",
        f"- Conditions evaluated: {len(condition_cols)} "
        f"({len([c for c in condition_cols if not c.startswith('ind_')])} declared + "
        f"{len([c for c in condition_cols if c.startswith('ind_')])} Step-3 indicator extremes)",
        "",
        f"HORIZONS: {','.join(str(h) for h in HORIZONS)}",
        "",
        f"SUBWINDOWS: 2 — {windows[0][0]}→{windows[0][1]} and {windows[1][0]}→{windows[1][1]} "
        "(disjoint contiguous halves of the evaluated date range)",
        "",
        f"PURGE_TD: max({MIN_PURGE_TD}, horizon) trading days between training and validation dates "
        "(WI-009 `PurgedWalkForwardSplit`, positions into the sorted unique date array) — per horizon: "
        + ", ".join(f"{h}d→{max(MIN_PURGE_TD, h)}td" for h in HORIZONS),
        "",
        "Additional boundary rule: inside a validation block only rows whose forward window ends inside "
        "the block are counted (`label_end_pos = val_pos_max − horizon`), so overlapping forward labels "
        "cannot straddle a fold boundary either. Forward labels use the forward path [t+1 .. t+h].",
        "",
        "Reading the tables: `mean/std` in bps of relative forward return; `hit%` share of firing rows "
        "with a positive forward return; `p05/p95` the 5% tails; `t_date` is the date-clustered t "
        "(per-date mean, then t across dates) — the statistic to read when a condition fires on many "
        "names on the same day; `n`/`dates` are firing observations and dated cross-sections.",
        f"A statistic is quoted as `insuf` (insufficient) when n < 30 or dated cross-sections < 3.",
        f"`STABLE_SIGN` requires both sub-windows evaluable, the same sign, and |t_date| > {T_FLOOR:.0f} in each.",
        "",
        "Unconditional reference (same rows, per horizon):",
        "",
        "| Horizon | mean bps (all rows) | date-clustered t | n |",
        "| ---: | ---: | ---: | ---: |",
    ]

    results: list[dict] = []
    baselines: dict[int, float] = {}
    fold_report: list[str] = []
    for h in HORIZONS:
        ret = panel[f"fwd_ret_{h}"].to_numpy(dtype="float64") * 1e4
        atr = panel[f"fwd_atr_ret_{h}"].to_numpy(dtype="float64")
        base = window_stats(ret, atr, panel["date"].to_numpy())
        baselines[h] = base["mean_bps"]
        u_dates, o_mean = date_overall_mean(ret, panel["date"].to_numpy())
        lines.append(
            f"| {h}d | {base['mean_bps']:+.1f} | {base['t_date']:+.2f} | {base['n']:,} |"
        )
        folds = fold_blocks(uniq_dates, h)
        fold_report.append(
            f"- **{h}d**: embargo {max(MIN_PURGE_TD, h)}td · {len(folds)} validation blocks "
            + ", ".join(f"fold {f['fold']} {f['val_min']}→{f['val_max']} (n_dates={f['val_n']})" for f in folds)
        )
        for c in condition_cols:
            results.append(
                evaluate_condition(
                    panel, c, h, date_positions, folds, windows, base["mean_bps"],
                    uniq_dates=u_dates, overall_mean=o_mean,
                )
            )

    lines += ["", "## Purged walk-forward blocks per horizon", ""] + fold_report

    stable = [r for r in results if r["stable_sign"]]
    unstable = [r for r in results if r["sign_disagreement"]]
    not_eval = [r for r in results if r["evaluable_subwindows"] < 2]
    insuf = [r for r in results if r["full"]["insufficient"]]

    lines += [
        "",
        "## Sign stability summary",
        "",
        f"STABLE_SIGN_COUNT: {len(stable)} (of {len(results)} condition × horizon cells)",
        f"UNSTABLE_SIGN_COUNT: {len(unstable)} (opposite signs in the two sub-windows)",
        f"NOT_EVALUABLE_COUNT: {len(not_eval)} (a sub-window had too few observations)",
        f"INSUFFICIENT_SAMPLE_COUNT: {len(insuf)} (full-sample statistic itself insufficient)",
        "",
        f"Stability is never claimed from a single window: {len(not_eval)} cells are reported as "
        "not-evaluable rather than stable or unstable.",
        "",
        "**Market-drift control (added within Step 4, not a re-selection).** Raw sign stability turns out "
        "to be nearly universal in this panel, because the equal-weight CAD universe drifts up over "
        "2016–2026: almost every condition fires on some positive-drift days and inherits the sign. The "
        "same stability clause is therefore also applied to the *within-date* component — each firing "
        "row's return minus its own date's all-name mean — which is the 'is this name rich or cheap versus "
        "its peers' question, with the day's market move removed.",
        "",
        f"STABLE_SIGN_WITHIN_COUNT: {sum(1 for r in results if r['stable_within_sign'])} "
        f"UNSTABLE_SIGN_WITHIN_COUNT: {sum(1 for r in results if r['within_sign_disagreement'])}",
        "",
        "Both verdicts are shown side by side below. Neither is a family-wise significance test "
        f"({len(results)} cells, no multiplicity correction), and neither accounts for costs.",
        "",
    ]
    if stable:
        lines += [
            "| Condition | Horizon | full mean bps | t_date | window 1 | window 2 |",
            "| :--- | ---: | ---: | ---: | ---: | ---: |",
        ]
        for r in sorted(stable, key=lambda r: (-abs(r["full"]["t_date"] or 0), r["condition"])):
            w = r["subwindows"]
            lines.append(
                f"| `{r['condition']}` | {r['horizon']}d | {r['full']['mean_bps']:+.1f} | "
                f"{r['full']['t_date']:+.2f} | {w[0]['mean_bps']:+.1f} ({w[0]['t_date']:+.2f}) | "
                f"{w[1]['mean_bps']:+.1f} ({w[1]['t_date']:+.2f}) |"
            )
    else:
        lines += ["No condition × horizon cell cleared the stable-sign clause.", ""]

    if unstable:
        lines += [
            "",
            "### UNSTABLE_SIGN cells (sign disagreement between sub-windows)",
            "",
            "| Condition | Horizon | window 1 mean bps (t) | window 2 mean bps (t) |",
            "| :--- | ---: | ---: | ---: |",
        ]
        for r in sorted(unstable, key=lambda r: r["condition"]):
            w = r["subwindows"]
            lines.append(
                f"| `{r['condition']}` | {r['horizon']}d | {w[0]['mean_bps']:+.1f} ({w[0]['t_date']:+.2f}) | "
                f"{w[1]['mean_bps']:+.1f} ({w[1]['t_date']:+.2f}) |"
            )

    # ---- per-horizon detail tables --------------------------------------- #
    for h in HORIZONS:
        rows = [r for r in results if r["horizon"] == h]
        rows = [r for r in rows if not r["full"]["insufficient"]]
        rows.sort(key=lambda r: -abs(r["full"]["t_date"] if np.isfinite(r["full"]["t_date"]) else 0.0))
        lines += [
            "",
            f"## Horizon {h}d — conditional expectancy ({len(rows)} conditions with sufficient samples)",
            "",
            "| Condition | mean bps | market bps | within bps | t_within | std | hit% | p05/p95 | t_date | n | dates | purged mean bps (n, dates) | excess bps | stability | stability (within) |",
            "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- | :--- |",
        ]
        for r in rows:
            f = r["full"]
            fw = r["full_within"]
            p = r["purged"]
            verdict = (
                "STABLE_SIGN"
                if r["stable_sign"]
                else ("UNSTABLE_SIGN" if r["sign_disagreement"] else ("not evaluable" if r["evaluable_subwindows"] < 2 else "single-window"))
            )
            wverdict = (
                "STABLE_SIGN_WITHIN"
                if r["stable_within_sign"]
                else ("UNSTABLE_SIGN_WITHIN" if r["within_sign_disagreement"] else "single-window")
            )
            lines.append(
                f"| `{r['condition']}` | {f['mean_bps']:+.1f} | {fw['market_bps']:+.1f} | {fw['within_bps']:+.1f} | "
                f"{fw['t_within']:+.2f} | {f['std_bps']:.0f} | {f['hit_rate'] * 100:.1f}% | "
                f"{f['p05_bps']:+.0f} / {f['p95_bps']:+.0f} | {f['t_date']:+.2f} | {f['n']:,} | {f['n_dates']:,} | "
                f"{p['mean_bps']:+.1f} ({p['n']:,}, {p['n_dates']:,}) | {r['excess_bps']:+.1f} | {verdict} | {wverdict} |"
            )
        dropped = [r for r in results if r["horizon"] == h and r["full"]["insufficient"]]
        if dropped:
            lines += [
                "",
                "Insufficient-sample cells at this horizon (reported, not quoted): "
                + ", ".join(f"`{r['condition']}` (n={r['full']['n']:,}, dates={r['full']['n_dates']:,})" for r in dropped),
            ]

    # ---- shadow overlap --------------------------------------------------- #
    lines += [
        "",
        "## Overlap with the base state each Step-3 indicator shadows",
        "",
        "Joint firing rate of `ind_*` conditions with the Step 2 state they restate "
        "(disclosed in Step 3; computed on real bars, point-in-time):",
        "",
        "| ind_* condition | base state | joint firing rate | joint rows | ind_* firing rows |",
        "| :--- | :--- | ---: | ---: | ---: |",
    ]
    for ind_col, base_col, rate, both_n, tot in _shadow_overlap(panel):
        lines.append(f"| `{ind_col}` | `{base_col}` | {rate * 100:.1f}% | {both_n:,} | {tot:,} |")

    lines += [
        "",
        "## Limits (read with the tables)",
        "",
        "- These are descriptive conditional distributions. No model is fitted, no threshold is tuned on "
        "the evaluated returns, and no multiplicity correction is applied across the "
        f"{len(results)} condition × horizon cells — the stable-sign clause is a *temporal* robustness "
        "check, not a family-wise significance test.",
        "- Conditional means are not tradeable expectancy: they say nothing about costs, position "
        "sizing, frequency or concurrency. Step 6 applies the cost/frequency/concurrency filter; Step 5 "
        "runs the per-symbol TS-momentum probe.",
        "- Rows where a condition is undefined (warm-up) are excluded per condition; the `n`/`dates` "
        "columns show exactly how much history each cell actually rests on.",
        "- The purged-fold column covers only dates after the initial training block (~60% of the timeline) and "
        "is smaller by construction (embargo plus the label-end rule), so its level is not directly "
        "comparable to the full-sample mean — read it as 'does the effect still show up in the later, "
        "out-of-block sample', not as the same rows re-measured.",
        "- **Market-beta caveat (read the `excess vs all-rows` column first).** A condition that fires "
        "disproportionately on strong market days inherits the market's drift: its raw mean bps is not a "
        "reason to trade it. The excess column subtracts the all-rows mean for the same horizon, and "
        "Step 5 decomposes each condition's forward return into a same-day market component and a "
        "within-date cross-sectional deviation, which is the cleaner 'which name' question.",
    ]

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")
    print(
        f"[wi011_condition_expectancy] wrote {REPORT}: cells={len(results)} stable={len(stable)} "
        f"unstable={len(unstable)} not_evaluable={len(not_eval)} insufficient={len(insuf)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())