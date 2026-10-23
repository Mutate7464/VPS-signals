# D-002 / E4 — Metric/target alignment diagnostics (USD)

- Generated (UTC): 2026-10-23T19:51:24Z
- Source: `data/oof_USD.parquet` from the E2 run (read-only); predictions `p_<target>`, labels `y_<target>`
- Ticker prior = past-only expanding mean of the label per symbol (no look-ahead)

| Target | Pooled AUC | Within-date AUC | Ticker-prior AUC | Prior − Model | Cont. IC (mean) | IC t | D10−D1 spread (ATR) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `y_15d_high` | 0.539 | 0.539 | 0.547 | +0.008 | +0.0117 | +4.31 | +0.3120 |
| `y_15d_low` | 0.537 | 0.535 | 0.551 | +0.016 | +0.0093 | +3.27 | +0.0952 |
| `y_20d_up` | 0.506 | 0.510 | 0.562 | +0.052 | +0.0015 | +0.60 | +0.0089 |
| `y_20d_down` | 0.483 | 0.524 | 0.591 | +0.066 | -0.0012 | -0.46 | -0.0626 |

Effective K: min=30, median=30, max=30; dates with K<5: 0/2696

## Verdict

Verdict: **CONTINUOUS SIGNAL PRESENT, BINARY GATES BLIND — H3 SUPPORTED** (|deflated-IC t| > 2 on y_15d_high, y_15d_low while all binary gates fail): ranking information exists in the continuous forward ATR return but the absolute ATR-breakout labels/within-date K-gates cannot express it. Per the matrix: target/metric redesign (H3).

| ADR row | Applies? | Basis |
| :--- | :--- | :--- |
| E4 → H3 (target/metric redesign) | **YES** | identity targets: 2/4; |IC t|>2: y_15d_high, y_15d_low |
| E3 → H2 / E5 → H4 | adjudicated next | see their reports |
