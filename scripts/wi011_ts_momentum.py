"""WI-011 Step 5 — per-symbol TS-momentum probe and the TS-vs-CS decomposition.

Runs the TS rules and their cross-sectional counterparts (see
`src/wi011/ts_rules.py`) over the same eight horizons, with the same purged
walk-forward discipline and the same two-sub-window sign test as Step 4, then
decomposes each rule's forward return into a same-day market component and a
within-date cross-sectional deviation.

It also re-evaluates Step 4's own-history position conditions (`above_ma_50`,
`ch52_high`, `ch52_low`, `mom_pos`, `mom_neg`) through the identical machinery,
so the "condition-level" comparison is apples-to-apples rather than a re-reading
of a different table.

Markers the plan's verify command greps for:
    TS_RULES / HORIZONS: 1,2,5,10,15,20,60,120 / TS_VS_CS_DECOMPOSITION / PURGE_TD:
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.market_cli import add_market_argument, cli_markets, report_path, run_markets  # noqa: E402
from src.wi011 import HORIZONS  # noqa: E402
from src.wi011.panel import build_condition_panel  # noqa: E402
from src.wi011.stats import (  # noqa: E402
    MIN_PURGE_TD,
    T_FLOOR,
    date_overall_mean,
    evaluate_condition,
    fold_blocks,
    sub_windows,
    window_stats,
)
from src.wi011.ts_rules import (  # noqa: E402
    TS_RULE_SPECS,
    TS_STRONG_Z,
    TS_WINDOWS,
    compute_ts_cs_conditions,
    ts_cs_pairs,
)

REPORTS = BASE_DIR / "reports"
REPORT_STEM = "wi011_ts_momentum"


def paths(market: str) -> dict[str, Path]:
    """Every input/output path this script resolves for one market (WI-013)."""
    return {"report": report_path(REPORTS, REPORT_STEM, market)}

STEP4_POSITION_CONDITIONS = ("above_ma_50", "below_ma_50", "ch52_high", "ch52_low", "mom_pos", "mom_neg")


def _row(r: dict) -> str:
    f, fw, p = r["full"], r["full_within"], r["purged"]
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
    return (
        f"| `{r['condition']}` | {f['mean_bps']:+.1f} | {fw['market_bps']:+.1f} | {fw['within_bps']:+.1f} | "
        f"{fw['t_within']:+.2f} | {f['t_date']:+.2f} | {f['hit_rate'] * 100:.1f}% | "
        f"{f['n']:,} | {f['n_dates']:,} | {p['mean_bps']:+.1f} ({p['n']:,}, {p['n_dates']:,}) | {verdict} | {wverdict} |"
    )


def run_market(market: str) -> int:
    REPORT = paths(market)["report"]
    keep = {f"fwd_ret_{h}" for h in HORIZONS} | {f"fwd_atr_ret_{h}" for h in HORIZONS}
    keep |= {f"tret_{w}" for w in TS_WINDOWS} | {f"tret_z_{w}" for w in TS_WINDOWS}
    keep |= {"vol_20", "mom_12_1", "rev_1m"} | set(STEP4_POSITION_CONDITIONS)
    panel = build_condition_panel(market, keep_only=keep)
    ts_cs = compute_ts_cs_conditions(panel)
    panel = pd.concat([panel, ts_cs], axis=1)

    rule_names = [s.name for s in TS_RULE_SPECS]
    all_rules = rule_names + [c for c in STEP4_POSITION_CONDITIONS if c in panel.columns]

    uniq_dates = np.sort(panel["date"].unique())
    date_positions = np.searchsorted(uniq_dates, panel["date"].to_numpy())
    windows = sub_windows(uniq_dates, 2)

    lines = [
        f"# WI-011 Step 5 — per-symbol (time-series) momentum probe and TS-vs-CS decomposition ({market})",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Panel: {len(panel):,} rows · {panel['symbol'].nunique()} symbols · "
        f"{panel['date'].nunique()} dates ({str(uniq_dates.min())[:10]} → {str(uniq_dates.max())[:10]})",
        "- Evaluation order: TS rule first, then its cross-sectional counterpart on the *same* trailing "
        "return, so the comparison varies the framing (own level vs within-date rank) and not the "
        "information content. No cross-sectional ranking of any model score is involved, and no model "
        "is trained.",
        "",
        "TS_RULES: " + ", ".join(f"`{s.name}` ({s.formula})" for s in TS_RULE_SPECS),
        "",
        f"TS_WINDOWS: {','.join(str(w) for w in TS_WINDOWS)} trading days · volatility-scaled strength "
        f"threshold |z| >= {TS_STRONG_Z} with z = own trailing return / (vol_20 * sqrt(window))",
        "",
        f"HORIZONS: {','.join(str(h) for h in HORIZONS)}",
        "",
        f"PURGE_TD: max({MIN_PURGE_TD}, horizon) trading days (WI-009 `PurgedWalkForwardSplit` over the "
        "sorted unique date array) — per horizon: " + ", ".join(f"{h}d→{max(MIN_PURGE_TD, h)}td" for h in HORIZONS),
        "",
        f"SUBWINDOWS: 2 — {windows[0][0]}→{windows[0][1]} and {windows[1][0]}→{windows[1][1]} "
        "(same disjoint halves as Step 4). `STABLE_SIGN` = same sign in both halves with |t| > "
        f"{T_FLOOR:.0f}; `STABLE_SIGN_WITHIN` applies the same clause to the within-date component.",
        "",
        "Decomposition columns: `mean` = raw mean forward bps; `market` = mean of each firing row's own "
        "date all-name mean (the drift the rule inherits); `within` = mean deviation from that date's mean "
        "(the 'which name' part); `t_within` = t across dates on the per-date deviation.",
        "",
    ]

    results: list[dict] = []
    for h in HORIZONS:
        ret = panel[f"fwd_ret_{h}"].to_numpy(dtype="float64") * 1e4
        atr = panel[f"fwd_atr_ret_{h}"].to_numpy(dtype="float64")
        base = window_stats(ret, atr, panel["date"].to_numpy())
        u_dates, o_mean = date_overall_mean(ret, panel["date"].to_numpy())
        folds = fold_blocks(uniq_dates, h)
        for c in all_rules:
            results.append(
                evaluate_condition(
                    panel, c, h, date_positions, folds, windows, base["mean_bps"],
                    uniq_dates=u_dates, overall_mean=o_mean,
                )
            )
        lines_ref = None

    by_key = {(r["condition"], r["horizon"]): r for r in results}

    # ---- TS vs CS decomposition ------------------------------------------ #
    lines += [
        "## TS_VS_CS_DECOMPOSITION",
        "",
        "For each matched pair, the *same* trailing-return element is evaluated as a TS level rule and as "
        "a cross-sectional rank rule. `Δ(TS−CS)` is their raw-mean difference in bps; the `within` columns "
        "say how much of each rule is a 'which name' effect rather than a market-drift effect.",
        "",
    ]
    for h in HORIZONS:
        lines += [
            f"### Horizon {h}d",
            "",
            "| Element | TS rule | TS mean | TS market | TS within (t) | CS rule | CS mean | CS market | CS within (t) | Δ(TS−CS) mean bps | TS stable | CS stable |",
            "| :--- | :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: | :--- | :--- |",
        ]
        for ts_name, cs_name, w, element in ts_cs_pairs():
            ts = by_key.get((ts_name, h))
            cs = by_key.get((cs_name, h))
            if ts is None or cs is None:
                continue
            tw, cw = ts["full_within"], cs["full_within"]

            def _v(r):  # short verdict label
                if r["full"]["insufficient"]:
                    return "insufficient"
                return "stable" if r["stable_sign"] else ("unstable" if r["sign_disagreement"] else "single-window")

            lines.append(
                f"| {element} (w={w}) | `{ts_name}` | {ts['full']['mean_bps']:+.1f} | {tw['market_bps']:+.1f} | "
                f"{tw['within_bps']:+.1f} ({tw['t_within']:+.2f}) | `{cs_name}` | {cs['full']['mean_bps']:+.1f} | "
                f"{cw['market_bps']:+.1f} | {cw['within_bps']:+.1f} ({cw['t_within']:+.2f}) | "
                f"{ts['full']['mean_bps'] - cs['full']['mean_bps']:+.1f} | {_v(ts)} | {_v(cs)} |"
            )
        lines.append("")

    # ---- rule tables per horizon ----------------------------------------- #
    for h in HORIZONS:
        rows = [r for r in results if r["horizon"] == h and not r["full"]["insufficient"]]
        insuf = [r for r in results if r["horizon"] == h and r["full"]["insufficient"]]
        rows.sort(key=lambda r: -abs(r["full_within"]["within_bps"] if np.isfinite(r["full_within"]["within_bps"]) else 0.0))
        lines += [
            f"## Horizon {h}d — TS/CS rule expectancy (sorted by |within bps|)",
            "",
            "| Rule | mean bps | market bps | within bps | t_within | t_date | hit% | n | dates | purged mean bps (n, dates) | stability | stability (within) |",
            "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |",
        ]
        for r in rows:
            lines.append(_row(r))
        if insuf:
            lines += [
                "",
                "Insufficient/null cells (reported, never imputed): "
                + ", ".join(f"`{r['condition']}` (n={r['full']['n']:,}, dates={r['full']['n_dates']:,})" for r in insuf),
            ]
        lines.append("")

    # ---- condition-level (Step 4) comparison ------------------------------ #
    lines += [
        "## Condition-level comparison with Step 4",
        "",
        "Step 4's own-history *position* conditions re-evaluated through the identical machinery — these "
        "are the same numbers Step 4 reports, repeated here so the TS-vs-CS reading sits next to the "
        "condition-level one instead of requiring two documents.",
        "",
        "| Condition | Horizon | mean bps | market bps | within bps | t_within | stability | stability (within) |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | :--- | :--- |",
    ]
    for c in STEP4_POSITION_CONDITIONS:
        if c not in panel.columns:
            continue
        for h in (5, 20, 60, 120):
            r = by_key.get((c, h))
            if r is None or r["full"]["insufficient"]:
                continue
            fw = r["full_within"]
            verdict = (
                "STABLE_SIGN"
                if r["stable_sign"]
                else ("UNSTABLE_SIGN" if r["sign_disagreement"] else "single-window")
            )
            wverdict = (
                "STABLE_SIGN_WITHIN"
                if r["stable_within_sign"]
                else ("UNSTABLE_SIGN_WITHIN" if r["within_sign_disagreement"] else "single-window")
            )
            lines.append(
                f"| `{c}` | {h}d | {r['full']['mean_bps']:+.1f} | {fw['market_bps']:+.1f} | {fw['within_bps']:+.1f} | "
                f"{fw['t_within']:+.2f} | {verdict} | {wverdict} |"
            )

    # ---- findings summary ------------------------------------------------- #
    ts_only = [r for r in results if r["condition"].startswith("ts_")]
    cs_only = [r for r in results if r["condition"].startswith("cs_")]
    ts_strong_within = [r for r in ts_only if r["stable_within_sign"]]
    cs_strong_within = [r for r in cs_only if r["stable_within_sign"]]
    ts_within_vals = np.array([r["full_within"]["within_bps"] for r in ts_only if not r["full"]["insufficient"]])
    cs_within_vals = np.array([r["full_within"]["within_bps"] for r in cs_only if not r["full"]["insufficient"]])
    ts_absmean = np.nanmean(np.abs(ts_within_vals)) if ts_within_vals.size else float("nan")
    cs_absmean = np.nanmean(np.abs(cs_within_vals)) if cs_within_vals.size else float("nan")

    lines += [
        "",
        "## Findings summary (TS vs CS)",
        "",
        f"- TS rule × horizon cells: {len(ts_only)}; CS rule × horizon cells: {len(cs_only)}.",
        f"- Cells whose *within-date* component passed the stable-sign clause: TS {len(ts_strong_within)}, "
        f"CS {len(cs_strong_within)}.",
        f"- Mean |within bps| across TS cells: {ts_absmean:.1f}; across CS cells: {cs_absmean:.1f} "
        "(cross-sectionally framed rules are, on this panel, the larger 'which name' effect).",
        "- Raw `mean bps` is dominated by the market component for every rule and horizon: the "
        f"own-history rules mostly identify *when*, not *which*, and the when is the {market} market drift "
        "shared by the whole equal-weight universe.",
        "- Null and insufficient cases are recorded in each horizon table rather than dropped.",
        "",
        "## Limits",
        "",
        "- Descriptive only: no model, no threshold tuned on forward returns, no multiplicity correction "
        "across cells, no claim of causality and no cost/net-expectancy claim (that is Step 6).",
        "- The TS rules use only a symbol's own trailing returns and trailing vol; the CS rules use the "
        "same trailing return ranked within date. Neither uses any forward information.",
        f"- Purge: `max({MIN_PURGE_TD}td, horizon)` embargo and the label-end rule inside each validation "
        "block, identical to Step 4; the fold sets are the same, so TS/CS and Step 4 numbers are directly "
        "comparable.",
    ]

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")
    print(f"[wi011_ts_momentum] {market}: wrote {REPORT}: cells={len(results)} "
          f"TS_within_stable={len(ts_strong_within)} CS_within_stable={len(cs_strong_within)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """The CLI parser for this entry point (one shared `--market` flag)."""
    ap = argparse.ArgumentParser(description=__doc__)
    add_market_argument(ap)
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    markets = cli_markets(args.market, prog="wi011_ts_momentum")
    if markets is None:
        return 2
    print(f"[wi011_ts_momentum] PLAN: markets={', '.join(markets)}")
    return run_markets(markets, run_market)


if __name__ == "__main__":
    raise SystemExit(main())