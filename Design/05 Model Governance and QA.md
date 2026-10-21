# 05\_MODEL\_GOVERNANCE\_AND\_QA.md — Quantitative Validation & Model Audit Protocol

## 1\. Automated Anti-Leakage Test Suite (`tests/test_leakage.py`)

Before any model training in Sprint 4 is permitted, `opencode` must run and pass three deterministic unit tests:

1. **Future Perturbation Invariance Test:** Select 10 random tickers and a cutoff index \$t \= \-30\$. Compute feature matrix \$X^{(A)}\$. Overwrite raw OHLCV rows \$t+1 \\dots T\$ with extreme synthetic spikes (\$+500%\$ price jumps). Recompute feature matrix \$X^{(B)}\$. Assert `max(|X_A[:t] - X_B[:t]|) == 0.0`.  
2. **Purged Fold Boundary Test:** Verify that for every `(train_idx, val_idx)` pair emitted by `PurgedWalkForwardSplit`, \$\\max(\\text{date}\[train\_idx\]) \+ 20\\text{ trading days} \< \\min(\\text{date}\[val\_idx\])\$.  
3. **Cross-Sectional Grouping Isolation Test:** Verify that cross-sectional rank features at date \$t\$ depend solely on tickers present at date \$t\$ and are invariant to removing dates \$\> t\$.

---

## 2\. Out-of-Sample Evaluation Metrics (`src/model_qa.py`)

Standard accuracy is misleading due to class imbalance. Models are graded across the 5 purged walk-forward folds using four institutional metrics:

| Metric | Target Threshold (MVP Gate) | Analytical Purpose |
| :---- | :---- | :---- |
| **Precision@30 (Lift over Base Rate)** | \$\\ge 1.5\\times\$ unconditional base rate | Measures actual hit rate within the exact 30-stock bucket rendered in the PDF report. |
| **Brier Skill Score (BSS)** | \$\> 0.05\$ vs. climatology | Confirms isotonic probability calibration is accurate for ranking `holdings.csv` exit urgency. |
| **PR-AUC (Precision-Recall AUC)** | \$\> 1.35\\times\$ positive class prior | Evaluates minority-class discrimination across all threshold cutoffs. |
| **Deflated Information Coefficient (IC)** | Spearman \$\\rho \> 0.04\$ (\$t\$-stat \$\> 2.5\$) | Measures rank-order correlation between predicted probability and realized forward ATR-adjusted return. |

---

## 3\. Overfitting & Sanity Diagnostics ("Check the Models" Extra Module)

`src/model_qa.py` automatically generates `reports/sprint4_model_qa.md` containing four diagnostic checks for human review at **Gate 4**:

1. **Placebo Target Permutation Test:** Re-trains `XGBClassifier` on randomly shuffled target labels \$Y\_{\\text{shuffled}}\$. If out-of-sample ROC-AUC exceeds `0.52`, the pipeline automatically flags a hidden data leak and halts execution.  
2. **Train vs. Validation Generalization Gap:** Logs `(PR-AUC_train - PR-AUC_val)`. If the gap exceeds `0.15`, the agent recommends tightening regularization (`max_depth: 4 -> 3`, `min_child_weight: 20 -> 40`, `colsample_bytree: 0.7 -> 0.5`).  
3. **Regime Stability Breakdown:** Slices out-of-fold validation precision across Bull, Bear, and Sideways market regimes (defined by SPY / XIU.TO trailing 50-day SMA slope and realized volatility) so you can see whether the `15d_Low` or `20d_Up` models degrade in high-volatility drawdowns.  
4. **SHAP Feature Dominance Audit:** Flags if any single feature accounts for \$\> 35%\$ of total model gain (indicating brittle reliance on a single indicator rather than multi-timeframe confluence).