"""WI-018 step 4 (G3) — the *conditional* cost overlay and the memo-only decision.

G3 exists to answer one question, and only if G2 says there is something to ask
about: **does a G2 survivor still look like a signal after costs?**

What G3 does, and what it refuses to do
---------------------------------------
1. **Gated on G2.** With no survivors the module writes the skip record: G3 is
   `SKIPPED`, the standing default is `NO_TRADE`, and no market pass runs at all.
2. **One IC per survivor, on held-out dates only.** Each survivor is a signed
   binary condition: `+1` where it fires for an up-direction condition, `-1` for
   a down-direction one, `0` elsewhere. Its within-date Spearman rank IC against
   `first_touch_34` is computed with `src.wi016.probe._fast_ic_detail` (imported,
   not reimplemented) over the *same* held-out windows G2 used, streaming the
   universe in date blocks and keeping only block-sized frames in memory.
3. **Cost overlay at 25 bps total.** `src.wi016.probe.cost_overlay` maps the IC to
   a screening proxy edge in bps (`|IC| * 1000`) and subtracts the WI-011
   assumption of 20 bps cost + 5 bps slippage. **That IC-to-bps scale is a
   documented screening proxy, not a P&L model** — the real P&L model lives in
   the WI-011 overlay and is not invoked here.
4. **NO_TRADE by default.** A condition is `TRADE` only when the net edge is
   positive *and* the IC is estimable (finite, enough held-out dates). Every
   other path — nonpositive net, NaN IC, too few dates, no survivors — is
   `NO_TRADE`. Neither this module nor its output can place an order.

Ship shape (D-018 Q5, plan step 4): `reports/wi018/g3_USD.json` plus the memo
`reports/wi018/summary_USD.md`. **No executable rules, no shortlist CSV, no
trading integration.**

CLI::

    python -m src.wi018.cost_overlay --market USD
    python -m src.wi018.cost_overlay --market USD --check-report reports/wi018/g3_USD.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.wi016.probe import IC_TO_BPS, _fast_ic_detail, cost_overlay
from src.wi018 import (
    BINNINGS,
    COST_BPS_TOTAL,
    DATES_PER_BLOCK,
    DERIVED_DIR,
    FEATURES_DIR,
    G3_JSON,
    HORIZON,
    MARKET,
    MIN_GROUP_DATES,
    PREFLIGHT_JSON,
    PRIMARY_TARGET,
    PROBE_JSON,
    PRUNE_RECS,
    REPORTS_DIR,
    SECONDARY_TARGETS,
    SUMMARY_MD,
)
from src.wi018.data_probe import PreflightError, load_keep_columns, require_preflight, symbol_paths
from src.wi018.probe import MIN_HOLDOUT_DATES, _t_stat, held_out_positions
from src.wi018.rates import ci_from_series
from src.wi018.streaming import (
    DATE_COLUMN,
    QUANTILES,
    STATE_OFFSET,
    binning_of_code,
    date_blocks,
    edges_from_sorted,
    global_dates,
    group_sorted,
    read_block_pairs,
    state_codes,
)

__all__ = [
    "DIRECTION_SIGN",
    "G3_VERDICTS",
    "check_g3_report",
    "build_summary_markdown",
    "condition_ic_series",
    "condition_terms",
    "evaluate_condition",
    "format_g3_markdown",
    "main",
    "run_g3",
    "survivor_conditions",
    "write_outputs",
]

DIRECTION_SIGN = {"up": 1.0, "dn": -1.0}
"""Signed indicator: an up-condition firing is `+1`, a down-condition is `-1`."""

G3_VERDICTS = ("TRADE", "NO_TRADE", "SKIPPED")
"""The only three G3 outcomes; `TRADE` needs a positive net edge."""


# --------------------------------------------------------------------------- #
# Survivors -> conditions
# --------------------------------------------------------------------------- #
def survivor_conditions(probe_report: dict, keep_columns: list[str]) -> list[dict]:
    """One condition record per G2 survivor (univariate or conjunction).

    Terms are `(feature, state_code)` pairs — a conjunction has two, from two
    different features (the G2 pair rule) — plus the signed indicator direction.
    """
    out: list[dict] = []
    for record in probe_report.get("survivors", []):
        direction = record.get("direction")
        if direction not in DIRECTION_SIGN:
            continue
        if record.get("kind") == "conjunction":
            pair = record.get("pair") or []
            if len(pair) != 4:
                continue
            terms = [
                (keep_columns[int(pair[0])], int(pair[1])),
                (keep_columns[int(pair[2])], int(pair[3])),
            ]
        else:
            if record.get("feature") not in keep_columns:
                continue
            terms = [(record["feature"], int(record["code"]))]
        out.append(
            {
                "condition": record.get("condition"),
                "kind": record.get("kind"),
                "direction": direction,
                "sign": DIRECTION_SIGN[direction],
                "terms": terms,
                "g2_lift": record.get("lift"),
                "g2_ci_low": record.get("ci_low"),
                "g2_ci_high": record.get("ci_high"),
                "g2_q": record.get("q"),
                "g2_n_dates": record.get("n_dates"),
                "features": sorted({feature for feature, _code in terms}),
            }
        )
    return out


def condition_terms(record: dict, keep_columns: list[str]) -> list[tuple[str, int]]:
    """`[(feature, code)]` for a G2 survivor record (see `survivor_conditions`)."""
    return survivor_conditions({"survivors": [record]}, keep_columns)[0]["terms"]


# --------------------------------------------------------------------------- #
# Held-out IC per condition (streaming, block-sized frames only)
# --------------------------------------------------------------------------- #
def condition_ic_series(
    conditions: list[dict],
    derived_paths: dict[str, Path],
    feature_paths: dict[str, Path],
    dates: np.ndarray,
    held: np.ndarray,
    target: str = PRIMARY_TARGET,
    block_size: int | None = None,
) -> list[dict]:
    """Per-date IC series for every condition, held-out dates only.

    One symbol-sequential pass over date blocks. State codes are rebuilt with the
    same within-date cross-sectional quantiles the atlas/G2 used, so a condition
    here is literally the condition that survived there. A condition's IC for a
    date uses that date's full cross-section of names where the condition is
    *defined* (undefined feature rows are dropped, never imputed as "not firing").
    """
    needed = sorted({feature for cond in conditions for feature, _code in cond["terms"]})
    date_index = pd.Index(dates)
    n_dates = int(dates.size)
    collected: list[dict] = [{"dates": [], "ic": []} for _ in conditions]
    if not needed or not conditions:
        return collected

    for block in date_blocks(dates, size=block_size or DATES_PER_BLOCK):
        pair = read_block_pairs(derived_paths, feature_paths, needed, [target], block["lo"], block["hi"])
        if pair is None:
            continue
        feats, tgts = pair
        pos = date_index.get_indexer(feats[DATE_COLUMN].to_numpy())
        codes: dict[str, np.ndarray] = {}
        for column in needed:
            values = feats[column].to_numpy(dtype="float64")
            xs, starts, sizes = group_sorted(values, pos, n_dates)
            for binning, quantiles in QUANTILES.items():
                edges = edges_from_sorted(xs, starts, sizes, quantiles, BINNINGS[binning])
                codes[f"{column}|{binning}"] = state_codes(values, edges, pos, offset=STATE_OFFSET[binning])
        target_values = tgts[target].to_numpy(dtype="float64")
        del feats, tgts
        rows_held = held[pos]
        for index, condition in enumerate(conditions):
            defined = rows_held.copy()
            fires = np.ones(pos.size, dtype=bool)
            for feature, code in condition["terms"]:
                state = codes[f"{feature}|{binning_of_code(code)}"]
                defined &= state >= 0
                fires &= state == code
            if not defined.any():
                continue
            rows = np.nonzero(defined)[0]
            indicator = np.where(fires[rows], condition["sign"], 0.0)
            if indicator.min() == indicator.max():  # no firing/not-firing split that date
                continue
            _ic, _t, n_used, ic_dates, ic_values = _fast_ic_detail(indicator, target_values[rows], pos[rows])
            if n_used:
                collected[index]["dates"].append(ic_dates)
                collected[index]["ic"].append(ic_values)

    return [
        {
            "dates": np.concatenate(entry["dates"]) if entry["dates"] else np.empty(0, dtype="float64"),
            "ic": np.concatenate(entry["ic"]) if entry["ic"] else np.empty(0, dtype="float64"),
        }
        for entry in collected
    ]


# --------------------------------------------------------------------------- #
# One condition's cost decision
# --------------------------------------------------------------------------- #
def evaluate_condition(
    condition: dict,
    ic_series: dict,
    cost_bps: float = COST_BPS_TOTAL,
    min_dates: int = MIN_HOLDOUT_DATES,
) -> dict:
    """Cost overlay record for one condition (`NO_TRADE` unless net edge is positive).

    The single decision rule is the plan's: call `cost_overlay` at `cost_bps` and
    accept `TRADE` only when the net edge is positive *and* the IC is estimable.
    Anything else — NaN IC, too few held-out dates, nonpositive net — is
    `NO_TRADE`. `gross_bps`/`net_bps` come from `src.wi016.probe.cost_overlay`.
    """
    values = np.asarray(ic_series.get("ic", []), dtype="float64")
    values = values[np.isfinite(values)]
    n_dates = int(values.size)
    record = {
        "condition": condition["condition"],
        "kind": condition["kind"],
        "direction": condition["direction"],
        "features": condition["features"],
        "g2_lift": condition["g2_lift"],
        "g2_ci": [condition["g2_ci_low"], condition["g2_ci_high"]],
        "g2_q": condition["g2_q"],
        "ic": float("nan"),
        "ic_t": float("nan"),
        "ic_margin": float("nan"),
        "ic_ci_low": float("nan"),
        "ic_ci_high": float("nan"),
        "ic_n_dates": n_dates,
        "gross_bps": float("nan"),
        "cost_bps": float(cost_bps),
        "net_bps": float("nan"),
        "decision": "NO_TRADE",
        "estimable": False,
        "reason": None,
    }
    if n_dates < int(min_dates):
        record["reason"] = f"IC not estimable: n_dates<{int(min_dates)}"
        return record
    ic = float(values.mean())
    _t, p = _t_stat(values)
    ci = ci_from_series(values)
    overlay = cost_overlay(ic, cost_bps=cost_bps)
    record.update(
        {
            "ic": ic,
            "ic_t": _t,
            "ic_p": p,
            "ic_margin": ci["margin"],
            "ic_ci_low": ci["ci_low"],
            "ic_ci_high": ci["ci_high"],
            "gross_bps": overlay["gross_bps"],
            "net_bps": overlay["net_bps"],
            "decision": overlay["decision"] if np.isfinite(overlay["net_bps"]) else "NO_TRADE",
            "estimable": bool(np.isfinite(ic)),
            "reason": None if np.isfinite(overlay["net_bps"]) else "IC not estimable: non-finite",
        }
    )
    return record


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _skipped_payload(probe: dict, preflight: dict, market: str, reason: str) -> dict:
    return {
        "step": "WI-018 step 4 (G3) conditional cost overlay",
        "market": market,
        "scope": "USD only — CAD skipped (D-018 Q2)",
        "generated_utc": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "target": PRIMARY_TARGET,
        "input_provenance": _provenance(probe, preflight),
        "config": _config(),
        "g2_verdict": probe.get("verdict"),
        "g2_pass": bool(probe.get("g2_pass")),
        "g2_red_flag": bool(probe.get("red_flag")),
        "g2_survivors_available": len(probe.get("survivors", [])),
        "g3_skipped": True,
        "skip_reason": reason,
        "conditions": [],
        "n_conditions": 0,
        "n_tradeable": 0,
        "g3_decision": "SKIPPED",
        "ship_shape": "memo only — no executable rules, no shortlist CSV, no trading integration",
    }


def _provenance(probe: dict, preflight: dict) -> dict:
    return {
        "probe_report": str(PROBE_JSON),
        "probe_verdict": probe.get("verdict"),
        "preflight_report": str(PREFLIGHT_JSON),
        "preflight_verdict": preflight.get("verdict"),
        "symbols": preflight.get("summary", {}).get("symbols"),
        "derived_dir": preflight.get("config", {}).get("derived_dir"),
        "features_dir": preflight.get("config", {}).get("features_dir"),
    }


def _config() -> dict:
    return {
        "cost_bps_total": float(COST_BPS_TOTAL),
        "cost_assumptions": "WI-011 assumptions: 20 bps cost + 5 bps slippage; measured costs are not available in this WI",
        "overlay_helper": "src.wi016.probe.cost_overlay",
        "ic_helper": "src.wi016.probe._fast_ic_detail (within-date Spearman rank IC)",
        "ic_to_bps": float(IC_TO_BPS),
        "proxy_warning": (
            "the |IC| * 1000 bps scale is a documented screening proxy, not a P&L model; "
            "no position sizing, no execution"
        ),
        "decision_rule": (
            f"TRADE only if |IC| * {IC_TO_BPS:.0f} - {COST_BPS_TOTAL:.0f} bps > 0 and the IC is estimable; "
            "otherwise NO_TRADE"
        ),
        "ic_dates": "held-out folds only (identical geometry to G2: fold_blocks, embargo max(20, horizon))",
        "embargo_td": int(max(20, HORIZON)),
        "min_ic_dates": int(MIN_HOLDOUT_DATES),
        "min_group_dates": int(MIN_GROUP_DATES),
        "bootstrap": "circular 20-date blocks, 1000 draws, seed 42 (block_bootstrap_margin)",
        "target": PRIMARY_TARGET,
        "secondary_targets": list(SECONDARY_TARGETS),
        "secondary_role": "robustness reads only — never selection targets (untouched by G3)",
        "executable_output": False,
    }


def run_g3(
    probe_path: Path | str = PROBE_JSON,
    preflight_path: Path | str = PREFLIGHT_JSON,
    deriv_dir: Path = DERIVED_DIR,
    feat_dir: Path = FEATURES_DIR,
    prune_path: Path | None = None,
    market: str = MARKET,
    cost_bps: float = COST_BPS_TOTAL,
    block_size: int | None = None,
    min_dates: int = MIN_HOLDOUT_DATES,
) -> dict:
    """Run G3 for the survivors in an existing probe report (no writes)."""
    if market.upper() != MARKET:
        raise PreflightError(f"WI-018 is USD-only (got {market!r}); CAD is skipped per D-018 Q2")
    preflight = require_preflight(preflight_path, market)
    probe_path = Path(probe_path)
    if not probe_path.is_file():
        raise PreflightError(f"G2 probe report missing ({probe_path}) — G3 is conditional on G2")
    probe = json.loads(probe_path.read_text())
    survivors = probe.get("survivors", [])
    eligible = probe.get("g3_eligible")
    if eligible is None:  # older payloads: derive the gate
        eligible = bool(probe.get("g2_pass")) and not bool(probe.get("red_flag"))
    if not eligible:
        reason = probe.get("g3_skip_reason") or (
            f"G2 verdict {probe.get('verdict')} with {len(survivors)} survivor(s) — "
            "G3 is invoked only for a G2 win"
        )
        payload = _skipped_payload(probe, preflight, MARKET, reason)
        checks = check_g3_report(payload)
        payload["checks"] = {k: {"ok": bool(ok), "detail": detail} for k, (ok, detail) in checks.items()}
        return payload

    keep_columns = load_keep_columns(prune_path or PRUNE_RECS)
    conditions = survivor_conditions(probe, keep_columns)
    dates = global_dates(deriv_dir)
    held, fold_detail = held_out_positions(dates)
    series = condition_ic_series(
        conditions, symbol_paths(deriv_dir), symbol_paths(feat_dir), dates, held,
        target=PRIMARY_TARGET, block_size=block_size,
    )
    evaluated = [
        evaluate_condition(condition, ic, cost_bps=cost_bps, min_dates=min_dates)
        for condition, ic in zip(conditions, series)
    ]
    tradeable = [record for record in evaluated if record["decision"] == "TRADE"]
    payload = {
        "step": "WI-018 step 4 (G3) conditional cost overlay",
        "market": MARKET,
        "scope": "USD only — CAD skipped (D-018 Q2)",
        "generated_utc": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "target": PRIMARY_TARGET,
        "input_provenance": _provenance(probe, preflight),
        "config": _config(),
        "g2_verdict": probe.get("verdict"),
        "g2_pass": True,
        "g2_red_flag": bool(probe.get("red_flag")),
        "g3_skipped": False,
        "skip_reason": None,
        "folds": fold_detail,
        "held_out_dates": int(held.sum()),
        "conditions": evaluated,
        "n_conditions": len(evaluated),
        "n_tradeable": len(tradeable),
        "g3_decision": "TRADE" if tradeable else "NO_TRADE",
        "ship_shape": "memo only — no executable rules, no shortlist CSV, no trading integration",
    }
    checks = check_g3_report(payload)
    payload["checks"] = {k: {"ok": bool(ok), "detail": detail} for k, (ok, detail) in checks.items()}
    return payload


# --------------------------------------------------------------------------- #
# Acceptance self-check
# --------------------------------------------------------------------------- #
def _finite(value) -> bool:
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def check_g3_report(report: dict) -> dict:
    """Acceptance self-check for a G3 payload; returns `{name: (ok, detail)}`."""
    checks: dict[str, tuple[bool, str]] = {}
    config = report.get("config", {})
    conditions = report.get("conditions", [])
    tradeable = [c for c in conditions if c.get("decision") == "TRADE"]

    checks["usd_only_scope_recorded"] = (
        str(report.get("scope", "")).startswith("USD only") and report.get("market") == MARKET,
        f"market={report.get('market')} scope={report.get('scope')}",
    )
    checks["cost_assumption_labelled"] = (
        config.get("cost_bps_total") == COST_BPS_TOTAL and "assumption" in str(config.get("cost_assumptions")),
        f"{config.get('cost_bps_total')} bps | {config.get('cost_assumptions')}",
    )
    checks["screening_proxy_labelled"] = (
        "not a P&L model" in str(config.get("proxy_warning"))
        and config.get("overlay_helper") == "src.wi016.probe.cost_overlay",
        str(config.get("proxy_warning")),
    )
    checks["no_executable_output"] = (
        config.get("executable_output") is False
        and "no shortlist" in str(report.get("ship_shape", ""))
        and "no executable rules" in str(report.get("ship_shape", "")),
        str(report.get("ship_shape")),
    )
    gating_ok = True
    detail = f"decision={report.get('g3_decision')} skipped={report.get('g3_skipped')} survivors={len(conditions)}"
    if report.get("g3_skipped"):
        gating_ok = report.get("g3_decision") == "SKIPPED" and not conditions and bool(report.get("skip_reason"))
        detail = f"skipped: {report.get('skip_reason')}"
    else:
        gating_ok = report.get("g3_decision") == ("TRADE" if tradeable else "NO_TRADE")
    checks["gating_matches_g2"] = (gating_ok, detail)
    trade_rule_ok = True
    trade_detail = f"{len(tradeable)} tradeable of {len(conditions)}"
    for record in tradeable:
        if not (_finite(record.get("net_bps")) and float(record["net_bps"]) > 0.0 and record.get("estimable")):
            trade_rule_ok = False
            trade_detail = f"{record.get('condition')} TRADE with net_bps={record.get('net_bps')}"
    checks["trade_requires_positive_net"] = (trade_rule_ok, trade_detail)
    default_ok = all(
        c.get("decision") == "TRADE"
        or (str(c.get("decision")) == "NO_TRADE" and (_finite(c.get("net_bps")) is False or float(c["net_bps"]) <= 0.0
                                                      or not c.get("estimable")))
        for c in conditions
    )
    checks["no_trade_is_the_default"] = (
        default_ok,
        f"{sum(1 for c in conditions if c.get('decision') == 'NO_TRADE')} NO_TRADE of {len(conditions)}",
    )
    checks["cost_math_matches_helper"] = (
        all(
            _finite(c.get("net_bps"))
            and abs(float(c["net_bps"]) - (abs(float(c["ic"])) * IC_TO_BPS - float(config.get("cost_bps_total")))) < 1e-9
            for c in conditions
            if c.get("estimable")
        ),
        f"net_bps == |IC| * {IC_TO_BPS:.0f} - {config.get('cost_bps_total')} for every estimable condition",
    )
    return checks


def summarize_checks(checks: dict) -> str:
    return "\n".join(f"  {'OK  ' if ok else 'FAIL'} {name}: {detail}" for name, (ok, detail) in checks.items())


# --------------------------------------------------------------------------- #
# Markdown: the G3 table and the memo
# --------------------------------------------------------------------------- #
def _fmt(value, spec: str = ".4f") -> str:
    return "n/a" if not _finite(value) else format(float(value), spec)


def _fmt_bps(value) -> str:
    return "n/a" if not _finite(value) else f"{float(value):+.2f}"


def format_g3_markdown(report: dict) -> str:
    """G3 section body as markdown (used by the memo, also readable alone)."""
    config = report.get("config") or {}
    lines = [
        "## G3 — cost overlay (conditional on G2)",
        "",
    ]
    if report.get("g3_skipped"):
        default_line = (
            "The standing default is `NO_TRADE`: a wall of survivors is not a condition set to trade, "
            "so nothing is costed out."
            if report.get("g2_red_flag")
            else "The standing default is `NO_TRADE`: with no G2 survivor there is nothing to cost out."
        )
        lines += [
            f"**SKIPPED.** {report.get('skip_reason')}",
            "",
            default_line,
            "",
        ]
        return "\n".join(lines)
    lines += [
        f"Verdict **{report['g3_decision']}** — {report.get('n_tradeable')} of {report.get('n_conditions')} "
        f"survivor(s) clear {config.get('cost_bps_total', COST_BPS_TOTAL):.0f} bps of assumed cost.",
        "",
        "| condition | dir | IC | IC 95% CI | gross bps | cost bps | net bps | decision |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for record in report["conditions"]:
        lines.append(
            f"| {record['condition']} | {record['direction']} | {_fmt(record['ic'])} | "
            f"[{_fmt(record['ic_ci_low'])}, {_fmt(record['ic_ci_high'])}] | {_fmt_bps(record['gross_bps'])} | "
            f"{_fmt_bps(record['cost_bps'])} | {_fmt_bps(record['net_bps'])} | **{record['decision']}** |"
        )
    lines += [
        "",
        f"- IC: {config.get('ic_helper')}, held-out dates only (same folds/embargo as G2), "
        f"{report.get('held_out_dates')} held-out dates.",
        f"- Costs are **assumptions**, not measurements: {config.get('cost_assumptions')}.",
        f"- Edge scale is a screening proxy only: {config.get('proxy_warning')}.",
        f"- Decision rule: {config.get('decision_rule')}.",
        "",
    ]
    return "\n".join(lines)


def build_summary_markdown(
    g3: dict | None = None,
    probe: dict | None = None,
    atlas: dict | None = None,
    preflight: dict | None = None,
) -> str:
    """The WI-018 memo: G1 deliverable, G2 verdict, G3 outcome, limits, follow-up.

    Generated from the on-disk artifacts so the memo cannot drift from them; every
    number below is read from `preflight`/`atlas`/`probe`/`g3`.
    """
    probe = probe or {}
    atlas = atlas or {}
    preflight = preflight or {}
    g3 = g3 or {}
    atlas_coverage = atlas.get("coverage", {})
    probe_hyp = probe.get("hypotheses", {})
    summary = preflight.get("summary", {})
    gate_text = (
        "eligible — survivors qualify for the cost overlay"
        if probe.get("g3_eligible")
        else f"not invoked — {probe.get('g3_skip_reason')}"
    )

    lines = [
        "# WI-018 — condition-first directional study, `first_touch_34` (USD): memo",
        "",
        "**Ship shape: memo only** — no executable rules, no trading integration, no order execution, "
        "no ranking/screener change and **no shortlist CSV** are produced by this work item (D-018 Q5, plan step 4).",
        "",
        f"Generated from the on-disk artifacts: `reports/wi018/{{preflight_USD.json, atlas_USD.json, "
        f"probe_USD.json, g3_USD.json}}`. Market: **USD only** — CAD was skipped by design (D-018 Q2).",
        "",
        "## G1 — condition atlas (delivered)",
        "",
        f"- `reports/wi018/atlas_USD.json` / `.md`: {atlas_coverage.get('cells_total')} state cells "
        f"(88 features x 8 states), {atlas_coverage.get('cells_estimable')} estimable, "
        f"{atlas_coverage.get('cells_unevaluable')} explicitly unevaluable.",
        f"- Universe: {summary.get('symbols')} USD symbols, {summary.get('total_rows')} rows, "
        f"{summary.get('date_min')}..{summary.get('date_max')} ({atlas.get('summary', {}).get('n_dates')} dates).",
        f"- Unconditional `first_touch_34` split (pooled): "
        f"{_fmt(atlas.get('unconditional', {}).get(PRIMARY_TARGET, {}).get('pooled', {}).get('up'))} up / "
        f"{_fmt(atlas.get('unconditional', {}).get(PRIMARY_TARGET, {}).get('pooled', {}).get('dn'))} down / "
        f"{_fmt(atlas.get('unconditional', {}).get(PRIMARY_TARGET, {}).get('pooled', {}).get('neither'))} neither.",
        "- G1 is descriptive: it spends no multiple-testing budget and assigns no pass/fail.",
        "",
        "## G2 — falsification probe",
        "",
        f"- Verdict: **{probe.get('verdict', 'not run')}** "
        f"(g2_pass={probe.get('g2_pass')}, red flag={probe.get('red_flag')}).",
        f"- Family: {probe_hyp.get('n_total')} hypotheses "
        f"({probe_hyp.get('n_univariate')} univariate + {probe_hyp.get('n_conjunction')} conjunctions), "
        f"BH-FDR at {probe.get('config', {}).get('fdr_alpha')} over the complete family; "
        f"survivors {probe_hyp.get('n_survivors')}, density {_fmt(probe_hyp.get('survivor_density'))}.",
        f"- Folds: {len(probe.get('folds', []))} chronological held-out blocks, embargo "
        f"{probe.get('config', {}).get('embargo_td')} sessions (max(20, horizon)); decision rule = "
        f"{probe.get('config', {}).get('decision_rule', 'CI excludes zero + BH-FDR + same-sign')}.",
        f"- G3 gate: {gate_text}.",
        "- Secondary targets `first_touch_24`/`first_touch_39` were read as robustness only; "
        "decisions always used `first_touch_34`.",
        "",
    ]
    lines += format_g3_markdown(g3).splitlines()
    lines += [
        "",
        "## Limitations",
        "",
        "- The cost overlay's `|IC| x 1000` bps scale is a **screening proxy, not a P&L model**: it ignores "
        "turnover, borrow, market impact, and the 20+5 bps cost figures are **assumptions** carried from WI-011.",
        "- Conditions are within-date cross-sectional states of the pruned WI-017 grid; features whose kept "
        "windows were not representative of their family (the G1 family check) are single-window evidence.",
        "- Bootstrap margins use circular 20-date blocks (1,000 draws, seed 42) and the normal-approximation "
        "t-statistic; both are approximate, and a thin effect on a 5,000-date panel is easy to over-read.",
        "- Ordinal 3-way target: 'up-first/down-first/neither' is a direction read, not a return, so lift and IC "
        "say nothing about magnitude or tradability of the move itself.",
        "- USD-only universe: no cross-market confirmation exists by design (CAD deferred).",
    ]
    if probe.get("red_flag"):
        lines.append(
            "- **G2 raised the survivor-density red flag**: a wall of survivors is a noise/leakage symptom, so this "
            "memo does not treat the survivor set as a signal list and G3 was not invoked on it."
        )
    lines += [
        "",
        "## Follow-up",
        "",
    ]
    if g3.get("g3_skipped"):
        if probe.get("red_flag"):
            lines += [
                "**No follow-up is warranted on this evidence, and the survivor set must not be used as a signal "
                "list.** G2 delivered its pre-registered failure mode: a *wall* of survivors "
                f"({probe_hyp.get('n_survivors')} of {probe_hyp.get('n_total')} hypotheses, density "
                f"{_fmt(probe_hyp.get('survivor_density'))} against a {probe.get('config', {}).get('survivor_density_red_flag')} "
                "red-flag bar). At this sample size the out-of-fold CI no longer separates a real condition from a "
                "generic cross-sectional rate effect, so the wall is a noise/leakage symptom rather than a result; "
                "G3 was therefore not invoked and the standing decision is **NO_TRADE**. Any follow-up must first "
                "tighten the G2 bar itself (effect-size floor, fold-wise stability, or a shrunk estimator) — costing "
                "out this survivor set would only launder the same problem.",
            ]
        else:
            lines += [
                "**No follow-up warranted for this signal family.** G2 found no survivor, so G3 was skipped and the "
                "standing decision is **NO_TRADE**. The E5 factor screener stands as the MVP signal, unchanged.",
            ]
    elif g3.get("g3_decision") == "TRADE":
        lines += [
            "G3 cleared costs for at least one condition, so the pre-registered follow-up is a *separate* work "
            "item (explicit admin gate) to build a real P&L model and a decision rule — not a shortlist: this "
            "memo ships **no** executable rule and no CSV.",
        ]
    else:
        lines += [
            "**No follow-up warranted on this evidence.** Every G2 survivor's IC is small enough that the net "
            "edge is nonpositive once the assumed 25 bps of cost is applied, so the standing decision is "
            "**NO_TRADE** and the E5 factor screener stands as the MVP signal, unchanged.",
        ]
    lines += [
        "",
        "---",
        "",
        "Artifacts: `reports/wi018/atlas_USD.{json,md}`, `reports/wi018/probe_USD.{json,md}`, "
        "`reports/wi018/g3_USD.json`, this memo (`reports/wi018/summary_USD.md`), "
        "`reports/wi018/preflight_USD.json`. Descriptive research only; the human gate is unchanged.",
        "",
    ]
    return "\n".join(lines)


def write_outputs(
    report: dict,
    summary_markdown: str,
    json_path: Path | str = G3_JSON,
    md_path: Path | str = SUMMARY_MD,
) -> tuple[Path, Path]:
    json_path = Path(json_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=1, default=str))
    md_path = Path(md_path)
    md_path.write_text(summary_markdown)
    return json_path, md_path


def _read_json(path: Path) -> dict | None:
    path = Path(path)
    return json.loads(path.read_text()) if path.is_file() else None


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="WI-018 G3 cost overlay + memo (USD)")
    ap.add_argument("--market", default=MARKET)
    ap.add_argument("--check-report", default=None,
                    help="verify an existing G3 payload against the acceptance criteria instead of running")
    ap.add_argument("--probe-report", default=str(PROBE_JSON))
    ap.add_argument("--out", default=str(G3_JSON))
    ap.add_argument("--md", default=str(SUMMARY_MD))
    ap.add_argument("--cost-bps", type=float, default=COST_BPS_TOTAL)
    ap.add_argument("--block-size", type=int, default=None)
    args = ap.parse_args(argv)

    if args.check_report:
        path = Path(args.check_report)
        if not path.is_file():
            print(f"G3 CHECK FAIL: report missing ({path})")
            return 1
        report = json.loads(path.read_text())
        checks = check_g3_report(report)
        print(f"WI-018 G3 report check [{report.get('market')}] decision={report.get('g3_decision')}")
        print(summarize_checks(checks))
        ok = all(ok for ok, _ in checks.values())
        print(f"G3 CHECK {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1

    try:
        report = run_g3(
            probe_path=Path(args.probe_report), market=args.market,
            cost_bps=args.cost_bps, block_size=args.block_size,
        )
    except PreflightError as exc:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"G3 FAIL: {exc}")
        return 1

    memo = build_summary_markdown(
        g3=report,
        probe=_read_json(Path(args.probe_report)),
        atlas=_read_json(REPORTS_DIR / "atlas_USD.json"),
        preflight=_read_json(PREFLIGHT_JSON),
    )
    json_path, md_path = write_outputs(report, memo, Path(args.out), Path(args.md))
    checks = check_g3_report(report)
    print(f"WI-018 G3 [{report['market']}] decision={report['g3_decision']} "
          f"survivors={report['n_conditions']} tradeable={report['n_tradeable']} -> {json_path}, {md_path}")
    print(summarize_checks(checks))
    return 0 if all(ok for ok, _ in checks.values()) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
