"""WI-018 step 4 regression tests — the conditional cost overlay and the memo.

Locks: the G2 gate (no survivors -> G3 skipped, standing `NO_TRADE`), the cost
math (`net_bps == |IC| * 1000 - 25` via `src.wi016.probe.cost_overlay`), the
`NO_TRADE`-by-default branch (nonpositive net, or an IC that is not estimable),
the hold that G3 emits **no executable rules and no shortlist**, and the memo
content (G1 deliverable, G2 verdict, G3 outcome, limitations, follow-up).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.wi016.probe import IC_TO_BPS, cost_overlay
from src.wi018 import COST_BPS_TOTAL, MARKET, PRIMARY_TARGET, SECONDARY_TARGETS
from src.wi018.cost_overlay import (
    G3_VERDICTS,
    build_summary_markdown,
    check_g3_report,
    condition_ic_series,
    evaluate_condition,
    format_g3_markdown,
    main,
    run_g3,
    survivor_conditions,
    write_outputs,
)
from src.wi018.data_probe import PreflightError

DISK_G3 = Path("reports/wi018/g3_USD.json")
DISK_MEMO = Path("reports/wi018/summary_USD.md")


# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #
def _toy_market(tmp_path: Path, n_symbols: int = 12, n_dates: int = 400) -> dict:
    """A small USD market with one strong directional feature and one noise feature.

    `signal_34` ranks each date's names 1..n and the target is up-first with
    probability rising in the rank (plus 8% down-first), so the top-quintile
    condition has a real held-out IC; `noise_34` is unrelated.
    """
    tmp_path.mkdir(parents=True, exist_ok=True)
    derived_dir = tmp_path / "derived"
    features_dir = tmp_path / "features"
    derived_dir.mkdir(exist_ok=True)
    features_dir.mkdir(exist_ok=True)
    dates = pd.bdate_range("2016-01-04", periods=n_dates)
    rng = np.random.default_rng(11)
    ranks = np.concatenate([rng.permutation(n_symbols) + 1 for _ in range(n_dates)]).astype("float32")
    score = (ranks - 1.0) / (n_symbols - 1.0)
    draw = rng.random(ranks.size)
    target = np.where(draw < 0.10 + 0.80 * score, 1.0, np.where(draw > 0.92, -1.0, 0.0)).astype("float32")
    columns = {"signal_34": ranks, "noise_34": rng.normal(size=ranks.size).astype("float32")}
    for j in range(n_symbols):
        take = slice(j, None, n_symbols)
        pq.write_table(
            pa.table({"date": pa.array(dates.to_numpy()).cast(pa.date32()),
                      **{name: column[take] for name, column in columns.items()}}),
            features_dir / f"SYM{j:02d}.parquet",
        )
        pq.write_table(
            pa.table({"date": pa.array(dates.to_numpy()).cast(pa.date32()),
                      **{name: target[take] for name in (PRIMARY_TARGET, *SECONDARY_TARGETS)}}),
            derived_dir / f"SYM{j:02d}.parquet",
        )
    prune = tmp_path / "run5_prune_recs.json"
    prune.write_text(json.dumps({"n_features": len(columns), "n_keep": len(columns),
                                 "keep_columns": list(columns)}))
    preflight = tmp_path / "preflight_USD.json"
    preflight.write_text(json.dumps({
        "market": MARKET, "verdict": "PASS", "summary": {"symbols": n_symbols, "total_rows": n_symbols * n_dates},
        "config": {"derived_dir": str(derived_dir), "features_dir": str(features_dir), "prune_recs": str(prune)},
    }))
    return {"derived": derived_dir, "features": features_dir, "prune": prune, "preflight": preflight,
            "keep": list(columns), "n_symbols": n_symbols, "n_dates": n_dates}


def _probe_report(market: dict, survivors: list[dict], passed: bool = True, red_flag: bool = False) -> Path:
    path = Path(market["prune"]).parent / "probe_USD.json"
    eligible = passed and not red_flag
    reason = None
    if not passed:
        reason = "no condition cleared the out-of-fold CI, BH-FDR 5% and the same-sign bar"
    elif red_flag:
        reason = "survivor density 0.685 > 0.1: a wall of survivors is a noise/leakage red flag, not a win"
    path.write_text(json.dumps({
        "market": MARKET, "target": PRIMARY_TARGET, "generated_utc": "2026-11-01T00:00:00Z",
        "verdict": "G2_PASS_WITH_RED_FLAG" if red_flag else ("G2_PASS" if passed else "G2_FAIL"),
        "g2_pass": passed, "red_flag": red_flag, "g3_eligible": eligible,
        "g3_skipped": not eligible, "g3_skip_reason": reason, "survivors": survivors if passed else [],
        "config": {"fdr_alpha": 0.05, "embargo_td": 34, "decision_rule": "CI excludes zero AND BH-FDR AND same-sign",
                   "secondary_role": "robustness reads only — never selection targets"},
        "hypotheses": {"n_total": 2600, "n_univariate": 1408, "n_conjunction": len(survivors),
                       "n_survivors": len(survivors) if passed else 0, "survivor_density": 0.001},
        "folds": [{"fold": i, "val_pos_min": 1, "label_end_pos": 2} for i in range(5)],
    }))
    return path


def _survivor(condition: str, feature: str, code: int, direction: str = "up", **over) -> dict:
    record = {"kind": "univariate", "condition": condition, "feature": feature, "code": code,
              "direction": direction, "lift": 0.2, "ci_low": 0.1, "ci_high": 0.3, "q": 0.001,
              "n_dates": 240, "n": 500}
    record.update(over)
    return record


def _run(market: dict, probe: Path, **kwargs) -> dict:
    return run_g3(
        probe_path=probe,
        preflight_path=market["preflight"],
        deriv_dir=market["derived"],
        feat_dir=market["features"],
        prune_path=market["prune"],
        block_size=64,
        **kwargs,
    )


# --------------------------------------------------------------------------- #
# cost math (pure)
# --------------------------------------------------------------------------- #
def test_evaluate_condition_matches_wi016_cost_overlay():
    rng = np.random.default_rng(3)
    series = {"ic": rng.normal(0.05, 0.01, size=200)}
    condition = {"condition": "f|quintile/5", "kind": "univariate", "direction": "up",
                 "features": ["f"], "g2_lift": 0.2, "g2_ci_low": 0.1, "g2_ci_high": 0.3, "g2_q": 0.001}
    record = evaluate_condition(condition, series)
    reference = cost_overlay(float(series["ic"].mean()), cost_bps=COST_BPS_TOTAL)
    assert record["ic"] == pytest.approx(float(series["ic"].mean()))
    assert record["gross_bps"] == pytest.approx(reference["gross_bps"])
    assert record["net_bps"] == pytest.approx(reference["net_bps"])
    assert record["decision"] == "TRADE" and reference["tradeable"] is True
    assert record["net_bps"] == pytest.approx(abs(record["ic"]) * IC_TO_BPS - COST_BPS_TOTAL)


def test_no_trade_when_net_edge_is_nonpositive():
    series = {"ic": np.full(200, 0.01)}  # gross 10 bps < 25 bps cost
    condition = {"condition": "f|tercile/1", "kind": "univariate", "direction": "dn",
                 "features": ["f"], "g2_lift": -0.02, "g2_ci_low": -0.03, "g2_ci_high": -0.01, "g2_q": 0.04}
    record = evaluate_condition(condition, series)
    assert record["net_bps"] == pytest.approx(10.0 - COST_BPS_TOTAL)
    assert record["decision"] == "NO_TRADE"


def test_no_trade_when_ic_is_not_estimable():
    condition = {"condition": "f|quintile/1", "kind": "univariate", "direction": "up",
                 "features": ["f"], "g2_lift": 0.1, "g2_ci_low": 0.05, "g2_ci_high": 0.15, "g2_q": 0.01}
    empty = evaluate_condition(condition, {"ic": np.array([])})
    assert empty["decision"] == "NO_TRADE" and empty["estimable"] is False
    assert "n_dates<" in empty["reason"]
    # a strong IC but too few dates to estimate is also NO_TRADE (default is the safe branch)
    short = evaluate_condition(condition, {"ic": np.full(5, 0.5)}, min_dates=60)
    assert short["decision"] == "NO_TRADE" and short["estimable"] is False


def test_default_decision_is_never_trade_without_a_positive_net():
    series = {"ic": np.zeros(200)}  # zero IC -> gross 0 -> net -25
    condition = {"condition": "f|quintile/3", "kind": "univariate", "direction": "up",
                 "features": ["f"], "g2_lift": 0.0, "g2_ci_low": 0.0, "g2_ci_high": 0.0, "g2_q": 0.9}
    record = evaluate_condition(condition, series)
    assert record["gross_bps"] == 0.0 and record["decision"] == "NO_TRADE"
    assert G3_VERDICTS == ("TRADE", "NO_TRADE", "SKIPPED")


# --------------------------------------------------------------------------- #
# survivor -> condition plumbing
# --------------------------------------------------------------------------- #
def test_survivor_conditions_reads_univariate_and_conjunction_terms():
    keep = ["a", "b", "c"]
    report = {"survivors": [
        {"kind": "univariate", "condition": "a|quintile/5", "feature": "a", "code": 4, "direction": "up",
         "lift": 0.2, "ci_low": 0.1, "ci_high": 0.3, "q": 0.01, "n_dates": 200},
        {"kind": "conjunction", "condition": "a|quintile/5 & c|tercile/1", "pair": [0, 4, 2, 5],
         "direction": "dn", "lift": -0.15, "ci_low": -0.2, "ci_high": -0.1, "q": 0.02, "n_dates": 200},
    ]}
    conditions = survivor_conditions(report, keep)
    assert conditions[0]["terms"] == [("a", 4)] and conditions[0]["sign"] == 1.0
    assert conditions[1]["terms"] == [("a", 4), ("c", 5)] and conditions[1]["sign"] == -1.0
    assert conditions[1]["features"] == ["a", "c"]


# --------------------------------------------------------------------------- #
# gate: G2 failure -> G3 skipped
# --------------------------------------------------------------------------- #
def test_run_g3_skips_when_g2_failed(tmp_path):
    market = _toy_market(tmp_path)
    probe = _probe_report(market, [], passed=False)
    report = _run(market, probe)
    assert report["g3_skipped"] is True
    assert report["g3_decision"] == "SKIPPED"
    assert report["conditions"] == [] and report["n_tradeable"] == 0
    assert "same-sign" in report["skip_reason"]
    assert report["config"]["executable_output"] is False
    assert all(ok for ok, _ in check_g3_report(report).values())
    body = format_g3_markdown(report)
    assert "SKIPPED" in body and "NO_TRADE" in body


def test_run_g3_skips_when_g2_raised_the_red_flag(tmp_path):
    # A wall of survivors is pre-registered as a red flag, not a win, so the
    # conditional G3 must not be invoked on it even though survivors exist.
    market = _toy_market(tmp_path)
    probe = _probe_report(market, [_survivor("signal_34|quintile/5", "signal_34", 4)], red_flag=True)
    report = _run(market, probe)
    assert report["g3_skipped"] is True and report["g3_decision"] == "SKIPPED"
    assert report["g2_pass"] is True and report["g2_red_flag"] is True
    assert report["g2_survivors_available"] == 1 and report["conditions"] == []
    assert "red flag" in report["skip_reason"]
    assert all(ok for ok, _ in check_g3_report(report).values())
    memo = build_summary_markdown(g3=report, probe=json.loads(probe.read_text()))
    assert "wall" in memo and "NO_TRADE" in memo


def test_run_g3_requires_the_probe_report(tmp_path):
    market = _toy_market(tmp_path)
    with pytest.raises(PreflightError, match="probe report missing"):
        _run(market, tmp_path / "absent.json")


def test_run_g3_rejects_non_usd_market(tmp_path):
    market = _toy_market(tmp_path)
    probe = _probe_report(market, [], passed=False)
    with pytest.raises(PreflightError, match="USD-only"):
        run_g3(
            probe_path=probe, preflight_path=market["preflight"], deriv_dir=market["derived"],
            feat_dir=market["features"], prune_path=market["prune"], market="CAD",
        )


# --------------------------------------------------------------------------- #
# end-to-end on a market with a real condition
# --------------------------------------------------------------------------- #
def test_run_g3_costs_g2_survivors(tmp_path):
    market = _toy_market(tmp_path)
    probe = _probe_report(market, [_survivor("signal_34|quintile/5", "signal_34", 4)])
    report = _run(market, probe)
    assert report["g3_skipped"] is False
    assert report["n_conditions"] == 1
    record = report["conditions"][0]
    assert np.isfinite(record["ic"]) and record["ic"] > 0.025  # the honest condition clears cost
    assert record["decision"] == "TRADE"
    assert report["g3_decision"] == "TRADE"
    assert report["held_out_dates"] >= 60
    assert len(report["folds"]) == 5
    assert all(ok for ok, _ in check_g3_report(report).values()), report["checks"]


def test_run_g3_marks_everything_no_trade_when_ic_is_unevaluable(tmp_path):
    market = _toy_market(tmp_path)
    probe = _probe_report(market, [
        _survivor("signal_34|quintile/5", "signal_34", 4),
        _survivor("noise_34|quintile/1", "noise_34", 0, direction="dn"),
    ])
    report = _run(market, probe, min_dates=10_000)
    assert report["g3_decision"] == "NO_TRADE"
    assert report["n_tradeable"] == 0
    assert all(c["decision"] == "NO_TRADE" and c["estimable"] is False for c in report["conditions"])
    assert all("n_dates<10000" in c["reason"] for c in report["conditions"])
    assert all(ok for ok, _ in check_g3_report(report).values())


def test_condition_ic_series_uses_held_out_dates_only(tmp_path):
    market = _toy_market(tmp_path)
    from src.wi018.data_probe import symbol_paths
    from src.wi018.probe import held_out_positions
    from src.wi018.streaming import global_dates

    dates = global_dates(market["derived"])
    held, _detail = held_out_positions(dates)
    conditions = survivor_conditions(
        {"survivors": [_survivor("signal_34|quintile/5", "signal_34", 4)]}, market["keep"]
    )
    series = condition_ic_series(
        conditions, symbol_paths(market["derived"]), symbol_paths(market["features"]), dates, held, block_size=64
    )[0]
    assert series["ic"].size == int(held.sum())  # one IC per held-out date, no in-sample date
    assert series["ic"].size < dates.size
    assert np.isfinite(series["ic"]).all()
    assert float(series["ic"].mean()) > 0.0


def test_run_g3_is_deterministic(tmp_path):
    market = _toy_market(tmp_path)
    probe = _probe_report(market, [_survivor("signal_34|quintile/5", "signal_34", 4)])
    first = _run(market, probe)
    second = _run(market, probe)
    first.pop("generated_utc"), second.pop("generated_utc")
    assert json.dumps(first, sort_keys=True, default=str) == json.dumps(second, sort_keys=True, default=str)


# --------------------------------------------------------------------------- #
# acceptance self-check
# --------------------------------------------------------------------------- #
def test_check_g3_report_flags_each_rule(tmp_path):
    market = _toy_market(tmp_path)
    probe = _probe_report(market, [_survivor("signal_34|quintile/5", "signal_34", 4)])
    report = _run(market, probe)
    assert all(ok for ok, _ in check_g3_report(report).values())

    broken = json.loads(json.dumps(report, default=str))
    broken["scope"] = "CAD too"
    assert not check_g3_report(broken)["usd_only_scope_recorded"][0]

    broken = json.loads(json.dumps(report, default=str))
    broken["config"]["cost_assumptions"] = "measured"
    assert not check_g3_report(broken)["cost_assumption_labelled"][0]

    broken = json.loads(json.dumps(report, default=str))
    broken["config"]["proxy_warning"] = "a P&L model"
    assert not check_g3_report(broken)["screening_proxy_labelled"][0]

    broken = json.loads(json.dumps(report, default=str))
    broken["ship_shape"] = "shortlist CSV"
    assert not check_g3_report(broken)["no_executable_output"][0]

    broken = json.loads(json.dumps(report, default=str))
    broken["g3_decision"] = "NO_TRADE"  # TRADE survivors but a NO_TRADE verdict
    assert not check_g3_report(broken)["gating_matches_g2"][0]

    broken = json.loads(json.dumps(report, default=str))
    broken["conditions"][0]["net_bps"] = -10.0  # a TRADE that lost money on costs
    assert not check_g3_report(broken)["trade_requires_positive_net"][0]

    broken = json.loads(json.dumps(report, default=str))
    broken["conditions"][0]["net_bps"] = 999.0
    assert not check_g3_report(broken)["cost_math_matches_helper"][0]

    skipped = _run(market, _probe_report(market, [], passed=False))
    broken = json.loads(json.dumps(skipped, default=str))
    broken["g3_decision"] = "TRADE"
    assert not check_g3_report(broken)["gating_matches_g2"][0]


# --------------------------------------------------------------------------- #
# memo
# --------------------------------------------------------------------------- #
def test_build_summary_markdown_states_verdicts_and_ship_shape(tmp_path):
    market = _toy_market(tmp_path)
    probe = _probe_report(market, [_survivor("signal_34|quintile/5", "signal_34", 4)])
    g3 = _run(market, probe)
    memo = build_summary_markdown(
        g3=g3,
        probe=json.loads(probe.read_text()),
        atlas={"coverage": {"cells_total": 704, "cells_estimable": 702, "cells_unevaluable": 2},
               "summary": {"n_dates": 5032},
               "unconditional": {PRIMARY_TARGET: {"pooled": {"up": 0.3756, "dn": 0.2971, "neither": 0.3273}}}},
        preflight={"verdict": "PASS", "summary": {"symbols": 593, "total_rows": 2340073,
                                                  "date_min": "2006-10-26", "date_max": "2026-10-28"}},
    )
    for token in ("G1", "G2", "G3", "NO_TRADE", "assumption", "memo", "Limitations", "Follow-up"):
        assert token in memo
    assert "no shortlist CSV" in memo.lower() or "no shortlist csv" in memo.lower()
    assert "US" in memo

    skipped = _run(market, _probe_report(market, [], passed=False))
    skipped_memo = build_summary_markdown(g3=skipped, probe=json.loads(probe.read_text()))
    assert "SKIPPED" in skipped_memo and "NO_TRADE" in skipped_memo
    assert "No follow-up warranted" in skipped_memo

    red = _run(market, probe)
    red["g2_red_flag"] = True
    probe_body = json.loads(probe.read_text())
    probe_body["red_flag"] = True
    assert "red flag" in build_summary_markdown(g3=red, probe=probe_body)


def test_write_outputs_writes_only_the_json_and_the_memo(tmp_path):
    market = _toy_market(tmp_path)
    probe = _probe_report(market, [])
    report = _run(market, probe)
    memo = build_summary_markdown(g3=report, probe=json.loads(probe.read_text()))
    out_dir = tmp_path / "out"
    json_path, md_path = write_outputs(report, memo, out_dir / "g3.json", out_dir / "summary.md")
    written = sorted(p.name for p in out_dir.iterdir())
    assert written == ["g3.json", "summary.md"]
    assert not any(p.suffix.lower() == ".csv" for p in out_dir.iterdir())
    assert json.loads(json_path.read_text())["market"] == MARKET
    assert md_path.read_text().startswith("# WI-018")


def test_cli_check_report_and_missing_file(tmp_path, capsys):
    market = _toy_market(tmp_path)
    probe = _probe_report(market, [_survivor("signal_34|quintile/5", "signal_34", 4)])
    report = _run(market, probe)
    out = tmp_path / "g3.json"
    out.write_text(json.dumps(report, default=str))
    assert main(["--market", "USD", "--check-report", str(out)]) == 0
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"market": MARKET, "config": {}, "conditions": [], "g3_decision": "TRADE"}))
    assert main(["--market", "USD", "--check-report", str(bad)]) == 1
    assert main(["--market", "USD", "--check-report", str(tmp_path / "absent.json")]) == 1


# --------------------------------------------------------------------------- #
# on-disk integration (skipped until the real artifacts exist)
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not DISK_G3.is_file(), reason="WI-018 G3 not generated yet")
def test_disk_g3_and_memo_agree():
    report = json.loads(DISK_G3.read_text())
    checks = check_g3_report(report)
    bad = {k: v for k, v in checks.items() if not v[0]}
    assert not bad, bad
    assert report["market"] == MARKET
    assert report["config"]["cost_bps_total"] == COST_BPS_TOTAL
    assert report["g3_decision"] in G3_VERDICTS
    assert report["ship_shape"].endswith("no trading integration")
    memo = DISK_MEMO.read_text()
    for token in ("G1", "G2", "G3", "NO_TRADE", "assumption", "memo"):
        assert token in memo
    assert report["g3_decision"] in memo or report["g3_skipped"]
