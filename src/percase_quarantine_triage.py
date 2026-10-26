#!/usr/bin/env python3
"""DEPRECATED by WI-010 (quarantine classifier consolidation).

This script applied a second, divergent quarantine-classifier path (the 11/61
claim path). WI-010 consolidates onto ONE tested classifier
(`src/quarantine_analysis.py`) and ONE report entry point
(`src/quarantine_triage_report.py`). This file no longer classifies anything and
deliberately exits non-zero if invoked.

Pending removal: file deletions are human-gated in this build configuration, so the
admin should delete it with:

    rm -f src/percase_quarantine_triage.py
"""

import sys

MESSAGE = (
    "[percase_quarantine_triage] DEPRECATED by WI-010 — no classifier logic here. "
    "Use: uv run python -m src.quarantine_triage_report "
    "(classifier: src/quarantine_analysis.py). Pending admin removal."
)


def main() -> int:
    print(MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
