# Experimental Protocols and Benchmarking Standards

## 1. Overview of Experimental Axes

RW-Guard evaluates the frozen primary seven-scheme model across eight comprehensive experimental protocols:

```
[Primary 7-Scheme Checkpoint]
    |---> Axis 1: In-Distribution Performance (MS-COCO, 256px)
    |---> Axis 2: Benign Post-Processing Robustness (JPEG, Noise, Blur, Photometric)
    |---> Axis 3: Multi-Resolution Invariance (128, 256, 384, 512, 1024 px)
    |---> Axis 4: Cross-Domain Style Shift (PACS: Photo, Art, Cartoon, Sketch)
    |---> Axis 5: Shortcut-Learning Controls & Baselines (Distortion-matched, RF, LR)
    |---> Axis 6: Deep Neural Watermarker Generalization (TrustMark ICCV 2025, StegaStamp)
    |---> Axis 7: Ownership Collision Stratification (Overwrite, Dual survival, Failed)
    |---> Axis 8: Adversarial Robustness & Evasion (PGD-10 white-box attack)
```

---

## 2. Protocol Details

### 2.1 Axis 1: In-Distribution Test Evaluation
- **Dataset:** MS-COCO val2017 held-out test split (1,500 source images, 3,000 derived samples).
- **Class Balance:** 1,500 singly-watermarked negative controls ($y=0$), 1,500 sequentially re-watermarked attacks ($y=1$).
- **Image Resolution:** $256 \times 256$ pixels.
- **Watermarking Schemes:** Randomly sampled from the 7 primary schemes (`dct_qim`, `dwt_qim`, `ss_spatial`, `fft_ring`, `nmp_freq`, `svd_qim`, `dct_svd`).
- **Primary Metrics:** ROC-AUC, ROC-derived TPR @ 1.00% FPR, Fixed-threshold TPR ($\tau = 1.3394016$), Fixed-threshold FPR.
- **Statistical Uncertainty:** 2,000 source-image grouped bootstrap replicates (95% percentile CI).

### 2.2 Axis 2: Benign Post-Processing Robustness
Images from the held-out test set are subjected to common non-adversarial digital edits prior to detection:
1. **JPEG Compression:** Quality factors $Q \in \{75, 85, 95\}$.
2. **Additive Gaussian Noise:** Standard deviations $\sigma \in \{1.0, 2.0\}$ gray-scale levels.
3. **Gaussian Blurring:** Kernel radius with filter $\sigma = 0.5$.
4. **Photometric Adjustments:** Simultaneous brightness and contrast variation ($\pm 10\%$).

### 2.3 Axis 3: Multi-Resolution Invariance
- **Tested Resolutions:** $128 \times 128$, $256 \times 256$, $384 \times 384$, $512 \times 512$, and $1024 \times 1024$ pixels.
- **Mechanism:** The model operates directly on full input tensors via dual global spatial average/max pooling; no input resizing, interpolation, or sliding-window tiling is employed.
- **Sample Accounting:** 1,500 sources $\times$ 2 samples = 3,000 samples per resolution (15,000 evaluations total).

### 2.4 Axis 4: Cross-Domain Generalization (PACS)
- **Dataset:** PACS benchmark (Photo, Art Painting, Cartoon, Sketch).
- **Primary Benchmark:** 200 source images per domain (400 derived samples per domain; 800 sources / 1,600 samples overall).
- **Extended Protocol:** 400 source images per domain (800 derived samples per domain; 1,600 sources / 3,200 samples overall).
- **Calibration Analysis:** Evaluation of domain score shift, Expected Calibration Error (ECE), Brier score, and domain-specific recalibration.

### 2.5 Axis 5: Shortcut-Learning Controls & Baselines
To eliminate the hypothesis that ForensicNet simply measures total distortion or high-frequency energy:
1. **Distortion-Matched Single Control:** Single watermarks embedded at double strength ($\Delta_{\text{matched}} = \sqrt{2}\Delta$, PSNR 38.5 dB) to match the total perturbation energy of sequential embedding.
2. **Matched-Noise Single Control:** Singly-watermarked images with additive Gaussian noise matched in MSE to the second watermark (PSNR 38.5 dB).
3. **Linear Baseline (L2 Logistic Regression):** Evaluated on 10 handcrafted residual and spectral features (mean residual energy, variance, kurtosis, high-frequency DCT energy, FFT ring energy).
4. **Nonlinear Baseline (Random Forest):** 100 trees, maximum depth 8, trained on the same 10 handcrafted residual features.

### 2.6 Axis 6: Deep Neural Watermarkers
1. **StegaStamp (CVPR 2020):** Evaluated using the official pretrained ONNX encoder/decoder on 150 held-out sources (300 derived samples).
2. **TrustMark (ICCV 2025):** Evaluated across 200 sources (400 samples) under two configurations:
   - *Zero-Shot Transfer:* Frozen primary 7-scheme model evaluated against stratified controls (50% clean, 50% single TrustMark).
   - *Supervised Domain Transfer:* Fine-tuning with 15% TrustMark exposure (20 epochs).
3. **Historical 4-Scheme Comparison:** Comparison against prior 4-scheme baseline model to verify architectural progression.

### 2.7 Axis 7: Ownership Collision Stratification
500 re-watermarking attacks are classified into four mutually exclusive operational categories based on watermark bit-recovery (threshold: $\ge 75\%$ bit-accuracy):
1. **Successful Overwrite:** Attacker $\ge 75\%$, Victim $< 75\%$.
2. **Dual Survival:** Both Attacker $\ge 75\%$ and Victim $\ge 75\%$.
3. **Failed Attacker Embedding:** Attacker $< 75\%$.
4. **Mutual Destruction:** Both Attacker $< 75\%$ and Victim $< 75\%$.

Each category is evaluated for fixed-threshold TPR ($\tau = 1.3394016$), ROC-AUC against singly-watermarked controls, and 95% Wilson score confidence intervals.

### 2.8 Axis 8: Adversarial Robustness
- **Attack Algorithm:** Projected Gradient Descent (PGD-10) with random start.
- **Perturbation Budgets:** $L_\infty$ ball with $\epsilon \in \{1/255, 2/255, 4/255\}$, step size $\alpha = \epsilon / 4$.
- **Evaluated Models:**
  - Undefended primary 7-scheme model.
  - Defended adversarially-trained checkpoint (`runs/adv_eps1/best.pt`, $\epsilon=1/255$).
