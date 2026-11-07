# Statistical Methodology and Uncertainty Quantification

## 1. Source-Grouped Bootstrap Analysis

To adhere to the rigorous statistical reporting standards of *Scientific Reports* and prevent artificial variance deflation caused by intra-image correlations, all empirical confidence intervals are estimated via **source-image-level grouped bootstrapping**:

1. Let $\mathcal{S}_{\text{test}} = \{s_1, s_2, \dots, s_N\}$ denote the set of $N$ unique source images in the evaluation partition (e.g., $N=1,500$ for held-out MS-COCO test).
2. For each bootstrap iteration $b \in \{1, 2, \dots, B\}$ with $B = 2,000$:
   a. Sample $N$ source image identifiers uniformly at random **with replacement**: $\mathcal{S}^{(b)} \sim \text{Multinomial}(\mathcal{S}_{\text{test}}, N)$.
   b. Retrieve all derived test samples (both negative controls and positive attacks) associated with the sampled source IDs to form bootstrap sample $\mathcal{D}^{(b)}$.
   c. Compute evaluation metrics (ROC-AUC, TPR@1%FPR, fixed TPR, fixed FPR) on $\mathcal{D}^{(b)}$.
3. Construct two-sided **95% Percentile Confidence Intervals** from the empirical distribution of bootstrap estimates:
   $$\text{CI}_{95\%} = \left[ \hat{\theta}^*_{(0.025 \cdot B)}, \; \hat{\theta}^*_{(0.975 \cdot B)} \right]$$

---

## 2. Evaluation Metrics and Operational Definitions

### 2.1 Receiver Operating Characteristic (ROC-AUC)
The Area Under the Receiver Operating Characteristic Curve (ROC-AUC) measures the ranking capability of scalar detector logits $z \in \mathbb{R}$ across all potential decision thresholds:
$$\text{AUC} = \int_0^1 \text{TPR}(\text{FPR}^{-1}(u)) \, du$$
computed via trapezoidal integration over non-redundant decision thresholds.

### 2.2 ROC-Derived TPR @ 1.00% FPR
The True Positive Rate evaluated at the empirical decision cutoff $\tau_{\text{test}}$ where the test False Positive Rate is exactly $1.00\%$:
$$\tau_{\text{test}} = \inf \{ t \in \mathbb{R} : \text{FPR}(t) \le 0.0100 \}$$
$$\text{TPR}_{@1\%\text{FPR}} = \text{TPR}(\tau_{\text{test}})$$
For the primary 1,500-source held-out test split, $\tau_{\text{test}} = 1.6040$, yielding $\text{TPR}_{@1\%\text{FPR}} = 7.87\%$ (118 / 1,500 positive attacks).

### 2.3 Fixed-Threshold Metrics ($\tau = 1.3394016$)
Evaluated at the frozen operating point $\tau = 1.3394016$ calibrated on the validation split:
$$\text{TPR}_{\text{fixed}} = \frac{\sum_{i: y_i=1} \mathbb{I}(z_i \ge \tau)}{\sum_{i: y_i=1} 1} = \frac{280}{1,500} = 18.67\%$$
$$\text{FPR}_{\text{fixed}} = \frac{\sum_{i: y_i=0} \mathbb{I}(z_i \ge \tau)}{\sum_{i: y_i=0} 1} = \frac{50}{1,500} = 3.33\%$$

---

## 3. Binomial Proportions & Wilson Score Intervals

For attack-outcome stratification categories (sample sizes $n \le 500$), ordinary normal approximations fail near boundary probabilities ($p \approx 0$ or $p \approx 1$). We report **Wilson Score Intervals with continuity correction**:
$$\text{CI}_{\text{Wilson}} = \frac{\hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$
where $z = 1.96$ for 95% coverage.

---

## 4. Calibration Metrics

To quantify probability distortion under domain shifts (PACS benchmark), we compute:
1. **Expected Calibration Error (ECE):**
   Group predicted posterior probabilities $p_i = \sigma(z_i)$ into $M=10$ equally-spaced bins $B_m \subset (0, 1]$:
   $$\text{ECE} = \sum_{m=1}^M \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$
2. **Brier Score:**
   The mean squared error of predicted posterior probabilities against true binary labels:
   $$\text{BS} = \frac{1}{N} \sum_{i=1}^N (p_i - y_i)^2$$

### Observed Calibration across PACS Domains
| Domain | ROC-AUC | Fixed TPR ($\tau$) | Fixed FPR ($\tau$) | ECE ($M=10$) | Brier Score |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Photo** | 0.8192 [0.774, 0.864] | 15.00% | 2.50% | 0.085 | 0.179 |
| **Art Painting** | 0.8616 [0.822, 0.901] | 18.00% | 3.50% | 0.092 | 0.161 |
| **Cartoon** | 0.8677 [0.830, 0.905] | 22.50% | 2.50% | 0.094 | 0.157 |
| **Sketch** | 0.8247 [0.781, 0.868] | 13.50% | 1.50% | 0.111 | 0.180 |

---

## 5. Hypothesis Testing & Baseline Comparisons

Paired difference tests ($\Delta \text{AUC} = \text{AUC}_{\text{RW-Guard}} - \text{AUC}_{\text{Baseline}}$) are computed over identical bootstrap resamples to establish whether performance improvements are statistically significant:

| Comparison Model | Model ROC-AUC | $\Delta \text{AUC}$ vs RW-Guard | 95% Bootstrap CI | $p$-value |
|:---|:---:|:---:|:---:|:---:|
| **L2 Logistic Regression (Linear)** | 0.5569 | **+0.2908** | [+0.267, +0.314] | $p < 0.001$ |
| **Random Forest (Nonlinear)** | 0.5500 | **+0.2982** | [+0.265, +0.331] | $p < 0.001$ |
| **Matched-Noise Control** | 0.7296 | **+0.1181** | [+0.089, +0.147] | $p < 0.001$ |
| **Distortion-Matched Single** | 0.5747 | **+0.2730** | [+0.246, +0.300] | $p < 0.001$ |

All baseline comparisons confirm that ForensicNet's detection cannot be replicated by linear/nonlinear combinations of elementary residual energy features.
