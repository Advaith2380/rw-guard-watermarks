# RW-Guard: Re-Watermarking Forensics

Part of the **RW-Guard** re-watermarking forensics project (Team 12). A re-watermarking attack suppresses an image's original ownership watermark by embedding a second, independent watermark on top of it. This repo contains the full pipeline: a 7-scheme watermark testbed, a resolution-agnostic CNN detector, and the training/evaluation harness used to test it.

## Background

An invisible watermark is a hidden signal placed inside an image, used to prove ownership or that an image was AI-generated. **Re-watermarking** is an attack where a second watermark is added on top of the first, suppressing the original owner's signal while installing a fully readable attacker signal -- creating genuine ownership ambiguity. This repo builds and validates the watermark simulators used to generate training/test data, and a detector (**ForensicNet**) that classifies whether an image has been re-watermarked, using only pixel evidence -- no secret key, no decoder, no fingerprint database.

## Setup

```bash
pip install -r requirements.txt
python download_data.py       # downloads COCO val2017 (5000 photos) and PACS (4 domains)
python sanity_check.py --data data/coco
```

`sanity_check.py` prints two tables and saves `example.png`, showing that every watermark is invisible and that re-watermarking behaves as expected.

## The 7 watermark methods (`rewm/watermarks.py`)

Each method hides a 32-bit message inside an image's luminance (brightness) channel, using a secret key that controls where and how it is hidden. All are invisible to the eye (PSNR ~35-51 dB) and decode with ~100% accuracy.

| Method | Idea | Notes |
|---|---|---|
| **`dct_qim`** | Splits the image into 8x8 blocks, transforms each into frequency values (block DCT -- the same transform JPEG uses), and rounds a few mid-frequency values to encode bits (QIM: quantization index modulation) | Leaves a faint grid-like pattern |
| **`dwt_qim`** | Splits the image into a blurry layer and detail layers (wavelet transform), then rounds values in the detail layers the same way | Pattern is finer, not grid-shaped |
| **`ss_spatial`** | Adds a faint random static pattern directly over the pixels (spread spectrum) -- no transform | Content-agnostic and additive, so it does *not* fully erase a differently-added mark |
| **`fft_ring`** | Adjusts the average strength of concentric rings in the image's frequency spectrum (Fourier transform) | Inspired by Tree-Ring watermarking used in generative AI images |
| **`nmp_freq`** | Only embeds in "stable" textured regions of the image (skips flat areas and hard edges), based on **Non-Melting Points** | Simplified version of **PECCVAI** (CVPR 2026) -- designed to survive heavy edits better than the others |
| **`svd_qim`** | Splits each 8x8 block via **Singular Value Decomposition** and rounds the block's dominant singular value | Classical SVD watermarking; harder to fully overwrite than block-QIM methods |
| **`dct_svd`** | Runs DCT first, then SVD on the result, and rounds the dominant singular value | Hybrid of `dct_qim` and `svd_qim` |

`nmp_freq`, `svd_qim` and `dct_svd` were added as simplified, code-only versions of real 2026-era watermarking research. Full neural methods such as StegaStamp and Stable Signature need large pretrained models; one real neural watermarker (TrustMark) was mixed in separately as an additional check, not as part of this core testbed.

## What the sanity check verifies

**Table 1 -- single embedding:** for each method, PSNR (higher = less visible) and bit accuracy of the owner's own decoder (1.00 = perfect).

**Table 2 -- re-watermarking attack:** for every "victim method > attacker method" pair, how much of the *original* owner's message survives (victim bit accuracy), how well the *attacker's* message reads, and the final image's PSNR.
- **Victim accuracy near 0.50** = the original watermark was destroyed (coin-flip). Happens for same-method attacks with `dct_qim`, `dwt_qim`, `fft_ring`, and partially with `svd_qim`/`dct_svd`.
- **Victim accuracy near 1.00** = both watermarks survive, creating ownership ambiguity. Common with `ss_spatial` and across different methods.

`example.png` shows this visually: the clean, single-watermarked and re-watermarked images look identical, while difference maps (amplified 20x) reveal the hidden patterns each method leaves behind.

## The detector (`rewm/model.py`)

**ForensicNet** is a small (2.47M-parameter) CNN with two deliberate design choices:
1. A **fixed, non-trainable high-pass front end** (KV filter + directional-difference filters) that strips image content and keeps only high-frequency residuals, where the watermark signal actually lives.
2. A **residual backbone with global average+max pooling**, making the network resolution-agnostic -- the same weights score 128px, 256px and 384px inputs.

Three alternative architectures are included for ablation comparison: `ForensicNet(use_highpass=False)`, a plain `SimpleClassifier` CNN, and a standard `TVResNet18`. Select with `--arch forensic|forensic_nohp|simple|resnet18`.

## Training and evaluation

```bash
# train the main detector
python train.py --data data/coco --out runs/baseline

# hold one watermark scheme out of training, to test generalisation to it
python train.py --data data/coco --out runs/holdout_fft --holdout fft_ring

# adversarial training (PGD)
python train.py --data data/coco --out runs/adv --adv-eps 1.0 --adv-steps 7

# full evaluation: in-distribution, benign edits, resolution, unseen scheme,
# cross-domain (PACS), and white-box PGD adversarial robustness
python evaluate.py --ckpt runs/baseline/best.pt --data data/coco --pacs data/pacs --out results/baseline

# a more realistic combined attack (random crop + JPEG re-encode together)
python test_realistic_attack.py --ckpt runs/baseline/best.pt --data data/coco
```

## Headline results

- **In-distribution detection:** AUC 0.859 on the full held-out COCO test split, using only pixel evidence.
- **Architecture matters:** removing the high-pass front end, or swapping in a plain CNN or a 4x-larger ResNet-18, collapses AUC to ~0.50-0.52 (chance). Only the proposed design learns the signal.
- **Reproducible:** three independent training seeds land within a 0.003 AUC band.
- **Generalises, partially, to unseen schemes:** AUC ~0.82 when only the attacker's scheme is novel; drops to ~0.58 when both watermarks involved are novel.
- **Robust to resolution and common edits** (JPEG, noise, blur, brightness, and a combined crop+JPEG attack); less robust to cross-domain shift (PACS cartoon/sketch) without recalibration, and not yet robust to a white-box adversary -- both are documented as open limitations, including two adversarial-training attempts that did not succeed.

## Files

| File | Purpose |
|---|---|
| `download_data.py` | Downloads COCO val2017 and PACS |
| `rewm/watermarks.py` | The 7 watermark schemes: embed and extract functions |
| `rewm/data.py` | On-the-fly dataset: generates clean/single/re-watermarked samples |
| `rewm/model.py` | ForensicNet detector + ablation architectures (`SimpleClassifier`, no-highpass variant, ResNet-18) |
| `rewm/engine.py` | Training/prediction loop helpers and the PGD adversarial attack |
| `rewm/metrics.py` | AUC, TPR@FPR, fixed-threshold and per-scheme breakdown metrics |
| `sanity_check.py` | Verifies the watermarks and saves `example.png` |
| `train.py` | Trains the detector (baseline, hold-one-scheme-out, adversarial training) |
| `evaluate.py` | Full 6-axis evaluation harness (in-distribution, benign ops, resolution, unseen scheme, cross-domain, adversarial) |
| `test_realistic_attack.py` | Combined crop+JPEG attack test, same fixed-threshold methodology as `evaluate.py` |
| `requirements.txt` | Python dependencies |
