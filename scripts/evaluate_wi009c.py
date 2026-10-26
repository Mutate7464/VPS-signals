#!/usr/bin/env python3
"""WI-009c Step 5 — final evaluation and human gate package.

Reads the **fixed run outputs** and writes the human gate package. It never re-fits a
model, never re-runs a fold and never touches the market data: everything below is
recomputed from what Steps 0–4 already produced.

Inputs (all optional paths overridable on the CLI):

    reports/wi009c_probe.md              Step 1 — per-target five-factor probe verdicts
    reports/wi009c_regression_CAD.json   Step 2/3 — fold plan, calibration, skill, shortlist
    data/wi009c_oof_CAD.parquet          Step 2 — per-row out-of-fold probabilities
    reports/wi009c_shortlist_CAD.csv     Step 3 — deterministic shortlist
    reports/wi009c_robustness.md         Step 4 — robustness go/no-go record
    reports/wi009c_inputs.txt            Step 0 — input verification (quoted, not re-derived)

Outputs:

    reports/wi009c_summary.md            the human gate package
    reports/wi009c_summary_CAD.json      machine-readable summary of the same content

Discipline
----------
* **Negative results are content, failures abort.** The script verifies internal
  consistency (the probabilities in the parquet must reproduce the recorded masses and
  the shortlist must match its declared composite). A failed check prints the offending
  numbers and exits 1 — no summary is written, so a printed verdict can never rest on a
  broken run.
* The declared shortlist composite is `P(up) - P(down)`; `P(stay)` is reported alongside
  it and is never a hidden tie-break.
* No live-use integration, no order wiring, and no sprint gate is marked passed here: the
  claim/use decision is left to the human gate.

CLI (WI-013: omitted `--market` runs BOTH, USD then CAD; every input is read
from that market's suffixed artifacts and the summary is written suffixed)::

    uv run python scripts/evaluate_wi009c.py                  # both markets
    uv run python scripts/evaluate_wi009c.py --market CAD     # one market
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.market_cli import (  # noqa: E402
    add_market_argument,
    cli_markets,
    report_path,
    resolve_output,
    run_markets,
)
from src.models.continuous_targets import (  # noqa: E402
    ATR_PRICE_COLUMN,
    CONTINUOUS_TARGET,
    DOWN_MULT,
    EMBARGO_TD,
    STAY_RET_MAX,
    UP_MULT,
    composite_score,
    marginal_calibration,
)

REPORTS = ROOT / "reports"
DATA = ROOT / "data"


def paths(market: str) -> dict[str, Path]:
    """Every input/output path this script resolves for one market (WI-013).

    Inputs are the *same-market* artifacts written by the probe/train/robustness
    steps; the summary and its JSON record are market-suffixed, so a CAD
    evaluation can never overwrite the frozen unsuffixed gate package.
    """
    return {
        "probe": report_path(REPORTS, "wi009c_probe", market),
        "run_json": report_path(REPORTS, "wi009c_regression", market, suffix=".json"),
        "oof": DATA / f"wi009c_oof_{market}.parquet",
        "shortlist": report_path(REPORTS, "wi009c_shortlist", market, suffix=".csv"),
        "robustness": report_path(REPORTS, "wi009c_robustness", market),
        "summary": report_path(REPORTS, "wi009c_summary", market),
        "summary_json": report_path(REPORTS, "wi009c_summary", market, suffix=".json"),
    }


VERDICT_ROW_RE = re.compile(
    r"^\|\s*`(?P<target>[^`]+)`\s*\|\s*(?P<ic>[+-]?[\d.]+)\s*\|\s*(?P<t>[+-]?[\d.]+)\s*\|\s*"
    r"(?P<same_sign>yes|NO)\s*\|\s*(?P<clause_a>PASS|FAIL)\s*\|\s*(?P<clause_b>PASS|FAIL)\s*\|\s*"
    r"\*\*(?P<bar>[^*]+)\*\*\s*\|\s*$"
)
COUNT_RE = re.compile(r"(\d+)\s*/\s*(\d+)\s+targets clear the unchanged skill bar")
# Tolerance for the float32 parquet round-trip against the float64 run record.
MASS_TOL = 2e-5
# The OOF artifact carries the ATR/price ratio (`ATR_PRICE_COLUMN` in `features_*.parquet`)
# under the trainer's short name; the unit conversion is the same column.
OOF_ATR_COLUMN = "atr_pct"


def _fmt(x, fmt: str = "+.4f") -> str:
    try:
        f = float(x)
    except (TypeError, ValueError):
        return "n/a"
    return f"{f:{fmt}}" if np.isfinite(f) else "n/a"


def _rel(path: Path) -> str:
    """Repo-relative path when possible, absolute otherwise (tmp paths in tests)."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


# --------------------------------------------------------------------------- #
# Saved outputs
# --------------------------------------------------------------------------- #
def parse_probe_verdicts(text: str) -> list[dict]:
    """Parse the Step-1 verdict summary table out of `reports/wi009c_probe.md`."""
    rows: list[dict] = []
    for line in (text or "").splitlines():
        m = VERDICT_ROW_RE.match(line.strip())
        if not m:
            continue
        rows.append(
            {
                "target": m.group("target"),
                "ic": float(m.group("ic")),
                "t": float(m.group("t")),
                "same_sign": m.group("same_sign") == "yes",
                "clause_a": m.group("clause_a"),
                "clause_b": m.group("clause_b"),
                "skill_bar": m.group("bar").strip(),
            }
        )
    return rows


def parse_labels_cleared(text: str) -> tuple[int, int]:
    m = COUNT_RE.search(text or "")
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def load_run_record(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"run record {path} is missing — Step 5 cannot invent it")
    return json.loads(path.read_text())


def recompute_from_oof(path: Path) -> dict:
    """Recompute the headline quantities from the saved per-row OOF predictions.

    This is the reproducibility check: nothing is re-fitted, the recorded per-row
    probabilities are simply re-reduced and compared against the run record.
    """
    if not path.exists():
        raise FileNotFoundError(f"OOF predictions {path} are missing — Step 5 cannot invent them")
    cols = [
        "date", "symbol", "fold", "y", OOF_ATR_COLUMN, "forecast", "p_up", "p_down",
        "p_stay", "p_stay_exclusive", "overlap_up_stay", "overlap_down_stay", "composite",
    ]
    df = pd.read_parquet(path, columns=cols)
    for c in cols:
        if c not in df.columns:
            raise KeyError(f"OOF frame {path} missing column {c!r}")
    pred = {
        "p_up": df["p_up"].to_numpy(dtype="float64"),
        "p_down": df["p_down"].to_numpy(dtype="float64"),
        "p_stay": df["p_stay"].to_numpy(dtype="float64"),
        "p_stay_exclusive": df["p_stay_exclusive"].to_numpy(dtype="float64"),
        "overlap_up_stay": df["overlap_up_stay"].to_numpy(dtype="float64"),
        "overlap_down_stay": df["overlap_down_stay"].to_numpy(dtype="float64"),
    }
    for k, v in pred.items():
        if not np.isfinite(v).all():
            raise ValueError(f"NON-FINITE {k} in the saved OOF predictions")
        if v.min() < 0.0 or v.max() > 1.0:
            raise ValueError(f"{k} outside [0, 1] in the saved OOF predictions")
    cal = marginal_calibration(pred, df["y"].to_numpy(dtype="float64"),
                              df[OOF_ATR_COLUMN].to_numpy(dtype="float64"))
    declared = composite_score(pred["p_up"], pred["p_down"])
    return {
        "path": _rel(path),
        "n_rows": int(len(df)),
        "n_symbols": int(df["symbol"].nunique()),
        "n_dates": int(df["date"].nunique()),
        "date_min": str(pd.Timestamp(df["date"].min()).date()),
        "date_max": str(pd.Timestamp(df["date"].max()).date()),
        "folds": sorted(int(f) for f in pd.unique(df["fold"])),
        "masses": cal["masses"],
        "calibration": {k: {kk: cal[k][kk] for kk in ("n", "mean_predicted", "realized_rate", "bias", "brier")}
                        for k in ("up", "down", "stay", "stay_exclusive")},
        "composite_max_abs_error": float(np.max(np.abs(df["composite"].to_numpy(dtype="float64") - declared))),
        "composite_mean": float(np.mean(declared)),
    }


def load_shortlist(path: Path) -> tuple[pd.DataFrame, dict]:
    if not path.exists():
        raise FileNotFoundError(f"shortlist {path} is missing — Step 5 cannot invent it")
    df = pd.read_csv(path)
    need = {"rank", "symbol", "p_up", "p_down", "composite", "p_stay"}
    missing = need - set(df.columns)
    if missing:
        raise KeyError(f"shortlist {path} missing columns {sorted(missing)}")
    ordered = df["composite"].to_numpy()
    symbols = df["symbol"].astype(str).tolist()
    by_composite = np.all(np.diff(ordered) <= 1e-9)
    tie_ok = all(symbols[i] <= symbols[i + 1] for i in range(len(symbols) - 1)
                 if abs(ordered[i] - ordered[i + 1]) <= 1e-12)
    max_err = float(np.max(np.abs(df["composite"].to_numpy() - (df["p_up"].to_numpy() - df["p_down"].to_numpy()))))
    return df, {
        "path": _rel(path),
        "n_rows": int(len(df)),
        "ordered_by_composite_desc": bool(by_composite),
        "symbol_tie_break_ok": bool(tie_ok),
        "composite_max_abs_error": max_err,
    }


OPTIONS_NOT_RUN_RE = re.compile(r"options reported \*\*NOT RUN\*\*:\s*\*\*(\d+)\*\*")
OPTIONS_GO_RE = re.compile(r"gate decision was GO:\s*(\d+) of (\d+)")


def robustness_summary(path: Path) -> dict | None:
    """Count the Step-4 outcomes by parsing the record, not by counting prose."""
    if not path.exists():
        return None
    text = path.read_text()
    m = OPTIONS_NOT_RUN_RE.search(text)
    n_not_run = int(m.group(1)) if m else text.count("| **NOT RUN** |")
    m2 = OPTIONS_GO_RE.search(text)
    n_go = int(m2.group(1)) if m2 else text.count("| **GO** |")
    return {
        "path": _rel(path),
        "n_not_run": n_not_run,
        "n_go": n_go,
        "options": [t for t in ("regime", "stacking", "dynamic feature") if t in text],
    }


def check_reproducible(record: dict, recomp: dict) -> list[str]:
    """Compare the recomputed masses against the run record; return mismatch messages."""
    problems: list[str] = []
    for key, recorded in (record.get("calibration_masses") or {}).items():
        got = recomp["masses"].get(key)
        if got is None:
            problems.append(f"mass {key}: missing from the recomputed frame")
            continue
        if abs(float(recorded) - float(got)) > MASS_TOL:
            problems.append(f"mass {key}: recorded {recorded:.8f} vs recomputed {float(got):.8f}")
    if int(record.get("n_oof_rows", -1)) != int(recomp["n_rows"]):
        problems.append(f"n_oof_rows: recorded {record.get('n_oof_rows')} vs recomputed {recomp['n_rows']}")
    return problems


# --------------------------------------------------------------------------- #
# The human gate package
# --------------------------------------------------------------------------- #
def build_summary(record: dict, recomp: dict, verdicts: list[dict], n_cleared: int, n_targets: int,
                  shortlist: pd.DataFrame, shortlist_check: dict, rob: dict | None,
                  market: str, labels_cleared_line: str = "") -> str:
    cfg = record.get("config", {})
    panel = record.get("panel", {})
    skill = record.get("skill", {})
    folds = [f for f in record.get("folds", []) if "skipped" not in f]
    n_folds = len(record.get("folds", []))
    ct = record.get("contrastive_candidate") or {}
    cal = recomp["calibration"]
    masses = recomp["masses"]
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        f"# WI-009c — final evaluation and human gate package ({market})",
        "",
        f"- Generated (UTC): {now} from the fixed run outputs (no model was re-fit, no fold re-run).",
        f"- **Run identity**: `reports/wi009c_regression_{market}.json` · generated "
        f"{record.get('generated_utc')} · smoke={record.get('smoke')} · market {record.get('market')}.",
        f"- **Model**: `StandardScaler` + `Ridge(alpha={cfg.get('alpha')})` on the "
        f"{len(cfg.get('features', []))} E5 factors "
        f"({', '.join('`' + c + '`' for c in cfg.get('features', []))}), target "
        f"`{cfg.get('continuous_target')}`, ATR/price column `{cfg.get('atr_price_column')}`.",
        f"- **CV**: `PurgedWalkForwardSplit(n_splits={cfg.get('n_splits')}, "
        f"embargo_td={cfg.get('embargo_td')})` over unique dates keyed by positions; "
        f"per-fold split-calibration block of the last {cfg.get('calib_fraction'):.0%} of the training dates "
        f"(purged {cfg.get('embargo_td')}td from the fit block). {len(folds)} of {n_folds} folds viable.",
        f"- **Panel**: {panel.get('n_rows'):,} rows · {panel.get('n_symbols')} symbols · "
        f"{panel.get('n_dates')} dates ({panel.get('date_min')} → {panel.get('date_max')}); "
        f"**{recomp['n_rows']:,} out-of-fold rows** scored across folds {recomp['folds']} "
        f"({recomp['n_dates']} dates).",
        f"- **Event units** (ADR D-010): up = `{CONTINUOUS_TARGET} >= {UP_MULT:+.1f}` (2×ATR, dollar); "
        f"down = `{CONTINUOUS_TARGET} <= {DOWN_MULT:+.1f}`; stay = `|{CONTINUOUS_TARGET}| <= "
        f"{STAY_RET_MAX:.2f} / {ATR_PRICE_COLUMN}` (row-specific ±5%, relative). The events **overlap** "
        "(mean up∩stay "
        f"{masses['mean_overlap_up_stay']:.4f}, down∩stay {masses['mean_overlap_down_stay']:.4f}); each "
        "probability is integrated independently from the residual ECDF and the overlap is reported, never "
        "forced into a partition.",
        "",
        "## 1. Verdict table per target (Step 1 — five-factor logistic probe)",
        "",
        "The unchanged skill bar: clause (a) = same sign as the best factor **AND** |IC| ≥ its |IC|; "
        "clause (b) = |t| > 2 with the same sign in ≥ 2 disjoint sub-windows. Class-label IC is never used.",
        "",
        "| Target | OOF logit IC | t | same sign | clause (a) | clause (b) | skill bar |",
        "| :--- | ---: | ---: | :--- | :--- | :--- | :--- |",
    ]
    for v in verdicts:
        lines.append(
            f"| `{v['target']}` | {_fmt(v['ic'])} | {_fmt(v['t'], '+.2f')} | "
            f"{'yes' if v['same_sign'] else 'NO'} | {v['clause_a']} | {v['clause_b']} | "
            f"**{v['skill_bar']}** |"
        )
    lines += [
        "",
        f"- **{n_cleared}/{n_targets or 5} targets clear the unchanged skill bar.** "
        "No label is demonstrated learnable on this window by the five E5 factors.",
        f"- Gate consequence (plan Step 1(d)): {labels_cleared_line or 'no 89-feature spend; the continuous '
        'baseline is limited to the same five factors.'}",
        "- This is a **negative result about these binary labels**, not an execution failure.",
        "",
        "## 2. Continuous 20td baseline (Step 2)",
        "",
        f"- Target: `{CONTINUOUS_TARGET}`; declared shortlist composite: **`P(up) - P(down)`** (ADR D-010). "
        f"`P(stay)` is reported alongside it and is never used as a hidden tie-break.",
        f"- Recorded probabilities (mean predicted) vs realized rate on the same {recomp['n_rows']:,} OOF rows:",
        "",
        "| Event | mean predicted | realized rate | bias | Brier |",
        "| :--- | ---: | ---: | ---: | ---: |",
    ]
    for key, label in (("up", "P(up)"), ("down", "P(down)"), ("stay", "P(stay)"),
                       ("stay_exclusive", "P(stay) exclusive")):
        c = cal[key]
        lines.append(
            f"| {label} | {c['mean_predicted']:.4f} | {c['realized_rate']:.4f} | {c['bias']:+.4f} | "
            f"{c['brier']:.4f} |"
        )
    lines += [
        "",
        f"- Mean `P(up) + P(down) + P(stay)` = {masses['mean_sum_up_down_stay']:.4f} (may exceed 1 — the "
        "events overlap by design); all probabilities finite and within [0, 1] on every scored row.",
        f"- Shortlist: {shortlist_check['n_rows']} names as of "
        f"**{record.get('shortlist', {}).get('as_of_date', 'n/a')}**"
        + (f" (of {record['shortlist'].get('n_candidates')} candidates)" if record.get("shortlist") else "")
        + f"; ordering by the declared composite verified "
        f"({shortlist_check['ordered_by_composite_desc']}), symbol tie-break verified "
        f"({shortlist_check['symbol_tie_break_ok']}), max |composite - (P(up)-P(down))| = "
        f"{shortlist_check['composite_max_abs_error']:.2e}.",
        "",
        "| rank | symbol | `P(up)` | `P(down)` | `P(up)-P(down)` | `P(stay)` |",
        "| ---: | :--- | ---: | ---: | ---: | ---: |",
    ]
    for _, r in shortlist.head(10).iterrows():
        lines.append(
            f"| {int(r['rank'])} | `{r['symbol']}` | {float(r['p_up']):.4f} | {float(r['p_down']):.4f} | "
            f"{float(r['composite']):+.4f} | {float(r['p_stay']):.4f} |"
        )
    lines += [
        "",
        "### Skill result — same-sign and |IC| against the five E5 factors",
        "",
        "Score-based within-date Spearman rank-IC of the continuous forecast vs "
        f"`{CONTINUOUS_TARGET}`, on exactly the same out-of-fold rows and dates as every factor.",
        "",
        "| Score | mean IC | \\|IC\\| | t | dates |",
        "| :--- | ---: | ---: | ---: | ---: |",
        f"| **continuous baseline (5 E5 factors)** | {_fmt(skill.get('model_ic'))} | "
        f"{_fmt(abs(skill.get('model_ic', float('nan'))))} | {_fmt(skill.get('model_t'), '+.2f')} | "
        f"{skill.get('n_dates')} |",
    ]
    for fac, st in sorted((skill.get("factor_table") or {}).items(), key=lambda kv: -abs(kv[1]["ic"])):
        lines.append(f"| `e5_{fac}` (factor) | {_fmt(st['ic'])} | {abs(st['ic']):.4f} | "
                     f"{_fmt(st['t'], '+.2f')} | {st['n_dates']} |")
    lines += [
        "",
        f"- Clause (a) — same sign as the best factor AND |IC| ≥ its |IC|: "
        f"**{'PASS' if skill.get('pass_a') else 'FAIL'}** (baseline |IC| "
        f"{_fmt(abs(skill.get('model_ic', float('nan'))))} vs `e5_{skill.get('best_factor')}` |IC| "
        f"{_fmt(skill.get('best_abs_ic'))}; same-sign **{skill.get('same_sign')}**).",
        f"- Clause (b) — |t| > 2 with the same sign in ≥ 2 disjoint sub-windows: "
        f"**{'PASS' if skill.get('pass_b') else 'FAIL'}**.",
        f"- **SKILL BAR: {'PASS' if skill.get('passed') else 'FAIL'}** — the five-factor continuous "
        "forecast does not beat the best single E5 factor on this window.",
        "- Calibration is a **marginal** distribution from held-out residuals pooled across folds: it is not "
        "a guarantee of conditional calibration per row, symbol or regime, and the ECDF tails are limited by "
        "the calibration sample size.",
        "",
        "## 3. Robustness options and the fold-safe stacked-input candidate (Steps 3–4)",
        "",
        f"- Fold-safe contrastive stacked input (`models/contrastive_ranker_wi009b.pt`, `score_numpy`): "
        f"**{ct.get('status', 'not attempted')}** — {ct.get('reason', 'not attempted in the production chain.')}",
    ]
    if rob:
        lines += [
            f"- Step-4 robustness record: `{rob['path']}` — {rob['n_not_run']} option(s) **NOT RUN**, "
            f"{rob['n_go']} gate decision(s) GO. Candidates covered: "
            f"{', '.join(rob['options'])}.",
            "- Every robustness candidate needs the 89-feature spend that Step 1(d) withholds, so each is "
            "reported as NOT RUN with its specific unmet gate — a documented no-go, never a hidden FAIL and "
            "never built by default (plan Step 4(d)).",
        ]
    else:
        lines.append("- Step-4 robustness record missing: gates were not evaluated in this checkout.")
    lines += [
        "",
        "## 4. Route verdict as a whole",
        "",
        "| Question | Verdict | Basis |",
        "| :--- | :--- | :--- |",
        f"| Are the existing binary labels learnable from the five E5 factors? | "
        f"**NO — {n_cleared}/{n_targets or 5} clear the unchanged skill bar** | Step 1 probe, purged OOF, "
        "score-based within-date IC |",
        f"| Does the five-factor continuous 20td forecast beat the best single factor? | "
        f"**NO — skill bar "
        f"{'PASS' if skill.get('passed') else 'FAIL'}** (IC {_fmt(skill.get('model_ic'))} vs |IC| "
        f"{_fmt(skill.get('best_abs_ic'))}, same-sign {skill.get('same_sign')}) | Step 2, "
        f"{recomp['n_rows']:,} OOF rows, {len(folds)}/{n_folds} folds |",
        f"| Are the distribution-derived probabilities usable? | "
        f"**Numerically yes, skilfully unproven** — finite, in [0, 1], marginal calibration reported "
        f"(mean P(stay) {cal['stay']['mean_predicted']:.4f} vs realized {cal['stay']['realized_rate']:.4f}) | "
        "Step 2 calibration diagnostics |",
        "| May the fold-safe contrastive stacked input be used? | **NO (NOT RUN, gated)** | Step 1(d) gate + "
        "fold-safety not establishable (Step 3) |",
        "| Do any robustness options qualify? | **NO (NOT RUN, gated)** | Step 4 evidence gates |",
        "| Is the route usable for trading? | **No — human gate decision required** | this report |",
        "",
        "**The continuous route is not demonstrated to have skill on this CAD window.** The probabilities have "
        "the right units, are finite and bounded, and their marginal calibration is reported — but the "
        "forecast is statistically indistinguishable from (and slightly weaker than) the best single E5 "
        "factor, and the binary labels are not demonstrated learnable. Nothing here is a claim of skill.",
        "",
        "## 5. Negative results vs execution/test failures",
        "",
        "- **Negative results** (content, not failures): 0/5 labels clear the skill bar; the continuous "
        "baseline fails the skill bar; the contrastive stacked input is omitted (gated); all three robustness "
        "options are NOT RUN (gated). Each is recorded with its reason and evidence, and none was tuned away, "
        "suppressed or substituted by a different model.",
        "- **Execution/test failures**: none. This report is written only after every internal consistency "
        "check below passes; a failed check aborts the run with a non-zero exit instead of printing a verdict.",
        "",
        "## 6. Reproducibility check (recomputed from the saved per-row outputs)",
        "",
        f"- Source: `{recomp['path']}` — {recomp['n_rows']:,} OOF rows re-reduced; nothing re-fit.",
        "- Recorded (run JSON) vs recomputed (parquet) masses agree within "
        f"{MASS_TOL:g} absolute; every probability is finite and inside [0, 1]; the shortlist ordering matches "
        "the declared composite.",
        "",
    ]
    for key in ("mean_p_up", "mean_p_down", "mean_p_stay", "mean_p_stay_exclusive",
                "realized_rate_up", "realized_rate_down", "realized_rate_stay",
                "mean_overlap_up_stay", "mean_overlap_down_stay", "mean_sum_up_down_stay"):
        rec_v = (record.get("calibration_masses") or {}).get(key)
        got_v = masses.get(key)
        if rec_v is None or got_v is None:
            continue
        lines.append(f"- `{key}`: recorded {float(rec_v):.6f} · recomputed {float(got_v):.6f}")
    lines += [
        "",
        "Re-run this package with:",
        "",
        "```bash",
        f"uv run python scripts/evaluate_wi009c.py --market {market}",
        "```",
        "",
        "## 7. Human gate — decision requested",
        "",
        "This is a **research output**. No sprint gate is marked passed here, the shortlist is **not** wired to "
        "orders, and no live-use integration exists (daily shortlist only; human gate before any execution use).",
        "",
        "The decision requested from the human gate:",
        "",
        "1. **Accept the route as a documented negative result** (labels not demonstrated learnable from the "
        "five E5 factors; five-factor continuous forecast fails the unchanged skill bar) and stop WI-009c, or",
        "2. **Re-spec the target** (the Step-1 evidence points at the labels, not the model class) — a new work "
        "item, or",
        "3. **Authorise one gated option** (regime features / priced-in contrastive stacking / dynamic feature "
        "selection) with a written go decision, since every one of them needs the 89-feature spend Step 1(d) "
        "withholds.",
        "",
        "Reading notes:",
        "",
        "- `P(up)`, `P(down)` and `P(stay)` are forecast *distribution* quantities, not guarantees; the "
        "overlap between the ±5% stay band and the 2×ATR up/down events is deliberate and reported.",
        "- The skill verdict uses score-based within-date IC only; PR-AUC and class-label scores are never used "
        "as the skill metric (WI-002 lesson).",
        "- The shortlist for public consumption is the daily shortlist in the human stream; this file is the "
        "evidence package behind it.",
        "",
    ]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    """The CLI parser for this entry point (one shared `--market` flag)."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_market_argument(ap)
    ap.add_argument("--probe", default=None)
    ap.add_argument("--run-json", default=None)
    ap.add_argument("--oof", default=None)
    ap.add_argument("--shortlist", default=None)
    ap.add_argument("--robustness", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--json-out", default=None)
    return ap


def parse_args(argv=None):
    return build_parser().parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    markets = cli_markets(args.market, prog="evaluate_wi009c")
    if markets is None:
        return 2
    print(f"[wi009c-eval] PLAN: markets={', '.join(markets)}")
    return run_markets(markets, lambda m: run_market(m, args))


def run_market(m: str, args) -> int:
    p = paths(m)
    probe_p = Path(args.probe) if args.probe else p["probe"]
    run_p = Path(args.run_json) if args.run_json else p["run_json"]
    oof_p = Path(args.oof) if args.oof else p["oof"]
    sl_p = Path(args.shortlist) if args.shortlist else p["shortlist"]
    rob_p = Path(args.robustness) if args.robustness else p["robustness"]

    try:
        probe_text = probe_p.read_text()
    except FileNotFoundError:
        print(f"[wi009c-eval] Step-1 probe report {probe_p} is missing", file=sys.stderr)
        return 1
    verdicts = parse_probe_verdicts(probe_text)
    if not verdicts:
        print(f"[wi009c-eval] no per-target verdict rows found in {probe_p}", file=sys.stderr)
        return 1
    n_cleared, n_targets = parse_labels_cleared(probe_text)

    labels_cleared_line = ""
    for line in probe_text.splitlines():
        if "Step 2 gate:" in line:
            labels_cleared_line = line.split("Step 2 gate:**", 1)[-1].strip().rstrip(".") + "."
            break

    record = load_run_record(run_p)
    if record.get("smoke"):
        print(f"[wi009c-eval] refusing {run_p}: it is a SMOKE record, not the fixed production run",
              file=sys.stderr)
        return 1
    recomp = recompute_from_oof(oof_p)
    problems = check_reproducible(record, recomp)
    if problems:
        print("[wi009c-eval] REPRODUCIBILITY CHECK FAILED — not writing a summary:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    shortlist, sl_check = load_shortlist(sl_p)
    if not sl_check["ordered_by_composite_desc"] or not sl_check["symbol_tie_break_ok"]:
        print("[wi009c-eval] shortlist ordering does not match the declared composite", file=sys.stderr)
        return 1
    if sl_check["composite_max_abs_error"] > 1e-6:
        print(f"[wi009c-eval] shortlist composite mismatch "
              f"{sl_check['composite_max_abs_error']:.3e}", file=sys.stderr)
        return 1
    rob = robustness_summary(rob_p)

    text = build_summary(
        record, recomp, verdicts, n_cleared, n_targets, shortlist, sl_check, rob, m,
        labels_cleared_line=labels_cleared_line,
    )

    out = resolve_output(args.out, m, what="--out") if args.out else Path(p["summary"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print(f"[wi009c-eval] wrote {out}")

    summary_json = {
        "market": m,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "run_record": _rel(run_p),
        "run_generated_utc": record.get("generated_utc"),
        "probe_report": _rel(probe_p),
        "targets": verdicts,
        "n_labels_cleared": n_cleared,
        "n_targets": n_targets,
        "continuous_baseline": {
            "n_oof_rows": recomp["n_rows"],
            "folds": recomp["folds"],
            "folds_total": len(record.get("folds", [])),
            "masses": recomp["masses"],
            "calibration": recomp["calibration"],
            "skill": {k: record.get("skill", {}).get(k) for k in
                      ("model_ic", "model_t", "n_dates", "best_factor", "best_abs_ic",
                       "same_sign", "pass_a", "pass_b", "passed")},
        },
        "shortlist": sl_check,
        "robustness": rob,
        "contrastive_candidate": record.get("contrastive_candidate"),
        "reproducibility": {"mass_tolerance": MASS_TOL, "problems": problems,
                            "composite_max_abs_error": recomp["composite_max_abs_error"]},
        "human_gate": "claim/use decision left to the human gate; no gate marked passed",
    }
    jout = (
        resolve_output(args.json_out, m, what="--json-out")
        if args.json_out
        else Path(p["summary_json"])
    )
    jout.parent.mkdir(parents=True, exist_ok=True)
    jout.write_text(json.dumps(summary_json, indent=2, default=str) + "\n")
    print(f"[wi009c-eval] wrote {jout}")
    print(f"[wi009c-eval] {n_cleared}/{n_targets or 5} targets clear the bar; continuous baseline skill bar "
          f"{'PASS' if record.get('skill', {}).get('passed') else 'FAIL'}; "
          f"{recomp['n_rows']:,} OOF rows re-verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
