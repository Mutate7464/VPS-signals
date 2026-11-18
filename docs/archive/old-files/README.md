# old-files/ — staging for deletion (created 2026-11-18 housekeeping)

Everything here is SUPERSEDED and safe to delete in a future cleanup pass. Kept out of
the live tree only so links in archived PM_LOGs / retros / human briefings remain
name-findable. Do not read these during a cold start; do not link to them from new docs.

Moved from:
- `plans/` ← `docs/plans/` Oct-dated WI plans + 26-W44/26-W45 + superseded 26-W46 v1 (all WIs closed, cards in `docs/archive/wi/`)
- `briefs/` ← `docs/workflow/briefs/` 2026-10-22…2026-11-01 briefs (WIs closed; verdicts in BOARD history + PM_LOG archive)
- `plans-logs/` ← `docs/plans/logs/` execution logs WI-010…019 (WIs closed)
- `human-briefings/` ← `docs/human/briefings/` gate briefings 2026-10-25…11-01 (superseded by WI cards/reports)
- `archive-design/`, `archive-plan.md` ← `docs/archive/Design/`, `docs/archive/plan.md` (original pre-lean workflow docs, 2026-10-22 era)

NOT here: `docs/archive/wi/` (still linked from BOARD rows), everything under
`docs/workflow/`, current plans/briefs.

Deletion is admin-approved only. When deleting: also run
`grep -r "old-files" docs/ --include='*.md'` to retire remaining inbound links.
