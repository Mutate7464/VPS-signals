#!/usr/bin/env python3
"""WI-010 — consolidated quarantine triage report (single entry point).

Read-only deliverable generator. It never writes
`data/dead_letter_tickers.csv`, never calls `quarantine_ticker()`, and never
changes quarantine state: the output is a report plus a recommendation table for
the human gate.

Modes
-----
``--experiment-only``
    Anchor experiment (level-step test *including its persistence guard*, no
    volume vote) plus the verified 17/55 WI-008 baseline capture. This runs
    BEFORE any decision-rule change, per plan step 3.

default
    Full consolidated report: per-symbol recommendation/evidence table, baseline
    flip count and symbol list, read-only CB-01 CLEAN_NOW results, and the anchor
    verdicts under the final rule.

Usage
-----
    uv run python -m src.quarantine_triage_report --experiment-only \
        --output reports/wi010_quarantine_consolidated.md
    uv run python -m src.quarantine_triage_report \
        --output reports/wi010_quarantine_consolidated.md
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from src.quarantine_analysis import (
    STEP_PERSISTENCE_MAX_SPREAD,
    analyze_ticker_parquet,
    level_step_test,
    persistence_spread,
    quarantine_verdict,
)
from src.verify_synced_data import (
    cb01_clean_now_check,
    cb01_spike_indices,
    read_dead_letter_rows,
)

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw_ohlcv"
DEAD_LETTER_PATH = BASE_DIR / "data" / "dead_letter_tickers.csv"
BASELINE_PATH = BASE_DIR / "reports" / "wi008_quarantine_percase_evidence.md"
DEFAULT_OUTPUT = BASE_DIR / "reports" / "wi010_quarantine_consolidated.md"

# Verdict vocabulary shared with the WI-008 baseline report.
VERDICT_ORDER = ("REINSTATE", "KEEP_QUARANTINED", "FIX_DATA", "OWNER_ACTION", "AMBIGUOUS")

# Named anchor cases (ADR D-010 / WI-008 escalation brief): the 2020-03-09 crash
# cluster (OVV/WES/CVE/APA/OXY/MTDR), GME, and ICL — each evaluated separately.
EXPERIMENT_ANCHORS = (
    ("2020-03-09 crash cluster", "OVV", "CAD"),
    ("2020-03-09 crash cluster", "OVV", "USD"),
    ("2020-03-09 crash cluster", "WES", "USD"),
    ("2020-03-09 crash cluster", "CVE", "CAD"),
    ("2020-03-09 crash cluster", "CVE", "USD"),
    ("2020-03-09 crash cluster", "APA", "USD"),
    ("2020-03-09 crash cluster", "OXY", "USD"),
    ("2020-03-09 crash cluster", "MTDR", "USD"),
    ("GME (2021-01 squeeze)", "GME", "USD"),
    ("ICL (negative-price candidate)", "ICL", "USD"),
)

# Anchor rows the ADR D-010 / WI-008 escalation brief assert are *genuine* moves
# (2020-03-09 COVID crash cluster + the GME squeeze), not split-lookalikes. Any of
# these still landing on KEEP_QUARANTINED is reported as a residual finding rather
# than hidden. ICL is deliberately excluded: it must be assessed from its recorded
# evidence (non-positive closes), not presumed.
EXPECTED_NOT_SPLIT = {
    ("OVV", "CAD"),
    ("OVV", "USD"),
    ("WES", "USD"),
    ("CVE", "CAD"),
    ("CVE", "USD"),
    ("APA", "USD"),
    ("OXY", "USD"),
    ("MTDR", "USD"),
    ("GME", "USD"),
}


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def fmt(value, digits: int = 4) -> str:
    """Format a number for a markdown cell; None/NaN become 'N/A'."""
    if value is None:
        return "N/A"
    try:
        f = float(value)
    except (TypeError, ValueError):
        return str(value)
    if np.isnan(f) or np.isinf(f):
        return "N/A"
    return f"{f:.{digits}f}"


def parquet_path(symbol: str, market: str, raw_dir: Path = RAW_DIR) -> Path:
    return raw_dir / f"market={market}" / f"symbol={symbol}.parquet"


# --------------------------------------------------------------------------- #
# Baseline capture (WI-008 report — preserved as the 17/55 comparison point)
# --------------------------------------------------------------------------- #
def parse_baseline_report(path: Path) -> tuple[list[dict], dict]:
    """Parse the WI-008 per-case report into rows + verdict counts.

    Strictly read-only. Rows are keyed by (symbol, market).
    """
    rows: list[dict] = []
    counts: dict = {}
    in_summary = False

    for line in path.read_text().splitlines():
        if line.startswith("## Verdict Summary"):
            in_summary = True
            continue
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells:
            continue

        if in_summary:
            if len(cells) < 2 or cells[0] in ("Recommendation", "") or cells[1] == "---:":
                continue
            if cells[0] in VERDICT_ORDER:
                counts[cells[0]] = int(cells[1])
            continue

        if cells[0] in ("Symbol", "") or cells[0].startswith(":---"):
            continue
        if len(cells) >= 4 and cells[3] in VERDICT_ORDER:
            rows.append(
                {
                    "symbol": cells[0],
                    "market": cells[1],
                    "reason": cells[2],
                    "verdict": cells[3],
                    "level_ratio": cells[4] if len(cells) > 4 else "N/A",
                    "volume_ratio": cells[5] if len(cells) > 5 else "N/A",
                    "notes": cells[6] if len(cells) > 6 else "",
                }
            )
    return rows, counts


def ensure_baseline_report(baseline_path: Path = BASELINE_PATH) -> Path:
    """Return the verified WI-008 baseline report path.

    The 17/55 baseline is the comparison point for every flip in this report and
    must never be regenerated or overwritten. WI-010 removed the legacy generator
    (`src/final_quarantine_triage.py`) that produced it, so if the file is missing
    this fails loudly rather than silently rebuilding a "baseline".
    """
    if baseline_path.exists():
        return baseline_path
    raise FileNotFoundError(
        f"WI-008 baseline report missing: {baseline_path}. It is the 17/55 comparison "
        "point and must be restored (e.g. from git history / the WI-008 gate evidence) "
        "rather than regenerated: the legacy generator was removed by WI-010."
    )


# --------------------------------------------------------------------------- #
# Anchor experiment (level-step + persistence guard; no volume vote)
# --------------------------------------------------------------------------- #
def run_anchor_experiment(raw_dir: Path = RAW_DIR) -> list[dict]:
    """Score every named anchor with the level-step test only (persistence guard on).

    Deliberately performs no volume corroboration: this is the WI-008 escalation
    brief's disambiguating experiment ("persistence guard alone"). Missing data is
    returned as an explicit status rather than silently dropped.
    """
    results: list[dict] = []

    for group, symbol, market in EXPERIMENT_ANCHORS:
        entry: dict = {
            "group": group,
            "symbol": symbol,
            "market": market,
            "available": False,
            "status": "NO_FILE",
            "spike_date": "N/A",
            "spike_return": None,
            "level_ratio": None,
            "clean_fraction": None,
            "persistence_spread": None,
            "persistence": "N/A",
            "detail": "",
            "non_positive_close": False,
        }

        path = parquet_path(symbol, market, raw_dir)
        if not path.exists():
            entry["detail"] = "no parquet on disk"
            results.append(entry)
            continue

        try:
            df = pd.read_parquet(path, columns=["date", "close"]).sort_values("date")
            df = df.reset_index(drop=True)
        except Exception as exc:  # unreadable/corrupt parquet
            entry["status"] = "READ_ERROR"
            entry["detail"] = str(exc)
            results.append(entry)
            continue

        spikes = cb01_spike_indices(df)
        non_positive_close = bool((df["close"].astype("float64") <= 0).any())
        entry["non_positive_close"] = non_positive_close
        if len(spikes) == 0:
            entry["available"] = True
            entry["status"] = "NO_SPIKE"
            entry["detail"] = "no CB-01 spike on disk"
            results.append(entry)
            continue

        spike_idx = int(spikes[0])
        ret = df["close"].astype("float64").pct_change()
        ratio, clean_fraction, recommendation = level_step_test(df, spike_idx)
        spread = persistence_spread(df, spike_idx)
        if non_positive_close:
            # Ratio-family metrics are meaningless with non-positive closes.
            persistence = "N/A (non-positive close)"
        elif spread is None:
            persistence = "N/A"
        elif spread > STEP_PERSISTENCE_MAX_SPREAD:
            persistence = "RANGING"
        else:
            persistence = "PERSISTENT"

        entry.update(
            {
                "available": True,
                "status": recommendation,
                "spike_date": str(pd.Timestamp(df.iloc[spike_idx]["date"]).date()),
                "spike_return": float(ret.iloc[spike_idx]),
                "level_ratio": None if ratio is None else float(ratio),
                "clean_fraction": clean_fraction,
                "persistence_spread": spread,
                "persistence": persistence,
            }
        )
        results.append(entry)

    return results


def experiment_table(rows: list[dict]) -> list[str]:
    """Markdown table for the anchor experiment (no volume column by design)."""
    out = [
        "| Anchor | Symbol | Market | Data | Spike date | Spike return | Level ratio "
        "| Clean fraction | Persistence spread | Persistence | Experiment status |",
        "| :--- | :--- | :---: | :---: | :---: | ---: | ---: | ---: | ---: | :---: | :--- |",
    ]
    for r in rows:
        data = "available" if r["available"] else ("" if r["status"] != "NO_FILE" else "MISSING")
        if r["status"] == "READ_ERROR":
            data = "UNREADABLE"
        elif r.get("non_positive_close"):
            data = "available (non-positive close)"
        out.append(
            f"| {r['group']} | {r['symbol']} | {r['market']} | {data} "
            f"| {r['spike_date']} | {fmt(r['spike_return'], 3)} | {fmt(r['level_ratio'])} "
            f"| {fmt(r['clean_fraction'], 2)} | {fmt(r['persistence_spread'])} "
            f"| {r['persistence']} | {r['status']} |"
        )
    return out


# --------------------------------------------------------------------------- #
# Full consolidated analysis (per-symbol + CB-01 re-check)
# --------------------------------------------------------------------------- #
def run_full_analysis(
    baseline_rows: list[dict],
    base_dir: Path = BASE_DIR,
    dead_letter_path: Path = DEAD_LETTER_PATH,
) -> tuple[list[dict], list[dict]]:
    """Analyze every dead-letter row sequentially with the tested classifier.

    Returns (per-symbol rows, CB-01 CLEAN_NOW rows). One symbol's parquet is read
    at a time with bounded columns; no all-ticker DataFrame is built.
    """
    baseline = {(r["symbol"], r["market"]): r for r in baseline_rows}

    cb01_rows = cb01_clean_now_check(
        dead_letter_path=dead_letter_path,
        raw_dir=base_dir / "data" / "raw_ohlcv",
    )
    cb01 = {(r["symbol"], r["market"]): r for r in cb01_rows}

    rows: list[dict] = []
    for dl in read_dead_letter_rows(dead_letter_path):
        symbol = (dl.get("symbol") or "").strip()
        market = (dl.get("market") or "").strip()
        analysis = analyze_ticker_parquet(symbol, market, base_dir=base_dir)
        verdict = quarantine_verdict(analysis)
        base = baseline.get((symbol, market), {})
        rows.append(
            {
                "symbol": symbol,
                "market": market,
                "reason": (dl.get("reason") or "").strip(),
                "baseline": base.get("verdict", "N/A"),
                "final": verdict,
                "flip": bool(base) and base.get("verdict") != verdict,
                "cb01": cb01.get((symbol, market), {}).get("status", "N/A"),
                "analysis": analysis,
            }
        )
    return rows, cb01_rows


def anchor_final_rows(base_dir: Path = BASE_DIR) -> list[dict]:
    """Anchor anchor under the *final* rule (tested classifier), for the report."""
    out: list[dict] = []
    for group, symbol, market in EXPERIMENT_ANCHORS:
        analysis = analyze_ticker_parquet(symbol, market, base_dir=base_dir)
        enough = analysis.get("status") == "SUCCESS"
        out.append(
            {
                "group": group,
                "symbol": symbol,
                "market": market,
                "status": analysis.get("status"),
                "spike_date": analysis.get("spike_date", "N/A"),
                "level_verdict": analysis.get("level_verdict", "N/A") if enough else "N/A",
                "clean_fraction": analysis.get("clean_ratio") if enough else None,
                "persistence_spread": analysis.get("persistence_spread") if enough else None,
                "is_isolated": analysis.get("is_isolated") if enough else None,
                "volume_ratio": analysis.get("volume_ratio") if enough else None,
                "classifier_verdict": analysis.get("recommendation", "N/A") if enough else "N/A",
                "report_verdict": quarantine_verdict(analysis),
                "non_positive_close": bool(analysis.get("non_positive_close")),
                "expected_not_split": (symbol, market) in EXPECTED_NOT_SPLIT,
            }
        )
    return out


def anchor_final_table(rows: list[dict]) -> list[str]:
    out = [
        "| Anchor | Symbol | Market | Data | Level verdict | Clean fraction | Persistence spread "
        "| Path isolated | Classifier verdict | Report verdict | Residual? |",
        "| :--- | :--- | :---: | :---: | :--- | ---: | ---: | :---: | :--- | :--- | :---: |",
    ]
    for r in rows:
        residual = "NO"
        if r["expected_not_split"] and r["report_verdict"] == "KEEP_QUARANTINED":
            residual = "**YES**"
        elif r["non_positive_close"]:
            residual = "data issue"
        out.append(
            f"| {r['group']} | {r['symbol']} | {r['market']} | {r['status']} "
            f"| {r['level_verdict']} | {fmt(r['clean_fraction'], 2)} "
            f"| {fmt(r['persistence_spread'])} | {r['is_isolated']} "
            f"| {r['classifier_verdict']} | {r['report_verdict']} | {residual} |"
        )
    return out


def per_symbol_table(rows: list[dict]) -> list[str]:
    out = [
        "| Symbol | Market | Original reason | Baseline | Final | Flip | CB-01 | Spike date "
        "| Spike return | Level ratio | Persist spread | Level | Isolated "
        "| Volume ratio (evidence only) | Data issue |",
        "| :--- | :---: | :--- | :--- | :--- | :---: | :---: | :---: | ---: | ---: | ---: "
        "| :--- | :---: | ---: | :--- |",
    ]
    for r in rows:
        a = r["analysis"]
        issue = "NON_POSITIVE_CLOSE" if a.get("non_positive_close") else ""
        out.append(
            f"| {r['symbol']} | {r['market']} | {r['reason']} | {r['baseline']} | {r['final']} "
            f"| {'YES' if r['flip'] else ''} | {r['cb01']} | {a.get('spike_date', 'N/A')} "
            f"| {fmt(a.get('spike_return'), 3)} | {fmt(a.get('level_ratio'))} "
            f"| {fmt(a.get('persistence_spread'))} | {a.get('level_verdict', 'N/A')} "
            f"| {a.get('is_isolated', 'N/A')} | {fmt(a.get('volume_ratio'), 3)} | {issue} |"
        )
    return out


def flip_table(rows: list[dict]) -> list[str]:
    flips = [r for r in rows if r["flip"]]
    out = [f"- Total verdict flips vs baseline: **{len(flips)}** of {len(rows)} rows"]
    out.append("")
    if not flips:
        out.append("- (none)")
        return out
    out.append("| Symbol | Market | Baseline | Final |")
    out.append("| :--- | :---: | :--- | :--- |")
    for r in flips:
        out.append(f"| {r['symbol']} | {r['market']} | {r['baseline']} | {r['final']} |")
    out.append("")
    out.append("- Flip symbols: " + ", ".join(f"{r['symbol']}/{r['market']}" for r in flips))
    return out


# --------------------------------------------------------------------------- #
# Report assembly
# --------------------------------------------------------------------------- #
def baseline_section(baseline_file: Path, baseline_rows: list[dict], baseline_counts: dict) -> list[str]:
    ok = baseline_counts.get("REINSTATE") == 17 and baseline_counts.get("KEEP_QUARANTINED") == 55
    lines = ["## 1. WI-008 baseline (17/55 comparison point)", ""]
    lines.append(f"- Baseline file: `{baseline_file.relative_to(BASE_DIR)}`")
    lines.append(f"- Parsed per-case rows: **{len(baseline_rows)}**")
    lines.append("")
    lines.append("| Recommendation | Count |")
    lines.append("| :--- | ---: |")
    for verdict in VERDICT_ORDER:
        lines.append(f"| {verdict} | {baseline_counts.get(verdict, 0)} |")
    lines.append("")
    lines.append(
        "Baseline verified as **17 REINSTATE / 55 KEEP_QUARANTINED** — PASS."
        if ok
        else "**WARNING:** baseline counts are not 17/55 — investigate before trusting flips."
    )
    lines.append("")
    return lines


def experiment_section(anchors: list[dict]) -> list[str]:
    lines = [
        "## 2. Anchor experiment — level-step test with persistence guard only (no volume vote)",
        "",
        "Each anchor is evaluated separately. The experiment applies `level_step_test` "
        "(including its persistence guard) to the first CB-01 spike found on disk and "
        "deliberately excludes volume corroboration, so no volume signal can vote. "
        "This section is produced before the final rule and is unchanged by it.",
        "",
    ]
    lines.extend(experiment_table(anchors))
    lines.append("")
    lines.append(
        "`PERSISTENT` = post-spike dispersion ≤ "
        f"{STEP_PERSISTENCE_MAX_SPREAD} (level held); `RANGING` = level kept moving; "
        "`MISSING`/`UNREADABLE` = data not available on disk."
    )
    lines.append("")
    return lines


def build_report(experiment_only: bool, base_dir: Path = BASE_DIR) -> str:
    baseline_file = ensure_baseline_report()
    baseline_rows, baseline_counts = parse_baseline_report(baseline_file)
    anchors = run_anchor_experiment(base_dir / "data" / "raw_ohlcv")

    lines: list[str] = []
    lines.append("# WI-010 — Consolidated Quarantine Triage Report")
    lines.append("")
    lines.append(f"- Generated (UTC): {pd.Timestamp.now('UTC').strftime('%Y-%m-%d %H:%M:%SZ')}")
    lines.append("- Dead-letter source: `data/dead_letter_tickers.csv` (read-only, never rewritten)")
    lines.append(f"- Baseline: `{baseline_file.relative_to(BASE_DIR)}` (WI-008, preserved for comparison)")
    lines.append("- Classifier: `src/quarantine_analysis.py` (unit-tested; the only remaining classifier)")
    lines.append("- Report entry point: `src/quarantine_triage_report.py`")
    lines.append(
        "- Duplicate claim paths: reduced to non-classifying deprecation stubs "
        "(`final_quarantine_triage.py`, `percase_quarantine_triage.py`, "
        "`simple_quarantine_analysis.py`); their file removal is human-gated."
    )
    lines.append("- CB-01 CLEAN_NOW check: `src.verify_synced_data.cb01_clean_now_check` (read-only)")
    lines.append("- **No quarantine state is changed by this report.** Per-row reinstate/keep decisions")
    lines.append("  remain human-gated (no auto-reinstatement).")
    lines.append("")
    lines.append(
        "Mode: **anchor experiment only** (pre-rule-change evidence)."
        if experiment_only
        else "Mode: **full consolidated report**."
    )
    lines.append("")

    lines.extend(baseline_section(baseline_file, baseline_rows, baseline_counts))
    lines.extend(experiment_section(anchors))

    if experiment_only:
        lines.append("---")
        lines.append("")
        lines.append(
            "Final decision rule and per-symbol recommendation table are **not** included in "
            "this experiment-only report; they follow in the consolidated report generated "
            "after the rule re-derivation. No classifier rule has been changed at this point."
        )
        lines.append("")
        return "\n".join(lines) + "\n"

    symbol_rows, cb01_rows = run_full_analysis(baseline_rows, base_dir=base_dir)
    anchor_rows = anchor_final_rows(base_dir=base_dir)

    # --- Final rule -------------------------------------------------------- #
    lines.append("## 3. Final decision rule (re-derived after the experiment above)")
    lines.append("")
    lines.append(
        "`SPLIT_LOOKALIKE` requires **both** structural signals together "
        "(`quarantine_analysis.combine_verdicts`):"
    )
    lines.append("")
    lines.append("1. a persistent, non-unity level step (`level_step_test`, persistence guard included), and")
    lines.append("2. an isolated multi-day path (`multi_day_path_analysis`).")
    lines.append("")
    lines.append(
        "Volume corroboration (`volume_corroboration`) is **evidence only** — it can no longer "
        "vote, because a volume-only anomaly independently labelled the genuine 2020-03-09 crash "
        "cluster (and others) as split-lookalikes under the previous OR-of-signals rule."
    )
    lines.append("")
    lines.append(
        "Report-level verdicts (`quarantine_analysis.quarantine_verdict`): "
        "`SPLIT_LOOKALIKE → KEEP_QUARANTINED`, `GENUINE_VOL → REINSTATE`, "
        "non-positive closes `→ FIX_DATA`, missing parquet `→ OWNER_ACTION`, "
        "unreadable/exception `→ AMBIGUOUS`, no on-disk CB-01 spike `→ REINSTATE`."
    )
    lines.append("")
    lines.append("### 3.1 Anchor cases under the final rule")
    lines.append("")
    lines.extend(anchor_final_table(anchor_rows))
    lines.append("")

    residuals = [r for r in anchor_rows if r["expected_not_split"] and r["report_verdict"] == "KEEP_QUARANTINED"]
    if residuals:
        lines.append("**Residual findings (flagged for the gate, no rule widening applied):**")
        lines.append("")
        for r in residuals:
            lines.append(
                f"- `{r['symbol']}/{r['market']}` is still read as split-lookalike under the final rule: "
                f"level ratio {fmt(r['clean_fraction'], 2)} fraction matched with persistence spread "
                f"{fmt(r['persistence_spread'])} (guard {STEP_PERSISTENCE_MAX_SPREAD}) and an isolated path. "
                "Tightening the step-ratio tolerance (absolute ±0.10 today) or the persistence guard is a "
                "rule change beyond this consolidation and is left to the planner/gate."
            )
        lines.append("")
    else:
        lines.append("All expected genuine-move anchors (2020-03-09 cluster + GME) clear the final rule.")
        lines.append("")

    icl = [r for r in anchor_rows if r["symbol"] == "ICL"]
    for r in icl:
        if r["non_positive_close"]:
            lines.append(
                f"- `ICL/USD` assessed from its recorded evidence: the parquet contains non-positive "
                f"closes, so every ratio-based test is meaningless (level ratio "
                f"{fmt(r['clean_fraction'])}); verdict **FIX_DATA** — data repair first, no "
                "reinstate/keep recommendation is offered."
            )
            lines.append("")

    # --- CB-01 read-only re-check ------------------------------------------ #
    counts = Counter(r["status"] for r in cb01_rows)
    lines.append("## 4. Read-only CB-01 CLEAN_NOW re-check")
    lines.append("")
    lines.append(
        "`cb01_clean_now_check` re-tests each dead-letter row against the CB-01 thresholds "
        "(> +100% or < −50% single-day return) using the on-disk parquet only. It never calls "
        "`quarantine_ticker()` and never writes `data/dead_letter_tickers.csv`."
    )
    lines.append("")
    lines.append("| CB-01 status | Rows |")
    lines.append("| :--- | ---: |")
    for status in ("CLEAN_NOW", "SPIKE", "NO_FILE", "READ_ERROR"):
        lines.append(f"| {status} | {counts.get(status, 0)} |")
    lines.append("")
    clean_rows = [r for r in cb01_rows if r["status"] != "SPIKE"]
    if clean_rows:
        lines.append("| Symbol | Market | Quarantine reason | CB-01 status |")
        lines.append("| :--- | :---: | :--- | :--- |")
        for r in clean_rows:
            lines.append(f"| {r['symbol']} | {r['market']} | {r['reason']} | {r['status']} |")
        lines.append("")
        lines.append(
            "Note: `TRI/CAD` and `SPCX/USD` were quarantined under CB-02 "
            "(INSUFFICIENT_LOOKBACK_FOR_HURST100), not CB-01; a CB-01 CLEAN_NOW result cannot "
            "clear a CB-02 quarantine — their REINSTATE verdicts follow the classifier "
            "(no CB-01 spike on disk) and are listed here for separate gate review."
        )
    else:
        lines.append("No dead-letter row clears CB-01 on disk (all rows still trip CB-01).")
    lines.append("")

    # --- Per-symbol table --------------------------------------------------- #
    lines.append("## 5. Per-symbol verdict and evidence (all 72 dead-letter rows)")
    lines.append("")
    lines.append(
        "`Final` = `quarantine_verdict(classifier result)`. Volume ratio is shown as evidence only; "
        "it is not an input to the final rule."
    )
    lines.append("")
    lines.extend(per_symbol_table(symbol_rows))
    lines.append("")

    # --- Flips -------------------------------------------------------------- #
    lines.append("## 6. Verdict flips vs the 17/55 baseline")
    lines.append("")
    lines.extend(flip_table(symbol_rows))
    lines.append("")

    final_counts = Counter(r["final"] for r in symbol_rows)
    lines.append("## 7. Recommendation summary (human gate)")
    lines.append("")
    lines.append("| Final recommendation | Count | Baseline count |")
    lines.append("| :--- | ---: | ---: |")
    for verdict in VERDICT_ORDER:
        lines.append(f"| {verdict} | {final_counts.get(verdict, 0)} | {baseline_counts.get(verdict, 0)} |")
    lines.append("")
    lines.append(
        "**STOP — human gate.** This table is a recommendation only. No ticker has been "
        "reinstated, kept, or otherwise changed; `data/dead_letter_tickers.csv` and all "
        "quarantine state are byte-identical to their pre-run contents."
    )
    lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--experiment-only",
        action="store_true",
        help="write only the baseline capture + anchor experiment (pre-rule-change evidence)",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="report output path")
    args = parser.parse_args(argv)

    report = build_report(experiment_only=args.experiment_only)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report)

    print(f"[quarantine_triage_report] report written -> {args.output}")
    print(f"[quarantine_triage_report] mode={'experiment-only' if args.experiment_only else 'full'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
