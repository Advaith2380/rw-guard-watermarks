# STATISTICAL METHODOLOGY & CONFIDENCE INTERVAL REPORT
**Document Version:** 1.0 (Faculty Review Implementation Master Standard)  
**Verification Engine:** Antigravity Forensic ML Audit Toolchain  
**Target Significance Level:** 95% ($1 - \alpha = 0.95$)  
**Bootstrap Replicates:** $B = 2,000$ paired source-level resamples  

---
## 1. Grouped Bootstrap Resampling at Independent Source-Image Level
A critical vulnerability in naive forensic ML evaluation is treating individual image crops or samples as independent and identically distributed (i.i.d.). In digital watermarking benchmarks:
- Each source image generates paired derivatives (e.g., negative single-watermarked vs. positive re-watermarked).
- Naive sample-level bootstrapping samples negatives and positives independently, breaking the underlying paired covariance structure and artificially narrowing standard error estimates.
- **RW-Guard Protocol:** Resampling is performed strictly by drawing source image IDs with replacement: $\mathcal{S}^* \sim \text{Uniform}(\mathcal{S}, |\mathcal{S}|)$. All positive and negative samples derived from selected source image $s_i$ are included collectively in the bootstrap replicate.

## 2. Paired Model Comparison Formulation
To evaluate whether RW-Guard outperforms handcrafted residual/spectral baselines without confounding variance from image difficulty:
$$\Delta \text{AUC}_b = \text{AUC}_{\text{RW-Guard}}(\mathcal{S}^*_b) - \text{AUC}_{\text{Baseline}}(\mathcal{S}^*_b)$$
For $b = 1, \dots, 2000$. The 95% bootstrap confidence interval is computed via empirical percentiles:
$$\text{CI}_{95}(\Delta \text{AUC}) = \left[ \hat{q}_{0.025}(\Delta \text{AUC}_b), \; \hat{q}_{0.975}(\Delta \text{AUC}_b) \right]$$
If $\hat{q}_{0.025} > 0$, baseline inferiority is proven at $p < 0.05$ (two-tailed equivalent). Both Logistic Regression and Random Forest comparisons strictly exclude zero by over 0.26 AUC.

## 3. Disentanglement of Operating Points and Error Rates
Forensic detection systems operate in high-precision regimes. This audit establishes clear separation between two reported concepts:
1. **Test ROC Operating Point (TPR@1%FPR):** Derived by sliding the threshold across test scores to the exact empirical 99th percentile of test negative scores. For the primary model on 1,500 test sources: $\text{TPR}@1\%\text{FPR} = 0.0787$ [95% CI: $0.0500, 0.1060$].
2. **Calibration-Frozen Operating Point (tau = 1.3394016):** Calibrated on the 300 validation negative sources ($3/300 = 1.00\%$ FPR). Evaluated on 1,500 held-out test negatives, this fixed threshold yields $\text{TPR} = 0.1867$ [95% CI: $0.1680, 0.2067$] and $\text{FPR} = 0.0333$ [95% CI: $0.0247, 0.0433$].

## 4. Analytic Formulations for Secondary Conditions
For secondary conditions where per-sample raw scores were summarized in the final benchmark, confidence intervals are established using proven forensic statistical formulations:
- **Hanley-McNeil Formulation for ROC-AUC:** Computes standard error incorporating the correlation of positive and negative pairs sharing the test set background.
- **Wilson Score Interval for Binomial Rates:** Used for fixed-threshold TPR and FPR proportions to maintain accurate coverage near boundary distributions ($p < 0.05$).

## 5. Summary Matrix
All 26 distinct experimental conditions are systematically audited in `consolidated_statistical_results.csv` and serialized in `confidence_intervals.json`.
