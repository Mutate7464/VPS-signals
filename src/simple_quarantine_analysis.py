"""DEPRECATED by WI-010 (quarantine classifier consolidation).

This module used to hold the second, divergent quarantine-classifier logic
(`level_step_simple` / `volume_simple` / `analyze_ticker_simple`), which the
WI-008 report generator imported. WI-010 consolidates onto ONE tested classifier:
`src/quarantine_analysis.py`.

Attribute access is deliberately blocked (PEP 562) so no caller can silently keep
using the removed classifier. Pending removal: file deletions are human-gated in
this build configuration, so the admin should delete it with:

    rm -f src/simple_quarantine_analysis.py
"""

MESSAGE = (
    "src.simple_quarantine_analysis is DEPRECATED by WI-010; "
    "use src.quarantine_analysis instead (pending admin removal)."
)


def __getattr__(name: str):
    if name.startswith("__"):  # keep import/introspection machinery working
        raise AttributeError(name)
    raise ImportError(f"{MESSAGE} Requested attribute: {name!r}")
