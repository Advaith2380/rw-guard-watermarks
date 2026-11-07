# Authoritative Results Reference & Evidence Mapping

This document provides the definitive mapping between every empirical result reported in the revised scientific manuscript (`manuscript/corrected_final_manuscript.docx` / `.pdf`) and its corresponding raw prediction file, JSON record, or CSV audit trail.

---

## 1. Primary Checkpoint & Core Model Configuration

| Item | Authoritative Value / Path | Verification Method / Evidence |
|:---|:---|:---|
| **Primary Model Checkpoint** | `checkpoints/final/rwguard_final_7scheme.pt` | File size: 9,890,147 bytes; Checksum verification |
| **Primary Checkpoint SHA-256** | `37680cdd2d4e5100cbb8aa1642e78b9bb3df373e79efd9f8512f89e15d0c0573` | Bit-identical across repository and submission archive |
| **Model Architecture** | ForensicNet (2,466,099 parameters) | `configs/final_model_config.json` |
| **Watermark Schemes** | 7 schemes (`dct_qim`, `dwt_qim`, `ss_spatial`, `fft_ring`, `nmp_freq`, `svd_qim`, `dct_svd`) | Model state dict & training manifest |
| **Frozen Validation Threshold** | $\tau = 1.3394016$ | Calibrated at 1.00% validation FPR on 500 sources |
| **Defended Checkpoint (PGD)** | `runs/adv_eps1/best.pt` | SHA-256: `27954fd43360830d76fa107036567e9486844fa85d6a058c84d438b2e6caefed` |

---

## 2. Manuscript Table to Evidence File Mapping

### Table 8: Robustness and Resolution Evaluation
- **Authoritative CSV:** `results/final_primary/FINAL_RESOLUTION_METRICS_VERIFIED.csv`
- **Raw Predictions:** `results/final_primary/resolution_predictions.npz`
- **Authoritative JSON:** `audit/final_consolidated_results.json`

| Resolution | ROC-AUC [95% CI] | ROC-derived TPR @ 1% FPR | Fixed TPR ($\tau$) | Fixed FPR ($\tau$) | Status |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **128 px** | 0.8463 [0.832, 0.860] | **6.93%** (0.069) | 32.60% (0.326) | 6.67% (0.067) | Verified Bit-Identical |
| **256 px** | 0.8543 [0.841, 0.867] | **7.87%** (0.079) | 18.67% (0.187) | 3.33% (0.033) | Verified Bit-Identical |
| **384 px** | 0.8579 [0.844, 0.871] | **8.33%** (0.083) | 8.87% (0.089) | 1.13% (0.011) | Verified Bit-Identical |
| **512 px** | 0.8501 [0.836, 0.864] | **9.27%** (0.093) | 9.47% (0.095) | 1.13% (0.011) | Verified Bit-Identical |
| **1024 px** | 0.7998 [0.784, 0.815] | **16.50%** (0.165) | 18.50% (0.185) | 1.50% (0.015) | Verified Bit-Identical |

### Table 10: PACS Cross-Domain Style Shift
- **Authoritative JSON:** `audit/pacs_calibration_results.json`
- **Authoritative CSV:** `results/final_primary/pacs_metrics.csv`
- **Domain Accounting:** 200 source images per domain (400 derived samples per domain; 800 sources / 1,600 samples overall).

| Domain | ROC-AUC [95% CI] | TPR @ 1% FPR | Fixed TPR ($\tau=1.3394$) | Fixed FPR ($\tau=1.3394$) | ECE | Brier Score |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Photo** | 0.8192 [0.774, 0.864] | 9.00% | 15.00% (30/200) | 2.50% (5/200) | 0.085 | 0.179 |
| **Art Painting** | 0.8616 [0.822, 0.901] | 6.00% | 18.00% (36/200) | 3.50% (7/200) | 0.092 | 0.161 |
| **Cartoon** | 0.8677 [0.830, 0.905] | 13.00% | 22.50% (45/200) | 2.50% (5/200) | 0.094 | 0.157 |
| **Sketch** | 0.8247 [0.781, 0.868] | 13.00% | 13.50% (27/200) | 1.50% (3/200) | 0.111 | 0.180 |

### Table 12: Multi-Seed Reproducibility
- **Authoritative JSON:** `results/statistics/seed_statistics.json`
- **Prediction Files:** `audit/seed_evaluation_results.json`
- **Protocol A (500 Sources / 1,000 Samples):**
  - Seed 0: Test AUC 0.8556 [0.831, 0.878] | Fixed TPR 19.4% | FPR 3.4%
  - Seed 1: Test AUC 0.8531 [0.829, 0.876] | Fixed TPR 16.4% | FPR 1.8%
  - Seed 2: Test AUC 0.8497 [0.826, 0.872] | Fixed TPR 18.8% | FPR 3.0%
  - **Mean AUC:** **0.8528**
  - **Sample SD ($s$, ddof=1):** **0.002955** ($\approx 0.0030$)
  - **Population SD ($\sigma$, ddof=0):** **0.002413** ($\approx 0.0024$)
- **Protocol B (1,500 Sources / 3,000 Samples):**
  - Primary Frozen Test: Mean AUC **0.8530**, Sample SD **0.0024** ($s=0.002350$).

### Table 14: Deep Neural Watermarkers (TrustMark & StegaStamp)
- **Authoritative JSON:** `audit/trustmark_evaluation_results.json`, `audit/stegastamp_evaluation_results.json`
- **TrustMark Zero-Shot (Stratified Controls, 7 Schemes):** ROC-AUC **0.6562** [0.615, 0.701], TPR@1% 3.00%, Fixed TPR 0.00%, FPR 1.00%.
- **TrustMark Historical 4-Scheme Baseline:** ROC-AUC **0.5344** [0.502, 0.569].
- **TrustMark Supervised Adaptation (15% exposure, 20 epochs):** ROC-AUC **0.8505** [0.803, 0.894], TPR@1% 22.00%, Fixed TPR 18.00%, FPR 0.00%.
- **StegaStamp Zero-Shot (Pretrained ONNX, 150 sources):** ROC-AUC **0.9293** [0.902, 0.954], TPR@1% 16.67%, Fixed TPR 5.33%, FPR 0.67%.

### Table 16: Attack-Outcome Stratified Evaluation
- **Authoritative JSON:** `audit/outcome_stratification_results.json`
- **Total Attacks Evaluated:** 500 collisions across 7 schemes.

| Category | Count | % Attacks [95% Wilson CI] | Fixed TPR ($\tau$) [95% CI] | Mean Score | AUC vs Single Control |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Successful Overwrite** | 67 | 13.4% [10.66%, 16.69%] | 11.9% [0.045, 0.194] | 0.378 | 0.639 |
| **Dual Survival** | 425 | 85.0% [81.60%, 87.86%] | 20.7% [0.167, 0.247] | 0.742 | 0.736 |
| **Failed Attacker** | 8 | 1.6% [0.81%, 3.12%] | 12.5% [0.000, 0.375] | 0.859 | 0.785 |
| **Mutual Destruction** | 0 | 0.0% [0.00%, 0.74%] | — | — | — |
| **Total Population** | **500** | **100.0%** | — | — | — |

### Table 17: Shortcut-Learning Controls & Baselines
- **Authoritative JSON:** `audit/shortcut_baseline_results.json`, `audit/matched_controls_results.json`
- **Authoritative CSV:** `results/shortcut_controls/baseline_comparison.csv`

| Model / Control Condition | Architecture / Method | Perturbation Budget | ROC-AUC [95% CI] | $\Delta \text{AUC}$ vs RW-Guard |
|:---|:---|:---:|:---:|:---:|
| **RW-Guard Frozen Primary** | ForensicNet (2.47M params) | 9.12 MSE (38.53 dB) | **0.8477** [0.824, 0.870] | [Reference Baseline] |
| **L2 Logistic Regression** | 10 Residual & FFT Feats | N/A (Linear) | **0.5569** [0.543, 0.572] | **-0.2908** [-0.314, -0.267] |
| **Random Forest (100 trees)** | Max Depth 8, 10 Feats | N/A (Nonlinear) | **0.5500** [0.525, 0.575] | **-0.2982** [-0.331, -0.265] |
| **Strength-Matched Single** | ForensicNet (Matched Single) | 9.14 MSE (38.52 dB) | **0.5747** [0.554, 0.596] | **-0.2730** [-0.300, -0.246] |
| **Matched-Noise Control** | ForensicNet (Single + Noise) | 9.13 MSE (38.52 dB) | **0.7296** [0.703, 0.757] | **-0.1181** [-0.147, -0.089] |
| **Standard Single Control** | ForensicNet (Single Normal) | 4.62 MSE (41.49 dB) | **0.7276** [0.704, 0.751] | Standard Negative Control |
