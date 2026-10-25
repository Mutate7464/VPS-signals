"""WI-009c Step 4 — evidence gates for the optional robustness candidates.

Why this module exists
----------------------
Plan Step 4 exposes three **optional** robustness switches, but only permits an option
to be built or run when it is (i) justified by the recorded Step-1 probe evidence and
(ii) aimed at a documented weakness in the core continuous baseline. Step 4(d) adds the
hard stop: never build all candidates by default, and never expand the feature set after
a failed probe (Step 1 cleared the unchanged skill bar for 0/5 labels).

The decision logic therefore *is* the deliverable for this work item, and it is a pure
function of the saved evidence:

* ``reports/wi009c_probe.md`` → the Step-1 go/no-go (fail-closed, via
  `src.models.continuous_targets.step1_permits_feature_spend`);
* the Step-2/3 run record (`reports/wi009c_regression_{MKT}.json`) → whether a weakness
  in the core continuous baseline is documented;
* the Step-3 fold-safety decision → whether the contrastive stacked input is usable at
  all.

Nothing here fits a model. `evaluate_robustness_gates` decides go/no-go and
`render_robustness_report` writes the decision; an option whose gate is unmet is
reported as ``NOT RUN`` with its **specific** unmet gate — never silently skipped, and
never built "just in case" (plan Step 4(a)/(d)). An option that is accepted still has
to pass the **unchanged** skill bar on identical purged folds; the bar is reused from
`src.models.skill_bar`, not weakened or redefined here.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

from src.models.continuous_targets import EMBARGO_TD, step1_permits_feature_spend

__all__ = [
    "BASELINE_WEAKNESS_GATE",
    "DYNAMIC_FEATURE_SELECTION",
    "FEATURE_POOL_GATE",
    "FOLD_SAFE_STACKING_GATE",
    "REGIME",
    "ROBUSTNESS_OPTIONS",
    "STACKING",
    "STEP1_PERMISSION_GATE",
    "count_labels_cleared",
    "evaluate_robustness_gates",
    "render_robustness_report",
]

# --------------------------------------------------------------------------- #
# Gate names (each unmet gate is named verbatim in the report)
# --------------------------------------------------------------------------- #
STEP1_PERMISSION_GATE = "step1_permits_feature_spend"
BASELINE_WEAKNESS_GATE = "baseline_weakness_documented"
FOLD_SAFE_STACKING_GATE = "contrastive_score_fold_safe"
FEATURE_POOL_GATE = "feature_pool_larger_than_baseline"

# --------------------------------------------------------------------------- #
# The three optional candidates, in plan Step 4(a) order
# --------------------------------------------------------------------------- #
REGIME = "regime"
STACKING = "stacking"
DYNAMIC_FEATURE_SELECTION = "dynamic_feature_selection"

ROBUSTNESS_OPTIONS = (
    {
        "key": REGIME,
        "title": "Trailing market-state / regime features",
        "switch": "--robustness-regime",
        "gates": (STEP1_PERMISSION_GATE, BASELINE_WEAKNESS_GATE),
        "feature_provenance": (
            "would add **trailing** market-state/regime columns computed from raw OHLCV through "
            "`src.factors.e5_baseline.build_e5_panel` (trailing windows only, so no forward-looking "
            "window enters a training row). Nothing is read from "
            "`data/features/features_CAD.parquet`, and no column is built in this work item: that is "
            "feature spend, gated by Step 1(d)."
        ),
    },
    {
        "key": STACKING,
        "title": "Factor + contrastive + continuous-regressor stacking",
        "switch": "--robustness-stacking",
        "gates": (STEP1_PERMISSION_GATE, FOLD_SAFE_STACKING_GATE),
        "feature_provenance": (
            "would append the fold-safe `score_numpy` output of `models/contrastive_ranker_wi009b.pt` "
            "as **one** extra column on the five E5 factors (via "
            "`src.models.continuous_targets.stacked_input_matrix`), never replacing the continuous "
            "model and never becoming the final ranking. The score is an 89-feature model output, so "
            "using it is 89-feature spend — gated by Step 1(d) — and its fold-safety must be "
            "established first (Step 3(a)/(d))."
        ),
    },
    {
        "key": DYNAMIC_FEATURE_SELECTION,
        "title": "Dynamic feature selection (per-fold subset of the 89-feature pool)",
        "switch": "--robustness-dynamic",
        "gates": (STEP1_PERMISSION_GATE, FEATURE_POOL_GATE),
        "feature_provenance": (
            "would select a per-fold subset of the 89 `float32` columns of "
            "`data/features/features_CAD.parquet` (bounded, `pyarrow.dataset` date chunks). Reading "
            "that pool *is* the 89-feature spend gated by Step 1(d); with the baseline deliberately "
            "limited to the same five factors, there is no larger pool in scope to select from."
        ),
    },
)

_COMPARISON_NOTE = (
    "same-sign and |IC| of the option vs the five E5 factors on **identical purged folds** "
    "(same fold plan, same 20td purge, same out-of-fold rows); an option is accepted only if it "
    "then passes the **unchanged** skill bar — clause (a) same sign as the best factor AND |IC| >=, "
    "clause (b) |t| > 2 with a stable sign in >= 2 disjoint sub-windows."
)

_COUNT_RE = re.compile(r"(\d+)\s*/\s*(\d+)\s+targets clear the unchanged skill bar")


def count_labels_cleared(probe_report_text: str) -> int:
    """Labels that cleared the unchanged skill bar, read from the Step-1 probe report.

    Fail-closed: a report without the summary line reads as 0.
    """
    m = _COUNT_RE.search(probe_report_text or "")
    return int(m.group(1)) if m else 0


def _permission_from_probe(probe_report_text: str) -> tuple[bool, int]:
    """Step-1 go/no-go plus the cleared-label count.

    The plan-mandated signal is the explicit permission sentence in the probe report
    (`step1_permits_feature_spend`, fail-closed). If the report *also* states a cleared
    count, that count must be >= 1 — a report with "0/5 targets clear" and a permission
    sentence is contradictory and is treated as **no** permission.
    """
    text = probe_report_text or ""
    permitted = step1_permits_feature_spend(text)
    n_cleared = count_labels_cleared(text)
    m = _COUNT_RE.search(text)
    if m is not None and int(m.group(1)) <= 0:
        permitted = False
    return bool(permitted), n_cleared


def _finite(x) -> bool:
    try:
        f = float(x)
    except (TypeError, ValueError):
        return False
    return f == f and abs(f) != float("inf")


def _fmt(x, fmt: str = "+.4f") -> str:
    return f"{x:{fmt}}" if _finite(x) else "n/a"


def _gate_evidence(name: str, facts: dict, baseline_skill: dict | None, contrastive_decision: dict | None,
                   n_base_features: int, n_pool_features: int) -> str:
    """One plain sentence of evidence for a gate, naming the plan clause behind it."""
    if name == STEP1_PERMISSION_GATE:
        return (
            f"plan Step 1(d)/Step 4(d): {facts['n_labels_cleared']}/5 labels cleared the unchanged skill "
            "bar in `reports/wi009c_probe.md`, so the 89-feature spend and every optional candidate "
            "stay gated and the feature set may not be expanded after a failed probe."
        )
    if name == BASELINE_WEAKNESS_GATE:
        if baseline_skill is None:
            return (
                "no recorded continuous-baseline skill result to document a weakness from "
                "(the run record is missing), so no option can be justified against one."
            )
        ic = baseline_skill.get("model_ic")
        best = baseline_skill.get("best_factor")
        best_abs = baseline_skill.get("best_abs_ic")
        return (
            f"continuous baseline skill bar {'FAIL' if not baseline_skill.get('passed') else 'PASS'}: "
            f"IC {_fmt(ic)} (t {_fmt(baseline_skill.get('model_t'), '+.2f')}) vs `e5_{best}` "
            f"|IC| {_fmt(best_abs)}, same-sign {baseline_skill.get('same_sign')} — a documented "
            "weakness exists to aim an option at (necessary, not sufficient: the Step-1 gate above is "
            "also required)."
        )
    if name == FOLD_SAFE_STACKING_GATE:
        if contrastive_decision is None:
            return (
                "plan Step 3(a)/(d): no fold-safety decision is recorded for the contrastive artifact, "
                "so fold-safe scoring is not established (fail-closed)."
            )
        return (
            f"plan Step 3(a)/(d): fold-safe contrastive score — "
            f"status {contrastive_decision.get('status')}, fold_safe "
            f"{contrastive_decision.get('fold_safe')}. {contrastive_decision.get('reason', '')}"
        ).strip()
    if name == FEATURE_POOL_GATE:
        return (
            f"plan Step 4(d): feature selection needs a candidate pool larger than the {n_base_features} "
            f"baseline factors; the only larger pool is the {n_pool_features}-feature matrix, whose read "
            "is the gated 89-feature spend."
        )
    raise KeyError(f"unknown gate {name!r}")


def evaluate_robustness_gates(
    probe_report_text: str,
    baseline_skill: dict | None = None,
    contrastive_decision: dict | None = None,
    n_base_features: int = 5,
    n_pool_features: int = 89,
    option_bodies_implemented: bool = False,
) -> dict:
    """Go/no-go for each Step-4 robustness option, from the saved evidence only.

    Args:
        probe_report_text: contents of `reports/wi009c_probe.md` (Step-1 evidence).
        baseline_skill: the continuous-baseline skill dict (`passed`, `model_ic`,
            `model_t`, `best_factor`, `best_abs_ic`, `same_sign`) from the Step-2/3 run
            record. ``None`` fails the weakness gate closed.
        contrastive_decision: the Step-3 `contrastive_candidate_decision` dict.
            ``None`` fails the fold-safety gate closed.
        n_base_features: number of factors the baseline is limited to (5).
        n_pool_features: size of the wider feature pool (89).
        option_bodies_implemented: ``False`` for WI-009c — this work item builds **no**
            option body, so even a GO option is reported as ``NOT RUN`` with an explicit
            reason. Exposed so the GO path is testable without pretending a model ran.

    Returns:
        dict with the shared gate facts and one record per option carrying
        `gate_decision` ("GO"/"NO-GO"), `unmet_gates` (named), `status` and `reason`.
    """
    permitted, n_cleared = _permission_from_probe(probe_report_text)
    weakness = bool(baseline_skill is not None and not baseline_skill.get("passed", True))
    fold_safe = bool(
        contrastive_decision is not None
        and contrastive_decision.get("run") is True
        and contrastive_decision.get("fold_safe") is True
    )
    pool_ok = bool(int(n_pool_features) > int(n_base_features))

    facts = {
        "step1_permits_feature_spend": permitted,
        "n_labels_cleared": int(n_cleared),
        BASELINE_WEAKNESS_GATE: weakness,
        FOLD_SAFE_STACKING_GATE: fold_safe,
        FEATURE_POOL_GATE: pool_ok,
    }

    options: list[dict] = []
    for spec in ROBUSTNESS_OPTIONS:
        gates = []
        for name in spec["gates"]:
            gates.append(
                {
                    "name": name,
                    "met": bool(facts[name]),
                    "evidence": _gate_evidence(
                        name, facts, baseline_skill, contrastive_decision, n_base_features, n_pool_features
                    ),
                }
            )
        unmet = [g["name"] for g in gates if not g["met"]]
        go = not unmet
        if not go:
            status = "NOT RUN"
            reason = (
                "gate(s) unmet — "
                + "; ".join(f"{g['name']}: {g['evidence']}" for g in gates if not g["met"])
                + " Optional candidate left unbuilt (plan Step 4(a)/(d)); this is a documented "
                "no-go, not an execution failure."
            )
        elif not option_bodies_implemented:
            status = "NOT RUN"
            reason = (
                "gates MET (GO), but no option body is implemented in WI-009c: plan Step 4(d) forbids "
                "running a gated option without its written go decision, and this work item's scope is "
                "the gate evaluation itself. The Planner/Hermes must author the option before it runs."
            )
        else:
            status = "RUN"
            reason = "gates MET (GO) and the option body is implemented."
        options.append(
            {
                "key": spec["key"],
                "title": spec["title"],
                "switch": spec["switch"],
                "gates": gates,
                "go": bool(go),
                "gate_decision": "GO" if go else "NO-GO",
                "unmet_gates": unmet,
                "status": status,
                "reason": reason,
                "feature_provenance": spec["feature_provenance"],
                "comparison": _COMPARISON_NOTE,
            }
        )

    return {
        "facts": facts,
        "options": options,
        "n_attempted": int(sum(1 for o in options if o["status"] == "RUN")),
        "n_not_run": int(sum(1 for o in options if o["status"] == "NOT RUN")),
        "n_go": int(sum(1 for o in options if o["go"])),
        "option_bodies_implemented": bool(option_bodies_implemented),
        "embargo_td": int(EMBARGO_TD),
        "n_base_features": int(n_base_features),
        "n_pool_features": int(n_pool_features),
        "comparison": _COMPARISON_NOTE,
    }


def render_robustness_report(
    ctx: dict,
    out_path: str | Path,
    market: str = "CAD",
    evidence_source: str = "",
    smoke: bool = False,
    baseline_skill: dict | None = None,
) -> Path:
    """Write `reports/wi009c_robustness.md` — the Step-4 go/no-go record.

    Args:
        ctx: the `evaluate_robustness_gates` output.
        out_path: destination markdown path.
        market: market key.
        evidence_source: human-readable provenance for the gate evidence.
        smoke: whether the invoking run was a `--smoke` run (the gate evidence may
            still come from the production run record — stated explicitly).
        baseline_skill: the baseline skill dict used for the reference line.
    """
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    facts = ctx["facts"]

    lines = [
        f"# WI-009c Step 4 — evidence-gated robustness options ({market})",
        "",
        f"- Generated (UTC): {now}" + ("  · **SMOKE INVOCATION**" if smoke else ""),
        f"- Gate evidence source: {evidence_source or 'this run (in-memory)'}",
        f"- Step-1 evidence: {facts['n_labels_cleared']}/5 labels cleared the unchanged skill bar in "
        "`reports/wi009c_probe.md` → 89-feature/optional-candidate spend "
        f"**{'permitted' if facts['step1_permits_feature_spend'] else 'NOT permitted'}** (fail-closed).",
        f"- Fixed purge/embargo reused unchanged: {ctx['embargo_td']} trading days "
        "(`src.models.skill_bar.EMBARGO_TD`).",
        f"- Baseline limited to the same {ctx['n_base_features']} E5 factors (plan Step 1(d)); the wider "
        f"pool is {ctx['n_pool_features']} features and is not read.",
        "",
        "## go/no-go gate table (Step 1 evidence + documented baseline weakness)",
        "",
        "| Option | Switch | Gate decision | Gates (met / total) | Status | Specific unmet gate |",
        "| :--- | :--- | :--- | ---: | :--- | :--- |",
    ]
    for o in ctx["options"]:
        n_met = sum(1 for g in o["gates"] if g["met"])
        unmet = ", ".join(f"`{u}`" for u in o["unmet_gates"]) if o["unmet_gates"] else "—"
        lines.append(
            f"| {o['title']} | `{o['switch']}` | **{o['gate_decision']}** | {n_met} / {len(o['gates'])} | "
            f"**{o['status']}** | {unmet} |"
        )
    lines += [
        "",
        f"- Options attempted: **{ctx['n_attempted']}** · options reported **NOT RUN**: "
        f"**{ctx['n_not_run']}** · options whose gate decision was GO: {ctx['n_go']} of "
        f"{len(ctx['options'])}.",
        "- No option is accepted unless it then passes the **unchanged** skill bar on identical purged "
        "folds; the bar is reused from `src.models.skill_bar`, never weakened or redefined.",
        "",
    ]

    if baseline_skill is not None:
        lines += [
            "## Baseline reference used for the go/no-go",
            "",
            f"- Continuous 20td baseline (5 E5 factors, `StandardScaler` + `Ridge`): IC "
            f"{_fmt(baseline_skill.get('model_ic'))} (t {_fmt(baseline_skill.get('model_t'), '+.2f')}) vs "
            f"`e5_{baseline_skill.get('best_factor')}` |IC| {_fmt(baseline_skill.get('best_abs_ic'))}; "
            f"same-sign {baseline_skill.get('same_sign')} → "
            f"**{'PASS' if baseline_skill.get('passed') else 'FAIL'}** the unchanged skill bar.",
            "",
        ]

    for o in ctx["options"]:
        lines += [
            f"## {o['title']} — {o['status']}",
            "",
            f"- Switch: `{o['switch']}` · gate decision **{o['gate_decision']}**.",
            f"- Reason: {o['reason']}",
            "- Gates:",
            "",
            "| Gate | Met | Evidence |",
            "| :--- | :--- | :--- |",
        ]
        for g in o["gates"]:
            lines.append(f"| `{g['name']}` | {'yes' if g['met'] else 'NO'} | {g['evidence']} |")
        lines += [
            "",
            f"- Feature provenance: {o['feature_provenance']}",
            f"- What would have been compared: {o['comparison']}",
            "",
        ]

    lines += [
        "## Gate semantics (why nothing was built)",
        "",
        "- Each switch evaluates its gate **first** and refuses to build or run the candidate while the "
        "gate is unmet, so no feature spend occurs. Plan Step 4(d): do not build all candidates by "
        "default, do not expand the feature set after a failed probe, and do not run a gated option "
        "without its written go decision.",
        "- No option body is implemented in WI-009c: the deliverable of this step is the recorded "
        "go/no-go per candidate, not a model. A GO decision would have to be authored by the Planner "
        "before any option runs.",
        "- This is a **documented no-go**, not an execution failure: the gates were evaluated, the "
        "evidence is named per option, and the candidate was left unbuilt on purpose.",
        "- Nothing here replaces the skill bar, the 20td purge/embargo, or the human gate.",
        "",
        "## Reading notes",
        "",
        "- The Step-1 negative result (0/5 labels clear the unchanged skill bar) is the single gate that "
        "blocks all three candidates: every one of them needs the 89-feature spend that Step 1(d) "
        "withholds.",
        "- The stacking candidate is blocked twice — by the Step-1 gate and, independently, because "
        "fold-safe contrastive scoring could not be established (the saved artifact's recorded cutoff "
        "2026-05-28 falls inside the last fold's validation window; a per-fold refit would itself be "
        "89-feature spend).",
        "- For dynamic feature selection there is nothing to select from while the baseline is deliberately "
        f"limited to {ctx['n_base_features']} factors — reading the {ctx['n_pool_features']}-feature pool "
        "is the gated spend.",
        "- Options are compared on identical purged folds whenever they do run, so a later GO cannot "
        "silently change the baseline's fold plan.",
        "",
    ]
    path.write_text("\n".join(lines) + "\n")
    return path
