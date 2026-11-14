# GMM STATES (WI-027b): unsupervised GMM (3 & 4 components) soft states

GaussianMixture(random_state=0, n_init=10, covariance_type=full), sklearn only (no hmmlearn); fit on CALIB (date < 2022-05-02) pooled rows (market ignored; per-market rows descriptive); features r1, r1_s5, r2, ret63, ret126, realized_vol63, float32, standardized (scaler fit on CALIB only); EVAL predicted once with the frozen model.

## 3-state GMM

### Per-state characterization (CALIB dates only; names are SUGGESTIONS ONLY — downstream stages use the raw probability vector, never the name)

| state | n_dates | mean r1 | mean r1_s5 | mean r2 | mean ret63 | mean ret126 | mean realized_vol63 | suggestion |
|---|---|---|---|---|---|---|---|---|
| s0 | 3649 | -1.388421 | -1.391375 | 0.583274 | 0.011692 | 0.025309 | 0.181930 | calm bull |
| s1 | 5134 | -1.394568 | -1.393275 | 0.568366 | -0.021785 | -0.058813 | 1.943307 | volatile bear |
| s2 | 875 | -1.378607 | -1.373641 | 0.558289 | 1.501936 | 1.947598 | 6.414822 | volatile bull |

### Per-state conditional edge (CALIB bottoms, own-market states; same format as WI-027 REGIME_LABELS.md; pooled ALL is the headline)

| state | market | n_events | screened rate | edge_pp | n_folds_pos |
|---|---|---|---|---|---|
| s0 | CAD | 10174 | 0.0681 | 7.5123 | 5 |
| s1 | CAD | 6858 | 0.0582 | 18.4259 | 4 |
| s2 | CAD | 1953 | 0.0824 | 8.7169 | 2 |
| na | CAD | 519 | 0.0597 | 2.3454 | 3 |
| s0 | USD | 16850 | 0.0647 | 11.0006 | 3 |
| s1 | USD | 7730 | 0.0455 | 15.1742 | 4 |
| s2 | USD | 1555 | 0.0900 | 30.1356 | 5 |
| na | USD | 7849 | 0.0594 | 3.5997 | 3 |
| s0 | ALL | 27024 | 0.0660 | 9.7744 | 4 |
| s1 | ALL | 14588 | 0.0515 | 17.8068 | 4 |
| s2 | ALL | 3508 | 0.0858 | 19.5973 | 4 |
| na | ALL | 8368 | 0.0594 | 1.8910 | 4 |

## 4-state GMM

### Per-state characterization (CALIB dates only; names are SUGGESTIONS ONLY — downstream stages use the raw probability vector, never the name)

| state | n_dates | mean r1 | mean r1_s5 | mean r2 | mean ret63 | mean ret126 | mean realized_vol63 | suggestion |
|---|---|---|---|---|---|---|---|---|
| s0 | 1443 | -1.399086 | -1.390158 | 0.576838 | 0.209281 | 0.402604 | 3.853349 | volatile bull |
| s1 | 3554 | -1.390845 | -1.392872 | 0.583237 | 0.014241 | 0.029741 | 0.177347 | calm bull |
| s2 | 94 | -1.407392 | -1.381049 | 0.453977 | 11.331921 | 11.348086 | 22.859434 | volatile bull |
| s3 | 4567 | -1.387804 | -1.389545 | 0.566452 | -0.037835 | -0.056672 | 1.732934 | volatile bear |

### Per-state conditional edge (CALIB bottoms, own-market states; same format as WI-027 REGIME_LABELS.md; pooled ALL is the headline)

| state | market | n_events | screened rate | edge_pp | n_folds_pos |
|---|---|---|---|---|---|
| s0 | CAD | 3730 | 0.0660 | 9.4920 | 2 |
| s1 | CAD | 9925 | 0.0627 | 5.3067 | 5 |
| s2 | CAD | 0 | nan | nan | - |
| s3 | CAD | 5330 | 0.0722 | 21.6249 | 5 |
| na | CAD | 519 | 0.0597 | 2.3454 | 3 |
| s0 | USD | 1558 | 0.0623 | 42.6245 | 5 |
| s1 | USD | 16283 | 0.0606 | 7.6837 | 3 |
| s2 | USD | 578 | 0.1125 | 0.2455 | 2 |
| s3 | USD | 7716 | 0.0561 | 22.6885 | 4 |
| na | USD | 7849 | 0.0594 | 3.5997 | 3 |
| s0 | ALL | 5288 | 0.0649 | 20.7635 | 3 |
| s1 | ALL | 26208 | 0.0614 | 6.8831 | 4 |
| s2 | ALL | 578 | 0.1125 | -1.7214 | 2 |
| s3 | ALL | 13046 | 0.0627 | 22.7622 | 4 |
| na | ALL | 8368 | 0.0594 | 1.8910 | 4 |

## fold5 callout (5th contiguous equal-count block of pooled CALIB screened resolved bottoms; WI-027 fold5: 2020-01-29 -> 2022-04-29)
- 3-state fold5: 2020-01-29 -> 2022-04-29 | states: s0 (n=616), s1 (n=50) | fold-stable (pooled ALL n_folds_pos==5): none | fold5 in failing states: 666/666
- 4-state fold5: 2020-01-29 -> 2022-04-29 | states: s1 (n=492), s3 (n=174) | fold-stable (pooled ALL n_folds_pos==5): none | fold5 in failing states: 666/666

## Comparison vs WI-027 rule-based labels (research ladder stage 1b)
- WI-027 fold-stable rows (n_folds_pos==5): up_high/USD + chop_normal/ALL (rule-based VERDICT: PASS).
- GMM-3 fold-stable states: none
- GMM-4 fold-stable states: none
- Which labeling is better: the rule-based labels keep the edge on this run (no GMM state clears).
- Raw probability vectors feed downstream ML either way; state names are SUGGESTIONS ONLY.

VERDICT: FAIL
