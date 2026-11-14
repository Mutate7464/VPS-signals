"""WI-009c Step 3 — fold-safe contrastive stacked input and the shortlist composite.

Locks the acceptance criteria of
`docs/plans/2026-10-25-WI-009c-classifier-route.md` Step 3(b):

* no held-out date contributes to its score model (fold-safety is enforced, and an
  in-sample score is refused);
* baseline and stacked results are comparable on identical folds;
* the output composite is finite and the shortlist ordering matches the declared
  formula `P(up)-P(down)`, with `P(stay)` reported but never a tie-break.
"""
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from src.models.continuous_targets import (
    ATR_PRICE_COLUMN,
    CONTINUOUS_TARGET,
    EMBARGO_TD,
    assert_fold_safe,
    contrastive_candidate_decision,
    fold_safe_cutoff,
    purged_fold_plan,
    shortlist_frame,
    stacked_input_matrix,
    step1_permits_feature_spend,
)
from src.models.skill_bar import EMBARGO_TD as SKILL_EMBARGO_TD

from scripts.train_wi009c import E5_COLS, run_folds, score_skill

PERMITTED_TEXT = (
    "- **Step 2 gate:** permission for one 89-feature continuous run "
    "(permission, not a claim of skill).\n"
)
BLOCKED_TEXT = (
    "- **Step 2 gate:** no label demonstrated learnable — no 89-feature spend; "
    "limit the continuous baseline to the same five factors.\n"
)


def _biz_dates(n: int, start: str = "2019-01-01") -> np.ndarray:
    return np.sort(pd.to_datetime(pd.date_range(start, periods=n, freq="B")).to_numpy())


# --------------------------------------------------------------------------- #
# Step-1 gate is fail-closed
# --------------------------------------------------------------------------- #
def test_step1_gate_requires_the_explicit_permission_sentence():
    assert step1_permits_feature_spend(PERMITTED_TEXT) is True
    assert step1_permits_feature_spend(BLOCKED_TEXT) is False
    assert step1_permits_feature_spend("") is False
    assert step1_permits_feature_spend("some unrelated report body") is False


def test_the_recorded_step1_probe_blocks_feature_spend():
    """The real `reports/wi009c_probe.md` recorded 0/5 labels clearing the bar."""
    from pathlib import Path

    probe = Path(__file__).resolve().parents[1] / "reports" / "wi009c_probe.md"
    if not probe.exists():
        pytest.skip("probe report not present")
    assert step1_permits_feature_spend(probe.read_text()) is False


def test_contrastive_candidate_is_omitted_when_the_step1_gate_blocks():
    d = contrastive_candidate_decision(
        BLOCKED_TEXT, "2026-05-28", _biz_dates(60, "2020-01-01"), _biz_dates(400, "2019-01-01")
    )
    assert d["run"] is False
    assert d["status"] == "NOT RUN"
    assert d["step1_permits_feature_spend"] is False
    assert "Step 1" in d["reason"]
    # the fold-safety question is not even reached: no 89-feature spend is allowed
    assert d["fold_safe"] is None


# --------------------------------------------------------------------------- #
# fold-safety of a saved artifact
# --------------------------------------------------------------------------- #
def test_fold_safe_cutoff_uses_the_positional_20td_rule():
    cal = _biz_dates(300)
    cutoff = cal[100]
    safe, offenders = fold_safe_cutoff(cutoff, [cal[120]], cal, EMBARGO_TD)
    assert safe is False and len(offenders) == 1  # exactly 20 trading days later
    safe, offenders = fold_safe_cutoff(cutoff, [cal[121]], cal, EMBARGO_TD)
    assert safe is True and offenders == []


def test_assert_fold_safe_refuses_an_in_sample_score():
    cal = _biz_dates(300)
    with pytest.raises(ValueError):
        assert_fold_safe(cal[100], [cal[101], cal[250]], cal, EMBARGO_TD)
    assert_fold_safe(cal[100], [cal[250]], cal, EMBARGO_TD) is None


def test_contrastive_candidate_is_omitted_when_the_cutoff_is_not_fold_safe():
    cal = _biz_dates(400)
    d = contrastive_candidate_decision(PERMITTED_TEXT, cal[200], [cal[210], cal[300]], cal, EMBARGO_TD)
    assert d["run"] is False and d["status"] == "NOT RUN"
    assert d["fold_safe"] is False and d["offenders"]
    assert "fold-safe" in d["reason"] and "Step 3(d)" in d["reason"]


def test_contrastive_candidate_runs_only_when_the_cutoff_precedes_every_held_out_date():
    cal = _biz_dates(400)
    d = contrastive_candidate_decision(PERMITTED_TEXT, cal[100], [cal[150], cal[300]], cal, EMBARGO_TD)
    assert d["run"] is True and d["status"] == "RUN" and d["fold_safe"] is True


@pytest.mark.parametrize("cutoff_pos", [10, 50, 100, 150, 200])
def test_a_run_decision_always_implies_every_held_out_date_is_beyond_the_embargo(cutoff_pos):
    """Property: `run=True` can never coexist with a held-out date inside the embargo."""
    cal = _biz_dates(400)
    val_dates = [cal[cutoff_pos + 5], cal[cutoff_pos + 30], cal[-1]]
    d = contrastive_candidate_decision(PERMITTED_TEXT, cal[cutoff_pos], val_dates, cal, EMBARGO_TD)
    if d["run"]:
        ok, offenders = fold_safe_cutoff(cal[cutoff_pos], val_dates, cal, EMBARGO_TD)
        assert ok is True and offenders == []
    else:
        assert d["status"] == "NOT RUN" and d["offenders"]


def test_no_held_out_date_contributes_to_a_per_fold_score_model():
    """Every fold's score model is fit on the fit block only — disjoint from val."""
    dates = _biz_dates(300)
    plan = purged_fold_plan(dates, n_splits=3, embargo_td=EMBARGO_TD)
    viable = [r for r in plan if "skipped" not in r]
    assert viable
    for r in viable:
        fit_dates = set(dates[r["fit_pos"]])
        cal_dates = set(dates[r["cal_pos"]])
        val_dates = set(dates[r["val_pos"]])
        assert fit_dates.isdisjoint(val_dates)
        assert fit_dates.isdisjoint(cal_dates)
        assert max(fit_dates) < min(cal_dates) <= max(cal_dates) < min(val_dates)
        # the same enforcement the runtime gate applies to a saved artifact
        assert_fold_safe(max(fit_dates), sorted(val_dates), dates, EMBARGO_TD) is None


# --------------------------------------------------------------------------- #
# stacked input
# --------------------------------------------------------------------------- #
def test_stacked_input_matrix_appends_the_score_as_one_column_float32():
    base = np.arange(12, dtype="float32").reshape(4, 3)
    score = np.array([1.0, 2.0, 3.0, 4.0])
    x = stacked_input_matrix(base, score)
    assert x.shape == (4, 4) and x.dtype == np.float32
    assert np.allclose(x[:, :3], base) and np.allclose(x[:, 3], score)


def test_stacked_input_matrix_refuses_misaligned_rows():
    with pytest.raises(ValueError):
        stacked_input_matrix(np.zeros((4, 3), dtype="float32"), np.zeros(3))


# --------------------------------------------------------------------------- #
# baseline vs stacked on identical folds
# --------------------------------------------------------------------------- #
def _synthetic_panel(n_dates: int = 260, n_symbols: int = 25, seed: int = 11) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = _biz_dates(n_dates)
    parts = []
    for d in dates:
        f = rng.normal(size=(n_symbols, len(E5_COLS)))
        parts.append(
            pd.DataFrame(
                {
                    "date": d,
                    "symbol": [f"S{i:03d}" for i in range(n_symbols)],
                    **{c: f[:, j].astype("float32") for j, c in enumerate(E5_COLS)},
                    CONTINUOUS_TARGET: (f @ np.array([0.4, -0.3, 0.2, 0.1, -0.15])
                                        + rng.normal(scale=1.0, size=n_symbols)).astype("float32"),
                    ATR_PRICE_COLUMN: np.full(n_symbols, 0.02, dtype="float32"),
                }
            )
        )
    return pd.concat(parts, ignore_index=True).sort_values(["date", "symbol"]).reset_index(drop=True)


def _args(**kw) -> SimpleNamespace:
    base = dict(n_splits=2, embargo_td=EMBARGO_TD, calib_fraction=0.20, max_minutes=5.0)
    base.update(kw)
    return SimpleNamespace(**base)


def test_baseline_and_stacked_are_evaluated_on_identical_folds():
    panel = _synthetic_panel()
    rng = np.random.default_rng(3)
    scores = rng.normal(size=len(panel))

    base = run_folds(panel, _args(), label="baseline")
    stacked = run_folds(panel, _args(), extra_scores=scores, label="stacked")

    assert base["n_input_cols"] == len(E5_COLS)
    assert stacked["n_input_cols"] == len(E5_COLS) + 1
    key = lambda recs: [(r["fold"], r.get("val_min"), r.get("val_max"), r.get("n_val_rows")) for r in recs]
    assert key(base["fold_records"]) == key(stacked["fold_records"])
    assert set(base["frame"]["symbol"]) == set(stacked["frame"]["symbol"])
    assert len(base["frame"]) == len(stacked["frame"])
    # identical rows and dates, so the two skill numbers are comparable
    assert base["frame"]["date"].tolist() == stacked["frame"]["date"].tolist()
    assert base["frame"]["y"].tolist() == stacked["frame"]["y"].tolist()


def test_stacked_and_baseline_skills_use_the_same_rows_and_dates():
    panel = _synthetic_panel()
    rng = np.random.default_rng(5)
    scores = rng.normal(size=len(panel))
    base = run_folds(panel, _args(), label="baseline")["frame"]
    stacked = run_folds(panel, _args(), extra_scores=scores, label="stacked")["frame"]
    sb = score_skill(base)
    ss = score_skill(stacked)
    assert sb["n_rows"] == ss["n_rows"] and sb["n_dates"] == ss["n_dates"]
    assert sb["factor_stats"].keys() == ss["factor_stats"].keys()
    for fac in sb["factor_stats"]:
        assert sb["factor_stats"][fac] == ss["factor_stats"][fac]


# --------------------------------------------------------------------------- #
# shortlist composite
# --------------------------------------------------------------------------- #
def _oof_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-09-21"] * 5 + ["2026-09-22"] * 5),
            "symbol": ["A", "B", "C", "D", "E", "A", "B", "C", "D", "E"],
            "p_up": [0.1, 0.2, 0.3, 0.4, 0.5, 0.50, 0.40, 0.60, 0.20, 0.30],
            "p_down": [0.2, 0.2, 0.2, 0.2, 0.2, 0.10, 0.30, 0.60, 0.05, 0.25],
            "p_stay": [0.7, 0.6, 0.5, 0.4, 0.3, 0.40, 0.30, 0.20, 0.75, 0.45],
            "forecast": [0.0, 0.1, 0.2, 0.3, 0.4, 0.9, 0.2, 0.0, 0.5, 0.1],
        }
    )


def test_shortlist_defaults_to_the_latest_date_and_orders_by_the_declared_composite():
    sl = shortlist_frame(_oof_frame(), top_n=3)
    assert set(sl["date"]) == {pd.Timestamp("2026-09-22")}
    # composites on 09-22: A .40, B .10, C .00, D .15, E .05
    assert sl["symbol"].tolist() == ["A", "D", "B"]
    assert np.allclose(sl["composite"], [0.40, 0.15, 0.10])
    assert np.allclose(sl["composite"], sl["p_up"] - sl["p_down"])
    assert sl["rank"].tolist() == [1, 2, 3]


def test_shortlist_ties_break_on_symbol_and_never_on_p_stay():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-09-22"] * 3),
            "symbol": ["Z", "M", "A"],
            "p_up": [0.5, 0.5, 0.5],
            "p_down": [0.2, 0.2, 0.2],
            "p_stay": [0.9, 0.1, 0.5],  # deliberately anti-correlated with the tie-break
            "forecast": [0.0, 0.0, 0.0],
        }
    )
    sl = shortlist_frame(df, top_n=3)
    assert sl["symbol"].tolist() == ["A", "M", "Z"]


def test_shortlist_is_reproducible_for_a_given_as_of_date():
    a = shortlist_frame(_oof_frame(), as_of_date="2026-09-21", top_n=5)
    b = shortlist_frame(_oof_frame(), as_of_date="2026-09-21", top_n=5)
    pd.testing.assert_frame_equal(a, b)


def test_shortlist_refuses_a_date_with_no_rows():
    with pytest.raises(ValueError):
        shortlist_frame(_oof_frame(), as_of_date="2026-01-01")


def test_skill_bar_embargo_is_the_same_20td_used_by_the_route():
    assert EMBARGO_TD == SKILL_EMBARGO_TD == 20
