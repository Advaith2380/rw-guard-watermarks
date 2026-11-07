# RW-Guard: Project Overview

## 1. Executive Summary

**RW-Guard** is a digital image forensics framework for the **passive, key-free, and database-free detection of sequential re-watermarking attacks** in digital imagery. 

While conventional image watermarking embeds machine-readable signals into carrier images to assert provenance, intellectual property, or regulatory compliance (e.g., California SB 942, EU AI Act Article 50), it is fundamentally vulnerable to **re-watermarking attacks**. In such attacks, an unauthorized adversary embeds a secondary watermark over an already watermarked image, attempting to overwrite the victim's provenance signal or create competing ownership claims.

RW-Guard introduces **ForensicNet**, a lightweight convolutional neural network (2.47M parameters) equipped with a non-trainable Spatial Rich Model (SRM) high-pass front-end and resolution-agnostic dual global pooling, capable of distinguishing singly-watermarked images from sequentially re-watermarked images directly from pixel evidence without access to watermarking keys, secret algorithms, or original reference images.

---

## 2. Research Problem & Research Gap

### 2.1 The Threat: Re-Watermarking Attacks
In a re-watermarking attack, an adversary takes a singly-watermarked carrier image $I_v = \text{Embed}(I, W_v, k_v, m_v)$ containing a victim's watermark and applies a secondary embedding operation:
$$I_{va} = \text{Embed}(I_v, W_a, k_a, m_a)$$
where $W_a$ may be identical to or different from the victim's scheme $W_v$.

Because watermark embedding and watermark removal are fundamentally aligned optimization objectives, applying a secondary watermark can suppress or corrupt the primary watermark while simultaneously installing an attacker-decodable signature. This attack:
1. Requires **zero access** to the victim's secret key or watermark encoder.
2. Operates at **low computational overhead**.
3. Results in **contested provenance**, creating legal and technical ambiguity regarding rightful authorship.

### 2.2 The Research Gap
Prior forensic literature has predominantly addressed:
- **Watermark Removal Detection (WRD):** Classifiers trained to identify artifacts left by image editing, inpainting, or generative regeneration.
- **Agnostic Watermark Presence Detection (AWPD):** Classifiers distinguishing clean images from singly-watermarked images.

Neither WRD nor AWPD addresses the operational reality of **re-watermarking**, where a secondary watermark is superimposed over an existing one. Detecting re-watermarking requires distinguishing **single embedding** (legitimate watermarking) from **sequential embedding** (adversarial collision), rather than merely flagging distortion or watermark presence.

---

## 3. Core Contributions

1. **Extensible Seven-Scheme Testbed:**
   A fully reproducible watermarking testbed spanning seven distinct embedding families:
   - `dct_qim`: Block Discrete Cosine Transform mid-frequency Quantization Index Modulation.
   - `dwt_qim`: Two-level Haar Discrete Wavelet Transform detail-subband QIM.
   - `ss_spatial`: Direct spatial spread-spectrum pseudorandom additive patterning.
   - `fft_ring`: Discrete Fourier Transform mid-frequency annular ring modulation.
   - `nmp_freq`: Non-Melting Points frequency-domain phase-invariant embedding.
   - `svd_qim`: Singular Value Decomposition singular-value quantization.
   - `dct_svd`: Hybrid DCT-SVD joint transform domain embedding.

2. **ForensicNet Architecture:**
   A lightweight, fully convolutional detector (2,466,099 parameters) featuring:
   - A frozen 9-channel SRM high-pass residual filter bank ($K_{hp}$) that strips semantic scene textures while isolating subtle watermark perturbation residuals.
   - A 4-stage residual backbone with full-resolution stem layers.
   - Resolution-agnostic dual global spatial pooling (concatenated average and max pooling).

3. **Multi-Resolution Invariance:**
   Demonstrated cross-resolution stability across five distinct spatial resolutions (128, 256, 384, 512, and 1024 px) without architectural alteration, input resizing, or interpolation artifacts.

4. **Rigorous Shortcut-Learning Controls:**
   Empirical invalidation of trivial shortcuts:
   - Evaluated against **distortion-matched single-watermark controls** (PSNR 38.5 dB) and **matched-noise controls** (PSNR 38.5 dB).
   - Linear (L2 Logistic Regression, AUC 0.5569) and shallow nonlinear (Random Forest, AUC 0.5500) baselines fail to detect sequential embedding, confirming that ForensicNet learns complex residual interactions rather than overall energy or distortion magnitude.

5. **Cross-Domain Generalization & Calibration (PACS):**
   Evaluated on the out-of-distribution PACS benchmark (Photo, Art, Cartoon, Sketch). ForensicNet maintains high ranking discrimination across domains (AUC 0.819–0.868) while identifying severe score deflation under domain shift, establishing the necessity of threshold recalibration.

6. **Generalization to Deep Neural Watermarkers:**
   - **StegaStamp:** Strong zero-shot generalization (ROC-AUC 0.9293, TPR@1% FPR 16.67%).
   - **TrustMark (ICCV 2025):** Zero-shot transfer achieves 0.6562 ROC-AUC on stratified controls; supervised domain adaptation with 15% exposure restores performance to 0.8505 ROC-AUC.

7. **Attack-Outcome Stratification:**
   Empirical categorization of 500 collision attacks into four mutually exclusive outcomes:
   - *Successful Overwrite* (13.4%): Attacker bit-accuracy $\ge 75\%$, victim $< 75\%$.
   - *Dual Survival* (85.0%): Both bit-accuracies $\ge 75\%$, creating competing ownership.
   - *Failed Attacker Embedding* (1.6%): Attacker fails to take hold.
   - *Mutual Destruction* (0.0%): Both signals corrupted.

8. **Transparent Reporting of Vulnerabilities:**
   Complete characterization of white-box adversarial fragility under PGD-10 (0% detection) and honest reporting of two failed adversarial training schedules, providing falsifiable diagnostic evidence.

---

## 4. Key Performance Reference

| Metric | Condition | Value | 95% Confidence Interval | Source Denominator |
|:---|:---|:---:|:---:|:---:|
| **In-Distribution ROC-AUC** | Held-Out Test (256px) | **0.8543** | [0.8410, 0.8672] | 1,500 sources (3,000 samples) |
| **TPR @ 1% FPR** | ROC-derived ($\tau = 1.6040$) | **7.87%** | [6.60%, 9.27%] | 1,500 sources (3,000 samples) |
| **Fixed-Threshold TPR** | Frozen $\tau = 1.3394016$ | **18.67%** | [16.73%, 20.67%] | 1,500 sources (3,000 samples) |
| **Fixed-Threshold FPR** | Frozen $\tau = 1.3394016$ | **3.33%** | [2.47%, 4.27%] | 1,500 sources (3,000 samples) |
| **Multi-Seed Stability** | Protocol A (500 sources) | **0.8528** | $s=0.0030, \sigma=0.0024$ | 3 seeds (500 sources) |
| **StegaStamp Transfer** | Zero-Shot ONNX | **0.9293** | [0.9024, 0.9543] | 150 sources (300 samples) |
| **TrustMark Transfer** | Zero-Shot Stratified | **0.6562** | [0.6150, 0.7010] | 200 sources (400 samples) |
| **TrustMark Adaptation** | 15% Mixed Exposure | **0.8505** | [0.8030, 0.8940] | 200 sources (400 samples) |

---

## 5. What RW-Guard Detects vs What It Does Not Establish

> [!IMPORTANT]
> **What RW-Guard Detects:**
> RW-Guard detects the **physical forensic traces of sequential watermark embedding** within a single digital image. It identifies the high-frequency residual interactions created when two watermark embedding operations are performed successively.

> [!CAUTION]
> **What RW-Guard Does NOT Establish:**
> 1. **Legal Rightful Ownership:** RW-Guard cannot determine which entity is the legitimate copyright holder or who embedded the first watermark.
> 2. **Watermark Extraction:** RW-Guard does not extract, decode, or recover the embedded bit payloads.
> 3. **Universal Neural Generalization:** While StegaStamp transfers strongly zero-shot (0.929 AUC), TrustMark shows significant domain shift (0.656 AUC), confirming that unseen neural watermarkers require fine-tuning exposure.
> 4. **Adversarial Security:** RW-Guard is susceptible to gradient-based adversarial evasion (PGD-10 achieves 100% evasion under $L_\infty$ perturbations of $\epsilon \ge 1/255$).
