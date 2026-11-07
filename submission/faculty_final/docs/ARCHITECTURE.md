# ForensicNet Architecture & Inference Pipeline

## 1. Overview

**ForensicNet** is a fully convolutional neural network designed specifically for digital image forensics under re-watermarking attacks. Unlike standard computer vision backbones that capture high-level semantic content (e.g., objects, textures, scenes), ForensicNet is structured to suppress semantic features and isolate faint, high-frequency spatial residual interactions produced by sequential watermark embeddings.

The complete network contains **2,466,099 trainable parameters** (approximately 2.47M), making it lightweight and deployable on consumer-grade hardware (e.g., NVIDIA GeForce GTX 1650 4GB).

---

## 2. Structural Principles

1. **Semantic Suppression via Fixed Front-End ($K_{hp}$):**
   A non-trainable 9-channel Spatial Rich Model (SRM) high-pass filter bank filters the input image before any learnable convolutional layers. This layer attenuates low-frequency semantic scene content and emphasizes noise-like residual patterns.
2. **Full-Resolution Residual Preservation (Stem):**
   Early convolutional layers operate at full input resolution without striding or pooling. This prevents premature decimation of subtle watermark manipulation traces.
3. **Hierarchical Residual Extraction (Backbone):**
   A 4-stage residual backbone progressively downsamples feature maps while increasing channel depth ($32 \to 64 \to 128 \to 256$).
4. **Resolution-Agnostic Spatial Pooling (Dual Head):**
   Global Average Pooling and Global Max Pooling are applied across the entire spatial extent, collapsing arbitrary spatial dimensions $(H/16, W/16)$ into a fixed 512-dimensional vector. This allows identical model weights to evaluate images at 128px, 256px, 384px, 512px, and 1024px without resizing or interpolation.

---

## 3. Detailed Architectural Specifications

```
Input Image: X in R^{B x 3 x H x W}
    |
    v
[Input Normalization: (X / 255.0 - mu) / sigma]
    |
    v
[Fixed High-Pass Filter Bank K_hp (9 channels, 5x5, padding=2, stride=1, frozen)]
    |   Output: R in R^{B x 9 x H x W}
    v
[Stem Conv 1: Conv2d(9 -> 32, kernel=3, pad=1) + BatchNorm + ReLU]
    |
    v
[Stem Conv 2: Conv2d(32 -> 32, kernel=3, pad=1) + BatchNorm + ReLU]
    |   Output: F_0 in R^{B x 32 x H x W}
    v
[Residual Stage 1: ConvBlock(32 -> 64, stride=2) + BasicBlock(64 -> 64)]
    |   Output: F_1 in R^{B x 64 x (H/2) x (W/2)}
    v
[Residual Stage 2: ConvBlock(64 -> 128, stride=2) + BasicBlock(128 -> 128)]
    |   Output: F_2 in R^{B x 128 x (H/4) x (W/4)}
    v
[Residual Stage 3: ConvBlock(128 -> 256, stride=2) + BasicBlock(256 -> 256)]
    |   Output: F_3 in R^{B x 256 x (H/8) x (W/8)}
    v
[Residual Stage 4: ConvBlock(256 -> 256, stride=2) + BasicBlock(256 -> 256)]
    |   Output: F_4 in R^{B x 256 x (H/16) x (W/16)}
    v
[Dual Global Spatial Pooling]
    |---> GlobalAvgPool2d(F_4) -> v_avg in R^{B x 256}
    |---> GlobalMaxPool2d(F_4) -> v_max in R^{B x 256}
    v
[Concatenation: v = Concat(v_avg, v_max) in R^{B x 512}]
    |
    v
[Classification Head: Linear(512 -> 1)]
    |   Output: Scalar Logit z in R^{B x 1}
    v
[Threshold Decision: y_hat = 1 if z >= tau (1.3394016) else 0]
```

### Parameter Breakdown
- **Fixed Filter Bank ($K_{hp}$):** 0 trainable parameters (9 fixed 5x5 kernels).
- **Stem Layers:** 10,240 parameters.
- **Stage 1 (32 $\to$ 64):** 55,680 parameters.
- **Stage 2 (64 $\to$ 128):** 221,952 parameters.
- **Stage 3 (128 $\to$ 256):** 886,272 parameters.
- **Stage 4 (256 $\to$ 256):** 1,180,416 parameters.
- **Linear Head:** 513 parameters ($512 \times 1 + 1$).
- **Total Parameters:** **2,466,099 weights**.

---

## 4. High-Pass Filter Bank Specifications ($K_{hp}$)

The fixed front-end applies three spatial difference filters per color channel (9 filters total):
1. **$5 \times 5$ Discrete 2D Laplacian Kernel:**
   $$\begin{bmatrix}
   0 & 0 & -1 & 0 & 0 \\
   0 & -1 & -2 & -1 & 0 \\
   -1 & -2 & 16 & -2 & -1 \\
   0 & -1 & -2 & -1 & 0 \\
   0 & 0 & -1 & 0 & 0
   \end{bmatrix} \times \frac{1}{16}$$
2. **Horizontal 2nd-Order Difference Kernel:**
   $$\begin{bmatrix}
   0 & 0 & 0 & 0 & 0 \\
   0 & 0 & 0 & 0 & 0 \\
   -1 & 2 & -2 & 2 & -1 \\
   0 & 0 & 0 & 0 & 0 \\
   0 & 0 & 0 & 0 & 0
   \end{bmatrix} \times \frac{1}{4}$$
3. **Diagonal 2nd-Order Difference Kernel:**
   $$\begin{bmatrix}
   -1 & 0 & 0 & 0 & 0 \\
   0 & 2 & 0 & 0 & 0 \\
   0 & 0 & -2 & 0 & 0 \\
   0 & 0 & 0 & 2 & 0 \\
   0 & 0 & 0 & 0 & -1
   \end{bmatrix} \times \frac{1}{4}$$

These filters are registered as frozen buffers within the PyTorch model module (`torch.nn.Module.register_buffer`), guaranteeing that backpropagation never updates them.

---

## 5. Inference Algorithm (Algorithm 2)

```text
Algorithm 2: ForensicNet Forward Inference and Classification Pipeline
Input: Query image X in R^{H x W x 3}, fixed SRM filter bank K_hp in R^{9 x 3 x 5 x 5}, trained model weights Theta, frozen threshold tau = 1.3394016.
Output: Scalar logit z in R, probability p in [0, 1], prediction y_hat in {0, 1}.

1: Input Normalization:
   X_norm = (X / 255.0 - mu) / sigma, with mu = [0.485, 0.456, 0.406], sigma = [0.229, 0.224, 0.225].
2: Spatial Residual Extraction:
   R = Conv2d(X_norm, K_hp, padding=2, stride=1).
3: Full-Resolution Stem Convolution:
   F_0 = ConvStem(R) in R^{32 x H x W}.
4: Hierarchical Residual Learning:
   F_1 = ResBlock_1(F_0) in R^{64 x (H/2) x (W/2)}
   F_2 = ResBlock_2(F_1) in R^{128 x (H/4) x (W/4)}
   F_3 = ResBlock_3(F_2) in R^{256 x (H/8) x (W/8)}
   F_4 = ResBlock_4(F_3) in R^{256 x (H/16) x (W/16)}
5: Dual Global Spatial Pooling:
   v_avg = GlobalAvgPool2d(F_4) in R^{256}
   v_max = GlobalMaxPool2d(F_4) in R^{256}
   v = Concat(v_avg, v_max) in R^{512}
6: Scalar Logit Scoring:
   z = W_head^T v + b_head in R.
7: Thresholded Decision:
   p = 1 / (1 + exp(-z)).
   y_hat = 1 if z >= tau else 0.
8: return (z, p, y_hat).
```

---

## 6. Threshold Semantics & Operating Points

The decision threshold $\tau = 1.3394016$ was calibrated exclusively on the **held-out validation split** (500 sources, 1,000 samples) to enforce a target False Positive Rate of **1.00%** (3 false positives out of 300 negative samples).

When applied to the held-out test set:
- **Test FPR at Frozen $\tau$:** $3.33\%$ (50 / 1,500 negative samples).
- **Test TPR at Frozen $\tau$:** $18.67\%$ (280 / 1,500 positive samples).
- **ROC-Derived TPR @ 1.00% Test FPR:** $7.87\%$ (achieved at test cutoff $\tau = 1.6040$).

This distinction between fixed-threshold operating point and ROC-derived curve operating point is maintained throughout all evaluations.
