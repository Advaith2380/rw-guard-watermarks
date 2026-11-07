# Dataset Accounting, Splits, and Generation Pipeline

## 1. Source Image Provenance

RW-Guard relies on two authoritative datasets for development and validation:

1. **MS-COCO val2017 (In-Distribution Benchmark):**
   - **Corpus:** 5,000 natural photographs depicting everyday objects, individuals, and outdoor/indoor environments.
   - **Preprocessing:** Preserved at native photographic dynamic range; cropped to 128x128 patches during training; evaluated at native or specified spatial resolutions (128, 256, 384, 512, 1024 px) during testing.
   - **Role:** Source corpus for training, validation threshold selection, and principal in-distribution test evaluation.

2. **PACS Benchmark (Cross-Domain Benchmark):**
   - **Corpus:** 4 visual domains (Photo, Art Painting, Cartoon, Sketch) across 7 semantic classes, originally created by Li et al. (ICCV 2017).
   - **Accounting:** 
     - **Primary Benchmark:** 200 independent source images per domain (800 sources overall), yielding 400 derived samples per domain (1,600 derived samples overall).
     - **Extended Ablation Split:** 400 sources per domain (1,600 sources / 3,200 samples overall).
   - **Role:** Strictly held-out, out-of-distribution evaluation. ForensicNet is **never trained or validated on PACS imagery**.

---

## 2. Partitioning Policy & Source-Level Independence

To prevent **data leakage** and guarantee valid generalization estimates, all dataset splits are enforced at the **source image identifier level** (`image_id`):

$$\mathcal{S}_{\text{train}} \cap \mathcal{S}_{\text{val}} = \emptyset, \quad \mathcal{S}_{\text{train}} \cap \mathcal{S}_{\text{test}} = \emptyset, \quad \mathcal{S}_{\text{val}} \cap \mathcal{S}_{\text{test}} = \emptyset$$

No image, cropped patch, or derived variant of a source image appearing in training or validation is ever presented during test evaluation.

### MS-COCO Split Summary
| Split | Source Images | Derived Samples | Negative Controls ($y=0$) | Positive Attacks ($y=1$) | Role |
|:---|:---:|:---:|:---:|:---:|:---|
| **Train** | 3,000 | Dynamic (On-the-fly) | 50% (Singly-watermarked) | 50% (Re-watermarked) | Model training (Backprop) |
| **Validation** | 500 | 1,000 | 500 (Singly-watermarked) | 500 (Re-watermarked) | Model selection & $\tau$ calibration |
| **Held-Out Test** | 1,500 | 3,000 | 1,500 (Singly-watermarked) | 1,500 (Re-watermarked) | Primary benchmark evaluation |
| **Total** | **5,000** | — | — | — | Full MS-COCO val2017 set |

---

## 3. Seven Watermarking Schemes

The training and test pipelines evaluate seven distinct classical and transform-domain watermarking algorithms:

| Scheme Identifier | Domain / Family | Description | Parameter / Strength Range | Baseline PSNR | Baseline Bit-Acc |
|:---|:---|:---|:---:|:---:|:---:|
| `dct_qim` | Block DCT | 8x8 block DCT; QIM on mid-frequency AC coefficients | $\Delta \in [10, 30]$ | 40.6 dB | 1.000 |
| `dwt_qim` | Wavelet DWT | 2-level Haar DWT; QIM on LH/HL detail subbands | $\Delta \in [8, 24]$ | 40.7 dB | 1.000 |
| `ss_spatial` | Pixel Spread-Spectrum | Content-agnostic pseudo-noise addition in spatial domain | $\alpha \in [1.0, 3.0]$ | 39.9 dB | 0.962 |
| `fft_ring` | Fourier Ring | Annular mid-frequency magnitude modulation in 2D DFT | $\alpha \in [0.5, 2.0]$ | 41.2 dB | 0.985 |
| `nmp_freq` | Non-Melting Points | Frequency-domain invariant feature point modulation | $\Delta \in [12, 32]$ | 42.1 dB | 1.000 |
| `svd_qim` | Singular Value Decomp. | SVD on spatial blocks; singular value quantization | $\Delta \in [15, 35]$ | 43.8 dB | 1.000 |
| `dct_svd` | Hybrid DCT-SVD | SVD applied to mid-frequency DCT coefficients | $\Delta \in [10, 25]$ | 45.0 dB | 1.000 |

---

## 4. Dataset Generation Algorithm (Algorithm 1)

```text
Algorithm 1: Re-Watermarking Forensic Dataset Generation Pipeline
Input: Natural source image dataset S (MS-COCO val2017, N = 5,000 images), watermark scheme family W = {dct_qim, dwt_qim, ss_spatial, fft_ring, nmp_freq, svd_qim, dct_svd}, parameter distributions D_w, class balance ratio r = 0.5.
Output: Labeled forensic dataset D = {(X_i, y_i)}_{i=1}^{M} partitioned by source image.

1: Partition source images by unique source ID into disjoint subsets:
   S_train (3,000 sources), S_val (500 sources), S_test (1,500 sources), ensuring S_train ∩ S_val = ∅, S_train ∩ S_test = ∅, and S_val ∩ S_test = ∅.
2: for each split S_split ∈ {S_train, S_val, S_test} do
3:    for each source image I ∈ S_split do
4:       Sample target label y ~ Bernoulli(r).
5:       if y = 0 then  // Negative control: singly-watermarked image
6:          Sample scheme W_v ~ Uniform(W).
7:          Sample random key k_v and payload m_v; sample embedding strength α_v ~ D_Wv.
8:          Generate singly-watermarked carrier: X = Embed(I, W_v, k_v, m_v, α_v).
9:          Verify fidelity PSNR(I, X) ≥ 36.0 dB and recovery Bit-Acc(Extract(X, W_v, k_v), m_v) ≥ 0.75.
10:      else  // Positive class: sequentially re-watermarked image (attack)
11:         Sample victim scheme W_v ~ Uniform(W) and attacker scheme W_a ~ Uniform(W) independently.
12:         Sample keys k_v, k_a and payloads m_v, m_a; sample strengths α_v ~ D_Wv, α_a ~ D_Wa.
13:         Embed victim watermark: I_v = Embed(I, W_v, k_v, m_v, α_v).
14:         Embed secondary attacker watermark: X = Embed(I_v, W_a, k_a, m_a, α_a).
15:         Record post-collision bit-accuracies for W_v and W_a; compute carrier PSNR(I, X).
16:      end if
17:      Optionally apply benign transformation T (JPEG, noise, blur, crop) if evaluating robustness.
18:      Append labeled tuple (X, y, source_id, W_v, W_a) to partition D_split.
19:   end for
20: end for
21: return D_train, D_val, D_test.
```

---

## 5. Seed Reproducibility Protocols

To ensure statistical rigor, two distinct multi-seed evaluation protocols are maintained:

1. **Protocol A (500-Source Subset):**
   - **Evaluated Models:** 3 independent training runs (Seed 0, Seed 1, Seed 2).
   - **Dataset:** Fixed 500-source test subset (1,000 samples).
   - **Results:**
     - Seed 0: AUC 0.8556 [0.831, 0.878]
     - Seed 1: AUC 0.8531 [0.829, 0.876]
     - Seed 2: AUC 0.8497 [0.826, 0.872]
     - **Mean AUC:** **0.8528**
     - **Sample Standard Deviation ($s$, ddof=1):** **0.002955** ($\approx 0.0030$)
     - **Population Standard Deviation ($\sigma$, ddof=0):** **0.002413** ($\approx 0.0024$)

2. **Protocol B (Full 1,500-Source Split):**
   - **Evaluated Model:** Primary frozen model (Seed 0) and validation cross-checks.
   - **Dataset:** Complete 1,500-source held-out test split (3,000 samples).
   - **Results:** Mean AUC **0.8530**, Sample SD **0.0024** ($s=0.002350$).
