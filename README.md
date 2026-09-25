# Watermark generation and sanity check

Part of the **RW-Guard** re-watermarking forensics project (Team 12). This piece covers environment setup, dataset download, 7 watermark simulators, and the sanity check that verifies they are invisible and that the re-watermarking attack works.

## Background

An invisible watermark is a hidden signal placed inside an image, used to prove ownership or that an image was AI-generated. **Re-watermarking** is an attack where a second watermark is added on top of the first, suppressing the original owner's signal. This repo builds and validates the watermark simulators used to train and test a detector for that attack.

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
| **`dct_qim`** | Splits the image into 8x8 blocks, transforms each into frequency values (block DCT — the same transform JPEG uses), and rounds a few mid-frequency values to encode bits (QIM: quantization index modulation) | Leaves a faint grid-like pattern |
| **`dwt_qim`** | Splits the image into a blurry layer and detail layers (wavelet transform), then rounds values in the detail layers the same way | Pattern is finer, not grid-shaped |
| **`ss_spatial`** | Adds a faint random static pattern directly over the pixels (spread spectrum) — no transform | Content-agnostic and additive, so it does *not* fully erase a differently-added mark |
| **`fft_ring`** | Adjusts the average strength of concentric rings in the image's frequency spectrum (Fourier transform) | Inspired by Tree-Ring watermarking used in generative AI images |
| **`nmp_freq`** | Only embeds in "stable" textured regions of the image (skips flat areas and hard edges), based on **Non-Melting Points** | Simplified version of **PECCAVI** (CVPR 2026) — designed to survive heavy edits better than the others |
| **`svd_qim`** | Splits each 8x8 block via **Singular Value Decomposition** and rounds the block's dominant singular value | Classical SVD watermarking; harder to fully overwrite than block-QIM methods |
| **`dct_svd`** | Runs DCT first, then SVD on the result, and rounds the dominant singular value | Hybrid of `dct_qim` and `svd_qim` |

`nmp_freq`, `svd_qim` and `dct_svd` were added as simplified, code-only versions of real 2026-era watermarking research. Neural methods such as StegaStamp, Stable Signature, VideoSeal and TrustMark need large pretrained models and are not implemented here.

## What the sanity check verifies

**Table 1 — single embedding:** for each method, PSNR (higher = less visible) and bit accuracy of the owner's own decoder (1.00 = perfect).

**Table 2 — re-watermarking attack:** for every "victim method > attacker method" pair, how much of the *original* owner's message survives (victim bit accuracy), how well the *attacker's* message reads, and the final image's PSNR.
- **Victim accuracy near 0.50** = the original watermark was destroyed (coin-flip). Happens for same-method attacks with `dct_qim`, `dwt_qim`, `fft_ring`, and partially with `svd_qim`/`dct_svd`.
- **Victim accuracy near 1.00** = both watermarks survive, creating ownership ambiguity. Common with `ss_spatial` and across different methods.

`example.png` shows this visually: the clean, single-watermarked and re-watermarked images look identical, while difference maps (amplified 20x) reveal the hidden patterns each method leaves behind.

## Files

| File | Purpose |
|---|---|
| `download_data.py` | Downloads COCO val2017 and PACS |
| `rewm/watermarks.py` | The 7 watermark schemes: embed and extract functions |
| `rewm/data.py` | Image loading utilities used by the sanity check |
| `sanity_check.py` | Verifies the watermarks and saves `example.png` |
| `requirements.txt` | Python dependencies |
