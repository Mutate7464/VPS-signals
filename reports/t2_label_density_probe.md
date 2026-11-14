# WI-048b — T2 label-density probe (D-025 tier 2)

- Generated (UTC): 2026-11-11T04:43:54Z
- Families: up, high_low, vol_expand; horizons 5, 8, 13, 21, 34, 55; pinned geometry per market {'USD': 'exact', 'CAD': 'tol2'}; sparse = < 25 positives
- Labels are computed from price paths only (no features, no training, no pickles).

## 1. Prevalence per cell

| market | family | h | event | events | positives | prevalence | flag |
| :--- | :--- | ---: | :--- | ---: | ---: | ---: | :--- |
| USD | `up` | 5 | exact | 117025 | 61805 | 0.5281 | ok |
| USD | `up` | 8 | exact | 117025 | 62775 | 0.5364 | ok |
| USD | `up` | 13 | exact | 117025 | 63573 | 0.5432 | ok |
| USD | `up` | 21 | exact | 117025 | 64206 | 0.5487 | ok |
| USD | `up` | 34 | exact | 117025 | 64927 | 0.5548 | ok |
| USD | `up` | 55 | exact | 117025 | 66078 | 0.5646 | ok |
| USD | `high_low` | 5 | exact | 117025 | 88392 | 0.7553 | ok |
| USD | `high_low` | 8 | exact | 117025 | 93969 | 0.8030 | ok |
| USD | `high_low` | 13 | exact | 117025 | 98530 | 0.8420 | ok |
| USD | `high_low` | 21 | exact | 117025 | 102332 | 0.8744 | ok |
| USD | `high_low` | 34 | exact | 117025 | 105290 | 0.8997 | ok |
| USD | `high_low` | 55 | exact | 117025 | 107785 | 0.9210 | ok |
| USD | `vol_expand` | 5 | exact | 117025 | 65431 | 0.5591 | ok |
| USD | `vol_expand` | 8 | exact | 117025 | 62064 | 0.5303 | ok |
| USD | `vol_expand` | 13 | exact | 117025 | 59156 | 0.5055 | ok |
| USD | `vol_expand` | 21 | exact | 117025 | 55204 | 0.4717 | ok |
| USD | `vol_expand` | 34 | exact | 117025 | 54361 | 0.4645 | ok |
| USD | `vol_expand` | 55 | exact | 117025 | 53809 | 0.4598 | ok |
| CAD | `up` | 5 | tol2 | 64166 | 32592 | 0.5079 | ok |
| CAD | `up` | 8 | tol2 | 64166 | 33315 | 0.5192 | ok |
| CAD | `up` | 13 | tol2 | 64166 | 33876 | 0.5279 | ok |
| CAD | `up` | 21 | tol2 | 64166 | 34758 | 0.5417 | ok |
| CAD | `up` | 34 | tol2 | 64166 | 35196 | 0.5485 | ok |
| CAD | `up` | 55 | tol2 | 64166 | 36060 | 0.5620 | ok |
| CAD | `high_low` | 5 | tol2 | 64166 | 35468 | 0.5528 | ok |
| CAD | `high_low` | 8 | tol2 | 64166 | 40827 | 0.6363 | ok |
| CAD | `high_low` | 13 | tol2 | 64166 | 45395 | 0.7075 | ok |
| CAD | `high_low` | 21 | tol2 | 64166 | 49152 | 0.7660 | ok |
| CAD | `high_low` | 34 | tol2 | 64166 | 52307 | 0.8152 | ok |
| CAD | `high_low` | 55 | tol2 | 64166 | 54736 | 0.8530 | ok |
| CAD | `vol_expand` | 5 | tol2 | 64166 | 35091 | 0.5469 | ok |
| CAD | `vol_expand` | 8 | tol2 | 64166 | 33539 | 0.5227 | ok |
| CAD | `vol_expand` | 13 | tol2 | 64166 | 32109 | 0.5004 | ok |
| CAD | `vol_expand` | 21 | tol2 | 64166 | 29911 | 0.4662 | ok |
| CAD | `vol_expand` | 34 | tol2 | 64166 | 29878 | 0.4656 | ok |
| CAD | `vol_expand` | 55 | tol2 | 64166 | 29247 | 0.4558 | ok |

## 2. Density ranking (mean prevalence per family x market)

| family | denser market | mean prevalence |
| :--- | :--- | ---: |
| `up` | USD | 0.5460 |
| `high_low` | USD | 0.8492 |
| `vol_expand` | USD | 0.4985 |

## 3. Sparse cells (reported, never dropped)

- none

## Notes / deviations

- This probe is the smoke gate for WI-048c/d/e: the denser market per family is the dry-run market named in the sprint brief.
- Prevalence is measured on the pinned event geometry only (USD `exact`, CAD `tol2`); the other geometry stays available through `target_labels`.

