"""WI-009b skill bar: widened purged split, disjoint sub-windows, verdict logic.

Locks the acceptance criteria fixed in
`docs/plans/2026-10-25-WI-009b-beat-e5-baseline.md`:
clause (a) beat the best single E5 factor's |IC| on the same dates/rows;
clause (b) |t| > 2 with the same IC sign in >= 2 disjoint sub-windows.
"""
import numpy as np
import pandas as pd
import pytest

from src.models.pair_sampler import within_date_rank_ic
from src.models.skill_bar import (
    EMBARGO_TD,
    factor_ics_from_panel,
    purged_date_split,
    skill_bar_verdict,
    stats_for_rows,
    sub_window_split,
    write_comparison_report,
)


def _dates(n: int) -> np.ndarray:
    return np.sort(pd.to_datetime(pd.date_range("2020-01-01", periods=n, freq="B")).to_numpy())


# --------------------------------------------------------------------------- #
# purged split
# --------------------------------------------------------------------------- #
def test_purged_split_holds_out_exactly_val_dates_with_purge_gap():
    dates = _dates(300)
    train, val, gap = purged_date_split(dates, val_dates=60)
    assert len(val) == 60 and len(train) == 300 - 60 - EMBARGO_TD
    assert gap == EMBARGO_TD
    assert train.max() < val.min()
    assert not set(train).intersection(set(val))
    # purge rows are in NEITHER fold
    assert len(train) + len(val) + gap == len(np.unique(dates))


def test_purged_split_train_never_abuts_val():
    dates = _dates(300)
    train, val, _ = purged_date_split(dates, val_dates=60)
    uniq = np.sort(pd.unique(dates))
    pos = {d: i for i, d in enumerate(uniq)}
    assert pos[val[0]] - pos[train[-1]] - 1 == EMBARGO_TD


def test_purged_split_rejects_window_larger_than_panel():
    with pytest.raises(ValueError):
        purged_date_split(_dates(50), val_dates=60)


def test_purged_split_rejects_zero_val_dates():
    with pytest.raises(ValueError):
        purged_date_split(_dates(100), val_dates=0)


def test_widened_window_is_at_least_60_dates_by_construction():
    train, val, _ = purged_date_split(_dates(300), val_dates=60)
    assert len(val) >= 60


# --------------------------------------------------------------------------- #
# sub-windows
# --------------------------------------------------------------------------- #
def test_sub_windows_are_disjoint_contiguous_and_cover_the_window():
    _, val, _ = purged_date_split(_dates(300), val_dates=60)
    blocks = sub_window_split(val, n_windows=2)
    assert len(blocks) == 2
    assert all(len(b) == 30 for b in blocks)
    assert len(set(blocks[0]).intersection(set(blocks[1]))) == 0
    assert set(np.concatenate(blocks)) == set(val)
    # a block must not interleave with the other: every date of block 1 precedes block 2
    assert blocks[0].max() < blocks[1].min()


def test_sub_windows_reject_single_window_or_too_few_dates():
    _, val, _ = purged_date_split(_dates(300), val_dates=60)
    with pytest.raises(ValueError):
        sub_window_split(val, n_windows=1)
    with pytest.raises(ValueError):
        sub_window_split(val[:1], n_windows=2)


# --------------------------------------------------------------------------- #
# verdict logic
# --------------------------------------------------------------------------- #
FACTORS_OK = {
    "mom_12_1": (0.027, 0.65, 60),
    "rev_1m": (-0.061, -2.10, 60),
    "vol_20": (-0.041, -0.95, 60),
    "amihud_20": (0.034, 1.88, 60),
    "log_dollar_vol_20": (-0.063, -3.50, 60),
}


def test_verdict_passes_when_both_clauses_hold():
    v = skill_bar_verdict(
        model_ic=0.09, model_t=3.4, factor_stats=FACTORS_OK,
        sub_stats=[(0.075, 2.6, 30), (0.104, 2.9, 30)],
    )
    assert v["passed"] is True
    assert v["clause_a"]["passed"] is True
    assert v["clause_a"]["best_factor"] == "log_dollar_vol_20"
    assert v["clause_b"]["passed"] is True
    assert v["clause_b"]["all_windows_same_sign"] is True


def test_verdict_fails_clause_a_when_a_factor_is_stronger():
    v = skill_bar_verdict(
        model_ic=0.05, model_t=3.4, factor_stats=FACTORS_OK,
        sub_stats=[(0.041, 2.6, 30), (0.058, 2.9, 30)],
    )
    assert v["passed"] is False
    assert v["clause_a"]["passed"] is False
    assert v["clause_a"]["margin"] < 0
    assert v["clause_b"]["passed"] is True


def test_verdict_fails_clause_b_on_sign_flip_between_sub_windows():
    v = skill_bar_verdict(
        model_ic=0.09, model_t=3.4, factor_stats=FACTORS_OK,
        sub_stats=[(-0.075, -2.6, 30), (0.104, 2.9, 30)],
    )
    assert v["passed"] is False
    assert v["clause_a"]["passed"] is True
    assert v["clause_b"]["passed"] is False
    assert v["clause_b"]["all_windows_same_sign"] is False


def test_verdict_fails_clause_b_when_a_sub_window_t_is_weak():
    v = skill_bar_verdict(
        model_ic=0.06, model_t=3.4, factor_stats=FACTORS_OK,
        sub_stats=[(0.02, 0.5, 30), (0.10, 2.9, 30)],
    )
    assert v["passed"] is False
    assert v["clause_b"]["passed"] is False
    assert v["clause_b"]["all_windows_abs_t_gt_2"] is False


def test_verdict_fails_clause_b_with_a_single_sub_window():
    v = skill_bar_verdict(
        model_ic=0.09, model_t=3.4, factor_stats=FACTORS_OK,
        sub_stats=[(0.09, 3.4, 60)],
    )
    assert v["clause_b"]["passed"] is False


def test_verdict_gives_no_credit_for_undefined_model_skill():
    v = skill_bar_verdict(
        model_ic=float("nan"), model_t=float("nan"), factor_stats=FACTORS_OK,
        sub_stats=[(float("nan"), float("nan"), 30), (0.10, 2.9, 30)],
    )
    assert v["passed"] is False
    assert v["clause_a"]["passed"] is False
    assert v["clause_b"]["passed"] is False


def test_verdict_requires_at_least_one_finite_factor():
    with pytest.raises(ValueError):
        skill_bar_verdict(
            model_ic=0.05, model_t=3.0,
            factor_stats={"a": (float("nan"), float("nan"), 0)},
            sub_stats=[(0.05, 3.0, 30), (0.05, 3.0, 30)],
        )


# --------------------------------------------------------------------------- #
# same-row factor harness
# --------------------------------------------------------------------------- #
def _planted_panel(n_dates: int = 80, n_names: int = 40, seed: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    dates = pd.date_range("2021-01-01", periods=n_dates, freq="B")
    for d in dates:
        fwd = rng.normal(size=n_names)
        rows.append(
            pd.DataFrame(
                {
                    "date": d,
                    "symbol": [f"S{i:03d}" for i in range(n_names)],
                    "fwd_atr_ret_15": fwd,
                    "e5_perfect": fwd,                        # planted: IC == 1 exactly
                    "e5_strong": fwd + 0.5 * rng.normal(size=n_names),
                    "e5_noise": rng.normal(size=n_names),
                }
            )
        )
    return pd.concat(rows, ignore_index=True)


def test_factor_harness_scores_each_factor_on_the_same_rows():
    panel = _planted_panel()
    out = factor_ics_from_panel(panel, factors=["perfect", "strong", "noise"])
    ic_p, t_p, n_p = out["perfect"]
    ic_s, t_s, n_s = out["strong"]
    ic_n, t_n, n_n = out["noise"]
    assert n_p == n_s == n_n == 80
    assert ic_p == pytest.approx(1.0, abs=1e-9)
    # a perfectly-planted factor has zero IC dispersion, so its t is undefined
    # (nan) by construction — documented, not a defect.
    assert np.isnan(t_p)
    assert ic_s > 0.8 and np.isfinite(t_s)
    assert abs(ic_n) < 0.25
    # identical to calling the shared metric directly — one metric, no divergence
    direct = within_date_rank_ic(
        panel["e5_strong"].to_numpy(), panel["fwd_atr_ret_15"].to_numpy(), panel["date"].to_numpy()
    )
    assert (ic_s, t_s, n_s) == direct


def test_factor_harness_raises_on_missing_factor_column():
    panel = _planted_panel()
    with pytest.raises(KeyError):
        factor_ics_from_panel(panel, factors=["not_there"])


def test_sub_window_stats_use_only_their_own_dates():
    panel = _planted_panel()
    blocks = sub_window_split(panel["date"].unique(), n_windows=4)
    for b in blocks:
        sub = panel[panel["date"].isin(set(b))]
        ic, _t, n = stats_for_rows(sub, "e5_perfect")
        assert n == len(b)
        assert ic == pytest.approx(1.0, abs=1e-9)


# --------------------------------------------------------------------------- #
# report writer
# --------------------------------------------------------------------------- #
def test_verdict_flags_a_sign_inverted_pass_as_a_caveat():
    """|IC| is a magnitude bar: a sign-flipped model passes it. That must be loud.

    Mirrors the real WI-009b full-history result on the widened window, so the
    reading ("passes on magnitude only, inverted sign, 3% margin") is locked.
    """
    factors = {
        "mom_12_1": (0.0677, 3.13, 60),
        "rev_1m": (-0.0555, -1.82, 60),
        "vol_20": (0.1274, 3.48, 60),
        "amihud_20": (0.0546, 4.08, 60),
        "log_dollar_vol_20": (-0.0242, -3.04, 60),
    }
    v = skill_bar_verdict(
        model_ic=-0.1313, model_t=-6.55, factor_stats=factors,
        sub_stats=[(-0.1951, -6.30, 30), (-0.0675, -3.39, 30)],
    )
    assert v["passed"] is True
    assert v["sign_agrees_with_best_factor"] is False
    assert any("SIGN INVERTED" in c for c in v["caveats"])
    assert any("THIN MARGIN" in c for c in v["caveats"])


def test_verdict_has_no_sign_caveat_when_signs_agree_comfortably():
    factors = {
        "mom_12_1": (0.0677, 3.13, 60),
        "vol_20": (0.1274, 3.48, 60),
        "amihud_20": (0.0546, 4.08, 60),
    }
    v = skill_bar_verdict(
        model_ic=0.20, model_t=4.0, factor_stats=factors,
        sub_stats=[(0.18, 3.4, 30), (0.22, 3.9, 30)],
    )
    assert v["passed"] is True and v["sign_agrees_with_best_factor"] is True
    assert v["caveats"] == []


def test_report_writer_emits_the_sign_caveat_block(tmp_path):
    panel = _planted_panel()
    factors = {"strong": (0.10, 3.0, 80)}
    verdict = skill_bar_verdict(
        model_ic=-0.11, model_t=-4.0, factor_stats=factors,
        sub_stats=[(-0.12, -3.1, 40), (-0.10, -2.9, 40)],
    )
    out = write_comparison_report(
        tmp_path / "c.mp4.md",
        {
            "market": "CAD", "n_rows": len(panel), "n_features": 2, "n_symbols": 40,
            "val_dates": list(panel["date"].unique())[:80],
            "val_start": "2021-01-01", "val_end": "2021-04-01", "embargo_td": 20,
            "n_train_dates": 1, "train_start": "2020-01-01", "train_end": "2020-02-01",
            "epochs_run": 5, "patience": 4, "early_stopped": True, "train_minutes": 0.9,
            "best_epoch": 1, "model_ic": -0.11, "model_t": -4.0,
            "final_epoch_ic": -0.14, "final_epoch_t": -6.0,
            "skill_bar": verdict, "sub_window_best_factor": {},
        },
    )
    text = out.read_text()
    assert "SKILL BAR: PASS (with caveats" in text
    assert "Caveats — read before acting on the verdict" in text
    assert "SIGN INVERTED" in text


def test_report_writer_emits_table_and_both_verdict_lines(tmp_path):
    panel = _planted_panel()
    factors = factor_ics_from_panel(panel, factors=["perfect", "noise"])
    # a model that cannot beat the planted factor: clause (a) FAIL, clause (b) PASS
    verdict = skill_bar_verdict(
        model_ic=0.02, model_t=2.5, factor_stats=factors,
        sub_stats=[(0.01, 2.2, 40), (0.03, 2.6, 40)],
    )
    out = write_comparison_report(
        tmp_path / "cmp.md",
        {
            "market": "CAD", "n_rows": len(panel), "n_features": 2, "n_symbols": 40,
            "val_dates": list(panel["date"].unique()),
            "val_start": "2021-01-01", "val_end": "2021-04-01",
            "embargo_td": 20, "n_train_dates": 0, "train_start": None, "train_end": None,
            "epochs_run": 1, "patience": 0, "early_stopped": False, "train_minutes": 0.1,
            "best_epoch": 1, "model_ic": 0.02, "model_t": 2.5,
            "final_epoch_ic": 0.02, "final_epoch_t": 2.5,
            "skill_bar": verdict,
            "sub_window_best_factor": {1: {"name": "perfect", "abs_ic": 1.0},
                                       2: {"name": "perfect", "abs_ic": 1.0}},
        },
    )
    text = out.read_text()
    assert "Clause (a)" in text and "FAIL" in text
    assert "Clause (b)" in text and "PASS" in text
    assert "SKILL BAR: FAIL" in text
    assert "`e5_perfect` (factor)" in text
    assert "Sub-window stability" in text
    assert "out of scope" in text