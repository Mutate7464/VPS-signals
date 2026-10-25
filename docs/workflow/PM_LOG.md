# PM_LOG.md — cursor for the Hermes PM cycle

> One entry per PM cycle, newest first. The newest entry's cursor (`cursor:` line)
> defines which opencode sessions the next cycle ingests. Kam's trigger: tell Hermes
> "run PM cycle". Full procedure: `docs/human/PM-CYCLE.md`.

## 2026-10-25 — Cycle 11 (quiescent close — no new work since cycle-10 gate)
- Ingest: 0 new opencode sessions past cursor `ses_e8ecc8dc`; the six newer
  sessions are the cycle-10 WI-009c planner/Build runs (already ingested,
  gate-closed 2026-10-25 option A). Repo delta since = docs-only
  (WI-011 proposal `e702f2`/amendments `6b907e`/hygiene `b7ec4aa`).
- Verified: WI-011 board row (PROPOSED, planner pass + admin approval pending)
  matches plan draft header + log stub `STATUS: PLAN`; no WI-011 brief exists
  yet. No code/artifact changes since cycle-10's 176-test verification.
- Hygiene flags (admin): `debug_test.py`/`debug_test2.py` untracked junk;
  `reports/wi009c_*`, `scripts/evaluate_wi009c.py`, `src/models/robustness_gates.py`,
  `tests/test_wi009c_evaluation.py` still untracked (WI-008-style "deliberately
  untracked" convention? unconfirmed) — same class as the WI-010 classifier
  consolidation.
- Next: admin decision — WI-011 brief + planner dispatch (or hold).
- cursor: `ses_e8e6bcfbdf…` sessions ingested; next cycle ingests past
  `ses_e8d88ee6aff` (newest, WI-009c Build steps 4-5).

## 2026-10-25 — Cycle 10 gate close (admin: WI-009c CLOSED — option A, negative result)
- **WI-009c gate: DECIDED — A, close as documented negative result** (admin
  "a close out 009c. note findings", same day, no appeal). Board row → DONE
  (kept in ACTIVE table per WI-008/009b convention). No model ships from the
  route; factor-baseline screener stands as the MVP signal. The P(up)−P(down)
  shortlist composite is explicitly NOT usable (noise forecast).
- Findings recorded in BOTH streams:
  - human: `docs/human/briefings/2026-10-25-gate-WI-009c-skill-route.md`
    (decision + durable findings: labels-not-features bottleneck; continuous
    route dies at the same place; triple-confirmation that E5 factors are the
    signal; process findings — same-sign clause caught 3 sign-inverted wins,
    loop-v2 + STOP clauses + evidence gates all fired as designed).
  - agent: board row, this log, handover open item 2 struck.
- Standing consequences: same-sign clause carries into any future skill bar;
  future model work on this universe requires a NEW target/data spec,
  probe-first; WI-010 + ELE follow-ups unchanged.
- Route artifacts frozen at commits `92f4716`, `7187ccf`, `4443539`, `43b7681`.

## 2026-10-25 — Cycle 10 (WI-009c steps 0–1 via loop-v2 headless Build; probe = negative)
- First full loop-v2 run: planner dispatched headless (`opencode run --agent
  planner --auto`, GPT-6-Luna) → plan written contract-clean in ~2.5 min,
  verified by PM before dispatch; Build dispatched headless (`--agent build
  --auto`, DeepSeek V4.1-Flash) for Steps 0–1 ONLY → `STATUS: DONE (steps 0-1)`,
  exit 0. Build respected: no BOARD touch, no commits, honest EXECUTION LOG rows.
- PM verification (reran, not trusted): inputs checker PASS (701,599 rows both
  artifacts, alignment dates+symbols identical, stay base 44.84%, 0 dup keys);
  probe rerun exit 0, report matches.
- **Probe verdict (the step-1 gate): 0/5 targets clear the same-sign skill bar**
  for a 5-E5-factor logistic on purged OOF folds (1,615 dates). Best magnitude
  +0.0304 (t +6.86) but **sign-inverted vs `vol_20`** — same regime-inversion
  pathology as WI-009b; others +0.0001 (t +0.04, pure noise), +0.0123 (t +3.15,
  inverted), −0.0231 (t −5.19, mismatch). Confirms WI-002: **labels are the
  bottleneck, not features** — and the same-sign clause is doing its job.
- Consequence per plan Step 1(d) STOP: **89-feature classifier spend stays
  gated**. The continuous-first combo (Step 2 regressor on continuous 20d move,
  5-factor baseline, bands derived from forecast distribution) proceeds — that
  was the admin's standing direction and the probe outcome supports it.
- Build side-notes adopted: plan schema nit (`y_20d_high/low` vs actual
  `y_15d_high/low`) logged; same-sign clause applied as a wrapper on top of
  `src/models/skill_bar.py` (module untouched).
- Next: admin decision — proceed to Steps 2–3 (continuous core + fold-safe
  stacking, detached run) with Step 4 robustness options still evidence-gated.
- cursor: session-since `ses_e8ecc8dc` unchanged (steps 0–1 ran inside PM's
  loop-v2 dispatch; PM verified artifacts directly — no TUI session to ingest).
- **Steps 2–5 (same cycle, admin "go" ×2, all loop-v2 headless):** Step 2
  5-factor continuous baseline **FAILS both clauses** (|IC| +0.0001 noise vs
  `vol_20` 0.0307 — honest negative, no tuning past it). Step 3 contrastive
  stacking **OMITTED** (fold-safety not establishable; artifact cutoff
  2026-05-28). Step 4: 3/3 robustness options **NO-GO / NOT RUN** (all gated
  behind Step 1's 89-feature spend gate). Step 5 gate package written
  (`reports/wi009c_summary.md`): route verdict = documented negative,
  shortlist composite rests on noise → NOT usable. PM re-verified: 44 tests
  (my run), full suite 176 passed (Build's detached run, EXIT:0), gates table
  and verdicts match Build's claims. Commits `92f4716`, `7187ccf`, `4443539`.
- **WI-009c route verdict for the human gate:** every level came back negative
  — binary labels (probe 0/5), continuous 5-factor forecast (noise), stacked
  contrastive (fold-safety), robustness candidates (gated). WI-002's
  diagnosis triple-confirmed: on this CAD universe/window the learnable signal
  lives in the E5 factors themselves; the 89-feature pool adds nothing at
  these label definitions. Gate: accept WI-009c closure (negative result,
  factor-baseline screener as the MVP signal) vs re-specify targets/data.

## 2026-10-25 — Cycle 9 gate close (admin decisions: WI-009b HOLD+re-spec; WI-009c combo scope)
- **WI-009b gate: DECIDED — HOLD + re-spec** (admin, this session). Closed DONE
  as documented negative result: clause (a) re-specified to same-sign-AND-|IC|,
  which this run fails (−0.1478 vs `vol_20` +0.1274). Model NOT shipped; inverse
  signal parked as candidate feature. Same-sign clause carries into WI-009c.
  Records: board row (agent stream), gate-brief decision section (human stream),
  handover open item 1 struck through — both streams confirmed.
- **WI-009c scope: DECIDED — continuous-first combo** (admin direction):
  regression on the continuous 20d move as starting point; band probabilities
  derived from its forecast distribution; factor-only logistic probe stays as
  cheap step-1 bound; regime-aware features / ensembles / stacking / dynamic
  feature selection in scope as candidates (PM verified NONE were built in
  WI-009/009b — checked executed plan + code constructs). Research doc updated
  with ADMIN DIRECTION section. Next: planner brief → loop-v2 headless planner
  dispatch → plan review → Build.
- WI-009 stale plan confirmed AGAIN: `docs/tech_approach/2026-W44/plans/
  contrastive-learning-plan.md` is the unexecuted draft (STATUS: PLAN, TBD log;
  `src/features/technical_features.py` never existed — Step 2 was dropped in
  favor of the existing 89-feature panel). Do not read it as record.

## 2026-10-25 — Cycle 9 continuation addendum: loop v2 (direct handoff, scoped auto)
- Admin direction: "update agent — direct interface with planning and build in
  opencode; direct handoff and completion". Loop v2 landed in
  `docs/human/PM-CYCLE.md`: Hermes dispatches planner/build headlessly via
  `opencode run --agent <name> --auto` (v2.1.4 verified on host), polls
  artifacts/STATUS lines (never transcripts), PM cycle verifies as before.
- **Scoped auto** (admin pick over full-auto/dispatch-only/keep-TUI): deny
  rules added to `~/.config/opencode/opencode.jsonc` → `agent.build.permission`
  (push/remote/filter-branch, rm/rmdir, sudo, curl/wget/webfetch, ssh/scp/
  rsync, nc/ping). Backup taken (`opencode.jsonc.backup.20261025_053912`).
- Verified LIVE (not from docs): deny blocks `git push --dry-run` under `--auto`
  ("Permission denied: shell"); `git status --short --branch` passes (returned
  `## main...origin/main [ahead 53]`). JSONC loads (opencode debug agents OK).
- Cost accounting (admin question): heavy generation unchanged on opencode
  flash models; Hermes overhead ≈ +30–50k tokens/cycle if artifact-first poll
  discipline holds (10-min sleep steps, `EXIT:0` markers, no transcript ingest).
  Admin relay time per cycle → 0. Gates unchanged: nothing self-approves.
- TUI fallback documented (ingest via opencode.db as before).


---

> **Archive pointer:** cycles 0–8 live in `docs/workflow/archive/PM_LOG-2026-10-cycles-0-8.md`.
> Rotation rule (WORKFLOW.md §7): keep the last 2 cycles here; older entries move to the
> archive at the weekly review. Read only the newest entry + its `cursor:` line (WORKFLOW.md §11).

