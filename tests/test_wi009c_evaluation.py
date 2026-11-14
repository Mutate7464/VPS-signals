"""WI-009c Step 5 — final evaluation and the human gate package.

Locks the acceptance criteria of
`docs/plans/2026-10-25-WI-009c-classifier-route.md` Step 5(b):

* the summary is reproducible from the saved run outputs (recomputed masses match the
  run record, and the shortlist matches its declared composite);
* the report lists the exact model/fold/run, shows `P(up)`, `P(down)`, `P(stay)` and the
  declared composite;
* negative results are distinguished from execution/test failures, and the claim/use
  decision is left to the human gate (no gate marked passed, no order wiring).

The tests are cheap: they parse the saved reports and re-reduce the saved OOF parquet.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts.evaluate_wi009c import (
    build_summary,
    check_reproducible,
    load_run_record,
    load_shortlist,
    parse_labels_cleared,
    parse_probe_verdicts,
    recompute_from_oof,
    robustness_summary,
)

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "reports" / "wi009c_probe.md"
RUN_JSON = ROOT / "reports" / "wi009c_regression_CAD.json"
OOF = ROOT / "data" / "wi009c_oof_CAD.parquet"
SHORTLIST = ROOT / "reports" / "wi009c_shortlist_CAD.csv"

SAMPLE_TABLE = """# probe

## Verdict summary (skill bar: clause a = same-sign AND |IC| >=, clause b = |t|>2 with stable sub-window sign)

| Target | OOF logit IC | t | same sign | clause (a) | clause (b) | skill bar |
| :--- | ---: | ---: | :--- | :--- | :--- | :--- |
| `y_20d_up` | +0.0123 | +3.15 | NO | FAIL | FAIL | **NEGATIVE RESULT** |
| `y_20d_stay` | -0.0355 | -10.06 | yes | FAIL | PASS | **NEGATIVE RESULT** |

- 0/5 targets clear the unchanged skill bar
- **Step 2 gate:** no label demonstrated learnable — no 89-feature spend; limit the continuous baseline to the same five factors.
"""


# --------------------------------------------------------------------------- #
# parsers (synthetic, so they run without the artifacts)
# --------------------------------------------------------------------------- #
def test_parse_probe_verdicts_reads_every_row_with_its_clauses():
    rows = parse_probe_verdicts(SAMPLE_TABLE)
    assert [r["target"] for r in rows] == ["y_20d_up", "y_20d_stay"]
    assert rows[0]["ic"] == pytest.approx(0.0123) and rows[0]["same_sign"] is False
    assert rows[0]["clause_a"] == "FAIL" and rows[0]["skill_bar"] == "NEGATIVE RESULT"
    assert rows[1]["same_sign"] is True and rows[1]["clause_b"] == "PASS"


def test_parse_probe_verdicts_returns_nothing_for_an_unrelated_body():
    assert parse_probe_verdicts("no table here") == []
    assert parse_probe_verdicts("") == []


def test_parse_labels_cleared_is_fail_closed():
    assert parse_labels_cleared(SAMPLE_TABLE) == (0, 5)
    assert parse_labels_cleared("- 3/5 targets clear the unchanged skill bar") == (3, 5)
    assert parse_labels_cleared("") == (0, 0)


# --------------------------------------------------------------------------- #
# reproducibility against the real saved outputs
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not (PROBE.exists() and RUN_JSON.exists() and OOF.exists() and SHORTLIST.exists()),
                    reason="WI-009c run outputs not present")
class TestRealOutputs:
    def test_the_saved_probe_reports_five_negative_targets(self):
        rows = parse_probe_verdicts(PROBE.read_text())
        assert len(rows) == 5
        assert {r["target"] for r in rows} == {
            "y_15d_high", "y_15d_low", "y_20d_up", "y_20d_down", "y_20d_stay"
        }
        assert all(r["skill_bar"] == "NEGATIVE RESULT" for r in rows)
        assert all(r["clause_a"] == "FAIL" for r in rows)
        assert parse_labels_cleared(PROBE.read_text()) == (0, 5)

    def test_the_run_record_is_the_production_run_not_a_smoke_run(self):
        rec = load_run_record(RUN_JSON)
        assert rec["smoke"] is False
        assert rec["n_viable_folds"] == 5 and len(rec["folds"]) == 5
        assert all(f["purge_ok"] for f in rec["folds"])
        assert all(f["gap_fit_cal"] >= 20 for f in rec["folds"])
        assert rec["config"]["embargo_td"] == 20

    def test_saved_probabilities_reproduce_the_recorded_masses_and_calibration_diagnostics(self):
        rec = load_run_record(RUN_JSON)
        recomp = recompute_from_oof(OOF)
        assert check_reproducible(rec, recomp) == []
        assert recomp["n_rows"] == 434_470
        for key, v in recomp["masses"].items():
            assert np.isfinite(v), key
        # overlap is preserved, not partitioned (the sum can exceed 1)
        assert recomp["masses"]["mean_sum_up_down_stay"] > 0.9
        # per-event calibration diagnostics are present for all four events
        for key in ("up", "down", "stay", "stay_exclusive"):
            assert recomp["calibration"][key]["n"] == 434_470
            assert 0.0 <= recomp["calibration"][key]["brier"] <= 1.0
        assert recomp["composite_max_abs_error"] < 1e-6

    def test_the_shortlist_matches_the_declared_composite_and_tie_break(self):
        df, check = load_shortlist(SHORTLIST)
        assert check["ordered_by_composite_desc"] is True
        assert check["symbol_tie_break_ok"] is True
        assert check["composite_max_abs_error"] < 1e-6
        assert check["n_rows"] == len(df) == 20
        assert np.allclose(df["composite"], df["p_up"] - df["p_down"], atol=1e-6)

    def test_a_tampered_mass_is_caught_instead_of_being_reported(self):
        rec = load_run_record(RUN_JSON)
        recomp = recompute_from_oof(OOF)
        bad = json.loads(json.dumps(rec))
        bad["calibration_masses"]["mean_p_up"] += 0.05
        problems = check_reproducible(bad, recomp)
        assert problems and "mean_p_up" in problems[0]

# --------------------------------------------------------------------------- #
# the human gate package itself
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not (PROBE.exists() and RUN_JSON.exists() and OOF.exists() and SHORTLIST.exists()),
                    reason="WI-009c run outputs not present")
def test_summary_carries_every_required_element(tmp_path):
    rec = load_run_record(RUN_JSON)
    recomp = recompute_from_oof(OOF)
    verdicts = parse_probe_verdicts(PROBE.read_text())
    n_cleared, n_targets = parse_labels_cleared(PROBE.read_text())
    shortlist, sl_check = load_shortlist(SHORTLIST)
    rob = {"path": "reports/wi009c_robustness.md", "n_not_run": 3, "n_go": 0,
           "options": ["regime", "stacking", "dynamic feature"]}

    text = build_summary(rec, recomp, verdicts, n_cleared, n_targets, shortlist, sl_check, rob, "CAD")

    # Step-5(c) grep targets
    for token in ("P(up)", "P(down)", "P(stay)", "same-sign", "human gate"):
        assert token in text, token
    # exact model / fold / run identity
    assert "wi009c_regression_CAD.json" in text
    assert "PurgedWalkForwardSplit(n_splits=5, embargo_td=20)" in text
    assert "5 of 5 folds viable" in text
    assert "434,470 out-of-fold rows" in text
    # per-target verdict table + the route verdict as a whole
    for target in ("y_15d_high", "y_15d_low", "y_20d_up", "y_20d_down", "y_20d_stay"):
        assert f"`{target}`" in text
    assert "0/5 targets clear the unchanged skill bar" in text
    assert "Route verdict as a whole" in text
    assert "not demonstrated to have skill" in text
    # declared composite + its verification
    assert "`P(up) - P(down)`" in text
    assert "ordering by the declared composite verified (True)" in text
    # negative results are distinguished from failures, and no gate is claimed passed
    assert "Negative results vs execution/test failures" in text
    assert "**Execution/test failures**: none" in text
    assert "human gate decision required" in text
    assert "No sprint gate is marked passed here" in text
    # no live wiring
    assert "not** wired to orders" in text or "not wired to orders" in text

    out = tmp_path / "wi009c_summary.md"
    out.write_text(text)
    assert out.read_text().endswith("\n")


@pytest.mark.skipif(not (RUN_JSON.exists() and OOF.exists() and SHORTLIST.exists()),
                    reason="WI-009c run outputs not present")
def test_summary_stays_honest_when_the_skill_bar_failed():
    rec = load_run_record(RUN_JSON)
    assert rec["skill"]["passed"] is False
    recomp = recompute_from_oof(OOF)
    verdicts = parse_probe_verdicts(PROBE.read_text())
    n_cleared, n_targets = parse_labels_cleared(PROBE.read_text())
    shortlist, sl_check = load_shortlist(SHORTLIST)
    text = build_summary(rec, recomp, verdicts, n_cleared, n_targets, shortlist, sl_check, None, "CAD")
    assert "SKILL BAR: FAIL" in text
    assert "no model was re-fit" in text
    # the route verdict refuses the trading question rather than answering it
    assert "Is the route usable for trading? | **No — human gate decision required**" in text
    # a missing robustness record is reported, never glossed over
    assert "Step-4 robustness record missing" in text


def test_robustness_counts_come_from_the_record_not_from_prose(tmp_path):
    synthetic = tmp_path / "wi009c_robustness.md"
    synthetic.write_text(
        "# Step 4\n\n- Options attempted: **0** · options reported **NOT RUN**: **3** · "
        "options whose gate decision was GO: 0 of 3.\n"
        "| regime | `--robustness-regime` | **NO-GO** | 1 / 2 | **NOT RUN** | `step1` |\n"
        "| stacking | `--robustness-stacking` | **NO-GO** | 0 / 2 | **NOT RUN** | `step1` |\n"
        "| dynamic feature selection | `--robustness-dynamic` | **NO-GO** | 1 / 2 | **NOT RUN** | `step1` |\n"
    )
    got = robustness_summary(synthetic)
    assert got["n_not_run"] == 3 and got["n_go"] == 0
    assert got["options"] == ["regime", "stacking", "dynamic feature"]
    assert robustness_summary(tmp_path / "absent.md") is None
