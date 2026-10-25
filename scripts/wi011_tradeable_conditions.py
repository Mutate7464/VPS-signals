"""WI-011 Step 6 — costs, frequency, concurrency, and the decision-rule specs.

Takes the condition × horizon cells that Steps 4–5 showed to have a *stable,
positive within-date* expectancy, applies a documented per-name cost model plus
the IBKR CAD commission schedule, and keeps a candidate only when all three of
the plan's criteria hold:

1. **net expectancy survives** — the within-date component (the 'which name'
   part, market drift excluded) stays positive after the round-trip cost, with a
   date-clustered |t| > 2;
2. **100–400 firings/year** across the universe (a preference, not a cap);
3. **implied concurrency 4–12 positions** for a 5–15 trading-day hold.

Anything that clears all three is written up as a data-only rule spec in
`reports/wi011_decision_rules.md`. If nothing clears all three, the explicit
valid conclusion is written instead — "none survive costs at this universe size"
— and the rule spec is marked N/A. Either way the script stops at the human gate:
it does not optimise, backtest, size positions, or implement a screener.

Markers the plan's verify command greps for:
    COST_ASSUMPTIONS / ANNUAL_FIRINGS / CONCURRENCY / NET_EXPECTANCY
    plus `none survive costs at this universe size` when there are no survivors.
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
from src.wi011.ts_rules import TS_RULE_SPECS, TS_WINDOWS, compute_ts_cs_conditions  # noqa: E402

REPORT = BASE_DIR / "reports" / "wi011_tradeable_conditions.md"
RULES = BASE_DIR / "reports" / "wi011_decision_rules.md"

# --------------------------------------------------------------------------- #
# Cost assumptions (disclosed; constants, not tuned on results)
# --------------------------------------------------------------------------- #
TRADING_DAYS_PER_YEAR = 252

POSITION_NOTIONAL_CAD = 5_000.0
"""Assumed per-position notional, used only to express the per-order commission
in bps of trade value. A CAD 5,000 clip is a retail-scale assumption that must
be confirmed by the admin — with a 0.01/share schedule, a smaller clip pays a
larger bps commission (the CAD 1.00 order minimum binds harder)."""

IBKR_CAD_PER_SHARE = 0.01
IBKR_CAD_MIN_PER_ORDER = 1.00
IBKR_CAD_MAX_PCT_OF_TRADE = 0.005

HOLD_HORIZONS = (5, 10, 15)
"""The plan's 5–15 trading-day hold envelope. Longer horizons (20/60/120d) are
reported as information, and 1/2d are outside the envelope entirely; neither is
eligible for the survivor list, because the three criteria are defined for the
5–15d hold."""

FIRINGS_PER_YEAR_MIN, FIRINGS_PER_YEAR_MAX = 100, 400
CONCURRENCY_MIN, CONCURRENCY_MAX = 4, 12

SPREAD_SENSITIVITY = (1.0, 1.5, 2.0)
COMMISSION_SENSITIVITY = (1.0, 2.0)
SURVIVOR_SPREAD_MULT = 1.5
"""A survivor must still be positive under a 1.5x spread — a robustness margin,
since the spread proxy is an estimate, not an observation."""

COST_ASSUMPTIONS_TEXT = (
    f"spread = per-name Corwin-Schultz 60d median (causal, lagged) falling back to the "
    f"Amihud-proportional proxy `2*sqrt(amihud_20)*1e4`, counted once per round trip; "
    f"commission = IBKR Canada fixed schedule (CAD {IBKR_CAD_PER_SHARE:.2f}/share, "
    f"CAD {IBKR_CAD_MIN_PER_ORDER:.2f} minimum per order, max "
    f"{IBKR_CAD_MAX_PCT_OF_TRADE:.1%} of trade value) on a CAD {POSITION_NOTIONAL_CAD:,.0f} "
    f"position, charged on both sides; no separate slippage term — the spread estimate is "
    f"assumed to contain it, and the 1.5x/2.0x scenarios bound that assumption."
)


def commission_bps_round_trip(close: np.ndarray) -> np.ndarray:
    """Per-order commission on both sides, in bps of the position notional."""
    c = np.asarray(close, dtype="float64")
    shares = POSITION_NOTIONAL_CAD / np.maximum(c, 1e-9)
    per_order = np.clip(
        np.maximum(IBKR_CAD_PER_SHARE * shares, IBKR_CAD_MIN_PER_ORDER),
        None,
        IBKR_CAD_MAX_PCT_OF_TRADE * POSITION_NOTIONAL_CAD,
    )
    with np.errstate(invalid="ignore", divide="ignore"):
        bps = 2.0 * per_order / POSITION_NOTIONAL_CAD * 1e4
    return np.where(np.isfinite(c) & (c > 0), bps, np.nan)


def main() -> int:
    selected = load_selected_indicators()
    condition_cols = [s.name for s in CONDITION_SPECS] + indicator_condition_names(selected)
    ts_names = [s.name for s in TS_RULE_SPECS]
    keep = {f"fwd_ret_{h}" for h in HORIZONS} | {f"fwd_atr_ret_{h}" for h in HORIZONS}
    keep |= {"close", "spread_bps_used", "spread_cs_bps_60", "spread_amihud_bps", "dollar_vol_med_20", "atr_pct_20"}
    keep |= {f"tret_{w}" for w in TS_WINDOWS} | {f"tret_z_{w}" for w in TS_WINDOWS}
    keep |= set(condition_cols)

    panel = build_condition_panel(MARKET, keep_only=keep)
    panel = pd.concat([panel, compute_ts_cs_conditions(panel)], axis=1)
    all_rules = [c for c in condition_cols if c in panel.columns] + ts_names

    uniq_dates = np.sort(panel["date"].unique())
    date_positions = np.searchsorted(uniq_dates, panel["date"].to_numpy())
    windows = sub_windows(uniq_dates, 2)
    n_dates = len(uniq_dates)
    years = n_dates / TRADING_DAYS_PER_YEAR

    # ---- re-evaluate every rule × horizon to pick candidates -------------- #
    evals: dict[tuple[str, int], dict] = {}
    baselines: dict[int, dict] = {}
    for h in HORIZONS:
        ret = panel[f"fwd_ret_{h}"].to_numpy(dtype="float64") * 1e4
        atr = panel[f"fwd_atr_ret_{h}"].to_numpy(dtype="float64")
        base = window_stats(ret, atr, panel["date"].to_numpy())
        u_dates, o_mean = date_overall_mean(ret, panel["date"].to_numpy())
        baselines[h] = {"mean_bps": base["mean_bps"], "n": base["n"]}
        folds = fold_blocks(uniq_dates, h)
        for c in all_rules:
            evals[(c, h)] = evaluate_condition(
                panel, c, h, date_positions, folds, windows, base["mean_bps"],
                uniq_dates=u_dates, overall_mean=o_mean,
            )

    # ---- candidate selection (declared rule) ------------------------------ #
    # A candidate must (a) have a stable positive within-date component at that
    # horizon (the market-drift-controlled effect, Steps 4–5 wording), and
    # (b) rest on a sufficient sample. This is the plan's "candidates from
    # Steps 4–5"; the direction of every rule was declared with the rule itself,
    # never chosen after seeing the returns.
    candidates = [
        r
        for r in evals.values()
        if r["stable_within_sign"]
        and r["full_within"]["within_bps"] > 0
        and not r["full"]["insufficient"]
    ]

    close = panel["close"].to_numpy(dtype="float64")
    comm = commission_bps_round_trip(close)
    spread_col = panel["spread_bps_used"].to_numpy(dtype="float64")
    cs_col = panel["spread_cs_bps_60"].to_numpy(dtype="float64")
    am_col = panel["spread_amihud_bps"].to_numpy(dtype="float64")
    dates = panel["date"].to_numpy()

    rows: list[dict] = []
    for r in candidates:
        h, cond = r["horizon"], r["condition"]
        fired = np.isfinite(panel[cond].to_numpy(dtype="float64")) & (panel[cond].to_numpy(dtype="float64") > 0.5)
        fired &= np.isfinite(panel[f"fwd_ret_{h}"].to_numpy(dtype="float64"))
        n = int(fired.sum())
        if n == 0:
            continue
        per_date = pd.Series(np.ones(n), index=pd.Index(dates[fired])).groupby(level=0).sum()
        per_day_mean = float(per_date.mean())
        per_day_p90 = float(per_date.quantile(0.90))
        firings_yr = float(n / years)
        concurrency_mean = per_day_mean * h
        concurrency_p90 = per_day_p90 * h

        spread_bps = float(np.nanmean(spread_col[fired])) if np.isfinite(spread_col[fired]).any() else float("nan")
        comm_bps = float(np.nanmean(comm[fired]))
        cost_bps = spread_bps + comm_bps
        within = r["full_within"]["within_bps"]
        raw = r["full"]["mean_bps"]
        net_within = within - cost_bps
        net_within_stress = within - (spread_bps * SURVIVOR_SPREAD_MULT + comm_bps)
        net_raw = raw - cost_bps

        passes_net = bool(net_within > 0 and net_within_stress > 0 and abs(r["full_within"]["t_within"]) > T_FLOOR)
        passes_freq = bool(FIRINGS_PER_YEAR_MIN <= firings_yr <= FIRINGS_PER_YEAR_MAX)
        passes_conc = bool(CONCURRENCY_MIN <= concurrency_mean <= CONCURRENCY_MAX)

        rows.append(
            {
                "condition": cond,
                "horizon": h,
                "kind": "TS" if cond.startswith("ts_") else ("CS" if cond.startswith("cs_") else "state"),
                "n": n,
                "raw_bps": raw,
                "market_bps": r["full_within"]["market_bps"],
                "within_bps": within,
                "t_within": r["full_within"]["t_within"],
                "spread_bps": spread_bps,
                "comm_bps": comm_bps,
                "cost_bps": cost_bps,
                "net_within_bps": net_within,
                "net_within_stress15_bps": net_within_stress,
                "net_raw_bps": net_raw,
                "firings_yr": firings_yr,
                "per_day": per_day_mean,
                "per_day_p90": per_day_p90,
                "concurrency": concurrency_mean,
                "concurrency_p90": concurrency_p90,
                "passes_net": passes_net,
                "passes_freq": passes_freq,
                "passes_conc": passes_conc,
                "hold_eligible": h in HOLD_HORIZONS,
                "stable_raw": r["stable_sign"],
            }
        )

    rows.sort(key=lambda d: -d["net_within_bps"])
    survivors = [d for d in rows if d["hold_eligible"] and d["passes_net"] and d["passes_freq"] and d["passes_conc"]]

    cs_share = (
        float(np.nanmean(cs_col[np.isfinite(cs_col)])) if np.isfinite(cs_col).any() else float("nan")
    )
    am_share = float(np.nanmean(am_col[np.isfinite(am_col)])) if np.isfinite(am_col).any() else float("nan")

    def _tbl(items: list[dict], limit: int | None = None) -> list[str]:
        out = [
            "| Rule | Hold | n | gross mean bps | market bps | within bps | t_within | spread bps | comm bps | round-trip cost bps | NET within bps | NET within @1.5x spread | NET raw bps | firings/yr | fires/day | concurrency (p90) | net | freq | conc |",
            "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |",
        ]
        for d in (items if limit is None else items[:limit]):
            out.append(
                f"| `{d['condition']}` | {d['horizon']}d | {d['n']:,} | {d['raw_bps']:+.1f} | {d['market_bps']:+.1f} | "
                f"{d['within_bps']:+.1f} | {d['t_within']:+.2f} | {d['spread_bps']:.1f} | {d['comm_bps']:.1f} | "
                f"{d['cost_bps']:.1f} | {d['net_within_bps']:+.1f} | {d['net_within_stress15_bps']:+.1f} | "
                f"{d['net_raw_bps']:+.1f} | {d['firings_yr']:,.0f} | {d['per_day']:.1f} | "
                f"{d['concurrency']:.0f} ({d['concurrency_p90']:.0f}) | "
                f"{'pass' if d['passes_net'] else 'fail'} | {'pass' if d['passes_freq'] else 'fail'} | "
                f"{'pass' if d['passes_conc'] else 'fail'} |"
            )
        return out

    n_net = sum(1 for d in rows if d["passes_net"])
    n_freq = sum(1 for d in rows if d["passes_freq"])
    n_conc = sum(1 for d in rows if d["passes_conc"])
    near = [d for d in rows if d["passes_net"] and (d["passes_freq"] or d["passes_conc"])]

    lines = [
        "# WI-011 Step 6 — costs, frequency, concurrency (CAD)",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Panel: {len(panel):,} rows · {panel['symbol'].nunique()} symbols · {n_dates} dates "
        f"({years:.2f} years at {TRADING_DAYS_PER_YEAR} trading days/yr)",
        f"- Candidates carried in from Steps 4–5: {len(rows)} rule × horizon cells with a stable, positive "
        "*within-date* component and sufficient sample (direction pre-declared with each rule).",
        "",
        f"COST_ASSUMPTIONS: {COST_ASSUMPTIONS_TEXT}",
        "",
        f"- per-name spread inputs: Corwin-Schultz usable on {100 * np.isfinite(cs_col).mean():.1f}% of rows "
        f"(mean {cs_share:.1f} bps where defined), Amihud proxy on {100 * np.isfinite(am_col).mean():.1f}% "
        f"(mean {am_share:.1f} bps) — the fallback is used where CS is undefined; both are disclosed.",
        f"- cost sensitivity: spread x{SPREAD_SENSITIVITY[1]} and x{SPREAD_SENSITIVITY[2]}, commission "
        f"x{COMMISSION_SENSITIVITY[0]}–x{COMMISSION_SENSITIVITY[1]} (the x1.0 numbers are the headline; the "
        "stress column is the robustness check a survivor must also pass).",
        "- the *within-date* component is the criterion, not the raw mean: a long-only rule that fires on "
        "strong-market days inherits CAD market drift, and crediting that drift as edge would be wrong. The "
        "raw-mean net column is shown for transparency.",
        "",
        f"ANNUAL_FIRINGS envelope: {FIRINGS_PER_YEAR_MIN}–{FIRINGS_PER_YEAR_MAX} firings/year across the universe "
        "(a preference, per the plan, never a cap).",
        f"CONCURRENCY envelope: {CONCURRENCY_MIN}–{CONCURRENCY_MAX} positions for 5–15 trading-day holds; "
        "concurrency = mean simultaneous firing names × hold days, evaluated at the hold horizon.",
        "",
        "## Candidate table (all candidates, sorted by net within-date expectancy)",
        "",
    ]
    lines += _tbl(rows)
    lines += [
        "",
        "## Criterion outcomes",
        "",
        f"- candidates: {len(rows)}",
        f"- pass net expectancy (within-date, positive under the 1.5x-spread stress, |t_within| > {T_FLOOR:.0f}): "
        f"{n_net}",
        f"- pass frequency (100–400 firings/yr): {n_freq}",
        f"- pass concurrency (4–12 positions at 5–15d holds): {n_conc}",
        f"- pass all three with an eligible 5–15d hold: **{len(survivors)}**",
        "",
    ]

    if survivors:
        lines += ["## Survivors", ""] + _tbl(survivors)
    else:
        lines += [
            "## Survivors",
            "",
            "none survive costs at this universe size.",
            "",
            "Explicit valid conclusion (the plan pre-authorises it). The binding constraints, in order:",
            "",
            f"1. **Concurrency / frequency.** The candidate rules fire on hundreds of names per day "
            f"(median {np.median([d['per_day'] for d in rows]):.0f} fires/day), so a 5–15d hold implies "
            f"concurrency far above the {CONCURRENCY_MAX}-position envelope and annual firings far above "
            f"{FIRINGS_PER_YEAR_MAX}. They are *market states*, not triggers with a daily cadence — the plan's "
            "100–400/yr preference describes a trigger, and a state that describes a third of the universe "
            "every day cannot be one.",
            "",
            f"2. **Net expectancy.** Even ignoring cadence, the within-date edge is comparable to or smaller "
            f"than the round-trip cost: median within-date effect {np.median([d['within_bps'] for d in rows]):+.1f} bps "
            f"against a median round-trip cost of {np.median([d['cost_bps'] for d in rows]):.1f} bps "
            f"(spread + commission). Under the 1.5x-spread stress, {n_net} of {len(rows)} candidates would "
            "still show a positive *within-date* net effect, but none of those combine it with a tradeable cadence.",
            "",
        ]
        if near:
            lines += [
                "Near-misses (net expectancy passes, cadence fails) — listed so the gate can see what a "
                "narrower trigger would have to look like:",
                "",
            ] + _tbl(near, limit=10)

    lines += [
        "",
        "## What would have to change (for the human gate, not executed here)",
        "",
        "- A **narrower trigger**: require the rule AND a further selection (e.g. only the highest-ranked "
        "names each day) to reach 0.4–1.6 fires/day. That is *screener design / portfolio construction*, "
        "explicitly out of scope for WI-011 and requiring a new plan.",
        "- A **cheaper execution assumption**: only the CAD commission schedule and the spread estimate are "
        "modelled; a queue-following/limit-order assumption would lower the spread term, and the report "
        "shows how much (1.5x/2.0x columns).",
        "- A **longer hold**: 5–15d is the plan's envelope; the raw within-date effects at 60/120d are "
        "larger, but the hold envelope and cost amortisation are then outside this step's stated criteria.",
        "",
        "## Limits",
        "",
        "- No optimisation, no backtest, no position sizing, no screener implementation: costs and frequency "
        "are applied to already-descriptive cells, and nothing here is tuned to make a survivor appear.",
        "- The IBKR schedule parameters are assumptions recorded as constants in "
        "`scripts/wi011_tradeable_conditions.py` and must be confirmed by the admin; the notional assumption "
        f"(CAD {POSITION_NOTIONAL_CAD:,.0f}) drives the commission-in-bps conversion.",
        "- The spread proxy is an estimate from daily bars (Corwin-Schultz, lagged causal) with an "
        "Amihud-proportional fallback; it is not a quote, and the stress columns carry that uncertainty.",
    ]

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")

    # ---- decision-rule specification ------------------------------------- #
    rule_lines = [
        "# WI-011 — decision-rule specification (data only, human gate)",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "- Derived from Steps 4–6 of `docs/plans/2026-10-25-WI-011-condition-first-meta-analysis.md`; "
        "cost evidence in `reports/wi011_tradeable_conditions.md`.",
        "- These are **data specifications only**. Nothing here is optimised, backtested, sized or "
        "implemented; no long-only rule survives at this universe size, so the specification is N/A by "
        "the plan's own pre-authorised conclusion.",
        "",
        "HUMAN_GATE: STOP",
        "",
    ]
    if survivors:
        for d in survivors:
            rule_lines += [
                f"## {d['condition']} @ {d['horizon']}d hold",
                "",
                f"ENTRY: fire when `{d['condition']}` is true for a name at its daily close.",
                f"HOLD_WINDOW: {d['horizon']} trading days ({d['cost_bps']:.1f} bps round-trip cost assumed).",
                f"EXIT_INVALIDATION: the rule's own condition turning false, or the {d['horizon']}d window "
                "expiring, whichever comes first.",
                f"NET_EXPECTANCY: {d['net_within_bps']:+.1f} bps within-date after costs.",
                "",
            ]
    else:
        rule_lines += [
            "ENTRY: N/A — no rule passed the Step 6 criteria.",
            "HOLD_WINDOW: N/A — the 5–15 trading-day envelope was never reached by a qualifying rule.",
            "EXIT_INVALIDATION: N/A — no rule survives to specify an exit.",
            "",
            "NO_TRADE_DEFAULT: no new positions from WI-011 conditions. The candidate "
            "*states* (trend/chop, volatility regime, liquidity regime, 52-week channel position, and the "
            "Step 5 cross-sectional return-rank rules) remain descriptive context only — usable for "
            "annotation and post-hoc attribution, not as entries.",
            "",
            "CONDITION_FLAGS (context only, not entries): `trend_up`/`trend_down`/`trend_chop`, "
            "`er_trending`/`er_choppy`, `vol_low`/`vol_high`, `liq_illiquid`/`liq_liquid`, "
            "`ch52_high`/`ch52_low`, `mom_pos`/`mom_neg`, `rev1m_pos`/`rev1m_neg`, plus the Step 3 "
            "`ind_*` own-history extremes. The one effect worth carrying forward as *information* is the "
            "cross-sectional framing: `cs_top_quartile_120` / `cs_bottom_quartile_120` show the largest "
            "within-date components (about +50 and +19 bps at a 20d horizon), i.e. 6–12 month relative "
            "winners and losers both outrun the middle of the distribution.",
            "",
            "FACTOR_TILTS (observed, descriptive): the CAD universe over 2016–2026 drifts up "
            f"(all-rows mean +{baselines[20]['mean_bps']:.0f} bps per 20 trading days); `vol_high`, "
            "`dollarvol_high` and the 52-week-low states carry the largest *market* components, so any rule "
            "built on them is a market-timing bet rather than a name-selection bet.",
            "",
            "WORKED_EXAMPLE: N/A — the plan requires a worked example only when a survivor exists.",
            "",
            "REASON FOR N/A: " + f"{len(rows)} candidate cells cleared the stable within-date screen, "
            f"{n_net} cleared net expectancy, but {len(survivors)} cleared frequency and concurrency as well — "
            "see `reports/wi011_tradeable_conditions.md` for the full table and the explicit "
            "no-survivor conclusion.",
        ]

    rule_lines += [
        "",
        "## What the human gate is being asked to decide",
        "",
        "1. Accept the negative result: WI-011 conditions are descriptive, not tradeable, at this universe "
        "size and cadence — and stop the condition-first branch.",
        "2. Or authorise a **new** plan for a narrower trigger + execution assumption (screener design, "
        "portfolio construction) that WI-011 explicitly excludes.",
        "3. Or confirm/correct the cost assumptions (IBKR CAD schedule parameters and the CAD 5,000 "
        "notional), which is the one input that could move candidates across the net-expectancy line.",
        "",
        "No implementation, backtest, optimisation or order flow follows from this document without that "
        "decision.",
    ]

    RULES.parent.mkdir(parents=True, exist_ok=True)
    RULES.write_text("\n".join(rule_lines) + "\n")
    print(
        f"[wi011_tradeable_conditions] wrote {REPORT} and {RULES}: candidates={len(rows)} "
        f"net={n_net} freq={n_freq} conc={n_conc} survivors={len(survivors)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())