# D-014 — WI-014 E5 factor screener and PDF

## Context
WI-014 needs a daily shortlist and tearsheet for both markets from the validated E5 baseline. Existing classifier-route shortlists are explicitly unusable, and the legacy predictions-based compiler and PDFs are frozen demo artifacts. The approved ranking is `mom_12_1` descending, with the five E5 factors shown as context; output is research-only under the NO_TRADE/cost caveat.

## Options considered
1. Reuse the classifier-route shortlist or legacy prediction PDFs — rejected because their signal route is not validated and legacy artifacts are frozen.
2. Modify `src/pdf_compiler.py` to consume E5 factors — rejected because it would alter the frozen Sprint-5 record and couple the new output to the predictions path.
3. Add a dedicated E5 shortlist command and factor renderer, reusing or copying only chart-drawing logic — selected.

## Decision
Implement `scripts/wi014_screener.py` and `src/pdf_compiler_factor.py` as a separate path. Route markets through `src/market_cli.py`, rank on the existing factor without a composite, and write only WI-014-prefixed/suffixed artifacts. Reuse chart helpers only when separable from the legacy predictions loader; otherwise copy the needed drawing logic without editing the legacy module.

## Consequences
- Positive: validated factor signal is surfaced for both markets, outputs are reproducible and market-specific, and the historical demo route stays intact.
- Negative: chart logic may be duplicated if extracting it would risk the frozen compiler; percentile/context presentation must remain descriptive and must not imply tradeability.

## Status
proposed
