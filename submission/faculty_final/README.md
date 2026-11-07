# RW-Guard: Key-Free Forensic Detection of Sequential Re-Watermarking in Digital Images

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-ee4c2c.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Verification Status](https://img.shields.io/badge/Faculty%20Audit-53%2F53%20PASS-brightgreen.svg)](docs/FACULTY_REQUIREMENT_TRACEABILITY.md)

---

## 1. Project Title
**RW-Guard: Forensic Detection of Re-Watermarking Attacks: A Deep Learning Approach to Identifying Ownership Forgery in Digital Images**  
*Scientific Reports (Nature Publishing Group) Revision & Submission Repository*

---

## 2. Research Problem
Digital image watermarking provides machine-readable provenance and copyright signaling. However, watermarking systems are vulnerable to **re-watermarking attacks**, where an unauthorized party applies a secondary watermark over an existing one. Because watermark embedding and removal are closely aligned optimization objectives, applying a secondary watermark can suppress or corrupt the original provenance signal while installing an attacker-decodable signature. This creates **contested provenance**, leaving the carrier image with competing, verifiable ownership claims without requiring access to the victim's secret keys.

---

## 3. Research Contribution
1. **Extensible Seven-Scheme Testbed:** A unified framework implementing classical, transform-domain, and frequency-domain watermarking schemes (`dct_qim`, `dwt_qim`, `ss_spatial`, `fft_ring`, `nmp_freq`, `svd_qim`, `dct_svd`).
2. **ForensicNet Detector:** A lightweight fully convolutional neural network (2.47M parameters) with a non-trainable Spatial Rich Model (SRM) high-pass front-end and dual global spatial pooling.
3. **Resolution-Agnostic Operation:** Seamless evaluation across five distinct resolutions (128, 256, 384, 512, and 1024 px) without architectural alteration or interpolation artifacts.
4. **Shortcut-Learning Verification:** Invalidation of distortion-energy heuristics via matched-distortion single-watermark controls (PSNR 38.5 dB), matched-noise controls, and linear/nonlinear baselines.
5. **Cross-Domain Generalization & Calibration:** Robust evaluation on the out-of-distribution PACS benchmark (Photo, Art, Cartoon, Sketch) with score-calibration characterization.
6. **Neural Watermarker Transfer:** Zero-shot evaluation and supervised domain adaptation on deep neural watermarkers: StegaStamp (0.9293 zero-shot AUC) and TrustMark (ICCV 2025; 0.6562 zero-shot, 0.8505 adapted).
7. **Collision Outcome Stratification:** Categorization of 500 attack collisions into four mutually exclusive operational categories (Overwrite, Dual survival, Failed attacker, Mutual destruction).
8. **Transparent Vulnerability Reporting:** Complete characterization of white-box adversarial fragility under PGD-10 (0% detection) and diagnostic analysis of failed adversarial training schedules.

---

## 4. What RW-Guard Detects and Does Not Establish
> [!IMPORTANT]
> **What RW-Guard Detects:**
> The physical, high-frequency spatial residual interactions produced when two watermark embedding operations are performed sequentially on a single digital carrier.

> [!CAUTION]
> **What RW-Guard Does NOT Establish:**
> - **Legal Ownership:** RW-Guard cannot determine which party is the rightful copyright owner or who embedded first.
> - **Payload Decoding:** RW-Guard is a passive binary detector; it does not decode or recover embedded message bits.
> - **Universal Neural Invariance:** Unseen deep latent diffusion watermarkers require representation adaptation.
> - **Adversarial Security:** The model is susceptible to white-box gradient-based evasion (PGD).

---

## 5. Model Architecture Overview
ForensicNet incorporates:
- **Fixed High-Pass Filter Bank ($K_{hp}$):** A non-trainable 9-channel SRM filter bank ($5 \times 5$ Laplacian, horizontal, and diagonal difference filters) suppressing semantic scene content.
- **Full-Resolution Stem:** Two non-strided convolutional layers operating at full resolution to preserve delicate residual interactions.
- **4-Stage Residual Backbone:** Successive residual downsampling stages (widths: 32 $\to$ 64 $\to$ 128 $\to$ 256).
- **Dual Global Spatial Pooling:** Concatenated Global Average Pooling and Global Max Pooling ($256 + 256 = 512$ dims), enabling arbitrary input dimensions.
- **Parameters:** Exactly **2,466,099 weights** (lightweight for consumer GPU/CPU deployment).

---

## 6. Seven Watermark Schemes
| Scheme | Domain | Description | Bit Accuracy | Baseline PSNR |
|:---|:---|:---|:---:|:---:|
| `dct_qim` | Block DCT | 8x8 block DCT; mid-frequency AC QIM | 1.000 | 40.6 dB |
| `dwt_qim` | Wavelet DWT | 2-level Haar DWT; detail subband QIM | 1.000 | 40.7 dB |
| `ss_spatial` | Pixel Spatial | Additive pseudo-noise spread-spectrum pattern | 0.962 | 39.9 dB |
| `fft_ring` | Fourier Ring | Annular mid-frequency magnitude modulation | 0.985 | 41.2 dB |
| `nmp_freq` | Non-Melting Points | Frequency-domain invariant feature point modulation | 1.000 | 42.1 dB |
| `svd_qim` | Block SVD | Spatial block singular value quantization | 1.000 | 43.8 dB |
| `dct_svd` | Hybrid DCT-SVD | SVD on mid-frequency DCT coefficients | 1.000 | 45.0 dB |

---

## 7. Dataset Provenance
- **MS-COCO val2017:** 5,000 photographic natural images used for training, threshold calibration, and in-distribution test evaluation.
- **PACS Benchmark:** 4 domains (Photo, Art Painting, Cartoon, Sketch) across 7 semantic categories. 200 source images per domain (800 sources / 1,600 derived samples overall) strictly reserved for out-of-distribution evaluation.

---

## 8. Source-Image and Derived-Sample Counts
| Dataset Partition | Source Images | Derived Samples | Negative Controls ($y=0$) | Positive Attacks ($y=1$) |
|:---|:---:|:---:|:---:|:---:|
| **Training Split** | 3,000 | On-the-fly random pairing | 50% | 50% |
| **Validation Split** | 500 | 1,000 | 500 | 500 |
| **Held-Out Test Split** | 1,500 | 3,000 | 1,500 | 1,500 |
| **PACS Cross-Domain** | 800 (200 / domain) | 1,600 (400 / domain) | 800 | 800 |

---

## 9. Train / Validation / Test Split Policy
Splits are strictly partitioned by **unique source image identifier** (`image_id`):
$$\mathcal{S}_{\text{train}} \cap \mathcal{S}_{\text{val}} = \emptyset, \quad \mathcal{S}_{\text{train}} \cap \mathcal{S}_{\text{test}} = \emptyset, \quad \mathcal{S}_{\text{val}} \cap \mathcal{S}_{\text{test}} = \emptyset$$
Zero image leakage exists across splits.

---

## 10. Frozen Checkpoint Identity and SHA-256
- **Checkpoint Location:** `checkpoints/final/rwguard_final_7scheme.pt`
- **File Size:** 9,890,147 bytes
- **SHA-256 Checksum:** `37680cdd2d4e5100cbb8aa1642e78b9bb3df373e79efd9f8512f89e15d0c0573`
- **Defended Checkpoint:** `runs/adv_eps1/best.pt` (SHA-256: `27954fd43360830d76fa107036567e9486844fa85d6a058c84d438b2e6caefed`)

---

## 11. Frozen Threshold
- **Operating Value:** $\tau = 1.3394016$
- **Calibration Criterion:** Calibrated on the 500-source validation split to enforce a 1.00% validation False Positive Rate.
- **Operating Behavior:** On the 1,500-source test split, $\tau$ yields $3.33\%$ FPR and $18.67\%$ TPR. The ROC-derived cutoff for 1.00% test FPR is $\tau_{\text{test}} = 1.6040$ (TPR: 7.87%).

---

## 12. Main Performance Summary
- **In-Distribution ROC-AUC:** **0.8543** [95% CI: 0.8410, 0.8672]
- **TPR @ 1.00% FPR:** **7.87%** [95% CI: 6.60%, 9.27%]
- **Fixed-Threshold TPR ($\tau=1.3394$):** **18.67%** [95% CI: 16.73%, 20.67%]
- **Fixed-Threshold FPR ($\tau=1.3394$):** **3.33%** [95% CI: 2.47%, 4.27%]

---

## 13. Resolution Evaluation (Table 8)
Evaluated across five spatial resolutions using dual global spatial pooling:
| Resolution | ROC-AUC [95% CI] | TPR @ 1% FPR | Fixed TPR ($\tau$) | Fixed FPR ($\tau$) | Status |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **128 px** | 0.8463 [0.832, 0.860] | 6.93% | 32.60% | 6.67% | Verified Bit-Identical |
| **256 px** | 0.8543 [0.841, 0.867] | 7.87% | 18.67% | 3.33% | Verified Bit-Identical |
| **384 px** | 0.8579 [0.844, 0.871] | 8.33% | 8.87% | 1.13% | Verified Bit-Identical |
| **512 px** | 0.8501 [0.836, 0.864] | 9.27% | 9.47% | 1.13% | Verified Bit-Identical |
| **1024 px** | 0.7998 [0.784, 0.815] | 16.50% | 18.50% | 1.50% | Verified Bit-Identical |

---

## 14. PACS Evaluation (Table 10)
| Domain | ROC-AUC [95% CI] | TPR @ 1% FPR | Fixed TPR ($\tau$) | Fixed FPR ($\tau$) | ECE | Brier Score |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Photo** | 0.8192 [0.774, 0.864] | 9.00% | 15.00% | 2.50% | 0.085 | 0.179 |
| **Art Painting** | 0.8616 [0.822, 0.901] | 6.00% | 18.00% | 3.50% | 0.092 | 0.161 |
| **Cartoon** | 0.8677 [0.830, 0.905] | 13.00% | 22.50% | 2.50% | 0.094 | 0.157 |
| **Sketch** | 0.8247 [0.781, 0.868] | 13.00% | 13.50% | 1.50% | 0.111 | 0.180 |

---

## 15. Shortcut-Learning Controls (Table 17)
- **Distortion-Matched Single Control:** Single watermarks embedded at matched double strength (38.5 dB PSNR) yield AUC **0.5747** ($\Delta \text{AUC} = -0.2730, p < 0.001$).
- **Matched-Noise Single Control:** Singly-watermarked images with matched Gaussian noise yield AUC **0.7296** ($\Delta \text{AUC} = -0.1181, p < 0.001$).
- **L2 Logistic Regression Baseline:** Handcrafted residual features yield AUC **0.5569** ($\Delta \text{AUC} = -0.2908, p < 0.001$).
- **Random Forest Baseline:** 100 trees, depth 8 yield AUC **0.5500** ($\Delta \text{AUC} = -0.2982, p < 0.001$).

---

## 16. TrustMark and StegaStamp Results (Table 14)
- **StegaStamp (CVPR 2020):** Pretrained ONNX model achieves zero-shot ROC-AUC **0.9293** [0.902, 0.954] and TPR@1% FPR **16.67%**.
- **TrustMark Zero-Shot (ICCV 2025):** Evaluated against stratified controls yields ROC-AUC **0.6562** [0.615, 0.701] (historical 4-scheme baseline: 0.5344).
- **TrustMark Supervised Adaptation:** Fine-tuning with 15% TrustMark exposure (20 epochs) achieves ROC-AUC **0.8505** [0.803, 0.894] and TPR@1% FPR **22.00%**.

---

## 17. Ownership Attack Categories (Table 16)
Evaluated across 500 collision attacks:
1. **Successful Overwrite (13.4% [10.66%, 16.69%]):** Fixed TPR 11.9%, AUC 0.639.
2. **Dual Survival (85.0% [81.60%, 87.86%]):** Fixed TPR 20.7%, AUC 0.736.
3. **Failed Attacker (1.6% [0.81%, 3.12%]):** Fixed TPR 12.5%, AUC 0.785.
4. **Mutual Destruction (0.0% [0.00%, 0.74%]):** Zero observed occurrences.

---

## 18. Adversarial Evaluation (Table 13)
- **PGD-10 ($L_\infty, \epsilon = 1/255, 2/255, 4/255$):** Undefended model detection drops from 36.0% (clean) to **0.0%** across all epsilon levels.
- **Defended Model (`runs/adv_eps1/best.pt`):** Achieves 81.2% detection on clean re-watermarks, but collapses under stronger perturbations, providing transparent diagnostic evidence of defense boundaries.

---

## 19. Statistical Methodology
- **Source-Grouped Bootstrapping:** $B = 2,000$ replicates resampled at the source `image_id` level.
- **Uncertainty Reporting:** 95% percentile confidence intervals on all primary metrics.
- **Seed Variance:**
  - *Protocol A (500 sources):* Mean AUC **0.8528**, Sample SD $s = 0.0030$, Population SD $\sigma = 0.0024$.
  - *Protocol B (1,500 sources):* Mean AUC **0.8530**, Sample SD $s = 0.0024$.

---

## 20. Limitations
1. Low-FPR tail sensitivity (7.87% TPR @ 1% FPR) due to subtle, localized perturbations.
2. Negative score deflation on non-photorealistic artwork (recalibration required).
3. Cross-family generalization drop on deep diffusion watermarkers without adaptation.
4. Susceptibility to white-box gradient evasion.

---

## 21. Repository Structure
```text
rwg-push/
├── checkpoints/              # Frozen model weights (SHA-256 verified)
├── configs/                  # Model and training hyperparameters
├── docs/                     # Authoritative compliance & reproducibility docs
├── manuscript/               # Final revised DOCX and PDF manuscripts
├── results/                  # Raw prediction arrays, metrics CSVs, and JSON logs
├── scripts/                  # Automated verification and reproduction scripts
├── tests/                    # Pytest automated regression test suite
├── deliverables/             # Final faculty submission ZIP archive & checksums
├── evaluate.py               # In-distribution evaluation harness
├── pacs_calibration.py       # Cross-domain PACS evaluation script
├── shortcut_baseline.py      # Baseline models evaluation script
└── requirements.txt          # Pinned dependency environment
```

---

## 22. Installation Instructions
```bash
git clone https://github.com/Advaith2380/rw-guard-watermarks.git
cd rw-guard-watermarks
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 23. Environment Requirements
- Python 3.10+
- PyTorch >= 2.0.0
- torchvision >= 0.15.0
- CUDA capable GPU (optional, CPU execution fully supported)

---

## 24. Reproduction Commands
```bash
# In-distribution evaluation
python evaluate.py --checkpoint checkpoints/final/rwguard_final_7scheme.pt --data-split test

# Multi-resolution metrics verification
python scripts/verification/verify_final_resolution_metrics.py

# PACS cross-domain calibration
python pacs_calibration.py --checkpoint checkpoints/final/rwguard_final_7scheme.pt

# Shortcut baselines & controls
python shortcut_baseline.py
python matched_controls.py

# StegaStamp & TrustMark evaluations
python test_stegastamp_detector.py
python evaluate_trustmark_cache.py

# Attack-outcome stratification
python evaluate_outcomes.py
```

---

## 25. Verification Commands
```bash
# Authoritative Faculty Submission Verification
python scripts/verify_faculty_submission.py

# Automated Regression Test Suite
pytest tests/
```

---

## 26. Expected Outputs
- `pytest tests/`: 22 passed in ~60 seconds.
- `scripts/verify_faculty_submission.py`: 11 audit gates reporting `[PASS]`, with `OVERALL VERDICT: ALL AUDIT GATES PASSED`.

---

## 27. Data Download Instructions
If generating raw images from scratch:
- **MS-COCO val2017:** Download from `http://images.cocodataset.org/zips/val2017.zip` and extract to `data/coco/val2017/`.
- **PACS Benchmark:** Download from official benchmark source and place in `data/pacs/`.

---

## 28. Checkpoint Usage
```python
import torch
from configs.model_config import load_config
from rewm.models import ForensicNet

config = load_config('configs/final_model_config.json')
model = ForensicNet(config)
state_dict = torch.load('checkpoints/final/rwguard_final_7scheme.pt', map_location='cpu')
model.load_state_dict(state_dict)
model.eval()

# Input image tensor: (B, 3, H, W) normalized to [0, 1]
# Output logit: scalar tensor where values >= 1.3394016 denote re-watermarking
```

---

## 29. Citation Instructions
```bibtex
@article{rajesh2026rwguard,
  title={RW-Guard: Key-Free Forensic Detection of Sequential Re-Watermarking in Digital Images},
  author={Rajesh, Advaith and Asrar and Eapen, Riz},
  journal={Scientific Reports (Under Revision)},
  year={2026}
}
```

---

## 30. License and Data Redistribution Notices
- **Code:** Licensed under the MIT License.
- **Checkpoints:** Provided for research and non-commercial evaluation.
- **Datasets:** MS-COCO is subject to Creative Commons Attribution 4.0; PACS is subject to its original academic research license.

---

## 31. Contributor Information
- **Advaith Rajesh** (Vellore Institute of Technology, Vellore, Tamil Nadu, India)
- **Asrar** (Vellore Institute of Technology, Vellore, Tamil Nadu, India)
- **Riz Eapen** (Vellore Institute of Technology, Vellore, Tamil Nadu, India)
- **Repository:** [https://github.com/Advaith2380/rw-guard-watermarks](https://github.com/Advaith2380/rw-guard-watermarks)
