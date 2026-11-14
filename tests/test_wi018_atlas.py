"""WI-018 step 2 regression tests — G1 atlas state coding, rates, coverage and self-check.

Locks: within-date cross-sectional binning (quintile/tercile packing, ties to the
upper bin, undefined dates never imputed), the block-invariance of the streaming
pass, rates summing to 1 with CIs present, explicit unevaluable marking, the
flagged-family representativeness check, and the acceptance self-check that
`--check-report` applies to the shipped artifact.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.wi018 import BINNINGS, PRIMARY_TARGET
from src.wi018.atlas import (
    FAMILY_REPRESENTATIVE_SHARE,
    check_atlas_report,
    collect_state_counts,
    family_representativeness,
    format_markdown,
    main,
    run_atlas,
    write_report,
)
from src.wi018.data_probe import PreflightError
from src.wi018.rates import rate_block, sums_to_one
from src.wi018.streaming import (
    BINNING_ORDER,
    CLASSES,
    N_STATES,
    QUANTILES,
    STATE_OFFSET,
    classify_target,
    global_dates,
    quantile_edges,
    state_codes,
    state_layout,
)

DISK_ATLAS = Path("reports/wi018/atlas_USD.json")


# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #
def _write_frame(path: Path, dates, columns: dict) -> None:
    table = pa.table({"date": pa.array(pd.to_datetime(dates).to_numpy()).cast(pa.date32()), **columns})
    pq.write_table(table, path)


def _toy_market(
    tmp_path: Path,
    n_per_date: int = 10,
    n_dates: int = 12,
    features=("atr_pct_34", "atr_pct_144", "fib_dist_34", "fib_dist_55", "range_pos_34", "range_pos_89", "adx_3"),
    keep=("atr_pct_34", "fib_dist_34", "range_pos_34", "adx_3"),
    nan_feature: str | None = None,
) -> dict:
    """A tiny cross-sectional market: every symbol appears on every date.

    Feature values are a fresh per-date permutation of 1..n_per_date, so one
    feature's states are populated by *different* names on different dates
    (breadth is checkable). The target is +1 for the day's top-ranked name, -1
    for the bottom, 0 for the rest, with two deliberate NaN targets on the first
    date so unusable rows are exercised.
    """
    tmp_path.mkdir(parents=True, exist_ok=True)
    derived_dir = tmp_path / "derived"
    features_dir = tmp_path / "features"
    derived_dir.mkdir(exist_ok=True)
    features_dir.mkdir(exist_ok=True)
    dates = pd.bdate_range("2020-01-01", periods=n_dates)
    # deterministic rotation: value(rank) of symbol j on date d is ((j + d) % n) + 1,
    # so every symbol reaches the top rank at least once over n_dates >= n
    ranks = np.array(
        [[((j + d) % n_per_date) + 1 for j in range(n_per_date)] for d in range(n_dates)], dtype="float32"
    ).reshape(-1)
    target = np.where(ranks == n_per_date, 1.0, np.where(ranks == 1, -1.0, 0.0)).astype("float32")
    target[:2] = np.nan
    feature_columns = {}
    for name in features:
        column = ranks.copy()
        if name == nan_feature:
            column = np.full_like(column, np.nan)
        feature_columns[name] = column
    # rows are date-major across symbols: symbol j owns every n_per_date-th row
    for j in range(n_per_date):
        take = slice(j, None, n_per_date)
        _write_frame(
            features_dir / f"SYM{j:02d}.parquet",
            dates.to_numpy(),
            {name: column[take] for name, column in feature_columns.items()},
        )
        _write_frame(
            derived_dir / f"SYM{j:02d}.parquet",
            dates.to_numpy(),
            {
                "first_touch_34": target[take],
                "first_touch_24": target[take],
                "first_touch_39": target[take],
            },
        )
    prune = tmp_path / "run5_prune_recs.json"
    prune.write_text(json.dumps({"n_features": len(features), "n_keep": len(keep), "keep_columns": list(keep)}))
    preflight = tmp_path / "preflight_USD.json"
    preflight.write_text(json.dumps({
        "market": "USD", "verdict": "PASS",
        "summary": {"symbols": n_per_date},
        "config": {"derived_dir": str(derived_dir), "features_dir": str(features_dir), "prune_recs": str(prune)},
    }))
    return {"derived": derived_dir, "features": features_dir, "prune": prune, "preflight": preflight,
            "keep": list(keep), "n_per_date": n_per_date, "n_dates": n_dates}


def _paths(market: dict) -> tuple[dict, dict]:
    derived = {p.stem: p for p in sorted(market["derived"].glob("*.parquet"))}
    features = {p.stem: p for p in sorted(market["features"].glob("*.parquet"))}
    return derived, features


# --------------------------------------------------------------------------- #
# state coding
# --------------------------------------------------------------------------- #
def test_state_layout_covers_both_binnings_without_overlap():
    layout = state_layout()
    codes = [c for _b, _i, c in layout]
    assert len(codes) == len(set(codes)) == 8
    assert [b for b, _i, _c in layout].count("quintile") == 5
    assert [b for b, _i, _c in layout].count("tercile") == 3
    assert max(codes) == N_STATES - 1


def test_state_codes_pack_quintiles_and_terciles_and_ties_go_up():
    values = np.arange(1, 11, dtype="float64")
    pos = np.zeros(10, dtype="int64")
    q = quantile_edges(values, pos, 1, QUANTILES["quintile"], BINNINGS["quintile"])
    codes_q = state_codes(values, q, pos, offset=STATE_OFFSET["quintile"])
    t = quantile_edges(values, pos, 1, QUANTILES["tercile"], BINNINGS["tercile"])
    codes_t = state_codes(values, t, pos, offset=STATE_OFFSET["tercile"])
    assert q.tolist() == [[2.0, 4.0, 6.0, 8.0]]
    assert codes_q.tolist() == [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
    assert codes_t.tolist() == [5, 5, 5, 5, 6, 6, 6, 7, 7, 7]
    # value exactly on an edge (4.0 -> tercile edge) lands in the upper bin
    assert codes_t[3] == 5 and codes_t[4] == 6


def test_state_codes_undefined_for_nan_and_undersized_dates():
    values = np.array([np.nan, 2.0, 3.0, 4.0], dtype="float64")
    pos = np.zeros(4, dtype="int64")
    # 3 finite names: quintiles undefined, terciles defined
    q = quantile_edges(values, pos, 1, QUANTILES["quintile"], BINNINGS["quintile"])
    assert np.isnan(q).all()
    assert (state_codes(values, q, pos) == -1).all()
    t = quantile_edges(values, pos, 1, QUANTILES["tercile"], BINNINGS["tercile"])
    codes = state_codes(values, t, pos, offset=STATE_OFFSET["tercile"])
    assert codes[0] == -1
    assert set(codes[1:].tolist()) <= {5, 6, 7}


def test_classify_target_keeps_unexpected_values_out_of_neither():
    classes = classify_target(np.array([1.0, -1.0, 0.0, np.nan, 2.0, -3.0]))
    assert classes.tolist() == [0, 1, 2, -1, -1, -1]


# --------------------------------------------------------------------------- #
# streaming accumulation
# --------------------------------------------------------------------------- #
def test_collect_state_counts_is_block_invariant(tmp_path):
    market = _toy_market(tmp_path, n_per_date=10, n_dates=12)
    derived, features = _paths(market)
    dates = global_dates(market["derived"])
    one = collect_state_counts(derived, features, market["keep"], dates, block_size=100)
    many = collect_state_counts(derived, features, market["keep"], dates, block_size=3)
    for key in ("state_counts", "feature_totals", "universe", "state_symbols"):
        assert np.array_equal(one[key], many[key]), key


def test_collect_state_counts_universe_and_breadth(tmp_path):
    market = _toy_market(tmp_path, n_per_date=10, n_dates=12)
    derived, features = _paths(market)
    dates = global_dates(market["derived"])
    counts = collect_state_counts(derived, features, market["keep"], dates)
    usable_rows = 10 * 12 - 2  # two deliberate NaN targets on the first date
    assert int(counts["universe"].sum()) == usable_rows
    for binning_index_ in range(len(BINNING_ORDER)):
        assert int(counts["feature_totals"][0, binning_index_].sum()) == usable_rows
    assert int(counts["other"].sum()) == 0
    # every one of the 10 symbols contributes to the top quintile of adx_3
    adx_index = market["keep"].index("adx_3")
    code = STATE_OFFSET["quintile"] + 4
    assert int((counts["state_symbols"][adx_index, code] > 0).sum()) == 10


def test_collect_state_counts_all_nan_feature_has_no_states(tmp_path):
    market = _toy_market(tmp_path, nan_feature="adx_3")
    derived, features = _paths(market)
    dates = global_dates(market["derived"])
    counts = collect_state_counts(derived, features, market["keep"], dates)
    adx_index = market["keep"].index("adx_3")
    assert int(counts["state_counts"][adx_index].sum()) == 0
    assert int(counts["feature_totals"][adx_index].sum()) == 0


# --------------------------------------------------------------------------- #
# rates
# --------------------------------------------------------------------------- #
def test_rate_block_reports_pooled_date_mean_and_ci():
    counts = np.zeros((len(CLASSES), 4))
    totals = np.full(4, 10.0)
    counts[0] = 8.0  # up
    counts[1] = 1.0  # dn
    counts[2] = 1.0  # neither
    record = rate_block(counts, totals, 40)
    assert record["estimable"] is True
    assert record["unevaluable_reason"] is None
    assert sums_to_one(record["rates"])
    assert record["rates"]["up"] == pytest.approx(0.8)
    assert record["pooled"]["up"] == pytest.approx(0.8)
    for cls in CLASSES:
        assert np.isfinite(record["ci"][cls]["ci_low"]) and np.isfinite(record["ci"][cls]["ci_high"])


def test_rate_block_marks_insufficient_groups_unevaluable():
    counts = np.zeros((len(CLASSES), 2))
    counts[0] = [5.0, 5.0]
    record = rate_block(counts, np.array([5.0, 5.0]), 10)
    assert record["estimable"] is False
    assert "n<" in record["unevaluable_reason"]


# --------------------------------------------------------------------------- #
# report assembly + self-check
# --------------------------------------------------------------------------- #
def _report(market: dict) -> dict:
    report = run_atlas(
        deriv_dir=market["derived"],
        feat_dir=market["features"],
        prune_path=market["prune"],
        preflight_path=market["preflight"],
        block_size=5,
    )
    return report


def test_run_atlas_produces_complete_report(tmp_path):
    market = _toy_market(tmp_path, n_per_date=10, n_dates=12)
    report = _report(market)
    assert report["verdict"] == "PASS", report["checks"]
    assert report["target"] == PRIMARY_TARGET
    assert report["scope"].startswith("USD only")
    assert sorted(report["features"]) == sorted(market["keep"])
    for feature in market["keep"]:
        for binning, n_bins in BINNINGS.items():
            assert len(report["features"][feature]["states"][binning]) == n_bins
    assert report["coverage"]["cells_total"] == len(market["keep"]) * 8
    assert all(report["checks"][k]["ok"] for k in report["checks"])
    assert report["unconditional"][PRIMARY_TARGET]["rates"]["up"] > 0


def test_run_atlas_marks_all_nan_feature_unevaluable(tmp_path):
    market = _toy_market(tmp_path, nan_feature="adx_3")
    report = _report(market)
    cells = report["features"]["adx_3"]["states"]["quintile"]
    assert all(not c["estimable"] for c in cells)
    assert all(c["unevaluable_reason"] for c in cells)
    assert "adx_3" in report["coverage"]["features_without_estimable_cells"]
    # a fully unevaluable feature must not break the acceptance self-check
    assert report["verdict"] == "PASS", report["checks"]


def test_run_atlas_requires_preflight_before_writing(tmp_path):
    market = _toy_market(tmp_path, n_dates=6)
    market["preflight"].unlink()
    with pytest.raises(PreflightError, match="preflight report missing"):
        _report(market)
    market["preflight"].write_text(json.dumps({"market": "USD", "verdict": "FAIL"}))
    with pytest.raises(PreflightError, match="not verified"):
        _report(market)


def test_run_atlas_rejects_non_usd_market(tmp_path):
    market = _toy_market(tmp_path, n_dates=6)
    with pytest.raises(PreflightError, match="USD-only"):
        run_atlas(deriv_dir=market["derived"], feat_dir=market["features"], prune_path=market["prune"],
                  preflight_path=market["preflight"], market="CAD")


def test_check_atlas_report_flags_each_acceptance_rule(tmp_path):
    market = _toy_market(tmp_path, n_per_date=20, n_dates=12)  # bins big enough to be estimable
    report = _report(market)
    assert all(ok for ok, _ in check_atlas_report(report).values())
    assert report["features"]["adx_3"]["states"]["quintile"][0]["estimable"] is True

    broken = json.loads(json.dumps(report, default=str))
    broken["features"]["adx_3"]["states"]["quintile"].pop()
    assert not check_atlas_report(broken)["cells_represented_or_marked"][0]

    broken = json.loads(json.dumps(report, default=str))
    broken["features"]["adx_3"]["states"]["quintile"][0]["rates"]["up"] += 0.2
    assert not check_atlas_report(broken)["estimable_rates_sum_to_one"][0]

    broken = json.loads(json.dumps(report, default=str))
    broken["features"]["adx_3"]["states"]["quintile"][0]["ci"]["up"]["ci_low"] = None
    assert not check_atlas_report(broken)["cis_present"][0]

    broken = json.loads(json.dumps(report, default=str))
    broken["family_representativeness"].pop("fib_dist")
    assert not check_atlas_report(broken)["flagged_families_checked"][0]

    broken = json.loads(json.dumps(report, default=str))
    broken["unconditional"][PRIMARY_TARGET]["rates"] = {"up": 0.9, "dn": 0.9, "neither": 0.9}
    assert not check_atlas_report(broken)["unconditional_split_present"][0]

    broken = json.loads(json.dumps(report, default=str))
    broken["features"].pop("adx_3")
    assert not check_atlas_report(broken)["all_features_present"][0]


def test_format_markdown_states_scope_and_families(tmp_path):
    market = _toy_market(tmp_path, n_per_date=10, n_dates=12)
    md = format_markdown(_report(market))
    assert "G1 condition atlas" in md
    assert "Unconditional split" in md
    assert "Flagged family representativeness" in md
    assert "no shortlist" in md.lower()


def test_write_report_roundtrips_through_check_report(tmp_path):
    market = _toy_market(tmp_path, n_per_date=10, n_dates=12)
    report = _report(market)
    json_path = tmp_path / "atlas.json"
    md_path = tmp_path / "atlas.md"
    write_report(report, json_path, md_path)
    assert json.loads(json_path.read_text())["verdict"] == "PASS"
    assert md_path.read_text().startswith("# WI-018 G1")
    rc = main(["--market", "USD", "--check-report", str(json_path)])
    assert rc == 0
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"market": "USD", "verdict": "FAIL", "features": {}, "config": {}}))
    assert main(["--market", "USD", "--check-report", str(bad)]) == 1
    assert main(["--market", "USD", "--check-report", str(tmp_path / "absent.json")]) == 1


# --------------------------------------------------------------------------- #
# flagged family representativeness
# --------------------------------------------------------------------------- #
def test_family_representativeness_sign_and_magnitude_rules(tmp_path):
    """Three families, three verdicts: sign-flipped kept, strong kept, weak kept."""
    market = _toy_market(tmp_path, n_per_date=10, n_dates=30)
    derived, features = _paths(market)
    dates = global_dates(market["derived"])
    rng = np.random.default_rng(0)
    for sym, path in features.items():
        frame = pq.read_table(path).to_pandas()
        target = pq.read_table(derived[sym]).to_pandas()["first_touch_34"]
        signed = target.fillna(0.0).astype("float32").to_numpy()  # +1 top rank, -1 bottom rank
        # reconstruction: use the fixture's rank feature as the family signal
        ranks = frame["atr_pct_34"].to_numpy()
        frame["atr_pct_34"] = (-ranks + rng.normal(0, 3, size=ranks.size)).astype("float32")  # flipped + weak
        frame["atr_pct_144"] = ranks.astype("float32")                # same sign, full strength
        frame["fib_dist_34"] = ranks.astype("float32")                # kept is the family best
        frame["fib_dist_55"] = (ranks * 0.5 + rng.normal(0, 5, size=ranks.size)).astype("float32")
        frame["range_pos_34"] = (ranks + rng.normal(0, 20, size=ranks.size)).astype("float32")  # weak
        frame["range_pos_89"] = ranks.astype("float32")               # strong, dropped
        frame["adx_3"] = signed
        pq.write_table(pa.Table.from_pandas(frame, preserve_index=False), path)

    result = family_representativeness(derived, features, market["keep"], dates, block_size=7)
    assert set(result) == {"atr_pct", "fib_dist", "range_pos"}
    assert result["atr_pct"]["kept_column"] == "atr_pct_34"
    assert result["atr_pct"]["representative"] is False
    assert result["atr_pct"]["same_sign_as_family_best"] is False
    assert result["fib_dist"]["kept_column"] == result["fib_dist"]["family_best_column"] == "fib_dist_34"
    assert result["fib_dist"]["representative"] is True
    assert result["fib_dist"]["retained_share"] >= FAMILY_REPRESENTATIVE_SHARE
    assert result["range_pos"]["representative"] is False
    assert result["range_pos"]["same_sign_as_family_best"] is True
    assert result["range_pos"]["retained_share"] < FAMILY_REPRESENTATIVE_SHARE
    for family in result:
        assert result[family]["n_columns"] == 2
        assert "within-date Spearman" in result[family]["estimator"]


def test_family_representativeness_handles_a_family_with_no_signal(tmp_path):
    market = _toy_market(tmp_path, n_per_date=10, n_dates=30)
    derived, features = _paths(market)
    dates = global_dates(market["derived"])
    for path in features.values():
        frame = pq.read_table(path).to_pandas()
        for col in ("atr_pct_34", "atr_pct_144"):
            frame[col] = 0.0  # zero dispersion per date -> IC undefined
        pq.write_table(pa.Table.from_pandas(frame, preserve_index=False), path)
    result = family_representativeness(derived, features, market["keep"], dates, block_size=7)
    entry = result["atr_pct"]
    assert entry["representative"] is False
    assert np.isnan(entry["retained_share"])


# --------------------------------------------------------------------------- #
# on-disk integration (skipped until the real artifacts exist)
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not DISK_ATLAS.is_file(), reason="WI-018 atlas not generated yet")
def test_disk_atlas_report_passes_acceptance_checks():
    report = json.loads(DISK_ATLAS.read_text())
    checks = check_atlas_report(report)
    bad = {k: v for k, v in checks.items() if not v[0]}
    assert not bad, bad
    assert report["market"] == "USD"
    assert report["config"]["n_features"] == 88
    assert report["coverage"]["cells_estimable"] > 0
    assert all(name in report["family_representativeness"] for name in ("atr_pct", "fib_dist", "range_pos"))
    assert Path("reports/wi018/atlas_USD.md").is_file()
