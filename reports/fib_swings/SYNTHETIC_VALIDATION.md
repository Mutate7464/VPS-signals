# SYNTHETIC VALIDATION — fold-stability gate (WI-031)

NULL/CONSTANT/CHAOTIC x 20 seeds | gate code imported

## Accept rate (NULL = false positive)

| variant | NULL FP | CONSTANT | CHAOTIC |
|---|---|---|---|
| strict_5of5 | 0.000 | 1.000 | 0.850 |
| loose_4of5 | 0.000 | 1.000 | 0.900 |
| loose_4of5_pooled | 0.000 | 1.000 | 0.900 |
| pooled_only_t2 | 0.250 | 1.000 | 1.000 |
| loose_3of5_pooled | 0.000 | 1.000 | 0.900 |

## Calibration check (strict 5/5)

edge 0.0125 over the 0.5% floor | NULL FP 0.000 vs CONSTANT false-rejection 0.000 | gap 0.000

## CPU (core-seconds, hard cap 4 core-hours = 14400)

- NULL: 163
- CONSTANT: 155
- CHAOTIC: 152
- total: 469

## Recommendation

Adopt loose_4of5: CHAOTIC detection 0.90 vs strict 0.85, NULL FP 0.00 vs 0.00.

VERDICT: ADOPT_LOOSE_4OF5
