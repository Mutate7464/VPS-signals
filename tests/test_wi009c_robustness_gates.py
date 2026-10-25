"""WI-009c Step 4 — evidence gates for the optional robustness candidates.

Locks the acceptance criteria of
`docs/plans/2026-10-25-WI-009c-classifier-route.md` Step 4(b)/(c):

* each candidate records its Step-1 go/no-go rationale, feature provenance and the
  same-sign/|IC| comparison it would face;
* no option is accepted unless it passes the unchanged skill bar;
* unattempted options are explicitly marked `NOT RUN` **with the specific unmet gate**
  — never silently skipped and never built "just in case" (Step 4(d)).

The tests are pure: they read `reports/wi009c_probe.md` as evidence text and synthetic
skill/decision dicts, so no CAD artifact is touched and the host budget is unaffected.
"""
from pathlib import Path

import pytest

from src.models.continuous_targets import EMBARGO_TD
from src.models.robustness_gates import (
    BASELINE_WEAKNESS_GATE,
    DYNAMIC_FEATURE_SELECTION,
    FEATURE_POOL_GATE,
    FOLD_SAFE_STACKING_GATE,
    REGIME,
    ROBUSTNESS_OPTIONS,
    STACKING,
    STEP1_PERMISSION_GATE,
    count_labels_cleared,
    evaluate_robustness_gates,
    render_robustness_report,
)

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "reports" / "wi009c_probe.md"

# The recorded Step-1 result: 0/5 labels cleared the bar → no feature spend.
BLOCKED_TEXT = (
    "## Verdict summary\n\n"
    "| Target | OOF logit IC |\n| :--- | ---: |\n| `y_20d_up` | +0.0123 |\n\n"
    "- 0/5 targets clear the unchanged skill bar\n"
    "- **Step 2 gate:** no label demonstrated learnable — no 89-feature spend; limit the "
    "continuous baseline to the same five factors.\n"
)
# A hypothetical permitted probe (1/5 cleared) — the permission sentence plus the count.
PERMITTED_TEXT = (
    "## Verdict summary\n\n"
    "- 1/5 targets clear the unchanged skill bar (`y_20d_up`)\n"
    "- **Step 2 gate:** permission for one 89-feature continuous run (permission, not a claim of skill).\n"
)
CONTRADICTORY_TEXT = (
    "- 0/5 targets clear the unchanged skill bar\n"
    "- **Step 2 gate:** permission for one 89-feature continuous run (permission, not a claim of skill).\n"
)

FAILED_BASELINE = {
    "model_ic": 0.00011381508108395793,
    "model_t": 0.027590428639330696,
    "best_factor": "vol_20",
    "best_abs_ic": 0.030664031724385126,
    "same_sign": False,
    "passed": False,
}
PASSED_BASELINE = dict(FAILED_BASELINE, model_ic=0.5, passed=True, same_sign=True)
NOT_RUN_DECISION = {
    "run": False,
    "fold_safe": None,
    "status": "NOT RUN",
    "reason": "Step 1 gate (plan Step 1(d)): ... candidate omitted.",
}
FOLD_SAFE_DECISION = {
    "run": True,
    "fold_safe": True,
    "status": "RUN",
    "reason": "cutoff precedes every held-out date.",
}


def _opt(ctx, key):
    return next(o for o in ctx["options"] if o["key"] == key)


# --------------------------------------------------------------------------- #
# the three candidates exist, one switch each, in plan order
# --------------------------------------------------------------------------- #
def test_three_candidates_are_declared_with_their_own_switches():
    keys = [o["key"] for o in ROBUSTNESS_OPTIONS]
    assert keys == [REGIME, STACKING, DYNAMIC_FEATURE_SELECTION]
    switches = [o["switch"] for o in ROBUSTNESS_OPTIONS]
    assert len(set(switches)) == 3
    assert switches == ["--robustness-regime", "--robustness-stacking", "--robustness-dynamic"]


# --------------------------------------------------------------------------- #
# fail-closed Step-1 evidence
# --------------------------------------------------------------------------- #
def test_labels_cleared_is_parsed_and_fails_closed_without_the_line():
    assert count_labels_cleared(BLOCKED_TEXT) == 0
    assert count_labels_cleared(PERMITTED_TEXT) == 1
    assert count_labels_cleared("") == 0
    assert count_labels_cleared("some unrelated report body") == 0


def test_permission_sentence_plus_a_zero_count_is_treated_as_no_permission():
    ctx = evaluate_robustness_gates(CONTRADICTORY_TEXT, FAILED_BASELINE, NOT_RUN_DECISION)
    assert ctx["facts"][STEP1_PERMISSION_GATE] is False
    assert all(o["gate_decision"] == "NO-GO" for o in ctx["options"])


def test_the_real_probe_report_blocks_every_candidate():
    if not PROBE.exists():
        pytest.skip("probe report not present")
    ctx = evaluate_robustness_gates(PROBE.read_text(), FAILED_BASELINE, NOT_RUN_DECISION)
    assert ctx["facts"]["n_labels_cleared"] == 0
    assert ctx["facts"][STEP1_PERMISSION_GATE] is False
    assert ctx["n_attempted"] == 0
    assert ctx["n_not_run"] == 3
    for o in ctx["options"]:
        assert o["status"] == "NOT RUN"
        assert STEP1_PERMISSION_GATE in o["unmet_gates"]


# --------------------------------------------------------------------------- #
# per-candidate go/no-go rationale names the SPECIFIC unmet gate
# --------------------------------------------------------------------------- #
def test_regime_is_blocked_by_the_step1_gate_only_and_its_weakness_gate_is_met():
    ctx = evaluate_robustness_gates(BLOCKED_TEXT, FAILED_BASELINE, NOT_RUN_DECISION)
    o = _opt(ctx, REGIME)
    assert o["gate_decision"] == "NO-GO"
    assert o["unmet_gates"] == [STEP1_PERMISSION_GATE]
    # the documented weakness (baseline FAIL) IS present — necessary, not sufficient
    assert ctx["facts"][BASELINE_WEAKNESS_GATE] is True
    assert "0/5" in o["reason"] and "Step 1" in o["reason"]
    assert "not an execution failure" in o["reason"]


def test_stacking_is_blocked_twice_step1_and_fold_safety():
    ctx = evaluate_robustness_gates(BLOCKED_TEXT, FAILED_BASELINE, NOT_RUN_DECISION)
    o = _opt(ctx, STACKING)
    assert o["unmet_gates"] == [STEP1_PERMISSION_GATE, FOLD_SAFE_STACKING_GATE]
    assert "fold" in o["reason"]


def test_a_permitted_step1_still_requires_a_fold_safe_contrastive_score():
    ctx = evaluate_robustness_gates(PERMITTED_TEXT, FAILED_BASELINE, NOT_RUN_DECISION)
    o = _opt(ctx, STACKING)
    assert ctx["facts"][STEP1_PERMISSION_GATE] is True
    assert o["gate_decision"] == "NO-GO"
    assert o["unmet_gates"] == [FOLD_SAFE_STACKING_GATE]
    # …while the regime candidate clears both of its gates under the same evidence
    assert _opt(ctx, REGIME)["gate_decision"] == "GO"


def test_dynamic_feature_selection_needs_a_pool_larger_than_the_baseline():
    ctx = evaluate_robustness_gates(BLOCKED_TEXT, FAILED_BASELINE, NOT_RUN_DECISION)
    o = _opt(ctx, DYNAMIC_FEATURE_SELECTION)
    assert o["unmet_gates"] == [STEP1_PERMISSION_GATE]
    assert ctx["facts"][FEATURE_POOL_GATE] is True  # 89 > 5 — but reading the pool is the gated spend
    assert "89" in o["reason"] or "gated 89-feature spend" in o["reason"] or "Step 1" in o["reason"]

    tight = evaluate_robustness_gates(
        BLOCKED_TEXT, FAILED_BASELINE, NOT_RUN_DECISION, n_base_features=5, n_pool_features=5
    )
    assert tight["facts"][FEATURE_POOL_GATE] is False
    assert FEATURE_POOL_GATE in _opt(tight, DYNAMIC_FEATURE_SELECTION)["unmet_gates"]


def test_no_option_is_justified_without_a_documented_baseline_weakness():
    """Necessary condition: an option needs something to aim at."""
    ctx = evaluate_robustness_gates(PERMITTED_TEXT, PASSED_BASELINE, FOLD_SAFE_DECISION)
    assert ctx["facts"][BASELINE_WEAKNESS_GATE] is False
    assert _opt(ctx, REGIME)["unmet_gates"] == [BASELINE_WEAKNESS_GATE]
    # the evidence sentence quotes the (passing) skill result rather than claiming a weakness
    ev = next(g for g in _opt(ctx, REGIME)["gates"] if g["name"] == BASELINE_WEAKNESS_GATE)
    assert "PASS" in ev["evidence"]


def test_a_missing_run_record_fails_the_weakness_gate_closed():
    ctx = evaluate_robustness_gates(PERMITTED_TEXT, None, None)
    assert ctx["facts"][BASELINE_WEAKNESS_GATE] is False
    assert ctx["facts"][FOLD_SAFE_STACKING_GATE] is False
    assert _opt(ctx, REGIME)["gate_decision"] == "NO-GO"
    assert _opt(ctx, STACKING)["gate_decision"] == "NO-GO"
    assert ctx["n_attempted"] == 0
    assert all(o["status"] == "NOT RUN" for o in ctx["options"])


# --------------------------------------------------------------------------- #
# every gate must be met before an option may run
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("key", [REGIME, STACKING, DYNAMIC_FEATURE_SELECTION])
def test_go_requires_every_gate_and_not_run_names_the_unmet_ones(key):
    for probe, skill, decision in (
        (BLOCKED_TEXT, FAILED_BASELINE, NOT_RUN_DECISION),
        (BLOCKED_TEXT, PASSED_BASELINE, FOLD_SAFE_DECISION),
        (PERMITTED_TEXT, FAILED_BASELINE, NOT_RUN_DECISION),
        (PERMITTED_TEXT, PASSED_BASELINE, FOLD_SAFE_DECISION),
    ):
        o = _opt(evaluate_robustness_gates(probe, skill, decision), key)
        assert o["go"] is (not o["unmet_gates"])
        assert o["gate_decision"] == ("GO" if o["go"] else "NO-GO")
        if not o["go"]:
            assert o["status"] == "NOT RUN" and o["unmet_gates"]
            for name in o["unmet_gates"]:
                assert name in o["reason"]


def test_no_option_body_is_built_in_this_work_item_even_on_a_go():
    ctx = evaluate_robustness_gates(PERMITTED_TEXT, FAILED_BASELINE, FOLD_SAFE_DECISION)
    assert ctx["n_go"] >= 1
    assert ctx["n_attempted"] == 0  # GO, but nothing is built: Step 4(d)
    for o in ctx["options"]:
        assert o["status"] == "NOT RUN"
        if o["go"]:
            assert "no option body is implemented in WI-009c" in o["reason"]

    # the GO path is reachable and testable without pretending a model ran
    live = evaluate_robustness_gates(
        PERMITTED_TEXT, FAILED_BASELINE, FOLD_SAFE_DECISION, option_bodies_implemented=True
    )
    assert live["n_attempted"] == live["n_go"] >= 1


# --------------------------------------------------------------------------- #
# declared comparison basis + feature provenance
# --------------------------------------------------------------------------- #
def test_every_candidate_declares_provenance_and_the_unchanged_skill_bar_comparison():
    ctx = evaluate_robustness_gates(BLOCKED_TEXT, FAILED_BASELINE, NOT_RUN_DECISION)
    for o in ctx["options"]:
        assert o["feature_provenance"]
        assert "identical purged folds" in o["comparison"]
        assert "unchanged" in o["comparison"]
    assert "contrastive" in _opt(ctx, STACKING)["feature_provenance"]
    assert "89" in _opt(ctx, DYNAMIC_FEATURE_SELECTION)["feature_provenance"]
    assert EMBARGO_TD == 20 and ctx["embargo_td"] == 20


# --------------------------------------------------------------------------- #
# the rendered Step-4 report is greppable and honest
# --------------------------------------------------------------------------- #
def test_report_renders_every_required_token(tmp_path):
    ctx = evaluate_robustness_gates(BLOCKED_TEXT, FAILED_BASELINE, NOT_RUN_DECISION)
    out = render_robustness_report(
        ctx, tmp_path / "wi009c_robustness.md", market="CAD",
        evidence_source="synthetic evidence (test)", baseline_skill=FAILED_BASELINE,
    )
    text = out.read_text()
    for token in ("regime", "stacking", "dynamic feature", "NOT RUN", "go/no-go"):
        assert token in text, token
    # the Step-1 gate is named per candidate, and the negative/exec-failure distinction is explicit
    assert text.count("`step1_permits_feature_spend`") >= 3
    assert "documented no-go" in text
    assert "not an execution failure" in text
    # no candidate is claimed accepted
    assert "Options attempted: **0**" in text
    # the bar is reused, never weakened
    assert "unchanged" in text and "src.models.skill_bar" in text
    # feature provenance is carried into the rendered artifact
    assert "Feature provenance:" in text


def test_report_never_claims_an_accepted_option(tmp_path):
    ctx = evaluate_robustness_gates(BLOCKED_TEXT, FAILED_BASELINE, NOT_RUN_DECISION)
    text = render_robustness_report(
        ctx, tmp_path / "r.md", market="CAD", evidence_source="synthetic", baseline_skill=FAILED_BASELINE
    ).read_text()
    # all three options are NOT RUN, no gate is GO, and no option is claimed to pass the bar
    assert text.count("**NOT RUN**") >= 3
    assert "**GO**" not in text
    assert "PASS the unchanged skill bar" not in text
