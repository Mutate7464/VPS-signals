"""WI-018 step 3 regression tests — G2 probe folds, statistics, family and verdict.

Locks: the fold geometry (`fold_blocks` + `max(20, w)` embargo, label-end
trim), the three-part pass rule (CI excludes zero AND BH-FDR AND same-sign), the
conjunction rule (only from univariate BH survivors, depth ≤ 2, different
features), single-family BH correction, the survivor-density red flag, the G3
skip on failure, deterministic reruns, and the `--check-report` acceptance gate.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.wi011.stats import fold_blocks
from src.wi018 import FDR_ALPHA, HORIZON, PRIMARY_TARGET, SECONDARY_TARGETS
from src.wi018.data_probe import PreflightError
from src.wi018.probe import (
    DIRECTIONS,
    MAX_CONJUNCTION_PAIRS,
    MIN_HOLDOUT_DATES,
    SURVIVOR_DENSITY_RED_FLAG,
    TOP_SURVIVOR_STATES,
    _apply_bh,
    _passes,
    check_probe_report,
    conjunction_pairs,
    format_markdown,
    held_out_positions,
    hypothesis_stats,
    main,
    run_probe,
    survivor_states,
    univariate_hypotheses,
    write_report,
)
from src.wi018.streaming import BINNING_ORDER, CLASSES, STATE_OFFSET, global_dates

DISK_PROBE = Path("reports/wi018/probe_USD.json")


# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #
def _toy_market(
    tmp_path: Path,
    n_symbols: int = 20,
    n_dates: int = 1000,
    keep=("signal_34", "noise_34", "flip_34"),
    features=("signal_34", "noise_34", "flip_34"),
    shift_symbol_first: bool = True,
) -> dict:
    """Cross-sectional market with one honest condition, one noise, one flipped.

    `signal_34` is a per-date permutation of 1..n_symbols, and the target is +1
    for the top three ranks, -1 for the bottom two, 0 otherwise, with 10% of rows
    relabelled at random. So the top quintile state has a genuinely *higher*
    up-first rate out of sample, while `noise_34` is unrelated and `flip_34` is
    the sign-reversed copy of signal. The relabelling matters: a perfectly
    deterministic rate is constant across dates, so its lift series has zero
    dispersion and the house rule (WI-011/WI-016) marks it unevaluable rather
    than manufacturing a t-statistic — the toy must be stochastic like real data.
    Symbol count and date count are chosen so quintile bins hold >= 3 names per
    date and five folds survive the 34-session label trim.
    """
    tmp_path.mkdir(parents=True, exist_ok=True)
    derived_dir = tmp_path / "derived"
    features_dir = tmp_path / "features"
    derived_dir.mkdir(exist_ok=True)
    features_dir.mkdir(exist_ok=True)
    dates = pd.bdate_range("2015-01-01", periods=n_dates)
    rng = np.random.default_rng(7)
    ranks = np.concatenate([rng.permutation(n_symbols) + 1 for _ in range(n_dates)]).astype("float32")
    target = np.where(ranks > n_symbols - 4, 1.0, np.where(ranks <= 2, -1.0, 0.0))
    shuffled = rng.random(target.size) < 0.10
    target = np.where(shuffled, rng.choice([1.0, 0.0, -1.0], size=target.size), target).astype("float32")
    columns = {"signal_34": ranks, "flip_34": -ranks, "noise_34": rng.normal(size=ranks.size).astype("float32")}
    for j in range(n_symbols):
        take = slice(j, None, n_symbols)
        pq.write_table(
            pa.table({"date": pa.array(dates.to_numpy()).cast(pa.date32()),
                      **{name: column[take] for name, column in columns.items()}}),
            features_dir / f"SYM{j:02d}.parquet",
        )
        pq.write_table(
            pa.table({"date": pa.array(dates.to_numpy()).cast(pa.date32()),
                      **{target_name: target[take] for target_name in (PRIMARY_TARGET, *SECONDARY_TARGETS)}}),
            derived_dir / f"SYM{j:02d}.parquet",
        )
    prune = tmp_path / "run5_prune_recs.json"
    prune.write_text(json.dumps({"n_features": len(features), "n_keep": len(keep), "keep_columns": list(keep)}))
    preflight = tmp_path / "preflight_USD.json"
    preflight.write_text(json.dumps({
        "market": "USD", "verdict": "PASS", "summary": {"symbols": n_symbols},
        "config": {"derived_dir": str(derived_dir), "features_dir": str(features_dir), "prune_recs": str(prune)},
    }))
    return {"derived": derived_dir, "features": features_dir, "prune": prune, "preflight": preflight,
            "keep": list(keep), "n_symbols": n_symbols, "n_dates": n_dates}


def _run(market_dir: dict, **kwargs) -> dict:
    kwargs.setdefault("min_holdout_dates", 20)
    return run_probe(
        deriv_dir=market_dir["derived"],
        feat_dir=market_dir["features"],
        prune_path=market_dir["prune"],
        preflight_path=market_dir["preflight"],
        block_size=128,
        **kwargs,
    )


# --------------------------------------------------------------------------- #
# folds
# --------------------------------------------------------------------------- #
def test_held_out_positions_uses_fold_blocks_with_horizon_embargo():
    dates = pd.bdate_range("2015-01-01", periods=1000).to_numpy().astype("datetime64[ns]")
    mask, detail = held_out_positions(dates)
    assert len(detail) == 5
    assert all(f["embargo_td"] == max(20, HORIZON) for f in detail)
    assert all(f["label_end_pos"] <= f["val_pos_max"] for f in detail)
    assert 0.3 < mask.mean() < 0.7  # held-out is a majority, not everything
    # every held-out position is inside some fold's [val_pos_min, label_end_pos]
    reference = np.zeros(dates.size, dtype=bool)
    for f in detail:
        reference[f["val_pos_min"] : f["label_end_pos"] + 1] = True
    assert np.array_equal(mask, reference)


def test_held_out_positions_matches_fold_blocks_geometry():
    dates = pd.bdate_range("2016-01-01", periods=1000).to_numpy().astype("datetime64[ns]")
    blocks = fold_blocks(dates, horizon=HORIZON, n_splits=5, initial_train_fraction=0.40)
    _mask, detail = held_out_positions(dates)
    assert [f["val_pos_min"] for f in detail] == [int(b["val_pos_min"]) for b in blocks]
    assert [f["label_end_pos"] for f in detail] == [int(b["label_end_pos"]) for b in blocks]


# --------------------------------------------------------------------------- #
# hypothesis statistics
# --------------------------------------------------------------------------- #
def _series_case(n_dates: int = 120, lift: float = 0.0, noise: float = 0.0, seed: int = 0):
    rng = np.random.default_rng(seed)
    held = np.ones(n_dates, dtype=bool)
    totals = np.full(n_dates, 20.0)
    unc_tot = np.full(n_dates, 100.0)
    unc_cls = np.full(n_dates, 40.0)  # unconditional up rate 0.40
    counts = np.clip(np.round((0.40 + lift) * totals + rng.normal(0, noise, n_dates)), 0, totals)
    return counts, totals, unc_cls, unc_tot, held


def test_hypothesis_stats_reports_positive_lift_with_ci_excluding_zero():
    counts, totals, unc_cls, unc_tot, held = _series_case(lift=0.15, noise=0.5)
    record = hypothesis_stats(counts, totals, unc_cls, unc_tot, held, min_holdout_dates=20)
    assert record["estimable"] is True
    assert record["lift"] == pytest.approx(0.15, abs=0.02)
    assert record["ci_low"] > 0.0
    assert abs(record["lift"]) > record["margin"]
    assert record["same_sign"] is True
    assert np.isfinite(record["p"]) and record["p"] < 0.01


def test_hypothesis_stats_flags_no_lift_and_sign_flips():
    counts, totals, unc_cls, unc_tot, held = _series_case(lift=0.0, noise=1.0)
    record = hypothesis_stats(counts, totals, unc_cls, unc_tot, held, min_holdout_dates=20)
    assert record["ci_low"] < 0.0 < record["ci_high"]
    assert abs(record["lift"]) < record["margin"]  # CI includes zero

    # half the dates flip sign -> the same-sign clause must fail
    counts, totals, unc_cls, unc_tot, held = _series_case(lift=0.15, noise=0.0)
    counts = counts.copy()
    counts[60:] = 0.25 * totals[: 120 - 60]
    record = hypothesis_stats(counts, totals, unc_cls, unc_tot, held, min_holdout_dates=20)
    assert record["same_sign"] is False


def test_zero_dispersion_lift_is_never_estimable():
    # A condition whose rate is identical every date has no dispersion, so the
    # normal-approximation t-stat is undefined. House convention (WI-011 stats,
    # WI-016 probe) reports "unevaluable" here rather than an infinite t.
    counts, totals, unc_cls, unc_tot, held = _series_case(lift=0.15, noise=0.0)
    record = hypothesis_stats(counts, totals, unc_cls, unc_tot, held, min_holdout_dates=20)
    assert record["lift"] == pytest.approx(0.15, abs=1e-9)
    assert record["estimable"] is False
    assert "dispersion" in record["unevaluable_reason"]
    assert _passes(record) is False


def test_hypothesis_stats_marks_short_series_unevaluable():
    counts, totals, unc_cls, unc_tot, held = _series_case(n_dates=30, lift=0.2, noise=0.3)
    record = hypothesis_stats(counts, totals, unc_cls, unc_tot, held, min_holdout_dates=60)
    assert record["estimable"] is False
    assert "n_dates<60" in record["unevaluable_reason"]


def test_hypothesis_stats_uses_only_held_out_dates():
    counts, totals, unc_cls, unc_tot, held = _series_case(lift=0.15, noise=0.0)
    held = held.copy()
    held[:60] = False
    counts = counts.copy()
    counts[:60] = 0.0  # absurd values outside the held-out window must be ignored
    record = hypothesis_stats(counts, totals, unc_cls, unc_tot, held, min_holdout_dates=20)
    assert record["lift"] == pytest.approx(0.15, abs=0.001)
    assert record["n_dates"] == 60


# --------------------------------------------------------------------------- #
# family construction
# --------------------------------------------------------------------------- #
def test_univariate_family_is_704_states_x_2_directions(tmp_path):
    market = _toy_market(tmp_path, n_symbols=20, n_dates=1000, keep=("signal_34", "noise_34"),
                         features=("signal_34", "noise_34"))
    report = _run(market)
    expected_states = len(market["keep"]) * 8
    assert report["hypotheses"]["n_univariate"] == expected_states * len(DIRECTIONS)
    assert report["hypotheses"]["n_univariate"] == 32  # 2 features x 8 states x 2 directions


def test_survivor_states_only_from_bh_rejects_and_capped():
    hypotheses = [
        {"kind": "univariate", "feature_index": 1, "code": 0, "reject": True, "q": 0.01},
        {"kind": "univariate", "feature_index": 2, "code": 0, "reject": False, "q": 0.9},
        {"kind": "conjunction", "feature_index": 3, "code": 0, "reject": True, "q": 0.001},
    ]
    states = survivor_states(hypotheses)
    assert states == [(1, 0)]
    capped = survivor_states(
        [{"kind": "univariate", "feature_index": i, "code": 0, "reject": True, "q": 0.01} for i in range(100)],
        cap=3,
    )
    assert len(capped) == 3


def test_conjunction_pairs_exclude_same_feature_and_respect_cap():
    states = [(0, 0), (0, 5), (1, 0), (2, 3)]
    pairs = conjunction_pairs(states, ["a", "b", "c"])
    assert all(p[0] != p[2] for p in pairs)
    assert len(pairs) == 5  # every cross-feature combination of the four states
    assert len(conjunction_pairs(states, ["a", "b", "c"], cap=1)) == 1


def test_apply_bh_controls_density_on_pure_noise():
    rng = np.random.default_rng(0)
    noise = [{"estimable": True, "p": float(p)} for p in rng.uniform(size=2000)]
    for h in noise:
        h.setdefault("reject", False)
    stats = _apply_bh(noise, FDR_ALPHA)
    assert stats["n_tested"] == 2000
    assert stats["n_rejected"] <= 2000 * 0.03  # BH keeps noise survivors rare

    strong = [{"estimable": True, "p": 1e-6} for _ in range(10)]
    stats = _apply_bh(strong, FDR_ALPHA)
    assert stats["n_rejected"] == 10


# --------------------------------------------------------------------------- #
# end-to-end verdicts
# --------------------------------------------------------------------------- #
def test_run_probe_passes_when_a_real_condition_exists(tmp_path):
    market = _toy_market(tmp_path, n_symbols=20, n_dates=1000)
    report = _run(market)
    assert report["verdict"] in {"G2_PASS", "G2_PASS_WITH_RED_FLAG"}
    assert report["g2_pass"] is True
    # the G3 gate follows the plan: a wall of survivors is a red flag, not a win
    assert report["g3_eligible"] == (not report["red_flag"])
    assert report["g3_skipped"] == (not report["g3_eligible"])
    conditions = {s["condition"] for s in report["survivors"]}
    assert any(c.startswith("signal_34|quintile/5") for c in conditions)
    for survivor in report["survivors"]:
        assert survivor["reject"] and survivor["same_sign"]
        assert abs(survivor["lift"]) > survivor["margin"]
        assert set(survivor["robustness"]) == set(SECONDARY_TARGETS)
        assert len(survivor["per_fold_lift"]) == 5
    assert report["checks"] and all(c["ok"] for c in report["checks"].values()), report["checks"]


def test_run_probe_fails_cleanly_on_pure_noise(tmp_path):
    market = _toy_market(tmp_path, n_symbols=20, n_dates=1000, keep=("noise_34",), features=("noise_34",))
    report = _run(market)
    assert report["verdict"] == "G2_FAIL"
    assert report["g2_pass"] is False
    assert report["g3_eligible"] is False
    assert report["g3_skipped"] is True
    assert report["g3_skip_reason"]
    assert report["survivors"] == []
    assert report["hypotheses"]["n_conjunction"] == 0
    # "closest to passing" is still reported so a negative is auditable
    assert report["closest_to_passing"]


def test_run_probe_is_deterministic(tmp_path):
    market = _toy_market(tmp_path, n_symbols=20, n_dates=1000)
    first = _run(market)
    second = _run(market)
    first.pop("generated_utc"), second.pop("generated_utc")
    assert json.dumps(first, sort_keys=True, default=str) == json.dumps(second, sort_keys=True, default=str)


def test_run_probe_conjunctions_only_from_univariate_survivors(tmp_path):
    # Regression: pair selection must run *after* a BH decision on the univariate
    # family. When it ran before, `reject` was never set, no pair was ever built
    # and the conjunction arm of the family was silently empty.
    market = _toy_market(tmp_path, n_symbols=20, n_dates=1000)
    report = _run(market)
    hyp = report["hypotheses"]
    assert hyp["univariate_selection_pass"]["n_rejected"] > 0
    assert hyp["n_survivor_states"] >= 2
    assert hyp["n_conjunction_pairs"] > 0
    assert hyp["n_survivor_states"] <= TOP_SURVIVOR_STATES
    assert hyp["n_conjunction_pairs"] <= MAX_CONJUNCTION_PAIRS
    assert hyp["n_conjunction"] == 2 * hyp["n_conjunction_pairs"]
    assert hyp["n_total"] == hyp["n_univariate"] + hyp["n_conjunction"]
    # conjunctions are AND-pairs of states from two different features
    for survivor in report["survivors"]:
        if survivor["kind"] == "conjunction":
            assert " & " in survivor["condition"]
            assert survivor["condition"].split(" & ")[0].split("|")[0] != survivor["condition"].split(" & ")[1].split("|")[0]
    assert check_probe_report(report)["conjunctions_built_only_from_univariate_survivors"][0]


def test_run_probe_requires_preflight(tmp_path):
    market = _toy_market(tmp_path, n_symbols=20, n_dates=1000)
    market["preflight"].unlink()
    with pytest.raises(PreflightError, match="preflight report missing"):
        _run(market)


def test_run_probe_rejects_non_usd_market(tmp_path):
    market = _toy_market(tmp_path, n_symbols=20, n_dates=1000)
    with pytest.raises(PreflightError, match="USD-only"):
        _run(market, market="CAD")


def test_probe_writes_no_rules_or_shortlist(tmp_path):
    market = _toy_market(tmp_path, n_symbols=20, n_dates=1000)
    report = _run(market)
    serialized = json.dumps(report, default=str)
    assert "shortlist" not in serialized.lower().replace("no shortlist", "")
    assert report["config"]["secondary_role"].startswith("robustness reads only")


# --------------------------------------------------------------------------- #
# acceptance self-check
# --------------------------------------------------------------------------- #
def test_check_probe_report_flags_each_rule(tmp_path):
    market = _toy_market(tmp_path, n_symbols=20, n_dates=1000)
    report = _run(market)
    assert all(ok for ok, _ in check_probe_report(report).values())

    broken = json.loads(json.dumps(report, default=str))
    broken["survivors"][0]["same_sign"] = False
    assert not check_probe_report(broken)["every_survivor_passes_all_criteria"][0]

    broken = json.loads(json.dumps(report, default=str))
    broken["survivors"][0]["margin"] = abs(broken["survivors"][0]["lift"]) * 2
    assert not check_probe_report(broken)["every_survivor_passes_all_criteria"][0]

    broken = json.loads(json.dumps(report, default=str))
    broken["hypotheses"]["n_conjunction"] += 1
    assert not check_probe_report(broken)["family_counts_consistent"][0]

    broken = json.loads(json.dumps(report, default=str))
    broken["hypotheses"]["univariate_selection_pass"]["n_rejected"] = 0
    assert not check_probe_report(broken)["conjunctions_built_only_from_univariate_survivors"][0]

    broken = json.loads(json.dumps(report, default=str))
    broken["g2_pass"] = False
    assert not check_probe_report(broken)["pass_and_gate_flags_consistent"][0]

    broken = json.loads(json.dumps(report, default=str))
    broken["g3_eligible"] = not broken["g3_eligible"]  # gate cannot disagree with the skip flag
    assert not check_probe_report(broken)["pass_and_gate_flags_consistent"][0]

    broken = json.loads(json.dumps(report, default=str))
    broken["g3_eligible"] = False
    broken["g3_skipped"] = True
    broken["g3_skip_reason"] = None
    assert not check_probe_report(broken)["g3_skip_reason_recorded"][0]

    broken = json.loads(json.dumps(report, default=str))
    broken["folds"] = broken["folds"][:2]
    assert not check_probe_report(broken)["folds_and_embargo_recorded"][0]

    broken = json.loads(json.dumps(report, default=str))
    broken["config"]["fdr_method"] = "uncorrected"
    assert not check_probe_report(broken)["fdr_applied_over_whole_family"][0]

    broken = json.loads(json.dumps(report, default=str))
    for survivor in broken["survivors"]:
        survivor["robustness"] = {}
    assert not check_probe_report(broken)["survivors_carry_secondary_reads_only"][0]

    broken = json.loads(json.dumps(report, default=str))
    broken["unconditional"][PRIMARY_TARGET]["held_out"]["rates"] = {"up": 0.5, "dn": 0.5, "neither": 0.5}
    assert not check_probe_report(broken)["unconditional_reference_present"][0]


def test_run_probe_red_flag_when_density_is_high(tmp_path):
    market = _toy_market(tmp_path, n_symbols=20, n_dates=1000)
    report = _run(market, top_states=2, max_pairs=1)
    density = report["hypotheses"]["survivor_density"]
    assert density == pytest.approx(report["hypotheses"]["n_survivors"] / report["hypotheses"]["n_total"])
    assert report["red_flag"] == (density > SURVIVOR_DENSITY_RED_FLAG)
    if report["red_flag"]:
        # a wall of survivors is not a win: G3 is not invoked on it
        assert report["g3_eligible"] is False and report["g3_skipped"] is True
        assert "red flag" in report["g3_skip_reason"]
        assert "G3 not invoked" in format_markdown(report)
        assert check_probe_report(report)["g3_skip_reason_recorded"][0]


def test_write_report_and_check_report_cli(tmp_path):
    market = _toy_market(tmp_path, n_symbols=20, n_dates=1000)
    report = _run(market)
    json_path = tmp_path / "probe.json"
    md_path = tmp_path / "probe.md"
    write_report(report, json_path, md_path)
    assert main(["--market", "USD", "--check-report", str(json_path)]) == 0
    body = md_path.read_text()
    assert "falsification probe" in body
    assert "closest to passing" in body.lower()
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"market": "USD", "verdict": "G2_FAIL", "hypotheses": {}, "config": {}}))
    assert main(["--market", "USD", "--check-report", str(bad)]) == 1
    assert main(["--market", "USD", "--check-report", str(tmp_path / "absent.json")]) == 1


def test_format_markdown_documents_negative_path(tmp_path):
    market = _toy_market(tmp_path, n_symbols=20, n_dates=1000, keep=("noise_34",), features=("noise_34",))
    md = format_markdown(_run(market))
    assert "G2_FAIL" in md
    assert "G3 skipped" in md
    assert "No condition cleared all three criteria" in md


# --------------------------------------------------------------------------- #
# on-disk integration (skipped until the real artifacts exist)
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not DISK_PROBE.is_file(), reason="WI-018 probe not generated yet")
def test_disk_probe_report_passes_acceptance_checks():
    report = json.loads(DISK_PROBE.read_text())
    checks = check_probe_report(report)
    bad = {k: v for k, v in checks.items() if not v[0]}
    assert not bad, bad
    assert report["market"] == "USD"
    assert report["config"]["fdr_alpha"] == FDR_ALPHA
    assert report["config"]["embargo_td"] == max(20, HORIZON)
    assert report["hypotheses"]["n_univariate"] == 88 * 8 * 2
    assert report["config"]["secondary_role"].startswith("robustness reads only")
    assert Path("reports/wi018/probe_USD.md").is_file()
