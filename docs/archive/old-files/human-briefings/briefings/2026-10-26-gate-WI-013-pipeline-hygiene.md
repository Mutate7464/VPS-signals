# GATE DECISION — WI-013 pipeline hygiene (2026-10-26)

**Decision: APPROVED.** Admin accepted the PM's SIMPLE-tier recommendation in-chat
("simple rec approved") — both open deviations accepted as-is:

1. **USD Step-0 checker baseline undeclared** — the checker reports-observes the USD
   baseline instead of asserting it (CAD assertions unchanged). Accepted as scoped;
   follow-up candidates live in the WI-012 iteration notes, not this item.
2. **`src/factors/e5_baseline.py` CLI default left CAD** — the plan scoped the
   `--market` fix to the F-2 scripts only. Accepted per plan scope; the module-level
   default is untouched until a future item orders otherwise.

**What ships:** `src/market_cli.py` (default BOTH = USD→CAD), market-parametrized
`wi011_*` scripts + `src/wi011` (MARKET constant dropped), F-2 suffixed report paths,
F-4 metadata label strip with old==new exact-equal rebuild (USD 71→67, CAD 91→87 cols),
CAD backfill under `_CAD` suffixes, default preflight for both markets.

**What carries forward:** WI-014 (factor-screener tearsheet PDF, both markets) proceeds
from this version; next week's analytics pivot follows it. WI-013 is DONE; no
unresolved blockers. Untracked `data/` remains an admin hygiene item.

**Evidence:** `docs/plans/logs/WI-013-pipeline-hygiene.md` STATUS: DONE (PM-set);
full suite 360 passed (Build log `EXIT:0`); targeted `tests/test_wi013_*.py` 126 PM-verified;
commits `d26da29`, `5642819`.