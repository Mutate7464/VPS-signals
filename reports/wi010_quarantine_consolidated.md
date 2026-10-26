# WI-010 — Consolidated Quarantine Triage Report

- Generated (UTC): 2026-10-26 05:00:19Z
- Dead-letter source: `data/dead_letter_tickers.csv` (read-only, never rewritten)
- Baseline: `reports/wi008_quarantine_percase_evidence.md` (WI-008, preserved for comparison)
- Classifier: `src/quarantine_analysis.py` (unit-tested; the only remaining classifier)
- Report entry point: `src/quarantine_triage_report.py`
- Duplicate claim paths: reduced to non-classifying deprecation stubs (`final_quarantine_triage.py`, `percase_quarantine_triage.py`, `simple_quarantine_analysis.py`); their file removal is human-gated.
- CB-01 CLEAN_NOW check: `src.verify_synced_data.cb01_clean_now_check` (read-only)
- **No quarantine state is changed by this report.** Per-row reinstate/keep decisions
  remain human-gated (no auto-reinstatement).

Mode: **full consolidated report**.

## 1. WI-008 baseline (17/55 comparison point)

- Baseline file: `reports/wi008_quarantine_percase_evidence.md`
- Parsed per-case rows: **72**

| Recommendation | Count |
| :--- | ---: |
| REINSTATE | 17 |
| KEEP_QUARANTINED | 55 |
| FIX_DATA | 0 |
| OWNER_ACTION | 0 |
| AMBIGUOUS | 0 |

Baseline verified as **17 REINSTATE / 55 KEEP_QUARANTINED** — PASS.

## 2. Anchor experiment — level-step test with persistence guard only (no volume vote)

Each anchor is evaluated separately. The experiment applies `level_step_test` (including its persistence guard) to the first CB-01 spike found on disk and deliberately excludes volume corroboration, so no volume signal can vote. This section is produced before the final rule and is unchanged by it.

| Anchor | Symbol | Market | Data | Spike date | Spike return | Level ratio | Clean fraction | Persistence spread | Persistence | Experiment status |
| :--- | :--- | :---: | :---: | :---: | ---: | ---: | ---: | ---: | :---: | :--- |
| 2020-03-09 crash cluster | OVV | CAD | available | 2020-03-09 | -0.724 | 0.1995 | N/A | 0.3552 | RANGING | GENUINE_VOL |
| 2020-03-09 crash cluster | OVV | USD | available | 2020-03-09 | -0.720 | 0.1869 | N/A | 0.3633 | RANGING | GENUINE_VOL |
| 2020-03-09 crash cluster | WES | USD | available | 2020-03-09 | -0.548 | 0.2490 | N/A | 0.5740 | RANGING | GENUINE_VOL |
| 2020-03-09 crash cluster | CVE | CAD | available | 2020-03-09 | -0.516 | 0.2313 | N/A | 0.5687 | RANGING | GENUINE_VOL |
| 2020-03-09 crash cluster | CVE | USD | available | 2020-03-09 | -0.525 | 0.2180 | N/A | 0.5684 | RANGING | GENUINE_VOL |
| 2020-03-09 crash cluster | APA | USD | available | 2020-03-09 | -0.539 | 0.1771 | N/A | 0.3860 | RANGING | GENUINE_VOL |
| 2020-03-09 crash cluster | OXY | USD | available | 2020-03-09 | -0.520 | 0.2915 | 0.25 | 0.3272 | PERSISTENT | SPLIT_LOOKALIKE |
| 2020-03-09 crash cluster | MTDR | USD | available | 2020-03-09 | -0.641 | 0.1824 | N/A | 0.7046 | RANGING | GENUINE_VOL |
| GME (2021-01 squeeze) | GME | USD | available | 2021-01-27 | 1.348 | 2.5639 | N/A | 1.3322 | RANGING | GENUINE_VOL |
| ICL (negative-price candidate) | ICL | USD | available (non-positive close) | 2014-12-01 | -1.207 | -0.2195 | N/A | -0.0991 | N/A (non-positive close) | GENUINE_VOL |

`PERSISTENT` = post-spike dispersion ≤ 0.35 (level held); `RANGING` = level kept moving; `MISSING`/`UNREADABLE` = data not available on disk.

## 3. Final decision rule (re-derived after the experiment above)

`SPLIT_LOOKALIKE` requires **both** structural signals together (`quarantine_analysis.combine_verdicts`):

1. a persistent, non-unity level step (`level_step_test`, persistence guard included), and
2. an isolated multi-day path (`multi_day_path_analysis`).

Volume corroboration (`volume_corroboration`) is **evidence only** — it can no longer vote, because a volume-only anomaly independently labelled the genuine 2020-03-09 crash cluster (and others) as split-lookalikes under the previous OR-of-signals rule.

Report-level verdicts (`quarantine_analysis.quarantine_verdict`): `SPLIT_LOOKALIKE → KEEP_QUARANTINED`, `GENUINE_VOL → REINSTATE`, non-positive closes `→ FIX_DATA`, missing parquet `→ OWNER_ACTION`, unreadable/exception `→ AMBIGUOUS`, no on-disk CB-01 spike `→ REINSTATE`.

### 3.1 Anchor cases under the final rule

| Anchor | Symbol | Market | Data | Level verdict | Clean fraction | Persistence spread | Path isolated | Classifier verdict | Report verdict | Residual? |
| :--- | :--- | :---: | :---: | :--- | ---: | ---: | :---: | :--- | :--- | :---: |
| 2020-03-09 crash cluster | OVV | CAD | SUCCESS | GENUINE_VOL | N/A | 0.3552 | True | GENUINE_VOL | REINSTATE | NO |
| 2020-03-09 crash cluster | OVV | USD | SUCCESS | GENUINE_VOL | N/A | 0.3633 | True | GENUINE_VOL | REINSTATE | NO |
| 2020-03-09 crash cluster | WES | USD | SUCCESS | GENUINE_VOL | N/A | 0.5740 | True | GENUINE_VOL | REINSTATE | NO |
| 2020-03-09 crash cluster | CVE | CAD | SUCCESS | GENUINE_VOL | N/A | 0.5687 | True | GENUINE_VOL | REINSTATE | NO |
| 2020-03-09 crash cluster | CVE | USD | SUCCESS | GENUINE_VOL | N/A | 0.5684 | True | GENUINE_VOL | REINSTATE | NO |
| 2020-03-09 crash cluster | APA | USD | SUCCESS | GENUINE_VOL | N/A | 0.3860 | False | GENUINE_VOL | REINSTATE | NO |
| 2020-03-09 crash cluster | OXY | USD | SUCCESS | SPLIT_LOOKALIKE | 0.25 | 0.3272 | True | SPLIT_LOOKALIKE | KEEP_QUARANTINED | **YES** |
| 2020-03-09 crash cluster | MTDR | USD | SUCCESS | GENUINE_VOL | N/A | 0.7046 | False | GENUINE_VOL | REINSTATE | NO |
| GME (2021-01 squeeze) | GME | USD | SUCCESS | GENUINE_VOL | N/A | 1.3322 | True | GENUINE_VOL | REINSTATE | NO |
| ICL (negative-price candidate) | ICL | USD | SUCCESS | GENUINE_VOL | N/A | -0.0991 | True | GENUINE_VOL | FIX_DATA | data issue |

**Residual findings (flagged for the gate, no rule widening applied):**

- `OXY/USD` is still read as split-lookalike under the final rule: level ratio 0.25 fraction matched with persistence spread 0.3272 (guard 0.35) and an isolated path. Tightening the step-ratio tolerance (absolute ±0.10 today) or the persistence guard is a rule change beyond this consolidation and is left to the planner/gate.

- `ICL/USD` assessed from its recorded evidence: the parquet contains non-positive closes, so every ratio-based test is meaningless (level ratio N/A); verdict **FIX_DATA** — data repair first, no reinstate/keep recommendation is offered.

## 4. Read-only CB-01 CLEAN_NOW re-check

`cb01_clean_now_check` re-tests each dead-letter row against the CB-01 thresholds (> +100% or < −50% single-day return) using the on-disk parquet only. It never calls `quarantine_ticker()` and never writes `data/dead_letter_tickers.csv`.

| CB-01 status | Rows |
| :--- | ---: |
| CLEAN_NOW | 2 |
| SPIKE | 70 |
| NO_FILE | 0 |
| READ_ERROR | 0 |

| Symbol | Market | Quarantine reason | CB-01 status |
| :--- | :---: | :--- | :--- |
| TRI | CAD | INSUFFICIENT_LOOKBACK_FOR_HURST100 | CLEAN_NOW |
| SPCX | USD | INSUFFICIENT_LOOKBACK_FOR_HURST100 | CLEAN_NOW |

Note: `TRI/CAD` and `SPCX/USD` were quarantined under CB-02 (INSUFFICIENT_LOOKBACK_FOR_HURST100), not CB-01; a CB-01 CLEAN_NOW result cannot clear a CB-02 quarantine — their REINSTATE verdicts follow the classifier (no CB-01 spike on disk) and are listed here for separate gate review.

## 5. Per-symbol verdict and evidence (all 72 dead-letter rows)

`Final` = `quarantine_verdict(classifier result)`. Volume ratio is shown as evidence only; it is not an input to the final rule.

| Symbol | Market | Original reason | Baseline | Final | Flip | CB-01 | Spike date | Spike return | Level ratio | Persist spread | Level | Isolated | Volume ratio (evidence only) | Data issue |
| :--- | :---: | :--- | :--- | :--- | :---: | :---: | :---: | ---: | ---: | ---: | :--- | :---: | ---: | :--- |
| APM | CAD | UNVERIFIED_CORP_ACTION | REINSTATE | REINSTATE |  | SPIKE | 2021-03-29 | 4.556 | 3.6250 | 0.1303 | GENUINE_VOL | True | N/A |  |
| BHC | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2016-03-15 | -0.507 | 0.4300 | 0.3113 | SPLIT_LOOKALIKE | True | 3.138 |  |
| CDE | CAD | UNVERIFIED_CORP_ACTION | REINSTATE | REINSTATE |  | SPIKE | 2026-03-16 | 2.726 | 2.1847 | 0.2665 | GENUINE_VOL | True | 4.692 |  |
| CGX | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2020-03-16 | -0.543 | 0.3630 | 0.2480 | SPLIT_LOOKALIKE | True | 0.523 |  |
| CRON | CAD | UNVERIFIED_CORP_ACTION | REINSTATE | REINSTATE |  | SPIKE | 2014-07-18 | 9.496 | 11.9964 | 0.5832 | GENUINE_VOL | True | N/A |  |
| CVE | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2020-03-09 | -0.516 | 0.2313 | 0.5687 | GENUINE_VOL | True | 2.040 |  |
| CVVY | CAD | UNVERIFIED_CORP_ACTION | REINSTATE | REINSTATE |  | SPIKE | 2017-07-19 | -0.931 | 0.8667 | 0.0771 | GENUINE_VOL | False | N/A |  |
| DSV | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2008-12-30 | -0.667 | 2.0000 | 0.6667 | GENUINE_VOL | False | 0.090 |  |
| ECOR | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2016-10-03 | 1.775 | 2.0938 | 0.0867 | SPLIT_LOOKALIKE | True | N/A |  |
| GSY | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2026-03-10 | -0.570 | 0.3283 | 0.2020 | SPLIT_LOOKALIKE | True | 4.559 |  |
| HMMC | CAD | UNVERIFIED_CORP_ACTION | REINSTATE | FIX_DATA | YES | SPIKE | 2023-01-03 | -6.000 | -0.3800 | 0.5965 | GENUINE_VOL | True | 2.551 | NON_POSITIVE_CLOSE |
| HON | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2026-06-29 | -0.507 | 0.4979 | 0.1189 | SPLIT_LOOKALIKE | True | 0.678 |  |
| HSLV | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2023-08-17 | -0.545 | 0.6364 | 0.5714 | GENUINE_VOL | True | N/A |  |
| ITH | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2013-07-24 | -0.538 | 0.9048 | 0.5526 | GENUINE_VOL | True | 2.128 |  |
| KNT | CAD | UNVERIFIED_CORP_ACTION | REINSTATE | REINSTATE |  | SPIKE | 2011-01-24 | 1.515 | 2.2000 | 0.2273 | GENUINE_VOL | True | 0.059 |  |
| LCFS | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2024-08-15 | -0.577 | 0.3094 | 0.1958 | SPLIT_LOOKALIKE | True | 5.675 |  |
| MARI | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2011-08-25 | -0.544 | 0.4426 | 0.3704 | GENUINE_VOL | True | 10.512 |  |
| NXR.UN | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2012-12-21 | 3.000 | 1.4999 | 1.7999 | GENUINE_VOL | False | 1.364 |  |
| OVV | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2020-03-09 | -0.724 | 0.1995 | 0.3552 | GENUINE_VOL | True | 2.397 |  |
| PMET | CAD | UNVERIFIED_CORP_ACTION | REINSTATE | REINSTATE |  | SPIKE | 2016-06-07 | 1.650 | 2.3333 | 0.3143 | GENUINE_VOL | True | 13.263 |  |
| RFA | CAD | UNVERIFIED_CORP_ACTION | REINSTATE | REINSTATE |  | SPIKE | 2026-02-04 | 2.373 | 2.6256 | 0.0889 | GENUINE_VOL | True | 0.561 |  |
| RIO | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2008-08-27 | -0.571 | 0.2666 | 1.2501 | GENUINE_VOL | False | 1.923 |  |
| SCR | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2010-10-19 | -0.602 | 0.3036 | 0.2060 | SPLIT_LOOKALIKE | True | 0.942 |  |
| SDE | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2010-01-25 | -0.541 | 0.4714 | 0.2727 | SPLIT_LOOKALIKE | False | 3.141 |  |
| SKE | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2008-10-14 | -0.600 | 0.4286 | 1.0000 | GENUINE_VOL | False | 0.619 |  |
| SOIL | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2011-03-29 | 1.022 | 1.5568 | 0.2044 | SPLIT_LOOKALIKE | True | 7.723 |  |
| SSRM | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2024-02-13 | -0.535 | 0.4549 | 0.1283 | SPLIT_LOOKALIKE | True | 2.835 |  |
| SVI | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2008-12-03 | 1.491 | 0.4119 | 1.8239 | GENUINE_VOL | False | 4.500 |  |
| TNZ | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2009-06-24 | -0.667 | 0.6346 | 1.0303 | GENUINE_VOL | False | 32.154 |  |
| TRI | CAD | INSUFFICIENT_LOOKBACK_FOR_HURST100 | REINSTATE | REINSTATE |  | CLEAN_NOW | N/A | N/A | N/A | N/A | N/A | N/A | N/A |  |
| TVE | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2008-12-18 | -0.546 | 1.0000 | 0.7335 | GENUINE_VOL | False | 1.456 |  |
| VLE | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2019-12-13 | -0.538 | 0.6011 | 0.2301 | SPLIT_LOOKALIKE | False | 5.254 |  |
| VZLA | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2018-09-20 | 2.286 | 2.9898 | 0.2321 | SPLIT_LOOKALIKE | True | N/A |  |
| WCP | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2008-12-05 | -0.560 | 0.7408 | 0.1998 | SPLIT_LOOKALIKE | False | 1.250 |  |
| WELL | CAD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2013-12-09 | 3.500 | 0.5682 | 0.8000 | GENUINE_VOL | True | N/A |  |
| AEG | USD | UNVERIFIED_CORP_ACTION | REINSTATE | REINSTATE |  | SPIKE | 2020-08-21 | -0.975 | 0.0226 | 0.1413 | GENUINE_VOL | True | 28.987 |  |
| APA | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2020-03-09 | -0.539 | 0.1771 | 0.3860 | GENUINE_VOL | False | 2.856 |  |
| AUGO | USD | UNVERIFIED_CORP_ACTION | REINSTATE | REINSTATE |  | SPIKE | 2017-01-06 | -0.900 | 1.1441 | 0.1159 | GENUINE_VOL | True | N/A |  |
| CDE | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2008-11-18 | -0.528 | 0.4112 | 0.6240 | GENUINE_VOL | False | 1.376 |  |
| CMCSA | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2017-02-17 | -0.504 | 0.9961 | 0.0171 | GENUINE_VOL | True | 0.772 |  |
| CNO | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2009-03-02 | -0.598 | 0.2389 | 1.0465 | GENUINE_VOL | False | 2.722 |  |
| COGT | USD | UNVERIFIED_CORP_ACTION | REINSTATE | REINSTATE |  | SPIKE | 2020-07-06 | 3.946 | 5.4216 | 0.2647 | GENUINE_VOL | True | 22.205 |  |
| CORT | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2014-05-07 | -0.505 | 0.5013 | 0.2323 | SPLIT_LOOKALIKE | True | 1.265 |  |
| CVE | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2020-03-09 | -0.525 | 0.2180 | 0.5684 | GENUINE_VOL | True | 2.059 |  |
| CYTK | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2014-04-25 | -0.647 | 0.4674 | 0.2095 | SPLIT_LOOKALIKE | True | 0.654 |  |
| EXEL | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2014-09-02 | -0.553 | 0.4056 | 0.2269 | SPLIT_LOOKALIKE | True | 2.389 |  |
| FTNT | USD | UNVERIFIED_CORP_ACTION | REINSTATE | REINSTATE |  | SPIKE | 2014-01-13 | 3.016 | 4.5270 | 0.0898 | GENUINE_VOL | True | 0.249 |  |
| GME | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2021-01-27 | 1.348 | 2.5639 | 1.3322 | GENUINE_VOL | True | 0.299 |  |
| GOOG | USD | UNVERIFIED_CORP_ACTION | REINSTATE | REINSTATE |  | SPIKE | 2014-04-03 | 1.010 | 1.8941 | 0.0762 | GENUINE_VOL | True | 79.074 |  |
| HIG | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2008-10-30 | -0.516 | 0.3647 | 1.0413 | GENUINE_VOL | True | 4.206 |  |
| ICL | USD | UNVERIFIED_CORP_ACTION | REINSTATE | FIX_DATA | YES | SPIKE | 2014-12-01 | -1.207 | -0.2195 | -0.0991 | GENUINE_VOL | True | 1.119 | NON_POSITIVE_CLOSE |
| INSM | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2009-06-25 | -0.530 | 0.4621 | 0.2462 | SPLIT_LOOKALIKE | True | 1.447 |  |
| IOVA | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2022-05-27 | -0.536 | 0.5853 | 0.4162 | GENUINE_VOL | True | 7.773 |  |
| LYG | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2009-01-20 | -0.579 | 0.6997 | 0.6750 | GENUINE_VOL | False | 1.418 |  |
| MRNA | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2026-08-19 | 1.770 | 2.5388 | 0.1552 | SPLIT_LOOKALIKE | True | 8.937 |  |
| MTCH | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2020-07-02 | -0.694 | 0.3355 | 0.1286 | SPLIT_LOOKALIKE | True | 4.596 |  |
| MTDR | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2020-03-09 | -0.641 | 0.1824 | 0.7046 | GENUINE_VOL | False | 3.272 |  |
| MTG | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2012-08-02 | -0.641 | 0.5021 | 0.1925 | SPLIT_LOOKALIKE | True | 2.281 |  |
| NBIS | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2022-03-07 | -0.578 | 0.3010 | 0.8122 | GENUINE_VOL | False | N/A |  |
| NWG | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2009-01-20 | -0.693 | 0.4287 | 0.4760 | GENUINE_VOL | False | 3.093 |  |
| ORKA | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2010-03-26 | 2.079 | 1.7300 | 0.2477 | SPLIT_LOOKALIKE | True | 215.710 |  |
| OVV | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2020-03-09 | -0.720 | 0.1869 | 0.3633 | GENUINE_VOL | True | 3.022 |  |
| OXY | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2020-03-09 | -0.520 | 0.2915 | 0.3272 | SPLIT_LOOKALIKE | True | 4.019 |  |
| PCG | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2019-01-14 | -0.524 | 0.5756 | 0.5655 | GENUINE_VOL | False | 2.302 |  |
| PR | USD | UNVERIFIED_CORP_ACTION | REINSTATE | REINSTATE |  | SPIKE | 2020-03-09 | -0.632 | 0.1324 | 0.9162 | GENUINE_VOL | False | 1.481 |  |
| SM | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2020-03-09 | -0.613 | 0.1524 | 0.4615 | GENUINE_VOL | False | 1.955 |  |
| SPCX | USD | INSUFFICIENT_LOOKBACK_FOR_HURST100 | REINSTATE | REINSTATE |  | CLEAN_NOW | N/A | N/A | N/A | N/A | N/A | N/A | N/A |  |
| SSRM | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2024-02-13 | -0.537 | 0.4539 | 0.1293 | SPLIT_LOOKALIKE | True | 3.770 |  |
| STT | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2009-01-20 | -0.590 | 0.6427 | 0.4368 | GENUINE_VOL | False | 5.093 |  |
| SYRE | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2022-06-02 | -0.513 | 0.4320 | 0.3606 | GENUINE_VOL | True | 10.976 |  |
| TAL | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | KEEP_QUARANTINED |  | SPIKE | 2021-07-23 | -0.708 | 0.2698 | 0.2392 | SPLIT_LOOKALIKE | True | 4.498 |  |
| WES | USD | UNVERIFIED_CORP_ACTION | KEEP_QUARANTINED | REINSTATE | YES | SPIKE | 2020-03-09 | -0.548 | 0.2490 | 0.5740 | GENUINE_VOL | True | 2.367 |  |

## 6. Verdict flips vs the 17/55 baseline

- Total verdict flips vs baseline: **36** of 72 rows

| Symbol | Market | Baseline | Final |
| :--- | :---: | :--- | :--- |
| CVE | CAD | KEEP_QUARANTINED | REINSTATE |
| DSV | CAD | KEEP_QUARANTINED | REINSTATE |
| HMMC | CAD | REINSTATE | FIX_DATA |
| HSLV | CAD | KEEP_QUARANTINED | REINSTATE |
| ITH | CAD | KEEP_QUARANTINED | REINSTATE |
| MARI | CAD | KEEP_QUARANTINED | REINSTATE |
| NXR.UN | CAD | KEEP_QUARANTINED | REINSTATE |
| OVV | CAD | KEEP_QUARANTINED | REINSTATE |
| RIO | CAD | KEEP_QUARANTINED | REINSTATE |
| SDE | CAD | KEEP_QUARANTINED | REINSTATE |
| SKE | CAD | KEEP_QUARANTINED | REINSTATE |
| SVI | CAD | KEEP_QUARANTINED | REINSTATE |
| TNZ | CAD | KEEP_QUARANTINED | REINSTATE |
| TVE | CAD | KEEP_QUARANTINED | REINSTATE |
| VLE | CAD | KEEP_QUARANTINED | REINSTATE |
| WCP | CAD | KEEP_QUARANTINED | REINSTATE |
| WELL | CAD | KEEP_QUARANTINED | REINSTATE |
| APA | USD | KEEP_QUARANTINED | REINSTATE |
| CDE | USD | KEEP_QUARANTINED | REINSTATE |
| CMCSA | USD | KEEP_QUARANTINED | REINSTATE |
| CNO | USD | KEEP_QUARANTINED | REINSTATE |
| CVE | USD | KEEP_QUARANTINED | REINSTATE |
| GME | USD | KEEP_QUARANTINED | REINSTATE |
| HIG | USD | KEEP_QUARANTINED | REINSTATE |
| ICL | USD | REINSTATE | FIX_DATA |
| IOVA | USD | KEEP_QUARANTINED | REINSTATE |
| LYG | USD | KEEP_QUARANTINED | REINSTATE |
| MTDR | USD | KEEP_QUARANTINED | REINSTATE |
| NBIS | USD | KEEP_QUARANTINED | REINSTATE |
| NWG | USD | KEEP_QUARANTINED | REINSTATE |
| OVV | USD | KEEP_QUARANTINED | REINSTATE |
| PCG | USD | KEEP_QUARANTINED | REINSTATE |
| SM | USD | KEEP_QUARANTINED | REINSTATE |
| STT | USD | KEEP_QUARANTINED | REINSTATE |
| SYRE | USD | KEEP_QUARANTINED | REINSTATE |
| WES | USD | KEEP_QUARANTINED | REINSTATE |

- Flip symbols: CVE/CAD, DSV/CAD, HMMC/CAD, HSLV/CAD, ITH/CAD, MARI/CAD, NXR.UN/CAD, OVV/CAD, RIO/CAD, SDE/CAD, SKE/CAD, SVI/CAD, TNZ/CAD, TVE/CAD, VLE/CAD, WCP/CAD, WELL/CAD, APA/USD, CDE/USD, CMCSA/USD, CNO/USD, CVE/USD, GME/USD, HIG/USD, ICL/USD, IOVA/USD, LYG/USD, MTDR/USD, NBIS/USD, NWG/USD, OVV/USD, PCG/USD, SM/USD, STT/USD, SYRE/USD, WES/USD

## 7. Recommendation summary (human gate)

| Final recommendation | Count | Baseline count |
| :--- | ---: | ---: |
| REINSTATE | 49 | 17 |
| KEEP_QUARANTINED | 21 | 55 |
| FIX_DATA | 2 | 0 |
| OWNER_ACTION | 0 | 0 |
| AMBIGUOUS | 0 | 0 |

**STOP — human gate.** This table is a recommendation only. No ticker has been reinstated, kept, or otherwise changed; `data/dead_letter_tickers.csv` and all quarantine state are byte-identical to their pre-run contents.

