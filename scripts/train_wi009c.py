#!/usr/bin/env python3
"""WI-009c Step 2 — continuous 20td regressor + distribution-derived band probabilities.

Route (fixed admin design, ADR D-010)
-------------------------------------
One continuous regressor for the CAD 20-trading-day move (`fwd_atr_ret_20`, the target
named by Step 0) on **the five E5 factors only** — Step 1's probe cleared the skill bar
for 0/5 labels, so plan Step 1(d) gates all 89-feature / optional-candidate spend and
limits the continuous baseline to the same five factors.

Per fold (`PurgedWalkForwardSplit(n_splits=5, embargo_td=20)`, positions into the sorted
unique dates, never `pd.factorize` codes):

    train dates  ->  [ fit block | 20td purge | calibration block ]
    validation    =  the fold's held-out dates

The regressor is fit on the *fit* block only; the calibration block supplies the held-out
residuals that form the split-calibration **residual empirical CDF** (ADR D-010). Each
validation row's three band events are then integrated from that shifted CDF after the
thresholds are converted into the continuous target's units (see
`src/models/continuous_targets.py`). The residual dates are disjoint from the model's
training dates by construction.

Outputs
-------
    data/wi009c_oof_{MKT}.parquet      per-row fold predictions + probabilities
    reports/wi009c_regression.md       folds, calibration, skill bar, limitations
    reports/wi009c_regression_{MKT}.json   machine-readable run record
    reports/wi009c_robustness.md       Step-4 evidence gates (gate evaluation only)

`--smoke` runs write the four artifacts above with a `_smoke` suffix (except the Step-4
report, which is canonical) so a bounded smoke window can never overwrite the production
artifacts Step 5 evaluates. Plan Step 4 exposes three optional robustness switches
(`--robustness-regime`, `--robustness-stacking`, `--robustness-dynamic`) that only
*evaluate* their evidence gate: no option body is implemented, so a GO decision is
recorded in `reports/wi009c_robustness.md` and refused rather than run.

CLI::

    uv run python scripts/train_wi009c.py --market CAD --max-dates 60 --smoke
    uv run python scripts/train_wi009c.py --market CAD --detach      # production

Host budget: 2 vCPU / 8 GB / no swap. BLAS/OMP threads pinned to 2, features stay
float32, one detached chain, wall-clock capped by `--max-minutes` (default 120).
"""

from __future__ import annotations

import os

# Thread pinning must happen before numpy/BLAS load (host guardrail: n_jobs=2).
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "2")

import argparse  # noqa: E402
import datetime as dt  # noqa: E402
import json  # noqa: E402
import shlex  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pyarrow.parquet as pq  # noqa: E402
from sklearn.linear_model import Ridge  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from src.factors.e5_baseline import E5_FACTORS, build_e5_panel, date_positions  # noqa: E402
from src.models.continuous_targets import (  # noqa: E402
    ATR_PRICE_COLUMN,
    CALIB_FRACTION,
    CONTINUOUS_TARGET,
    DEFAULT_N_SPLITS,
    DOWN_MULT,
    EMBARGO_TD,
    STAY_RET_MAX,
    UP_MULT,
    composite_score,
    contrastive_candidate_decision,
    event_probabilities,
    marginal_calibration,
    purged_fold_plan,
    residual_quantiles,
    shortlist_frame,
    stacked_input_matrix,
)
from src.models.robustness_gates import (  # noqa: E402
    evaluate_robustness_gates,
    render_robustness_report,
)
from src.models.skill_bar import (  # noqa: E402
    factor_ics_from_panel,
    skill_bar_verdict,
    stats_for_rows,
    sub_window_split,
)

REPORTS = ROOT / "reports"
DATA = ROOT / "data"
FEATURES_DIR = DATA / "features"
LOGS = ROOT / "logs"
E5_COLS = [f"e5_{f}" for f in E5_FACTORS]
RIDGE_ALPHA = 100.0  # matches the E5 multivariate ridge baseline
SMOKE_DATES = 60
PROBE_REPORT = REPORTS / "wi009c_probe.md"
CONTRASTIVE_ARTIFACT = ROOT / "models" / "contrastive_ranker_wi009b.pt"
WI009B_TRAIN_JSON = REPORTS / "wi009b_train_CAD.json"


def _finite(x) -> bool:
    return x is not None and bool(np.isfinite(x))


def _fmt(x, fmt: str = "+.4f") -> str:
    return f"{x:{fmt}}" if _finite(x) else "n/a"


# --------------------------------------------------------------------------- #
# Panel
# --------------------------------------------------------------------------- #
def build_route_panel(market: str, max_dates: int = 0) -> pd.DataFrame:
    """E5 factors + the continuous target + `atr_pct_20`, float32, bounded memory.

    Streams raw OHLCV through the WI-009b E5 harness (`build_e5_panel`) and reads only
    the three identifier/ATR columns of `features_{MKT}.parquet` (never the 89-feature
    frame). Features and targets are not rebuilt.
    """
    e5 = build_e5_panel(market)
    # `amihud_20` also exists in the 89-feature matrix: namespace to avoid a silent
    # merge suffix (the WI-009b lesson).
    e5 = e5.rename(columns={f: f"e5_{f}" for f in E5_FACTORS})
    atr = pq.read_table(
        str(FEATURES_DIR / f"features_{market}.parquet"),
        columns=["date", "symbol", ATR_PRICE_COLUMN],
    ).to_pandas()

    panel = e5.merge(atr, on=["date", "symbol"], how="left")
    panel = panel.dropna(subset=E5_COLS + [CONTINUOUS_TARGET, ATR_PRICE_COLUMN])
    panel = panel[panel[ATR_PRICE_COLUMN] > 0.0]
    panel = panel.sort_values(["date", "symbol"], kind="stable").reset_index(drop=True)
    for c in E5_COLS + [CONTINUOUS_TARGET, ATR_PRICE_COLUMN]:
        panel[c] = panel[c].astype("float32")
    if max_dates > 0:
        keep = np.sort(pd.unique(panel["date"].to_numpy()))[-int(max_dates):]
        panel = panel[panel["date"].isin(set(keep))].reset_index(drop=True)
    return panel


# --------------------------------------------------------------------------- #
# Folds
# --------------------------------------------------------------------------- #
def run_folds(panel: pd.DataFrame, args, extra_scores=None, label: str = "baseline") -> dict:
    """Fit the continuous regressor fold by fold; emit OOF probabilities.

    The fold plan is computed identically whatever `extra_scores` is, so a stacked
    variant and the baseline are always evaluated on *the same* purged folds.

    Args:
        extra_scores: optional fold-safe score column appended to the five E5 factors
            as one candidate regressor input (Step 3). Never replaces the baseline.
        label: printed prefix, so a stacked run is distinguishable in the log.
    """
    dates = panel["date"].to_numpy()
    uniq = np.sort(pd.unique(dates))
    pos = date_positions(dates)  # positions, never factorize codes (WI-009 leak)
    y = panel[CONTINUOUS_TARGET].to_numpy(dtype="float64")
    atr_pct = panel[ATR_PRICE_COLUMN].to_numpy(dtype="float64")
    x_base = panel[E5_COLS].to_numpy(dtype="float32")
    x = x_base if extra_scores is None else stacked_input_matrix(x_base, extra_scores)

    plan = purged_fold_plan(
        uniq,
        n_splits=args.n_splits,
        embargo_td=args.embargo_td,
        calib_fraction=args.calib_fraction,
    )

    n = len(panel)
    oof = np.zeros(n, dtype=bool)
    forecast = np.full(n, np.nan)
    p_up = np.full(n, np.nan)
    p_down = np.full(n, np.nan)
    p_stay = np.full(n, np.nan)
    p_stay_excl = np.full(n, np.nan)
    ov_up = np.full(n, np.nan)
    ov_down = np.full(n, np.nan)
    fold_id = np.full(n, -1, dtype="int16")
    resid_parts: list[np.ndarray] = []
    fold_records: list[dict] = []
    t0 = time.time()
    budget_s = float(args.max_minutes) * 60.0

    for rec in plan:
        fold = rec["fold"]
        if "skipped" in rec:
            fold_records.append({"fold": fold, "skipped": rec["skipped"],
                                 "n_val_dates": rec["n_val_dates"]})
            print(f"[wi009c:{label}] fold {fold}: skipped ({rec['skipped']})")
            continue
        if not rec["purge_ok"]:
            raise RuntimeError(
                f"LEAKAGE DEFECT in fold {fold}: gaps fit->cal {rec['gap_fit_cal']}, "
                f"fit->val {rec['gap_fit_val']}, cal->val {rec['gap_cal_val']} "
                f"(embargo {args.embargo_td}td)"
            )
        if time.time() - t0 > budget_s:
            fold_records.append({"fold": fold, "skipped": f"wall-clock budget {args.max_minutes}min reached"})
            print(f"[wi009c:{label}] fold {fold}: skipped (wall-clock budget reached)")
            continue

        fit_rows = np.isin(pos, rec["fit_pos"])
        cal_rows = np.isin(pos, rec["cal_pos"])
        val_rows = np.isin(pos, rec["val_pos"])
        model = make_pipeline(StandardScaler(), Ridge(alpha=RIDGE_ALPHA))
        model.fit(x[fit_rows], y[fit_rows])

        resid = y[cal_rows] - model.predict(x[cal_rows])
        resid_parts.append(resid)
        f_val = model.predict(x[val_rows])
        probs = event_probabilities(f_val, resid, atr_pct[val_rows])

        forecast[val_rows] = f_val
        p_up[val_rows] = probs["p_up"]
        p_down[val_rows] = probs["p_down"]
        p_stay[val_rows] = probs["p_stay"]
        p_stay_excl[val_rows] = probs["p_stay_exclusive"]
        ov_up[val_rows] = probs["overlap_up_stay"]
        ov_down[val_rows] = probs["overlap_down_stay"]
        fold_id[val_rows] = fold
        oof |= val_rows

        fold_records.append(
            {
                "fold": fold,
                "n_fit_rows": int(fit_rows.sum()),
                "n_cal_rows": int(cal_rows.sum()),
                "n_val_rows": int(val_rows.sum()),
                "n_fit_dates": rec["n_fit_dates"],
                "n_cal_dates": rec["n_cal_dates"],
                "n_val_dates": rec["n_val_dates"],
                "fit_min": rec["fit_min"],
                "fit_max": rec["fit_max"],
                "cal_min": rec["cal_min"],
                "cal_max": rec["cal_max"],
                "val_min": rec["val_min"],
                "val_max": rec["val_max"],
                "gap_fit_cal": rec["gap_fit_cal"],
                "gap_fit_val": rec["gap_fit_val"],
                "gap_cal_val": rec["gap_cal_val"],
                "purge_ok": rec["purge_ok"],
                "resid_mean": float(np.mean(resid)),
                "resid_std": float(np.std(resid, ddof=1)) if resid.size > 1 else float("nan"),
            }
        )
        print(
            f"[wi009c:{label}] fold {fold}: fit {rec['n_fit_dates']}d/{int(fit_rows.sum()):,}r "
            f"cal {rec['n_cal_dates']}d/{int(cal_rows.sum()):,}r "
            f"val {rec['n_val_dates']}d/{int(val_rows.sum()):,}r "
            f"gaps fit->cal {rec['gap_fit_cal']}td fit->val {rec['gap_fit_val']}td "
            f"purge_ok={rec['purge_ok']} | {time.time() - t0:.1f}s"
        )

    if not oof.any():
        raise RuntimeError("no viable fold produced out-of-fold rows")

    frame = panel.loc[oof, ["date", "symbol"] + E5_COLS].reset_index(drop=True)
    frame["fold"] = fold_id[oof]
    frame["forecast"] = forecast[oof]
    frame["y"] = y[oof]
    frame["atr_pct"] = atr_pct[oof]
    frame["p_up"] = p_up[oof]
    frame["p_down"] = p_down[oof]
    frame["p_stay"] = p_stay[oof]
    frame["p_stay_exclusive"] = p_stay_excl[oof]
    frame["overlap_up_stay"] = ov_up[oof]
    frame["overlap_down_stay"] = ov_down[oof]

    return {
        "frame": frame,
        "fold_records": fold_records,
        "residuals": np.concatenate(resid_parts) if resid_parts else np.empty(0),
        "n_oof_rows": int(oof.sum()),
        "elapsed_s": time.time() - t0,
        "n_viable_folds": int(sum(1 for r in fold_records if "skipped" not in r)),
        "n_input_cols": int(x.shape[1]),
        "label": label,
    }


# --------------------------------------------------------------------------- #
# Skill bar
# --------------------------------------------------------------------------- #
def score_skill(frame: pd.DataFrame, score_col: str = "forecast") -> dict:
    """Same-rows comparison of the OOF continuous forecast against the five E5 factors.

    Score-based within-date Spearman rank-IC only (`pair_sampler.within_date_rank_ic`);
    clause (a) = same sign as the best factor AND |IC| >= (admin-adopted, WI-009b);
    clause (b) = |t| > 2 with the same sign in >= 2 disjoint sub-windows. The module
    `src.models.skill_bar` is reused unchanged; the >= tie-break is applied on top.
    """
    scored = frame[np.isfinite(frame[score_col].to_numpy()) & np.isfinite(frame["y"].to_numpy())]
    scored = scored.reset_index(drop=True)
    model_ic, model_t, n_dates = stats_for_rows(scored, score_col, "y")
    factor_stats = factor_ics_from_panel(scored, E5_FACTORS, "e5_", "y")
    blocks = sub_window_split(pd.unique(scored["date"].to_numpy()), n_windows=2)
    sub_stats = [stats_for_rows(scored[scored["date"].isin(set(b))], score_col, "y") for b in blocks]
    verdict = skill_bar_verdict(model_ic, model_t, factor_stats, sub_stats)

    best_name = verdict["clause_a"]["best_factor"]
    best_ic = factor_stats[best_name][0]
    best_abs = float(abs(best_ic))
    same_sign = _finite(model_ic) and _finite(best_ic) and np.sign(model_ic) == np.sign(best_ic)
    pass_a = bool(same_sign and _finite(model_ic) and abs(model_ic) >= best_abs)
    pass_b = bool(verdict["clause_b"]["passed"])
    return {
        "n_rows": int(len(scored)),
        "n_dates": int(n_dates),
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
    }


# --------------------------------------------------------------------------- #
# Step 4 — evidence-gated robustness options (gate evaluation only)
# --------------------------------------------------------------------------- #
def robustness_evidence(args, skill: dict, contrastive) -> tuple[dict | None, dict | None, str]:
    """Gate evidence for Step 4 plus a human-readable provenance line.

    A `--smoke` invocation must not fabricate thinner gate evidence, so a smoke run
    reads the **production** run record when one exists. A non-smoke run is its own
    evidence. `--robustness-evidence` overrides both (used to re-evaluate the gates
    against a pinned record).
    """
    prod = REPORTS / f"wi009c_regression_{args.market}.json"
    if args.robustness_evidence:
        p = Path(args.robustness_evidence)
        if not p.exists():
            raise FileNotFoundError(f"--robustness-evidence {p} does not exist")
        rec = json.loads(p.read_text())
        return (
            rec.get("skill"),
            rec.get("contrastive_candidate"),
            f"`{p}` (explicit `--robustness-evidence`)",
        )
    if args.smoke and prod.exists():
        rec = json.loads(prod.read_text())
        return (
            rec.get("skill"),
            rec.get("contrastive_candidate"),
            f"`{prod.relative_to(ROOT)}` — production run record "
            f"(smoke={rec.get('smoke')}, generated {rec.get('generated_utc')}), read so a "
            "`--smoke` invocation cannot record thinner gate evidence",
        )
    return skill, contrastive, "this run (in-memory skill + fold-safety decision)"


def run_robustness_gates(args, skill: dict, contrastive, panel: pd.DataFrame, frame: pd.DataFrame) -> dict:
    """Evaluate the three Step-4 gates, print each verdict, write the Step-4 report.

    No option body exists in this work item (plan Step 4(a)/(d)): a GO decision is
    recorded and refused, never silently executed.
    """
    b_skill, b_ct, source = robustness_evidence(args, skill, contrastive)
    if b_ct is None:
        uniq_dates = np.sort(pd.unique(panel["date"].to_numpy()))
        b_ct = contrastive_status(args.market, uniq_dates, frame["date"].unique(), args.embargo_td)
        source += "; Step-3 fold-safety decision recomputed for this panel (no feature spend)"
    ctx = evaluate_robustness_gates(
        PROBE_REPORT.read_text() if PROBE_REPORT.exists() else "", b_skill, b_ct
    )
    requested = [
        s for s, on in (
            ("--robustness-regime", args.robustness_regime),
            ("--robustness-stacking", args.robustness_stacking),
            ("--robustness-dynamic", args.robustness_dynamic),
        ) if on
    ]
    ctx["requested_switches"] = requested
    print(f"[wi009c] robustness: {ctx['n_attempted']} attempted, {ctx['n_not_run']} NOT RUN, "
          f"{ctx['n_go']} GO — evidence: {source}")
    for o in ctx["options"]:
        print(f"[wi009c] robustness {o['key']}: {o['status']} ({o['gate_decision']}) — {o['reason']}")
        if o["go"]:
            print(f"[wi009c] robustness {o['key']}: GO recorded but refused — no option body is "
                  "implemented in WI-009c (plan Step 4(d))", file=sys.stderr)
    if requested:
        print(f"[wi009c] robustness switches requested: {', '.join(requested)}")
    out = Path(args.robustness_out) if args.robustness_out else REPORTS / "wi009c_robustness.md"
    render_robustness_report(
        ctx, out, market=args.market, evidence_source=source, smoke=bool(args.smoke),
        baseline_skill=b_skill,
    )
    print(f"[wi009c] wrote {out}")
    return ctx


# --------------------------------------------------------------------------- #
# Step 3 — fold-safe contrastive stacked-input candidate
# --------------------------------------------------------------------------- #
def contrastive_status(market: str, uniq_dates, val_dates, embargo_td: int) -> dict:
    """Decide whether the saved contrastive artifact may be used as a stacked input.

    Two gates (plan Step 1(d) and Step 3(a)/(d)) are evaluated by
    `contrastive_candidate_decision`; the provenance it needs is the Step-1 probe
    report and the artifact's recorded training cutoff. The `.pt` blob carries only
    `state_dict`/`input_dim`/`embed_dim`/`feature_cols` (see
    `src.models.contrastive_ranking.save_model`), so the cutoff is established from the
    WI-009b run metadata that produced the artifact. If neither is available the
    decision fails closed.
    """
    probe_text = PROBE_REPORT.read_text() if PROBE_REPORT.exists() else ""
    provenance: list[str] = []
    cutoff = None
    if not probe_text:
        provenance.append(f"Step-1 probe report {PROBE_REPORT.relative_to(ROOT)} MISSING (gate treated as no permission)")
    if WI009B_TRAIN_JSON.exists():
        blob = json.loads(WI009B_TRAIN_JSON.read_text())
        train_dates = blob.get("train_dates") or []
        if train_dates:
            cutoff = str(train_dates[-1])
            provenance.append(
                f"artifact cutoff established from {WI009B_TRAIN_JSON.relative_to(ROOT)}: "
                f"train_dates[-1] = {cutoff} ({len(train_dates)} training dates)"
            )
        val = blob.get("val_dates") or []
        if val:
            provenance.append(f"WI-009b validation window {val[0]} → {val[-1]}")
    provenance.append(
        "`models/contrastive_ranker_wi009b.pt` carries no cutoff metadata "
        "(state_dict/input_dim/embed_dim/feature_cols only)"
    )
    if CONTRASTIVE_ARTIFACT.exists():
        provenance.append(f"artifact present: models/{CONTRASTIVE_ARTIFACT.name}")
    else:
        provenance.append(f"artifact MISSING: models/{CONTRASTIVE_ARTIFACT.name}")

    if cutoff is None:
        decision = {
            "step1_permits_feature_spend": False,
            "artifact_train_max_date": "unknown",
            "embargo_td": int(embargo_td),
            "run": False,
            "fold_safe": None,
            "offenders": [],
            "status": "NOT RUN",
            "reason": (
                "fold-safe scoring could not be established (plan Step 3(d)): no recorded "
                "training cutoff for the artifact, so no held-out date can be shown to be "
                "outside its training window. Candidate omitted."
            ),
        }
    else:
        decision = contrastive_candidate_decision(
            probe_text, cutoff, val_dates, uniq_dates, embargo_td
        )
    decision["market"] = market
    decision["provenance"] = provenance
    decision["artifact"] = f"models/{CONTRASTIVE_ARTIFACT.name}"
    return decision


def contrastive_scores_for_panel(market: str, panel: pd.DataFrame, model, feature_cols, chunk_dates: int = 60) -> np.ndarray:
    """Score the panel's rows with `ContrastiveRanker.score_numpy`, streamed by date chunk.

    This is the 89-feature spend the Step-1 gate controls: it is only reachable after
    `contrastive_candidate_decision` returns `run=True`. The feature matrix is read from
    `features_{MKT}.parquet` in bounded date chunks (`pyarrow.dataset`), never as one
    all-ticker frame.
    """
    import pyarrow.dataset as ds

    path = FEATURES_DIR / f"features_{market}.parquet"
    dataset = ds.dataset(str(path), format="parquet")
    dates = np.sort(pd.unique(panel["date"].to_numpy()))
    scores = np.full(len(panel), np.nan, dtype="float64")
    pos_of = pd.Series(
        np.arange(len(panel)), index=pd.MultiIndex.from_arrays([panel["date"], panel["symbol"]])
    )
    for i in range(0, len(dates), int(chunk_dates)):
        chunk = list(dates[i : i + int(chunk_dates)])
        tbl = dataset.to_table(
            columns=["date", "symbol"] + list(feature_cols),
            filter=ds.field("date").isin(chunk),
        )
        df = tbl.to_pandas()
        if df.empty:
            continue
        s = model.score_numpy(df[list(feature_cols)].to_numpy(dtype="float32"))
        idx = pos_of.reindex(pd.MultiIndex.from_arrays([df["date"], df["symbol"]])).to_numpy()
        ok = ~pd.isna(idx)
        scores[idx[ok].astype(int)] = s[ok]
    if not np.isfinite(scores).all():
        raise RuntimeError("contrastive scoring left non-finite rows: refusing to feed a partial score")
    return scores


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def write_report(ctx: dict, out_path: Path) -> Path:
    skill = ctx["skill"]
    cal = ctx["calibration"]
    masses = cal["masses"]
    q = ctx["residual_quantiles"]
    v = skill["verdict"]
    a, b = v["clause_a"], v["clause_b"]

    lines = [
        f"# WI-009c Steps 2–3 — continuous 20td regressor, band probabilities and shortlist "
        f"({ctx['market']})",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}"
        + ("  · **SMOKE RUN** (`--max-dates` cap, not the production chain)" if ctx["smoke"] else ""),
        f"- Panel: {ctx['n_rows']:,} rows · {ctx['n_symbols']} symbols · {ctx['n_dates']} dates "
        f"({ctx['date_min']} → {ctx['date_max']})",
        f"- Continuous target: `{CONTINUOUS_TARGET}` (the Step-0 named target), ATR/price column "
        f"`{ATR_PRICE_COLUMN}`.",
        f"- Features: the five E5 factors only ({', '.join('`' + c + '`' for c in E5_COLS)}). "
        "Step 1 cleared the skill bar for 0/5 labels, so plan Step 1(d) gates all 89-feature and "
        "optional-candidate spend — this baseline is limited to the same five factors.",
        f"- Model: `StandardScaler` + `Ridge(alpha={RIDGE_ALPHA:g})`, float32 features, "
        f"BLAS/OMP threads pinned to 2. Wall clock {ctx['elapsed_s']:.1f}s.",
        f"- CV: `PurgedWalkForwardSplit(n_splits={ctx['n_splits']}, embargo_td={ctx['embargo_td']})` "
        "over unique dates keyed by *positions* (`src.factors.e5_baseline.date_positions`).",
        f"- Split calibration (ADR D-010): per fold the last {ctx['calib_fraction']:.0%} of the "
        f"training dates (purged {ctx['embargo_td']}td from the fit block) supplies the held-out "
        "residual empirical CDF; the model is fit on the remaining training dates only.",
        "",
        "## Fold plan and leakage evidence",
        "",
        "Calibration residuals are drawn from the `cal` block, which is disjoint from the `fit` "
        "block that trained that fold's model, and both are separated from the `val` block by the "
        "20td purge. `purge_ok` asserts `gap(fit→cal) >= 20td` and `gap(fit→val) >= 20td` and "
        "`gap(cal→val) >= 0`.",
        "",
        "| Fold | fit dates | fit rows | cal dates | cal rows | val dates | val rows | "
        "gap fit→cal | gap fit→val | gap cal→val | purge ok |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |",
    ]
    for r in ctx["fold_records"]:
        if "skipped" in r:
            lines.append(f"| {r['fold']} | — | — | — | — | {r.get('n_val_dates', 0)} | — | — | — | — | "
                         f"SKIPPED ({r['skipped']}) |")
            continue
        lines.append(
            f"| {r['fold']} | {r['n_fit_dates']} ({r['fit_min']}→{r['fit_max']}) | {r['n_fit_rows']:,} | "
            f"{r['n_cal_dates']} ({r['cal_min']}→{r['cal_max']}) | {r['n_cal_rows']:,} | "
            f"{r['n_val_dates']} ({r['val_min']}→{r['val_max']}) | {r['n_val_rows']:,} | "
            f"{r['gap_fit_cal']} | {r['gap_fit_val']} | {r['gap_cal_val']} | "
            f"{'OK' if r['purge_ok'] else 'FAIL'} |"
        )
    lines += [
        "",
        f"- Viable folds: {ctx['n_viable_folds']} of {len(ctx['fold_records'])}; "
        f"out-of-fold rows scored: {ctx['n_oof_rows']:,}.",
        "",
        "## Event thresholds in the continuous target's units",
        "",
        "| Event | definition (raw) | in `fwd_atr_ret_20` units |",
        "| :--- | :--- | :--- |",
        f"| up | forward dollar move >= {UP_MULT:+.1f}×ATR | `{CONTINUOUS_TARGET} >= {UP_MULT:+.1f}` |",
        f"| down | forward dollar move <= {DOWN_MULT:+.1f}×ATR | `{CONTINUOUS_TARGET} <= {DOWN_MULT:+.1f}` |",
        f"| stay | forward return within ±{STAY_RET_MAX:.0%} (relative) | "
        f"`\\|{CONTINUOUS_TARGET}\\| <= {STAY_RET_MAX:.2f} / {ATR_PRICE_COLUMN}` (row-specific) |",
        "",
        "The up/down events are ATR-dollar based and the stay event is relative; the conversion "
        f"uses the Step-0 named ratio `{ATR_PRICE_COLUMN}`. **The events overlap** under these "
        "thresholds (a small ATR/price makes 2×ATR smaller than ±5%), so each probability is "
        "integrated independently and the overlap is reported — it is never forced into a partition.",
        "",
        "## Probabilities P(up), P(down), P(stay) and the declared composite",
        "",
        f"- Declared shortlist composite: `P(up) - P(down)` (ADR D-010). `P(stay)` is reported "
        "alongside it and is never used as a hidden tie-break.",
        f"- Mean P(up) = {masses['mean_p_up']:.4f} (realized {masses['realized_rate_up']:.4f}) · "
        f"mean P(down) = {masses['mean_p_down']:.4f} (realized {masses['realized_rate_down']:.4f}) · "
        f"mean P(stay) = {masses['mean_p_stay']:.4f} (realized {masses['realized_rate_stay']:.4f})",
        f"- Mean P(stay) exclusive of up/down = {masses['mean_p_stay_exclusive']:.4f} "
        f"(realized {masses['realized_rate_stay_exclusive']:.4f}) — this is the `y_20d_stay` "
        "definition; the raw `P(stay)` above is the ±5% event without that exclusion.",
        f"- Mean overlap mass: up∩stay {masses['mean_overlap_up_stay']:.4f}, "
        f"down∩stay {masses['mean_overlap_down_stay']:.4f}; "
        f"mean P(up)+P(down)+P(stay) = {masses['mean_sum_up_down_stay']:.4f} "
        "(may exceed 1 — overlap preserved by design).",
        f"- All probabilities finite and within [0, 1] on all {ctx['n_oof_rows']:,} scored rows.",
        "",
        "## Calibration diagnostics",
        "",
        f"- Residual ECDF sample: {q['n']:,} held-out residuals (pooled across folds), "
        f"mean {_fmt(q.get('mean'))}, std {_fmt(q.get('std'))}, "
        f"q01 {_fmt(q.get('q01'))}, q05 {_fmt(q.get('q05'))}, q50 {_fmt(q.get('q50'))}, "
        f"q95 {_fmt(q.get('q95'))}, q99 {_fmt(q.get('q99'))}.",
        "",
        "| Event | n | mean predicted | realized rate | bias | Brier |",
        "| :--- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key, label in (("up", "P(up)"), ("down", "P(down)"), ("stay", "P(stay)"),
                       ("stay_exclusive", "P(stay) exclusive")):
        s = cal[key]
        lines.append(
            f"| {label} | {s['n']:,} | {s['mean_predicted']:.4f} | {s['realized_rate']:.4f} | "
            f"{s['bias']:+.4f} | {s['brier']:.4f} |"
        )
    lines += ["", "Reliability (equal-count deciles of the predicted probability):", ""]
    for key, label in (("up", "P(up)"), ("down", "P(down)"), ("stay", "P(stay)")):
        bins = cal[key]["bins"]
        lines.append(f"`{label}`:")
        lines.append("")
        lines.append("| bin | n | predicted | realized |")
        lines.append("| ---: | ---: | ---: | ---: |")
        for bn in bins:
            lines.append(
                f"| {bn['bin']} | {bn['n']:,} | {bn['mean_predicted']:.4f} | "
                f"{bn['realized_rate']:.4f} |"
            )
        lines.append("")
    lines += [
        "**Calibration limits (read before using these numbers):**",
        "",
        "- This is a **marginal** forecast distribution, not a guarantee of conditional "
        "calibration: residuals are pooled across folds and regimes, so a row's true event "
        "probability may differ from the reported value.",
        "- The tails are data-limited (the ECDF cannot exceed the largest observed residual), so "
        "extreme up/down probabilities are bounded by the calibration sample size.",
        "- The residual sample is drawn from dates before each fold's validation block; regime "
        "drift between the calibration block and the validation block is not corrected.",
        "- No independent binary classifiers were fit, and none were substituted when "
        "diagnostics are imperfect (ADR D-010).",
        "",
        "## Skill result — same-sign and |IC| against the five E5 factors",
        "",
        "Score-based within-date Spearman rank-IC of the continuous forecast vs "
        f"`{CONTINUOUS_TARGET}`, on exactly the same out-of-fold rows and dates as every factor. "
        "Class-label IC is never used (WI-002 lesson).",
        "",
        "| Score | mean IC | \\|IC\\| | t | dates |",
        "| :--- | ---: | ---: | ---: | ---: |",
        f"| **continuous baseline (5 E5 factors)** | {_fmt(skill['model_ic'])} | "
        f"{_fmt(abs(skill['model_ic']) if _finite(skill['model_ic']) else float('nan'))} | "
        f"{_fmt(skill['model_t'], '+.2f')} | {skill['n_dates']} |",
    ]
    for fac, (ic, t, n) in sorted(skill["factor_stats"].items(), key=lambda kv: -abs(kv[1][0])):
        lines.append(f"| `e5_{fac}` (factor) | {_fmt(ic)} | {abs(ic):.4f} | {_fmt(t, '+.2f')} | {n} |")
    lines += [
        "",
        f"- **Clause (a)** — same sign as the best factor AND |IC| >= its |IC|: "
        f"**{'PASS' if skill['pass_a'] else 'FAIL'}** (baseline |IC| "
        f"{_fmt(abs(skill['model_ic']) if _finite(skill['model_ic']) else float('nan'))} vs "
        f"`e5_{skill['best_factor']}` |IC| {_fmt(skill['best_abs_ic'])}, "
        f"same-sign {skill['same_sign']}, margin {_fmt(a['margin'])})",
        f"- **Clause (b)** — |t| > 2 with the same sign in >= 2 disjoint sub-windows: "
        f"**{'PASS' if skill['pass_b'] else 'FAIL'}** (t {_fmt(skill['model_t'], '+.2f')}, "
        f"{b['n_sub_windows']} sub-windows, same sign all: {b['all_windows_same_sign']}, "
        f"|t|>2 all: {b['all_windows_abs_t_gt_2']})",
        f"- **SKILL BAR: {'PASS' if skill['passed'] else 'FAIL'}**"
        + (" (with caveats)" if v.get("caveats") and skill["passed"] else ""),
        "",
    ]
    if v.get("caveats"):
        lines += ["Caveats (emitted verbatim by the reused `src/models/skill_bar.py`):", ""]
        lines += [f"- {c}" for c in v["caveats"]]
        if not skill["pass_a"]:
            # The module's "met in MAGNITUDE only" phrasing assumes clause (a) passed on
            # magnitude. It did not here, so say so rather than let the caveat imply a pass.
            lines += [
                "",
                f"- **Correction for this run:** clause (a) also FAILS on magnitude "
                f"(baseline |IC| {_fmt(abs(skill['model_ic']) if _finite(skill['model_ic']) else float('nan'))} "
                f"< `e5_{skill['best_factor']}` |IC| {_fmt(skill['best_abs_ic'])}), so the "
                "\"met in MAGNITUDE only\" phrasing in the caveat above does **not** apply here — "
                "the bar fails on both clauses.",
            ]
        lines.append("")
    subs = b.get("sub_windows") or []
    if subs:
        lines += [
            "| Sub-window | dates | baseline mean IC | t | sign matches full window |",
            "| ---: | ---: | ---: | ---: | :--- |",
        ]
        for w in subs:
            lines.append(
                f"| {w['window']} | {w['n_dates']} | {_fmt(w['ic'])} | {_fmt(w['t'], '+.2f')} | "
                f"{w['sign_matches_model']} |"
            )
        lines.append("")
    if not skill["passed"]:
        lines += [
            "**This is a documented negative result, not an execution failure.** Per plan Step 2(d) "
            "a failed skill clause is reported and is not tuned away or suppressed, and no "
            "independent binary classifier is substituted.",
            "",
        ]

    # ---- Step 3: shortlist ------------------------------------------------- #
    sl = ctx.get("shortlist")
    lines += [
        "## Shortlist — deterministic daily ranking by `P(up)-P(down)`",
        "",
    ]
    if sl is None:
        lines += ["Not produced in this run.", ""]
    else:
        lines += [
            f"- As-of date: **{sl['as_of_date']}** (latest scored out-of-fold date) · "
            f"shortlist length {len(sl['rows'])} of {sl['n_candidates']:,} candidates · "
            f"declared composite `P(up)-P(down)` with `symbol` ascending as the deterministic "
            "tie-break; `P(stay)` is reported alongside and is never a tie-break.",
            "- Research output only: this is a daily shortlist for human review, not trade "
            "advice and not wired to orders.",
            "",
            "| rank | symbol | `P(up)` | `P(down)` | `P(up)-P(down)` | `P(stay)` | forecast |",
            "| ---: | :--- | ---: | ---: | ---: | ---: | ---: |",
        ]
        for r in sl["rows"]:
            lines.append(
                f"| {r['rank']} | `{r['symbol']}` | {r['p_up']:.4f} | {r['p_down']:.4f} | "
                f"{r['composite']:+.4f} | {r['p_stay']:.4f} | {r['forecast']:+.4f} |"
            )
        lines.append("")

    # ---- Step 3: contrastive candidate ------------------------------------- #
    ct = ctx.get("contrastive")
    lines += [
        "## Fold-safe contrastive stacked-input candidate (`score_numpy`)",
        "",
    ]
    if ct is None:
        lines += [
            "Not attempted in this run (`--contrastive` was not passed). The candidate is "
            "optional and is gated by the Step-1 evidence.",
            "",
        ]
    else:
        lines += [
            f"- Artifact: `{ct['artifact']}`; loaded through "
            "`src.models.contrastive_ranking.ContrastiveRanker.score_numpy` as **one candidate "
            "regressor input** — it never replaces the continuous model and never becomes the "
            "final ranking.",
            f"- **Step 1 gate — 89-feature spend permitted: {ct['step1_permits_feature_spend']}** "
            "(plan Step 1(d): permitted only when a label clears the unchanged skill bar).",
            f"- **fold-safe for every held-out date: "
            f"{'yes' if ct['fold_safe'] else ('no' if ct['fold_safe'] is False else 'not established')}** "
            f"(recorded artifact cutoff {ct['artifact_train_max_date']}, "
            f"{ct['embargo_td']}td embargo, {len(ct['offenders'])} offending held-out date(s)).",
            f"- **Status: {ct['status']}** — {ct['reason']}",
            "",
            "Provenance used for the fold-safety decision:",
            "",
        ]
        lines += [f"- {p}" for p in ct["provenance"]]
        lines.append("")
        if ct.get("stacked_skill"):
            s = ct["stacked_skill"]
            lines += [
                "Stacked vs baseline on **identical purged folds**:",
                "",
                "| Score | mean IC | \\|IC\\| | t | dates | same sign | clause (a) | skill bar |",
                "| :--- | ---: | ---: | ---: | ---: | :--- | :--- | :--- |",
                f"| baseline (5 E5 factors) | {_fmt(skill['model_ic'])} | "
                f"{_fmt(abs(skill['model_ic']) if _finite(skill['model_ic']) else float('nan'))} | "
                f"{_fmt(skill['model_t'], '+.2f')} | {skill['n_dates']} | {skill['same_sign']} | "
                f"{'PASS' if skill['pass_a'] else 'FAIL'} | {'PASS' if skill['passed'] else 'FAIL'} |",
                f"| + contrastive score | {_fmt(s['model_ic'])} | "
                f"{_fmt(abs(s['model_ic']) if _finite(s['model_ic']) else float('nan'))} | "
                f"{_fmt(s['model_t'], '+.2f')} | {s['n_dates']} | {s['same_sign']} | "
                f"{'PASS' if s['pass_a'] else 'FAIL'} | {'PASS' if s['passed'] else 'FAIL'} |",
                "",
            ]
        else:
            lines += [
                "The candidate was **omitted, not silently skipped**: no stacked model was fit and "
                "no in-sample score was fed anywhere. `P(up)-P(down)` ranking above comes from the "
                "five-factor continuous baseline only.",
                "",
            ]

    lines += [
        "## Reading notes",
        "",
        "- The five-factor probe (Step 1) is a statement about the *binary labels*; this baseline "
        "is the continuous route, so a negative result here is a statement about the five-factor "
        "continuous forecast on this window.",
        "- `fwd_atr_ret_20` is derived from raw OHLCV by the E5 harness (`wilder_atr`, trailing); "
        "the forward window is the thing being predicted, and every feature is trailing.",
        "- No live-use integration: the shortlist and probabilities are research output pending the "
        "human gate.",
        "",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n")
    return out_path


# --------------------------------------------------------------------------- #
# Detached launcher
# --------------------------------------------------------------------------- #
def launch_detached(argv: list[str]) -> int:
    """Start the production run as an independent process and return immediately.

    Mirrors `scripts/wi009b_launch.py`: `start_new_session=True`, everything appended to
    `logs/wi009c_train.out`, `END`/`EXIT:<code>` markers written by the detached shell.
    """
    LOGS.mkdir(parents=True, exist_ok=True)
    log = LOGS / "wi009c_train.out"
    pidfile = LOGS / "wi009c_train.pid"
    cmd = [sys.executable, "-u", str(ROOT / "scripts" / "train_wi009c.py")]
    cmd += [a for a in argv if a != "--detach"]
    env = dict(os.environ)
    env.update(
        {
            "OMP_NUM_THREADS": "2",
            "OPENBLAS_NUM_THREADS": "2",
            "MKL_NUM_THREADS": "2",
            "NUMEXPR_NUM_THREADS": "2",
            "PYTHONUNBUFFERED": "1",
        }
    )
    inner = " ".join(shlex.quote(c) for c in cmd)
    wrapper = f"{inner}; rc=$?; echo 'END '\"$(date -Is)\"; echo EXIT:$rc"
    with log.open("a") as fh:
        fh.write(f"START {dt.datetime.now().isoformat()} {inner}\n")
        fh.flush()
        proc = subprocess.Popen(
            ["/bin/sh", "-c", wrapper],
            cwd=str(ROOT),
            stdout=fh,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            env=env,
        )
    pidfile.write_text(f"{proc.pid}\n")
    print(f"[wi009c] detached pid={proc.pid} → {log}")
    print(f"[wi009c] poll: tail -n 40 {log} ; grep -c EXIT: {log}")
    return 0


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--market", default="CAD")
    ap.add_argument("--max-dates", type=int, default=0, help="Keep only the last N dates (0 = all).")
    ap.add_argument("--smoke", action="store_true", help="Bounded smoke run (caps dates, never detached).")
    ap.add_argument("--detach", action="store_true", help="Re-exec this run as a detached production process.")
    ap.add_argument("--n-splits", type=int, default=DEFAULT_N_SPLITS)
    ap.add_argument("--embargo-td", type=int, default=EMBARGO_TD)
    ap.add_argument("--calib-fraction", type=float, default=CALIB_FRACTION)
    ap.add_argument("--alpha", type=float, default=RIDGE_ALPHA)
    ap.add_argument("--max-minutes", type=float, default=120.0, help="Wall-clock cap for the detached chain.")
    ap.add_argument("--top-n", type=int, default=20, help="Shortlist length.")
    ap.add_argument("--shortlist-out", default=None)
    ap.add_argument("--contrastive", action="store_true",
                    help="Attempt the fold-safe contrastive stacked-input candidate (gated).")
    ap.add_argument("--robustness-report", action="store_true",
                    help="Evaluate the Step-4 evidence gates and write reports/wi009c_robustness.md.")
    ap.add_argument("--robustness-regime", action="store_true",
                    help="Evaluate the trailing market-state/regime candidate gate (Step 4).")
    ap.add_argument("--robustness-stacking", action="store_true",
                    help="Evaluate the factor + contrastive + regressor stacking candidate gate (Step 4).")
    ap.add_argument("--robustness-dynamic", action="store_true",
                    help="Evaluate the dynamic feature selection candidate gate (Step 4).")
    ap.add_argument("--robustness-out", default=None,
                    help="Step-4 report path (default: reports/wi009c_robustness.md, never smoke-suffixed).")
    ap.add_argument("--robustness-evidence", default=None,
                    help="Run-record JSON to read the Step-4 gate evidence from (default: production "
                         "record for a --smoke run, else this run).")
    ap.add_argument("--report", default=None)
    ap.add_argument("--oof-out", default=None)
    ap.add_argument("--json-out", default=None)
    return ap.parse_args(argv)


def main(argv=None) -> int:
    global RIDGE_ALPHA
    args = parse_args(argv)

    if args.embargo_td != EMBARGO_TD:
        print(f"[wi009c] refusing embargo_td={args.embargo_td}: the fixed purge is {EMBARGO_TD}td",
              file=sys.stderr)
        return 2
    if args.smoke and args.detach:
        print("[wi009c] --smoke and --detach are mutually exclusive", file=sys.stderr)
        return 2
    if args.smoke and not args.max_dates:
        args.max_dates = SMOKE_DATES
    RIDGE_ALPHA = float(args.alpha)

    if args.detach:
        return launch_detached(sys.argv[1:])

    t_start = time.time()
    panel = build_route_panel(args.market, max_dates=args.max_dates)
    if panel.empty:
        print(f"[wi009c] {args.market}: empty route panel", file=sys.stderr)
        return 1
    print(f"[wi009c] panel: {len(panel):,} rows · {panel['symbol'].nunique()} symbols · "
          f"{panel['date'].nunique()} dates ({panel['date'].min().date()} → {panel['date'].max().date()})"
          + ("  [SMOKE]" if args.smoke else ""))

    folds = run_folds(panel, args)
    frame = folds["frame"]
    if not np.isfinite(frame[["p_up", "p_down", "p_stay", "p_stay_exclusive"]].to_numpy()).all():
        print("[wi009c] NON-FINITE probabilities — stopping (plan Step 2(d))", file=sys.stderr)
        return 1
    for col in ("p_up", "p_down", "p_stay", "p_stay_exclusive"):
        vals = frame[col].to_numpy()
        if vals.min() < 0.0 or vals.max() > 1.0:
            print(f"[wi009c] {col} outside [0,1] — stopping", file=sys.stderr)
            return 1

    skill = score_skill(frame)
    pred = {
        "p_up": frame["p_up"].to_numpy(),
        "p_down": frame["p_down"].to_numpy(),
        "p_stay": frame["p_stay"].to_numpy(),
        "p_stay_exclusive": frame["p_stay_exclusive"].to_numpy(),
        "overlap_up_stay": frame["overlap_up_stay"].to_numpy(),
        "overlap_down_stay": frame["overlap_down_stay"].to_numpy(),
    }
    calibration = marginal_calibration(pred, frame["y"].to_numpy(), frame["atr_pct"].to_numpy())
    resid_q = residual_quantiles(folds["residuals"])

    print(f"[wi009c] skill: baseline IC {_fmt(skill['model_ic'])} (t {_fmt(skill['model_t'], '+.2f')}) "
          f"vs best factor {skill['best_factor']} |IC| {_fmt(skill['best_abs_ic'])} — "
          f"same-sign {skill['same_sign']} — "
          f"{'PASS' if skill['passed'] else 'NEGATIVE RESULT'}")

    # ---- Step 3a: deterministic shortlist (not feature-gated) -------------- #
    sl_frame = shortlist_frame(frame, top_n=args.top_n)
    as_of = sl_frame["date"].iloc[0]
    shortlist = {
        "as_of_date": str(pd.Timestamp(as_of).date()),
        "n_candidates": int((frame["date"] == as_of).sum()),
        "rows": [
            {
                "rank": int(r["rank"]),
                "symbol": str(r["symbol"]),
                "p_up": float(r["p_up"]),
                "p_down": float(r["p_down"]),
                "composite": float(r["composite"]),
                "p_stay": float(r["p_stay"]),
                "forecast": float(r["forecast"]),
            }
            for _, r in sl_frame.iterrows()
        ],
    }
    print(f"[wi009c] shortlist: {len(shortlist['rows'])} names as of {shortlist['as_of_date']} "
          f"ranked by P(up)-P(down)")

    # ---- Step 3a: gated fold-safe contrastive candidate -------------------- #
    contrastive = None
    if args.contrastive:
        uniq_dates = np.sort(pd.unique(panel["date"].to_numpy()))
        contrastive = contrastive_status(args.market, uniq_dates, frame["date"].unique(), args.embargo_td)
        print(f"[wi009c] contrastive candidate: {contrastive['status']} — {contrastive['reason']}")
        if contrastive["run"]:
            from src.models.contrastive_ranking import load_model

            model, feature_cols = load_model(CONTRASTIVE_ARTIFACT)
            scores = contrastive_scores_for_panel(args.market, panel, model, feature_cols)
            folds_c = run_folds(panel, args, extra_scores=scores, label="stacked")
            contrastive["stacked_skill"] = score_skill(folds_c["frame"])
            s = contrastive["stacked_skill"]
            print(f"[wi009c] stacked skill: IC {_fmt(s['model_ic'])} (t {_fmt(s['model_t'], '+.2f')}) "
                  f"— {'PASS' if s['passed'] else 'NEGATIVE RESULT'}")

    # ---- Step 4: evidence-gated robustness options (no body is built) ------- #
    robustness = None
    if (args.robustness_report or args.robustness_regime
            or args.robustness_stacking or args.robustness_dynamic):
        robustness = run_robustness_gates(args, skill, contrastive, panel, frame)

    ctx = {
        "market": args.market,
        "smoke": bool(args.smoke),
        "n_rows": int(len(panel)),
        "n_symbols": int(panel["symbol"].nunique()),
        "n_dates": int(panel["date"].nunique()),
        "date_min": str(panel["date"].min().date()),
        "date_max": str(panel["date"].max().date()),
        "n_splits": int(args.n_splits),
        "embargo_td": int(args.embargo_td),
        "calib_fraction": float(args.calib_fraction),
        "fold_records": folds["fold_records"],
        "n_oof_rows": folds["n_oof_rows"],
        "n_viable_folds": folds["n_viable_folds"],
        "elapsed_s": folds["elapsed_s"],
        "skill": skill,
        "calibration": calibration,
        "residual_quantiles": resid_q,
        "shortlist": shortlist,
        "contrastive": contrastive,
    }

    # `--smoke` outputs are namespaced so a bounded smoke run can never overwrite the
    # production artifacts that Step 5 evaluates (explicit --*-out paths still win).
    suffix = "_smoke" if args.smoke else ""
    shortlist_out = (
        Path(args.shortlist_out) if args.shortlist_out
        else REPORTS / f"wi009c_shortlist_{args.market}{suffix}.csv"
    )
    shortlist_out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(shortlist["rows"]).to_csv(shortlist_out, index=False)
    print(f"[wi009c] wrote {shortlist_out}")

    report = Path(args.report) if args.report else REPORTS / f"wi009c_regression{suffix}.md"
    write_report(ctx, report)
    print(f"[wi009c] wrote {report}")

    oof_out = Path(args.oof_out) if args.oof_out else DATA / f"wi009c_oof_{args.market}{suffix}.parquet"
    oof_out.parent.mkdir(parents=True, exist_ok=True)
    out_frame = frame.copy()
    out_frame["composite"] = out_frame["p_up"].astype("float64") - out_frame["p_down"].astype("float64")
    for c in ("forecast", "y", "atr_pct", "p_up", "p_down", "p_stay", "p_stay_exclusive",
              "overlap_up_stay", "overlap_down_stay", "composite"):
        out_frame[c] = out_frame[c].astype("float32")
    out_frame.to_parquet(oof_out, index=False)
    print(f"[wi009c] wrote {oof_out} ({len(out_frame):,} rows)")

    json_out = Path(args.json_out) if args.json_out else REPORTS / f"wi009c_regression_{args.market}{suffix}.json"
    record = {
        "market": args.market,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "smoke": bool(args.smoke),
        "config": {
            "n_splits": int(args.n_splits),
            "embargo_td": int(args.embargo_td),
            "calib_fraction": float(args.calib_fraction),
            "alpha": float(args.alpha),
            "max_dates": int(args.max_dates),
            "features": E5_COLS,
            "continuous_target": CONTINUOUS_TARGET,
            "atr_price_column": ATR_PRICE_COLUMN,
            "up_mult": UP_MULT,
            "down_mult": DOWN_MULT,
            "stay_ret_max": STAY_RET_MAX,
        },
        "panel": {k: ctx[k] for k in ("n_rows", "n_symbols", "n_dates", "date_min", "date_max")},
        "folds": folds["fold_records"],
        "n_oof_rows": folds["n_oof_rows"],
        "n_viable_folds": folds["n_viable_folds"],
        "residual_quantiles": resid_q,
        "calibration_masses": calibration["masses"],
        "calibration": {k: calibration[k] for k in ("up", "down", "stay", "stay_exclusive")},
        "skill": {
            "model_ic": skill["model_ic"],
            "model_t": skill["model_t"],
            "n_dates": skill["n_dates"],
            "best_factor": skill["best_factor"],
            "best_abs_ic": skill["best_abs_ic"],
            "same_sign": skill["same_sign"],
            "pass_a": skill["pass_a"],
            "pass_b": skill["pass_b"],
            "passed": skill["passed"],
            "factor_table": {k: {"ic": vv[0], "t": vv[1], "n_dates": vv[2]}
                             for k, vv in skill["factor_stats"].items()},
            "caveats": skill["verdict"].get("caveats", []),
        },
        "shortlist": shortlist,
        "contrastive_candidate": contrastive,
        "robustness": robustness,
        "elapsed_s": time.time() - t_start,
    }
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(record, indent=2, default=str) + "\n")
    print(f"[wi009c] wrote {json_out}")
    print(f"[wi009c] DONE in {time.time() - t_start:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
