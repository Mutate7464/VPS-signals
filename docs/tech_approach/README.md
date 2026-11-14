# Technical Approach Documentation

This directory contains documentation for the technical trading approach implementation following the E3-E5 diagnostic findings.

## Structure

```
tech_approach/
├── YYYY-WW/                # Week-based organization (e.g., 2026-W44 = Oct 24-30, 2026)
│   ├── briefs/             # Planning briefs for work items
│   ├── plans/              # Detailed implementation plans
│   └── reports/            # Progress and summary reports
├── template-brief.md       # Template for new briefs
├── template-plan.md        # Template for new plans
└── README.md               # This file
```

## Naming Convention

- Use `YYYY-WW` format for weeks (e.g., 2026-W44 for October 24-30, 2026)
- Files named descriptively with kebab-case
- Plans follow format: `topic-name-plan.md`
- Briefs follow format: `topic-name-brief.md`
- Reports follow format: `WW-description.md` or `topic-name-report.md`

## Workflow

1. Create brief for each work item in `briefs/` folder
2. Create detailed plan in `plans/` folder
3. Execute plan and document progress in `reports/`
4. Update BOARD.md with progress
5. Archive completed work at end of week

## Token Economy Benefits

- Year/week structure reduces cognitive load
- Single location for all technical approach docs
- Templates ensure consistency
- Clear separation from historical diagnostic work