# Baseline Performance Audit: RW-Guard

## 1. Executive Summary & Provenance
- **Model Checkpoint:** `D:/projects/rewm-guard/runs/baseline_e9/best.pt` (Epoch 9, validation AUC 0.8602, trained on 4 classical schemes: `['dct_qim', 'dwt_qim', 'ss_spatial', 'fft_ring']`).
- **Primary Results Artifact:** `D:/projects/rewm-guard/results/baseline_e9_final/results.json` & `results.md`.
- **Dataset:** MS-COCO val2017 (5,000 images, source-image split: 60% train, 10% val, 30% test).
- **Operating Threshold:** `1.1413` (selected on 300 validation negatives targeting 1% nominal FPR).
- **Observed Test FPR at Threshold:** `3.53%` (demonstrating threshold calibration shift between validation and test sets).

---

## 2. In-Distribution Performance (COCO 256px, Seen Schemes)
- **Sample Count:** $N = 3,000$ test evaluations (1,500 positive, 1,500 negative).
- **ROC-AUC:** `0.8586`
- **TPR @ 1% FPR:** `16.47%` (0.1647)
- **TPR @ 0.1% FPR:** `4.53%` (0.0453)
- **TPR @ Fixed Threshold (1.141):** `29.47%`
- **FPR @ Fixed Threshold (1.141):** `3.53%`

---

## 3. Generalization to Unseen Watermark Schemes
- **Unseen Attacker Scheme** (`nmp_freq`, `svd_qim`, `dct_svd`):
  - ROC-AUC: `0.817`
  - TPR @ 1% FPR: `3.10%`
  - TPR @ Fixed Threshold: `7.70%`
  - FPR @ Fixed Threshold: `2.40%`
- **Unseen Victim and Attacker Scheme** (Both unseen):
  - ROC-AUC: `0.580` (collapses near chance)
  - TPR @ 1% FPR: `0.10%`
  - TPR @ Fixed Threshold: `0.30%`

---

## 4. Robustness to Benign Post-Processing
Evaluated across 8 benign transformations at 256px:

| Transformation | AUC | TPR @ 1% FPR | TPR @ Fixed Thr | FPR @ Fixed Thr |
|---|---|---|---|---|
| None (clean) | 0.877 | 0.194 | 0.350 | 0.041 |
| JPEG Quality 95 | 0.863 | 0.120 | 0.317 | 0.033 |
| JPEG Quality 85 | 0.853 | 0.171 | 0.199 | 0.015 |
| JPEG Quality 75 | 0.846 | 0.141 | 0.155 | 0.013 |
| Gaussian Noise ($\sigma=1.0$) | 0.871 | 0.206 | 0.342 | 0.039 |
| Gaussian Noise ($\sigma=2.0$) | 0.862 | 0.194 | 0.353 | 0.045 |
| Gaussian Blur ($\sigma=0.5$) | 0.868 | 0.151 | 0.177 | 0.015 |
| Brightness ($\pm 10\%$) | 0.830 | 0.164 | 0.249 | 0.027 |

---

## 5. Resolution Invariance
Evaluated on variable input resolutions without retraining (enabled by Global Average + Max Pooling):

| Resolution | AUC | TPR @ 1% FPR | TPR @ Fixed Thr | FPR @ Fixed Thr |
|---|---|---|---|---|
| 128px | 0.860 | 0.109 | 0.373 | 0.050 |
| 256px | 0.859 | 0.165 | 0.295 | 0.035 |
| 384px | 0.859 | 0.191 | 0.229 | 0.015 |

---

## 6. Cross-Domain Generalization (PACS Dataset)
Evaluated on 4 domains (800 samples each) without retraining:

| Domain | AUC | TPR @ 1% FPR | TPR @ Fixed Thr | FPR @ Fixed Thr |
|---|---|---|---|---|
| Art Painting | 0.842 | 0.147 | 0.350 | 0.052 |
| Cartoon | 0.891 | 0.297 | 0.028 | 0.003 |
| Photo | 0.819 | 0.105 | 0.360 | 0.058 |
| Sketch | 0.897 | 0.345 | 0.003 | 0.000 |

---

## 7. White-Box Adversarial Robustness (PGD-10)
- Clean Positives Detected Rate: `40.0%`
- PGD-10 ($\epsilon = 0.5 / 255$): `0.0%`
- PGD-10 ($\epsilon = 1.0 / 255$): `0.0%`
- PGD-10 ($\epsilon = 2.0 / 255$): `0.0%`
*(Demonstrates extreme vulnerability to gradient-based high-frequency perturbations).*

---

## 8. Architectural Ablations
From existing checkpoints in `D:/projects/rewm-guard/runs/`:

| Architecture | Validation AUC | Training Loss (Epoch 9/10) | Notes |
|---|---|---|---|
| **ForensicNet (with HP front-end)** | **0.8602** | 0.5124 | Headline model (`baseline_e9`) |
| **ForensicNet (without HP front-end)** | 0.5150 | 0.5109 | Near chance without high-pass filter |
| **ResNet-18 (without HP front-end)** | 0.5034 | 0.4980 | Complete collapse near chance |
| **SimpleClassifier (without HP front-end)** | 0.5019 | 0.4995 | Complete collapse near chance |

---

## 9. Training Seed Variability
Across three independent runs on COCO:
- Seed 0: Validation AUC = `0.8483`
- Seed 1: Validation AUC = `0.8473`
- Seed 2: Validation AUC = `0.8453`
*(Range $\Delta = 0.0030$, standard deviation $\approx 0.0015$).*

---

## 10. Real Pretrained Neural Watermarker (TrustMark)
- Zero-Shot Evaluation AUC: `0.696`
- Mixed Training ($p=0.15$): AUC `0.925` (without degrading classical watermark detection)
