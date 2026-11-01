# WI-018 G2 falsification probe — `first_touch_34` (USD)

Generated 2026-11-01T03:56:26Z. Verdict **G2_PASS_WITH_RED_FLAG** (G3 skipped).

**G3 gate:** G3 not invoked — survivor density 0.685 > 0.1: a wall of survivors is a noise/leakage red flag, not a win, so G3 is not invoked.

## Design (frozen before the run)

- states: within-date USD cross-sectional quantiles, identical to the G1 atlas (88 features × 8 states × 2 directions)
- folds: 5 chronological held-out blocks (`src.wi011.stats.fold_blocks`), embargo 34 sessions (= max(20, horizon 34)); held-out dates 2850 (56.64%)
- correction: Benjamini-Hochberg over the complete family (univariate + conjunctions), alpha 0.05
- evidence: circular 20-date blocks, 1000 draws, seed 42; decision rule = CI excludes zero AND BH-FDR reject AND same-sign bar
- conjunctions: AND-pairs of the 50 best univariate FDR-surviving states (≤50), 1125 pairs, depth ≤ 2

## Hypothesis family

| quantity | value |
|---|---|
| univariate hypotheses | 1408 (1392 estimable) |
| conjunction hypotheses | 2250 |
| total family | 3658 (3454 tested) |
| BH rejections at 0.05 | 2933 |
| univariate BH rejections (pair-selection pass) | 931 |
| survivors (CI excludes zero + BH + same sign) | **2506** |
| survivor density | 0.6851 (red flag above 0.1) |
| smallest p in the family | 0.0000 |

Red flag: survivor density 0.685 > 0.1 — a wall of survivors is a noise/leakage red flag, not a win

## Unconditional reference (held-out dates)

| class | date-mean rate | 95% CI | pooled |
|---|---|---|---|
| up | 0.3794 | [0.3574, 0.4015] | 0.3836 |
| dn | 0.2976 | [0.2709, 0.3243] | 0.2999 |
| neither | 0.3229 | [0.2996, 0.3462] | 0.3165 |

## Survivors

| condition | dir | n | n_dates | lift | 95% CI | q | same-sign | folds same-sign |
|---|---|---|---|---|---|---|---|---|
| amihud_102|quintile/1 | up | 98790 | 2850 | -0.0530 | [-0.0607, -0.0454] | 0.0000 | True | True |
| amihud_102|quintile/5 | dn | 102904 | 2850 | +0.0507 | [+0.0412, +0.0602] | 0.0000 | True | True |
| amihud_102|quintile/5 | up | 133833 | 2850 | +0.0714 | [+0.0633, +0.0794] | 0.0000 | True | True |
| amihud_102|tercile/1 | dn | 130870 | 2850 | -0.0371 | [-0.0439, -0.0303] | 0.0000 | True | True |
| amihud_102|tercile/1 | up | 167886 | 2850 | -0.0453 | [-0.0514, -0.0393] | 0.0000 | True | True |
| amihud_102|tercile/3 | dn | 165499 | 2850 | +0.0375 | [+0.0305, +0.0445] | 0.0000 | True | True |
| amihud_102|tercile/3 | up | 215128 | 2850 | +0.0541 | [+0.0480, +0.0602] | 0.0000 | True | True |
| amihud_144|quintile/1 | up | 98323 | 2850 | -0.0532 | [-0.0612, -0.0453] | 0.0000 | True | True |
| amihud_144|quintile/5 | dn | 102417 | 2850 | +0.0506 | [+0.0414, +0.0599] | 0.0000 | True | True |
| amihud_144|quintile/5 | up | 133240 | 2850 | +0.0713 | [+0.0631, +0.0794] | 0.0000 | True | True |
| amihud_144|tercile/1 | dn | 129788 | 2850 | -0.0381 | [-0.0447, -0.0314] | 0.0000 | True | True |
| amihud_144|tercile/1 | up | 167146 | 2850 | -0.0455 | [-0.0515, -0.0395] | 0.0000 | True | True |
| amihud_144|tercile/3 | dn | 164785 | 2850 | +0.0375 | [+0.0305, +0.0446] | 0.0000 | True | True |
| amihud_144|tercile/3 | up | 214276 | 2850 | +0.0542 | [+0.0482, +0.0602] | 0.0000 | True | True |
| amihud_233|quintile/1 | up | 97496 | 2850 | -0.0529 | [-0.0608, -0.0450] | 0.0000 | True | True |
| amihud_233|quintile/5 | up | 132090 | 2850 | +0.0714 | [+0.0633, +0.0794] | 0.0000 | True | True |
| amihud_233|tercile/1 | dn | 128495 | 2850 | -0.0380 | [-0.0447, -0.0313] | 0.0000 | True | True |
| amihud_233|tercile/1 | up | 165041 | 2850 | -0.0466 | [-0.0524, -0.0408] | 0.0000 | True | True |
| amihud_233|tercile/3 | up | 211497 | 2850 | +0.0525 | [+0.0465, +0.0585] | 0.0000 | True | True |
| amihud_24|quintile/1 | up | 98418 | 2850 | -0.0563 | [-0.0641, -0.0484] | 0.0000 | True | True |
| amihud_24|quintile/1 & amihud_39|quintile/1 | up | 94074 | 2850 | -0.0569 | [-0.0648, -0.0489] | 0.0000 | True | True |
| amihud_24|quintile/1 & amihud_39|tercile/1 | up | 98218 | 2850 | -0.0565 | [-0.0643, -0.0487] | 0.0000 | True | True |
| amihud_24|quintile/1 & amihud_63|quintile/1 | up | 92019 | 2850 | -0.0570 | [-0.0651, -0.0489] | 0.0000 | True | True |
| amihud_24|quintile/5 | up | 135135 | 2850 | +0.0721 | [+0.0644, +0.0798] | 0.0000 | True | True |
| amihud_24|quintile/5 & amihud_39|quintile/5 | up | 128928 | 2850 | +0.0723 | [+0.0642, +0.0804] | 0.0000 | True | True |
| amihud_24|quintile/5 & amihud_39|tercile/3 | up | 134644 | 2850 | +0.0720 | [+0.0644, +0.0797] | 0.0000 | True | True |
| amihud_24|tercile/1 | up | 168787 | 2850 | -0.0459 | [-0.0519, -0.0400] | 0.0000 | True | True |
| amihud_24|tercile/1 & amihud_39|quintile/1 | up | 98453 | 2850 | -0.0558 | [-0.0635, -0.0480] | 0.0000 | True | True |
| amihud_24|tercile/1 & amihud_39|tercile/1 | up | 162673 | 2850 | -0.0466 | [-0.0528, -0.0405] | 0.0000 | True | True |
| amihud_24|tercile/1 & amihud_63|quintile/1 | up | 98518 | 2850 | -0.0549 | [-0.0625, -0.0473] | 0.0000 | True | True |
| amihud_24|tercile/3 | dn | 167315 | 2850 | +0.0387 | [+0.0312, +0.0461] | 0.0000 | True | True |
| amihud_24|tercile/3 | up | 216981 | 2850 | +0.0545 | [+0.0485, +0.0605] | 0.0000 | True | True |
| amihud_24|tercile/3 & amihud_39|quintile/5 | up | 134476 | 2850 | +0.0711 | [+0.0633, +0.0789] | 0.0000 | True | True |
| amihud_24|tercile/3 & amihud_39|tercile/3 | dn | 161117 | 2850 | +0.0388 | [+0.0313, +0.0464] | 0.0000 | True | True |
| amihud_24|tercile/3 & amihud_39|tercile/3 | up | 209482 | 2850 | +0.0557 | [+0.0496, +0.0618] | 0.0000 | True | True |
| amihud_39|quintile/1 | up | 98453 | 2850 | -0.0558 | [-0.0635, -0.0480] | 0.0000 | True | True |
| amihud_39|quintile/1 & amihud_63|quintile/1 | up | 94452 | 2850 | -0.0563 | [-0.0641, -0.0485] | 0.0000 | True | True |
| amihud_39|quintile/5 | up | 134632 | 2850 | +0.0712 | [+0.0634, +0.0790] | 0.0000 | True | True |
| amihud_39|tercile/1 | up | 168705 | 2850 | -0.0456 | [-0.0518, -0.0394] | 0.0000 | True | True |
| amihud_39|tercile/1 & amihud_63|quintile/1 | up | 98520 | 2850 | -0.0549 | [-0.0625, -0.0473] | 0.0000 | True | True |
| amihud_39|tercile/3 | dn | 166799 | 2850 | +0.0381 | [+0.0306, +0.0456] | 0.0000 | True | True |
| amihud_39|tercile/3 | up | 216414 | 2850 | +0.0540 | [+0.0481, +0.0599] | 0.0000 | True | True |
| amihud_3|quintile/1 | up | 99122 | 2850 | -0.0544 | [-0.0617, -0.0471] | 0.0000 | True | True |
| amihud_3|quintile/1 & amihud_24|quintile/1 | up | 81689 | 2850 | -0.0592 | [-0.0678, -0.0505] | 0.0000 | True | True |
| amihud_3|quintile/1 & amihud_24|tercile/1 | up | 94435 | 2850 | -0.0564 | [-0.0641, -0.0487] | 0.0000 | True | True |
| amihud_3|quintile/1 & amihud_39|quintile/1 | up | 80851 | 2850 | -0.0592 | [-0.0678, -0.0506] | 0.0000 | True | True |
| amihud_3|quintile/1 & amihud_39|tercile/1 | up | 93897 | 2850 | -0.0566 | [-0.0644, -0.0488] | 0.0000 | True | True |
| amihud_3|quintile/1 & amihud_63|quintile/1 | up | 80271 | 2850 | -0.0590 | [-0.0677, -0.0502] | 0.0000 | True | True |
| amihud_3|quintile/1 & amihud_6|quintile/1 | up | 86600 | 2850 | -0.0569 | [-0.0651, -0.0486] | 0.0000 | True | True |
| amihud_3|quintile/1 & amihud_6|tercile/1 | up | 97022 | 2850 | -0.0551 | [-0.0626, -0.0477] | 0.0000 | True | True |
| amihud_3|quintile/1 & amihud_9|quintile/1 | up | 84517 | 2850 | -0.0576 | [-0.0660, -0.0492] | 0.0000 | True | True |
| amihud_3|quintile/1 & amihud_9|tercile/1 | up | 96018 | 2850 | -0.0556 | [-0.0631, -0.0481] | 0.0000 | True | True |
| amihud_3|quintile/5 | up | 134618 | 2850 | +0.0696 | [+0.0619, +0.0772] | 0.0000 | True | True |
| amihud_3|quintile/5 & amihud_24|quintile/5 | up | 115227 | 2850 | +0.0750 | [+0.0666, +0.0834] | 0.0000 | True | True |
| amihud_3|quintile/5 & amihud_24|tercile/3 | up | 133212 | 2850 | +0.0698 | [+0.0621, +0.0775] | 0.0000 | True | True |
| amihud_3|quintile/5 & amihud_39|quintile/5 | up | 113557 | 2850 | +0.0744 | [+0.0659, +0.0830] | 0.0000 | True | True |
| amihud_3|quintile/5 & amihud_39|tercile/3 | up | 132476 | 2850 | +0.0698 | [+0.0621, +0.0776] | 0.0000 | True | True |
| amihud_3|quintile/5 & amihud_6|quintile/5 | up | 121335 | 2850 | +0.0733 | [+0.0650, +0.0817] | 0.0000 | True | True |
| amihud_3|quintile/5 & amihud_6|tercile/3 | up | 134461 | 2850 | +0.0696 | [+0.0618, +0.0773] | 0.0000 | True | True |
| amihud_3|quintile/5 & amihud_9|quintile/5 | up | 119012 | 2850 | +0.0745 | [+0.0660, +0.0829] | 0.0000 | True | True |
| amihud_3|quintile/5 & amihud_9|tercile/3 | up | 134195 | 2850 | +0.0696 | [+0.0619, +0.0773] | 0.0000 | True | True |
| amihud_3|tercile/1 | up | 169601 | 2850 | -0.0448 | [-0.0505, -0.0392] | 0.0000 | True | True |
| amihud_3|tercile/1 & amihud_24|quintile/1 | up | 97708 | 2850 | -0.0562 | [-0.0641, -0.0483] | 0.0000 | True | True |
| amihud_3|tercile/1 & amihud_24|tercile/1 | up | 145690 | 2850 | -0.0485 | [-0.0550, -0.0421] | 0.0000 | True | True |
| amihud_3|tercile/1 & amihud_39|quintile/1 | up | 97448 | 2850 | -0.0557 | [-0.0636, -0.0479] | 0.0000 | True | True |
| amihud_3|tercile/1 & amihud_39|tercile/1 | up | 144517 | 2850 | -0.0486 | [-0.0550, -0.0421] | 0.0000 | True | True |
| amihud_3|tercile/1 & amihud_63|quintile/1 | up | 97266 | 2850 | -0.0551 | [-0.0627, -0.0475] | 0.0000 | True | True |
| amihud_3|tercile/1 & amihud_6|quintile/1 | up | 98953 | 2850 | -0.0547 | [-0.0626, -0.0469] | 0.0000 | True | True |
| amihud_3|tercile/1 & amihud_6|tercile/1 | up | 152362 | 2850 | -0.0473 | [-0.0535, -0.0412] | 0.0000 | True | True |
| amihud_3|tercile/1 & amihud_9|quintile/1 | up | 98510 | 2850 | -0.0554 | [-0.0634, -0.0474] | 0.0000 | True | True |
| amihud_3|tercile/1 & amihud_9|tercile/1 | up | 149495 | 2850 | -0.0481 | [-0.0544, -0.0419] | 0.0000 | True | True |
| amihud_3|tercile/3 | dn | 167049 | 2850 | +0.0374 | [+0.0306, +0.0443] | 0.0000 | True | True |
| amihud_3|tercile/3 | up | 216258 | 2850 | +0.0521 | [+0.0463, +0.0580] | 0.0000 | True | True |
| amihud_3|tercile/3 & amihud_24|quintile/5 | up | 130828 | 2850 | +0.0728 | [+0.0649, +0.0807] | 0.0000 | True | True |
| amihud_3|tercile/3 & amihud_24|tercile/3 | dn | 147375 | 2850 | +0.0411 | [+0.0335, +0.0487] | 0.0000 | True | True |
| amihud_3|tercile/3 & amihud_24|tercile/3 | up | 191576 | 2850 | +0.0591 | [+0.0528, +0.0654] | 0.0000 | True | True |
| amihud_3|tercile/3 & amihud_39|quintile/5 | up | 129728 | 2850 | +0.0719 | [+0.0639, +0.0800] | 0.0000 | True | True |
| amihud_3|tercile/3 & amihud_39|tercile/3 | dn | 145750 | 2850 | +0.0409 | [+0.0333, +0.0486] | 0.0000 | True | True |
| amihud_3|tercile/3 & amihud_39|tercile/3 | up | 189607 | 2850 | +0.0590 | [+0.0526, +0.0653] | 0.0000 | True | True |
| amihud_3|tercile/3 & amihud_6|quintile/5 | up | 133373 | 2850 | +0.0716 | [+0.0637, +0.0795] | 0.0000 | True | True |
| amihud_3|tercile/3 & amihud_6|tercile/3 | dn | 153493 | 2850 | +0.0401 | [+0.0329, +0.0474] | 0.0000 | True | True |
| amihud_3|tercile/3 & amihud_6|tercile/3 | up | 199055 | 2850 | +0.0569 | [+0.0506, +0.0632] | 0.0000 | True | True |
| amihud_3|tercile/3 & amihud_9|quintile/5 | up | 132533 | 2850 | +0.0722 | [+0.0642, +0.0803] | 0.0000 | True | True |
| amihud_3|tercile/3 & amihud_9|tercile/3 | dn | 151044 | 2850 | +0.0406 | [+0.0332, +0.0479] | 0.0000 | True | True |
| amihud_3|tercile/3 & amihud_9|tercile/3 | up | 196049 | 2850 | +0.0579 | [+0.0514, +0.0643] | 0.0000 | True | True |
| amihud_63|quintile/1 | up | 98520 | 2850 | -0.0549 | [-0.0625, -0.0473] | 0.0000 | True | True |
| amihud_63|quintile/5 | up | 134519 | 2850 | +0.0720 | [+0.0640, +0.0800] | 0.0000 | True | True |
| amihud_63|tercile/1 | up | 168183 | 2850 | -0.0460 | [-0.0521, -0.0399] | 0.0000 | True | True |
| amihud_63|tercile/3 | dn | 166138 | 2850 | +0.0375 | [+0.0302, +0.0448] | 0.0000 | True | True |
| amihud_63|tercile/3 | up | 216041 | 2850 | +0.0544 | [+0.0482, +0.0605] | 0.0000 | True | True |
| amihud_6|quintile/1 | up | 99008 | 2850 | -0.0547 | [-0.0626, -0.0469] | 0.0000 | True | True |
| amihud_6|quintile/1 & amihud_24|quintile/1 | up | 87937 | 2850 | -0.0580 | [-0.0665, -0.0494] | 0.0000 | True | True |
| amihud_6|quintile/1 & amihud_24|tercile/1 | up | 97785 | 2850 | -0.0557 | [-0.0636, -0.0478] | 0.0000 | True | True |
| amihud_6|quintile/1 & amihud_39|quintile/1 | up | 86717 | 2850 | -0.0580 | [-0.0665, -0.0495] | 0.0000 | True | True |
| amihud_6|quintile/1 & amihud_39|tercile/1 | up | 97285 | 2850 | -0.0561 | [-0.0640, -0.0481] | 0.0000 | True | True |
| amihud_6|quintile/1 & amihud_63|quintile/1 | up | 85808 | 2850 | -0.0580 | [-0.0665, -0.0496] | 0.0000 | True | True |
| amihud_6|quintile/1 & amihud_9|quintile/1 | up | 92158 | 2850 | -0.0564 | [-0.0646, -0.0482] | 0.0000 | True | True |
| amihud_6|quintile/1 & amihud_9|tercile/1 | up | 98728 | 2850 | -0.0550 | [-0.0629, -0.0472] | 0.0000 | True | True |
| amihud_6|quintile/5 | up | 135046 | 2850 | +0.0711 | [+0.0632, +0.0790] | 0.0000 | True | True |
| amihud_6|quintile/5 & amihud_24|quintile/5 | up | 121399 | 2850 | +0.0739 | [+0.0655, +0.0823] | 0.0000 | True | True |
| amihud_6|quintile/5 & amihud_24|tercile/3 | up | 134391 | 2850 | +0.0710 | [+0.0631, +0.0789] | 0.0000 | True | True |
| amihud_6|quintile/5 & amihud_39|quintile/5 | up | 119298 | 2850 | +0.0737 | [+0.0652, +0.0822] | 0.0000 | True | True |
| amihud_6|quintile/5 & amihud_39|tercile/3 | up | 133801 | 2850 | +0.0710 | [+0.0632, +0.0789] | 0.0000 | True | True |
| amihud_6|quintile/5 & amihud_9|quintile/5 | up | 127190 | 2850 | +0.0731 | [+0.0648, +0.0814] | 0.0000 | True | True |
| amihud_6|quintile/5 & amihud_9|tercile/3 | up | 134942 | 2850 | +0.0711 | [+0.0631, +0.0790] | 0.0000 | True | True |
| amihud_6|tercile/1 | up | 169121 | 2850 | -0.0457 | [-0.0516, -0.0398] | 0.0000 | True | True |
| amihud_6|tercile/1 & amihud_24|quintile/1 | up | 98376 | 2850 | -0.0563 | [-0.0641, -0.0484] | 0.0000 | True | True |
| amihud_6|tercile/1 & amihud_24|tercile/1 | up | 153682 | 2850 | -0.0477 | [-0.0538, -0.0416] | 0.0000 | True | True |
| amihud_6|tercile/1 & amihud_39|quintile/1 | up | 98317 | 2850 | -0.0558 | [-0.0635, -0.0480] | 0.0000 | True | True |
| amihud_6|tercile/1 & amihud_39|tercile/1 | up | 152016 | 2850 | -0.0478 | [-0.0541, -0.0416] | 0.0000 | True | True |
| amihud_6|tercile/1 & amihud_63|quintile/1 | up | 98296 | 2850 | -0.0550 | [-0.0626, -0.0474] | 0.0000 | True | True |
| amihud_6|tercile/1 & amihud_9|quintile/1 | up | 98761 | 2850 | -0.0554 | [-0.0634, -0.0475] | 0.0000 | True | True |
| amihud_6|tercile/1 & amihud_9|tercile/1 | up | 159538 | 2850 | -0.0471 | [-0.0532, -0.0411] | 0.0000 | True | True |
| amihud_6|tercile/3 | dn | 167513 | 2850 | +0.0385 | [+0.0314, +0.0456] | 0.0000 | True | True |
| amihud_6|tercile/3 | up | 216910 | 2850 | +0.0536 | [+0.0476, +0.0595] | 0.0000 | True | True |
| amihud_6|tercile/3 & amihud_24|quintile/5 | up | 133823 | 2850 | +0.0721 | [+0.0644, +0.0799] | 0.0000 | True | True |
| amihud_6|tercile/3 & amihud_24|tercile/3 | dn | 153854 | 2850 | +0.0407 | [+0.0332, +0.0482] | 0.0000 | True | True |
| amihud_6|tercile/3 & amihud_24|tercile/3 | up | 199790 | 2850 | +0.0580 | [+0.0518, +0.0642] | 0.0000 | True | True |
| amihud_6|tercile/3 & amihud_39|quintile/5 | up | 132779 | 2850 | +0.0712 | [+0.0631, +0.0792] | 0.0000 | True | True |
| amihud_6|tercile/3 & amihud_39|tercile/3 | dn | 151815 | 2850 | +0.0407 | [+0.0331, +0.0483] | 0.0000 | True | True |
| amihud_6|tercile/3 & amihud_39|tercile/3 | up | 197229 | 2850 | +0.0579 | [+0.0517, +0.0642] | 0.0000 | True | True |
| amihud_6|tercile/3 & amihud_9|quintile/5 | up | 134933 | 2850 | +0.0718 | [+0.0638, +0.0798] | 0.0000 | True | True |
| amihud_6|tercile/3 & amihud_9|tercile/3 | dn | 159377 | 2850 | +0.0398 | [+0.0325, +0.0470] | 0.0000 | True | True |
| amihud_6|tercile/3 & amihud_9|tercile/3 | up | 206777 | 2850 | +0.0563 | [+0.0500, +0.0626] | 0.0000 | True | True |
| amihud_9|quintile/1 | up | 98761 | 2850 | -0.0554 | [-0.0634, -0.0475] | 0.0000 | True | True |
| amihud_9|quintile/1 & amihud_24|quintile/1 | up | 90555 | 2850 | -0.0577 | [-0.0660, -0.0494] | 0.0000 | True | True |
| amihud_9|quintile/1 & amihud_24|tercile/1 | up | 98237 | 2850 | -0.0560 | [-0.0639, -0.0481] | 0.0000 | True | True |
| amihud_9|quintile/1 & amihud_39|quintile/1 | up | 89028 | 2850 | -0.0578 | [-0.0662, -0.0494] | 0.0000 | True | True |
| amihud_9|quintile/1 & amihud_39|tercile/1 | up | 97815 | 2850 | -0.0564 | [-0.0643, -0.0485] | 0.0000 | True | True |
| amihud_9|quintile/1 & amihud_63|quintile/1 | up | 87885 | 2850 | -0.0579 | [-0.0661, -0.0496] | 0.0000 | True | True |
| amihud_9|quintile/5 | up | 135182 | 2850 | +0.0717 | [+0.0637, +0.0797] | 0.0000 | True | True |
| amihud_9|quintile/5 & amihud_24|quintile/5 | up | 124528 | 2850 | +0.0732 | [+0.0649, +0.0816] | 0.0000 | True | True |
| amihud_9|quintile/5 & amihud_24|tercile/3 | up | 134678 | 2850 | +0.0716 | [+0.0636, +0.0795] | 0.0000 | True | True |
| amihud_9|quintile/5 & amihud_39|quintile/5 | up | 122035 | 2850 | +0.0731 | [+0.0646, +0.0816] | 0.0000 | True | True |
| amihud_9|quintile/5 & amihud_39|tercile/3 | up | 134147 | 2850 | +0.0715 | [+0.0635, +0.0794] | 0.0000 | True | True |
| amihud_9|tercile/1 | up | 168716 | 2850 | -0.0464 | [-0.0524, -0.0405] | 0.0000 | True | True |
| amihud_9|tercile/1 & amihud_24|quintile/1 | up | 98416 | 2850 | -0.0563 | [-0.0641, -0.0484] | 0.0000 | True | True |
| amihud_9|tercile/1 & amihud_24|tercile/1 | up | 157337 | 2850 | -0.0475 | [-0.0537, -0.0413] | 0.0000 | True | True |
| amihud_9|tercile/1 & amihud_39|quintile/1 | up | 98428 | 2850 | -0.0558 | [-0.0635, -0.0480] | 0.0000 | True | True |
| amihud_9|tercile/1 & amihud_39|tercile/1 | up | 155210 | 2850 | -0.0477 | [-0.0540, -0.0414] | 0.0000 | True | True |
| amihud_9|tercile/1 & amihud_63|quintile/1 | up | 98461 | 2850 | -0.0550 | [-0.0626, -0.0473] | 0.0000 | True | True |
| amihud_9|tercile/3 | dn | 167404 | 2850 | +0.0383 | [+0.0313, +0.0454] | 0.0000 | True | True |
| amihud_9|tercile/3 | up | 217164 | 2850 | +0.0542 | [+0.0483, +0.0602] | 0.0000 | True | True |
| amihud_9|tercile/3 & amihud_24|quintile/5 | up | 134555 | 2850 | +0.0719 | [+0.0642, +0.0797] | 0.0000 | True | True |
| amihud_9|tercile/3 & amihud_24|tercile/3 | dn | 157009 | 2850 | +0.0401 | [+0.0327, +0.0476] | 0.0000 | True | True |
| amihud_9|tercile/3 & amihud_24|tercile/3 | up | 203936 | 2850 | +0.0573 | [+0.0511, +0.0635] | 0.0000 | True | True |
| amihud_9|tercile/3 & amihud_39|quintile/5 | dn | 102889 | 2850 | +0.0512 | [+0.0417, +0.0607] | 0.0000 | True | True |
| amihud_9|tercile/3 & amihud_39|quintile/5 | up | 133618 | 2850 | +0.0710 | [+0.0630, +0.0790] | 0.0000 | True | True |
| amihud_9|tercile/3 & amihud_39|tercile/3 | dn | 154515 | 2850 | +0.0401 | [+0.0325, +0.0477] | 0.0000 | True | True |
| amihud_9|tercile/3 & amihud_39|tercile/3 | up | 200853 | 2850 | +0.0574 | [+0.0511, +0.0636] | 0.0000 | True | True |
| atr_pct_34|quintile/1 | dn | 50418 | 2850 | -0.1321 | [-0.1419, -0.1222] | 0.0000 | True | True |
| atr_pct_34|quintile/1 | up | 67716 | 2850 | -0.1576 | [-0.1708, -0.1443] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_24|quintile/1 | dn | 15174 | 2850 | -0.1414 | [-0.1538, -0.1289] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_24|quintile/1 | up | 20201 | 2850 | -0.1776 | [-0.1933, -0.1620] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_24|tercile/1 | dn | 23466 | 2850 | -0.1391 | [-0.1512, -0.1270] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_24|tercile/1 | up | 31260 | 2850 | -0.1738 | [-0.1895, -0.1582] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_24|tercile/3 | dn | 10182 | 2850 | -0.1193 | [-0.1314, -0.1072] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_24|tercile/3 | up | 14201 | 2850 | -0.1262 | [-0.1416, -0.1109] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_39|quintile/1 | dn | 15052 | 2850 | -0.1411 | [-0.1536, -0.1286] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_39|quintile/1 | up | 20084 | 2850 | -0.1774 | [-0.1930, -0.1618] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_39|tercile/1 | dn | 23420 | 2850 | -0.1392 | [-0.1513, -0.1271] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_39|tercile/1 | up | 31240 | 2850 | -0.1733 | [-0.1891, -0.1575] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_39|tercile/3 | dn | 10259 | 2850 | -0.1192 | [-0.1310, -0.1074] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_39|tercile/3 | up | 14244 | 2850 | -0.1252 | [-0.1406, -0.1098] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_3|quintile/1 | dn | 15425 | 2850 | -0.1413 | [-0.1529, -0.1296] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_3|quintile/1 | up | 20580 | 2850 | -0.1765 | [-0.1919, -0.1610] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_3|quintile/5 | dn | 5262 | 2702 | -0.1111 | [-0.1263, -0.0959] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_3|tercile/1 | dn | 23498 | 2850 | -0.1387 | [-0.1500, -0.1274] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_3|tercile/1 | up | 31368 | 2850 | -0.1716 | [-0.1867, -0.1565] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_3|tercile/3 | dn | 10317 | 2850 | -0.1215 | [-0.1336, -0.1094] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_3|tercile/3 | up | 14042 | 2850 | -0.1320 | [-0.1469, -0.1171] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_63|quintile/1 | dn | 14920 | 2850 | -0.1408 | [-0.1533, -0.1283] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_63|quintile/1 | up | 20096 | 2850 | -0.1758 | [-0.1913, -0.1603] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_6|quintile/1 | dn | 15383 | 2850 | -0.1415 | [-0.1534, -0.1296] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_6|quintile/1 | up | 20609 | 2850 | -0.1760 | [-0.1922, -0.1598] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_6|quintile/5 | dn | 5160 | 2683 | -0.1101 | [-0.1263, -0.0939] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_6|tercile/1 | dn | 23499 | 2850 | -0.1393 | [-0.1507, -0.1280] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_6|tercile/1 | up | 31451 | 2850 | -0.1723 | [-0.1877, -0.1568] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_6|tercile/3 | dn | 10283 | 2849 | -0.1194 | [-0.1322, -0.1067] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_6|tercile/3 | up | 14011 | 2849 | -0.1307 | [-0.1459, -0.1155] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_9|quintile/1 | dn | 15255 | 2850 | -0.1423 | [-0.1544, -0.1301] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_9|quintile/1 | up | 20520 | 2850 | -0.1761 | [-0.1921, -0.1600] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_9|tercile/1 | dn | 23494 | 2850 | -0.1393 | [-0.1508, -0.1277] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_9|tercile/1 | up | 31388 | 2850 | -0.1731 | [-0.1888, -0.1575] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_9|tercile/3 | dn | 10215 | 2849 | -0.1197 | [-0.1324, -0.1070] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_9|tercile/3 | up | 14080 | 2849 | -0.1275 | [-0.1428, -0.1122] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_144|quintile/1 | dn | 22817 | 2850 | -0.1448 | [-0.1567, -0.1330] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_144|quintile/1 | up | 31319 | 2850 | -0.1780 | [-0.1934, -0.1626] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_144|quintile/2 | dn | 13092 | 2850 | -0.1318 | [-0.1429, -0.1207] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_144|quintile/2 | up | 17925 | 2850 | -0.1500 | [-0.1657, -0.1342] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_144|tercile/1 | dn | 32192 | 2850 | -0.1416 | [-0.1526, -0.1307] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_144|tercile/1 | up | 43770 | 2850 | -0.1731 | [-0.1878, -0.1583] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_233|quintile/1 | dn | 22576 | 2850 | -0.1454 | [-0.1571, -0.1337] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_233|quintile/1 | up | 30812 | 2850 | -0.1808 | [-0.1961, -0.1654] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_233|quintile/2 | dn | 13012 | 2850 | -0.1306 | [-0.1417, -0.1195] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_233|quintile/2 | up | 17966 | 2850 | -0.1454 | [-0.1599, -0.1309] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_233|tercile/1 | dn | 31655 | 2850 | -0.1431 | [-0.1542, -0.1320] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_233|tercile/1 | up | 43883 | 2850 | -0.1710 | [-0.1852, -0.1567] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_3|quintile/1 | dn | 18589 | 2850 | -0.1411 | [-0.1511, -0.1311] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_3|quintile/1 | up | 24986 | 2850 | -0.1696 | [-0.1842, -0.1549] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_3|quintile/2 | dn | 14830 | 2850 | -0.1318 | [-0.1422, -0.1215] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_3|quintile/2 | up | 19896 | 2850 | -0.1567 | [-0.1701, -0.1433] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_3|tercile/1 | dn | 28922 | 2850 | -0.1384 | [-0.1484, -0.1284] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_3|tercile/1 | up | 38875 | 2850 | -0.1658 | [-0.1798, -0.1517] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_9|quintile/1 | dn | 23699 | 2850 | -0.1431 | [-0.1538, -0.1324] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_9|quintile/1 | up | 32216 | 2850 | -0.1709 | [-0.1854, -0.1564] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_9|quintile/2 | dn | 13981 | 2850 | -0.1254 | [-0.1357, -0.1151] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_9|quintile/2 | up | 18601 | 2850 | -0.1499 | [-0.1636, -0.1361] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_9|tercile/1 | dn | 33887 | 2850 | -0.1382 | [-0.1483, -0.1280] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_9|tercile/1 | up | 45649 | 2850 | -0.1658 | [-0.1800, -0.1516] | 0.0000 | True | True |
| atr_pct_34|quintile/2 | dn | 70710 | 2850 | -0.0639 | [-0.0724, -0.0555] | 0.0000 | True | True |
| atr_pct_34|quintile/2 | up | 95159 | 2850 | -0.0654 | [-0.0738, -0.0570] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_24|tercile/1 | dn | 29084 | 2850 | -0.0628 | [-0.0743, -0.0514] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_24|tercile/1 | up | 38418 | 2850 | -0.0672 | [-0.0772, -0.0571] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_39|tercile/1 | up | 38376 | 2850 | -0.0673 | [-0.0774, -0.0572] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_3|tercile/1 | up | 38428 | 2850 | -0.0681 | [-0.0779, -0.0583] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_6|tercile/1 | up | 38429 | 2850 | -0.0687 | [-0.0786, -0.0589] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_9|tercile/1 | up | 38380 | 2850 | -0.0690 | [-0.0788, -0.0592] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_144|quintile/1 | dn | 19291 | 2850 | -0.0880 | [-0.0994, -0.0766] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_144|quintile/1 | up | 26911 | 2850 | -0.0817 | [-0.0952, -0.0681] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_144|quintile/2 | dn | 19891 | 2850 | -0.0772 | [-0.0870, -0.0674] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_144|tercile/1 | dn | 33127 | 2850 | -0.0815 | [-0.0919, -0.0711] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_144|tercile/1 | up | 46846 | 2850 | -0.0758 | [-0.0874, -0.0643] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_233|quintile/1 | dn | 19152 | 2850 | -0.0889 | [-0.1006, -0.0772] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_233|quintile/1 | up | 26508 | 2850 | -0.0865 | [-0.1003, -0.0727] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_233|quintile/2 | dn | 20447 | 2850 | -0.0678 | [-0.0783, -0.0572] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_233|tercile/1 | dn | 32974 | 2850 | -0.0811 | [-0.0915, -0.0707] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_233|tercile/1 | up | 45526 | 2850 | -0.0820 | [-0.0942, -0.0699] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_3|tercile/1 | dn | 29980 | 2850 | -0.0660 | [-0.0749, -0.0571] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_3|tercile/1 | up | 39901 | 2850 | -0.0703 | [-0.0795, -0.0611] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_9|quintile/2 | dn | 20831 | 2850 | -0.0655 | [-0.0746, -0.0564] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_9|tercile/1 | dn | 33644 | 2850 | -0.0660 | [-0.0751, -0.0569] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_9|tercile/1 | up | 45136 | 2850 | -0.0683 | [-0.0783, -0.0583] | 0.0000 | True | True |
| atr_pct_34|quintile/4 | dn | 109226 | 2850 | +0.0670 | [+0.0599, +0.0742] | 0.0000 | True | True |
| atr_pct_34|quintile/4 | up | 138044 | 2850 | +0.0792 | [+0.0715, +0.0869] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_24|quintile/5 | up | 34674 | 2850 | +0.0949 | [+0.0832, +0.1066] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_24|tercile/3 | dn | 43350 | 2850 | +0.0651 | [+0.0548, +0.0753] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_24|tercile/3 | up | 56259 | 2850 | +0.0849 | [+0.0753, +0.0946] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_39|quintile/5 | up | 34846 | 2850 | +0.0951 | [+0.0833, +0.1069] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_39|tercile/3 | dn | 43257 | 2850 | +0.0643 | [+0.0542, +0.0744] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_39|tercile/3 | up | 56245 | 2850 | +0.0846 | [+0.0752, +0.0939] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_3|quintile/5 | up | 33929 | 2850 | +0.0907 | [+0.0793, +0.1021] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_3|tercile/3 | dn | 43032 | 2850 | +0.0650 | [+0.0555, +0.0746] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_3|tercile/3 | up | 55790 | 2850 | +0.0842 | [+0.0753, +0.0931] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_6|quintile/5 | up | 34149 | 2850 | +0.0915 | [+0.0799, +0.1030] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_6|tercile/3 | dn | 43092 | 2850 | +0.0646 | [+0.0550, +0.0742] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_6|tercile/3 | up | 55947 | 2850 | +0.0844 | [+0.0752, +0.0937] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_9|quintile/5 | up | 34253 | 2850 | +0.0927 | [+0.0809, +0.1046] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_9|tercile/3 | dn | 43095 | 2850 | +0.0642 | [+0.0545, +0.0740] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_9|tercile/3 | up | 56068 | 2850 | +0.0850 | [+0.0757, +0.0944] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_144|quintile/4 | dn | 34786 | 2850 | +0.0763 | [+0.0657, +0.0869] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_144|quintile/4 | up | 43220 | 2850 | +0.0776 | [+0.0661, +0.0891] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_144|quintile/5 | up | 35343 | 2850 | +0.1098 | [+0.0961, +0.1236] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_144|tercile/3 | dn | 51755 | 2850 | +0.0819 | [+0.0717, +0.0922] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_144|tercile/3 | up | 65236 | 2850 | +0.0968 | [+0.0864, +0.1072] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_233|quintile/4 | up | 45208 | 2850 | +0.0899 | [+0.0780, +0.1019] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_233|quintile/5 | dn | 27598 | 2850 | +0.0892 | [+0.0753, +0.1031] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_233|quintile/5 | up | 34510 | 2850 | +0.1059 | [+0.0929, +0.1189] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_233|tercile/3 | dn | 51514 | 2850 | +0.0768 | [+0.0670, +0.0865] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_233|tercile/3 | up | 66347 | 2850 | +0.1022 | [+0.0922, +0.1122] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_3|quintile/5 | up | 35482 | 2850 | +0.0843 | [+0.0755, +0.0930] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_3|tercile/3 | dn | 49216 | 2850 | +0.0736 | [+0.0660, +0.0813] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_3|tercile/3 | up | 61917 | 2850 | +0.0836 | [+0.0749, +0.0924] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_9|quintile/4 | dn | 33571 | 2850 | +0.0702 | [+0.0616, +0.0789] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_9|quintile/4 | up | 42414 | 2850 | +0.0822 | [+0.0726, +0.0918] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_9|tercile/3 | dn | 50195 | 2850 | +0.0737 | [+0.0660, +0.0814] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_9|tercile/3 | up | 62665 | 2850 | +0.0798 | [+0.0713, +0.0883] | 0.0000 | True | True |
| atr_pct_34|quintile/5 | dn | 128712 | 2850 | +0.1355 | [+0.1203, +0.1508] | 0.0000 | True | True |
| atr_pct_34|quintile/5 | up | 153612 | 2850 | +0.1359 | [+0.1207, +0.1511] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_24|quintile/5 | dn | 49158 | 2850 | +0.1343 | [+0.1163, +0.1524] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_24|quintile/5 | up | 59225 | 2850 | +0.1427 | [+0.1265, +0.1589] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_24|tercile/1 | dn | 23670 | 2843 | +0.1386 | [+0.1189, +0.1583] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_24|tercile/3 | dn | 69813 | 2850 | +0.1313 | [+0.1143, +0.1483] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_24|tercile/3 | up | 85110 | 2850 | +0.1456 | [+0.1302, +0.1609] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_39|quintile/5 | dn | 49121 | 2850 | +0.1356 | [+0.1174, +0.1538] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_39|quintile/5 | up | 59018 | 2850 | +0.1422 | [+0.1258, +0.1586] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_39|tercile/1 | dn | 23655 | 2846 | +0.1396 | [+0.1194, +0.1599] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_39|tercile/3 | dn | 69654 | 2850 | +0.1307 | [+0.1137, +0.1477] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_39|tercile/3 | up | 85245 | 2850 | +0.1458 | [+0.1304, +0.1613] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_3|quintile/5 | dn | 48418 | 2850 | +0.1343 | [+0.1167, +0.1519] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_3|quintile/5 | up | 58454 | 2850 | +0.1439 | [+0.1277, +0.1602] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_3|tercile/3 | dn | 68894 | 2850 | +0.1319 | [+0.1151, +0.1487] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_3|tercile/3 | up | 83816 | 2850 | +0.1445 | [+0.1294, +0.1596] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_6|quintile/5 | dn | 48845 | 2850 | +0.1343 | [+0.1167, +0.1518] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_6|quintile/5 | up | 58961 | 2850 | +0.1439 | [+0.1277, +0.1600] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_6|tercile/3 | dn | 69534 | 2850 | +0.1320 | [+0.1152, +0.1488] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_6|tercile/3 | up | 84537 | 2850 | +0.1448 | [+0.1296, +0.1599] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_9|quintile/5 | dn | 48862 | 2850 | +0.1340 | [+0.1163, +0.1518] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_9|quintile/5 | up | 59064 | 2850 | +0.1437 | [+0.1277, +0.1598] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_9|tercile/1 | dn | 23746 | 2846 | +0.1368 | [+0.1180, +0.1557] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_9|tercile/3 | dn | 69679 | 2850 | +0.1317 | [+0.1148, +0.1487] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_9|tercile/3 | up | 84818 | 2850 | +0.1451 | [+0.1298, +0.1604] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_144|quintile/4 | dn | 29768 | 2850 | +0.1267 | [+0.1108, +0.1427] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_144|quintile/4 | up | 35746 | 2850 | +0.1265 | [+0.1091, +0.1440] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_144|quintile/5 | dn | 78564 | 2850 | +0.1428 | [+0.1251, +0.1604] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_144|quintile/5 | up | 94614 | 2850 | +0.1477 | [+0.1309, +0.1644] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_144|tercile/3 | dn | 101129 | 2850 | +0.1393 | [+0.1229, +0.1556] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_144|tercile/3 | up | 121982 | 2850 | +0.1434 | [+0.1273, +0.1594] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_233|quintile/4 | dn | 27660 | 2850 | +0.1285 | [+0.1113, +0.1458] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_233|quintile/4 | up | 33272 | 2850 | +0.1226 | [+0.1051, +0.1402] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_233|quintile/5 | dn | 78248 | 2850 | +0.1428 | [+0.1252, +0.1605] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_233|quintile/5 | up | 94215 | 2850 | +0.1480 | [+0.1315, +0.1646] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_233|tercile/3 | dn | 99503 | 2850 | +0.1398 | [+0.1233, +0.1564] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_233|tercile/3 | up | 119581 | 2850 | +0.1422 | [+0.1261, +0.1583] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_3|quintile/5 | dn | 66840 | 2850 | +0.1429 | [+0.1270, +0.1588] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_3|quintile/5 | up | 78658 | 2850 | +0.1389 | [+0.1232, +0.1545] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_3|tercile/3 | dn | 87673 | 2850 | +0.1404 | [+0.1246, +0.1562] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_3|tercile/3 | up | 103481 | 2850 | +0.1379 | [+0.1224, +0.1533] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_9|quintile/4 | dn | 32263 | 2850 | +0.1303 | [+0.1149, +0.1457] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_9|quintile/4 | up | 39102 | 2850 | +0.1374 | [+0.1222, +0.1525] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_9|quintile/5 | dn | 74766 | 2850 | +0.1450 | [+0.1288, +0.1611] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_9|quintile/5 | up | 87220 | 2850 | +0.1357 | [+0.1198, +0.1516] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_9|tercile/3 | dn | 99027 | 2850 | +0.1415 | [+0.1257, +0.1574] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_9|tercile/3 | up | 116548 | 2850 | +0.1363 | [+0.1208, +0.1518] | 0.0000 | True | True |
| atr_pct_34|tercile/1 | dn | 96063 | 2850 | -0.1079 | [-0.1165, -0.0993] | 0.0000 | True | True |
| atr_pct_34|tercile/1 | up | 128773 | 2850 | -0.1253 | [-0.1359, -0.1147] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_24|quintile/1 | dn | 27179 | 2850 | -0.1159 | [-0.1269, -0.1048] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_24|quintile/1 | up | 36253 | 2850 | -0.1409 | [-0.1532, -0.1285] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_24|tercile/1 | dn | 42876 | 2850 | -0.1139 | [-0.1243, -0.1035] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_24|tercile/1 | up | 56694 | 2850 | -0.1396 | [-0.1517, -0.1274] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_24|tercile/3 | dn | 20344 | 2850 | -0.0940 | [-0.1051, -0.0828] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_24|tercile/3 | up | 28229 | 2850 | -0.0943 | [-0.1067, -0.0820] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_39|quintile/1 | dn | 27038 | 2850 | -0.1154 | [-0.1264, -0.1043] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_39|quintile/1 | up | 36122 | 2850 | -0.1408 | [-0.1533, -0.1283] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_39|tercile/1 | dn | 42832 | 2850 | -0.1138 | [-0.1243, -0.1032] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_39|tercile/1 | up | 56605 | 2850 | -0.1395 | [-0.1516, -0.1274] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_39|tercile/3 | dn | 20428 | 2850 | -0.0941 | [-0.1045, -0.0836] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_39|tercile/3 | up | 28125 | 2850 | -0.0944 | [-0.1068, -0.0820] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_3|quintile/1 | dn | 27283 | 2850 | -0.1161 | [-0.1267, -0.1055] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_3|quintile/1 | up | 36394 | 2850 | -0.1405 | [-0.1528, -0.1283] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_3|tercile/1 | dn | 42873 | 2850 | -0.1130 | [-0.1230, -0.1030] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_3|tercile/1 | up | 56751 | 2850 | -0.1382 | [-0.1500, -0.1264] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_3|tercile/3 | dn | 20637 | 2850 | -0.0956 | [-0.1065, -0.0847] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_3|tercile/3 | up | 28175 | 2850 | -0.0996 | [-0.1115, -0.0877] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_63|quintile/1 | dn | 26806 | 2850 | -0.1156 | [-0.1267, -0.1045] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_63|quintile/1 | up | 36109 | 2850 | -0.1398 | [-0.1526, -0.1270] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_6|quintile/1 | dn | 27302 | 2850 | -0.1164 | [-0.1270, -0.1057] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_6|quintile/1 | up | 36621 | 2850 | -0.1397 | [-0.1524, -0.1270] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_6|tercile/1 | dn | 42990 | 2850 | -0.1134 | [-0.1235, -0.1032] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_6|tercile/1 | up | 56869 | 2850 | -0.1389 | [-0.1508, -0.1271] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_6|tercile/3 | dn | 20538 | 2850 | -0.0942 | [-0.1052, -0.0832] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_6|tercile/3 | up | 28085 | 2850 | -0.0974 | [-0.1096, -0.0853] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_9|quintile/1 | dn | 27233 | 2850 | -0.1166 | [-0.1274, -0.1058] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_9|quintile/1 | up | 36518 | 2850 | -0.1398 | [-0.1525, -0.1271] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_9|tercile/1 | dn | 42997 | 2850 | -0.1135 | [-0.1239, -0.1031] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_9|tercile/1 | up | 56769 | 2850 | -0.1396 | [-0.1516, -0.1276] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_9|tercile/3 | dn | 20415 | 2850 | -0.0945 | [-0.1056, -0.0834] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_9|tercile/3 | up | 28064 | 2850 | -0.0962 | [-0.1083, -0.0841] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_144|quintile/1 | dn | 36347 | 2850 | -0.1295 | [-0.1406, -0.1185] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_144|quintile/1 | up | 50377 | 2850 | -0.1507 | [-0.1640, -0.1374] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_144|quintile/2 | dn | 25779 | 2850 | -0.1115 | [-0.1208, -0.1022] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_144|quintile/2 | up | 36496 | 2850 | -0.1194 | [-0.1320, -0.1069] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_144|tercile/1 | dn | 54622 | 2850 | -0.1235 | [-0.1335, -0.1136] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_144|tercile/1 | up | 75861 | 2850 | -0.1425 | [-0.1553, -0.1297] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_233|quintile/1 | dn | 36027 | 2850 | -0.1293 | [-0.1399, -0.1186] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_233|quintile/1 | up | 49771 | 2850 | -0.1534 | [-0.1671, -0.1398] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_233|quintile/2 | dn | 26195 | 2850 | -0.1074 | [-0.1172, -0.0975] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_233|quintile/2 | up | 35922 | 2850 | -0.1184 | [-0.1298, -0.1069] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_233|tercile/1 | dn | 54097 | 2850 | -0.1239 | [-0.1338, -0.1140] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_233|tercile/1 | up | 75157 | 2850 | -0.1433 | [-0.1559, -0.1307] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_3|quintile/1 | dn | 30456 | 2850 | -0.1203 | [-0.1293, -0.1113] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_3|quintile/1 | up | 40898 | 2850 | -0.1411 | [-0.1537, -0.1286] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_3|quintile/2 | dn | 27266 | 2850 | -0.1090 | [-0.1180, -0.1000] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_3|quintile/2 | up | 36384 | 2850 | -0.1272 | [-0.1378, -0.1167] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_3|tercile/1 | dn | 49177 | 2850 | -0.1166 | [-0.1256, -0.1077] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_3|tercile/1 | up | 65799 | 2850 | -0.1369 | [-0.1486, -0.1253] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_3|tercile/3 | dn | 11883 | 2844 | -0.0860 | [-0.0952, -0.0769] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_3|tercile/3 | up | 16102 | 2844 | -0.0953 | [-0.1055, -0.0852] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_9|quintile/1 | dn | 37349 | 2850 | -0.1234 | [-0.1327, -0.1141] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_9|quintile/1 | up | 50775 | 2850 | -0.1436 | [-0.1563, -0.1310] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_9|quintile/2 | dn | 27680 | 2850 | -0.1030 | [-0.1119, -0.0940] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_9|quintile/2 | up | 36770 | 2850 | -0.1199 | [-0.1306, -0.1093] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_9|quintile/4 | up | 12794 | 2845 | -0.0984 | [-0.1092, -0.0876] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_9|tercile/1 | dn | 56967 | 2850 | -0.1170 | [-0.1260, -0.1080] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_9|tercile/1 | up | 76692 | 2850 | -0.1369 | [-0.1485, -0.1253] | 0.0000 | True | True |
| atr_pct_34|tercile/3 | dn | 204354 | 2850 | +0.1137 | [+0.1030, +0.1243] | 0.0000 | True | True |
| atr_pct_34|tercile/3 | up | 247678 | 2850 | +0.1173 | [+0.1060, +0.1285] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_24|quintile/5 | dn | 67716 | 2850 | +0.1129 | [+0.0980, +0.1278] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_24|quintile/5 | up | 84199 | 2850 | +0.1316 | [+0.1185, +0.1447] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_24|tercile/1 | dn | 41944 | 2850 | +0.1089 | [+0.0933, +0.1245] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_24|tercile/1 | up | 49358 | 2850 | +0.1061 | [+0.0898, +0.1225] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_24|tercile/3 | dn | 101663 | 2850 | +0.1139 | [+0.1001, +0.1278] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_24|tercile/3 | up | 125342 | 2850 | +0.1282 | [+0.1160, +0.1405] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_39|quintile/5 | dn | 67684 | 2850 | +0.1134 | [+0.0984, +0.1283] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_39|quintile/5 | up | 84118 | 2850 | +0.1312 | [+0.1182, +0.1441] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_39|tercile/1 | dn | 41992 | 2850 | +0.1103 | [+0.0941, +0.1264] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_39|tercile/1 | up | 49364 | 2850 | +0.1063 | [+0.0896, +0.1229] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_39|tercile/3 | dn | 101395 | 2850 | +0.1133 | [+0.0997, +0.1268] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_39|tercile/3 | up | 125455 | 2850 | +0.1284 | [+0.1162, +0.1406] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_3|quintile/5 | dn | 66961 | 2850 | +0.1144 | [+0.1001, +0.1288] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_3|quintile/5 | up | 82888 | 2850 | +0.1309 | [+0.1179, +0.1440] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_3|tercile/1 | dn | 42423 | 2850 | +0.1089 | [+0.0942, +0.1236] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_3|tercile/1 | up | 49963 | 2850 | +0.1060 | [+0.0909, +0.1212] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_3|tercile/3 | dn | 100220 | 2850 | +0.1140 | [+0.1011, +0.1270] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_3|tercile/3 | up | 123629 | 2850 | +0.1277 | [+0.1154, +0.1399] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_6|quintile/5 | dn | 67407 | 2850 | +0.1138 | [+0.0994, +0.1281] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_6|quintile/5 | up | 83501 | 2850 | +0.1310 | [+0.1182, +0.1438] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_6|tercile/1 | dn | 42067 | 2850 | +0.1094 | [+0.0943, +0.1245] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_6|tercile/1 | up | 49374 | 2850 | +0.1043 | [+0.0886, +0.1201] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_6|tercile/3 | dn | 100966 | 2850 | +0.1140 | [+0.1008, +0.1271] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_6|tercile/3 | up | 124540 | 2850 | +0.1281 | [+0.1160, +0.1402] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_9|quintile/5 | dn | 67479 | 2850 | +0.1135 | [+0.0990, +0.1280] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_9|quintile/5 | up | 83721 | 2850 | +0.1312 | [+0.1180, +0.1445] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_9|tercile/1 | dn | 42062 | 2850 | +0.1101 | [+0.0946, +0.1255] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_9|tercile/1 | up | 49173 | 2850 | +0.1040 | [+0.0880, +0.1200] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_9|tercile/3 | dn | 101252 | 2850 | +0.1140 | [+0.1008, +0.1272] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_9|tercile/3 | up | 124841 | 2850 | +0.1283 | [+0.1162, +0.1403] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_144|quintile/4 | dn | 54663 | 2850 | +0.1092 | [+0.0973, +0.1211] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_144|quintile/4 | up | 66295 | 2850 | +0.1080 | [+0.0945, +0.1215] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_144|quintile/5 | dn | 100365 | 2850 | +0.1306 | [+0.1155, +0.1456] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_144|quintile/5 | up | 121950 | 2850 | +0.1395 | [+0.1247, +0.1542] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_144|tercile/3 | dn | 140351 | 2850 | +0.1247 | [+0.1112, +0.1382] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_144|tercile/3 | up | 170903 | 2850 | +0.1315 | [+0.1180, +0.1451] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_233|quintile/4 | dn | 52614 | 2850 | +0.1035 | [+0.0916, +0.1154] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_233|quintile/4 | up | 65030 | 2850 | +0.1105 | [+0.0976, +0.1235] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_233|quintile/5 | dn | 99944 | 2850 | +0.1319 | [+0.1165, +0.1473] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_233|quintile/5 | up | 121143 | 2850 | +0.1393 | [+0.1247, +0.1540] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_233|tercile/3 | dn | 138634 | 2850 | +0.1236 | [+0.1102, +0.1370] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_233|tercile/3 | up | 169124 | 2850 | +0.1316 | [+0.1184, +0.1449] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_3|quintile/2 | up | 25562 | 2850 | +0.1046 | [+0.0941, +0.1151] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_3|quintile/5 | dn | 88398 | 2850 | +0.1281 | [+0.1151, +0.1410] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_3|quintile/5 | up | 105219 | 2850 | +0.1266 | [+0.1133, +0.1399] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_3|tercile/1 | dn | 29362 | 2850 | +0.0933 | [+0.0827, +0.1039] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_3|tercile/1 | up | 36740 | 2850 | +0.1071 | [+0.0968, +0.1174] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_3|tercile/3 | dn | 123763 | 2850 | +0.1228 | [+0.1108, +0.1348] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_3|tercile/3 | up | 148350 | 2850 | +0.1236 | [+0.1110, +0.1361] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_9|quintile/4 | dn | 56150 | 2850 | +0.1100 | [+0.0987, +0.1213] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_9|quintile/4 | up | 68847 | 2850 | +0.1161 | [+0.1045, +0.1277] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_9|quintile/5 | dn | 95459 | 2850 | +0.1298 | [+0.1164, +0.1431] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_9|quintile/5 | up | 112878 | 2850 | +0.1239 | [+0.1108, +0.1371] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_9|tercile/3 | dn | 136251 | 2850 | +0.1243 | [+0.1121, +0.1366] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_9|tercile/3 | up | 162685 | 2850 | +0.1219 | [+0.1097, +0.1341] | 0.0000 | True | True |
| bb_width_144|quintile/1 | dn | 58825 | 2850 | -0.1017 | [-0.1115, -0.0919] | 0.0000 | True | True |
| bb_width_144|quintile/1 | up | 80309 | 2850 | -0.1121 | [-0.1228, -0.1014] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_24|quintile/1 | dn | 15125 | 2850 | -0.1172 | [-0.1307, -0.1037] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_24|quintile/1 | up | 20624 | 2850 | -0.1473 | [-0.1606, -0.1340] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_24|tercile/1 | dn | 24272 | 2850 | -0.1140 | [-0.1263, -0.1017] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_24|tercile/1 | up | 33600 | 2850 | -0.1367 | [-0.1495, -0.1240] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_24|tercile/3 | dn | 14013 | 2850 | -0.0786 | [-0.0911, -0.0660] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_39|quintile/1 | dn | 15087 | 2850 | -0.1164 | [-0.1298, -0.1030] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_39|quintile/1 | up | 20618 | 2850 | -0.1467 | [-0.1602, -0.1332] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_39|tercile/1 | dn | 24172 | 2850 | -0.1140 | [-0.1262, -0.1018] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_39|tercile/1 | up | 33640 | 2850 | -0.1357 | [-0.1484, -0.1230] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_39|tercile/3 | dn | 13987 | 2850 | -0.0788 | [-0.0918, -0.0658] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_3|quintile/1 | dn | 15010 | 2850 | -0.1192 | [-0.1323, -0.1061] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_3|quintile/1 | up | 20733 | 2850 | -0.1467 | [-0.1598, -0.1336] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_3|tercile/1 | dn | 24197 | 2850 | -0.1139 | [-0.1259, -0.1018] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_3|tercile/1 | up | 33313 | 2850 | -0.1369 | [-0.1493, -0.1244] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_3|tercile/3 | dn | 14228 | 2850 | -0.0811 | [-0.0932, -0.0690] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_63|quintile/1 | dn | 14976 | 2850 | -0.1165 | [-0.1300, -0.1031] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_63|quintile/1 | up | 20634 | 2850 | -0.1455 | [-0.1589, -0.1320] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_6|quintile/1 | dn | 15153 | 2850 | -0.1185 | [-0.1319, -0.1051] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_6|quintile/1 | up | 20873 | 2850 | -0.1461 | [-0.1593, -0.1328] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_6|tercile/1 | dn | 24244 | 2850 | -0.1145 | [-0.1267, -0.1023] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_6|tercile/1 | up | 33575 | 2850 | -0.1366 | [-0.1488, -0.1243] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_6|tercile/3 | dn | 14093 | 2850 | -0.0793 | [-0.0918, -0.0667] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_9|quintile/1 | dn | 15077 | 2850 | -0.1190 | [-0.1326, -0.1054] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_9|quintile/1 | up | 20807 | 2850 | -0.1460 | [-0.1593, -0.1328] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_9|tercile/1 | dn | 24229 | 2850 | -0.1145 | [-0.1267, -0.1024] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_9|tercile/1 | up | 33511 | 2850 | -0.1373 | [-0.1499, -0.1246] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_9|tercile/3 | dn | 14076 | 2850 | -0.0789 | [-0.0914, -0.0663] | 0.0000 | True | True |
| bb_width_144|quintile/1 & bb_width_233|quintile/1 | dn | 35626 | 2850 | -0.1158 | [-0.1270, -0.1045] | 0.0000 | True | True |
| bb_width_144|quintile/1 & bb_width_233|quintile/1 | up | 48351 | 2850 | -0.1351 | [-0.1477, -0.1225] | 0.0000 | True | True |
| bb_width_144|quintile/1 & bb_width_233|quintile/2 | dn | 13620 | 2850 | -0.0888 | [-0.1004, -0.0773] | 0.0000 | True | True |
| bb_width_144|quintile/1 & bb_width_233|tercile/1 | dn | 45599 | 2850 | -0.1112 | [-0.1218, -0.1007] | 0.0000 | True | True |
| bb_width_144|quintile/1 & bb_width_233|tercile/1 | up | 62540 | 2850 | -0.1254 | [-0.1375, -0.1134] | 0.0000 | True | True |
| bb_width_144|quintile/2 | dn | 73164 | 2850 | -0.0525 | [-0.0585, -0.0464] | 0.0000 | True | True |
| bb_width_144|quintile/2 | up | 100208 | 2850 | -0.0454 | [-0.0523, -0.0386] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_24|quintile/1 | dn | 14727 | 2850 | -0.0727 | [-0.0841, -0.0613] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_24|tercile/1 | dn | 24549 | 2850 | -0.0720 | [-0.0815, -0.0624] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_24|tercile/1 | up | 33565 | 2850 | -0.0740 | [-0.0855, -0.0626] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_39|quintile/1 | dn | 14772 | 2850 | -0.0723 | [-0.0838, -0.0607] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_39|tercile/1 | dn | 24548 | 2850 | -0.0715 | [-0.0811, -0.0619] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_39|tercile/1 | up | 33606 | 2850 | -0.0732 | [-0.0850, -0.0615] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_3|quintile/1 | dn | 14621 | 2850 | -0.0750 | [-0.0856, -0.0644] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_3|tercile/1 | dn | 24764 | 2850 | -0.0702 | [-0.0791, -0.0614] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_3|tercile/1 | up | 33531 | 2850 | -0.0741 | [-0.0851, -0.0631] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_63|quintile/1 | dn | 14831 | 2850 | -0.0725 | [-0.0843, -0.0607] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_6|quintile/1 | dn | 14663 | 2850 | -0.0742 | [-0.0853, -0.0630] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_6|tercile/1 | dn | 24776 | 2850 | -0.0706 | [-0.0799, -0.0612] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_6|tercile/1 | up | 33445 | 2850 | -0.0753 | [-0.0862, -0.0644] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_9|quintile/1 | dn | 14709 | 2850 | -0.0740 | [-0.0850, -0.0630] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_9|tercile/1 | dn | 24710 | 2850 | -0.0711 | [-0.0806, -0.0617] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_9|tercile/1 | up | 33425 | 2850 | -0.0753 | [-0.0863, -0.0644] | 0.0000 | True | True |
| bb_width_144|quintile/2 & bb_width_233|quintile/1 | dn | 19198 | 2850 | -0.0821 | [-0.0914, -0.0727] | 0.0000 | True | True |
| bb_width_144|quintile/2 & bb_width_233|quintile/1 | up | 25859 | 2850 | -0.0894 | [-0.1015, -0.0773] | 0.0000 | True | True |
| bb_width_144|quintile/2 & bb_width_233|quintile/2 | dn | 26884 | 2850 | -0.0545 | [-0.0630, -0.0459] | 0.0000 | True | True |
| bb_width_144|quintile/2 & bb_width_233|tercile/1 | dn | 38547 | 2850 | -0.0703 | [-0.0784, -0.0623] | 0.0000 | True | True |
| bb_width_144|quintile/2 & bb_width_233|tercile/1 | up | 53455 | 2850 | -0.0669 | [-0.0760, -0.0578] | 0.0000 | True | True |
| bb_width_144|quintile/4 | dn | 101424 | 2850 | +0.0443 | [+0.0382, +0.0504] | 0.0000 | True | True |
| bb_width_144|quintile/4 | up | 125421 | 2850 | +0.0419 | [+0.0356, +0.0481] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_24|tercile/3 | dn | 39751 | 2850 | +0.0650 | [+0.0551, +0.0750] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_24|tercile/3 | up | 49980 | 2850 | +0.0759 | [+0.0654, +0.0865] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_39|tercile/3 | dn | 39843 | 2850 | +0.0647 | [+0.0548, +0.0747] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_39|tercile/3 | up | 49889 | 2850 | +0.0747 | [+0.0643, +0.0850] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_3|tercile/3 | dn | 39455 | 2850 | +0.0646 | [+0.0553, +0.0740] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_3|tercile/3 | up | 49582 | 2850 | +0.0736 | [+0.0637, +0.0835] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_6|tercile/3 | dn | 39477 | 2850 | +0.0639 | [+0.0541, +0.0737] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_6|tercile/3 | up | 49913 | 2850 | +0.0761 | [+0.0660, +0.0863] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_9|tercile/3 | dn | 39573 | 2850 | +0.0643 | [+0.0542, +0.0744] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_9|tercile/3 | up | 49969 | 2850 | +0.0768 | [+0.0663, +0.0872] | 0.0000 | True | True |
| bb_width_144|quintile/4 & bb_width_233|tercile/3 | dn | 50567 | 2850 | +0.0641 | [+0.0538, +0.0744] | 0.0000 | True | True |
| bb_width_144|quintile/4 & bb_width_233|tercile/3 | up | 62638 | 2850 | +0.0687 | [+0.0578, +0.0796] | 0.0000 | True | True |
| bb_width_144|quintile/5 | dn | 119816 | 2850 | +0.1097 | [+0.0973, +0.1220] | 0.0000 | True | True |
| bb_width_144|quintile/5 | up | 147528 | 2850 | +0.1204 | [+0.1079, +0.1330] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_24|quintile/5 | dn | 38787 | 2850 | +0.1185 | [+0.1005, +0.1366] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_24|quintile/5 | up | 48438 | 2850 | +0.1412 | [+0.1255, +0.1569] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_24|tercile/3 | dn | 56878 | 2850 | +0.1170 | [+0.1011, +0.1329] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_24|tercile/3 | up | 70692 | 2850 | +0.1374 | [+0.1230, +0.1517] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_39|quintile/5 | dn | 38911 | 2850 | +0.1186 | [+0.1009, +0.1364] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_39|quintile/5 | up | 48680 | 2850 | +0.1412 | [+0.1253, +0.1571] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_39|tercile/3 | dn | 56886 | 2850 | +0.1159 | [+0.0997, +0.1320] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_39|tercile/3 | up | 71130 | 2850 | +0.1379 | [+0.1234, +0.1523] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_3|quintile/5 | dn | 38145 | 2850 | +0.1206 | [+0.1032, +0.1380] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_3|quintile/5 | up | 47275 | 2850 | +0.1400 | [+0.1247, +0.1552] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_3|tercile/3 | dn | 56074 | 2850 | +0.1179 | [+0.1024, +0.1334] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_3|tercile/3 | up | 69597 | 2850 | +0.1365 | [+0.1221, +0.1509] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_6|quintile/5 | dn | 38493 | 2850 | +0.1202 | [+0.1028, +0.1377] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_6|quintile/5 | up | 47768 | 2850 | +0.1407 | [+0.1254, +0.1560] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_6|tercile/3 | dn | 56611 | 2850 | +0.1187 | [+0.1030, +0.1345] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_6|tercile/3 | up | 70009 | 2850 | +0.1360 | [+0.1215, +0.1504] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_9|quintile/5 | dn | 38562 | 2850 | +0.1195 | [+0.1020, +0.1370] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_9|quintile/5 | up | 47963 | 2850 | +0.1410 | [+0.1257, +0.1564] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_9|tercile/3 | dn | 56700 | 2850 | +0.1182 | [+0.1024, +0.1341] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_9|tercile/3 | up | 70283 | 2850 | +0.1368 | [+0.1226, +0.1511] | 0.0000 | True | True |
| bb_width_144|quintile/5 & bb_width_233|quintile/5 | dn | 89299 | 2850 | +0.1217 | [+0.1072, +0.1363] | 0.0000 | True | True |
| bb_width_144|quintile/5 & bb_width_233|quintile/5 | up | 108967 | 2850 | +0.1317 | [+0.1182, +0.1453] | 0.0000 | True | True |
| bb_width_144|quintile/5 & bb_width_233|tercile/3 | dn | 111090 | 2850 | +0.1131 | [+0.1002, +0.1259] | 0.0000 | True | True |
| bb_width_144|quintile/5 & bb_width_233|tercile/3 | up | 136328 | 2850 | +0.1231 | [+0.1106, +0.1356] | 0.0000 | True | True |
| bb_width_144|tercile/1 | dn | 106632 | 2850 | -0.0839 | [-0.0917, -0.0761] | 0.0000 | True | True |
| bb_width_144|tercile/1 | up | 145305 | 2850 | -0.0889 | [-0.0973, -0.0805] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_24|quintile/1 | dn | 25070 | 2850 | -0.1029 | [-0.1147, -0.0910] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_24|quintile/1 | up | 34077 | 2850 | -0.1251 | [-0.1371, -0.1130] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_24|tercile/1 | dn | 40656 | 2850 | -0.1001 | [-0.1108, -0.0894] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_24|tercile/1 | up | 55720 | 2850 | -0.1174 | [-0.1283, -0.1064] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_24|tercile/3 | dn | 28523 | 2850 | -0.0563 | [-0.0651, -0.0475] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_39|quintile/1 | dn | 25064 | 2850 | -0.1017 | [-0.1134, -0.0900] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_39|quintile/1 | up | 34129 | 2850 | -0.1243 | [-0.1366, -0.1120] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_39|tercile/1 | dn | 40503 | 2850 | -0.0999 | [-0.1108, -0.0891] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_39|tercile/1 | up | 55757 | 2850 | -0.1166 | [-0.1276, -0.1056] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_39|tercile/3 | dn | 28485 | 2850 | -0.0565 | [-0.0655, -0.0476] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_3|quintile/1 | dn | 24887 | 2850 | -0.1050 | [-0.1164, -0.0937] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_3|quintile/1 | up | 34153 | 2850 | -0.1252 | [-0.1368, -0.1136] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_3|tercile/1 | dn | 40821 | 2850 | -0.0992 | [-0.1096, -0.0888] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_3|tercile/1 | up | 55486 | 2850 | -0.1172 | [-0.1281, -0.1064] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_3|tercile/3 | dn | 28831 | 2850 | -0.0580 | [-0.0665, -0.0494] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_63|quintile/1 | dn | 24961 | 2850 | -0.1020 | [-0.1140, -0.0899] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_63|quintile/1 | up | 34294 | 2850 | -0.1227 | [-0.1350, -0.1103] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_6|quintile/1 | dn | 25039 | 2850 | -0.1044 | [-0.1159, -0.0928] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_6|quintile/1 | up | 34348 | 2850 | -0.1247 | [-0.1367, -0.1127] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_6|tercile/1 | dn | 40829 | 2850 | -0.0999 | [-0.1104, -0.0894] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_6|tercile/1 | up | 55688 | 2850 | -0.1176 | [-0.1285, -0.1067] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_6|tercile/3 | dn | 28789 | 2850 | -0.0560 | [-0.0648, -0.0473] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_9|quintile/1 | dn | 25003 | 2850 | -0.1044 | [-0.1160, -0.0927] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_9|quintile/1 | up | 34245 | 2850 | -0.1247 | [-0.1364, -0.1129] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_9|tercile/1 | dn | 40751 | 2850 | -0.1001 | [-0.1106, -0.0897] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_9|tercile/1 | up | 55569 | 2850 | -0.1182 | [-0.1292, -0.1072] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_9|tercile/3 | dn | 28589 | 2850 | -0.0566 | [-0.0654, -0.0477] | 0.0000 | True | True |
| bb_width_144|tercile/1 & bb_width_233|quintile/1 | dn | 50823 | 2850 | -0.1066 | [-0.1165, -0.0966] | 0.0000 | True | True |
| bb_width_144|tercile/1 & bb_width_233|quintile/1 | up | 68790 | 2850 | -0.1230 | [-0.1343, -0.1118] | 0.0000 | True | True |
| bb_width_144|tercile/1 & bb_width_233|quintile/2 | dn | 30307 | 2850 | -0.0724 | [-0.0815, -0.0633] | 0.0000 | True | True |
| bb_width_144|tercile/1 & bb_width_233|quintile/2 | up | 42304 | 2850 | -0.0662 | [-0.0766, -0.0558] | 0.0000 | True | True |
| bb_width_144|tercile/1 & bb_width_233|tercile/1 | dn | 72852 | 2850 | -0.0982 | [-0.1072, -0.0893] | 0.0000 | True | True |
| bb_width_144|tercile/1 & bb_width_233|tercile/1 | up | 100018 | 2850 | -0.1082 | [-0.1185, -0.0980] | 0.0000 | True | True |
| bb_width_144|tercile/3 | dn | 188968 | 2850 | +0.0865 | [+0.0777, +0.0953] | 0.0000 | True | True |
| bb_width_144|tercile/3 | up | 233390 | 2850 | +0.0934 | [+0.0840, +0.1029] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_24|quintile/5 | dn | 55782 | 2850 | +0.1034 | [+0.0883, +0.1186] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_24|quintile/5 | up | 70248 | 2850 | +0.1246 | [+0.1118, +0.1374] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_24|tercile/3 | dn | 84761 | 2850 | +0.1010 | [+0.0877, +0.1144] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_24|tercile/3 | up | 105959 | 2850 | +0.1182 | [+0.1067, +0.1297] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_39|quintile/5 | dn | 56007 | 2850 | +0.1041 | [+0.0890, +0.1193] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_39|quintile/5 | up | 70555 | 2850 | +0.1246 | [+0.1119, +0.1374] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_39|tercile/3 | dn | 84929 | 2850 | +0.1006 | [+0.0875, +0.1137] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_39|tercile/3 | up | 106346 | 2850 | +0.1182 | [+0.1067, +0.1297] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_3|quintile/5 | dn | 55290 | 2850 | +0.1052 | [+0.0910, +0.1194] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_3|quintile/5 | up | 68957 | 2850 | +0.1222 | [+0.1094, +0.1350] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_3|tercile/3 | dn | 83701 | 2850 | +0.1012 | [+0.0885, +0.1138] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_3|tercile/3 | up | 104527 | 2850 | +0.1167 | [+0.1050, +0.1284] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_6|quintile/5 | dn | 55612 | 2850 | +0.1045 | [+0.0902, +0.1189] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_6|quintile/5 | up | 69582 | 2850 | +0.1231 | [+0.1102, +0.1360] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_6|tercile/3 | dn | 84287 | 2850 | +0.1015 | [+0.0886, +0.1144] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_6|tercile/3 | up | 105184 | 2850 | +0.1173 | [+0.1057, +0.1288] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_9|quintile/5 | dn | 55609 | 2850 | +0.1039 | [+0.0893, +0.1185] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_9|quintile/5 | up | 69838 | 2850 | +0.1238 | [+0.1110, +0.1366] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_9|tercile/3 | dn | 84454 | 2850 | +0.1014 | [+0.0884, +0.1145] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_9|tercile/3 | up | 105492 | 2850 | +0.1180 | [+0.1065, +0.1295] | 0.0000 | True | True |
| bb_width_144|tercile/3 & bb_width_233|quintile/4 | dn | 57738 | 2850 | +0.0642 | [+0.0556, +0.0728] | 0.0000 | True | True |
| bb_width_144|tercile/3 & bb_width_233|quintile/4 | up | 71356 | 2850 | +0.0653 | [+0.0549, +0.0757] | 0.0000 | True | True |
| bb_width_144|tercile/3 & bb_width_233|quintile/5 | dn | 106769 | 2850 | +0.1155 | [+0.1022, +0.1288] | 0.0000 | True | True |
| bb_width_144|tercile/3 & bb_width_233|quintile/5 | up | 130864 | 2850 | +0.1260 | [+0.1127, +0.1393] | 0.0000 | True | True |
| bb_width_144|tercile/3 & bb_width_233|tercile/3 | dn | 149977 | 2850 | +0.1003 | [+0.0896, +0.1110] | 0.0000 | True | True |
| bb_width_144|tercile/3 & bb_width_233|tercile/3 | up | 184318 | 2850 | +0.1088 | [+0.0975, +0.1200] | 0.0000 | True | True |
| bb_width_233|quintile/1 | dn | 57421 | 2850 | -0.1042 | [-0.1136, -0.0947] | 0.0000 | True | True |
| bb_width_233|quintile/1 | up | 77991 | 2850 | -0.1172 | [-0.1281, -0.1063] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_24|quintile/1 | dn | 14485 | 2850 | -0.1204 | [-0.1324, -0.1084] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_24|quintile/1 | up | 19642 | 2850 | -0.1511 | [-0.1652, -0.1370] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_24|tercile/1 | dn | 23308 | 2850 | -0.1190 | [-0.1303, -0.1076] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_24|tercile/1 | up | 32597 | 2850 | -0.1388 | [-0.1523, -0.1253] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_24|tercile/3 | dn | 13944 | 2850 | -0.0793 | [-0.0907, -0.0680] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_39|quintile/1 | dn | 14508 | 2850 | -0.1191 | [-0.1310, -0.1073] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_39|quintile/1 | up | 19659 | 2850 | -0.1514 | [-0.1660, -0.1368] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_39|tercile/1 | dn | 23253 | 2850 | -0.1188 | [-0.1301, -0.1075] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_39|tercile/1 | up | 32683 | 2850 | -0.1381 | [-0.1516, -0.1247] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_39|tercile/3 | dn | 13893 | 2850 | -0.0798 | [-0.0907, -0.0689] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_3|quintile/1 | dn | 14390 | 2850 | -0.1224 | [-0.1339, -0.1109] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_3|quintile/1 | up | 19724 | 2850 | -0.1507 | [-0.1646, -0.1368] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_3|tercile/1 | dn | 23230 | 2850 | -0.1176 | [-0.1288, -0.1063] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_3|tercile/1 | up | 32009 | 2850 | -0.1407 | [-0.1537, -0.1277] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_3|tercile/3 | dn | 14318 | 2850 | -0.0814 | [-0.0917, -0.0711] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_63|quintile/1 | dn | 14484 | 2850 | -0.1188 | [-0.1307, -0.1070] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_63|quintile/1 | up | 19725 | 2850 | -0.1507 | [-0.1652, -0.1362] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_6|quintile/1 | dn | 14465 | 2850 | -0.1222 | [-0.1339, -0.1104] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_6|quintile/1 | up | 19857 | 2850 | -0.1499 | [-0.1638, -0.1359] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_6|tercile/1 | dn | 23278 | 2850 | -0.1184 | [-0.1296, -0.1073] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_6|tercile/1 | up | 32372 | 2850 | -0.1402 | [-0.1533, -0.1271] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_6|tercile/3 | dn | 14225 | 2850 | -0.0794 | [-0.0904, -0.0684] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_9|quintile/1 | dn | 14391 | 2850 | -0.1225 | [-0.1344, -0.1107] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_9|quintile/1 | up | 19738 | 2850 | -0.1502 | [-0.1642, -0.1362] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_9|tercile/1 | dn | 23290 | 2850 | -0.1186 | [-0.1296, -0.1077] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_9|tercile/1 | up | 32393 | 2850 | -0.1403 | [-0.1536, -0.1269] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_9|tercile/3 | dn | 14138 | 2850 | -0.0795 | [-0.0904, -0.0686] | 0.0000 | True | True |
| bb_width_233|quintile/2 | dn | 73294 | 2850 | -0.0492 | [-0.0559, -0.0426] | 0.0000 | True | True |
| bb_width_233|quintile/2 | up | 98683 | 2850 | -0.0478 | [-0.0553, -0.0403] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_24|tercile/1 | dn | 25669 | 2850 | -0.0633 | [-0.0728, -0.0539] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_24|tercile/1 | up | 32896 | 2850 | -0.0749 | [-0.0845, -0.0653] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_39|tercile/1 | dn | 25787 | 2850 | -0.0624 | [-0.0718, -0.0529] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_39|tercile/1 | up | 32785 | 2850 | -0.0750 | [-0.0845, -0.0654] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_3|tercile/1 | dn | 25529 | 2850 | -0.0643 | [-0.0736, -0.0550] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_3|tercile/1 | up | 33083 | 2850 | -0.0726 | [-0.0820, -0.0633] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_6|tercile/1 | dn | 25520 | 2850 | -0.0645 | [-0.0738, -0.0551] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_6|tercile/1 | up | 33044 | 2850 | -0.0735 | [-0.0829, -0.0642] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_9|tercile/1 | dn | 25541 | 2850 | -0.0643 | [-0.0737, -0.0549] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_9|tercile/1 | up | 32874 | 2850 | -0.0747 | [-0.0842, -0.0652] | 0.0000 | True | True |
| bb_width_233|quintile/4 | dn | 98800 | 2850 | +0.0388 | [+0.0324, +0.0453] | 0.0000 | True | True |
| bb_width_233|quintile/4 | up | 126558 | 2850 | +0.0490 | [+0.0422, +0.0559] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_24|quintile/5 | up | 31680 | 2850 | +0.0936 | [+0.0804, +0.1068] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_24|tercile/3 | up | 50773 | 2850 | +0.0819 | [+0.0708, +0.0930] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_39|quintile/5 | up | 31584 | 2850 | +0.0931 | [+0.0802, +0.1059] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_39|tercile/3 | up | 51005 | 2850 | +0.0822 | [+0.0716, +0.0928] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_3|quintile/5 | up | 31347 | 2850 | +0.0919 | [+0.0790, +0.1048] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_3|tercile/3 | up | 50539 | 2850 | +0.0817 | [+0.0711, +0.0923] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_6|quintile/5 | up | 31476 | 2850 | +0.0927 | [+0.0797, +0.1056] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_6|tercile/3 | up | 50807 | 2850 | +0.0832 | [+0.0727, +0.0938] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_9|quintile/5 | up | 31513 | 2850 | +0.0934 | [+0.0800, +0.1069] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_9|tercile/3 | up | 50844 | 2850 | +0.0831 | [+0.0727, +0.0936] | 0.0000 | True | True |
| bb_width_233|quintile/5 | dn | 118765 | 2850 | +0.1101 | [+0.0972, +0.1231] | 0.0000 | True | True |
| bb_width_233|quintile/5 | up | 146108 | 2850 | +0.1205 | [+0.1083, +0.1327] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_24|quintile/5 | dn | 37276 | 2850 | +0.1188 | [+0.0994, +0.1381] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_24|quintile/5 | up | 46858 | 2850 | +0.1428 | [+0.1269, +0.1586] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_24|tercile/3 | dn | 55041 | 2850 | +0.1173 | [+0.1008, +0.1339] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_24|tercile/3 | up | 68609 | 2850 | +0.1390 | [+0.1250, +0.1529] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_39|quintile/5 | dn | 37498 | 2850 | +0.1190 | [+0.0999, +0.1381] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_39|quintile/5 | up | 47187 | 2850 | +0.1423 | [+0.1264, +0.1581] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_39|tercile/3 | dn | 55201 | 2850 | +0.1179 | [+0.1013, +0.1344] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_39|tercile/3 | up | 68793 | 2850 | +0.1382 | [+0.1243, +0.1520] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_3|quintile/5 | dn | 36615 | 2850 | +0.1214 | [+0.1026, +0.1401] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_3|quintile/5 | up | 45633 | 2850 | +0.1402 | [+0.1253, +0.1552] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_3|tercile/3 | dn | 54403 | 2850 | +0.1184 | [+0.1021, +0.1346] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_3|tercile/3 | up | 67701 | 2850 | +0.1369 | [+0.1231, +0.1506] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_6|quintile/5 | dn | 36953 | 2850 | +0.1205 | [+0.1019, +0.1391] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_6|quintile/5 | up | 46237 | 2850 | +0.1412 | [+0.1258, +0.1567] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_6|tercile/3 | dn | 54787 | 2850 | +0.1187 | [+0.1021, +0.1353] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_6|tercile/3 | up | 68107 | 2850 | +0.1372 | [+0.1234, +0.1510] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_9|quintile/5 | dn | 37083 | 2850 | +0.1202 | [+0.1012, +0.1392] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_9|quintile/5 | up | 46412 | 2850 | +0.1414 | [+0.1259, +0.1569] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_9|tercile/3 | dn | 54853 | 2850 | +0.1182 | [+0.1017, +0.1348] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_9|tercile/3 | up | 68289 | 2850 | +0.1380 | [+0.1241, +0.1519] | 0.0000 | True | True |
| bb_width_233|tercile/1 | dn | 104400 | 2850 | -0.0861 | [-0.0937, -0.0785] | 0.0000 | True | True |
| bb_width_233|tercile/1 | up | 142805 | 2850 | -0.0913 | [-0.1000, -0.0825] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_24|quintile/1 | dn | 24452 | 2850 | -0.1035 | [-0.1146, -0.0924] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_24|quintile/1 | up | 32789 | 2850 | -0.1264 | [-0.1387, -0.1142] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_24|tercile/1 | dn | 39962 | 2850 | -0.1019 | [-0.1118, -0.0921] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_24|tercile/1 | up | 54453 | 2850 | -0.1183 | [-0.1299, -0.1067] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_24|tercile/3 | dn | 27730 | 2850 | -0.0615 | [-0.0704, -0.0527] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_39|quintile/1 | dn | 24403 | 2850 | -0.1029 | [-0.1137, -0.0921] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_39|quintile/1 | up | 32747 | 2850 | -0.1264 | [-0.1386, -0.1143] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_39|tercile/1 | dn | 39982 | 2850 | -0.1013 | [-0.1110, -0.0916] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_39|tercile/1 | up | 54450 | 2850 | -0.1180 | [-0.1296, -0.1064] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_39|tercile/3 | dn | 27691 | 2850 | -0.0620 | [-0.0707, -0.0532] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_3|quintile/1 | dn | 24286 | 2850 | -0.1055 | [-0.1162, -0.0948] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_3|quintile/1 | up | 32848 | 2850 | -0.1263 | [-0.1382, -0.1143] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_3|tercile/1 | dn | 39891 | 2850 | -0.1010 | [-0.1108, -0.0912] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_3|tercile/1 | up | 53974 | 2850 | -0.1183 | [-0.1294, -0.1072] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_3|tercile/3 | dn | 28122 | 2850 | -0.0633 | [-0.0719, -0.0548] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_63|quintile/1 | dn | 24416 | 2850 | -0.1023 | [-0.1133, -0.0914] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_63|quintile/1 | up | 32857 | 2850 | -0.1253 | [-0.1374, -0.1132] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_6|quintile/1 | dn | 24391 | 2850 | -0.1052 | [-0.1159, -0.0944] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_6|quintile/1 | up | 32997 | 2850 | -0.1256 | [-0.1378, -0.1134] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_6|tercile/1 | dn | 39962 | 2850 | -0.1017 | [-0.1115, -0.0918] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_6|tercile/1 | up | 54196 | 2850 | -0.1189 | [-0.1302, -0.1076] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_6|tercile/3 | dn | 27959 | 2850 | -0.0616 | [-0.0704, -0.0528] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_9|quintile/1 | dn | 24383 | 2850 | -0.1049 | [-0.1158, -0.0939] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_9|quintile/1 | up | 32886 | 2850 | -0.1259 | [-0.1383, -0.1136] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_9|tercile/1 | dn | 39983 | 2850 | -0.1018 | [-0.1116, -0.0920] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_9|tercile/1 | up | 54120 | 2850 | -0.1194 | [-0.1308, -0.1080] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_9|tercile/3 | dn | 27795 | 2850 | -0.0618 | [-0.0705, -0.0532] | 0.0000 | True | True |
| bb_width_233|tercile/3 | dn | 186161 | 2850 | +0.0846 | [+0.0752, +0.0941] | 0.0000 | True | True |
| bb_width_233|tercile/3 | up | 232930 | 2850 | +0.0968 | [+0.0872, +0.1064] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_24|quintile/5 | dn | 53736 | 2850 | +0.0971 | [+0.0812, +0.1130] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_24|quintile/5 | up | 69674 | 2850 | +0.1310 | [+0.1181, +0.1439] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_24|tercile/3 | dn | 81764 | 2850 | +0.0959 | [+0.0819, +0.1098] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_24|tercile/3 | up | 104827 | 2850 | +0.1242 | [+0.1126, +0.1358] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_39|quintile/5 | dn | 53970 | 2850 | +0.0977 | [+0.0819, +0.1135] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_39|quintile/5 | up | 69901 | 2850 | +0.1304 | [+0.1178, +0.1430] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_39|tercile/3 | dn | 81908 | 2850 | +0.0959 | [+0.0819, +0.1099] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_39|tercile/3 | up | 105181 | 2850 | +0.1240 | [+0.1125, +0.1354] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_3|quintile/5 | dn | 52956 | 2850 | +0.0986 | [+0.0832, +0.1141] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_3|quintile/5 | up | 68167 | 2850 | +0.1292 | [+0.1165, +0.1419] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_3|tercile/3 | dn | 80897 | 2850 | +0.0966 | [+0.0832, +0.1100] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_3|tercile/3 | up | 103634 | 2850 | +0.1225 | [+0.1110, +0.1340] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_6|quintile/5 | dn | 53418 | 2850 | +0.0983 | [+0.0829, +0.1137] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_6|quintile/5 | up | 68911 | 2850 | +0.1302 | [+0.1175, +0.1429] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_6|tercile/3 | dn | 81447 | 2850 | +0.0969 | [+0.0836, +0.1102] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_6|tercile/3 | up | 104252 | 2850 | +0.1231 | [+0.1117, +0.1346] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_9|quintile/5 | dn | 53538 | 2850 | +0.0981 | [+0.0826, +0.1137] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_9|quintile/5 | up | 69114 | 2850 | +0.1304 | [+0.1176, +0.1432] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_9|tercile/3 | dn | 81535 | 2850 | +0.0963 | [+0.0829, +0.1098] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_9|tercile/3 | up | 104530 | 2850 | +0.1238 | [+0.1125, +0.1351] | 0.0000 | True | True |
| bb_width_3|quintile/1 | dn | 72541 | 2850 | -0.0589 | [-0.0640, -0.0538] | 0.0000 | True | True |
| bb_width_3|quintile/1 | up | 95393 | 2850 | -0.0656 | [-0.0720, -0.0592] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_24|quintile/1 | dn | 16002 | 2850 | -0.0891 | [-0.0989, -0.0792] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_24|quintile/1 | up | 21075 | 2850 | -0.1104 | [-0.1214, -0.0994] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_24|tercile/1 | dn | 26175 | 2850 | -0.0834 | [-0.0916, -0.0752] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_24|tercile/1 | up | 34413 | 2850 | -0.1021 | [-0.1118, -0.0923] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_39|quintile/1 | dn | 15743 | 2850 | -0.0878 | [-0.0978, -0.0779] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_39|quintile/1 | up | 20700 | 2850 | -0.1111 | [-0.1220, -0.1002] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_39|tercile/1 | dn | 25796 | 2850 | -0.0832 | [-0.0915, -0.0749] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_39|tercile/1 | up | 33853 | 2850 | -0.1027 | [-0.1125, -0.0928] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_3|quintile/1 | dn | 22758 | 2850 | -0.0774 | [-0.0858, -0.0691] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_3|quintile/1 | up | 29745 | 2850 | -0.0944 | [-0.1040, -0.0848] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_3|tercile/1 | dn | 34625 | 2850 | -0.0733 | [-0.0808, -0.0659] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_3|tercile/1 | up | 45351 | 2850 | -0.0884 | [-0.0971, -0.0797] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_63|quintile/1 | dn | 15474 | 2850 | -0.0880 | [-0.0981, -0.0780] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_63|quintile/1 | up | 20447 | 2850 | -0.1100 | [-0.1207, -0.0992] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_6|quintile/1 | dn | 18454 | 2850 | -0.0850 | [-0.0944, -0.0756] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_6|quintile/1 | up | 24297 | 2850 | -0.1036 | [-0.1144, -0.0927] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_6|tercile/1 | dn | 29361 | 2850 | -0.0794 | [-0.0874, -0.0714] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_6|tercile/1 | up | 38552 | 2850 | -0.0964 | [-0.1060, -0.0867] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_9|quintile/1 | dn | 17272 | 2850 | -0.0871 | [-0.0968, -0.0774] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_9|quintile/1 | up | 22818 | 2850 | -0.1063 | [-0.1173, -0.0954] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_9|tercile/1 | dn | 27917 | 2850 | -0.0812 | [-0.0893, -0.0731] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_9|tercile/1 | up | 36624 | 2850 | -0.0997 | [-0.1095, -0.0898] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_144|quintile/1 | dn | 16545 | 2850 | -0.1236 | [-0.1343, -0.1129] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_144|quintile/1 | up | 22705 | 2850 | -0.1452 | [-0.1579, -0.1326] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_144|quintile/2 | dn | 15862 | 2850 | -0.0794 | [-0.0875, -0.0714] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_144|quintile/2 | up | 21548 | 2850 | -0.0830 | [-0.0927, -0.0733] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_144|tercile/1 | dn | 27507 | 2850 | -0.1086 | [-0.1178, -0.0994] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_144|tercile/1 | up | 37197 | 2850 | -0.1267 | [-0.1377, -0.1156] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_233|quintile/1 | dn | 16329 | 2850 | -0.1256 | [-0.1361, -0.1150] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_233|quintile/1 | up | 22295 | 2850 | -0.1476 | [-0.1603, -0.1349] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_233|quintile/2 | dn | 15832 | 2850 | -0.0773 | [-0.0861, -0.0685] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_233|quintile/2 | up | 21701 | 2850 | -0.0793 | [-0.0888, -0.0698] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_233|tercile/1 | dn | 26967 | 2850 | -0.1112 | [-0.1202, -0.1022] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_233|tercile/1 | up | 37003 | 2850 | -0.1260 | [-0.1367, -0.1153] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_9|quintile/1 | dn | 24098 | 2850 | -0.1021 | [-0.1109, -0.0933] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_9|quintile/1 | up | 31846 | 2850 | -0.1211 | [-0.1326, -0.1096] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_9|tercile/1 | dn | 35393 | 2850 | -0.0915 | [-0.0993, -0.0838] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_9|tercile/1 | up | 46656 | 2850 | -0.1083 | [-0.1186, -0.0980] | 0.0000 | True | True |
| bb_width_3|quintile/2 | dn | 78353 | 2850 | -0.0385 | [-0.0424, -0.0346] | 0.0000 | True | True |
| bb_width_3|quintile/2 | up | 102000 | 2850 | -0.0428 | [-0.0473, -0.0383] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_24|quintile/1 | up | 20719 | 2850 | -0.0854 | [-0.0944, -0.0765] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_24|tercile/1 | dn | 26947 | 2850 | -0.0635 | [-0.0717, -0.0552] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_24|tercile/1 | up | 34901 | 2850 | -0.0771 | [-0.0849, -0.0693] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_39|quintile/1 | up | 20588 | 2850 | -0.0861 | [-0.0949, -0.0773] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_39|tercile/1 | dn | 26829 | 2850 | -0.0637 | [-0.0719, -0.0555] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_39|tercile/1 | up | 34818 | 2850 | -0.0770 | [-0.0847, -0.0693] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_3|quintile/1 | up | 21537 | 2850 | -0.0759 | [-0.0845, -0.0674] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_3|tercile/1 | up | 36547 | 2850 | -0.0685 | [-0.0753, -0.0616] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_63|quintile/1 | up | 20558 | 2850 | -0.0858 | [-0.0951, -0.0766] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_6|quintile/1 | up | 21364 | 2850 | -0.0801 | [-0.0889, -0.0712] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_6|tercile/1 | dn | 27667 | 2850 | -0.0606 | [-0.0687, -0.0526] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_6|tercile/1 | up | 35723 | 2850 | -0.0733 | [-0.0806, -0.0661] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_9|quintile/1 | up | 21113 | 2850 | -0.0823 | [-0.0912, -0.0734] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_9|tercile/1 | dn | 27415 | 2850 | -0.0617 | [-0.0700, -0.0535] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_9|tercile/1 | up | 35345 | 2850 | -0.0758 | [-0.0834, -0.0683] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_144|quintile/1 | dn | 15617 | 2850 | -0.1060 | [-0.1167, -0.0953] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_144|quintile/1 | up | 20915 | 2850 | -0.1215 | [-0.1327, -0.1102] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_144|quintile/2 | dn | 16643 | 2850 | -0.0669 | [-0.0736, -0.0602] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_144|tercile/1 | dn | 26706 | 2850 | -0.0923 | [-0.1009, -0.0837] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_144|tercile/1 | up | 36027 | 2850 | -0.1032 | [-0.1124, -0.0940] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_233|quintile/1 | dn | 15222 | 2850 | -0.1091 | [-0.1192, -0.0990] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_233|quintile/1 | up | 20714 | 2850 | -0.1246 | [-0.1360, -0.1133] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_233|tercile/1 | dn | 26236 | 2850 | -0.0949 | [-0.1033, -0.0865] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_233|tercile/1 | up | 35961 | 2850 | -0.1039 | [-0.1136, -0.0942] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_9|quintile/1 | dn | 20431 | 2850 | -0.0841 | [-0.0922, -0.0760] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_9|quintile/1 | up | 26707 | 2850 | -0.0985 | [-0.1086, -0.0884] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_9|tercile/1 | dn | 33288 | 2850 | -0.0739 | [-0.0808, -0.0669] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_9|tercile/1 | up | 43570 | 2850 | -0.0858 | [-0.0942, -0.0774] | 0.0000 | True | True |
| bb_width_3|quintile/5 | dn | 114661 | 2850 | +0.0862 | [+0.0776, +0.0949] | 0.0000 | True | True |
| bb_width_3|quintile/5 | up | 140151 | 2850 | +0.0878 | [+0.0788, +0.0968] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_24|quintile/5 | dn | 37323 | 2850 | +0.1071 | [+0.0927, +0.1215] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_24|quintile/5 | up | 46274 | 2850 | +0.1205 | [+0.1083, +0.1327] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_24|tercile/3 | dn | 55126 | 2850 | +0.1017 | [+0.0889, +0.1144] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_24|tercile/3 | up | 68408 | 2850 | +0.1144 | [+0.1035, +0.1254] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_39|quintile/5 | dn | 36946 | 2850 | +0.1083 | [+0.0938, +0.1228] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_39|quintile/5 | up | 45747 | 2850 | +0.1197 | [+0.1075, +0.1318] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_39|tercile/3 | dn | 54516 | 2850 | +0.1012 | [+0.0885, +0.1139] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_39|tercile/3 | up | 67882 | 2850 | +0.1148 | [+0.1039, +0.1258] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_3|quintile/5 | dn | 41632 | 2850 | +0.1032 | [+0.0896, +0.1169] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_3|quintile/5 | up | 51832 | 2850 | +0.1180 | [+0.1070, +0.1291] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_3|tercile/3 | dn | 60215 | 2850 | +0.0985 | [+0.0867, +0.1103] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_3|tercile/3 | up | 74702 | 2850 | +0.1099 | [+0.0994, +0.1205] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_6|quintile/5 | dn | 39219 | 2850 | +0.1051 | [+0.0911, +0.1191] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_6|quintile/5 | up | 48736 | 2850 | +0.1199 | [+0.1081, +0.1316] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_6|tercile/3 | dn | 57291 | 2850 | +0.1007 | [+0.0883, +0.1131] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_6|tercile/3 | up | 70958 | 2850 | +0.1130 | [+0.1022, +0.1237] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_9|quintile/5 | dn | 38326 | 2850 | +0.1055 | [+0.0914, +0.1196] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_9|quintile/5 | up | 47651 | 2850 | +0.1208 | [+0.1088, +0.1328] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_9|tercile/3 | dn | 56388 | 2850 | +0.1011 | [+0.0887, +0.1135] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_9|tercile/3 | up | 69873 | 2850 | +0.1138 | [+0.1028, +0.1247] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_144|quintile/4 | dn | 26561 | 2850 | +0.0877 | [+0.0781, +0.0973] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_144|quintile/5 | dn | 54584 | 2850 | +0.1335 | [+0.1177, +0.1492] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_144|quintile/5 | up | 65658 | 2850 | +0.1375 | [+0.1227, +0.1523] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_144|tercile/3 | dn | 73866 | 2850 | +0.1218 | [+0.1086, +0.1349] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_144|tercile/3 | up | 89239 | 2850 | +0.1253 | [+0.1119, +0.1388] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_233|quintile/5 | dn | 54320 | 2850 | +0.1339 | [+0.1181, +0.1497] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_233|quintile/5 | up | 65314 | 2850 | +0.1364 | [+0.1210, +0.1518] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_233|tercile/3 | dn | 72987 | 2850 | +0.1208 | [+0.1077, +0.1339] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_233|tercile/3 | up | 88571 | 2850 | +0.1251 | [+0.1120, +0.1382] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_9|quintile/5 | dn | 62718 | 2850 | +0.1191 | [+0.1063, +0.1320] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_9|quintile/5 | up | 74286 | 2850 | +0.1126 | [+0.1002, +0.1251] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_9|tercile/3 | dn | 86031 | 2850 | +0.1069 | [+0.0957, +0.1180] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_9|tercile/3 | up | 103291 | 2850 | +0.1047 | [+0.0935, +0.1160] | 0.0000 | True | True |
| bb_width_3|tercile/1 | dn | 124097 | 2850 | -0.0520 | [-0.0564, -0.0476] | 0.0000 | True | True |
| bb_width_3|tercile/1 | up | 162333 | 2850 | -0.0585 | [-0.0640, -0.0529] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_24|quintile/1 | dn | 26781 | 2850 | -0.0824 | [-0.0920, -0.0728] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_24|quintile/1 | up | 34960 | 2850 | -0.1031 | [-0.1130, -0.0933] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_24|tercile/1 | dn | 44090 | 2850 | -0.0772 | [-0.0853, -0.0691] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_24|tercile/1 | up | 57704 | 2850 | -0.0945 | [-0.1032, -0.0858] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_39|quintile/1 | dn | 26560 | 2850 | -0.0810 | [-0.0905, -0.0714] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_39|quintile/1 | up | 34489 | 2850 | -0.1037 | [-0.1134, -0.0940] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_39|tercile/1 | dn | 43609 | 2850 | -0.0771 | [-0.0852, -0.0690] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_39|tercile/1 | up | 57088 | 2850 | -0.0947 | [-0.1035, -0.0859] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_3|quintile/1 | dn | 34235 | 2850 | -0.0735 | [-0.0818, -0.0651] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_3|quintile/1 | up | 44557 | 2850 | -0.0901 | [-0.0988, -0.0813] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_3|tercile/1 | dn | 53905 | 2850 | -0.0685 | [-0.0758, -0.0613] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_3|tercile/1 | up | 70324 | 2850 | -0.0832 | [-0.0910, -0.0754] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_63|quintile/1 | dn | 26183 | 2850 | -0.0814 | [-0.0908, -0.0720] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_63|quintile/1 | up | 34213 | 2850 | -0.1026 | [-0.1121, -0.0931] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_6|quintile/1 | dn | 29540 | 2850 | -0.0797 | [-0.0888, -0.0706] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_6|quintile/1 | up | 38739 | 2850 | -0.0973 | [-0.1070, -0.0875] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_6|tercile/1 | dn | 47905 | 2850 | -0.0740 | [-0.0817, -0.0663] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_6|tercile/1 | up | 62676 | 2850 | -0.0896 | [-0.0981, -0.0811] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_9|quintile/1 | dn | 28245 | 2850 | -0.0814 | [-0.0907, -0.0720] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_9|quintile/1 | up | 37045 | 2850 | -0.0997 | [-0.1096, -0.0897] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_9|tercile/1 | dn | 46221 | 2850 | -0.0755 | [-0.0834, -0.0675] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_9|tercile/1 | up | 60383 | 2850 | -0.0926 | [-0.1014, -0.0837] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_144|quintile/1 | dn | 27213 | 2850 | -0.1174 | [-0.1280, -0.1068] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_144|quintile/1 | up | 36730 | 2850 | -0.1387 | [-0.1507, -0.1266] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_144|quintile/2 | dn | 26939 | 2850 | -0.0754 | [-0.0828, -0.0680] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_144|quintile/2 | up | 36874 | 2850 | -0.0765 | [-0.0855, -0.0676] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_144|tercile/1 | dn | 45576 | 2850 | -0.1031 | [-0.1120, -0.0943] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_144|tercile/1 | up | 61433 | 2850 | -0.1193 | [-0.1295, -0.1092] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_233|quintile/1 | dn | 26790 | 2850 | -0.1200 | [-0.1303, -0.1097] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_233|quintile/1 | up | 36391 | 2850 | -0.1404 | [-0.1523, -0.1285] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_233|quintile/2 | dn | 27133 | 2850 | -0.0717 | [-0.0793, -0.0642] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_233|quintile/2 | up | 36626 | 2850 | -0.0753 | [-0.0842, -0.0665] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_233|tercile/1 | dn | 44810 | 2850 | -0.1055 | [-0.1141, -0.0969] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_233|tercile/1 | up | 61185 | 2850 | -0.1192 | [-0.1296, -0.1088] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_9|quintile/1 | dn | 38154 | 2850 | -0.0972 | [-0.1057, -0.0888] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_9|quintile/1 | up | 50391 | 2850 | -0.1142 | [-0.1251, -0.1034] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_9|quintile/2 | dn | 28696 | 2850 | -0.0578 | [-0.0635, -0.0522] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_9|quintile/2 | up | 37762 | 2850 | -0.0652 | [-0.0721, -0.0582] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_9|tercile/1 | dn | 58037 | 2850 | -0.0860 | [-0.0934, -0.0786] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_9|tercile/1 | up | 76228 | 2850 | -0.1014 | [-0.1107, -0.0920] | 0.0000 | True | True |
| bb_width_3|tercile/3 | dn | 180636 | 2850 | +0.0641 | [+0.0580, +0.0702] | 0.0000 | True | True |
| bb_width_3|tercile/3 | up | 224560 | 2850 | +0.0683 | [+0.0616, +0.0750] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_24|quintile/5 | dn | 53315 | 2850 | +0.0902 | [+0.0776, +0.1029] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_24|quintile/5 | up | 67608 | 2850 | +0.1098 | [+0.0990, +0.1206] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_24|tercile/3 | dn | 81122 | 2850 | +0.0841 | [+0.0737, +0.0944] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_24|tercile/3 | up | 102563 | 2850 | +0.1012 | [+0.0920, +0.1104] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_39|quintile/5 | dn | 52869 | 2850 | +0.0913 | [+0.0786, +0.1040] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_39|quintile/5 | up | 66914 | 2850 | +0.1091 | [+0.0981, +0.1201] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_39|tercile/3 | dn | 80278 | 2850 | +0.0836 | [+0.0732, +0.0940] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_39|tercile/3 | up | 101763 | 2850 | +0.1012 | [+0.0920, +0.1105] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_3|quintile/5 | dn | 59071 | 2850 | +0.0854 | [+0.0737, +0.0971] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_3|quintile/5 | up | 75165 | 2850 | +0.1054 | [+0.0953, +0.1154] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_3|tercile/3 | dn | 88434 | 2850 | +0.0799 | [+0.0703, +0.0895] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_3|tercile/3 | up | 111785 | 2850 | +0.0952 | [+0.0865, +0.1039] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_6|quintile/5 | dn | 55798 | 2850 | +0.0879 | [+0.0760, +0.0998] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_6|quintile/5 | up | 70871 | 2850 | +0.1080 | [+0.0974, +0.1186] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_6|tercile/3 | dn | 84227 | 2850 | +0.0825 | [+0.0724, +0.0925] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_6|tercile/3 | up | 106346 | 2850 | +0.0986 | [+0.0895, +0.1076] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_9|quintile/5 | dn | 54636 | 2850 | +0.0887 | [+0.0765, +0.1009] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_9|quintile/5 | up | 69384 | 2850 | +0.1092 | [+0.0984, +0.1201] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_9|tercile/3 | dn | 82895 | 2850 | +0.0831 | [+0.0730, +0.0932] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_9|tercile/3 | up | 104698 | 2850 | +0.0998 | [+0.0907, +0.1089] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_144|quintile/4 | dn | 43833 | 2850 | +0.0767 | [+0.0689, +0.0846] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_144|quintile/4 | up | 53615 | 2850 | +0.0761 | [+0.0668, +0.0855] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_144|quintile/5 | dn | 73784 | 2850 | +0.1268 | [+0.1124, +0.1412] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_144|quintile/5 | up | 89402 | 2850 | +0.1331 | [+0.1192, +0.1470] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_144|tercile/3 | dn | 104870 | 2850 | +0.1125 | [+0.1010, +0.1239] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_144|tercile/3 | up | 127675 | 2850 | +0.1176 | [+0.1056, +0.1295] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_233|quintile/4 | dn | 42411 | 2850 | +0.0696 | [+0.0611, +0.0780] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_233|quintile/4 | up | 53750 | 2850 | +0.0813 | [+0.0717, +0.0909] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_233|quintile/5 | dn | 73506 | 2850 | +0.1275 | [+0.1129, +0.1420] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_233|quintile/5 | up | 88876 | 2850 | +0.1315 | [+0.1170, +0.1460] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_233|tercile/3 | dn | 103683 | 2850 | +0.1104 | [+0.0983, +0.1224] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_233|tercile/3 | up | 127373 | 2850 | +0.1182 | [+0.1064, +0.1299] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_9|quintile/4 | dn | 50160 | 2850 | +0.0623 | [+0.0558, +0.0688] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_9|quintile/4 | up | 63084 | 2850 | +0.0714 | [+0.0638, +0.0790] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_9|quintile/5 | dn | 79957 | 2850 | +0.1132 | [+0.1015, +0.1249] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_9|quintile/5 | up | 95123 | 2850 | +0.1074 | [+0.0957, +0.1191] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_9|tercile/3 | dn | 115769 | 2850 | +0.0980 | [+0.0881, +0.1080] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_9|tercile/3 | up | 139950 | 2850 | +0.0971 | [+0.0869, +0.1073] | 0.0000 | True | True |
| bb_width_9|quintile/1 | dn | 64400 | 2850 | -0.0862 | [-0.0938, -0.0787] | 0.0000 | True | True |
| bb_width_9|quintile/1 | up | 85154 | 2850 | -0.0994 | [-0.1090, -0.0898] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_24|quintile/1 | dn | 16056 | 2850 | -0.1073 | [-0.1188, -0.0959] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_24|quintile/1 | up | 21399 | 2850 | -0.1356 | [-0.1489, -0.1222] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_24|tercile/1 | dn | 25937 | 2850 | -0.1032 | [-0.1132, -0.0932] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_24|tercile/1 | up | 34390 | 2850 | -0.1273 | [-0.1398, -0.1147] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_39|quintile/1 | dn | 15831 | 2850 | -0.1060 | [-0.1175, -0.0945] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_39|quintile/1 | up | 20986 | 2850 | -0.1370 | [-0.1498, -0.1243] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_39|tercile/1 | dn | 25501 | 2850 | -0.1035 | [-0.1136, -0.0934] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_39|tercile/1 | up | 33945 | 2850 | -0.1276 | [-0.1401, -0.1151] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_3|quintile/1 | dn | 17163 | 2850 | -0.1055 | [-0.1161, -0.0948] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_3|quintile/1 | up | 23035 | 2850 | -0.1291 | [-0.1419, -0.1164] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_3|tercile/1 | dn | 27393 | 2850 | -0.0993 | [-0.1087, -0.0899] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_3|tercile/1 | up | 36322 | 2850 | -0.1219 | [-0.1340, -0.1097] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_63|quintile/1 | dn | 15590 | 2850 | -0.1060 | [-0.1177, -0.0944] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_63|quintile/1 | up | 20763 | 2850 | -0.1360 | [-0.1486, -0.1233] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_6|quintile/1 | dn | 17414 | 2850 | -0.1050 | [-0.1158, -0.0943] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_6|quintile/1 | up | 23381 | 2850 | -0.1290 | [-0.1421, -0.1160] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_6|tercile/1 | dn | 27701 | 2850 | -0.1001 | [-0.1098, -0.0904] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_6|tercile/1 | up | 36845 | 2850 | -0.1220 | [-0.1342, -0.1099] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_9|quintile/1 | dn | 17136 | 2850 | -0.1058 | [-0.1164, -0.0952] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_9|quintile/1 | up | 23028 | 2850 | -0.1301 | [-0.1432, -0.1170] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_9|tercile/1 | dn | 27476 | 2850 | -0.1003 | [-0.1102, -0.0905] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_9|tercile/1 | up | 36336 | 2850 | -0.1241 | [-0.1365, -0.1117] | 0.0000 | True | True |
| bb_width_9|quintile/1 & bb_width_144|quintile/1 | dn | 19849 | 2850 | -0.1285 | [-0.1394, -0.1176] | 0.0000 | True | True |
| bb_width_9|quintile/1 & bb_width_144|quintile/1 | up | 26995 | 2850 | -0.1530 | [-0.1668, -0.1393] | 0.0000 | True | True |
| bb_width_9|quintile/1 & bb_width_144|quintile/2 | dn | 16093 | 2850 | -0.0913 | [-0.1008, -0.0817] | 0.0000 | True | True |
| bb_width_9|quintile/1 & bb_width_144|quintile/2 | up | 22014 | 2850 | -0.0979 | [-0.1097, -0.0862] | 0.0000 | True | True |
| bb_width_9|quintile/1 & bb_width_144|tercile/1 | dn | 31095 | 2850 | -0.1168 | [-0.1265, -0.1072] | 0.0000 | True | True |
| bb_width_9|quintile/1 & bb_width_144|tercile/1 | up | 41979 | 2850 | -0.1382 | [-0.1506, -0.1257] | 0.0000 | True | True |
| bb_width_9|quintile/1 & bb_width_233|quintile/1 | dn | 19660 | 2850 | -0.1300 | [-0.1411, -0.1190] | 0.0000 | True | True |
| bb_width_9|quintile/1 & bb_width_233|quintile/1 | up | 26606 | 2850 | -0.1549 | [-0.1685, -0.1412] | 0.0000 | True | True |
| bb_width_9|quintile/1 & bb_width_233|quintile/2 | dn | 16272 | 2850 | -0.0897 | [-0.0992, -0.0803] | 0.0000 | True | True |
| bb_width_9|quintile/1 & bb_width_233|quintile/2 | up | 22186 | 2850 | -0.0969 | [-0.1081, -0.0858] | 0.0000 | True | True |
| bb_width_9|quintile/1 & bb_width_233|tercile/1 | dn | 30763 | 2850 | -0.1190 | [-0.1289, -0.1090] | 0.0000 | True | True |
| bb_width_9|quintile/1 & bb_width_233|tercile/1 | up | 41932 | 2850 | -0.1382 | [-0.1505, -0.1258] | 0.0000 | True | True |
| bb_width_9|quintile/2 | dn | 77556 | 2850 | -0.0411 | [-0.0459, -0.0363] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_24|tercile/1 | dn | 26841 | 2850 | -0.0606 | [-0.0687, -0.0526] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_24|tercile/1 | up | 35226 | 2850 | -0.0654 | [-0.0733, -0.0575] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_39|tercile/1 | dn | 26829 | 2850 | -0.0607 | [-0.0685, -0.0528] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_39|tercile/1 | up | 35135 | 2850 | -0.0656 | [-0.0734, -0.0577] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_3|tercile/1 | up | 34725 | 2850 | -0.0651 | [-0.0728, -0.0574] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_6|tercile/1 | dn | 26831 | 2850 | -0.0585 | [-0.0664, -0.0506] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_6|tercile/1 | up | 35120 | 2850 | -0.0644 | [-0.0725, -0.0564] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_9|tercile/1 | dn | 26868 | 2850 | -0.0589 | [-0.0669, -0.0509] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_9|tercile/1 | up | 35133 | 2850 | -0.0652 | [-0.0735, -0.0570] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_144|quintile/1 | dn | 16138 | 2850 | -0.0972 | [-0.1082, -0.0862] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_144|quintile/1 | up | 21479 | 2850 | -0.1101 | [-0.1215, -0.0987] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_144|quintile/2 | dn | 17819 | 2850 | -0.0645 | [-0.0720, -0.0571] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_144|tercile/1 | dn | 28034 | 2850 | -0.0847 | [-0.0937, -0.0757] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_144|tercile/1 | up | 37764 | 2850 | -0.0920 | [-0.1011, -0.0829] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_233|quintile/1 | dn | 15672 | 2850 | -0.1002 | [-0.1104, -0.0900] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_233|quintile/1 | up | 20954 | 2850 | -0.1140 | [-0.1260, -0.1020] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_233|tercile/1 | dn | 27371 | 2850 | -0.0879 | [-0.0963, -0.0795] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_233|tercile/1 | up | 37206 | 2850 | -0.0929 | [-0.1027, -0.0832] | 0.0000 | True | True |
| bb_width_9|quintile/4 | dn | 100779 | 2850 | +0.0378 | [+0.0339, +0.0417] | 0.0000 | True | True |
| bb_width_9|quintile/4 | up | 127936 | 2850 | +0.0444 | [+0.0391, +0.0496] | 0.0000 | True | True |
| bb_width_9|quintile/4 & amihud_24|quintile/5 | up | 32751 | 2850 | +0.0905 | [+0.0803, +0.1008] | 0.0000 | True | True |
| bb_width_9|quintile/4 & amihud_24|tercile/3 | up | 52781 | 2850 | +0.0790 | [+0.0704, +0.0876] | 0.0000 | True | True |
| bb_width_9|quintile/4 & amihud_39|quintile/5 | up | 32512 | 2850 | +0.0893 | [+0.0790, +0.0996] | 0.0000 | True | True |
| bb_width_9|quintile/4 & amihud_39|tercile/3 | up | 52413 | 2850 | +0.0791 | [+0.0706, +0.0877] | 0.0000 | True | True |
| bb_width_9|quintile/4 & amihud_3|quintile/5 | up | 33449 | 2850 | +0.0878 | [+0.0778, +0.0978] | 0.0000 | True | True |
| bb_width_9|quintile/4 & amihud_3|tercile/3 | up | 53494 | 2850 | +0.0781 | [+0.0697, +0.0864] | 0.0000 | True | True |
| bb_width_9|quintile/4 & amihud_6|quintile/5 | up | 33610 | 2850 | +0.0891 | [+0.0791, +0.0991] | 0.0000 | True | True |
| bb_width_9|quintile/4 & amihud_6|tercile/3 | up | 53780 | 2850 | +0.0782 | [+0.0698, +0.0865] | 0.0000 | True | True |
| bb_width_9|quintile/4 & amihud_9|quintile/5 | up | 33356 | 2850 | +0.0891 | [+0.0789, +0.0992] | 0.0000 | True | True |
| bb_width_9|quintile/4 & amihud_9|tercile/3 | up | 53717 | 2850 | +0.0783 | [+0.0701, +0.0866] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_144|quintile/5 | dn | 29191 | 2850 | +0.1048 | [+0.0915, +0.1182] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_144|quintile/5 | up | 37017 | 2850 | +0.1261 | [+0.1119, +0.1402] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_144|tercile/3 | dn | 48037 | 2850 | +0.0911 | [+0.0814, +0.1008] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_144|tercile/3 | up | 59963 | 2850 | +0.1043 | [+0.0934, +0.1152] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_233|quintile/5 | dn | 29636 | 2850 | +0.1071 | [+0.0941, +0.1201] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_233|quintile/5 | up | 36855 | 2850 | +0.1253 | [+0.1125, +0.1381] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_233|tercile/3 | dn | 48259 | 2850 | +0.0894 | [+0.0791, +0.0997] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_233|tercile/3 | up | 60784 | 2850 | +0.1054 | [+0.0948, +0.1159] | 0.0000 | True | True |
| bb_width_9|quintile/5 | dn | 117362 | 2850 | +0.0955 | [+0.0855, +0.1055] | 0.0000 | True | True |
| bb_width_9|quintile/5 | up | 141258 | 2850 | +0.0920 | [+0.0820, +0.1020] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_24|quintile/5 | dn | 39484 | 2850 | +0.1155 | [+0.1006, +0.1303] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_24|quintile/5 | up | 47950 | 2850 | +0.1225 | [+0.1091, +0.1359] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_24|tercile/3 | dn | 57656 | 2850 | +0.1102 | [+0.0965, +0.1240] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_24|tercile/3 | up | 70081 | 2850 | +0.1175 | [+0.1053, +0.1297] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_39|quintile/5 | dn | 39262 | 2850 | +0.1166 | [+0.1015, +0.1318] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_39|quintile/5 | up | 47527 | 2850 | +0.1216 | [+0.1083, +0.1348] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_39|tercile/3 | dn | 57179 | 2850 | +0.1096 | [+0.0960, +0.1231] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_39|tercile/3 | up | 69757 | 2850 | +0.1175 | [+0.1055, +0.1295] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_3|quintile/5 | dn | 38672 | 2850 | +0.1159 | [+0.1012, +0.1305] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_3|quintile/5 | up | 47097 | 2850 | +0.1249 | [+0.1120, +0.1378] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_3|tercile/3 | dn | 56339 | 2850 | +0.1111 | [+0.0983, +0.1240] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_3|tercile/3 | up | 68518 | 2850 | +0.1182 | [+0.1060, +0.1303] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_6|quintile/5 | dn | 39704 | 2850 | +0.1142 | [+0.0995, +0.1288] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_6|quintile/5 | up | 48407 | 2850 | +0.1243 | [+0.1110, +0.1375] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_6|tercile/3 | dn | 57868 | 2850 | +0.1112 | [+0.0979, +0.1244] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_6|tercile/3 | up | 70126 | 2850 | +0.1170 | [+0.1051, +0.1289] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_9|quintile/5 | dn | 39934 | 2850 | +0.1146 | [+0.0999, +0.1292] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_9|quintile/5 | up | 48622 | 2850 | +0.1236 | [+0.1102, +0.1371] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_9|tercile/3 | dn | 58097 | 2850 | +0.1109 | [+0.0974, +0.1243] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_9|tercile/3 | up | 70506 | 2850 | +0.1177 | [+0.1056, +0.1299] | 0.0000 | True | True |
| bb_width_9|quintile/5 & bb_width_144|quintile/4 | dn | 26874 | 2850 | +0.0921 | [+0.0810, +0.1032] | 0.0000 | True | True |
| bb_width_9|quintile/5 & bb_width_144|quintile/5 | dn | 60395 | 2850 | +0.1379 | [+0.1217, +0.1541] | 0.0000 | True | True |
| bb_width_9|quintile/5 & bb_width_144|quintile/5 | up | 71267 | 2850 | +0.1344 | [+0.1191, +0.1498] | 0.0000 | True | True |
| bb_width_9|quintile/5 & bb_width_144|tercile/3 | dn | 80052 | 2850 | +0.1269 | [+0.1123, +0.1414] | 0.0000 | True | True |
| bb_width_9|quintile/5 & bb_width_144|tercile/3 | up | 95116 | 2850 | +0.1241 | [+0.1103, +0.1380] | 0.0000 | True | True |
| bb_width_9|quintile/5 & bb_width_233|quintile/5 | dn | 59889 | 2850 | +0.1377 | [+0.1212, +0.1543] | 0.0000 | True | True |
| bb_width_9|quintile/5 & bb_width_233|quintile/5 | up | 71247 | 2850 | +0.1343 | [+0.1190, +0.1497] | 0.0000 | True | True |
| bb_width_9|quintile/5 & bb_width_233|tercile/3 | dn | 78624 | 2850 | +0.1258 | [+0.1115, +0.1401] | 0.0000 | True | True |
| bb_width_9|quintile/5 & bb_width_233|tercile/3 | up | 93802 | 2850 | +0.1235 | [+0.1102, +0.1369] | 0.0000 | True | True |
| bb_width_9|tercile/1 | dn | 115131 | 2850 | -0.0701 | [-0.0763, -0.0639] | 0.0000 | True | True |
| bb_width_9|tercile/1 | up | 151931 | 2850 | -0.0791 | [-0.0868, -0.0714] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_24|quintile/1 | dn | 27058 | 2850 | -0.0926 | [-0.1029, -0.0822] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_24|quintile/1 | up | 35303 | 2850 | -0.1163 | [-0.1273, -0.1053] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_24|tercile/1 | dn | 44033 | 2850 | -0.0890 | [-0.0980, -0.0800] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_24|tercile/1 | up | 57956 | 2850 | -0.1076 | [-0.1183, -0.0969] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_39|quintile/1 | dn | 26846 | 2850 | -0.0913 | [-0.1018, -0.0807] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_39|quintile/1 | up | 34813 | 2850 | -0.1175 | [-0.1283, -0.1067] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_39|tercile/1 | dn | 43580 | 2850 | -0.0891 | [-0.0983, -0.0798] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_39|tercile/1 | up | 57355 | 2850 | -0.1081 | [-0.1188, -0.0975] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_3|quintile/1 | dn | 27828 | 2850 | -0.0927 | [-0.1024, -0.0830] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_3|quintile/1 | up | 36706 | 2850 | -0.1128 | [-0.1238, -0.1018] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_3|tercile/1 | dn | 45367 | 2850 | -0.0861 | [-0.0946, -0.0776] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_3|tercile/1 | up | 59625 | 2850 | -0.1045 | [-0.1146, -0.0943] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_63|quintile/1 | dn | 26560 | 2850 | -0.0913 | [-0.1018, -0.0808] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_63|quintile/1 | up | 34563 | 2850 | -0.1166 | [-0.1276, -0.1057] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_6|quintile/1 | dn | 28293 | 2850 | -0.0922 | [-0.1022, -0.0823] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_6|quintile/1 | up | 37312 | 2850 | -0.1120 | [-0.1230, -0.1009] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_6|tercile/1 | dn | 45875 | 2850 | -0.0868 | [-0.0954, -0.0783] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_6|tercile/1 | up | 60465 | 2850 | -0.1042 | [-0.1144, -0.0941] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_9|quintile/1 | dn | 28083 | 2850 | -0.0924 | [-0.1022, -0.0825] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_9|quintile/1 | up | 37027 | 2850 | -0.1126 | [-0.1238, -0.1014] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_9|tercile/1 | dn | 45647 | 2850 | -0.0870 | [-0.0957, -0.0782] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_9|tercile/1 | up | 59908 | 2850 | -0.1060 | [-0.1164, -0.0956] | 0.0000 | True | True |
| bb_width_9|tercile/1 & bb_width_144|quintile/1 | dn | 31107 | 2850 | -0.1189 | [-0.1296, -0.1082] | 0.0000 | True | True |
| bb_width_9|tercile/1 & bb_width_144|quintile/1 | up | 41919 | 2850 | -0.1403 | [-0.1530, -0.1276] | 0.0000 | True | True |
| bb_width_9|tercile/1 & bb_width_144|quintile/2 | dn | 28004 | 2850 | -0.0812 | [-0.0892, -0.0733] | 0.0000 | True | True |
| bb_width_9|tercile/1 & bb_width_144|quintile/2 | up | 38158 | 2850 | -0.0849 | [-0.0950, -0.0749] | 0.0000 | True | True |
| bb_width_9|tercile/1 & bb_width_144|tercile/1 | dn | 50304 | 2850 | -0.1064 | [-0.1156, -0.0973] | 0.0000 | True | True |
| bb_width_9|tercile/1 & bb_width_144|tercile/1 | up | 67637 | 2850 | -0.1242 | [-0.1352, -0.1132] | 0.0000 | True | True |
| bb_width_9|tercile/1 & bb_width_233|quintile/1 | dn | 30595 | 2850 | -0.1209 | [-0.1314, -0.1104] | 0.0000 | True | True |
| bb_width_9|tercile/1 & bb_width_233|quintile/1 | up | 41037 | 2850 | -0.1437 | [-0.1565, -0.1309] | 0.0000 | True | True |
| bb_width_9|tercile/1 & bb_width_233|quintile/2 | dn | 28316 | 2850 | -0.0794 | [-0.0880, -0.0708] | 0.0000 | True | True |
| bb_width_9|tercile/1 & bb_width_233|quintile/2 | up | 38499 | 2850 | -0.0830 | [-0.0927, -0.0734] | 0.0000 | True | True |
| bb_width_9|tercile/1 & bb_width_233|tercile/1 | dn | 49568 | 2850 | -0.1090 | [-0.1180, -0.1000] | 0.0000 | True | True |
| bb_width_9|tercile/1 & bb_width_233|tercile/1 | up | 67291 | 2850 | -0.1245 | [-0.1357, -0.1132] | 0.0000 | True | True |
| bb_width_9|tercile/3 | dn | 186081 | 2850 | +0.0754 | [+0.0680, +0.0827] | 0.0000 | True | True |
| bb_width_9|tercile/3 | up | 228086 | 2850 | +0.0759 | [+0.0680, +0.0837] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_24|quintile/5 | dn | 57084 | 2850 | +0.1002 | [+0.0869, +0.1135] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_24|quintile/5 | up | 70936 | 2850 | +0.1136 | [+0.1021, +0.1252] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_24|tercile/3 | dn | 86091 | 2850 | +0.0940 | [+0.0824, +0.1055] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_24|tercile/3 | up | 106911 | 2850 | +0.1063 | [+0.0960, +0.1166] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_39|quintile/5 | dn | 56809 | 2850 | +0.1014 | [+0.0880, +0.1147] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_39|quintile/5 | up | 70333 | 2850 | +0.1124 | [+0.1007, +0.1240] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_39|tercile/3 | dn | 85331 | 2850 | +0.0932 | [+0.0817, +0.1046] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_39|tercile/3 | up | 106358 | 2850 | +0.1064 | [+0.0963, +0.1165] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_3|quintile/5 | dn | 56742 | 2850 | +0.1002 | [+0.0875, +0.1130] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_3|quintile/5 | up | 70489 | 2850 | +0.1139 | [+0.1029, +0.1250] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_3|tercile/3 | dn | 85152 | 2850 | +0.0941 | [+0.0832, +0.1050] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_3|tercile/3 | up | 105772 | 2850 | +0.1060 | [+0.0958, +0.1163] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_6|quintile/5 | dn | 57754 | 2850 | +0.0988 | [+0.0859, +0.1118] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_6|quintile/5 | up | 71978 | 2850 | +0.1142 | [+0.1031, +0.1252] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_6|tercile/3 | dn | 86808 | 2850 | +0.0941 | [+0.0829, +0.1054] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_6|tercile/3 | up | 107674 | 2850 | +0.1056 | [+0.0955, +0.1156] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_9|quintile/5 | dn | 57911 | 2850 | +0.0994 | [+0.0867, +0.1122] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_9|quintile/5 | up | 72012 | 2850 | +0.1137 | [+0.1025, +0.1249] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_9|tercile/3 | dn | 87041 | 2850 | +0.0941 | [+0.0830, +0.1052] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_9|tercile/3 | up | 107991 | 2850 | +0.1060 | [+0.0956, +0.1163] | 0.0000 | True | True |
| bb_width_9|tercile/3 & bb_width_144|quintile/4 | dn | 45648 | 2850 | +0.0833 | [+0.0740, +0.0926] | 0.0000 | True | True |
| bb_width_9|tercile/3 & bb_width_144|quintile/4 | up | 55104 | 2850 | +0.0801 | [+0.0695, +0.0907] | 0.0000 | True | True |
| bb_width_9|tercile/3 & bb_width_144|quintile/5 | dn | 81839 | 2850 | +0.1298 | [+0.1144, +0.1452] | 0.0000 | True | True |
| bb_width_9|tercile/3 & bb_width_144|quintile/5 | up | 98254 | 2850 | +0.1326 | [+0.1181, +0.1472] | 0.0000 | True | True |
| bb_width_9|tercile/3 & bb_width_144|tercile/3 | dn | 114530 | 2850 | +0.1170 | [+0.1044, +0.1296] | 0.0000 | True | True |
| bb_width_9|tercile/3 & bb_width_144|tercile/3 | up | 137905 | 2850 | +0.1189 | [+0.1065, +0.1314] | 0.0000 | True | True |
| bb_width_9|tercile/3 & bb_width_233|quintile/4 | dn | 43654 | 2850 | +0.0760 | [+0.0666, +0.0854] | 0.0000 | True | True |
| bb_width_9|tercile/3 & bb_width_233|quintile/4 | up | 54069 | 2850 | +0.0805 | [+0.0701, +0.0909] | 0.0000 | True | True |
| bb_width_9|tercile/3 & bb_width_233|quintile/5 | dn | 81683 | 2850 | +0.1304 | [+0.1149, +0.1459] | 0.0000 | True | True |
| bb_width_9|tercile/3 & bb_width_233|quintile/5 | up | 98170 | 2850 | +0.1321 | [+0.1176, +0.1466] | 0.0000 | True | True |
| bb_width_9|tercile/3 & bb_width_233|tercile/3 | dn | 113154 | 2850 | +0.1153 | [+0.1024, +0.1282] | 0.0000 | True | True |
| bb_width_9|tercile/3 & bb_width_233|tercile/3 | up | 137122 | 2850 | +0.1187 | [+0.1063, +0.1311] | 0.0000 | True | True |
| range_width_144|quintile/1 | dn | 53878 | 2850 | -0.1185 | [-0.1287, -0.1084] | 0.0000 | True | True |
| range_width_144|quintile/1 | up | 75112 | 2850 | -0.1298 | [-0.1416, -0.1179] | 0.0000 | True | True |
| range_width_144|quintile/2 | dn | 71928 | 2850 | -0.0568 | [-0.0640, -0.0497] | 0.0000 | True | True |
| range_width_144|quintile/2 | up | 96114 | 2850 | -0.0595 | [-0.0673, -0.0517] | 0.0000 | True | True |
| range_width_144|quintile/4 | dn | 104138 | 2850 | +0.0537 | [+0.0472, +0.0602] | 0.0000 | True | True |
| range_width_144|quintile/4 | up | 130287 | 2850 | +0.0580 | [+0.0504, +0.0656] | 0.0000 | True | True |
| range_width_144|quintile/5 | dn | 123667 | 2850 | +0.1233 | [+0.1094, +0.1371] | 0.0000 | True | True |
| range_width_144|quintile/5 | up | 150802 | 2850 | +0.1318 | [+0.1178, +0.1458] | 0.0000 | True | True |
| range_width_144|tercile/1 | dn | 100200 | 2850 | -0.0970 | [-0.1054, -0.0886] | 0.0000 | True | True |
| range_width_144|tercile/1 | up | 137793 | 2850 | -0.1045 | [-0.1141, -0.0948] | 0.0000 | True | True |
| range_width_144|tercile/3 | dn | 195203 | 2850 | +0.0996 | [+0.0895, +0.1097] | 0.0000 | True | True |
| range_width_144|tercile/3 | up | 240779 | 2850 | +0.1086 | [+0.0986, +0.1186] | 0.0000 | True | True |
| range_width_233|quintile/1 | dn | 53216 | 2850 | -0.1186 | [-0.1281, -0.1090] | 0.0000 | True | True |
| range_width_233|quintile/1 | up | 71933 | 2850 | -0.1380 | [-0.1500, -0.1261] | 0.0000 | True | True |
| range_width_233|quintile/2 | dn | 71081 | 2850 | -0.0577 | [-0.0657, -0.0498] | 0.0000 | True | True |
| range_width_233|quintile/2 | up | 93971 | 2850 | -0.0638 | [-0.0722, -0.0554] | 0.0000 | True | True |
| range_width_233|quintile/4 | dn | 102832 | 2850 | +0.0527 | [+0.0450, +0.0604] | 0.0000 | True | True |
| range_width_233|quintile/4 | up | 131222 | 2850 | +0.0653 | [+0.0574, +0.0733] | 0.0000 | True | True |
| range_width_233|quintile/5 | dn | 122885 | 2850 | +0.1250 | [+0.1109, +0.1390] | 0.0000 | True | True |
| range_width_233|quintile/5 | up | 148878 | 2850 | +0.1304 | [+0.1167, +0.1442] | 0.0000 | True | True |
| range_width_233|tercile/1 | dn | 98514 | 2850 | -0.0986 | [-0.1068, -0.0904] | 0.0000 | True | True |
| range_width_233|tercile/1 | up | 133372 | 2850 | -0.1107 | [-0.1201, -0.1012] | 0.0000 | True | True |
| range_width_233|tercile/3 | dn | 192773 | 2850 | +0.0988 | [+0.0881, +0.1094] | 0.0000 | True | True |
| range_width_233|tercile/3 | up | 239411 | 2850 | +0.1105 | [+0.1000, +0.1210] | 0.0000 | True | True |
| yangzhang_144|quintile/1 | dn | 48752 | 2850 | -0.1357 | [-0.1464, -0.1251] | 0.0000 | True | True |
| yangzhang_144|quintile/1 | up | 67265 | 2850 | -0.1562 | [-0.1701, -0.1423] | 0.0000 | True | True |
| yangzhang_144|quintile/2 | dn | 71484 | 2850 | -0.0586 | [-0.0675, -0.0498] | 0.0000 | True | True |
| yangzhang_144|quintile/2 | up | 93686 | 2850 | -0.0677 | [-0.0759, -0.0594] | 0.0000 | True | True |
| yangzhang_144|quintile/4 | dn | 107498 | 2850 | +0.0658 | [+0.0583, +0.0733] | 0.0000 | True | True |
| yangzhang_144|quintile/4 | up | 135203 | 2850 | +0.0745 | [+0.0666, +0.0825] | 0.0000 | True | True |
| yangzhang_144|quintile/5 | dn | 125077 | 2850 | +0.1276 | [+0.1132, +0.1420] | 0.0000 | True | True |
| yangzhang_144|quintile/5 | up | 152286 | 2850 | +0.1373 | [+0.1231, +0.1515] | 0.0000 | True | True |
| yangzhang_144|tercile/1 | dn | 94096 | 2850 | -0.1097 | [-0.1188, -0.1006] | 0.0000 | True | True |
| yangzhang_144|tercile/1 | up | 127425 | 2850 | -0.1253 | [-0.1360, -0.1146] | 0.0000 | True | True |
| yangzhang_144|tercile/3 | dn | 199137 | 2850 | +0.1078 | [+0.0969, +0.1186] | 0.0000 | True | True |
| yangzhang_144|tercile/3 | up | 245028 | 2850 | +0.1173 | [+0.1063, +0.1282] | 0.0000 | True | True |
| yangzhang_233|quintile/1 | dn | 48245 | 2850 | -0.1356 | [-0.1462, -0.1250] | 0.0000 | True | True |
| yangzhang_233|quintile/1 | up | 66914 | 2850 | -0.1553 | [-0.1694, -0.1413] | 0.0000 | True | True |
| yangzhang_233|quintile/2 | dn | 70658 | 2850 | -0.0590 | [-0.0681, -0.0499] | 0.0000 | True | True |
| yangzhang_233|quintile/2 | up | 92075 | 2850 | -0.0700 | [-0.0783, -0.0617] | 0.0000 | True | True |
| yangzhang_233|quintile/4 | dn | 106300 | 2850 | +0.0653 | [+0.0579, +0.0727] | 0.0000 | True | True |
| yangzhang_233|quintile/4 | up | 133757 | 2850 | +0.0739 | [+0.0653, +0.0824] | 0.0000 | True | True |
| yangzhang_233|quintile/5 | dn | 123885 | 2850 | +0.1280 | [+0.1137, +0.1423] | 0.0000 | True | True |
| yangzhang_233|quintile/5 | up | 150052 | 2850 | +0.1344 | [+0.1202, +0.1486] | 0.0000 | True | True |
| yangzhang_233|tercile/1 | dn | 92994 | 2850 | -0.1099 | [-0.1192, -0.1006] | 0.0000 | True | True |
| yangzhang_233|tercile/1 | up | 125900 | 2850 | -0.1261 | [-0.1368, -0.1154] | 0.0000 | True | True |
| yangzhang_233|tercile/3 | dn | 197321 | 2850 | +0.1082 | [+0.0974, +0.1189] | 0.0000 | True | True |
| yangzhang_233|tercile/3 | up | 241602 | 2850 | +0.1149 | [+0.1044, +0.1255] | 0.0000 | True | True |
| yangzhang_3|quintile/1 | dn | 56762 | 2850 | -0.1115 | [-0.1203, -0.1028] | 0.0000 | True | True |
| yangzhang_3|quintile/1 | up | 75914 | 2850 | -0.1305 | [-0.1417, -0.1194] | 0.0000 | True | True |
| yangzhang_3|quintile/2 | dn | 74006 | 2850 | -0.0532 | [-0.0597, -0.0468] | 0.0000 | True | True |
| yangzhang_3|quintile/2 | up | 98324 | 2850 | -0.0554 | [-0.0618, -0.0489] | 0.0000 | True | True |
| yangzhang_3|quintile/4 | dn | 106026 | 2850 | +0.0552 | [+0.0497, +0.0608] | 0.0000 | True | True |
| yangzhang_3|quintile/4 | up | 134985 | 2850 | +0.0677 | [+0.0606, +0.0749] | 0.0000 | True | True |
| yangzhang_3|quintile/5 | dn | 122520 | 2850 | +0.1129 | [+0.1006, +0.1251] | 0.0000 | True | True |
| yangzhang_3|quintile/5 | up | 146082 | 2850 | +0.1084 | [+0.0962, +0.1206] | 0.0000 | True | True |
| yangzhang_3|tercile/1 | dn | 104363 | 2850 | -0.0917 | [-0.0992, -0.0841] | 0.0000 | True | True |
| yangzhang_3|tercile/1 | up | 139245 | 2850 | -0.1048 | [-0.1139, -0.0957] | 0.0000 | True | True |
| yangzhang_3|tercile/3 | dn | 195059 | 2850 | +0.0934 | [+0.0842, +0.1026] | 0.0000 | True | True |
| yangzhang_3|tercile/3 | up | 237983 | 2850 | +0.0959 | [+0.0863, +0.1054] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_3|tercile/1 | dn | 23998 | 2846 | +0.1338 | [+0.1151, +0.1525] | 0.0000 | True | True |
| amihud_39|quintile/5 | dn | 103594 | 2850 | +0.0509 | [+0.0414, +0.0605] | 0.0000 | True | True |
| amihud_24|tercile/3 & amihud_39|quintile/5 | dn | 103502 | 2850 | +0.0510 | [+0.0415, +0.0606] | 0.0000 | True | True |
| amihud_6|tercile/3 & amihud_39|quintile/5 | dn | 102173 | 2850 | +0.0512 | [+0.0416, +0.0608] | 0.0000 | True | True |
| bb_width_144|quintile/5 & bb_width_233|quintile/4 | up | 32519 | 2850 | +0.0901 | [+0.0755, +0.1048] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_3|tercile/1 | up | 17795 | 2824 | +0.1343 | [+0.1195, +0.1492] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_39|tercile/1 | dn | 29096 | 2850 | -0.0621 | [-0.0734, -0.0509] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_9|quintile/5 | dn | 5191 | 2681 | -0.1082 | [-0.1253, -0.0910] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_3|tercile/3 | dn | 4519 | 2640 | -0.1139 | [-0.1263, -0.1014] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_24|quintile/5 | up | 30461 | 2850 | +0.0825 | [+0.0694, +0.0956] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_24|quintile/1 | up | 19428 | 2850 | -0.0759 | [-0.0882, -0.0636] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_6|tercile/1 | dn | 23748 | 2847 | +0.1350 | [+0.1153, +0.1547] | 0.0000 | True | True |
| amihud_63|quintile/5 | dn | 103270 | 2850 | +0.0505 | [+0.0409, +0.0601] | 0.0000 | True | True |
| amihud_3|tercile/3 & amihud_39|quintile/5 | dn | 99724 | 2850 | +0.0513 | [+0.0418, +0.0609] | 0.0000 | True | True |
| bb_width_9|quintile/2 | up | 102881 | 2850 | -0.0399 | [-0.0450, -0.0349] | 0.0000 | True | True |
| amihud_63|tercile/1 | dn | 131929 | 2850 | -0.0360 | [-0.0430, -0.0291] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_3|quintile/5 | dn | 10793 | 2850 | -0.0854 | [-0.0990, -0.0718] | 0.0000 | True | True |
| amihud_6|tercile/1 | dn | 132512 | 2850 | -0.0362 | [-0.0430, -0.0294] | 0.0000 | True | True |
| bb_width_9|quintile/5 & bb_width_233|quintile/4 | dn | 25380 | 2850 | +0.0876 | [+0.0765, +0.0987] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_3|tercile/1 | dn | 26589 | 2850 | -0.0582 | [-0.0660, -0.0504] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_3|quintile/2 | dn | 20657 | 2850 | +0.0960 | [+0.0851, +0.1070] | 0.0000 | True | True |
| amihud_9|tercile/3 & amihud_24|quintile/5 | dn | 103046 | 2850 | +0.0502 | [+0.0407, +0.0597] | 0.0000 | True | True |
| amihud_6|tercile/3 & amihud_24|quintile/5 | dn | 102434 | 2850 | +0.0503 | [+0.0408, +0.0598] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_9|quintile/5 | up | 30594 | 2850 | +0.0825 | [+0.0695, +0.0955] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_39|quintile/5 | up | 30552 | 2850 | +0.0819 | [+0.0692, +0.0947] | 0.0000 | True | True |
| amihud_24|tercile/1 | dn | 132096 | 2850 | -0.0366 | [-0.0437, -0.0296] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_9|quintile/1 | up | 19476 | 2850 | -0.0752 | [-0.0869, -0.0635] | 0.0000 | True | True |
| amihud_9|tercile/1 | dn | 132455 | 2850 | -0.0363 | [-0.0433, -0.0293] | 0.0000 | True | True |
| amihud_9|quintile/5 & amihud_39|quintile/5 | dn | 93778 | 2850 | +0.0524 | [+0.0425, +0.0623] | 0.0000 | True | True |
| amihud_233|tercile/3 | dn | 162881 | 2850 | +0.0370 | [+0.0299, +0.0442] | 0.0000 | True | True |
| amihud_24|quintile/5 | dn | 103436 | 2850 | +0.0500 | [+0.0404, +0.0595] | 0.0000 | True | True |
| amihud_24|quintile/5 & amihud_39|quintile/5 | dn | 98960 | 2850 | +0.0514 | [+0.0417, +0.0611] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_9|quintile/4 | up | 39455 | 2850 | +0.0806 | [+0.0719, +0.0893] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_9|quintile/4 | dn | 9789 | 2845 | -0.0859 | [-0.0967, -0.0751] | 0.0000 | True | True |
| amihud_9|quintile/5 & amihud_24|quintile/5 | dn | 95574 | 2850 | +0.0519 | [+0.0421, +0.0617] | 0.0000 | True | True |
| amihud_3|tercile/1 | dn | 133037 | 2850 | -0.0351 | [-0.0418, -0.0285] | 0.0000 | True | True |
| amihud_24|quintile/5 & amihud_39|tercile/3 | dn | 102995 | 2850 | +0.0499 | [+0.0403, +0.0594] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_233|quintile/4 | up | 31981 | 2850 | +0.0902 | [+0.0793, +0.1010] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_39|quintile/1 | up | 20672 | 2850 | -0.0750 | [-0.0847, -0.0653] | 0.0000 | True | True |
| amihud_39|tercile/1 | dn | 132115 | 2850 | -0.0362 | [-0.0433, -0.0292] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_233|quintile/2 | dn | 16927 | 2850 | -0.0627 | [-0.0700, -0.0554] | 0.0000 | True | True |
| amihud_3|tercile/3 & amihud_24|quintile/5 | dn | 100100 | 2850 | +0.0504 | [+0.0409, +0.0600] | 0.0000 | True | True |
| amihud_9|tercile/1 & amihud_24|tercile/1 | dn | 123144 | 2850 | -0.0377 | [-0.0451, -0.0304] | 0.0000 | True | True |
| amihud_6|tercile/3 & amihud_9|quintile/5 | dn | 103142 | 2850 | +0.0491 | [+0.0399, +0.0583] | 0.0000 | True | True |
| amihud_6|quintile/5 & amihud_39|quintile/5 | dn | 91712 | 2850 | +0.0528 | [+0.0430, +0.0626] | 0.0000 | True | True |
| amihud_9|quintile/5 & amihud_24|tercile/3 | dn | 102917 | 2850 | +0.0490 | [+0.0397, +0.0582] | 0.0000 | True | True |
| amihud_9|quintile/5 | dn | 103350 | 2850 | +0.0491 | [+0.0398, +0.0583] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_24|quintile/5 | dn | 5203 | 2671 | -0.1059 | [-0.1237, -0.0880] | 0.0000 | True | True |
| amihud_3|tercile/3 & amihud_9|quintile/5 | dn | 101330 | 2850 | +0.0495 | [+0.0402, +0.0587] | 0.0000 | True | True |
| amihud_9|quintile/5 & amihud_39|tercile/3 | dn | 102460 | 2850 | +0.0488 | [+0.0396, +0.0580] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_233|quintile/2 | dn | 17847 | 2850 | -0.0624 | [-0.0703, -0.0544] | 0.0000 | True | True |
| amihud_9|tercile/1 & amihud_39|tercile/1 | dn | 121566 | 2850 | -0.0376 | [-0.0448, -0.0304] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_3|tercile/3 | up | 6210 | 2640 | -0.1285 | [-0.1421, -0.1150] | 0.0000 | True | True |
| bb_width_144|quintile/4 & bb_width_233|quintile/5 | up | 27318 | 2850 | +0.1004 | [+0.0833, +0.1175] | 0.0000 | True | True |
| amihud_233|quintile/2 | up | 102509 | 2850 | -0.0335 | [-0.0397, -0.0274] | 0.0000 | True | True |
| amihud_6|quintile/5 & amihud_9|quintile/5 | dn | 97399 | 2850 | +0.0506 | [+0.0412, +0.0600] | 0.0000 | True | True |
| amihud_6|tercile/1 & amihud_9|tercile/1 | dn | 125107 | 2850 | -0.0370 | [-0.0442, -0.0297] | 0.0000 | True | True |
| amihud_6|tercile/1 & amihud_24|tercile/1 | dn | 120230 | 2850 | -0.0379 | [-0.0453, -0.0305] | 0.0000 | True | True |
| amihud_6|quintile/5 & amihud_24|quintile/5 | dn | 93156 | 2850 | +0.0522 | [+0.0424, +0.0620] | 0.0000 | True | True |
| amihud_24|tercile/1 & amihud_39|tercile/1 | dn | 127379 | 2850 | -0.0369 | [-0.0441, -0.0298] | 0.0000 | True | True |
| amihud_6|quintile/5 | dn | 103314 | 2850 | +0.0489 | [+0.0398, +0.0580] | 0.0000 | True | True |
| amihud_3|quintile/5 & amihud_39|quintile/5 | dn | 87400 | 2850 | +0.0535 | [+0.0436, +0.0634] | 0.0000 | True | True |
| amihud_3|tercile/3 & amihud_6|quintile/5 | dn | 101995 | 2850 | +0.0491 | [+0.0399, +0.0582] | 0.0000 | True | True |
| amihud_6|quintile/5 & amihud_9|tercile/3 | dn | 103244 | 2850 | +0.0489 | [+0.0398, +0.0580] | 0.0000 | True | True |
| bb_width_144|quintile/5 & bb_width_233|quintile/4 | dn | 25598 | 2850 | +0.0808 | [+0.0678, +0.0939] | 0.0000 | True | True |
| amihud_6|quintile/5 & amihud_24|tercile/3 | dn | 102758 | 2850 | +0.0487 | [+0.0396, +0.0578] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_63|quintile/1 | up | 20644 | 2850 | -0.0749 | [-0.0848, -0.0650] | 0.0000 | True | True |
| amihud_102|quintile/2 | up | 104279 | 2850 | -0.0323 | [-0.0377, -0.0269] | 0.0000 | True | True |
| amihud_6|tercile/1 & amihud_39|tercile/1 | dn | 118907 | 2850 | -0.0378 | [-0.0452, -0.0305] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_3|tercile/1 | dn | 29097 | 2850 | -0.0619 | [-0.0732, -0.0505] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_233|quintile/4 | dn | 25666 | 2850 | +0.0839 | [+0.0739, +0.0938] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_3|tercile/1 | dn | 28343 | 2850 | -0.0559 | [-0.0636, -0.0481] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_233|quintile/2 | up | 28038 | 2850 | -0.0713 | [-0.0831, -0.0596] | 0.0000 | True | True |
| amihud_6|quintile/5 & amihud_39|tercile/3 | dn | 102210 | 2850 | +0.0485 | [+0.0394, +0.0576] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_9|tercile/1 | dn | 29141 | 2850 | -0.0623 | [-0.0738, -0.0508] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_233|quintile/4 | dn | 34772 | 2850 | +0.0657 | [+0.0552, +0.0761] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_6|quintile/5 | up | 30580 | 2850 | +0.0816 | [+0.0685, +0.0947] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_3|quintile/1 | up | 20574 | 2845 | +0.1085 | [+0.0978, +0.1192] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_9|quintile/1 | dn | 19394 | 2850 | -0.0670 | [-0.0770, -0.0570] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_39|quintile/5 | dn | 5302 | 2679 | -0.1041 | [-0.1226, -0.0855] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_3|quintile/1 | up | 19461 | 2850 | -0.0753 | [-0.0868, -0.0638] | 0.0000 | True | True |
| amihud_3|quintile/5 | dn | 103170 | 2850 | +0.0482 | [+0.0392, +0.0573] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_39|quintile/1 | up | 19464 | 2850 | -0.0742 | [-0.0859, -0.0624] | 0.0000 | True | True |
| bb_width_144|quintile/1 & bb_width_233|quintile/2 | up | 19337 | 2850 | -0.0806 | [-0.0952, -0.0660] | 0.0000 | True | True |
| amihud_3|quintile/5 & amihud_6|tercile/3 | dn | 103071 | 2850 | +0.0482 | [+0.0392, +0.0573] | 0.0000 | True | True |
| amihud_3|quintile/5 & amihud_9|tercile/3 | dn | 102872 | 2850 | +0.0483 | [+0.0393, +0.0573] | 0.0000 | True | True |
| amihud_233|quintile/5 | dn | 101098 | 2850 | +0.0498 | [+0.0402, +0.0594] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_9|quintile/4 | up | 4657 | 2611 | -0.1346 | [-0.1500, -0.1193] | 0.0000 | True | True |
| amihud_3|quintile/5 & amihud_24|tercile/3 | dn | 102013 | 2850 | +0.0482 | [+0.0392, +0.0571] | 0.0000 | True | True |
| bb_width_9|quintile/5 & bb_width_144|quintile/4 | up | 32496 | 2850 | +0.0894 | [+0.0770, +0.1017] | 0.0000 | True | True |
| amihud_3|tercile/1 & amihud_6|tercile/1 | dn | 119473 | 2850 | -0.0372 | [-0.0444, -0.0300] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_3|tercile/1 | up | 34042 | 2850 | +0.1016 | [+0.0860, +0.1171] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_6|quintile/5 | dn | 10618 | 2850 | -0.0851 | [-0.0997, -0.0706] | 0.0000 | True | True |
| amihud_3|quintile/5 & amihud_24|quintile/5 | dn | 88400 | 2850 | +0.0527 | [+0.0428, +0.0627] | 0.0000 | True | True |
| amihud_3|quintile/5 & amihud_9|quintile/5 | dn | 91176 | 2850 | +0.0515 | [+0.0419, +0.0612] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_24|quintile/1 | up | 20754 | 2850 | -0.0738 | [-0.0837, -0.0639] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_3|quintile/5 | dn | 28560 | 2850 | +0.0781 | [+0.0700, +0.0862] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_6|tercile/1 | up | 33724 | 2850 | +0.1024 | [+0.0867, +0.1182] | 0.0000 | True | True |
| amihud_3|quintile/5 & amihud_39|tercile/3 | dn | 101352 | 2850 | +0.0480 | [+0.0391, +0.0570] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_6|tercile/1 | dn | 29156 | 2850 | -0.0619 | [-0.0735, -0.0502] | 0.0000 | True | True |
| amihud_3|tercile/1 & amihud_24|tercile/1 | dn | 114115 | 2850 | -0.0382 | [-0.0457, -0.0307] | 0.0000 | True | True |
| amihud_3|tercile/1 & amihud_9|tercile/1 | dn | 117377 | 2850 | -0.0374 | [-0.0448, -0.0301] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_9|quintile/1 | dn | 16355 | 2850 | -0.0675 | [-0.0771, -0.0578] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_3|quintile/2 | dn | 18716 | 2850 | -0.0639 | [-0.0725, -0.0554] | 0.0000 | True | True |
| amihud_144|quintile/1 | dn | 76290 | 2850 | -0.0441 | [-0.0528, -0.0353] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_6|quintile/1 | up | 19481 | 2850 | -0.0748 | [-0.0865, -0.0630] | 0.0000 | True | True |
| amihud_3|quintile/5 & amihud_6|quintile/5 | dn | 92952 | 2850 | +0.0507 | [+0.0412, +0.0603] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_3|quintile/5 | up | 30398 | 2850 | +0.0803 | [+0.0676, +0.0931] | 0.0000 | True | True |
| amihud_3|tercile/1 & amihud_39|tercile/1 | dn | 113192 | 2850 | -0.0381 | [-0.0456, -0.0306] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_3|tercile/1 | up | 34511 | 2850 | +0.1038 | [+0.0883, +0.1193] | 0.0000 | True | True |
| amihud_144|quintile/2 | up | 103687 | 2850 | -0.0329 | [-0.0388, -0.0270] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_9|quintile/2 | up | 19875 | 2845 | +0.1039 | [+0.0913, +0.1165] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_24|quintile/1 | up | 19942 | 2850 | -0.0785 | [-0.0927, -0.0642] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_3|quintile/1 | dn | 15055 | 2850 | -0.0684 | [-0.0800, -0.0568] | 0.0000 | True | True |
| amihud_233|quintile/1 | dn | 75630 | 2850 | -0.0434 | [-0.0522, -0.0347] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_6|quintile/1 | dn | 15138 | 2850 | -0.0677 | [-0.0795, -0.0559] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_144|quintile/4 | up | 13917 | 2804 | -0.0907 | [-0.1058, -0.0755] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_3|quintile/5 | up | 14703 | 2850 | -0.0901 | [-0.1047, -0.0755] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_9|quintile/5 | dn | 10630 | 2850 | -0.0836 | [-0.0987, -0.0686] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_3|quintile/1 | up | 19902 | 2850 | -0.0784 | [-0.0919, -0.0650] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_6|tercile/1 | up | 34188 | 2850 | +0.1039 | [+0.0881, +0.1197] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_9|quintile/1 | dn | 23047 | 2850 | +0.1154 | [+0.0962, +0.1346] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_9|quintile/5 | dn | 27172 | 2850 | +0.0757 | [+0.0665, +0.0850] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_3|quintile/1 | dn | 23128 | 2850 | +0.1132 | [+0.0953, +0.1311] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_6|quintile/1 | up | 20001 | 2850 | -0.0780 | [-0.0922, -0.0638] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_9|quintile/1 | up | 19985 | 2850 | -0.0778 | [-0.0917, -0.0639] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_3|quintile/1 | dn | 17382 | 2850 | -0.0683 | [-0.0777, -0.0589] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_3|quintile/5 | up | 7382 | 2702 | -0.1159 | [-0.1358, -0.0960] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_6|quintile/1 | dn | 16415 | 2850 | -0.0665 | [-0.0762, -0.0569] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_39|quintile/1 | up | 20058 | 2850 | -0.0772 | [-0.0912, -0.0633] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_3|quintile/2 | up | 24861 | 2850 | -0.0696 | [-0.0789, -0.0604] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_9|quintile/1 | dn | 15198 | 2850 | -0.0671 | [-0.0789, -0.0554] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_144|quintile/4 | up | 32421 | 2850 | +0.0872 | [+0.0760, +0.0983] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_24|quintile/1 | dn | 23224 | 2850 | +0.1159 | [+0.0952, +0.1367] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_3|quintile/1 | up | 20337 | 2850 | -0.0722 | [-0.0814, -0.0631] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_9|tercile/1 | up | 33429 | 2850 | +0.1004 | [+0.0846, +0.1162] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_24|quintile/1 | dn | 16196 | 2850 | -0.0670 | [-0.0768, -0.0571] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_24|quintile/1 | dn | 15131 | 2850 | -0.0677 | [-0.0795, -0.0560] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_24|tercile/1 | up | 33387 | 2850 | +0.1010 | [+0.0848, +0.1171] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_9|quintile/5 | up | 33612 | 2850 | +0.0779 | [+0.0684, +0.0875] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_144|quintile/5 | dn | 27827 | 2850 | +0.0844 | [+0.0700, +0.0989] | 0.0000 | True | True |
| amihud_3|quintile/1 | dn | 77675 | 2850 | -0.0430 | [-0.0513, -0.0348] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_6|quintile/1 | dn | 22945 | 2850 | +0.1127 | [+0.0938, +0.1315] | 0.0000 | True | True |
| amihud_3|quintile/1 & amihud_39|tercile/1 | dn | 73508 | 2850 | -0.0445 | [-0.0532, -0.0358] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_39|quintile/1 | dn | 15065 | 2850 | -0.0679 | [-0.0801, -0.0558] | 0.0000 | True | True |
| amihud_3|tercile/1 & amihud_6|quintile/1 | dn | 77535 | 2850 | -0.0433 | [-0.0519, -0.0347] | 0.0000 | True | True |
| bb_width_9|quintile/4 & amihud_3|tercile/3 | dn | 41197 | 2850 | +0.0574 | [+0.0493, +0.0656] | 0.0000 | True | True |
| amihud_6|quintile/1 | dn | 77583 | 2850 | -0.0433 | [-0.0519, -0.0347] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_9|quintile/1 | up | 20807 | 2850 | -0.0712 | [-0.0807, -0.0617] | 0.0000 | True | True |
| bb_width_9|quintile/5 & bb_width_233|quintile/4 | up | 30875 | 2850 | +0.0868 | [+0.0745, +0.0991] | 0.0000 | True | True |
| amihud_3|quintile/1 & amihud_24|tercile/1 | dn | 73960 | 2850 | -0.0444 | [-0.0531, -0.0356] | 0.0000 | True | True |
| amihud_3|quintile/1 & amihud_6|tercile/1 | dn | 76014 | 2850 | -0.0435 | [-0.0520, -0.0351] | 0.0000 | True | True |
| amihud_3|quintile/1 & amihud_9|tercile/1 | dn | 75234 | 2850 | -0.0438 | [-0.0523, -0.0354] | 0.0000 | True | True |
| amihud_6|quintile/1 & amihud_9|tercile/1 | dn | 77401 | 2850 | -0.0434 | [-0.0521, -0.0347] | 0.0000 | True | True |
| amihud_6|quintile/1 & amihud_39|tercile/1 | dn | 76310 | 2850 | -0.0438 | [-0.0525, -0.0350] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_39|quintile/1 | dn | 23353 | 2850 | +0.1176 | [+0.0967, +0.1385] | 0.0000 | True | True |
| bb_width_9|quintile/4 & amihud_9|tercile/3 | dn | 41283 | 2850 | +0.0568 | [+0.0484, +0.0651] | 0.0000 | True | True |
| bb_width_9|quintile/4 & amihud_6|tercile/3 | dn | 41343 | 2850 | +0.0568 | [+0.0484, +0.0652] | 0.0000 | True | True |
| amihud_6|quintile/1 & amihud_24|tercile/1 | dn | 76688 | 2850 | -0.0436 | [-0.0523, -0.0350] | 0.0000 | True | True |
| amihud_102|quintile/1 | dn | 77014 | 2850 | -0.0428 | [-0.0518, -0.0339] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_3|tercile/1 | up | 27691 | 2846 | +0.1285 | [+0.1082, +0.1488] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_63|quintile/1 | up | 19575 | 2850 | -0.0722 | [-0.0842, -0.0601] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_9|quintile/2 | up | 28059 | 2850 | -0.0653 | [-0.0748, -0.0558] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_233|quintile/4 | dn | 4192 | 2604 | -0.1085 | [-0.1270, -0.0899] | 0.0000 | True | True |
| amihud_6|tercile/1 & amihud_9|quintile/1 | dn | 77673 | 2850 | -0.0429 | [-0.0517, -0.0342] | 0.0000 | True | True |
| amihud_9|quintile/1 | dn | 77673 | 2850 | -0.0429 | [-0.0517, -0.0342] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_63|quintile/1 | dn | 16137 | 2850 | -0.0658 | [-0.0756, -0.0560] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_24|tercile/1 | up | 33926 | 2850 | +0.1032 | [+0.0863, +0.1200] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_9|tercile/1 | up | 33984 | 2850 | +0.1023 | [+0.0860, +0.1186] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_63|quintile/1 | up | 20267 | 2850 | -0.0759 | [-0.0900, -0.0617] | 0.0000 | True | True |
| amihud_3|tercile/1 & amihud_9|quintile/1 | dn | 77481 | 2850 | -0.0429 | [-0.0517, -0.0342] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_9|quintile/4 | dn | 31640 | 2850 | +0.0724 | [+0.0646, +0.0803] | 0.0000 | True | True |
| amihud_9|quintile/1 & amihud_24|tercile/1 | dn | 77307 | 2850 | -0.0431 | [-0.0520, -0.0342] | 0.0000 | True | True |
| amihud_9|quintile/1 & amihud_39|tercile/1 | dn | 77011 | 2850 | -0.0432 | [-0.0520, -0.0343] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_144|quintile/4 | dn | 27368 | 2850 | +0.0660 | [+0.0580, +0.0740] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_9|quintile/4 | dn | 3611 | 2611 | -0.1133 | [-0.1273, -0.0993] | 0.0000 | True | True |
| amihud_3|quintile/1 & amihud_6|quintile/1 | dn | 67633 | 2850 | -0.0455 | [-0.0544, -0.0366] | 0.0000 | True | True |
| amihud_63|quintile/2 | up | 105144 | 2850 | -0.0307 | [-0.0362, -0.0252] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_3|tercile/3 | up | 19566 | 2850 | -0.0757 | [-0.0882, -0.0632] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_39|tercile/1 | up | 33132 | 2850 | +0.1011 | [+0.0843, +0.1178] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_39|quintile/1 | dn | 16234 | 2850 | -0.0654 | [-0.0753, -0.0555] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_39|tercile/1 | up | 33753 | 2850 | +0.1025 | [+0.0858, +0.1193] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_9|quintile/2 | dn | 16272 | 2850 | -0.0621 | [-0.0684, -0.0559] | 0.0000 | True | True |
| bb_width_9|quintile/4 & amihud_24|tercile/3 | dn | 40567 | 2850 | +0.0574 | [+0.0486, +0.0661] | 0.0000 | True | True |
| amihud_6|quintile/1 & amihud_9|quintile/1 | dn | 72296 | 2850 | -0.0440 | [-0.0530, -0.0351] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_63|quintile/1 | dn | 15105 | 2850 | -0.0671 | [-0.0799, -0.0544] | 0.0000 | True | True |
| amihud_3|quintile/1 & amihud_9|quintile/1 | dn | 66179 | 2850 | -0.0454 | [-0.0545, -0.0364] | 0.0000 | True | True |
| bb_width_9|quintile/4 & amihud_39|tercile/3 | dn | 40223 | 2850 | +0.0568 | [+0.0479, +0.0657] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_6|quintile/1 | up | 20705 | 2850 | -0.0706 | [-0.0798, -0.0615] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_24|tercile/1 | up | 27377 | 2843 | +0.1280 | [+0.1072, +0.1489] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_6|tercile/1 | up | 27385 | 2847 | +0.1274 | [+0.1070, +0.1479] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_24|quintile/5 | dn | 10690 | 2850 | -0.0805 | [-0.0960, -0.0651] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_233|quintile/2 | up | 22684 | 2850 | -0.0665 | [-0.0750, -0.0580] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_39|quintile/5 | dn | 24277 | 2850 | +0.0725 | [+0.0597, +0.0853] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_39|tercile/1 | up | 27302 | 2846 | +0.1289 | [+0.1069, +0.1508] | 0.0000 | True | True |
| amihud_3|quintile/1 & amihud_63|quintile/1 | dn | 62968 | 2850 | -0.0457 | [-0.0550, -0.0364] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_9|tercile/1 | up | 27225 | 2846 | +0.1258 | [+0.1052, +0.1465] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_6|quintile/5 | up | 14584 | 2850 | -0.0863 | [-0.1016, -0.0710] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_63|quintile/1 | dn | 23177 | 2850 | +0.1160 | [+0.0945, +0.1376] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_39|quintile/5 | dn | 10846 | 2850 | -0.0790 | [-0.0944, -0.0636] | 0.0000 | True | True |
| bb_width_144|quintile/4 & bb_width_233|quintile/5 | dn | 21907 | 2850 | +0.0828 | [+0.0681, +0.0975] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_3|tercile/1 | dn | 14357 | 2824 | +0.1179 | [+0.1030, +0.1328] | 0.0000 | True | True |
| amihud_6|quintile/1 & amihud_63|quintile/1 | dn | 67483 | 2850 | -0.0443 | [-0.0535, -0.0352] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_3|tercile/1 | up | 29639 | 2850 | +0.0738 | [+0.0654, +0.0822] | 0.0000 | True | True |
| amihud_9|quintile/1 & amihud_63|quintile/1 | dn | 69291 | 2850 | -0.0438 | [-0.0529, -0.0346] | 0.0000 | True | True |
| amihud_6|quintile/1 & amihud_24|quintile/1 | dn | 69206 | 2850 | -0.0443 | [-0.0536, -0.0349] | 0.0000 | True | True |
| amihud_3|quintile/1 & amihud_24|quintile/1 | dn | 64194 | 2850 | -0.0455 | [-0.0550, -0.0361] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_144|quintile/5 | up | 22611 | 2848 | +0.0941 | [+0.0823, +0.1059] | 0.0000 | True | True |
| amihud_9|quintile/1 & amihud_24|quintile/1 | dn | 71449 | 2850 | -0.0435 | [-0.0528, -0.0343] | 0.0000 | True | True |
| amihud_24|quintile/1 & amihud_63|quintile/1 | dn | 72694 | 2850 | -0.0427 | [-0.0518, -0.0336] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_6|quintile/1 | dn | 15997 | 2850 | -0.0631 | [-0.0726, -0.0537] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_9|quintile/1 | dn | 16105 | 2850 | -0.0629 | [-0.0724, -0.0533] | 0.0000 | True | True |
| amihud_24|quintile/1 & amihud_39|tercile/1 | dn | 77783 | 2850 | -0.0419 | [-0.0510, -0.0328] | 0.0000 | True | True |
| amihud_3|tercile/1 & amihud_24|quintile/1 | dn | 77285 | 2850 | -0.0420 | [-0.0511, -0.0329] | 0.0000 | True | True |
| amihud_6|tercile/1 & amihud_24|quintile/1 | dn | 77875 | 2850 | -0.0418 | [-0.0510, -0.0327] | 0.0000 | True | True |
| amihud_9|quintile/1 & amihud_39|quintile/1 | dn | 70289 | 2850 | -0.0435 | [-0.0527, -0.0343] | 0.0000 | True | True |
| amihud_24|quintile/1 | dn | 77914 | 2850 | -0.0418 | [-0.0509, -0.0327] | 0.0000 | True | True |
| amihud_9|tercile/1 & amihud_24|quintile/1 | dn | 77911 | 2850 | -0.0418 | [-0.0509, -0.0327] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_3|tercile/3 | up | 19788 | 2850 | -0.0745 | [-0.0877, -0.0612] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_233|quintile/4 | up | 34081 | 2850 | +0.0680 | [+0.0583, +0.0777] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_3|quintile/5 | dn | 24119 | 2850 | +0.0705 | [+0.0587, +0.0822] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_3|quintile/1 | dn | 15727 | 2850 | -0.0634 | [-0.0726, -0.0541] | 0.0000 | True | True |
| amihud_6|quintile/1 & amihud_39|quintile/1 | dn | 68312 | 2850 | -0.0440 | [-0.0533, -0.0347] | 0.0000 | True | True |
| amihud_24|quintile/1 & amihud_39|quintile/1 | dn | 74497 | 2850 | -0.0421 | [-0.0513, -0.0330] | 0.0000 | True | True |
| amihud_3|quintile/1 & amihud_39|quintile/1 | dn | 63612 | 2850 | -0.0452 | [-0.0545, -0.0359] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_24|quintile/5 | dn | 24067 | 2850 | +0.0711 | [+0.0583, +0.0840] | 0.0000 | True | True |
| amihud_3|tercile/1 & amihud_63|quintile/1 | dn | 76843 | 2850 | -0.0414 | [-0.0504, -0.0324] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_233|quintile/5 | up | 22304 | 2848 | +0.0984 | [+0.0856, +0.1113] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_24|tercile/3 | dn | 39040 | 2850 | +0.0590 | [+0.0477, +0.0704] | 0.0000 | True | True |
| amihud_39|quintile/1 & amihud_63|quintile/1 | dn | 74749 | 2850 | -0.0416 | [-0.0506, -0.0326] | 0.0000 | True | True |
| amihud_24|quintile/2 | up | 105866 | 2850 | -0.0298 | [-0.0356, -0.0241] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_63|quintile/1 | dn | 16211 | 2850 | -0.0620 | [-0.0717, -0.0522] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_3|tercile/1 | up | 56906 | 2850 | +0.0684 | [+0.0561, +0.0807] | 0.0000 | True | True |
| amihud_6|tercile/1 & amihud_63|quintile/1 | dn | 77724 | 2850 | -0.0410 | [-0.0501, -0.0320] | 0.0000 | True | True |
| amihud_9|tercile/1 & amihud_63|quintile/1 | dn | 77844 | 2850 | -0.0410 | [-0.0501, -0.0320] | 0.0000 | True | True |
| amihud_39|tercile/1 & amihud_63|quintile/1 | dn | 77890 | 2850 | -0.0410 | [-0.0500, -0.0320] | 0.0000 | True | True |
| amihud_63|quintile/1 | dn | 77890 | 2850 | -0.0410 | [-0.0500, -0.0320] | 0.0000 | True | True |
| amihud_24|tercile/1 & amihud_63|quintile/1 | dn | 77890 | 2850 | -0.0410 | [-0.0500, -0.0320] | 0.0000 | True | True |
| amihud_39|quintile/2 | up | 105463 | 2850 | -0.0307 | [-0.0364, -0.0249] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_39|tercile/3 | up | 19274 | 2850 | -0.0728 | [-0.0865, -0.0590] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_144|quintile/2 | up | 22974 | 2850 | -0.0649 | [-0.0737, -0.0562] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_6|quintile/5 | dn | 24074 | 2850 | +0.0699 | [+0.0576, +0.0823] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_144|quintile/2 | up | 28943 | 2850 | -0.0640 | [-0.0756, -0.0524] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_39|tercile/3 | dn | 39045 | 2850 | +0.0581 | [+0.0472, +0.0691] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_9|tercile/3 | dn | 38944 | 2850 | +0.0579 | [+0.0472, +0.0686] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_144|quintile/4 | up | 6031 | 2597 | -0.1143 | [-0.1360, -0.0927] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_3|quintile/2 | up | 12387 | 2766 | +0.1312 | [+0.1155, +0.1469] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_3|quintile/1 | up | 23394 | 2850 | -0.0692 | [-0.0792, -0.0592] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_24|quintile/1 | dn | 16247 | 2850 | -0.0623 | [-0.0722, -0.0524] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_9|quintile/5 | dn | 24022 | 2850 | +0.0698 | [+0.0570, +0.0827] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_9|quintile/5 | up | 14577 | 2850 | -0.0848 | [-0.1009, -0.0686] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_9|quintile/2 | up | 21639 | 2850 | -0.0681 | [-0.0761, -0.0601] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_3|quintile/1 | dn | 16732 | 2850 | -0.0617 | [-0.0713, -0.0521] | 0.0000 | True | True |
| amihud_6|tercile/1 & amihud_39|quintile/1 | dn | 78040 | 2850 | -0.0407 | [-0.0496, -0.0317] | 0.0000 | True | True |
| amihud_3|tercile/1 & amihud_39|quintile/1 | dn | 77306 | 2850 | -0.0408 | [-0.0497, -0.0319] | 0.0000 | True | True |
| amihud_24|tercile/1 & amihud_39|quintile/1 | dn | 78143 | 2850 | -0.0406 | [-0.0496, -0.0317] | 0.0000 | True | True |
| amihud_39|quintile/1 | dn | 78143 | 2850 | -0.0406 | [-0.0496, -0.0317] | 0.0000 | True | True |
| amihud_9|tercile/1 & amihud_39|quintile/1 | dn | 78124 | 2850 | -0.0406 | [-0.0496, -0.0317] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_3|tercile/1 | up | 34238 | 2850 | +0.0744 | [+0.0613, +0.0874] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_6|tercile/3 | up | 19423 | 2850 | -0.0732 | [-0.0861, -0.0603] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_3|tercile/3 | dn | 38692 | 2850 | +0.0577 | [+0.0471, +0.0682] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_39|quintile/1 | dn | 16273 | 2850 | -0.0613 | [-0.0711, -0.0515] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_63|quintile/1 | up | 23848 | 2850 | -0.0648 | [-0.0769, -0.0526] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_9|tercile/3 | dn | 8525 | 2827 | -0.0816 | [-0.0941, -0.0692] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_6|tercile/3 | dn | 38870 | 2850 | +0.0576 | [+0.0466, +0.0686] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_9|quintile/1 | up | 26089 | 2850 | -0.0692 | [-0.0804, -0.0580] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_39|quintile/1 | up | 23838 | 2850 | -0.0639 | [-0.0758, -0.0521] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_6|tercile/1 | up | 56418 | 2850 | +0.0679 | [+0.0554, +0.0803] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_3|tercile/3 | dn | 14974 | 2849 | -0.0620 | [-0.0707, -0.0533] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_144|quintile/4 | dn | 4317 | 2597 | -0.1012 | [-0.1196, -0.0829] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_9|tercile/1 | up | 18295 | 2822 | +0.0991 | [+0.0855, +0.1128] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_6|quintile/5 | up | 7412 | 2683 | -0.1086 | [-0.1305, -0.0868] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_24|quintile/1 | up | 23849 | 2850 | -0.0641 | [-0.0762, -0.0520] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_9|tercile/3 | up | 19454 | 2850 | -0.0722 | [-0.0854, -0.0589] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_6|tercile/3 | up | 19587 | 2850 | -0.0723 | [-0.0858, -0.0588] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_3|tercile/1 | dn | 27849 | 2850 | +0.0865 | [+0.0724, +0.1007] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_24|quintile/1 | dn | 13034 | 2575 | +0.1425 | [+0.1180, +0.1671] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_24|tercile/3 | up | 19474 | 2850 | -0.0713 | [-0.0850, -0.0577] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_9|quintile/2 | dn | 18749 | 2850 | -0.0519 | [-0.0574, -0.0463] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_3|quintile/1 | up | 26829 | 2850 | +0.1068 | [+0.0880, +0.1257] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_3|tercile/1 | up | 56917 | 2850 | +0.0685 | [+0.0560, +0.0810] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_9|tercile/3 | up | 11459 | 2827 | -0.0904 | [-0.1033, -0.0775] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_3|tercile/1 | dn | 28068 | 2850 | +0.0865 | [+0.0724, +0.1006] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_3|tercile/3 | dn | 16634 | 2850 | -0.0592 | [-0.0698, -0.0486] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_6|quintile/1 | dn | 17938 | 2850 | -0.0619 | [-0.0748, -0.0489] | 0.0000 | True | True |
| amihud_9|quintile/2 | up | 106207 | 2850 | -0.0290 | [-0.0343, -0.0237] | 0.0000 | True | True |
| amihud_6|quintile/2 | up | 106135 | 2850 | -0.0292 | [-0.0343, -0.0242] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_6|tercile/1 | up | 33937 | 2850 | +0.0731 | [+0.0595, +0.0868] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_39|tercile/3 | up | 19466 | 2850 | -0.0718 | [-0.0858, -0.0578] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_3|quintile/1 | up | 19720 | 2825 | +0.1104 | [+0.0915, +0.1293] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_3|quintile/1 | dn | 17773 | 2850 | -0.0622 | [-0.0748, -0.0496] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_39|tercile/1 | up | 33988 | 2850 | +0.0747 | [+0.0599, +0.0896] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_3|quintile/1 | dn | 16311 | 2845 | +0.0916 | [+0.0805, +0.1027] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_9|tercile/3 | dn | 14789 | 2850 | -0.0613 | [-0.0702, -0.0525] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_9|tercile/3 | dn | 16430 | 2850 | -0.0585 | [-0.0695, -0.0474] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_24|tercile/1 | up | 33892 | 2850 | +0.0741 | [+0.0593, +0.0890] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_9|tercile/3 | up | 19606 | 2850 | -0.0715 | [-0.0852, -0.0578] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_24|quintile/5 | up | 14477 | 2850 | -0.0818 | [-0.0982, -0.0655] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_9|quintile/1 | up | 23784 | 2850 | -0.0628 | [-0.0746, -0.0511] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_24|quintile/1 | dn | 18109 | 2850 | -0.0609 | [-0.0739, -0.0479] | 0.0000 | True | True |
| bb_width_144|quintile/4 & bb_width_233|quintile/4 | dn | 43508 | 2850 | +0.0470 | [+0.0384, +0.0555] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_6|quintile/1 | up | 26572 | 2850 | +0.1069 | [+0.0867, +0.1271] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_6|tercile/1 | up | 56452 | 2850 | +0.0684 | [+0.0555, +0.0814] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_39|tercile/3 | dn | 16430 | 2850 | -0.0581 | [-0.0694, -0.0467] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_3|quintile/1 | dn | 13093 | 2698 | +0.1354 | [+0.1138, +0.1570] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_39|tercile/3 | dn | 16348 | 2850 | -0.0578 | [-0.0663, -0.0494] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_9|tercile/1 | up | 33858 | 2850 | +0.0732 | [+0.0589, +0.0874] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_233|tercile/3 | up | 42333 | 2850 | +0.0630 | [+0.0541, +0.0719] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_9|tercile/1 | dn | 27479 | 2850 | +0.0840 | [+0.0694, +0.0986] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_9|tercile/1 | up | 56066 | 2850 | +0.0662 | [+0.0535, +0.0789] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_6|tercile/3 | dn | 14626 | 2850 | -0.0613 | [-0.0705, -0.0521] | 0.0000 | True | True |
| bb_width_3|quintile/4 | up | 124207 | 2850 | +0.0316 | [+0.0276, +0.0355] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_24|tercile/3 | up | 19712 | 2850 | -0.0706 | [-0.0848, -0.0563] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_6|quintile/1 | up | 23820 | 2850 | -0.0624 | [-0.0738, -0.0509] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_9|quintile/1 | dn | 12929 | 2603 | +0.1366 | [+0.1133, +0.1598] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_39|quintile/1 | dn | 12891 | 2537 | +0.1401 | [+0.1155, +0.1647] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_6|quintile/1 | up | 19311 | 2797 | +0.1102 | [+0.0911, +0.1292] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_9|quintile/1 | dn | 18044 | 2850 | -0.0607 | [-0.0740, -0.0474] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_6|tercile/3 | dn | 16557 | 2850 | -0.0578 | [-0.0685, -0.0471] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_63|quintile/1 | dn | 17990 | 2850 | -0.0607 | [-0.0740, -0.0475] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_6|tercile/1 | dn | 27488 | 2850 | +0.0834 | [+0.0691, +0.0977] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_3|quintile/2 | dn | 9961 | 2766 | +0.1214 | [+0.1056, +0.1371] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_3|quintile/1 | up | 23644 | 2850 | -0.0626 | [-0.0740, -0.0512] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_24|tercile/3 | dn | 16333 | 2850 | -0.0585 | [-0.0700, -0.0471] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_3|quintile/1 | up | 9825 | 2598 | +0.1357 | [+0.1187, +0.1527] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_39|quintile/1 | dn | 18044 | 2850 | -0.0605 | [-0.0734, -0.0476] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_24|tercile/1 | up | 56030 | 2850 | +0.0661 | [+0.0532, +0.0790] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_9|quintile/5 | up | 7458 | 2681 | -0.1056 | [-0.1283, -0.0830] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_3|tercile/1 | dn | 27705 | 2850 | +0.0657 | [+0.0538, +0.0776] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_9|quintile/2 | up | 24789 | 2850 | -0.0568 | [-0.0632, -0.0504] | 0.0000 | True | True |
| amihud_3|quintile/2 | up | 106471 | 2850 | -0.0282 | [-0.0329, -0.0234] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_3|quintile/1 | up | 20196 | 2840 | +0.1083 | [+0.0886, +0.1280] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_24|tercile/3 | dn | 15999 | 2850 | -0.0581 | [-0.0669, -0.0493] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_3|tercile/3 | dn | 29710 | 2850 | -0.0450 | [-0.0527, -0.0373] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_39|tercile/1 | up | 55836 | 2850 | +0.0659 | [+0.0532, +0.0786] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & amihud_39|quintile/5 | up | 14431 | 2850 | -0.0793 | [-0.0961, -0.0626] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_6|tercile/1 | dn | 27662 | 2850 | +0.0831 | [+0.0684, +0.0977] | 0.0000 | True | True |
| amihud_63|quintile/2 | dn | 81991 | 2850 | -0.0256 | [-0.0314, -0.0198] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_6|quintile/1 | dn | 12900 | 2627 | +0.1342 | [+0.1102, +0.1582] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_9|tercile/3 | dn | 2915 | 2296 | -0.1080 | [-0.1229, -0.0930] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_9|quintile/1 | up | 19116 | 2791 | +0.1068 | [+0.0874, +0.1263] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_9|tercile/1 | dn | 27651 | 2850 | +0.0834 | [+0.0685, +0.0982] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_6|quintile/1 | up | 19803 | 2830 | +0.1097 | [+0.0883, +0.1310] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_9|quintile/1 | up | 26377 | 2850 | +0.1049 | [+0.0844, +0.1254] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_9|tercile/1 | up | 56190 | 2850 | +0.0674 | [+0.0540, +0.0808] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_233|quintile/4 | dn | 11015 | 2849 | -0.0728 | [-0.0871, -0.0585] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_144|quintile/4 | up | 33025 | 2850 | +0.0633 | [+0.0540, +0.0726] | 0.0000 | True | True |
| bb_width_9|quintile/4 & amihud_3|quintile/5 | dn | 25610 | 2850 | +0.0634 | [+0.0532, +0.0736] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_6|tercile/1 | dn | 27580 | 2850 | +0.0660 | [+0.0532, +0.0789] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_233|quintile/4 | dn | 26903 | 2850 | +0.0585 | [+0.0496, +0.0674] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_144|quintile/2 | up | 24545 | 2850 | -0.0558 | [-0.0642, -0.0475] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_24|tercile/1 | dn | 27227 | 2850 | +0.0829 | [+0.0677, +0.0980] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_39|tercile/1 | up | 56159 | 2850 | +0.0681 | [+0.0543, +0.0819] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_9|tercile/1 | dn | 27547 | 2850 | +0.0663 | [+0.0533, +0.0793] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_24|tercile/1 | up | 56163 | 2850 | +0.0678 | [+0.0545, +0.0811] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_39|tercile/1 | dn | 27485 | 2850 | +0.0659 | [+0.0529, +0.0790] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_39|tercile/1 | dn | 27061 | 2850 | +0.0835 | [+0.0682, +0.0989] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_9|tercile/3 | up | 3815 | 2296 | -0.1247 | [-0.1417, -0.1077] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_233|quintile/2 | up | 24418 | 2850 | -0.0573 | [-0.0660, -0.0486] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_9|quintile/1 | up | 19644 | 2828 | +0.1071 | [+0.0857, +0.1285] | 0.0000 | True | True |
| bb_width_9|quintile/4 & amihud_39|quintile/5 | dn | 24849 | 2850 | +0.0637 | [+0.0528, +0.0747] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_3|tercile/1 | dn | 46410 | 2850 | +0.0577 | [+0.0467, +0.0686] | 0.0000 | True | True |
| amihud_24|quintile/2 | dn | 82551 | 2850 | -0.0246 | [-0.0302, -0.0190] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_3|quintile/5 | dn | 14852 | 2850 | -0.0577 | [-0.0682, -0.0471] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_39|quintile/5 | dn | 14620 | 2850 | -0.0575 | [-0.0695, -0.0454] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_24|tercile/1 | dn | 27336 | 2850 | +0.0830 | [+0.0673, +0.0986] | 0.0000 | True | True |
| adx_144|quintile/5 | up | 122542 | 2850 | +0.0396 | [+0.0313, +0.0480] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_39|quintile/5 | dn | 7005 | 2817 | -0.0740 | [-0.0899, -0.0582] | 0.0000 | True | True |
| amihud_233|quintile/2 | dn | 80878 | 2850 | -0.0246 | [-0.0302, -0.0189] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_24|quintile/5 | up | 7458 | 2671 | -0.1016 | [-0.1234, -0.0798] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_39|tercile/1 | dn | 27196 | 2850 | +0.0838 | [+0.0678, +0.0997] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_24|tercile/1 | dn | 27430 | 2850 | +0.0653 | [+0.0521, +0.0784] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_24|quintile/1 | up | 26365 | 2850 | +0.1036 | [+0.0818, +0.1255] | 0.0000 | True | True |
| amihud_102|quintile/2 | dn | 82123 | 2850 | -0.0242 | [-0.0299, -0.0186] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_63|quintile/1 | dn | 12528 | 2504 | +0.1329 | [+0.1074, +0.1585] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_3|tercile/1 | dn | 46308 | 2850 | +0.0580 | [+0.0467, +0.0693] | 0.0000 | True | True |
| bb_width_9|quintile/4 & amihud_6|quintile/5 | dn | 25539 | 2850 | +0.0618 | [+0.0512, +0.0723] | 0.0000 | True | True |
| bb_width_9|quintile/4 & amihud_9|quintile/5 | dn | 25380 | 2850 | +0.0620 | [+0.0515, +0.0725] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_24|quintile/5 | dn | 14430 | 2850 | -0.0582 | [-0.0703, -0.0461] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_9|quintile/2 | dn | 15736 | 2845 | +0.0828 | [+0.0700, +0.0956] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_233|quintile/5 | up | 14817 | 2836 | +0.0976 | [+0.0841, +0.1112] | 0.0000 | True | True |
| bb_width_9|quintile/4 & amihud_24|quintile/5 | dn | 24904 | 2850 | +0.0627 | [+0.0516, +0.0738] | 0.0000 | True | True |
| adx_233|tercile/1 | up | 169026 | 2850 | -0.0281 | [-0.0346, -0.0216] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_3|quintile/5 | dn | 7272 | 2834 | -0.0740 | [-0.0881, -0.0598] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_144|quintile/5 | up | 15080 | 2832 | +0.0943 | [+0.0817, +0.1069] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_39|quintile/1 | up | 26446 | 2850 | +0.1034 | [+0.0801, +0.1268] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_9|tercile/3 | dn | 29181 | 2850 | -0.0440 | [-0.0521, -0.0359] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & amihud_39|quintile/5 | up | 7515 | 2679 | -0.0989 | [-0.1213, -0.0765] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_6|tercile/3 | dn | 29057 | 2850 | -0.0439 | [-0.0518, -0.0360] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_233|tercile/3 | up | 28347 | 2850 | +0.0652 | [+0.0564, +0.0740] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_9|quintile/2 | up | 20646 | 2849 | +0.0751 | [+0.0636, +0.0865] | 0.0000 | True | True |
| adx_144|tercile/3 | up | 198462 | 2850 | +0.0270 | [+0.0211, +0.0329] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_24|quintile/5 | dn | 7003 | 2826 | -0.0740 | [-0.0903, -0.0577] | 0.0000 | True | True |
| amihud_144|quintile/2 | dn | 81755 | 2850 | -0.0241 | [-0.0297, -0.0184] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_6|quintile/5 | dn | 14603 | 2850 | -0.0571 | [-0.0688, -0.0455] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_9|quintile/5 | dn | 14586 | 2850 | -0.0571 | [-0.0690, -0.0451] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & amihud_63|quintile/1 | up | 26480 | 2850 | +0.1023 | [+0.0790, +0.1255] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_39|quintile/5 | dn | 6979 | 2849 | -0.0780 | [-0.0956, -0.0604] | 0.0000 | True | True |
| amihud_39|quintile/2 | dn | 82414 | 2850 | -0.0247 | [-0.0307, -0.0187] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_6|quintile/5 | dn | 7081 | 2829 | -0.0735 | [-0.0888, -0.0583] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_3|quintile/2 | up | 20592 | 2850 | +0.0704 | [+0.0620, +0.0788] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_24|quintile/1 | up | 18691 | 2753 | +0.0993 | [+0.0797, +0.1190] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_9|quintile/5 | dn | 7081 | 2828 | -0.0716 | [-0.0865, -0.0567] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_9|tercile/1 | dn | 46026 | 2850 | +0.0561 | [+0.0443, +0.0679] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_3|quintile/1 | up | 14932 | 2698 | +0.1260 | [+0.1031, +0.1490] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_6|tercile/1 | dn | 45999 | 2850 | +0.0556 | [+0.0440, +0.0671] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_39|quintile/1 | up | 18536 | 2739 | +0.0991 | [+0.0796, +0.1187] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_39|tercile/3 | dn | 30931 | 2850 | -0.0413 | [-0.0493, -0.0332] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_144|tercile/3 | up | 42516 | 2850 | +0.0543 | [+0.0458, +0.0629] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_233|quintile/4 | up | 5823 | 2604 | -0.1042 | [-0.1272, -0.0812] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_24|quintile/5 | dn | 7022 | 2846 | -0.0772 | [-0.0959, -0.0585] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_3|tercile/3 | up | 39666 | 2850 | -0.0477 | [-0.0577, -0.0377] | 0.0000 | True | True |
| bb_width_144|quintile/2 & bb_width_233|quintile/2 | up | 37584 | 2850 | -0.0450 | [-0.0545, -0.0356] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_6|tercile/1 | dn | 45742 | 2850 | +0.0561 | [+0.0443, +0.0679] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_9|tercile/1 | dn | 45628 | 2850 | +0.0564 | [+0.0441, +0.0686] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_3|tercile/1 | dn | 23188 | 2850 | +0.0578 | [+0.0499, +0.0658] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_3|tercile/3 | up | 19972 | 2849 | -0.0600 | [-0.0697, -0.0503] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_3|quintile/1 | up | 32594 | 2850 | +0.0705 | [+0.0559, +0.0852] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_24|tercile/3 | dn | 30507 | 2850 | -0.0414 | [-0.0496, -0.0332] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_63|quintile/1 | up | 18378 | 2711 | +0.0978 | [+0.0778, +0.1177] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_6|quintile/1 | up | 32314 | 2850 | +0.0714 | [+0.0562, +0.0866] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_24|tercile/1 | dn | 45908 | 2850 | +0.0561 | [+0.0438, +0.0684] | 0.0000 | True | True |
| adx_233|quintile/5 | up | 120096 | 2850 | +0.0391 | [+0.0300, +0.0482] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_39|tercile/1 | dn | 45809 | 2850 | +0.0564 | [+0.0440, +0.0688] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_233|quintile/1 | dn | 9643 | 2836 | -0.0653 | [-0.0751, -0.0555] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_3|quintile/5 | dn | 7252 | 2838 | -0.0754 | [-0.0928, -0.0581] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_144|quintile/2 | up | 15883 | 2806 | +0.0815 | [+0.0646, +0.0985] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_233|quintile/1 | dn | 7433 | 2832 | -0.0718 | [-0.0829, -0.0606] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_63|quintile/1 | up | 18786 | 2767 | +0.1028 | [+0.0798, +0.1257] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_6|quintile/5 | dn | 7108 | 2840 | -0.0758 | [-0.0942, -0.0575] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_24|quintile/1 | up | 19243 | 2830 | +0.1024 | [+0.0793, +0.1254] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_3|quintile/1 | dn | 7903 | 2598 | +0.1161 | [+0.0999, +0.1324] | 0.0000 | True | True |
| amihud_9|quintile/2 | dn | 83207 | 2850 | -0.0229 | [-0.0285, -0.0174] | 0.0000 | True | False |
| bb_width_144|quintile/1 & amihud_9|quintile/5 | dn | 7102 | 2838 | -0.0757 | [-0.0940, -0.0575] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_6|quintile/1 | up | 14654 | 2627 | +0.1249 | [+0.0997, +0.1501] | 0.0000 | True | True |
| bb_width_3|quintile/4 | dn | 96877 | 2850 | +0.0243 | [+0.0213, +0.0273] | 0.0000 | True | True |
| adx_144|tercile/1 | up | 174308 | 2850 | -0.0246 | [-0.0306, -0.0186] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_3|quintile/5 | dn | 24946 | 2850 | +0.0552 | [+0.0435, +0.0669] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_233|quintile/5 | up | 12799 | 2796 | +0.0994 | [+0.0842, +0.1147] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_3|quintile/1 | up | 16519 | 2842 | +0.0767 | [+0.0677, +0.0858] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_144|quintile/5 | dn | 17686 | 2848 | +0.0735 | [+0.0618, +0.0853] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_9|tercile/1 | dn | 14631 | 2822 | +0.0808 | [+0.0662, +0.0953] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_39|quintile/1 | up | 18990 | 2822 | +0.1010 | [+0.0785, +0.1236] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_3|tercile/3 | up | 40182 | 2850 | -0.0450 | [-0.0549, -0.0351] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_3|quintile/5 | dn | 23675 | 2850 | +0.0583 | [+0.0453, +0.0712] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_24|tercile/1 | dn | 45328 | 2850 | +0.0557 | [+0.0431, +0.0683] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_9|quintile/5 | dn | 23738 | 2850 | +0.0578 | [+0.0445, +0.0711] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_6|quintile/5 | dn | 23760 | 2850 | +0.0581 | [+0.0448, +0.0714] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_9|quintile/1 | up | 32159 | 2850 | +0.0696 | [+0.0541, +0.0851] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_9|quintile/5 | dn | 24981 | 2850 | +0.0534 | [+0.0414, +0.0655] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_9|quintile/1 | up | 14511 | 2603 | +0.1232 | [+0.0967, +0.1497] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_6|quintile/5 | dn | 24947 | 2850 | +0.0538 | [+0.0418, +0.0659] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_39|quintile/5 | dn | 23768 | 2850 | +0.0587 | [+0.0450, +0.0724] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_9|quintile/2 | up | 6929 | 2228 | +0.1330 | [+0.1130, +0.1531] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_39|tercile/3 | up | 39334 | 2850 | -0.0452 | [-0.0555, -0.0348] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_144|quintile/1 | dn | 10044 | 2839 | -0.0622 | [-0.0722, -0.0522] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_3|tercile/3 | dn | 12516 | 2849 | -0.0582 | [-0.0667, -0.0497] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_24|quintile/5 | dn | 23756 | 2850 | +0.0572 | [+0.0436, +0.0707] | 0.0000 | True | True |
| adx_144|quintile/2 | up | 104619 | 2850 | -0.0239 | [-0.0291, -0.0186] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_6|tercile/3 | up | 39534 | 2850 | -0.0456 | [-0.0559, -0.0353] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_63|quintile/1 | up | 14277 | 2504 | +0.1221 | [+0.0960, +0.1482] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_233|quintile/5 | dn | 17325 | 2848 | +0.0746 | [+0.0618, +0.0873] | 0.0000 | True | True |
| amihud_6|quintile/2 | dn | 83401 | 2850 | -0.0224 | [-0.0277, -0.0171] | 0.0000 | True | False |
| bb_width_233|tercile/3 & amihud_39|tercile/1 | dn | 45228 | 2850 | +0.0556 | [+0.0429, +0.0682] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_9|tercile/1 | up | 20464 | 2845 | +0.0716 | [+0.0594, +0.0839] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_144|tercile/3 | up | 28255 | 2850 | +0.0572 | [+0.0485, +0.0659] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_144|quintile/5 | up | 12937 | 2810 | +0.0914 | [+0.0777, +0.1050] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_24|quintile/5 | dn | 24965 | 2850 | +0.0513 | [+0.0393, +0.0634] | 0.0000 | True | True |
| adx_233|tercile/3 | up | 194238 | 2850 | +0.0259 | [+0.0195, +0.0324] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_3|quintile/5 | dn | 15549 | 2850 | -0.0500 | [-0.0613, -0.0388] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_9|tercile/3 | up | 39553 | 2850 | -0.0452 | [-0.0557, -0.0347] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_39|tercile/3 | up | 39855 | 2850 | -0.0433 | [-0.0535, -0.0332] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_6|tercile/3 | up | 19678 | 2850 | -0.0571 | [-0.0671, -0.0470] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_24|tercile/3 | up | 39545 | 2850 | -0.0445 | [-0.0550, -0.0340] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_233|quintile/1 | up | 10108 | 2832 | -0.0739 | [-0.0866, -0.0611] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_6|tercile/3 | up | 40028 | 2850 | -0.0431 | [-0.0533, -0.0329] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_144|quintile/1 | dn | 7799 | 2832 | -0.0658 | [-0.0777, -0.0539] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_3|quintile/2 | dn | 16311 | 2850 | +0.0602 | [+0.0517, +0.0688] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_144|quintile/5 | dn | 11837 | 2832 | +0.0802 | [+0.0686, +0.0918] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_3|tercile/1 | dn | 26748 | 2849 | +0.0657 | [+0.0526, +0.0789] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_24|tercile/3 | up | 40105 | 2850 | -0.0427 | [-0.0527, -0.0326] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_9|quintile/4 | dn | 10423 | 2849 | -0.0583 | [-0.0691, -0.0475] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_9|tercile/1 | dn | 25789 | 2850 | +0.0673 | [+0.0532, +0.0814] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_39|quintile/1 | up | 14314 | 2537 | +0.1170 | [+0.0915, +0.1424] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_9|quintile/4 | up | 13877 | 2849 | -0.0627 | [-0.0731, -0.0524] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_39|quintile/5 | dn | 25028 | 2850 | +0.0507 | [+0.0385, +0.0628] | 0.0000 | True | True |
| adx_233|quintile/1 | up | 100707 | 2850 | -0.0313 | [-0.0400, -0.0226] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_144|tercile/3 | dn | 22530 | 2850 | +0.0529 | [+0.0449, +0.0609] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_24|tercile/1 | dn | 25928 | 2850 | +0.0674 | [+0.0535, +0.0814] | 0.0000 | True | True |
| bb_width_144|quintile/4 & bb_width_233|quintile/4 | up | 52698 | 2850 | +0.0405 | [+0.0306, +0.0504] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_233|quintile/5 | dn | 11604 | 2836 | +0.0817 | [+0.0690, +0.0944] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & amihud_24|quintile/1 | up | 14331 | 2575 | +0.1152 | [+0.0889, +0.1415] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_9|tercile/3 | up | 19922 | 2850 | -0.0554 | [-0.0657, -0.0450] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_3|quintile/1 | up | 32795 | 2849 | +0.0670 | [+0.0519, +0.0821] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_9|tercile/3 | up | 40096 | 2850 | -0.0423 | [-0.0523, -0.0323] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_39|tercile/1 | dn | 25842 | 2850 | +0.0671 | [+0.0533, +0.0809] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_233|tercile/1 | dn | 16094 | 2850 | -0.0493 | [-0.0582, -0.0405] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_6|tercile/1 | dn | 25900 | 2850 | +0.0663 | [+0.0523, +0.0803] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_144|tercile/3 | dn | 33649 | 2850 | +0.0451 | [+0.0373, +0.0529] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_6|quintile/5 | dn | 15420 | 2850 | -0.0482 | [-0.0600, -0.0363] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_63|quintile/1 | dn | 15357 | 2850 | +0.0752 | [+0.0570, +0.0935] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_3|quintile/5 | up | 5717 | 2490 | -0.0961 | [-0.1086, -0.0835] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_24|quintile/1 | up | 31950 | 2850 | +0.0651 | [+0.0490, +0.0812] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_144|quintile/2 | dn | 12658 | 2806 | +0.0701 | [+0.0554, +0.0848] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_39|quintile/1 | dn | 15176 | 2850 | +0.0736 | [+0.0551, +0.0921] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_9|quintile/5 | dn | 15445 | 2850 | -0.0473 | [-0.0592, -0.0353] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_39|quintile/1 | up | 31960 | 2850 | +0.0645 | [+0.0483, +0.0808] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_233|tercile/3 | up | 24143 | 2850 | +0.0619 | [+0.0523, +0.0716] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_6|quintile/1 | up | 32425 | 2850 | +0.0661 | [+0.0510, +0.0812] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_144|tercile/1 | dn | 16642 | 2850 | -0.0461 | [-0.0548, -0.0375] | 0.0000 | True | True |
| amihud_3|quintile/2 | dn | 83820 | 2850 | -0.0209 | [-0.0259, -0.0160] | 0.0000 | True | False |
| atr_pct_34|tercile/1 & bb_width_3|quintile/5 | dn | 4184 | 2490 | -0.0817 | [-0.0933, -0.0701] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_3|tercile/3 | up | 16908 | 2849 | -0.0588 | [-0.0675, -0.0501] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_233|quintile/2 | dn | 11615 | 2811 | +0.0785 | [+0.0595, +0.0976] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_3|quintile/1 | dn | 14873 | 2848 | +0.0698 | [+0.0537, +0.0859] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_144|quintile/5 | up | 12151 | 2773 | +0.0883 | [+0.0734, +0.1031] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_39|quintile/5 | dn | 15533 | 2850 | -0.0460 | [-0.0583, -0.0338] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_3|quintile/1 | up | 18236 | 2848 | +0.0732 | [+0.0557, +0.0908] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_63|quintile/1 | up | 31731 | 2850 | +0.0628 | [+0.0470, +0.0787] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_24|quintile/5 | dn | 15430 | 2850 | -0.0463 | [-0.0584, -0.0342] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_24|tercile/3 | up | 21544 | 2850 | -0.0511 | [-0.0614, -0.0409] | 0.0000 | True | True |
| adx_144|tercile/1 | dn | 135035 | 2850 | -0.0209 | [-0.0266, -0.0152] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_9|quintile/1 | dn | 14770 | 2849 | +0.0699 | [+0.0530, +0.0868] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_9|quintile/1 | up | 32300 | 2850 | +0.0647 | [+0.0491, +0.0803] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_3|tercile/1 | dn | 44080 | 2850 | +0.0461 | [+0.0352, +0.0570] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_3|quintile/1 | dn | 15862 | 2825 | +0.0769 | [+0.0600, +0.0938] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_6|quintile/1 | dn | 14736 | 2849 | +0.0689 | [+0.0522, +0.0856] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_233|tercile/3 | up | 25415 | 2850 | +0.0579 | [+0.0463, +0.0695] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_233|quintile/4 | up | 14410 | 2849 | -0.0672 | [-0.0857, -0.0488] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_24|quintile/1 | dn | 14860 | 2849 | +0.0699 | [+0.0522, +0.0877] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_9|tercile/3 | up | 13086 | 2838 | -0.0635 | [-0.0761, -0.0509] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_6|quintile/1 | up | 18154 | 2849 | +0.0742 | [+0.0551, +0.0932] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_24|quintile/1 | dn | 15379 | 2753 | +0.0777 | [+0.0586, +0.0968] | 0.0000 | True | True |
| hurst_233|tercile/1 | dn | 138932 | 2850 | -0.0148 | [-0.0183, -0.0114] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_233|quintile/5 | up | 11615 | 2765 | +0.0862 | [+0.0707, +0.1016] | 0.0000 | True | True |
| adx_233|tercile/1 | dn | 131769 | 2850 | -0.0212 | [-0.0271, -0.0152] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_233|tercile/1 | dn | 20953 | 2849 | -0.0417 | [-0.0493, -0.0342] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_9|quintile/2 | dn | 16160 | 2849 | +0.0566 | [+0.0460, +0.0672] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_39|quintile/1 | dn | 15232 | 2739 | +0.0775 | [+0.0591, +0.0959] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_9|tercile/1 | dn | 43033 | 2850 | +0.0465 | [+0.0348, +0.0583] | 0.0000 | True | True |
| adx_233|quintile/2 | up | 102598 | 2850 | -0.0231 | [-0.0293, -0.0168] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_3|quintile/1 | dn | 16120 | 2840 | +0.0756 | [+0.0580, +0.0932] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_233|quintile/1 | up | 13076 | 2836 | -0.0645 | [-0.0765, -0.0524] | 0.0000 | True | True |
| amihud_6|quintile/4 | up | 120865 | 2850 | +0.0212 | [+0.0162, +0.0261] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_63|quintile/1 | dn | 14881 | 2711 | +0.0772 | [+0.0585, +0.0959] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_144|quintile/1 | up | 10723 | 2832 | -0.0642 | [-0.0766, -0.0519] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_144|tercile/3 | dn | 3371 | 2255 | -0.0798 | [-0.0980, -0.0617] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_6|tercile/1 | dn | 43034 | 2850 | +0.0458 | [+0.0341, +0.0575] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_24|tercile/1 | dn | 43663 | 2850 | +0.0465 | [+0.0350, +0.0580] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_9|quintile/1 | up | 18098 | 2849 | +0.0733 | [+0.0538, +0.0929] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_39|tercile/1 | dn | 43780 | 2850 | +0.0467 | [+0.0349, +0.0585] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_39|tercile/3 | up | 21961 | 2850 | -0.0492 | [-0.0597, -0.0387] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_24|quintile/1 | up | 18288 | 2849 | +0.0743 | [+0.0537, +0.0949] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_39|tercile/1 | dn | 25669 | 2850 | +0.0569 | [+0.0455, +0.0683] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_9|tercile/1 | up | 5720 | 1990 | +0.1250 | [+0.1046, +0.1454] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_144|tercile/1 | dn | 21635 | 2850 | -0.0401 | [-0.0473, -0.0328] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_9|tercile/1 | dn | 24623 | 2850 | +0.0572 | [+0.0453, +0.0691] | 0.0000 | True | True |
| amihud_9|quintile/4 | up | 120721 | 2850 | +0.0208 | [+0.0156, +0.0261] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_233|tercile/3 | dn | 21989 | 2850 | +0.0501 | [+0.0407, +0.0594] | 0.0000 | True | True |
| adx_144|quintile/1 | dn | 79820 | 2850 | -0.0254 | [-0.0330, -0.0179] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_24|tercile/1 | dn | 25489 | 2850 | +0.0563 | [+0.0448, +0.0678] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_6|quintile/1 | dn | 15583 | 2797 | +0.0740 | [+0.0565, +0.0916] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_9|quintile/2 | dn | 5342 | 2228 | +0.1103 | [+0.0918, +0.1287] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_39|quintile/1 | up | 18302 | 2850 | +0.0721 | [+0.0522, +0.0920] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_233|quintile/2 | dn | 15145 | 2850 | +0.0562 | [+0.0419, +0.0706] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_144|tercile/3 | up | 11576 | 2792 | -0.0670 | [-0.0847, -0.0492] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_144|quintile/4 | up | 13415 | 2841 | -0.0562 | [-0.0702, -0.0422] | 0.0000 | True | True |
| bb_width_144|quintile/5 & amihud_9|quintile/1 | dn | 15485 | 2791 | +0.0736 | [+0.0558, +0.0915] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_3|tercile/3 | up | 40046 | 2850 | -0.0380 | [-0.0466, -0.0294] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_6|tercile/1 | dn | 23776 | 2850 | +0.0569 | [+0.0453, +0.0686] | 0.0000 | True | True |
| di_spread_233|quintile/4 | up | 105529 | 2850 | -0.0236 | [-0.0296, -0.0175] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_9|tercile/3 | dn | 9735 | 2838 | -0.0561 | [-0.0682, -0.0439] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_144|quintile/2 | up | 20294 | 2841 | +0.0587 | [+0.0437, +0.0738] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_9|tercile/1 | dn | 16213 | 2845 | +0.0570 | [+0.0452, +0.0689] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_144|quintile/4 | dn | 11267 | 2804 | -0.0566 | [-0.0724, -0.0408] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_144|tercile/3 | up | 24412 | 2849 | +0.0539 | [+0.0442, +0.0635] | 0.0000 | True | True |
| amihud_3|quintile/4 | up | 120588 | 2850 | +0.0202 | [+0.0159, +0.0246] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_233|tercile/3 | dn | 32725 | 2850 | +0.0429 | [+0.0338, +0.0520] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_233|tercile/3 | dn | 9056 | 2811 | -0.0593 | [-0.0750, -0.0435] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_24|quintile/1 | up | 32128 | 2850 | +0.0611 | [+0.0451, +0.0770] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_9|quintile/1 | dn | 15743 | 2828 | +0.0729 | [+0.0540, +0.0918] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_233|quintile/2 | up | 14583 | 2811 | +0.0736 | [+0.0548, +0.0924] | 0.0000 | True | False |
| bb_width_144|tercile/3 & amihud_3|quintile/1 | dn | 26450 | 2850 | +0.0512 | [+0.0385, +0.0639] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_6|quintile/1 | dn | 15803 | 2830 | +0.0719 | [+0.0541, +0.0898] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_144|quintile/2 | dn | 15898 | 2841 | +0.0541 | [+0.0394, +0.0689] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & amihud_63|quintile/1 | up | 18403 | 2850 | +0.0698 | [+0.0500, +0.0897] | 0.0000 | True | True |
| bb_width_9|tercile/3 & bb_width_144|quintile/1 | dn | 7895 | 2806 | -0.0570 | [-0.0698, -0.0443] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_3|tercile/1 | dn | 21292 | 2847 | +0.0587 | [+0.0459, +0.0715] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_39|quintile/1 | up | 32154 | 2850 | +0.0594 | [+0.0432, +0.0755] | 0.0000 | True | True |
| bb_width_9|tercile/3 & bb_width_233|quintile/1 | up | 10341 | 2797 | -0.0644 | [-0.0773, -0.0515] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_3|tercile/3 | up | 23257 | 2850 | -0.0457 | [-0.0584, -0.0331] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_233|tercile/3 | dn | 3175 | 2193 | -0.0878 | [-0.1119, -0.0637] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_144|tercile/1 | up | 11712 | 2646 | +0.0726 | [+0.0544, +0.0907] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_24|quintile/1 | dn | 15569 | 2830 | +0.0733 | [+0.0536, +0.0930] | 0.0000 | True | True |
| amihud_9|quintile/4 | dn | 94949 | 2850 | +0.0188 | [+0.0135, +0.0242] | 0.0000 | True | False |
| bb_width_3|quintile/1 & bb_width_144|quintile/5 | dn | 10219 | 2810 | +0.0728 | [+0.0598, +0.0858] | 0.0000 | True | True |
| bb_width_9|tercile/3 & bb_width_233|quintile/1 | dn | 7737 | 2797 | -0.0588 | [-0.0711, -0.0465] | 0.0000 | True | True |
| amihud_6|quintile/4 | dn | 94894 | 2850 | +0.0185 | [+0.0135, +0.0235] | 0.0000 | True | False |
| bb_width_9|quintile/5 & amihud_3|tercile/1 | up | 32162 | 2849 | +0.0578 | [+0.0450, +0.0705] | 0.0000 | True | True |
| bb_width_233|quintile/5 & amihud_39|quintile/1 | dn | 15412 | 2822 | +0.0736 | [+0.0534, +0.0937] | 0.0000 | True | True |
| adx_233|quintile/1 | dn | 78546 | 2850 | -0.0235 | [-0.0308, -0.0161] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_63|quintile/1 | up | 31964 | 2850 | +0.0581 | [+0.0417, +0.0744] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_39|tercile/3 | up | 22770 | 2850 | -0.0449 | [-0.0587, -0.0310] | 0.0000 | True | True |
| amihud_24|quintile/4 | dn | 94847 | 2850 | +0.0188 | [+0.0131, +0.0245] | 0.0000 | True | False |
| adx_144|quintile/1 | up | 104784 | 2850 | -0.0245 | [-0.0321, -0.0168] | 0.0000 | True | True |
| amihud_3|quintile/4 | dn | 94846 | 2850 | +0.0183 | [+0.0137, +0.0229] | 0.0000 | True | False |
| hurst_233|quintile/1 | dn | 82523 | 2850 | -0.0182 | [-0.0230, -0.0133] | 0.0000 | True | True |
| amihud_39|quintile/4 | up | 119929 | 2850 | +0.0193 | [+0.0137, +0.0248] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_3|quintile/5 | dn | 8795 | 2848 | -0.0517 | [-0.0650, -0.0385] | 0.0000 | True | True |
| di_spread_233|quintile/4 | dn | 81855 | 2850 | -0.0209 | [-0.0267, -0.0151] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_3|quintile/1 | dn | 12849 | 2842 | +0.0573 | [+0.0479, +0.0667] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_63|quintile/1 | dn | 26020 | 2850 | +0.0513 | [+0.0371, +0.0655] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_39|tercile/1 | up | 31089 | 2850 | +0.0584 | [+0.0451, +0.0717] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_144|tercile/3 | up | 25188 | 2850 | +0.0480 | [+0.0376, +0.0583] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_9|tercile/3 | up | 23042 | 2850 | -0.0439 | [-0.0570, -0.0307] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_9|tercile/1 | dn | 4438 | 1990 | +0.1112 | [+0.0898, +0.1325] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_144|tercile/3 | up | 4392 | 2255 | -0.0897 | [-0.1162, -0.0631] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_24|tercile/1 | up | 31132 | 2850 | +0.0577 | [+0.0444, +0.0709] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_6|tercile/3 | up | 39354 | 2850 | -0.0356 | [-0.0445, -0.0267] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_233|quintile/5 | dn | 9950 | 2796 | +0.0714 | [+0.0572, +0.0855] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_6|tercile/3 | up | 23117 | 2850 | -0.0435 | [-0.0568, -0.0301] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_24|quintile/1 | dn | 26275 | 2850 | +0.0497 | [+0.0351, +0.0642] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_6|quintile/5 | dn | 8665 | 2847 | -0.0511 | [-0.0650, -0.0373] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_9|quintile/5 | dn | 8644 | 2846 | -0.0510 | [-0.0650, -0.0370] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_39|quintile/1 | dn | 26282 | 2850 | +0.0503 | [+0.0359, +0.0646] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_6|quintile/1 | dn | 26181 | 2850 | +0.0482 | [+0.0352, +0.0612] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_3|quintile/1 | dn | 26425 | 2849 | +0.0485 | [+0.0353, +0.0618] | 0.0000 | True | True |
| adx_144|tercile/3 | dn | 154113 | 2850 | +0.0190 | [+0.0129, +0.0251] | 0.0000 | True | True |
| amihud_24|quintile/4 | up | 119881 | 2850 | +0.0186 | [+0.0131, +0.0242] | 0.0000 | True | True |
| bb_width_144|tercile/3 & amihud_9|quintile/1 | dn | 26166 | 2850 | +0.0480 | [+0.0348, +0.0613] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_6|tercile/1 | up | 30994 | 2850 | +0.0561 | [+0.0425, +0.0696] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_9|tercile/3 | up | 39607 | 2850 | -0.0346 | [-0.0433, -0.0259] | 0.0000 | True | True |
| adx_144|quintile/5 | dn | 94408 | 2850 | +0.0260 | [+0.0174, +0.0347] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_9|tercile/1 | up | 30701 | 2850 | +0.0551 | [+0.0417, +0.0685] | 0.0000 | True | True |
| amihud_102|quintile/4 | up | 118825 | 2850 | +0.0177 | [+0.0125, +0.0230] | 0.0000 | True | True |
| di_spread_233|tercile/2 | up | 180549 | 2850 | -0.0133 | [-0.0171, -0.0095] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_24|tercile/3 | up | 22987 | 2850 | -0.0424 | [-0.0563, -0.0285] | 0.0000 | True | True |
| amihud_63|quintile/4 | up | 119343 | 2850 | +0.0182 | [+0.0125, +0.0238] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_3|quintile/1 | dn | 15021 | 2835 | +0.0609 | [+0.0455, +0.0762] | 0.0000 | True | True |
| bb_width_9|tercile/1 & bb_width_144|quintile/5 | up | 13014 | 2782 | +0.0688 | [+0.0521, +0.0855] | 0.0000 | True | True |
| hurst_233|tercile/3 | dn | 151584 | 2850 | +0.0126 | [+0.0092, +0.0161] | 0.0000 | True | True |
| amihud_144|quintile/4 | up | 118312 | 2850 | +0.0177 | [+0.0123, +0.0231] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_3|quintile/5 | up | 1749 | 1364 | -0.1210 | [-0.1405, -0.1014] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_3|quintile/5 | dn | 1282 | 1364 | -0.1069 | [-0.1251, -0.0886] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_9|quintile/5 | dn | 2735 | 2117 | -0.0794 | [-0.0962, -0.0626] | 0.0000 | True | True |
| amihud_39|quintile/4 | dn | 94120 | 2850 | +0.0168 | [+0.0113, +0.0222] | 0.0000 | True | False |
| bb_width_233|quintile/5 & amihud_63|quintile/1 | dn | 14938 | 2767 | +0.0675 | [+0.0460, +0.0890] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_144|tercile/1 | dn | 9180 | 2646 | +0.0634 | [+0.0469, +0.0799] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_9|quintile/1 | dn | 14283 | 2813 | +0.0637 | [+0.0476, +0.0799] | 0.0000 | True | True |
| amihud_144|tercile/2 | up | 182901 | 2850 | -0.0117 | [-0.0155, -0.0080] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_3|quintile/5 | up | 10446 | 2834 | -0.0563 | [-0.0729, -0.0398] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_144|quintile/1 | up | 14025 | 2839 | -0.0528 | [-0.0645, -0.0411] | 0.0000 | True | True |
| amihud_63|quintile/4 | dn | 93784 | 2850 | +0.0164 | [+0.0112, +0.0216] | 0.0000 | True | False |
| bb_width_3|tercile/2 | dn | 143665 | 2850 | -0.0120 | [-0.0144, -0.0096] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_6|quintile/5 | dn | 7546 | 2810 | -0.0536 | [-0.0655, -0.0417] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_233|tercile/3 | up | 4314 | 2193 | -0.0858 | [-0.1121, -0.0595] | 0.0000 | True | True |
| bb_width_9|tercile/1 & bb_width_233|quintile/5 | up | 12446 | 2794 | +0.0715 | [+0.0528, +0.0901] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_9|quintile/5 | up | 3774 | 2117 | -0.0884 | [-0.1068, -0.0700] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_39|quintile/1 | dn | 26338 | 2850 | +0.0472 | [+0.0327, +0.0617] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_144|tercile/1 | up | 17326 | 2821 | +0.0536 | [+0.0368, +0.0705] | 0.0000 | True | True |
| amihud_233|tercile/2 | up | 181251 | 2850 | -0.0118 | [-0.0158, -0.0079] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_24|quintile/1 | dn | 14440 | 2821 | +0.0625 | [+0.0465, +0.0785] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_3|quintile/5 | up | 10745 | 2838 | -0.0558 | [-0.0732, -0.0385] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_6|quintile/1 | dn | 26173 | 2850 | +0.0459 | [+0.0322, +0.0596] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_24|tercile/1 | up | 30800 | 2850 | +0.0491 | [+0.0382, +0.0600] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_63|quintile/1 | dn | 26098 | 2850 | +0.0463 | [+0.0316, +0.0611] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_24|quintile/5 | dn | 8721 | 2849 | -0.0463 | [-0.0598, -0.0328] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_39|tercile/1 | up | 30938 | 2850 | +0.0489 | [+0.0381, +0.0597] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_39|tercile/3 | up | 41762 | 2850 | -0.0314 | [-0.0403, -0.0226] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_24|tercile/3 | up | 41363 | 2850 | -0.0313 | [-0.0399, -0.0227] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_6|quintile/1 | dn | 14348 | 2813 | +0.0610 | [+0.0450, +0.0771] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_9|quintile/1 | dn | 26152 | 2850 | +0.0455 | [+0.0314, +0.0596] | 0.0000 | True | True |
| bb_pct_b_55|tercile/3 | up | 178116 | 2850 | -0.0245 | [-0.0326, -0.0164] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_6|tercile/1 | up | 28774 | 2850 | +0.0494 | [+0.0383, +0.0605] | 0.0000 | True | True |
| di_spread_233|quintile/1 | dn | 96293 | 2850 | +0.0312 | [+0.0201, +0.0424] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_3|quintile/5 | dn | 7830 | 2817 | -0.0516 | [-0.0628, -0.0403] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_39|quintile/1 | dn | 14469 | 2821 | +0.0611 | [+0.0450, +0.0772] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_9|quintile/5 | up | 17444 | 2838 | +0.0551 | [+0.0464, +0.0638] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_6|quintile/5 | up | 10354 | 2829 | -0.0539 | [-0.0712, -0.0366] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_144|tercile/3 | dn | 19234 | 2849 | +0.0414 | [+0.0334, +0.0494] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_9|quintile/5 | dn | 7742 | 2818 | -0.0509 | [-0.0629, -0.0389] | 0.0000 | True | True |
| entropy_144|tercile/2 | up | 183192 | 2850 | -0.0115 | [-0.0152, -0.0077] | 0.0000 | True | True |
| bb_width_233|tercile/3 & amihud_24|quintile/1 | dn | 26277 | 2850 | +0.0458 | [+0.0315, +0.0602] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_9|tercile/1 | up | 29634 | 2850 | +0.0484 | [+0.0374, +0.0594] | 0.0000 | True | True |
| hurst_233|quintile/5 | dn | 91946 | 2850 | +0.0168 | [+0.0122, +0.0214] | 0.0000 | True | True |
| amihud_102|quintile/4 | dn | 93155 | 2850 | +0.0155 | [+0.0105, +0.0205] | 0.0000 | True | False |
| atr_pct_34|tercile/3 & bb_width_9|quintile/1 | dn | 5210 | 2217 | +0.0855 | [+0.0675, +0.1035] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_3|tercile/1 | up | 53563 | 2850 | +0.0374 | [+0.0271, +0.0477] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_9|tercile/1 | dn | 41900 | 2850 | +0.0339 | [+0.0242, +0.0435] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_24|quintile/5 | dn | 8613 | 2832 | -0.0478 | [-0.0605, -0.0351] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_3|tercile/1 | dn | 36732 | 2850 | +0.0365 | [+0.0262, +0.0469] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_9|quintile/1 | up | 6516 | 2217 | +0.0869 | [+0.0678, +0.1061] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_3|quintile/5 | dn | 15751 | 2850 | -0.0370 | [-0.0471, -0.0269] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_6|tercile/1 | dn | 40604 | 2850 | +0.0339 | [+0.0242, +0.0436] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_6|quintile/5 | dn | 15328 | 2850 | -0.0371 | [-0.0484, -0.0259] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_233|quintile/2 | up | 19103 | 2850 | +0.0504 | [+0.0336, +0.0671] | 0.0000 | True | False |
| bb_width_9|quintile/5 & amihud_63|quintile/1 | dn | 14397 | 2825 | +0.0583 | [+0.0428, +0.0738] | 0.0000 | True | True |
| bb_width_9|tercile/3 & bb_width_144|tercile/1 | dn | 18155 | 2845 | -0.0343 | [-0.0428, -0.0257] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_3|quintile/1 | dn | 24724 | 2850 | +0.0420 | [+0.0286, +0.0554] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_39|tercile/1 | up | 53248 | 2850 | +0.0380 | [+0.0269, +0.0492] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_9|quintile/1 | dn | 23936 | 2850 | +0.0440 | [+0.0298, +0.0583] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_233|tercile/1 | up | 22183 | 2850 | -0.0380 | [-0.0473, -0.0287] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_233|tercile/1 | up | 28387 | 2849 | -0.0359 | [-0.0445, -0.0273] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_24|tercile/1 | up | 53108 | 2850 | +0.0376 | [+0.0264, +0.0487] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_9|quintile/5 | up | 10307 | 2828 | -0.0521 | [-0.0697, -0.0345] | 0.0000 | True | True |
| bb_width_9|tercile/3 & bb_width_144|quintile/1 | up | 10816 | 2806 | -0.0519 | [-0.0649, -0.0389] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_3|tercile/1 | up | 25554 | 2847 | +0.0503 | [+0.0384, +0.0622] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_233|tercile/1 | dn | 8895 | 2613 | +0.0660 | [+0.0422, +0.0898] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_9|quintile/5 | dn | 15507 | 2850 | -0.0361 | [-0.0474, -0.0248] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_39|tercile/1 | dn | 43645 | 2850 | +0.0327 | [+0.0234, +0.0421] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_24|tercile/1 | dn | 43288 | 2850 | +0.0325 | [+0.0232, +0.0419] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_144|tercile/1 | dn | 13359 | 2821 | +0.0472 | [+0.0313, +0.0632] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_6|tercile/1 | up | 52249 | 2850 | +0.0369 | [+0.0258, +0.0480] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_39|quintile/5 | dn | 8783 | 2849 | -0.0431 | [-0.0570, -0.0293] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_39|tercile/3 | dn | 22649 | 2850 | -0.0271 | [-0.0360, -0.0182] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_9|tercile/3 | dn | 22687 | 2850 | -0.0273 | [-0.0357, -0.0189] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_233|quintile/5 | dn | 8721 | 2765 | +0.0607 | [+0.0444, +0.0770] | 0.0000 | True | True |
| adx_233|quintile/5 | dn | 92206 | 2850 | +0.0241 | [+0.0152, +0.0330] | 0.0000 | True | False |
| di_spread_233|tercile/2 | dn | 140581 | 2850 | -0.0109 | [-0.0145, -0.0073] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_24|quintile/1 | dn | 24509 | 2850 | +0.0428 | [+0.0283, +0.0572] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_144|quintile/5 | dn | 9137 | 2773 | +0.0592 | [+0.0445, +0.0739] | 0.0000 | True | True |
| amihud_102|tercile/2 | up | 184166 | 2850 | -0.0107 | [-0.0146, -0.0069] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_24|tercile/3 | dn | 22650 | 2850 | -0.0270 | [-0.0355, -0.0185] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_9|quintile/5 | up | 11752 | 2802 | +0.0579 | [+0.0490, +0.0668] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_39|tercile/3 | dn | 21817 | 2850 | -0.0288 | [-0.0396, -0.0179] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_9|tercile/1 | up | 52001 | 2850 | +0.0361 | [+0.0251, +0.0472] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_144|quintile/2 | dn | 2894 | 1431 | +0.1087 | [+0.0776, +0.1399] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_39|quintile/1 | dn | 24676 | 2850 | +0.0424 | [+0.0283, +0.0566] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_6|quintile/5 | up | 10697 | 2840 | -0.0516 | [-0.0691, -0.0341] | 0.0000 | True | True |
| bb_pct_b_55|tercile/1 | up | 201083 | 2850 | +0.0220 | [+0.0135, +0.0306] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_39|quintile/1 | dn | 14323 | 2826 | +0.0535 | [+0.0398, +0.0673] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_3|quintile/5 | dn | 4767 | 2594 | -0.0573 | [-0.0683, -0.0463] | 0.0000 | True | True |
| bb_width_9|tercile/3 & bb_width_233|tercile/1 | dn | 17837 | 2849 | -0.0341 | [-0.0438, -0.0244] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_39|quintile/5 | dn | 8912 | 2834 | -0.0447 | [-0.0573, -0.0320] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_9|quintile/5 | dn | 13740 | 2838 | +0.0469 | [+0.0376, +0.0561] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_233|tercile/3 | dn | 18725 | 2850 | +0.0402 | [+0.0306, +0.0497] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_6|quintile/1 | dn | 23893 | 2850 | +0.0419 | [+0.0276, +0.0562] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_24|quintile/5 | up | 10346 | 2826 | -0.0492 | [-0.0671, -0.0313] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_3|quintile/5 | up | 10669 | 2817 | -0.0497 | [-0.0621, -0.0374] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_24|quintile/1 | dn | 14176 | 2824 | +0.0533 | [+0.0390, +0.0676] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_3|tercile/3 | dn | 21982 | 2850 | -0.0284 | [-0.0383, -0.0185] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_3|quintile/5 | up | 6437 | 2594 | -0.0634 | [-0.0741, -0.0526] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_233|tercile/1 | up | 11098 | 2613 | +0.0633 | [+0.0411, +0.0856] | 0.0000 | True | False |
| bb_width_233|quintile/2 & amihud_9|tercile/3 | dn | 21788 | 2850 | -0.0279 | [-0.0377, -0.0181] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_144|tercile/1 | up | 23002 | 2850 | -0.0348 | [-0.0437, -0.0258] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_63|quintile/1 | dn | 14307 | 2833 | +0.0510 | [+0.0373, +0.0647] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_24|tercile/3 | dn | 21874 | 2850 | -0.0274 | [-0.0380, -0.0168] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_9|quintile/1 | dn | 13532 | 2812 | +0.0532 | [+0.0391, +0.0673] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_63|quintile/1 | dn | 24621 | 2850 | +0.0404 | [+0.0263, +0.0545] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_3|tercile/3 | dn | 22857 | 2850 | -0.0264 | [-0.0348, -0.0179] | 0.0000 | True | True |
| amihud_144|quintile/4 | dn | 92331 | 2850 | +0.0141 | [+0.0089, +0.0193] | 0.0000 | True | False |
| amihud_233|quintile/4 | up | 116615 | 2850 | +0.0156 | [+0.0095, +0.0217] | 0.0000 | True | True |
| bb_pct_b_55|quintile/2 | up | 119324 | 2850 | +0.0178 | [+0.0120, +0.0237] | 0.0000 | True | True |
| bb_width_233|quintile/1 & amihud_39|quintile/5 | up | 10399 | 2817 | -0.0473 | [-0.0657, -0.0289] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_9|quintile/5 | up | 10705 | 2838 | -0.0488 | [-0.0672, -0.0305] | 0.0000 | True | True |
| entropy_144|tercile/2 | dn | 143024 | 2850 | -0.0091 | [-0.0128, -0.0055] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_9|tercile/3 | up | 23054 | 2848 | +0.0379 | [+0.0314, +0.0444] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_9|quintile/1 | up | 8012 | 2547 | +0.0675 | [+0.0518, +0.0831] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_6|tercile/3 | dn | 21908 | 2850 | -0.0273 | [-0.0376, -0.0171] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_6|quintile/1 | dn | 12971 | 2807 | +0.0537 | [+0.0397, +0.0676] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_144|tercile/3 | dn | 9639 | 2792 | -0.0426 | [-0.0582, -0.0270] | 0.0000 | True | False |
| di_spread_233|quintile/3 | up | 108215 | 2850 | -0.0139 | [-0.0184, -0.0093] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_6|tercile/3 | dn | 22884 | 2850 | -0.0258 | [-0.0345, -0.0171] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_144|tercile/3 | dn | 19341 | 2850 | +0.0353 | [+0.0255, +0.0451] | 0.0000 | True | True |
| bb_width_3|quintile/3 | dn | 85966 | 2850 | -0.0127 | [-0.0153, -0.0101] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_3|quintile/1 | up | 18000 | 2835 | +0.0545 | [+0.0389, +0.0702] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_3|quintile/1 | dn | 11135 | 2767 | +0.0571 | [+0.0409, +0.0732] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_24|quintile/5 | dn | 16578 | 2850 | -0.0321 | [-0.0429, -0.0213] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_6|quintile/5 | up | 10382 | 2810 | -0.0478 | [-0.0606, -0.0350] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_9|tercile/3 | up | 33688 | 2849 | +0.0338 | [+0.0278, +0.0398] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_233|tercile/1 | dn | 13043 | 2806 | +0.0447 | [+0.0283, +0.0611] | 0.0000 | True | True |
| di_spread_233|quintile/1 | up | 120201 | 2850 | +0.0275 | [+0.0159, +0.0391] | 0.0000 | True | True |
| hurst_233|tercile/1 | up | 181420 | 2850 | -0.0121 | [-0.0165, -0.0076] | 0.0000 | True | False |
| adx_233|tercile/2 | up | 177027 | 2850 | -0.0109 | [-0.0152, -0.0067] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_9|tercile/3 | dn | 26522 | 2849 | +0.0301 | [+0.0242, +0.0359] | 0.0000 | True | True |
| entropy_233|quintile/3 | up | 108255 | 2850 | -0.0139 | [-0.0195, -0.0083] | 0.0000 | True | False |
| bb_pct_b_55|quintile/5 | up | 105802 | 2850 | -0.0277 | [-0.0378, -0.0175] | 0.0000 | True | True |
| entropy_233|tercile/2 | dn | 141404 | 2850 | -0.0093 | [-0.0129, -0.0057] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_9|tercile/3 | dn | 18230 | 2848 | +0.0342 | [+0.0283, +0.0401] | 0.0000 | True | True |
| bb_width_144|quintile/2 & bb_width_233|tercile/3 | up | 8571 | 2535 | +0.0643 | [+0.0415, +0.0871] | 0.0000 | True | True |
| adx_233|quintile/2 | dn | 80742 | 2850 | -0.0153 | [-0.0218, -0.0087] | 0.0000 | True | False |
| bb_width_3|quintile/2 & bb_width_9|quintile/5 | dn | 9395 | 2802 | +0.0501 | [+0.0408, +0.0594] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_39|quintile/1 | up | 17271 | 2821 | +0.0536 | [+0.0370, +0.0703] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_233|quintile/2 | dn | 2408 | 1334 | +0.1058 | [+0.0693, +0.1423] | 0.0000 | True | True |
| amihud_233|quintile/4 | dn | 91189 | 2850 | +0.0133 | [+0.0079, +0.0186] | 0.0000 | True | False |
| bb_width_9|quintile/5 & amihud_6|quintile/1 | up | 17118 | 2813 | +0.0542 | [+0.0372, +0.0713] | 0.0000 | True | True |
| adx_144|quintile/2 | dn | 82959 | 2850 | -0.0135 | [-0.0195, -0.0075] | 0.0000 | True | True |
| adx_233|tercile/3 | dn | 149132 | 2850 | +0.0148 | [+0.0083, +0.0214] | 0.0000 | True | False |
| bb_width_9|tercile/1 & bb_width_233|quintile/5 | dn | 9425 | 2794 | +0.0521 | [+0.0352, +0.0691] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_63|quintile/1 | up | 17383 | 2825 | +0.0526 | [+0.0356, +0.0695] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_9|quintile/5 | up | 10599 | 2818 | -0.0450 | [-0.0579, -0.0321] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_233|quintile/2 | up | 2938 | 1334 | +0.1106 | [+0.0721, +0.1492] | 0.0000 | True | True |
| entropy_233|tercile/2 | up | 182146 | 2850 | -0.0102 | [-0.0145, -0.0058] | 0.0000 | True | False |
| bb_pct_b_55|quintile/4 | up | 109301 | 2850 | -0.0166 | [-0.0228, -0.0104] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_39|tercile/1 | up | 53769 | 2850 | +0.0299 | [+0.0205, +0.0394] | 0.0000 | True | True |
| di_spread_233|tercile/1 | dn | 154778 | 2850 | +0.0196 | [+0.0108, +0.0283] | 0.0000 | True | True |
| amihud_63|tercile/2 | up | 185359 | 2850 | -0.0095 | [-0.0136, -0.0054] | 0.0000 | True | True |
| adx_144|tercile/2 | up | 181246 | 2850 | -0.0097 | [-0.0137, -0.0057] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_24|tercile/1 | up | 53380 | 2850 | +0.0296 | [+0.0207, +0.0386] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_6|tercile/1 | up | 50024 | 2850 | +0.0301 | [+0.0207, +0.0394] | 0.0000 | True | False |
| bb_width_9|tercile/1 & amihud_39|quintile/5 | dn | 16958 | 2850 | -0.0297 | [-0.0406, -0.0187] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_144|tercile/1 | up | 29893 | 2850 | -0.0299 | [-0.0378, -0.0221] | 0.0000 | True | True |
| bb_width_9|tercile/1 & bb_width_233|tercile/3 | up | 28501 | 2850 | +0.0355 | [+0.0230, +0.0480] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_144|quintile/2 | up | 3383 | 1431 | +0.0969 | [+0.0640, +0.1298] | 0.0000 | True | True |
| hurst_144|tercile/1 | dn | 142817 | 2850 | -0.0098 | [-0.0135, -0.0061] | 0.0000 | True | True |
| entropy_102|tercile/2 | dn | 144404 | 2850 | -0.0078 | [-0.0108, -0.0048] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_24|quintile/5 | up | 10749 | 2846 | -0.0454 | [-0.0635, -0.0273] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_3|tercile/1 | up | 44946 | 2850 | +0.0319 | [+0.0218, +0.0420] | 0.0000 | True | False |
| atr_pct_34|quintile/4 & bb_width_233|tercile/1 | up | 16581 | 2806 | +0.0448 | [+0.0276, +0.0619] | 0.0000 | True | False |
| amihud_39|tercile/2 | up | 185903 | 2850 | -0.0092 | [-0.0133, -0.0052] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_9|quintile/1 | up | 16921 | 2813 | +0.0526 | [+0.0353, +0.0698] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_9|quintile/5 | up | 4605 | 2316 | -0.0657 | [-0.0814, -0.0501] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_9|quintile/5 | dn | 3389 | 2316 | -0.0575 | [-0.0732, -0.0418] | 0.0000 | True | True |
| di_spread_55|quintile/4 | up | 109855 | 2850 | -0.0148 | [-0.0205, -0.0092] | 0.0000 | True | True |
| bb_width_9|quintile/5 & amihud_24|quintile/1 | up | 17141 | 2821 | +0.0514 | [+0.0345, +0.0683] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_9|tercile/1 | up | 51414 | 2850 | +0.0288 | [+0.0197, +0.0380] | 0.0000 | True | False |
| amihud_24|tercile/2 | up | 186214 | 2850 | -0.0091 | [-0.0131, -0.0050] | 0.0000 | True | True |
| entropy_144|quintile/3 | up | 109807 | 2850 | -0.0119 | [-0.0169, -0.0069] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_233|quintile/4 | dn | 11280 | 2850 | -0.0353 | [-0.0496, -0.0209] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_9|quintile/1 | dn | 6357 | 2547 | +0.0552 | [+0.0401, +0.0704] | 0.0000 | True | True |
| bb_width_144|quintile/1 & amihud_39|quintile/5 | up | 10696 | 2849 | -0.0440 | [-0.0627, -0.0253] | 0.0000 | True | True |
| hurst_233|quintile/1 | up | 108328 | 2850 | -0.0145 | [-0.0203, -0.0086] | 0.0000 | True | False |
| bb_width_144|quintile/2 & bb_width_233|quintile/4 | up | 12062 | 2797 | +0.0486 | [+0.0288, +0.0685] | 0.0000 | True | True |
| di_spread_233|tercile/1 | up | 196248 | 2850 | +0.0196 | [+0.0099, +0.0292] | 0.0000 | True | True |
| bb_width_3|tercile/2 | up | 186561 | 2850 | -0.0096 | [-0.0121, -0.0072] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_9|quintile/5 | dn | 7768 | 2710 | +0.0470 | [+0.0369, +0.0571] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_233|quintile/1 | up | 5384 | 2451 | -0.0562 | [-0.0687, -0.0436] | 0.0000 | True | True |
| bb_width_233|quintile/3 | up | 108520 | 2850 | -0.0137 | [-0.0200, -0.0075] | 0.0000 | True | False |
| bb_width_3|quintile/1 & bb_width_9|quintile/5 | up | 9802 | 2710 | +0.0519 | [+0.0424, +0.0615] | 0.0000 | True | True |
| bb_pct_b_55|quintile/1 | up | 120905 | 2850 | +0.0222 | [+0.0117, +0.0328] | 0.0000 | True | True |
| bb_width_9|tercile/1 & bb_width_144|quintile/5 | dn | 9937 | 2782 | +0.0450 | [+0.0289, +0.0610] | 0.0000 | True | True |
| vwap_zscore_233|quintile/4 | dn | 81550 | 2850 | -0.0134 | [-0.0190, -0.0077] | 0.0000 | True | True |
| entropy_144|quintile/5 | dn | 92063 | 2850 | +0.0146 | [+0.0076, +0.0217] | 0.0000 | True | False |
| bb_width_9|quintile/2 & bb_width_233|tercile/3 | dn | 18836 | 2850 | +0.0307 | [+0.0198, +0.0415] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_9|quintile/5 | dn | 12090 | 2850 | -0.0304 | [-0.0439, -0.0168] | 0.0000 | True | False |
| bb_width_3|quintile/5 & bb_width_233|quintile/1 | dn | 4014 | 2451 | -0.0500 | [-0.0620, -0.0379] | 0.0000 | True | True |
| bb_width_9|tercile/3 & bb_width_233|tercile/1 | up | 24080 | 2849 | -0.0299 | [-0.0409, -0.0189] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & bb_width_144|tercile/3 | up | 12177 | 2783 | -0.0388 | [-0.0560, -0.0216] | 0.0000 | True | False |
| di_spread_55|quintile/1 | up | 120962 | 2850 | +0.0225 | [+0.0106, +0.0344] | 0.0000 | True | True |
| di_spread_55|tercile/1 | up | 198868 | 2850 | +0.0176 | [+0.0084, +0.0268] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_3|tercile/3 | dn | 28721 | 2850 | -0.0206 | [-0.0270, -0.0143] | 0.0000 | True | True |
| entropy_102|quintile/5 | dn | 92290 | 2850 | +0.0138 | [+0.0072, +0.0205] | 0.0000 | True | False |
| atr_pct_34|quintile/2 & bb_width_233|quintile/4 | up | 14215 | 2850 | -0.0364 | [-0.0535, -0.0192] | 0.0000 | True | True |
| bb_pct_b_55|quintile/4 | dn | 85511 | 2850 | -0.0132 | [-0.0186, -0.0078] | 0.0000 | True | True |
| bb_pct_b_15|tercile/3 | up | 182752 | 2850 | -0.0162 | [-0.0221, -0.0104] | 0.0000 | True | True |
| bb_pct_b_55|tercile/3 | dn | 141409 | 2850 | -0.0151 | [-0.0219, -0.0083] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_24|quintile/5 | up | 11676 | 2849 | -0.0377 | [-0.0537, -0.0216] | 0.0000 | True | True |
| amihud_6|tercile/2 | up | 187142 | 2850 | -0.0078 | [-0.0113, -0.0044] | 0.0000 | True | True |
| hurst_144|quintile/1 | dn | 85433 | 2850 | -0.0113 | [-0.0157, -0.0069] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_9|quintile/1 | dn | 23328 | 2850 | +0.0309 | [+0.0195, +0.0424] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_6|quintile/1 | dn | 22432 | 2850 | +0.0318 | [+0.0199, +0.0436] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_3|quintile/5 | dn | 12159 | 2850 | -0.0291 | [-0.0417, -0.0166] | 0.0000 | True | False |
| bb_width_3|quintile/5 & bb_width_144|quintile/1 | dn | 4273 | 2482 | -0.0463 | [-0.0571, -0.0355] | 0.0000 | True | True |
| bb_width_233|quintile/2 & amihud_6|quintile/5 | dn | 12064 | 2849 | -0.0292 | [-0.0425, -0.0159] | 0.0000 | True | False |
| amihud_9|tercile/2 | up | 187100 | 2850 | -0.0078 | [-0.0115, -0.0041] | 0.0000 | True | True |
| di_spread_55|quintile/4 | dn | 85861 | 2850 | -0.0119 | [-0.0173, -0.0065] | 0.0000 | True | True |
| entropy_144|quintile/3 | dn | 85582 | 2850 | -0.0100 | [-0.0147, -0.0053] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_6|quintile/1 | up | 15668 | 2807 | +0.0453 | [+0.0312, +0.0595] | 0.0000 | True | False |
| entropy_144|quintile/1 | up | 117383 | 2850 | +0.0135 | [+0.0068, +0.0203] | 0.0000 | True | False |
| bb_width_3|tercile/3 & amihud_39|quintile/1 | dn | 24749 | 2850 | +0.0294 | [+0.0180, +0.0408] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_39|quintile/5 | up | 11504 | 2849 | -0.0368 | [-0.0532, -0.0205] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_3|quintile/1 | dn | 19488 | 2848 | +0.0335 | [+0.0206, +0.0464] | 0.0000 | True | False |
| bb_width_3|tercile/3 & amihud_24|quintile/1 | dn | 24474 | 2850 | +0.0295 | [+0.0177, +0.0414] | 0.0000 | True | False |
| bb_width_233|quintile/2 & amihud_24|quintile/5 | dn | 12137 | 2850 | -0.0284 | [-0.0427, -0.0141] | 0.0000 | True | False |
| atr_pct_34|quintile/2 & amihud_3|quintile/5 | up | 12122 | 2848 | -0.0359 | [-0.0510, -0.0209] | 0.0000 | True | False |
| bb_pct_b_15|tercile/1 | up | 198595 | 2850 | +0.0154 | [+0.0093, +0.0215] | 0.0000 | True | True |
| adx_233|quintile/3 | up | 106193 | 2850 | -0.0114 | [-0.0168, -0.0059] | 0.0000 | True | True |
| amihud_233|quintile/3 | up | 109079 | 2850 | -0.0102 | [-0.0154, -0.0050] | 0.0000 | True | False |
| atr_pct_34|quintile/1 & bb_width_9|quintile/5 | dn | 659 | 800 | -0.0947 | [-0.1196, -0.0699] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_3|tercile/3 | dn | 14794 | 2850 | -0.0263 | [-0.0336, -0.0191] | 0.0000 | True | True |
| atr_pct_34|tercile/1 & bb_width_233|tercile/3 | up | 11930 | 2811 | -0.0394 | [-0.0583, -0.0204] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_9|quintile/1 | up | 16242 | 2812 | +0.0428 | [+0.0287, +0.0570] | 0.0000 | True | False |
| di_spread_233|quintile/3 | dn | 84565 | 2850 | -0.0101 | [-0.0145, -0.0057] | 0.0000 | True | False |
| bb_width_233|tercile/1 & amihud_3|quintile/5 | up | 22009 | 2850 | -0.0272 | [-0.0392, -0.0151] | 0.0000 | True | False |
| bb_width_3|quintile/5 & amihud_63|quintile/1 | up | 17313 | 2833 | +0.0407 | [+0.0261, +0.0553] | 0.0000 | True | False |
| atr_pct_34|quintile/2 & amihud_6|quintile/5 | up | 11881 | 2847 | -0.0354 | [-0.0512, -0.0197] | 0.0000 | True | False |
| range_pos_5|tercile/1 | up | 198410 | 2850 | +0.0145 | [+0.0104, +0.0186] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_3|quintile/1 | up | 13402 | 2767 | +0.0467 | [+0.0308, +0.0627] | 0.0000 | True | False |
| range_pos_5|quintile/1 | up | 120449 | 2850 | +0.0187 | [+0.0134, +0.0241] | 0.0000 | True | True |
| hurst_144|tercile/3 | dn | 151006 | 2850 | +0.0081 | [+0.0047, +0.0116] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_9|tercile/3 | dn | 14970 | 2842 | +0.0302 | [+0.0231, +0.0373] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_39|quintile/1 | up | 17184 | 2826 | +0.0408 | [+0.0266, +0.0550] | 0.0000 | True | False |
| bb_width_9|quintile/2 & amihud_3|tercile/3 | dn | 23370 | 2850 | -0.0199 | [-0.0276, -0.0123] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_39|tercile/3 | dn | 21958 | 2850 | -0.0215 | [-0.0282, -0.0149] | 0.0000 | True | True |
| atr_pct_34|quintile/2 & amihud_9|quintile/5 | up | 11823 | 2846 | -0.0347 | [-0.0504, -0.0190] | 0.0000 | True | False |
| entropy_102|quintile/3 | dn | 86454 | 2850 | -0.0083 | [-0.0119, -0.0048] | 0.0000 | True | False |
| bb_width_3|quintile/2 & amihud_39|quintile/5 | up | 18585 | 2850 | +0.0296 | [+0.0211, +0.0381] | 0.0000 | True | True |
| di_spread_55|tercile/3 | up | 182139 | 2850 | -0.0162 | [-0.0251, -0.0074] | 0.0000 | True | True |
| bb_width_9|tercile/3 & bb_width_144|tercile/1 | up | 25008 | 2845 | -0.0256 | [-0.0354, -0.0158] | 0.0000 | True | True |
| atr_pct_34|quintile/1 & bb_width_9|quintile/5 | up | 925 | 800 | -0.1068 | [-0.1371, -0.0765] | 0.0000 | True | True |
| entropy_233|quintile/2 | dn | 84878 | 2850 | -0.0099 | [-0.0148, -0.0051] | 0.0000 | True | False |
| bb_width_3|quintile/2 & amihud_24|quintile/5 | up | 18552 | 2850 | +0.0298 | [+0.0214, +0.0382] | 0.0000 | True | True |
| entropy_102|quintile/2 | dn | 86124 | 2850 | -0.0100 | [-0.0151, -0.0049] | 0.0000 | True | True |
| bb_width_3|quintile/3 | up | 111703 | 2850 | -0.0105 | [-0.0129, -0.0080] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_144|tercile/1 | dn | 1478 | 866 | +0.1025 | [+0.0607, +0.1442] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_9|tercile/3 | dn | 19998 | 2850 | -0.0223 | [-0.0289, -0.0157] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_3|quintile/1 | up | 29945 | 2850 | +0.0310 | [+0.0177, +0.0444] | 0.0000 | True | False |
| bb_width_3|tercile/3 & amihud_63|quintile/1 | dn | 24786 | 2850 | +0.0276 | [+0.0163, +0.0388] | 0.0000 | True | True |
| bb_width_144|tercile/1 & bb_width_233|tercile/3 | up | 6465 | 2260 | +0.0522 | [+0.0299, +0.0745] | 0.0000 | True | True |
| hurst_233|quintile/2 | dn | 85012 | 2850 | -0.0089 | [-0.0118, -0.0059] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_6|quintile/1 | up | 28975 | 2850 | +0.0319 | [+0.0181, +0.0458] | 0.0000 | True | False |
| bb_width_9|quintile/2 & amihud_6|tercile/3 | dn | 22901 | 2850 | -0.0198 | [-0.0277, -0.0119] | 0.0000 | True | True |
| amihud_3|tercile/2 | up | 187527 | 2850 | -0.0072 | [-0.0106, -0.0039] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_9|tercile/3 | dn | 22800 | 2850 | -0.0197 | [-0.0279, -0.0116] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_24|tercile/3 | dn | 21522 | 2850 | -0.0212 | [-0.0279, -0.0145] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_6|tercile/3 | dn | 18806 | 2850 | -0.0224 | [-0.0289, -0.0159] | 0.0000 | True | True |
| bb_width_3|quintile/5 & amihud_24|quintile/1 | up | 16982 | 2824 | +0.0397 | [+0.0254, +0.0539] | 0.0000 | True | False |
| bb_width_144|tercile/1 & amihud_3|quintile/5 | up | 22413 | 2850 | -0.0252 | [-0.0372, -0.0132] | 0.0000 | True | True |
| bb_width_9|tercile/3 & amihud_39|quintile/1 | up | 29790 | 2850 | +0.0305 | [+0.0165, +0.0445] | 0.0000 | True | False |
| donchian_break_55|quintile/1 | up | 549076 | 2850 | +0.0019 | [+0.0013, +0.0026] | 0.0000 | True | True |
| donchian_break_55|tercile/1 | up | 549076 | 2850 | +0.0019 | [+0.0013, +0.0026] | 0.0000 | True | True |
| bb_width_9|quintile/5 & bb_width_144|quintile/1 | dn | 2947 | 2141 | -0.0480 | [-0.0645, -0.0315] | 0.0000 | True | True |
| di_spread_55|tercile/1 | dn | 155104 | 2850 | +0.0133 | [+0.0061, +0.0205] | 0.0000 | True | False |
| bb_width_9|tercile/3 & amihud_63|quintile/1 | up | 30025 | 2850 | +0.0304 | [+0.0161, +0.0447] | 0.0000 | True | False |
| bb_width_9|tercile/3 & amihud_24|quintile/1 | up | 29562 | 2850 | +0.0305 | [+0.0165, +0.0445] | 0.0000 | True | False |
| bb_width_9|tercile/3 & amihud_9|quintile/1 | up | 28845 | 2850 | +0.0310 | [+0.0170, +0.0450] | 0.0000 | True | False |
| bb_width_9|quintile/1 & amihud_24|quintile/5 | up | 11848 | 2832 | -0.0331 | [-0.0460, -0.0201] | 0.0000 | True | False |
| kama_er_233|tercile/2 | up | 183322 | 2850 | -0.0074 | [-0.0112, -0.0037] | 0.0000 | True | True |
| entropy_233|quintile/3 | dn | 84959 | 2850 | -0.0088 | [-0.0131, -0.0046] | 0.0000 | True | False |
| atr_pct_34|quintile/5 & bb_width_233|tercile/1 | up | 1602 | 820 | +0.1129 | [+0.0569, +0.1688] | 0.0000 | True | False |
| bb_width_9|tercile/1 & amihud_3|quintile/5 | up | 21771 | 2850 | -0.0253 | [-0.0352, -0.0154] | 0.0000 | True | True |
| bb_width_144|tercile/1 & bb_width_233|quintile/4 | up | 9841 | 2645 | +0.0420 | [+0.0206, +0.0633] | 0.0000 | True | True |
| bb_width_9|tercile/1 & bb_width_144|tercile/3 | up | 28864 | 2848 | +0.0256 | [+0.0138, +0.0373] | 0.0000 | True | True |
| bb_pct_b_55|tercile/1 | dn | 155021 | 2850 | +0.0128 | [+0.0059, +0.0197] | 0.0000 | True | True |
| bb_pct_b_15|quintile/4 | up | 111061 | 2850 | -0.0122 | [-0.0173, -0.0072] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_144|quintile/1 | up | 5800 | 2482 | -0.0452 | [-0.0570, -0.0333] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_6|quintile/5 | up | 21824 | 2850 | -0.0247 | [-0.0375, -0.0120] | 0.0000 | True | False |
| bb_width_3|quintile/2 & amihud_9|quintile/5 | up | 18050 | 2850 | +0.0277 | [+0.0192, +0.0363] | 0.0000 | True | True |
| bb_pct_b_15|quintile/1 | up | 119932 | 2850 | +0.0175 | [+0.0100, +0.0250] | 0.0000 | True | True |
| entropy_233|quintile/1 | up | 116060 | 2850 | +0.0131 | [+0.0056, +0.0207] | 0.0000 | True | False |
| atr_pct_34|quintile/5 & bb_width_233|tercile/1 | dn | 1278 | 820 | +0.1014 | [+0.0527, +0.1502] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_39|tercile/1 | dn | 27959 | 2850 | +0.0201 | [+0.0090, +0.0312] | 0.0000 | True | False |
| bb_width_144|quintile/4 & amihud_3|tercile/1 | dn | 27736 | 2850 | +0.0194 | [+0.0090, +0.0297] | 0.0000 | True | False |
| bb_width_3|tercile/1 & amihud_6|tercile/3 | dn | 33805 | 2850 | -0.0163 | [-0.0223, -0.0103] | 0.0000 | True | True |
| bb_width_9|quintile/1 & bb_width_233|quintile/5 | up | 5061 | 2125 | +0.0587 | [+0.0333, +0.0842] | 0.0000 | True | False |
| vwap_zscore_233|tercile/2 | dn | 138490 | 2850 | -0.0074 | [-0.0112, -0.0035] | 0.0000 | True | True |
| bb_width_9|quintile/5 & bb_width_233|quintile/1 | up | 4026 | 2172 | -0.0504 | [-0.0688, -0.0320] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_6|quintile/5 | up | 22281 | 2850 | -0.0235 | [-0.0358, -0.0112] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_144|tercile/1 | up | 1750 | 866 | +0.0988 | [+0.0549, +0.1427] | 0.0000 | True | True |
| entropy_144|quintile/4 | dn | 85864 | 2850 | -0.0084 | [-0.0129, -0.0039] | 0.0000 | True | True |
| bb_width_9|quintile/1 & bb_width_233|quintile/4 | dn | 9275 | 2840 | -0.0285 | [-0.0397, -0.0173] | 0.0000 | True | True |
| yangzhang_3|tercile/2 | up | 196158 | 2850 | +0.0093 | [+0.0045, +0.0140] | 0.0000 | True | False |
| bb_width_3|tercile/1 & amihud_9|tercile/3 | dn | 35326 | 2850 | -0.0159 | [-0.0220, -0.0097] | 0.0000 | True | True |
| hurst_144|quintile/5 | dn | 90859 | 2850 | +0.0097 | [+0.0050, +0.0144] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_9|tercile/1 | dn | 12249 | 2757 | -0.0261 | [-0.0323, -0.0199] | 0.0000 | True | True |
| bb_width_9|quintile/1 & bb_width_144|quintile/5 | up | 5403 | 2223 | +0.0531 | [+0.0302, +0.0759] | 0.0000 | True | True |
| bb_width_9|quintile/1 & amihud_39|quintile/5 | up | 12076 | 2834 | -0.0306 | [-0.0437, -0.0175] | 0.0000 | True | False |
| bb_pct_b_15|quintile/5 | up | 109169 | 2850 | -0.0172 | [-0.0242, -0.0101] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_9|tercile/1 | dn | 27679 | 2850 | +0.0189 | [+0.0079, +0.0299] | 0.0000 | True | False |
| di_spread_55|quintile/1 | dn | 93820 | 2850 | +0.0157 | [+0.0063, +0.0252] | 0.0000 | True | False |
| bb_width_9|quintile/1 & bb_width_144|quintile/4 | up | 12479 | 2821 | -0.0300 | [-0.0434, -0.0166] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_24|tercile/1 | dn | 27789 | 2850 | +0.0195 | [+0.0082, +0.0308] | 0.0000 | True | False |
| entropy_39|tercile/1 | dn | 145907 | 2850 | -0.0074 | [-0.0115, -0.0033] | 0.0000 | True | True |
| bb_width_9|quintile/5 & bb_width_233|quintile/1 | dn | 3030 | 2172 | -0.0446 | [-0.0620, -0.0272] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_9|quintile/5 | up | 21808 | 2850 | -0.0235 | [-0.0366, -0.0104] | 0.0000 | True | False |
| bb_width_144|quintile/4 & amihud_6|tercile/1 | dn | 27629 | 2850 | +0.0189 | [+0.0079, +0.0299] | 0.0000 | True | False |
| bb_width_233|quintile/4 & amihud_39|tercile/1 | up | 34108 | 2850 | +0.0216 | [+0.0087, +0.0346] | 0.0000 | True | True |
| bb_width_3|quintile/1 & bb_width_9|tercile/3 | up | 18944 | 2842 | +0.0289 | [+0.0220, +0.0358] | 0.0000 | True | True |
| range_pos_5|tercile/3 | up | 184773 | 2850 | -0.0125 | [-0.0166, -0.0084] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_39|tercile/3 | dn | 37733 | 2850 | -0.0150 | [-0.0213, -0.0087] | 0.0000 | True | True |
| entropy_102|tercile/2 | up | 186515 | 2850 | -0.0061 | [-0.0094, -0.0029] | 0.0000 | True | True |
| adx_144|quintile/4 | dn | 89382 | 2850 | +0.0085 | [+0.0037, +0.0132] | 0.0000 | True | True |
| donchian_break_55|tercile/3 | up | 24179 | 2614 | -0.0347 | [-0.0477, -0.0216] | 0.0000 | True | True |
| adx_144|quintile/3 | up | 108967 | 2850 | -0.0089 | [-0.0139, -0.0038] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_39|quintile/5 | up | 22186 | 2850 | -0.0224 | [-0.0355, -0.0094] | 0.0000 | True | True |
| fib_dist_3|quintile/1 | up | 119613 | 2850 | +0.0157 | [+0.0112, +0.0201] | 0.0000 | True | True |
| donchian_break_55|quintile/5 | up | 23413 | 2592 | -0.0347 | [-0.0474, -0.0220] | 0.0000 | True | True |
| entropy_233|quintile/4 | dn | 85081 | 2850 | -0.0082 | [-0.0127, -0.0037] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_3|tercile/1 | up | 34163 | 2850 | +0.0206 | [+0.0082, +0.0329] | 0.0000 | True | True |
| atr_pct_34|quintile/5 & bb_width_9|quintile/1 | dn | 1002 | 662 | +0.1103 | [+0.0691, +0.1516] | 0.0000 | True | True |
| yangzhang_3|quintile/3 | up | 118081 | 2850 | +0.0105 | [+0.0053, +0.0156] | 0.0000 | True | False |
| bb_width_233|quintile/2 & amihud_39|quintile/5 | dn | 12463 | 2850 | -0.0234 | [-0.0382, -0.0087] | 0.0000 | True | False |
| atr_pct_34|quintile/5 & bb_width_9|quintile/1 | up | 1315 | 662 | +0.1149 | [+0.0667, +0.1631] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_6|tercile/1 | up | 33911 | 2850 | +0.0207 | [+0.0077, +0.0337] | 0.0000 | True | True |
| fib_dist_3|tercile/1 | up | 197212 | 2850 | +0.0118 | [+0.0085, +0.0151] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_9|quintile/5 | up | 22311 | 2850 | -0.0220 | [-0.0349, -0.0091] | 0.0000 | True | True |
| bb_width_9|tercile/1 & amihud_6|quintile/5 | up | 21275 | 2850 | -0.0228 | [-0.0336, -0.0121] | 0.0000 | True | False |
| entropy_55|tercile/1 | dn | 145849 | 2850 | -0.0071 | [-0.0116, -0.0027] | 0.0000 | True | False |
| kama_er_233|quintile/5 | up | 116433 | 2850 | +0.0163 | [+0.0064, +0.0263] | 0.0000 | True | False |
| bb_width_3|tercile/1 & amihud_24|tercile/3 | dn | 37229 | 2850 | -0.0147 | [-0.0209, -0.0084] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_6|quintile/5 | up | 17586 | 2850 | +0.0254 | [+0.0168, +0.0340] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_233|quintile/1 | dn | 1939 | 1211 | +0.0720 | [+0.0297, +0.1142] | 0.0000 | True | True |
| di_spread_55|tercile/3 | dn | 143340 | 2850 | -0.0115 | [-0.0186, -0.0043] | 0.0000 | True | True |
| bb_width_9|quintile/4 & bb_width_144|quintile/2 | dn | 14185 | 2850 | -0.0207 | [-0.0293, -0.0122] | 0.0000 | True | True |
| amihud_9|quintile/3 | up | 112109 | 2850 | -0.0080 | [-0.0125, -0.0035] | 0.0000 | True | True |
| vwap_zscore_144|quintile/4 | up | 108234 | 2850 | -0.0110 | [-0.0177, -0.0043] | 0.0000 | True | False |
| bb_width_3|tercile/3 & amihud_3|quintile/1 | up | 23794 | 2848 | +0.0284 | [+0.0149, +0.0418] | 0.0000 | True | False |
| bb_pct_b_15|quintile/2 | up | 117772 | 2850 | +0.0110 | [+0.0065, +0.0155] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_233|tercile/1 | dn | 9526 | 2810 | -0.0271 | [-0.0371, -0.0172] | 0.0000 | True | True |
| vwap_zscore_144|tercile/3 | up | 179601 | 2850 | -0.0123 | [-0.0202, -0.0044] | 0.0000 | True | True |
| di_spread_3|quintile/1 | up | 119612 | 2850 | +0.0157 | [+0.0096, +0.0218] | 0.0000 | True | True |
| hurst_233|quintile/2 | up | 109802 | 2850 | -0.0081 | [-0.0115, -0.0048] | 0.0000 | True | True |
| amihud_6|quintile/3 | up | 112119 | 2850 | -0.0081 | [-0.0124, -0.0039] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_24|tercile/1 | up | 33882 | 2850 | +0.0203 | [+0.0071, +0.0334] | 0.0000 | True | True |
| bb_width_233|quintile/4 & amihud_9|tercile/1 | up | 33843 | 2850 | +0.0202 | [+0.0069, +0.0334] | 0.0000 | True | True |
| bb_pct_b_55|quintile/1 | dn | 93530 | 2850 | +0.0142 | [+0.0060, +0.0224] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_24|tercile/3 | dn | 22928 | 2850 | -0.0165 | [-0.0249, -0.0082] | 0.0000 | True | True |
| bb_pct_b_55|quintile/2 | dn | 91916 | 2850 | +0.0094 | [+0.0042, +0.0146] | 0.0000 | True | True |
| bb_width_9|quintile/1 & bb_width_233|quintile/5 | dn | 3954 | 2125 | +0.0474 | [+0.0271, +0.0678] | 0.0000 | True | True |
| bb_pct_b_55|quintile/5 | dn | 84769 | 2850 | -0.0149 | [-0.0234, -0.0065] | 0.0000 | True | True |
| bb_width_144|tercile/1 & amihud_24|quintile/5 | up | 22344 | 2850 | -0.0211 | [-0.0341, -0.0082] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_63|quintile/1 | dn | 16694 | 2850 | +0.0217 | [+0.0079, +0.0356] | 0.0000 | True | False |
| bb_width_3|tercile/1 & amihud_39|quintile/5 | up | 29336 | 2850 | +0.0194 | [+0.0106, +0.0281] | 0.0000 | True | False |
| range_width_233|quintile/3 | dn | 84956 | 2850 | -0.0095 | [-0.0157, -0.0034] | 0.0000 | True | False |
| hurst_233|tercile/3 | up | 189867 | 2850 | +0.0072 | [+0.0029, +0.0116] | 0.0000 | True | False |
| entropy_102|quintile/3 | up | 111613 | 2850 | -0.0073 | [-0.0112, -0.0034] | 0.0000 | True | True |
| entropy_144|quintile/2 | up | 110800 | 2850 | -0.0081 | [-0.0132, -0.0029] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_3|quintile/5 | dn | 12932 | 2850 | -0.0202 | [-0.0313, -0.0092] | 0.0000 | True | False |
| di_spread_3|tercile/1 | up | 196986 | 2850 | +0.0115 | [+0.0068, +0.0161] | 0.0000 | True | True |
| bb_width_9|quintile/1 & bb_width_144|quintile/4 | dn | 9929 | 2821 | -0.0242 | [-0.0367, -0.0117] | 0.0000 | True | False |
| bb_width_9|quintile/2 & amihud_39|tercile/3 | dn | 23021 | 2850 | -0.0160 | [-0.0241, -0.0078] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_233|quintile/4 | up | 20560 | 2850 | +0.0219 | [+0.0134, +0.0304] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_39|quintile/5 | up | 21891 | 2850 | -0.0209 | [-0.0346, -0.0073] | 0.0000 | True | False |
| atr_pct_34|quintile/2 & bb_width_233|tercile/3 | dn | 9813 | 2811 | -0.0260 | [-0.0413, -0.0106] | 0.0000 | True | False |
| range_pos_5|quintile/5 | up | 110000 | 2850 | -0.0146 | [-0.0198, -0.0095] | 0.0000 | True | True |
| adx_144|quintile/3 | dn | 84913 | 2850 | -0.0071 | [-0.0115, -0.0027] | 0.0000 | True | False |
| bb_width_3|tercile/1 & amihud_24|quintile/5 | up | 28921 | 2850 | +0.0190 | [+0.0103, +0.0276] | 0.0000 | True | False |
| entropy_102|quintile/1 | up | 116807 | 2850 | +0.0101 | [+0.0031, +0.0171] | 0.0000 | True | False |
| entropy_39|tercile/3 | dn | 151530 | 2850 | +0.0064 | [+0.0023, +0.0104] | 0.0000 | True | True |
| amihud_144|quintile/3 | up | 110761 | 2850 | -0.0077 | [-0.0130, -0.0024] | 0.0000 | True | False |
| atr_pct_34|quintile/1 & bb_width_144|quintile/5 | up | 449 | 477 | -0.1025 | [-0.1644, -0.0406] | 0.0000 | True | True |
| bb_width_233|tercile/1 & amihud_24|quintile/5 | up | 21865 | 2850 | -0.0206 | [-0.0344, -0.0069] | 0.0000 | True | False |
| bb_width_9|tercile/1 & amihud_9|quintile/5 | up | 21516 | 2850 | -0.0207 | [-0.0314, -0.0099] | 0.0000 | True | False |
| bb_width_144|quintile/4 & amihud_3|tercile/1 | up | 34031 | 2850 | +0.0180 | [+0.0063, +0.0297] | 0.0000 | True | True |
| entropy_24|tercile/1 | dn | 148038 | 2850 | -0.0059 | [-0.0098, -0.0021] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_9|quintile/1 | up | 4256 | 1752 | -0.0459 | [-0.0571, -0.0346] | 0.0000 | True | True |
| kama_er_144|tercile/2 | dn | 144816 | 2850 | -0.0051 | [-0.0081, -0.0021] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_6|quintile/1 | up | 27357 | 2850 | +0.0239 | [+0.0110, +0.0368] | 0.0000 | True | False |
| bb_width_144|tercile/2 | dn | 144481 | 2850 | -0.0065 | [-0.0114, -0.0017] | 0.0000 | True | False |
| bb_width_144|quintile/2 & bb_width_233|quintile/5 | up | 1240 | 662 | +0.0899 | [+0.0433, +0.1366] | 0.0000 | True | True |
| fib_dist_3|tercile/3 | up | 185791 | 2850 | -0.0104 | [-0.0137, -0.0070] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_9|quintile/1 | dn | 3135 | 1752 | -0.0401 | [-0.0499, -0.0304] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_6|tercile/1 | up | 33773 | 2850 | +0.0177 | [+0.0055, +0.0299] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_63|quintile/1 | up | 30352 | 2850 | +0.0222 | [+0.0101, +0.0343] | 0.0000 | True | False |
| vwap_zscore_233|tercile/3 | up | 176091 | 2850 | -0.0120 | [-0.0209, -0.0031] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_144|tercile/1 | dn | 9975 | 2821 | -0.0231 | [-0.0319, -0.0144] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_24|quintile/5 | up | 18060 | 2850 | +0.0214 | [+0.0117, +0.0312] | 0.0000 | True | True |
| donchian_break_13|quintile/1 | up | 524277 | 2850 | +0.0022 | [+0.0014, +0.0030] | 0.0000 | True | True |
| donchian_break_13|tercile/1 | up | 524277 | 2850 | +0.0022 | [+0.0014, +0.0030] | 0.0000 | True | True |
| hurst_144|quintile/2 | dn | 86495 | 2850 | -0.0065 | [-0.0095, -0.0036] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_39|quintile/5 | up | 18035 | 2850 | +0.0213 | [+0.0114, +0.0311] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_233|quintile/4 | up | 21113 | 2850 | +0.0210 | [+0.0097, +0.0323] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_9|quintile/1 | up | 28408 | 2850 | +0.0224 | [+0.0101, +0.0348] | 0.0000 | True | False |
| kama_er_233|quintile/4 | up | 110061 | 2850 | -0.0077 | [-0.0127, -0.0028] | 0.0000 | True | False |
| bb_pct_b_5|tercile/1 | up | 196496 | 2850 | +0.0106 | [+0.0066, +0.0146] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_39|quintile/1 | up | 30098 | 2850 | +0.0214 | [+0.0092, +0.0337] | 0.0000 | True | False |
| bb_width_9|tercile/1 & bb_width_144|tercile/3 | dn | 22486 | 2848 | +0.0167 | [+0.0073, +0.0260] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_9|tercile/1 | up | 33682 | 2850 | +0.0169 | [+0.0046, +0.0291] | 0.0000 | True | True |
| amihud_3|quintile/3 | up | 112587 | 2850 | -0.0069 | [-0.0108, -0.0031] | 0.0000 | True | True |
| amihud_102|quintile/3 | up | 111453 | 2850 | -0.0069 | [-0.0121, -0.0017] | 0.0000 | True | False |
| entropy_55|quintile/2 | up | 111990 | 2850 | -0.0072 | [-0.0120, -0.0025] | 0.0000 | True | False |
| di_spread_55|quintile/5 | up | 109326 | 2850 | -0.0154 | [-0.0274, -0.0033] | 0.0000 | True | True |
| di_spread_233|tercile/3 | up | 181063 | 2850 | -0.0124 | [-0.0222, -0.0026] | 0.0000 | True | False |
| vwap_zscore_233|tercile/3 | dn | 137695 | 2850 | -0.0095 | [-0.0162, -0.0027] | 0.0000 | True | False |
| entropy_21|tercile/1 | dn | 150072 | 2850 | -0.0052 | [-0.0088, -0.0017] | 0.0000 | True | True |
| vwap_zscore_233|quintile/3 | dn | 83102 | 2850 | -0.0072 | [-0.0119, -0.0026] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_144|quintile/4 | dn | 16292 | 2850 | +0.0174 | [+0.0100, +0.0248] | 0.0000 | True | True |
| bb_width_3|tercile/3 & amihud_24|quintile/1 | up | 29717 | 2850 | +0.0211 | [+0.0088, +0.0334] | 0.0000 | True | False |
| bb_width_144|quintile/4 & amihud_39|quintile/1 | dn | 16536 | 2850 | +0.0188 | [+0.0048, +0.0329] | 0.0000 | True | False |
| adx_144|tercile/2 | dn | 142334 | 2850 | -0.0051 | [-0.0088, -0.0015] | 0.0000 | True | False |
| hurst_102|tercile/1 | up | 186478 | 2850 | -0.0063 | [-0.0106, -0.0020] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_233|quintile/4 | up | 30771 | 2850 | +0.0166 | [+0.0081, +0.0250] | 0.0000 | True | True |
| hurst_144|quintile/1 | up | 111160 | 2850 | -0.0083 | [-0.0137, -0.0028] | 0.0000 | True | False |
| range_pos_5|quintile/4 | up | 112285 | 2850 | -0.0084 | [-0.0115, -0.0054] | 0.0000 | True | False |
| bb_width_3|tercile/1 & amihud_9|quintile/5 | up | 27136 | 2850 | +0.0174 | [+0.0083, +0.0265] | 0.0000 | True | False |
| atr_pct_34|quintile/4 & bb_width_144|quintile/1 | up | 4928 | 2041 | +0.0394 | [+0.0155, +0.0632] | 0.0000 | True | False |
| di_spread_3|tercile/3 | up | 186081 | 2850 | -0.0099 | [-0.0148, -0.0051] | 0.0000 | True | True |
| hurst_144|tercile/1 | up | 185831 | 2850 | -0.0063 | [-0.0109, -0.0018] | 0.0000 | True | False |
| entropy_55|tercile/3 | dn | 151188 | 2850 | +0.0061 | [+0.0015, +0.0107] | 0.0000 | True | False |
| entropy_144|tercile/1 | up | 191803 | 2850 | +0.0063 | [+0.0016, +0.0109] | 0.0000 | True | False |
| hurst_233|quintile/5 | up | 113998 | 2850 | +0.0081 | [+0.0028, +0.0135] | 0.0000 | True | False |
| bb_width_9|tercile/2 | dn | 146846 | 2850 | -0.0052 | [-0.0083, -0.0022] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_24|tercile/1 | up | 33601 | 2850 | +0.0162 | [+0.0038, +0.0287] | 0.0000 | True | True |
| entropy_39|quintile/1 | dn | 87629 | 2850 | -0.0078 | [-0.0137, -0.0018] | 0.0000 | True | False |
| di_spread_55|quintile/2 | dn | 91323 | 2850 | +0.0073 | [+0.0026, +0.0119] | 0.0000 | True | True |
| bb_width_144|tercile/1 & bb_width_233|quintile/4 | dn | 6468 | 2645 | -0.0253 | [-0.0426, -0.0080] | 0.0000 | True | True |
| entropy_24|tercile/3 | dn | 147866 | 2850 | +0.0049 | [+0.0018, +0.0081] | 0.0000 | True | True |
| bb_width_9|tercile/1 & bb_width_233|quintile/4 | dn | 19111 | 2850 | -0.0153 | [-0.0248, -0.0059] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_6|quintile/5 | dn | 12992 | 2850 | -0.0165 | [-0.0280, -0.0050] | 0.0000 | True | False |
| bb_width_144|quintile/4 & amihud_39|tercile/1 | up | 33663 | 2850 | +0.0159 | [+0.0032, +0.0286] | 0.0000 | True | True |
| bb_pct_b_5|quintile/1 | up | 118598 | 2850 | +0.0125 | [+0.0076, +0.0174] | 0.0000 | True | False |
| bb_width_9|quintile/5 & bb_width_144|tercile/1 | dn | 7813 | 2754 | -0.0224 | [-0.0343, -0.0105] | 0.0000 | True | True |
| entropy_39|quintile/2 | dn | 87753 | 2850 | -0.0059 | [-0.0094, -0.0024] | 0.0000 | True | True |
| kama_er_233|quintile/2 | up | 109756 | 2850 | -0.0078 | [-0.0131, -0.0024] | 0.0000 | True | False |
| vwap_zscore_233|quintile/5 | up | 104957 | 2850 | -0.0136 | [-0.0251, -0.0021] | 0.0000 | True | True |
| bb_width_144|quintile/4 & bb_width_233|quintile/2 | up | 5799 | 2005 | -0.0303 | [-0.0495, -0.0110] | 0.0000 | True | False |
| fib_dist_3|quintile/5 | up | 110888 | 2850 | -0.0117 | [-0.0158, -0.0075] | 0.0000 | True | True |
| vwap_zscore_233|quintile/4 | up | 106911 | 2850 | -0.0088 | [-0.0158, -0.0017] | 0.0000 | True | False |
| bb_pct_b_5|tercile/3 | up | 186226 | 2850 | -0.0093 | [-0.0130, -0.0056] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_3|tercile/3 | dn | 21923 | 2850 | -0.0131 | [-0.0195, -0.0066] | 0.0000 | True | True |
| hurst_89|tercile/1 | up | 186889 | 2850 | -0.0059 | [-0.0100, -0.0017] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_233|tercile/1 | up | 12789 | 2810 | -0.0228 | [-0.0330, -0.0126] | 0.0000 | True | False |
| entropy_15|tercile/1 | dn | 157793 | 2850 | -0.0042 | [-0.0067, -0.0017] | 0.0000 | True | True |
| amihud_233|tercile/2 | dn | 143538 | 2850 | -0.0044 | [-0.0082, -0.0007] | 0.0000 | True | False |
| entropy_21|tercile/3 | dn | 146130 | 2850 | +0.0046 | [+0.0016, +0.0077] | 0.0000 | True | True |
| entropy_233|quintile/1 | dn | 90073 | 2850 | +0.0073 | [+0.0012, +0.0133] | 0.0000 | True | True |
| bb_pct_b_5|quintile/4 | up | 112302 | 2850 | -0.0083 | [-0.0116, -0.0051] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_9|quintile/5 | up | 17797 | 2850 | +0.0184 | [+0.0087, +0.0281] | 0.0000 | True | True |
| kama_er_39|quintile/4 | dn | 87619 | 2850 | -0.0059 | [-0.0091, -0.0027] | 0.0000 | True | True |
| amihud_63|quintile/3 | up | 112057 | 2850 | -0.0062 | [-0.0114, -0.0010] | 0.0000 | True | False |
| bb_width_144|quintile/2 & amihud_9|quintile/5 | dn | 13049 | 2850 | -0.0156 | [-0.0268, -0.0044] | 0.0000 | True | False |
| bb_width_3|quintile/2 & amihud_3|quintile/5 | up | 16296 | 2850 | +0.0194 | [+0.0107, +0.0282] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_3|quintile/5 | up | 18513 | 2850 | +0.0175 | [+0.0052, +0.0299] | 0.0000 | True | False |
| hurst_55|quintile/1 | dn | 87512 | 2850 | -0.0073 | [-0.0125, -0.0021] | 0.0000 | True | False |
| hurst_102|quintile/1 | dn | 87338 | 2850 | -0.0065 | [-0.0108, -0.0022] | 0.0000 | True | False |
| donchian_break_13|tercile/3 | up | 45596 | 2699 | -0.0205 | [-0.0297, -0.0114] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_233|quintile/1 | dn | 3837 | 2008 | +0.0343 | [+0.0071, +0.0615] | 0.0000 | True | True |
| fib_dist_3|quintile/4 | up | 112553 | 2850 | -0.0075 | [-0.0100, -0.0049] | 0.0000 | True | False |
| atr_pct_34|quintile/4 & bb_width_233|quintile/1 | up | 4812 | 2008 | +0.0337 | [+0.0093, +0.0581] | 0.0000 | True | False |
| entropy_24|tercile/1 | up | 190612 | 2850 | -0.0050 | [-0.0087, -0.0013] | 0.0000 | True | True |
| atr_pct_34|tercile/2 | dn | 146254 | 2850 | -0.0063 | [-0.0123, -0.0003] | 0.0000 | True | False |
| entropy_55|quintile/5 | dn | 90794 | 2850 | +0.0069 | [+0.0014, +0.0125] | 0.0000 | True | False |
| vwap_zscore_144|quintile/5 | up | 107775 | 2850 | -0.0116 | [-0.0215, -0.0018] | 0.0000 | True | True |
| entropy_102|quintile/2 | up | 111921 | 2850 | -0.0061 | [-0.0107, -0.0014] | 0.0000 | True | False |
| bb_width_3|tercile/1 & amihud_6|quintile/5 | up | 25588 | 2850 | +0.0153 | [+0.0068, +0.0238] | 0.0000 | True | False |
| hurst_55|tercile/1 | dn | 146476 | 2850 | -0.0053 | [-0.0092, -0.0014] | 0.0000 | True | False |
| atr_pct_34|tercile/3 & bb_width_144|quintile/1 | dn | 1786 | 1202 | +0.0492 | [+0.0128, +0.0856] | 0.0000 | True | False |
| entropy_39|quintile/4 | dn | 90991 | 2850 | +0.0056 | [+0.0019, +0.0094] | 0.0000 | True | False |
| hurst_63|tercile/1 | dn | 146484 | 2850 | -0.0052 | [-0.0090, -0.0014] | 0.0000 | True | False |
| kama_er_144|quintile/3 | dn | 86768 | 2850 | -0.0055 | [-0.0092, -0.0018] | 0.0000 | True | True |
| vwap_zscore_144|quintile/2 | up | 113913 | 2850 | +0.0079 | [+0.0016, +0.0143] | 0.0000 | True | False |
| entropy_39|quintile/5 | dn | 90718 | 2850 | +0.0066 | [+0.0016, +0.0116] | 0.0000 | True | True |
| bb_pct_b_15|quintile/4 | dn | 87562 | 2850 | -0.0071 | [-0.0111, -0.0030] | 0.0000 | True | True |
| bb_width_9|quintile/5 & bb_width_233|tercile/1 | up | 10439 | 2758 | -0.0238 | [-0.0381, -0.0095] | 0.0000 | True | False |
| bb_width_9|quintile/5 & bb_width_144|quintile/1 | up | 4043 | 2141 | -0.0340 | [-0.0515, -0.0164] | 0.0000 | True | True |
| bb_width_9|quintile/1 & bb_width_144|quintile/5 | dn | 4206 | 2223 | +0.0332 | [+0.0132, +0.0532] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_9|quintile/2 | dn | 15645 | 2832 | -0.0148 | [-0.0202, -0.0094] | 0.0000 | True | True |
| entropy_24|quintile/1 | up | 113971 | 2850 | -0.0067 | [-0.0118, -0.0016] | 0.0000 | True | True |
| kama_er_144|quintile/5 | up | 115796 | 2850 | +0.0109 | [+0.0013, +0.0206] | 0.0000 | True | False |
| vwap_zscore_63|tercile/2 | dn | 145515 | 2850 | -0.0046 | [-0.0077, -0.0014] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_24|quintile/1 | dn | 16262 | 2850 | +0.0164 | [+0.0025, +0.0303] | 0.0000 | True | False |
| adx_233|tercile/2 | dn | 139920 | 2850 | -0.0044 | [-0.0082, -0.0006] | 0.0000 | True | False |
| entropy_24|quintile/1 | dn | 88887 | 2850 | -0.0065 | [-0.0116, -0.0013] | 0.0000 | True | True |
| bb_pct_b_3|quintile/1 | up | 118154 | 2850 | +0.0106 | [+0.0070, +0.0142] | 0.0000 | True | True |
| kama_er_34|quintile/4 | dn | 87781 | 2850 | -0.0056 | [-0.0086, -0.0025] | 0.0000 | True | True |
| di_spread_3|quintile/5 | up | 111076 | 2850 | -0.0111 | [-0.0174, -0.0048] | 0.0000 | True | True |
| entropy_21|quintile/1 | dn | 89745 | 2850 | -0.0062 | [-0.0112, -0.0012] | 0.0000 | True | True |
| bb_width_144|quintile/3 | dn | 86852 | 2850 | -0.0062 | [-0.0118, -0.0005] | 0.0000 | True | False |
| hurst_102|tercile/3 | up | 191654 | 2850 | +0.0053 | [+0.0011, +0.0095] | 0.0000 | True | True |
| bb_width_9|quintile/3 | dn | 87961 | 2850 | -0.0057 | [-0.0092, -0.0022] | 0.0000 | True | True |
| hurst_63|quintile/1 | dn | 87661 | 2850 | -0.0068 | [-0.0119, -0.0016] | 0.0000 | True | False |
| hurst_233|quintile/4 | up | 113760 | 2850 | +0.0058 | [+0.0025, +0.0091] | 0.0000 | True | False |
| bb_width_9|tercile/1 & bb_width_233|tercile/3 | dn | 21377 | 2850 | +0.0148 | [+0.0035, +0.0261] | 0.0000 | True | False |
| entropy_21|quintile/5 | dn | 84457 | 2850 | +0.0058 | [+0.0019, +0.0097] | 0.0000 | True | True |
| donchian_break_13|quintile/5 | up | 36039 | 2481 | -0.0204 | [-0.0296, -0.0112] | 0.0000 | True | True |
| vwap_zscore_89|tercile/3 | up | 183772 | 2850 | -0.0083 | [-0.0155, -0.0011] | 0.0000 | True | False |
| donchian_break_3|tercile/1 | up | 476884 | 2850 | +0.0029 | [+0.0017, +0.0040] | 0.0000 | True | True |
| bb_width_9|tercile/1 & bb_width_144|quintile/4 | up | 25229 | 2850 | -0.0139 | [-0.0240, -0.0037] | 0.0000 | True | True |
| hurst_89|quintile/1 | up | 112015 | 2850 | -0.0069 | [-0.0123, -0.0016] | 0.0000 | True | True |
| range_pos_5|quintile/1 | dn | 92690 | 2850 | +0.0095 | [+0.0048, +0.0142] | 0.0000 | True | True |
| bb_pct_b_3|tercile/1 | up | 195401 | 2850 | +0.0081 | [+0.0052, +0.0110] | 0.0000 | True | True |
| kama_er_55|quintile/4 | dn | 87743 | 2850 | -0.0052 | [-0.0083, -0.0021] | 0.0000 | True | True |
| obv_zscore_233|quintile/4 | up | 109972 | 2850 | -0.0077 | [-0.0102, -0.0051] | 0.0000 | True | True |
| entropy_24|quintile/5 | dn | 87609 | 2850 | +0.0057 | [+0.0015, +0.0099] | 0.0000 | True | False |
| kama_er_233|quintile/3 | up | 110486 | 2850 | -0.0059 | [-0.0105, -0.0012] | 0.0000 | True | True |
| bb_width_144|quintile/2 & amihud_6|quintile/5 | up | 18402 | 2850 | +0.0156 | [+0.0029, +0.0283] | 0.0000 | True | False |
| bb_width_9|quintile/4 & bb_width_233|quintile/2 | dn | 14214 | 2850 | -0.0144 | [-0.0234, -0.0053] | 0.0000 | True | True |
| hurst_102|quintile/1 | up | 111973 | 2850 | -0.0068 | [-0.0121, -0.0014] | 0.0000 | True | True |
| di_spread_3|quintile/4 | up | 112694 | 2850 | -0.0069 | [-0.0104, -0.0035] | 0.0000 | True | True |
| donchian_break_55|quintile/1 | dn | 427160 | 2850 | +0.0011 | [+0.0005, +0.0017] | 0.0000 | True | False |
| donchian_break_55|tercile/1 | dn | 427160 | 2850 | +0.0011 | [+0.0005, +0.0017] | 0.0000 | True | False |
| hurst_102|quintile/5 | up | 115278 | 2850 | +0.0068 | [+0.0014, +0.0122] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_9|quintile/1 | dn | 16037 | 2850 | +0.0151 | [+0.0017, +0.0284] | 0.0000 | True | False |
| donchian_break_3|quintile/1 | up | 475998 | 2850 | +0.0028 | [+0.0017, +0.0039] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_3|quintile/1 | dn | 15869 | 2849 | +0.0150 | [+0.0023, +0.0278] | 0.0000 | True | False |
| hurst_39|tercile/1 | dn | 146855 | 2850 | -0.0048 | [-0.0085, -0.0011] | 0.0000 | True | False |
| bb_width_9|quintile/2 & amihud_3|quintile/5 | dn | 12740 | 2850 | -0.0149 | [-0.0250, -0.0048] | 0.0000 | True | True |
| bb_width_3|tercile/3 & bb_width_9|tercile/1 | up | 16381 | 2757 | -0.0182 | [-0.0254, -0.0109] | 0.0000 | True | False |
| fib_dist_3|quintile/1 | dn | 92621 | 2850 | +0.0091 | [+0.0053, +0.0129] | 0.0000 | True | True |
| entropy_144|quintile/2 | dn | 87013 | 2850 | -0.0053 | [-0.0104, -0.0002] | 0.0000 | True | False |
| entropy_24|quintile/2 | dn | 88978 | 2850 | -0.0046 | [-0.0074, -0.0019] | 0.0000 | True | True |
| adx_144|quintile/4 | up | 113104 | 2850 | +0.0056 | [+0.0004, +0.0107] | 0.0000 | True | False |
| bb_width_9|quintile/2 & amihud_9|quintile/5 | dn | 12456 | 2850 | -0.0147 | [-0.0256, -0.0037] | 0.0000 | True | False |
| hurst_89|tercile/3 | up | 191693 | 2850 | +0.0048 | [+0.0008, +0.0089] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_233|quintile/4 | dn | 15923 | 2850 | +0.0138 | [+0.0063, +0.0212] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_6|quintile/5 | up | 17711 | 2850 | +0.0157 | [+0.0056, +0.0257] | 0.0000 | True | True |
| bb_width_9|quintile/1 & bb_width_233|quintile/4 | up | 12186 | 2840 | -0.0193 | [-0.0338, -0.0049] | 0.0000 | True | True |
| bb_width_144|quintile/4 & amihud_6|quintile/1 | dn | 15931 | 2850 | +0.0147 | [+0.0012, +0.0281] | 0.0000 | True | False |
| kama_er_144|tercile/2 | up | 186764 | 2850 | -0.0041 | [-0.0079, -0.0003] | 0.0000 | True | False |
| obv_zscore_233|tercile/3 | up | 183194 | 2850 | -0.0068 | [-0.0096, -0.0041] | 0.0000 | True | True |
| kama_er_102|tercile/2 | up | 187545 | 2850 | -0.0039 | [-0.0070, -0.0008] | 0.0000 | True | False |
| hurst_102|tercile/1 | dn | 146312 | 2850 | -0.0042 | [-0.0074, -0.0009] | 0.0000 | True | False |
| bb_width_9|quintile/2 & amihud_6|quintile/5 | dn | 12464 | 2850 | -0.0144 | [-0.0253, -0.0035] | 0.0000 | True | True |
| bb_width_3|quintile/5 & bb_width_144|tercile/1 | up | 13494 | 2821 | -0.0180 | [-0.0274, -0.0086] | 0.0000 | True | False |
| entropy_15|quintile/1 | dn | 95395 | 2850 | -0.0051 | [-0.0089, -0.0012] | 0.0000 | True | True |
| atr_pct_34|quintile/4 & bb_width_144|quintile/1 | dn | 3717 | 2041 | +0.0293 | [+0.0041, +0.0546] | 0.0000 | True | False |
| bb_pct_b_5|quintile/5 | up | 111356 | 2850 | -0.0098 | [-0.0144, -0.0053] | 0.0000 | True | True |
| hurst_233|tercile/2 | dn | 144419 | 2850 | -0.0031 | [-0.0051, -0.0012] | 0.0000 | True | False |
| bb_pct_b_5|quintile/2 | up | 116682 | 2850 | +0.0067 | [+0.0036, +0.0099] | 0.0000 | True | True |
| kama_er_34|tercile/3 | up | 187369 | 2850 | -0.0062 | [-0.0118, -0.0006] | 0.0000 | True | False |
| bb_width_9|tercile/1 & amihud_24|quintile/5 | up | 23024 | 2850 | -0.0135 | [-0.0241, -0.0028] | 0.0000 | True | False |
| kama_er_24|tercile/3 | up | 187575 | 2850 | -0.0062 | [-0.0117, -0.0007] | 0.0000 | True | False |
| vwap_zscore_89|quintile/5 | up | 109598 | 2850 | -0.0100 | [-0.0194, -0.0005] | 0.0000 | True | False |
| bb_pct_b_15|tercile/1 | dn | 152733 | 2850 | +0.0067 | [+0.0016, +0.0119] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_39|quintile/5 | up | 17370 | 2850 | +0.0156 | [+0.0057, +0.0255] | 0.0000 | True | False |
| bb_width_9|tercile/1 & amihud_39|quintile/5 | up | 23236 | 2850 | -0.0131 | [-0.0239, -0.0024] | 0.0000 | True | False |
| bb_width_9|quintile/5 & bb_width_233|quintile/2 | dn | 7842 | 2769 | +0.0189 | [+0.0056, +0.0321] | 0.0000 | True | False |
| di_spread_55|quintile/2 | up | 115989 | 2850 | +0.0064 | [+0.0007, +0.0121] | 0.0000 | True | True |
| hurst_34|quintile/1 | dn | 88006 | 2850 | -0.0060 | [-0.0106, -0.0015] | 0.0000 | True | False |
| hurst_233|quintile/4 | dn | 88778 | 2850 | +0.0043 | [+0.0017, +0.0068] | 0.0000 | True | True |
| bb_pct_b_15|quintile/1 | dn | 92333 | 2850 | +0.0085 | [+0.0021, +0.0148] | 0.0000 | True | False |
| bb_width_9|quintile/5 & bb_width_233|tercile/1 | dn | 7903 | 2758 | -0.0169 | [-0.0296, -0.0043] | 0.0000 | True | False |
| hurst_39|quintile/1 | dn | 88000 | 2850 | -0.0058 | [-0.0107, -0.0009] | 0.0000 | True | False |
| kama_er_24|quintile/5 | up | 111797 | 2850 | -0.0081 | [-0.0157, -0.0005] | 0.0000 | True | False |
| kama_er_63|quintile/4 | dn | 87894 | 2850 | -0.0046 | [-0.0081, -0.0011] | 0.0000 | True | False |
| hurst_144|quintile/4 | dn | 89707 | 2850 | +0.0044 | [+0.0014, +0.0073] | 0.0000 | True | True |
| kama_er_102|quintile/4 | dn | 87414 | 2850 | -0.0049 | [-0.0091, -0.0007] | 0.0000 | True | False |
| hurst_34|tercile/1 | dn | 147161 | 2850 | -0.0044 | [-0.0079, -0.0008] | 0.0000 | True | False |
| di_spread_55|tercile/2 | dn | 147031 | 2850 | -0.0035 | [-0.0067, -0.0003] | 0.0000 | True | False |
| bb_width_3|quintile/1 & amihud_24|quintile/5 | up | 16991 | 2850 | +0.0150 | [+0.0051, +0.0248] | 0.0000 | True | False |
| hurst_34|tercile/3 | dn | 150699 | 2850 | +0.0043 | [+0.0008, +0.0077] | 0.0000 | True | True |
| kama_er_21|tercile/3 | up | 187852 | 2850 | -0.0058 | [-0.0110, -0.0006] | 0.0000 | True | False |
| bb_pct_b_3|tercile/3 | up | 187445 | 2850 | -0.0068 | [-0.0095, -0.0040] | 0.0000 | True | True |
| atr_pct_34|tercile/3 & bb_width_144|quintile/1 | up | 2226 | 1202 | +0.0406 | [+0.0033, +0.0778] | 0.0000 | True | False |
| bb_width_3|quintile/1 & amihud_3|quintile/5 | dn | 7867 | 2812 | -0.0174 | [-0.0278, -0.0070] | 0.0000 | True | False |
| kama_er_24|tercile/1 | dn | 151753 | 2850 | +0.0044 | [+0.0003, +0.0085] | 0.0000 | True | False |
| bb_width_9|quintile/5 & bb_width_144|tercile/1 | up | 10704 | 2754 | -0.0179 | [-0.0310, -0.0048] | 0.0000 | True | False |
| bb_width_144|quintile/2 & bb_width_233|quintile/4 | dn | 7722 | 2797 | -0.0170 | [-0.0340, -0.0001] | 0.0000 | True | True |
| fib_dist_3|quintile/4 | dn | 88195 | 2850 | -0.0052 | [-0.0076, -0.0028] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_9|quintile/4 | dn | 13743 | 2850 | +0.0126 | [+0.0069, +0.0183] | 0.0000 | True | True |
| vwap_zscore_34|quintile/5 | dn | 91229 | 2850 | +0.0081 | [+0.0007, +0.0155] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_24|tercile/3 | up | 32114 | 2850 | +0.0102 | [+0.0033, +0.0171] | 0.0000 | True | True |
| hurst_39|quintile/5 | dn | 90630 | 2850 | +0.0056 | [+0.0008, +0.0103] | 0.0000 | True | True |
| range_pos_5|quintile/2 | up | 116335 | 2850 | +0.0057 | [+0.0025, +0.0089] | 0.0000 | True | True |
| entropy_13|tercile/1 | dn | 164627 | 2850 | -0.0029 | [-0.0051, -0.0006] | 0.0000 | True | True |
| range_pos_5|tercile/1 | dn | 152450 | 2850 | +0.0059 | [+0.0022, +0.0095] | 0.0000 | True | True |
| hurst_39|tercile/3 | dn | 150522 | 2850 | +0.0040 | [+0.0004, +0.0075] | 0.0000 | True | True |
| obv_zscore_233|quintile/4 | dn | 85992 | 2850 | -0.0056 | [-0.0083, -0.0029] | 0.0000 | True | False |
| hurst_102|quintile/2 | up | 112253 | 2850 | -0.0045 | [-0.0079, -0.0011] | 0.0000 | True | True |
| kama_er_24|quintile/2 | up | 115910 | 2850 | +0.0051 | [+0.0012, +0.0090] | 0.0000 | True | False |
| kama_er_34|tercile/1 | dn | 151566 | 2850 | +0.0044 | [+0.0001, +0.0087] | 0.0000 | True | False |
| range_pos_5|quintile/4 | dn | 88222 | 2850 | -0.0052 | [-0.0078, -0.0025] | 0.0000 | True | True |
| bb_width_9|quintile/2 & amihud_3|quintile/5 | up | 18059 | 2850 | +0.0132 | [+0.0038, +0.0226] | 0.0000 | True | True |
| vwap_zscore_63|quintile/3 | dn | 87381 | 2850 | -0.0044 | [-0.0081, -0.0007] | 0.0000 | True | False |
| kama_er_34|quintile/1 | dn | 91388 | 2850 | +0.0053 | [+0.0006, +0.0100] | 0.0000 | True | False |
| donchian_break_55|tercile/3 | dn | 20967 | 2614 | -0.0163 | [-0.0269, -0.0057] | 0.0000 | True | False |
| bb_width_3|quintile/2 & amihud_39|tercile/3 | up | 32118 | 2850 | +0.0096 | [+0.0027, +0.0166] | 0.0000 | True | True |
| donchian_break_55|quintile/5 | dn | 19920 | 2592 | -0.0163 | [-0.0275, -0.0051] | 0.0000 | True | True |
| bb_pct_b_3|quintile/4 | up | 113019 | 2850 | -0.0058 | [-0.0083, -0.0033] | 0.0000 | True | True |
| entropy_21|quintile/1 | up | 115610 | 2850 | -0.0047 | [-0.0093, -0.0001] | 0.0000 | True | True |
| bb_width_3|tercile/1 & bb_width_144|quintile/4 | dn | 24403 | 2850 | +0.0092 | [+0.0015, +0.0170] | 0.0000 | True | False |
| hurst_55|tercile/3 | dn | 150094 | 2850 | +0.0037 | [+0.0003, +0.0072] | 0.0000 | True | False |
| donchian_break_3|tercile/3 | up | 67613 | 2470 | -0.0125 | [-0.0195, -0.0056] | 0.0000 | True | True |
| donchian_break_3|tercile/2 | up | 29091 | 343 | -0.0151 | [-0.0231, -0.0071] | 0.0000 | True | False |
| kama_er_24|tercile/1 | up | 193175 | 2850 | +0.0045 | [+0.0001, +0.0089] | 0.0000 | True | False |
| kama_er_39|tercile/1 | dn | 151305 | 2850 | +0.0040 | [+0.0000, +0.0080] | 0.0000 | True | False |
| kama_er_24|quintile/1 | dn | 91413 | 2850 | +0.0050 | [+0.0004, +0.0095] | 0.0000 | True | False |
| bb_width_3|quintile/1 & bb_width_233|quintile/4 | up | 17439 | 2848 | +0.0133 | [+0.0039, +0.0226] | 0.0000 | True | True |
| hurst_89|quintile/5 | up | 114897 | 2850 | +0.0052 | [+0.0001, +0.0104] | 0.0000 | True | True |
| donchian_break_3|quintile/3 | up | 16706 | 192 | -0.0183 | [-0.0248, -0.0118] | 0.0000 | True | True |
| entropy_21|quintile/2 | dn | 90499 | 2850 | -0.0036 | [-0.0062, -0.0010] | 0.0000 | True | False |
| bb_width_3|tercile/3 & bb_width_144|quintile/2 | dn | 18870 | 2850 | -0.0097 | [-0.0172, -0.0022] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_9|quintile/4 | up | 17452 | 2850 | +0.0125 | [+0.0065, +0.0185] | 0.0000 | True | True |
| di_spread_3|tercile/2 | dn | 147979 | 2850 | -0.0031 | [-0.0049, -0.0013] | 0.0000 | True | True |
| hurst_21|quintile/5 | dn | 90492 | 2850 | +0.0047 | [+0.0012, +0.0081] | 0.0000 | True | False |
| fib_dist_3|tercile/1 | dn | 152245 | 2850 | +0.0054 | [+0.0025, +0.0082] | 0.0000 | True | True |
| donchian_break_3|quintile/5 | up | 35475 | 1811 | -0.0158 | [-0.0249, -0.0067] | 0.0000 | True | True |
| di_spread_3|quintile/3 | dn | 88504 | 2850 | -0.0039 | [-0.0060, -0.0019] | 0.0000 | True | True |
| kama_er_21|quintile/2 | up | 115788 | 2850 | +0.0047 | [+0.0008, +0.0086] | 0.0000 | True | False |
| hurst_34|quintile/5 | dn | 90442 | 2850 | +0.0049 | [+0.0005, +0.0093] | 0.0000 | True | False |
| hurst_21|tercile/3 | dn | 150517 | 2850 | +0.0035 | [+0.0007, +0.0063] | 0.0000 | True | False |
| bb_width_3|tercile/1 & amihud_3|quintile/5 | dn | 15476 | 2850 | -0.0105 | [-0.0194, -0.0016] | 0.0000 | True | False |
| kama_er_39|quintile/1 | dn | 91174 | 2850 | +0.0047 | [+0.0003, +0.0092] | 0.0000 | True | False |
| kama_er_15|tercile/3 | up | 188359 | 2850 | -0.0047 | [-0.0093, -0.0001] | 0.0000 | True | False |
| kama_er_55|tercile/2 | dn | 147411 | 2850 | -0.0027 | [-0.0049, -0.0004] | 0.0000 | True | False |
| bb_pct_b_3|quintile/5 | up | 112042 | 2850 | -0.0074 | [-0.0110, -0.0038] | 0.0000 | True | True |
| kama_er_15|quintile/2 | up | 115818 | 2850 | +0.0044 | [+0.0012, +0.0075] | 0.0000 | True | True |
| bb_width_3|quintile/2 & bb_width_144|quintile/4 | up | 20124 | 2850 | +0.0106 | [+0.0027, +0.0184] | 0.0000 | True | True |
| entropy_13|quintile/1 | dn | 97453 | 2850 | -0.0036 | [-0.0068, -0.0003] | 0.0000 | True | False |
| kama_er_3|quintile/5 | dn | 28151 | 875 | +0.0094 | [+0.0038, +0.0151] | 0.0000 | True | False |
| entropy_15|quintile/5 | dn | 78876 | 2850 | +0.0039 | [+0.0006, +0.0072] | 0.0000 | True | True |
| donchian_break_13|quintile/4 | up | 11847 | 249 | -0.0209 | [-0.0342, -0.0076] | 0.0000 | True | False |
| hurst_144|tercile/2 | dn | 146224 | 2850 | -0.0025 | [-0.0043, -0.0006] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_3|quintile/5 | up | 21032 | 2850 | +0.0110 | [+0.0019, +0.0200] | 0.0000 | True | False |
| bb_width_3|quintile/2 & amihud_9|tercile/3 | up | 31536 | 2850 | +0.0086 | [+0.0017, +0.0154] | 0.0000 | True | True |
| kama_er_102|quintile/3 | up | 112568 | 2850 | -0.0038 | [-0.0074, -0.0002] | 0.0000 | True | False |
| vwap_zscore_9|tercile/2 | dn | 147824 | 2850 | -0.0030 | [-0.0047, -0.0012] | 0.0000 | True | True |
| entropy_21|quintile/4 | dn | 91880 | 2850 | +0.0034 | [+0.0007, +0.0060] | 0.0000 | True | True |
| bb_width_9|quintile/2 & bb_width_144|quintile/4 | dn | 15881 | 2850 | +0.0098 | [+0.0003, +0.0194] | 0.0000 | True | False |
| vwap_zscore_9|quintile/3 | dn | 88427 | 2850 | -0.0038 | [-0.0060, -0.0017] | 0.0000 | True | True |
| hurst_55|quintile/4 | dn | 90221 | 2850 | +0.0035 | [+0.0007, +0.0063] | 0.0000 | True | False |
| bb_pct_b_3|tercile/2 | dn | 147871 | 2850 | -0.0033 | [-0.0050, -0.0016] | 0.0000 | True | False |
| entropy_15|tercile/3 | dn | 128955 | 2850 | +0.0029 | [+0.0001, +0.0056] | 0.0000 | True | True |
| bb_width_3|quintile/1 & amihud_9|quintile/5 | up | 15555 | 2849 | +0.0123 | [+0.0024, +0.0222] | 0.0000 | True | False |
| donchian_break_3|quintile/4 | dn | 33390 | 796 | -0.0104 | [-0.0157, -0.0051] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_39|quintile/5 | dn | 13975 | 2850 | +0.0102 | [+0.0009, +0.0195] | 0.0000 | True | False |
| vwap_zscore_21|quintile/2 | dn | 88075 | 2850 | -0.0043 | [-0.0081, -0.0004] | 0.0000 | True | True |
| bb_pct_b_5|quintile/1 | dn | 91828 | 2850 | +0.0065 | [+0.0022, +0.0108] | 0.0000 | True | False |
| vwap_zscore_34|quintile/2 | dn | 87890 | 2850 | -0.0042 | [-0.0082, -0.0002] | 0.0000 | True | False |
| kama_er_24|quintile/4 | dn | 88452 | 2850 | -0.0034 | [-0.0062, -0.0005] | 0.0000 | True | False |
| vwap_zscore_34|tercile/2 | dn | 147190 | 2850 | -0.0027 | [-0.0052, -0.0002] | 0.0000 | True | True |
| bb_width_3|quintile/2 & amihud_6|tercile/3 | dn | 23236 | 2850 | -0.0073 | [-0.0138, -0.0007] | 0.0000 | True | False |
| bb_width_3|quintile/1 & amihud_3|tercile/3 | up | 20062 | 2850 | -0.0098 | [-0.0175, -0.0021] | 0.0000 | True | False |
| vwap_zscore_15|quintile/5 | dn | 90896 | 2850 | +0.0059 | [+0.0007, +0.0110] | 0.0000 | True | False |
| hurst_24|quintile/5 | dn | 90246 | 2850 | +0.0041 | [+0.0000, +0.0081] | 0.0000 | True | False |
| hurst_144|quintile/3 | dn | 87553 | 2850 | -0.0030 | [-0.0051, -0.0009] | 0.0000 | True | True |
| hurst_233|quintile/3 | dn | 86676 | 2850 | -0.0029 | [-0.0052, -0.0007] | 0.0000 | True | True |
| bb_width_3|tercile/1 & amihud_3|tercile/3 | up | 38496 | 2850 | -0.0070 | [-0.0137, -0.0004] | 0.0000 | True | False |
| kama_er_24|quintile/4 | up | 113469 | 2850 | -0.0036 | [-0.0068, -0.0004] | 0.0000 | True | False |
| vwap_zscore_9|quintile/5 | dn | 90921 | 2850 | +0.0057 | [+0.0018, +0.0096] | 0.0000 | True | True |
| range_pos_5|tercile/3 | dn | 147154 | 2850 | -0.0043 | [-0.0080, -0.0007] | 0.0000 | True | False |
| bb_pct_b_3|quintile/3 | dn | 88554 | 2850 | -0.0038 | [-0.0059, -0.0017] | 0.0000 | True | False |
| bb_width_3|quintile/1 & amihud_6|quintile/5 | dn | 10588 | 2848 | -0.0105 | [-0.0206, -0.0005] | 0.0001 | True | False |
| entropy_13|quintile/5 | dn | 70740 | 2850 | +0.0035 | [+0.0005, +0.0065] | 0.0001 | True | False |
| kama_er_55|quintile/3 | dn | 88405 | 2850 | -0.0029 | [-0.0057, -0.0002] | 0.0001 | True | False |
| bb_width_144|quintile/1 & bb_width_233|quintile/5 | up | 66 | 70 | -0.0956 | [-0.1872, -0.0041] | 0.0001 | True | False |
| di_spread_3|quintile/1 | dn | 91525 | 2850 | +0.0055 | [+0.0002, +0.0108] | 0.0001 | True | False |
| obv_zscore_233|tercile/1 | dn | 144175 | 2850 | -0.0038 | [-0.0060, -0.0016] | 0.0001 | True | False |
| bb_width_3|quintile/2 & amihud_6|tercile/3 | up | 31010 | 2850 | +0.0070 | [+0.0002, +0.0138] | 0.0001 | True | False |
| obv_zscore_233|quintile/5 | up | 110130 | 2850 | -0.0053 | [-0.0094, -0.0011] | 0.0001 | True | False |
| fib_dist_3|quintile/2 | up | 115882 | 2850 | +0.0039 | [+0.0014, +0.0063] | 0.0001 | True | True |
| bb_pct_b_5|tercile/1 | dn | 151644 | 2850 | +0.0042 | [+0.0010, +0.0074] | 0.0001 | True | False |
| bb_pct_b_3|quintile/2 | up | 116019 | 2850 | +0.0042 | [+0.0014, +0.0070] | 0.0002 | True | True |
| bb_width_3|quintile/1 & amihud_6|quintile/5 | up | 14363 | 2848 | +0.0105 | [+0.0011, +0.0199] | 0.0002 | True | False |
| hurst_63|tercile/2 | up | 189115 | 2850 | -0.0021 | [-0.0040, -0.0002] | 0.0002 | True | False |
| hurst_34|quintile/4 | dn | 90177 | 2850 | +0.0028 | [+0.0005, +0.0052] | 0.0002 | True | True |
| bb_pct_b_3|tercile/1 | dn | 151654 | 2850 | +0.0040 | [+0.0014, +0.0065] | 0.0002 | True | False |
| kama_er_8|tercile/3 | up | 189089 | 2850 | -0.0033 | [-0.0065, -0.0001] | 0.0002 | True | False |
| bb_pct_b_5|tercile/2 | dn | 148273 | 2850 | -0.0025 | [-0.0043, -0.0006] | 0.0002 | True | False |
| di_spread_3|quintile/2 | up | 115782 | 2850 | +0.0037 | [+0.0004, +0.0069] | 0.0003 | True | True |
| donchian_break_13|quintile/1 | dn | 407292 | 2850 | +0.0009 | [+0.0001, +0.0017] | 0.0003 | True | False |
| donchian_break_13|tercile/1 | dn | 407292 | 2850 | +0.0009 | [+0.0001, +0.0017] | 0.0003 | True | False |
| bb_pct_b_15|tercile/2 | dn | 148147 | 2850 | -0.0024 | [-0.0047, -0.0000] | 0.0003 | True | False |
| kama_er_13|quintile/2 | up | 115513 | 2850 | +0.0032 | [+0.0003, +0.0062] | 0.0004 | True | True |
| vwap_zscore_15|tercile/2 | dn | 148046 | 2850 | -0.0023 | [-0.0045, -0.0001] | 0.0005 | True | False |
| hurst_39|quintile/2 | dn | 88612 | 2850 | -0.0026 | [-0.0049, -0.0003] | 0.0005 | True | False |
| kama_er_15|quintile/4 | up | 113720 | 2850 | -0.0029 | [-0.0058, -0.0001] | 0.0005 | True | False |
| vwap_zscore_3|quintile/3 | dn | 88787 | 2850 | -0.0030 | [-0.0051, -0.0010] | 0.0005 | True | False |
| hurst_24|quintile/2 | dn | 88690 | 2850 | -0.0026 | [-0.0047, -0.0005] | 0.0005 | True | True |
| bb_width_3|tercile/1 & bb_width_9|quintile/4 | dn | 19831 | 2848 | +0.0068 | [+0.0015, +0.0122] | 0.0005 | True | False |
| hurst_63|quintile/2 | dn | 88414 | 2850 | -0.0026 | [-0.0050, -0.0002] | 0.0005 | True | False |
| vwap_zscore_6|quintile/5 | dn | 90698 | 2850 | +0.0048 | [+0.0015, +0.0081] | 0.0006 | True | True |
| vwap_zscore_3|tercile/2 | dn | 148389 | 2850 | -0.0023 | [-0.0039, -0.0006] | 0.0006 | True | False |
| obv_zscore_5|quintile/5 | dn | 90521 | 2850 | +0.0042 | [+0.0020, +0.0063] | 0.0007 | True | True |
| bb_pct_b_3|quintile/4 | dn | 88717 | 2850 | -0.0034 | [-0.0059, -0.0009] | 0.0007 | True | False |
| bb_pct_b_5|quintile/4 | dn | 88747 | 2850 | -0.0034 | [-0.0062, -0.0006] | 0.0007 | True | False |
| obv_zscore_5|tercile/2 | dn | 148433 | 2850 | -0.0021 | [-0.0036, -0.0006] | 0.0009 | True | False |
| obv_zscore_5|quintile/4 | dn | 88765 | 2850 | -0.0031 | [-0.0049, -0.0014] | 0.0009 | True | False |
| obv_zscore_3|quintile/5 | dn | 90486 | 2850 | +0.0039 | [+0.0021, +0.0058] | 0.0009 | True | False |
| bb_pct_b_5|quintile/3 | dn | 88851 | 2850 | -0.0029 | [-0.0051, -0.0006] | 0.0010 | True | False |
| range_pos_5|tercile/2 | up | 190127 | 2850 | -0.0022 | [-0.0041, -0.0004] | 0.0011 | True | False |
| fib_dist_3|tercile/3 | dn | 147601 | 2850 | -0.0034 | [-0.0062, -0.0005] | 0.0011 | True | True |
| kama_er_6|tercile/3 | up | 189318 | 2850 | -0.0030 | [-0.0059, -0.0001] | 0.0012 | True | False |
| vwap_zscore_6|tercile/2 | dn | 148352 | 2850 | -0.0020 | [-0.0039, -0.0001] | 0.0014 | True | False |
| donchian_break_13|quintile/4 | dn | 9841 | 249 | -0.0133 | [-0.0246, -0.0021] | 0.0016 | True | True |
| bb_width_3|quintile/5 & bb_width_144|quintile/2 | dn | 9347 | 2820 | +0.0090 | [+0.0000, +0.0179] | 0.0016 | True | False |
| vwap_zscore_15|quintile/3 | dn | 88741 | 2850 | -0.0026 | [-0.0051, -0.0000] | 0.0017 | True | False |
| kama_er_3|tercile/3 | dn | 126491 | 2415 | +0.0026 | [+0.0006, +0.0047] | 0.0020 | True | False |
| vwap_zscore_9|tercile/3 | dn | 150681 | 2850 | +0.0033 | [+0.0003, +0.0063] | 0.0021 | True | True |
| vwap_zscore_6|quintile/2 | dn | 88793 | 2850 | -0.0029 | [-0.0052, -0.0006] | 0.0026 | True | False |
| entropy_15|quintile/2 | dn | 91411 | 2850 | -0.0021 | [-0.0039, -0.0002] | 0.0029 | True | True |
| kama_er_9|quintile/2 | up | 115411 | 2850 | +0.0027 | [+0.0000, +0.0053] | 0.0033 | True | False |
| hurst_15|quintile/3 | dn | 88897 | 2850 | -0.0020 | [-0.0034, -0.0006] | 0.0043 | True | True |
| obv_zscore_5|quintile/3 | dn | 88973 | 2850 | -0.0024 | [-0.0042, -0.0006] | 0.0049 | True | True |
| adx_3|quintile/3 | up | 115403 | 2850 | +0.0023 | [+0.0001, +0.0044] | 0.0074 | True | False |
| kama_er_6|quintile/3 | dn | 89037 | 2850 | -0.0020 | [-0.0037, -0.0002] | 0.0082 | True | False |
| kama_er_3|quintile/3 | up | 129635 | 2824 | +0.0021 | [+0.0003, +0.0039] | 0.0105 | True | False |
| kama_er_6|tercile/2 | up | 191939 | 2850 | +0.0016 | [+0.0000, +0.0031] | 0.0112 | True | False |
| vwap_zscore_6|tercile/3 | dn | 150449 | 2850 | +0.0027 | [+0.0004, +0.0050] | 0.0114 | True | True |
| obv_zscore_3|quintile/3 | dn | 89060 | 2850 | -0.0021 | [-0.0041, -0.0002] | 0.0152 | True | False |
| kama_er_3|tercile/2 | dn | 170600 | 2836 | -0.0013 | [-0.0026, -0.0000] | 0.0163 | True | False |
| vwap_zscore_3|quintile/5 | dn | 90250 | 2850 | +0.0032 | [+0.0009, +0.0055] | 0.0172 | True | True |
| obv_zscore_3|tercile/3 | dn | 150282 | 2850 | +0.0022 | [+0.0010, +0.0034] | 0.0188 | True | False |
| obv_zscore_5|quintile/5 | up | 115078 | 2850 | +0.0030 | [+0.0008, +0.0052] | 0.0254 | True | False |
| vwap_zscore_3|tercile/3 | dn | 150182 | 2850 | +0.0021 | [+0.0006, +0.0036] | 0.0470 | True | True |

## Closest to passing (smallest p, regardless of outcome)

| condition | dir | n_dates | lift | 95% CI | p | q | same-sign (2 windows) | folds same-sign |
|---|---|---|---|---|---|---|---|---|
| amihud_102|quintile/1 | up | 2850 | -0.0530 | [-0.0607, -0.0454] | 0.0000 | 0.0000 | True | True |
| amihud_102|quintile/5 | up | 2850 | +0.0714 | [+0.0633, +0.0794] | 0.0000 | 0.0000 | True | True |
| amihud_102|quintile/5 | dn | 2850 | +0.0507 | [+0.0412, +0.0602] | 0.0000 | 0.0000 | True | True |
| amihud_102|tercile/1 | up | 2850 | -0.0453 | [-0.0514, -0.0393] | 0.0000 | 0.0000 | True | True |
| amihud_102|tercile/1 | dn | 2850 | -0.0371 | [-0.0439, -0.0303] | 0.0000 | 0.0000 | True | True |
| amihud_102|tercile/3 | up | 2850 | +0.0541 | [+0.0480, +0.0602] | 0.0000 | 0.0000 | True | True |
| amihud_102|tercile/3 | dn | 2850 | +0.0375 | [+0.0305, +0.0445] | 0.0000 | 0.0000 | True | True |
| amihud_144|quintile/1 | up | 2850 | -0.0532 | [-0.0612, -0.0453] | 0.0000 | 0.0000 | True | True |
| amihud_144|quintile/5 | up | 2850 | +0.0713 | [+0.0631, +0.0794] | 0.0000 | 0.0000 | True | True |
| amihud_144|quintile/5 | dn | 2850 | +0.0506 | [+0.0414, +0.0599] | 0.0000 | 0.0000 | True | True |

Robustness reads at `first_touch_24`/`first_touch_39` are reported for survivors only and are never selection targets; decisions always use `first_touch_34`.

## Self-check

```
  OK   family_counts_consistent: total=3658 vs univariate=1408 + conjunction=2250
  OK   conjunctions_built_only_from_univariate_survivors: pairs=1125 from 50 states; univariate BH rejects=931 at alpha=0.05
  OK   fdr_applied_over_whole_family: Benjamini-Hochberg over the complete family (univariate + conjunctions) at alpha=0.05
  OK   folds_and_embargo_recorded: 5 folds, embargo 34 td
  OK   every_survivor_passes_all_criteria: 2506 survivors checked
  OK   pass_and_gate_flags_consistent: g2_pass=True red_flag=True g3_eligible=False g3_skipped=True survivors=2506
  OK   g3_skip_reason_recorded: survivor density 0.685 > 0.1: a wall of survivors is a noise/leakage red flag, not a win, so G3 is not invoked
  OK   density_red_flag_consistent: density=0.6850738108255877 red_flag=True
  OK   determinism_config_present: circular 20-date blocks, 1000 draws, seed 42
  OK   survivors_carry_secondary_reads_only: secondary targets ['first_touch_24', 'first_touch_39'] present for every survivor
  OK   unconditional_reference_present: held-out rates={'up': 0.3794, 'dn': 0.2976, 'neither': 0.3229}
```

No executable rules and no shortlist are produced by G2.
