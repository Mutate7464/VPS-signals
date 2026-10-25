"""WI-009c Steps 2–3 — continuous-target event probabilities, fold plan, shortlist.

Why this module exists
----------------------
WI-009c routes the CAD up/down/stay question through **one continuous 20-trading-day
forecast** instead of three independent binary classifiers (ADR D-010, fixed admin
design). Everything that turns that forecast into probabilities lives here so it can
be unit-tested on synthetic arrays without touching the 2 vCPU / 8 GB host budget or
the CAD artifacts:

* **Event units.** The three band events are defined in two different unit systems
  (`src/targets.compute_targets`) and must be mapped into the continuous target's own
  units before any probability is computed:

      continuous target   fwd_atr_ret_20 = (close.shift(-20) - close) / wilder_atr_20
      up     event        fwd_atr_ret_20 >= +TREND_ATR_MULT          (2x ATR, dollar)
      down   event        fwd_atr_ret_20 <= -TREND_ATR_MULT
      stay   event        |close.shift(-20)/close - 1| <= STAY_RET_MAX   (+/-5%, relative)
                          <=> |fwd_atr_ret_20| * atr_pct_20 <= STAY_RET_MAX
                          <=> |fwd_atr_ret_20| <= STAY_RET_MAX / atr_pct_20

  The stay threshold is therefore *row-specific*: the ATR/price ratio
  (`atr_pct_20`, the column named in Step 0) is what converts a relative 5% band into
  the ATR-multiple space the regressor predicts in.

* **Overlap is preserved, never silently partitioned.** The raw up/down and stay
  events are *not* mutually exclusive (a small `atr_pct_20` makes 2x ATR smaller than
  5%), so each probability is integrated independently from the same residual
  distribution. `P(stay)` is the raw +/-5% event; `P(stay) exclusive` additionally
  excludes the up/down events, mirroring the `y_20d_stay` label definition. The sum
  `P(up) + P(down) + P(stay)` may exceed 1 and that is reported, not hidden.

* **Split-calibration residual empirical CDF** (ADR D-010): per fold the last
  `CALIB_FRACTION` of the *training* dates (purged by the 20td embargo from the fit
  block) is held out, the regressor is fit on the remaining training dates, and the
  held-out residuals form the empirical CDF. The shifted CDF is then integrated over
  each row's event interval. This is a **marginal** forecast distribution: it does not
  guarantee conditional calibration per row or regime.

* **Fold-safe stacking** (Step 3): `fold_safe_cutoff` / `contrastive_candidate_decision`
  encode the rule that a pre-trained score may only be used as a stacked input when
  its training cutoff is provably more than `EMBARGO_TD` trading days before *every*
  held-out fold date — otherwise the candidate is omitted and documented, never fed
  in-sample.

Pure numpy/pandas: no torch, no xgboost at import time (the splitter is imported
lazily inside `purged_fold_plan`), so the tests are cheap.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.factors.e5_baseline import E5_FACTORS
from src.models.skill_bar import EMBARGO_TD
from src.targets import ATR_WINDOW, STAY_RET_MAX, TREND_ATR_MULT, TREND_HORIZON

__all__ = [
    "ATR_PRICE_COLUMN",
    "CALIB_FRACTION",
    "CONTINUOUS_TARGET",
    "DEFAULT_N_SPLITS",
    "DOWN_MULT",
    "E5_FACTORS",
    "EMBARGO_TD",
    "INITIAL_TRAIN_FRACTION",
    "STAY_RET_MAX",
    "UP_MULT",
    "assert_fold_safe",
    "calibration_summary",
    "composite_score",
    "contrastive_candidate_decision",
    "event_probabilities",
    "event_thresholds",
    "fold_safe_cutoff",
    "marginal_calibration",
    "purged_fit_calibration_split",
    "purged_fold_plan",
    "realized_events",
    "shortlist_frame",
    "stacked_input_matrix",
    "step1_permits_feature_spend",
]

# --------------------------------------------------------------------------- #
# Route constants (Step 0 named these; never silently substituted)
# --------------------------------------------------------------------------- #
CONTINUOUS_TARGET = f"fwd_atr_ret_{TREND_HORIZON}"  # "fwd_atr_ret_20"
ATR_PRICE_COLUMN = "atr_pct_20"  # wilder_atr(df, 20) / close, in features_{MKT}.parquet
UP_MULT = float(TREND_ATR_MULT)  # +2x ATR, dollar-based
DOWN_MULT = -float(TREND_ATR_MULT)  # -2x ATR, dollar-based

# Split + calibration policy. Mirrors `src.xgb_trainer` (CALIB_FRACTION /
# INITIAL_TRAIN_FRACTION) so the WI-009c route keeps the established discipline;
# `tests/test_wi009c_continuous.py` asserts the mirror, and `purged_fold_plan`
# imports the splitter itself rather than re-implementing it.
DEFAULT_N_SPLITS = 5
CALIB_FRACTION = 0.20
INITIAL_TRAIN_FRACTION = 0.40


# --------------------------------------------------------------------------- #
# Event definitions in the continuous target's units
# --------------------------------------------------------------------------- #
def event_thresholds(forecast, atr_pct) -> dict[str, np.ndarray]:
    """The three band thresholds, expressed in the continuous target's units.

    Args:
        forecast: (n,) predicted `fwd_atr_ret_20` (ATR multiples). Only used for shape.
        atr_pct: (n,) `atr_pct_20` = wilder_atr_20 / close, finite and > 0.

    Returns:
        dict with ``up`` (+2.0), ``down`` (-2.0) and ``stay_abs`` (row-specific
        ``STAY_RET_MAX / atr_pct``) thresholds in ATR-multiple units.
    """
    f = np.asarray(forecast, dtype="float64").ravel()
    a = np.asarray(atr_pct, dtype="float64").ravel()
    if f.shape != a.shape:
        raise ValueError(f"forecast {f.shape} and atr_pct {a.shape} must align")
    _require_usable_atr_pct(a)
    return {
        "up": np.full(f.shape, UP_MULT, dtype="float64"),
        "down": np.full(f.shape, DOWN_MULT, dtype="float64"),
        "stay_abs": STAY_RET_MAX / a,
    }


def _require_usable_atr_pct(a: np.ndarray) -> None:
    bad = ~np.isfinite(a) | (a <= 0.0)
    if bad.any():
        raise ValueError(
            f"atr_pct must be finite and > 0 to convert the relative +/-{STAY_RET_MAX:.0%} "
            f"stay band into target units; {int(bad.sum())} of {a.size} rows are unusable"
        )


def _sorted_finite(residuals) -> np.ndarray:
    r = np.asarray(residuals, dtype="float64").ravel()
    r = r[np.isfinite(r)]
    if r.size == 0:
        raise ValueError("no finite calibration residuals: the empirical CDF is undefined")
    return np.sort(r)


def event_probabilities(
    forecast,
    residuals,
    atr_pct,
    up_mult: float = UP_MULT,
    stay_ret_max: float = STAY_RET_MAX,
) -> dict[str, np.ndarray]:
    """Row-level P(up), P(down), P(stay) from the split-calibration residual ECDF.

    The forecast is the centre of a distribution whose shape is the held-out
    residual sample: ``move = forecast + residual``. Each event is integrated
    independently, so overlap between the +/-5% stay band and the 2x ATR up/down
    events is *preserved* (never forced into a partition).

    Args:
        forecast: (n,) predicted continuous target (ATR multiples).
        residuals: (m,) calibration residuals (`y - forecast` on held-out dates only).
        atr_pct: (n,) `atr_pct_20`, finite and > 0.
        up_mult: up/down threshold in ATR multiples (+2.0 by the fixed route).
        stay_ret_max: relative stay band (+/-0.05 by the fixed route).

    Returns:
        dict of (n,) float64 arrays, all finite and within [0, 1]:
        ``p_up``, ``p_down``, ``p_stay`` (raw +/-5% event),
        ``p_stay_exclusive`` (stay and not up and not down — the `y_20d_stay`
        definition), ``overlap_up_stay``, ``overlap_down_stay``.
    """
    f = np.asarray(forecast, dtype="float64").ravel()
    a = np.asarray(atr_pct, dtype="float64").ravel()
    if f.shape != a.shape:
        raise ValueError(f"forecast {f.shape} and atr_pct {a.shape} must align")
    _require_usable_atr_pct(a)
    rs = _sorted_finite(residuals)
    n = float(rs.size)
    stay_abs = stay_ret_max / a

    # move >= +up_mult  <=>  residual >= up_mult - forecast
    up_thr = up_mult - f
    # move <= -up_mult  <=>  residual <= -up_mult - forecast
    down_thr = -up_mult - f
    # |move| <= stay_abs  <=>  residual in [-stay_abs - f, stay_abs - f]
    lo = -stay_abs - f
    hi = stay_abs - f

    p_up = (n - np.searchsorted(rs, up_thr, side="left")) / n
    p_down = np.searchsorted(rs, down_thr, side="right") / n
    hi_i = np.searchsorted(rs, hi, side="right")
    lo_i = np.searchsorted(rs, lo, side="left")
    p_stay = (hi_i - lo_i) / n

    # Overlap masses: the stay interval intersected with each up/down half-line.
    up_ov = _count_between(rs, np.maximum(up_thr, lo), hi) / n
    down_ov = _count_between(rs, lo, np.minimum(down_thr, hi)) / n
    p_stay_excl = p_stay - up_ov - down_ov

    out = {
        "p_up": p_up,
        "p_down": p_down,
        "p_stay": p_stay,
        "p_stay_exclusive": p_stay_excl,
        "overlap_up_stay": up_ov,
        "overlap_down_stay": down_ov,
    }
    for k, v in out.items():
        out[k] = np.clip(np.nan_to_num(v, nan=0.0), 0.0, 1.0)
    return out


def _count_between(rs: np.ndarray, lo, hi) -> np.ndarray:
    """Count of sorted `rs` values in the closed interval [lo, hi] (0 when lo > hi)."""
    lo = np.asarray(lo, dtype="float64")
    hi = np.asarray(hi, dtype="float64")
    n_hi = np.searchsorted(rs, hi, side="right")
    n_lo = np.searchsorted(rs, lo, side="left")
    return np.clip(n_hi - n_lo, 0, None).astype("float64")


def realized_events(y, atr_pct, up_mult: float = UP_MULT, stay_ret_max: float = STAY_RET_MAX) -> dict[str, np.ndarray]:
    """The *realized* band events for the same rows, mirroring `src.targets.compute_targets`.

    Used only for calibration diagnostics (predicted vs realized), never as a
    training target and never as a class-label score.
    """
    yy = np.asarray(y, dtype="float64").ravel()
    a = np.asarray(atr_pct, dtype="float64").ravel()
    if yy.shape != a.shape:
        raise ValueError(f"y {yy.shape} and atr_pct {a.shape} must align")
    _require_usable_atr_pct(a)
    up = yy >= up_mult
    down = yy <= -up_mult
    stay = np.abs(yy) * a <= stay_ret_max
    return {
        "up": up,
        "down": down,
        "stay": stay,
        "stay_exclusive": stay & ~up & ~down,
    }


def composite_score(p_up, p_down) -> np.ndarray:
    """The declared shortlist composite: `P(up) - P(down)`."""
    return np.asarray(p_up, dtype="float64") - np.asarray(p_down, dtype="float64")


def shortlist_frame(
    oof: pd.DataFrame,
    as_of_date=None,
    top_n: int = 20,
    composite_col: str = "composite",
) -> pd.DataFrame:
    """Deterministic daily shortlist ranked by `P(up) - P(down)`.

    Args:
        oof: per-row frame with `date`, `symbol`, `p_up`, `p_down`, `p_stay`
            (and optionally `forecast`).
        as_of_date: the date to rank; defaults to the latest date carrying a
            finite composite.
        top_n: shortlist length.
        composite_col: name of the composite column to rank on.

    Returns:
        The top `top_n` rows for that date, ordered by composite descending with
        `symbol` ascending as the deterministic tie-break. `P(stay)` is carried
        alongside and is never used as a tie-break.
    """
    for col in ("date", "symbol", "p_up", "p_down", "p_stay"):
        if col not in oof.columns:
            raise KeyError(f"oof frame missing column {col!r}")
    df = oof.copy()
    df[composite_col] = composite_score(df["p_up"].to_numpy(), df["p_down"].to_numpy())
    df = df[np.isfinite(df[composite_col].to_numpy())]
    if df.empty:
        raise ValueError("no finite composite values to rank")
    if as_of_date is None:
        as_of = df["date"].max()
    else:
        as_of = pd.Timestamp(as_of_date)
    day = df[df["date"] == as_of]
    if day.empty:
        raise ValueError(f"no rows for as_of_date={as_of}")
    day = day.sort_values([composite_col, "symbol"], ascending=[False, True], kind="stable")
    out = day.head(int(top_n)).reset_index(drop=True)
    out.insert(0, "rank", np.arange(1, len(out) + 1))
    return out


# --------------------------------------------------------------------------- #
# Purged fold plan with a split-calibration block
# --------------------------------------------------------------------------- #
def purged_fit_calibration_split(
    train_positions,
    calib_fraction: float = CALIB_FRACTION,
    embargo_td: int = EMBARGO_TD,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Split training *date positions* into (fit, calibration) with a purge gap.

    The calibration block is the last `calib_fraction` of the training positions;
    every fit position within `embargo_td` of the calibration block is dropped, so
    the purge gap is `>= embargo_td` by construction. The calibration rows are
    therefore excluded from the model's training dates, which is exactly what makes
    the residual empirical CDF a held-out quantity.

    Returns:
        (fit_positions, calibration_positions, gap) where `gap` is the number of
        unique dates strictly between the last fit position and the first
        calibration position (-1 when either block is empty).
    """
    if not 0.0 < calib_fraction < 1.0:
        raise ValueError(f"calib_fraction must be in (0, 1), got {calib_fraction}")
    if embargo_td < 0:
        raise ValueError(f"embargo_td must be >= 0, got {embargo_td}")
    tr = np.sort(np.unique(np.asarray(train_positions, dtype=int)))
    if tr.size == 0:
        return tr, tr, -1
    cut = int(tr.size * (1.0 - calib_fraction))
    fit_pos, cal_pos = tr[:cut], tr[cut:]
    if cal_pos.size and fit_pos.size:
        fit_pos = fit_pos[fit_pos <= int(cal_pos[0]) - embargo_td - 1]
    gap = int(cal_pos[0] - fit_pos[-1] - 1) if (cal_pos.size and fit_pos.size) else -1
    return fit_pos, cal_pos, gap


def purged_fold_plan(
    uniq_dates,
    n_splits: int = DEFAULT_N_SPLITS,
    embargo_td: int = EMBARGO_TD,
    calib_fraction: float = CALIB_FRACTION,
    initial_train_fraction: float = INITIAL_TRAIN_FRACTION,
) -> list[dict]:
    """Chronological purged walk-forward plan over *sorted unique dates*.

    Reuses `src.xgb_trainer.PurgedWalkForwardSplit` unchanged (the WI-009 discipline:
    positions into the sorted unique date array, never `pd.factorize` codes) and adds
    the per-fold split-calibration block. Each record carries the positions, the date
    strings, both purge gaps and a `purge_ok` assertion so leakage evidence is
    reportable without re-deriving it.

    Returns:
        list of fold records. A record with a `skipped` key has no usable blocks and
        contributes no rows (e.g. the early folds of a short smoke window).
    """
    from src.xgb_trainer import PurgedWalkForwardSplit

    uniq = np.sort(pd.unique(np.asarray(uniq_dates)))
    if uniq.size < 3:
        raise ValueError(f"need >= 3 unique dates, got {uniq.size}")
    splitter = PurgedWalkForwardSplit(
        n_splits=n_splits, embargo_td=embargo_td, initial_train_fraction=initial_train_fraction
    )

    def d(i: int) -> str:
        return str(pd.Timestamp(uniq[int(i)]).date())

    plan: list[dict] = []
    for k, (tr_pos, va_pos) in enumerate(splitter.split(uniq)):
        tr_pos = np.sort(np.unique(np.asarray(tr_pos, dtype=int)))
        va_pos = np.sort(np.unique(np.asarray(va_pos, dtype=int)))
        rec: dict = {"fold": int(k), "val_pos": va_pos, "n_val_dates": int(va_pos.size)}
        if tr_pos.size == 0 or va_pos.size == 0:
            rec["skipped"] = "empty train or validation block"
            plan.append(rec)
            continue

        fit_pos, cal_pos, gap_fit_cal = purged_fit_calibration_split(
            tr_pos, calib_fraction=calib_fraction, embargo_td=embargo_td
        )
        rec.update(
            {
                "fit_pos": fit_pos,
                "cal_pos": cal_pos,
                "n_fit_dates": int(fit_pos.size),
                "n_cal_dates": int(cal_pos.size),
                "gap_fit_cal": int(gap_fit_cal),
                "train_min": d(tr_pos[0]),
                "train_max": d(tr_pos[-1]),
                "val_min": d(va_pos[0]),
                "val_max": d(va_pos[-1]),
            }
        )
        if fit_pos.size == 0 or cal_pos.size == 0:
            rec["skipped"] = "purge emptied the fit or calibration block"
            plan.append(rec)
            continue

        gap_fit_val = int(va_pos[0] - fit_pos[-1] - 1)
        gap_cal_val = int(va_pos[0] - cal_pos[-1] - 1)
        rec.update(
            {
                "fit_min": d(fit_pos[0]),
                "fit_max": d(fit_pos[-1]),
                "cal_min": d(cal_pos[0]),
                "cal_max": d(cal_pos[-1]),
                "gap_fit_val": gap_fit_val,
                "gap_cal_val": gap_cal_val,
                # Calibration residuals are drawn from dates that are neither fit
                # dates nor validation dates, and every gap respects the embargo.
                "purge_ok": bool(
                    gap_fit_cal >= embargo_td and gap_fit_val >= embargo_td and gap_cal_val >= 0
                ),
            }
        )
        plan.append(rec)
    return plan


# --------------------------------------------------------------------------- #
# Step-3 fold-safety rules
# --------------------------------------------------------------------------- #
def fold_safe_cutoff(
    cutoff_date,
    val_dates,
    calendar_dates,
    embargo_td: int = EMBARGO_TD,
) -> tuple[bool, list[str]]:
    """Is a model whose training cutoff is `cutoff_date` fold-safe for `val_dates`?

    Fold-safe means *every* held-out date is more than `embargo_td` trading days
    after the cutoff, i.e. `val_pos > cutoff_pos + embargo_td` on the trading
    calendar — the same positional rule the splitter uses
    (`max_train_pos + embargo_td < min_val_pos`).

    Returns:
        (is_safe, offenders) where `offenders` lists the held-out dates that fail
        (empty when safe).
    """
    cal = np.sort(pd.unique(np.asarray(calendar_dates)))
    if cal.size == 0:
        raise ValueError("empty trading calendar")
    cut_pos = int(np.searchsorted(cal, np.datetime64(pd.Timestamp(cutoff_date))))
    val = pd.to_datetime(pd.Series(list(val_dates))).to_numpy()
    val_pos = np.searchsorted(cal, val)
    bad = val_pos <= cut_pos + int(embargo_td)
    offenders = [str(pd.Timestamp(v).date()) for v in val[bad]]
    return (not bool(bad.any())), offenders


def assert_fold_safe(cutoff_date, val_dates, calendar_dates, embargo_td: int = EMBARGO_TD) -> None:
    """Raise `ValueError` when a score model's cutoff is not fold-safe (Step 3(d))."""
    ok, offenders = fold_safe_cutoff(cutoff_date, val_dates, calendar_dates, embargo_td)
    if not ok:
        raise ValueError(
            f"model cutoff {pd.Timestamp(cutoff_date).date()} is not fold-safe: "
            f"{len(offenders)} held-out date(s) are within {embargo_td}td of it "
            f"(first: {offenders[0]}). An in-sample score must never be fed."
        )


STEP1_PERMISSION_SENTENCE = "permission for one 89-feature continuous run"


def step1_permits_feature_spend(probe_report_text: str) -> bool:
    """Fail-closed read of the Step-1 gate line in `reports/wi009c_probe.md`.

    Step 1(d) permits 89-feature / optional-candidate spend only when at least one
    label cleared the unchanged skill bar. Anything other than the explicit
    permission sentence is treated as *no permission*.
    """
    return STEP1_PERMISSION_SENTENCE in (probe_report_text or "")


def contrastive_candidate_decision(
    probe_report_text: str,
    artifact_train_max_date,
    val_dates,
    calendar_dates,
    embargo_td: int = EMBARGO_TD,
) -> dict:
    """Decide whether the fold-safe contrastive stacked input may run.

    Two independent gates, in plan order:

    1. Step 1(d): 89-feature / optional-candidate spend is permitted only if the
       probe cleared the skill bar. The contrastive score is an 89-feature model
       output, so this gate alone can stop the candidate.
    2. Step 3(a)/(d): the score must be fold-safe — produced by weights that never
       saw a held-out date. A saved artifact is only acceptable when its recorded
       training cutoff is more than `embargo_td` trading days before *every*
       held-out date; otherwise per-fold refitting is required (89-feature spend).

    Returns:
        dict with `run` (bool), `status`, `reason`, `step1_permits_feature_spend`,
        `fold_safe` and `offenders`. When `run` is False the candidate is omitted
        and the reason is the documented negative result — never a silent skip.
    """
    permitted = step1_permits_feature_spend(probe_report_text)
    out = {
        "step1_permits_feature_spend": bool(permitted),
        "artifact_train_max_date": str(pd.Timestamp(artifact_train_max_date).date()),
        "embargo_td": int(embargo_td),
        "run": False,
        "fold_safe": None,
        "offenders": [],
        "status": "NOT RUN",
        "reason": "",
    }
    if not permitted:
        out["reason"] = (
            "Step 1 gate (plan Step 1(d)): no label cleared the unchanged skill bar, so the "
            "89-feature spend and all optional candidates stay gated; the contrastive score is "
            "an 89-feature model output, so it is omitted and documented, not run."
        )
        return out

    ok, offenders = fold_safe_cutoff(artifact_train_max_date, val_dates, calendar_dates, embargo_td)
    out["fold_safe"] = bool(ok)
    out["offenders"] = offenders
    if not ok:
        out["reason"] = (
            f"fold-safe scoring could not be established (plan Step 3(d)): the saved artifact's "
            f"recorded training cutoff {out['artifact_train_max_date']} is within {embargo_td}td of "
            f"{len(offenders)} held-out fold date(s) (first: {offenders[0]}). Scoring those dates "
            "would feed an in-sample score, and per-fold refitting is 89-feature spend gated by "
            "Step 1. Candidate omitted."
        )
        return out

    out["run"] = True
    out["status"] = "RUN"
    out["reason"] = (
        f"Step 1 permitted feature spend and the artifact cutoff "
        f"{out['artifact_train_max_date']} is > {embargo_td}td before every held-out date."
    )
    return out


def stacked_input_matrix(base_x, extra_scores) -> np.ndarray:
    """Column-stack a fold-safe score onto the base feature matrix, float32.

    The contrastive score is *one additional candidate input*; it never replaces
    the continuous model and never becomes the final ranking.
    """
    b = np.asarray(base_x, dtype="float32")
    e = np.asarray(extra_scores, dtype="float32").reshape(len(b), -1)
    if b.shape[0] != e.shape[0]:
        raise ValueError(f"base rows {b.shape[0]} != score rows {e.shape[0]}")
    return np.ascontiguousarray(np.hstack([b, e]), dtype="float32")


# --------------------------------------------------------------------------- #
# Calibration diagnostics
# --------------------------------------------------------------------------- #
def calibration_summary(pred, realized, n_bins: int = 10) -> dict:
    """Marginal calibration of one predicted probability against its realized event.

    Returns mean predicted vs realized rate, the bias, the Brier score and a
    reliability table (equal-count bins of the predicted probability). This is a
    *marginal* diagnostic: it says nothing about conditional calibration per row,
    symbol or regime, which is reported as a limitation.
    """
    p = np.asarray(pred, dtype="float64").ravel()
    z = np.asarray(realized, dtype="float64").ravel()
    if p.shape != z.shape:
        raise ValueError(f"pred {p.shape} and realized {z.shape} must align")
    m = np.isfinite(p) & np.isfinite(z)
    p, z = p[m], z[m]
    if p.size == 0:
        return {
            "n": 0, "mean_predicted": float("nan"), "realized_rate": float("nan"),
            "bias": float("nan"), "brier": float("nan"), "bins": [],
        }
    out = {
        "n": int(p.size),
        "mean_predicted": float(p.mean()),
        "realized_rate": float(z.mean()),
        "bias": float(p.mean() - z.mean()),
        "brier": float(np.mean((p - z) ** 2)),
        "bins": [],
    }
    edges = np.unique(np.quantile(p, np.linspace(0.0, 1.0, int(n_bins) + 1)))
    if edges.size < 3:
        return out
    idx = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, edges.size - 2)
    for b in range(edges.size - 1):
        sel = idx == b
        if not sel.any():
            continue
        out["bins"].append(
            {
                "bin": int(b) + 1,
                "n": int(sel.sum()),
                "lo": float(edges[b]),
                "hi": float(edges[b + 1]),
                "mean_predicted": float(p[sel].mean()),
                "realized_rate": float(z[sel].mean()),
            }
        )
    return out


def marginal_calibration(pred: dict, y, atr_pct, n_bins: int = 10) -> dict:
    """Marginal calibration for all three events on the same scored rows.

    `pred` is the `event_probabilities` output; `y` is the realized continuous
    target. Returns per-event summaries plus the overlap diagnostics, so the report
    can state plainly that `P(up) + P(down) + P(stay)` need not sum to 1.
    """
    real = realized_events(y, atr_pct)
    out = {
        "up": calibration_summary(pred["p_up"], real["up"].astype("float64"), n_bins),
        "down": calibration_summary(pred["p_down"], real["down"].astype("float64"), n_bins),
        "stay": calibration_summary(pred["p_stay"], real["stay"].astype("float64"), n_bins),
        "stay_exclusive": calibration_summary(
            pred["p_stay_exclusive"], real["stay_exclusive"].astype("float64"), n_bins
        ),
    }
    p_up, p_dn, p_st = pred["p_up"], pred["p_down"], pred["p_stay"]
    out["masses"] = {
        "mean_p_up": float(np.mean(p_up)),
        "mean_p_down": float(np.mean(p_dn)),
        "mean_p_stay": float(np.mean(p_st)),
        "mean_p_stay_exclusive": float(np.mean(pred["p_stay_exclusive"])),
        "mean_sum_up_down_stay": float(np.mean(p_up + p_dn + p_st)),
        "mean_overlap_up_stay": float(np.mean(pred["overlap_up_stay"])),
        "mean_overlap_down_stay": float(np.mean(pred["overlap_down_stay"])),
        "realized_rate_up": float(np.mean(real["up"])),
        "realized_rate_down": float(np.mean(real["down"])),
        "realized_rate_stay": float(np.mean(real["stay"])),
        "realized_rate_stay_exclusive": float(np.mean(real["stay_exclusive"])),
    }
    return out


def residual_quantiles(residuals) -> dict:
    """Quantiles of the calibration residual sample (the ECDF's shape)."""
    r = np.asarray(residuals, dtype="float64").ravel()
    r = r[np.isfinite(r)]
    if r.size == 0:
        return {"n": 0}
    qs = [0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]
    vals = np.quantile(r, qs)
    out = {"n": int(r.size), "mean": float(r.mean()), "std": float(r.std(ddof=1)) if r.size > 1 else float("nan")}
    for q, v in zip(qs, vals):
        out[f"q{int(q * 100):02d}"] = float(v)
    return out


def mirror_check() -> dict:
    """Confirm the local split/calibration policy still mirrors `src.xgb_trainer`."""
    from src.xgb_trainer import CALIB_FRACTION as xf, INITIAL_TRAIN_FRACTION as xi

    return {
        "calib_fraction_matches_xgb_trainer": bool(CALIB_FRACTION == xf),
        "initial_train_fraction_matches_xgb_trainer": bool(INITIAL_TRAIN_FRACTION == xi),
        "atr_window_matches_targets": bool(ATR_WINDOW == 20),
        "trend_horizon_matches_targets": bool(TREND_HORIZON == 20),
    }
