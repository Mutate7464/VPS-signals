#!/usr/bin/env python3
"""DEPRECATED by WI-010 (quarantine classifier consolidation).

This script was one of three divergent quarantine-classifier claim paths (it
produced the 17/55 WI-008 report via `src/simple_quarantine_analysis.py`).

WI-010 consolidates onto ONE tested classifier (`src/quarantine_analysis.py`) and
ONE report entry point (`src/quarantine_triage_report.py`). This file no longer
classifies anything and deliberately exits non-zero if invoked, so nothing can
silently regenerate a stale report.

Pending removal: file deletions are human-gated in this build configuration (the
agent's build permission policy denies `rm`), so the admin should delete it with:

    rm -f src/final_quarantine_triage.py
"""

import sys

MESSAGE = (
    "[final_quarantine_triage] DEPRECATED by WI-010 — no classifier logic here. "
    "Use: uv run python -m src.quarantine_triage_report "
    "(classifier: src/quarantine_analysis.py). Pending admin removal."
)


def main() -> int:
    print(MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
