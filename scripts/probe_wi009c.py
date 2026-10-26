#!/usr/bin/env python3
"""WI-009c Step 1 — cheap five-factor logistic probe (CAD by default).

Bounds whether the *existing binary labels* are learnable before any feature
spend. For each of the five E5 factors (`mom_12_1`, `rev_1m`, `vol_20`,
`amihud_20`, `log_dollar_vol_20`) a standardised logistic regression is fit on
**those five factors only**, with purged chronological walk-forward CV
(`PurgedWalkForwardSplit(n_splits=5, embargo_td=20)`, positional date mapping
from `src.factors.e5_baseline.date_positions` — never `pd.factorize` codes).
The out-of-fold *probabilities* are scored with the same score-based
within-date rank-IC used everywhere else (`src.models.pair_sampler.
within_date_rank_ic`) and compared, on exactly the same rows and dates, with
each single factor's IC under the unchanged WI-009b skill-bar criteria
(`src.models.skill_bar`), plus the admin-adopted same-sign clause:

    clause (a): same sign as the best factor AND |IC| >= best factor |IC|
    clause (b): |t| > 2 with the same IC sign in >= 2 disjoint sub-windows

Metric mapping (documented Build assumption — the plan fixes the *bar*, not the
per-label reference): class-label IC is never used (WI-002 lesson), so each
binary label is scored against the aligned continuous forward move with its
established direction sign from `src.xgb_trainer.TARGET_DIRECTION`:

    y_20d_up    -> +fwd_atr_ret_20      y_20d_down -> -fwd_atr_ret_20
    y_15d_low   -> +fwd_atr_ret_15      y_15d_high -> -fwd_atr_ret_15
    y_20d_stay  -> -|fwd_atr_ret_20|    (stay ~ small |move|; magnitude ref)

Writes `reports/wi009c_probe_{market}.md` (WI-013: market-suffixed, never the
frozen unsuffixed gate report). No 89-feature model, no robustness variant.

CLI (WI-013: omitted `--market` runs BOTH, USD then CAD)::

    uv run python scripts/probe_wi009c.py                  # both markets
    uv run python scripts/probe_wi009c.py --market CAD     # one market
    uv run python scripts/probe_wi009c.py --market CAD --max-dates 400   # smoke
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import average_precision_score  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from src.factors.e5_baseline import E5_FACTORS, build_e5_panel, date_positions  # noqa: E402
from src.market_cli import (  # noqa: E402
    add_market_argument,
    cli_markets,
    report_path,
    resolve_output,
    run_markets,
)
from src.models.skill_bar import (  # noqa: E402
    EMBARGO_TD,
    factor_ics_from_panel,
    skill_bar_verdict,
    stats_for_rows,
    sub_window_split,
)
from src.targets import TARGET_COLUMNS  # noqa: E402
from src.xgb_trainer import PurgedWalkForwardSplit  # noqa: E402

REPORTS = ROOT / "reports"
FEATURES_DIR = ROOT / "data" / "features"
E5_COLS = [f"e5_{f}" for f in E5_FACTORS]
REPORT_STEM = "wi009c_probe"


def paths(market: str) -> dict[str, Path]:
    """Every input/output path this script resolves for one market (WI-013)."""
    return {
        "report": report_path(REPORTS, REPORT_STEM, market),
        "targets": FEATURES_DIR / f"targets_{market}.parquet",
    }

# Per-label continuous reference (see module docstring). 0 = magnitude reference.
TARGET_HORIZON = {
    "y_15d_high": 15,
    "y_15d_low": 15,
    "y_20d_up": 20,
    "y_20d_down": 20,
    "y_20d_stay": 20,
}
TARGET_SIGN = {"y_15d_high": -1, "y_15d_low": 1, "y_20d_up": 1, "y_20d_down": -1, "y_20d_stay": 0}


def _finite(x) -> bool:
    return x is not None and bool(np.isfinite(x))


def _fmt(x, fmt="+.4f"):
    return f"{x:{fmt}}" if _finite(x) else "n/a"


def build_probe_panel(market: str, max_dates: int = 0) -> pd.DataFrame:
    """E5 factors + forward moves (from raw, via the WI-009b harness) joined to targets.

    Streams raw OHLCV through `build_e5_panel` (never an all-ticker uncompressed
    frame) and joins `targets_{MKT}.parquet` on (date, symbol). Factor columns
    are float32 throughout.
    """
    e5 = build_e5_panel(market)
    # `amihud_20` also exists in the 89-feature matrix; namespace to avoid a
    # silent merge suffix (the WI-009b lesson).
    e5 = e5.rename(columns={f: f"e5_{f}" for f in E5_FACTORS})
    t = pd.read_parquet(FEATURES_DIR / f"targets_{market}.parquet")[["date", "symbol"] + list(TARGET_COLUMNS)]
    panel = e5.merge(t, on=["date", "symbol"], how="inner")
    panel = panel.dropna(subset=E5_COLS).sort_values(["date", "symbol"], kind="stable").reset_index(drop=True)
    if max_dates > 0:
        keep = np.sort(pd.unique(panel["date"].to_numpy()))[-max_dates:]
        panel = panel[panel["date"].isin(set(keep))].reset_index(drop=True)
    return panel


def reference_for(panel: pd.DataFrame, target: str) -> tuple[np.ndarray, str]:
    """Continuous reference values + human-readable description for one label."""
    col = f"fwd_atr_ret_{TARGET_HORIZON[target]}"
    sign = TARGET_SIGN[target]
    if sign == 0:
        return -np.abs(panel[col].to_numpy(dtype="float64")), f"-|{col}| (stay ≈ small |move|)"
    return sign * panel[col].to_numpy(dtype="float64"), f"{sign:+d} × {col}"


def cv_logit(
    panel: pd.DataFrame,
    target: str,
    n_splits: int,
    embargo_td: int,
) -> tuple[np.ndarray, list[dict]]:
    """Out-of-fold logistic probabilities on the five E5 factors + fold evidence.

    Returns:
        (oof probabilities, fold records). Split keys are *positions* into the
        sorted unique dates (`date_positions`), never factorize codes.
    """
    dates = panel["date"].to_numpy()
    uniq = np.sort(pd.unique(dates))
    pos = date_positions(dates)
    y = panel[target].to_numpy(dtype="int8")
    x = panel[E5_COLS].to_numpy(dtype="float32")

    splitter = PurgedWalkForwardSplit(n_splits=n_splits, embargo_td=embargo_td)
    oof = np.full(len(panel), np.nan, dtype="float64")
    folds: list[dict] = []
    for k, (tr, va) in enumerate(splitter.split(uniq)):
        tr_rows = np.isin(pos, tr)
        va_rows = np.isin(pos, va)
        if not tr_rows.any() or not va_rows.any():
            continue
        rec = {
            "fold": k,
            "n_train_rows": int(tr_rows.sum()),
            "n_val_rows": int(va_rows.sum()),
            "n_train_dates": int(len(tr)),
            "n_val_dates": int(len(va)),
            "train_max_date": str(pd.Timestamp(uniq[tr.max()]).date()),
            "val_min_date": str(pd.Timestamp(uniq[va.min()]).date()),
            "gap_positions": int(va.min() - tr.max() - 1),
            "purge_ok": bool(tr.max() + embargo_td < va.min()),
            "train_pos_rate": float(y[tr_rows].mean()),
        }
        if y[tr_rows].min() == y[tr_rows].max():
            rec["skipped"] = "single-class training fold"
            folds.append(rec)
            continue
        model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500, C=0.1))
        model.fit(x[tr_rows], y[tr_rows])
        oof[va_rows] = model.predict_proba(x[va_rows])[:, 1]
        folds.append(rec)
    return oof, folds


def label_metrics(
    panel: pd.DataFrame,
    target: str,
    oof: np.ndarray,
    n_splits: int,
) -> dict:
    """Same-rows IC comparison of the OOF probability vs the best single factor."""
    ref, ref_desc = reference_for(panel, target)
    dates = panel["date"].to_numpy()
    mask = np.isfinite(oof) & np.isfinite(ref)
    scored = panel.loc[mask, E5_COLS].copy()
    scored["date"] = dates[mask]
    scored["score"] = oof[mask]
    scored["ref"] = ref[mask]

    model_ic, model_t, n_dates = stats_for_rows(scored, "score", "ref")
    factor_stats = factor_ics_from_panel(scored, E5_FACTORS, "e5_", "ref")
    blocks = sub_window_split(pd.unique(scored["date"].to_numpy()), n_windows=2)
    sub_stats = [
        stats_for_rows(scored[scored["date"].isin(set(b))], "score", "ref") for b in blocks
    ]
    verdict = skill_bar_verdict(model_ic, model_t, factor_stats, sub_stats)

    best_name = verdict["clause_a"]["best_factor"]
    best_ic = factor_stats[best_name][0]
    best_abs = float(abs(best_ic))
    same_sign = _finite(model_ic) and _finite(best_ic) and np.sign(model_ic) == np.sign(best_ic)
    # Admin-adopted clause (a): same sign AND |IC| >=. `skill_bar_verdict` is
    # reused unchanged; it implements the strict-|IC| magnitude test, so the
    # >= tie-break is applied here on top rather than by editing the module.
    pass_a = bool(same_sign and _finite(model_ic) and abs(model_ic) >= best_abs)
    pass_b = bool(verdict["clause_b"]["passed"])
    y = panel[target].to_numpy(dtype="int8")[mask]
    pr_auc = (
        float(average_precision_score(y, oof[mask]))
        if len(np.unique(y)) > 1
        else float("nan")
    )
    return {
        "target": target,
        "ref_desc": ref_desc,
        "n_rows": int(mask.sum()),
        "n_dates": int(n_dates),
        "scored_dates": blocks,
        "model_ic": model_ic,
        "model_t": model_t,
        "factor_stats": factor_stats,
        "verdict": verdict,
        "best_factor": best_name,
        "best_abs_ic": best_abs,
        "same_sign": bool(same_sign),
        "pass_a": pass_a,
        "pass_b": pass_b,
        "passed": bool(pass_a and pass_b),
        "pr_auc": pr_auc,
        "base_rate": float(y.mean()) if len(y) else float("nan"),
        "n_splits": n_splits,
    }


def write_report(
    market: str, panel: pd.DataFrame, metrics: list[dict], elapsed_s: float, folds: dict,
    out_path: Path | None = None,
) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = Path(out_path) if out_path is not None else paths(market)["report"]
    out.parent.mkdir(parents=True, exist_ok=True)
    n_pass = sum(1 for m in metrics if m["passed"])

    lines = [
        f"# WI-009c Step 1 — cheap five-factor logistic probe ({market})",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Panel: {len(panel):,} rows · {panel['symbol'].nunique()} symbols · "
        f"{panel['date'].nunique()} dates ({panel['date'].min().date()} → {panel['date'].max().date()})",
        f"- Features: the five E5 factors only ({', '.join('`' + c + '`' for c in E5_COLS)}) — "
        "no 89-feature model, no robustness variant.",
        "- E5 factors are computed from raw OHLCV by `src.factors.e5_baseline.build_e5_panel` "
        "(the WI-009b harness) and joined to `targets_" + market + ".parquet` on (date, symbol). "
        "Features and targets are not rebuilt.",
        f"- CV: `PurgedWalkForwardSplit(n_splits={metrics[0]['n_splits']}, embargo_td={EMBARGO_TD})`, "
        "chronological expanding folds over unique dates, keyed by *positions* "
        "(`src.factors.e5_baseline.date_positions`) — never `pd.factorize` codes (the WI-009 leak). "
        f"Score-based within-date Spearman rank-IC only; class-label IC is never used. Wall clock {elapsed_s:.1f}s.",
        "",
        "## Metric mapping (documented Build assumption)",
        "",
        "Each binary label is scored against the aligned continuous forward move with its established "
        "direction sign (`src.xgb_trainer.TARGET_DIRECTION`); `y_20d_stay` uses the magnitude reference "
        "`-|fwd_atr_ret_20|` (stay ≈ small |move|). The same reference is used for the logistic "
        "probability and for every factor, on identical rows and dates.",
        "",
        "| Target | continuous reference |",
        "| :--- | :--- |",
    ]
    for m in metrics:
        lines.append(f"| `{m['target']}` | `{m['ref_desc']}` |")

    lines += [
        "",
        "## Verdict summary (skill bar: clause a = same-sign AND |IC| >=, clause b = |t|>2 with stable sub-window sign)",
        "",
        "| Target | OOF logit IC | t | same sign | clause (a) | clause (b) | skill bar |",
        "| :--- | ---: | ---: | :--- | :--- | :--- | :--- |",
    ]
    for m in metrics:
        lines.append(
            f"| `{m['target']}` | {_fmt(m['model_ic'])} | {_fmt(m['model_t'], '+.2f')} | "
            f"{'yes' if m['same_sign'] else 'NO'} | "
            f"{'PASS' if m['pass_a'] else 'FAIL'} | {'PASS' if m['pass_b'] else 'FAIL'} | "
            f"**{'PASS' if m['passed'] else 'NEGATIVE RESULT'}** |"
        )
    lines += [
        "",
        f"- {n_pass}/5 targets clear the unchanged skill bar"
        + (f" ({', '.join('`' + m['target'] + '`' for m in metrics if m['passed'])})" if n_pass else ""),
        f"- **Step 2 gate:** {'permission for one 89-feature continuous run (permission, not a claim of skill)' if n_pass else 'no label demonstrated learnable — no 89-feature spend; limit the continuous baseline to the same five factors'}.",
        "",
    ]

    for m in metrics:
        lines += [
            f"## `{m['target']}`",
            "",
            f"- Reference: `{m['ref_desc']}` · scored rows {m['n_rows']:,} · scored dates {m['n_dates']} "
            f"· class base rate {m['base_rate'] * 100:.2f}%",
            f"- OOF logistic: IC {_fmt(m['model_ic'])} (t {_fmt(m['model_t'], '+.2f')}), "
            f"PR-AUC {_fmt(m['pr_auc'])} (descriptive only — the skill metric is the score-based IC).",
            f"- Skill bar: clause (a) {'PASS' if m['pass_a'] else 'FAIL'} "
            f"(same sign as best factor: {m['same_sign']}; logit |IC| {_fmt(abs(m['model_ic']))} vs "
            f"`{m['best_factor']}` |IC| {_fmt(m['best_abs_ic'])}) · "
            f"clause (b) {'PASS' if m['pass_b'] else 'FAIL'} "
            f"(sub-windows same sign: {m['verdict']['clause_b']['all_windows_same_sign']}, "
            f"|t|>2 in all: {m['verdict']['clause_b']['all_windows_abs_t_gt_2']}) · "
            f"**{'PASS' if m['passed'] else 'negative result'}**.",
            "",
            "| Score | mean IC | \\|IC\\| | t | dates |",
            "| :--- | ---: | ---: | ---: | ---: |",
            f"| **OOF logit (5 E5 factors)** | {_fmt(m['model_ic'])} | {_fmt(abs(m['model_ic']) if _finite(m['model_ic']) else float('nan'))} | "
            f"{_fmt(m['model_t'], '+.2f')} | {m['n_dates']} |",
        ]
        for fac, (ic, t, n) in sorted(m["factor_stats"].items(), key=lambda kv: -abs(kv[1][0])):
            lines.append(f"| `e5_{fac}` (factor) | {_fmt(ic)} | {abs(ic):.4f} | {_fmt(t, '+.2f')} | {n} |")
        subs = m["verdict"]["clause_b"]["sub_windows"]
        lines += [
            "",
            f"Sub-window stability (purged OOF rows only; {len(subs)} disjoint contiguous blocks):",
            "",
            "| Sub-window | dates | logit mean IC | t | sign matches full window |",
            "| :--- | ---: | ---: | ---: | :--- |",
        ]
        for w in subs:
            lines.append(
                f"| {w['window']} | {w['n_dates']} | {_fmt(w['ic'])} | {_fmt(w['t'], '+.2f')} | "
                f"{w['sign_matches_model']} |"
            )
        caveats = m["verdict"].get("caveats") or []
        if caveats:
            lines += ["", "Caveats:", ""] + [f"- {c}" for c in caveats]
        lines += [""]

    lines += [
        "## Leakage-safe split evidence",
        "",
        "Per fold: training dates end at `train_max_date`; validation starts at `val_min_date`; the gap in "
        "unique-date positions is the purge. `purge_ok` asserts `max_train_pos + "
        f"{EMBARGO_TD} < min_val_pos`, so no training label's 20td forward window reaches the validation block.",
        "",
        "| Target | Fold | train rows | val rows | train dates | val dates | train max | val min | gap (td) | purge ok |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | :--- | :--- | ---: | :--- |",
    ]
    for target, recs in folds.items():
        for r in recs:
            lines.append(
                f"| `{target}` | {r['fold']} | {r['n_train_rows']:,} | {r['n_val_rows']:,} | "
                f"{r['n_train_dates']} | {r['n_val_dates']} | {r['train_max_date']} | {r['val_min_date']} | "
                f"{r['gap_positions']} | {'OK' if r.get('purge_ok') else 'FAIL'} |"
            )
    lines += [
        "",
        "## Reading notes",
        "",
        "- The probe bounds the *existing labels*: a negative result here is a statement about these binary "
        "labels and this five-factor probe, not about the continuous route.",
        "- The E5 baseline moves with the window (WI-009b); the per-label factor table above is the bar for "
        "the rows actually scored, not a constant.",
        "- No class-label score is used anywhere; PR-AUC is descriptive colour only.",
        "",
    ]
    out.write_text("\n".join(lines) + "\n")
    return out


def build_parser() -> argparse.ArgumentParser:
    """The CLI parser for this entry point (one shared `--market` flag)."""
    ap = argparse.ArgumentParser(description=__doc__)
    add_market_argument(ap)
    ap.add_argument("--n-splits", type=int, default=5)
    ap.add_argument("--embargo-td", type=int, default=EMBARGO_TD)
    ap.add_argument("--max-dates", type=int, default=0, help="Smoke cap: keep only the last N dates (0 = all).")
    ap.add_argument("--out", default=None, help="Report path; suffixed with the market if it is not.")
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if args.embargo_td != EMBARGO_TD:
        print(f"[probe] refusing embargo_td={args.embargo_td}: the unchanged bar is {EMBARGO_TD}td", file=sys.stderr)
        return 2

    markets = cli_markets(args.market, prog="probe_wi009c")
    if markets is None:
        return 2
    print(f"[probe] PLAN: markets={', '.join(markets)}")
    return run_markets(markets, lambda m: run_market(m, args))


def run_market(market: str, args) -> int:
    t0 = time.time()
    panel = build_probe_panel(market, max_dates=args.max_dates)
    if panel.empty:
        print(f"[probe] {market}: empty panel", file=sys.stderr)
        return 1
    print(f"[probe] panel: {len(panel):,} rows, {panel['date'].nunique()} dates, "
          f"{panel['symbol'].nunique()} symbols")

    metrics: list[dict] = []
    folds: dict[str, list[dict]] = {}
    for target in TARGET_COLUMNS:
        oof, recs = cv_logit(panel, target, args.n_splits, args.embargo_td)
        folds[target] = recs
        m = label_metrics(panel, target, oof, args.n_splits)
        metrics.append(m)
        print(f"[probe] {target}: OOF IC {_fmt(m['model_ic'])} (t {_fmt(m['model_t'], '+.2f')}) vs best "
              f"factor {m['best_factor']} |IC| {_fmt(m['best_abs_ic'])} — "
              f"{'PASS' if m['passed'] else 'NEGATIVE RESULT'}")
        if any(not r.get("purge_ok", True) for r in recs):
            print(f"[probe] LEAKAGE DEFECT in {target} folds — stopping", file=sys.stderr)
            return 1

    out_override = resolve_output(args.out, market, what="--out") if args.out else None
    out = write_report(market, panel, metrics, time.time() - t0, folds, out_override)
    print(f"[probe] {market}: wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
