# REPOSITORY_INVENTORY.md

Repo root: `https://github.com/Advaith2380/rw-guard-watermarks`, branch `main`, commit `17a54fc`
at time of audit. Total working-tree size: 7.5 MB (no datasets, checkpoints, or results
committed — see `.gitignore` and `RESOURCE_AUDIT.md`).

## Top-level files

| File | Role |
|---|---|
| `README.md` | Project overview, setup instructions, scheme descriptions, TrustMark/StegaStamp usage. |
| `requirements.txt` | pip dependencies; PyTorch intentionally left out (install separately per platform/CUDA); neural-watermarker deps (`trustmark`, `onnxruntime`, `requests`) marked optional. |
| `.gitignore` | Excludes `__pycache__/`, `*.pyc` only (UTF-16LE encoded file — unusual but functions correctly with git). No `data/`, `runs/`, `results/` entries — those directories simply have never been created/committed, not explicitly ignored. |
| `example.png` | Output of `sanity_check.py`: visual proof of watermark invisibility + re-watermarking difference maps (3.7 MB). |
| `download_data.py` | Downloads MS-COCO val2017 subset (`--n-coco`, default 5000) and PACS (`--n-pacs` per domain, default 400) via the `datasets` package. Entry point, `__main__` guard present. |
| `sanity_check.py` | Validates all 7 watermark schemes on real photos: PSNR + bit-accuracy (single embedding) and victim/attacker bit-accuracy for every re-watermarking pair. Computes attack-outcome data (success/dual-survival) **as print output only**, not persisted or reusable by other scripts. |
| `train.py` | Main training entry point for the classical 7-scheme testbed. Supports architecture choice, holdout schemes, adversarial (PGD) training, seeding. Saves `last.pt`/`best.pt` (each embeds `args=vars(args)` and `train_schemes`) and `history.json` to `--out`. |
| `evaluate.py` | Six-axis evaluation harness (in-distribution, benign post-processing, resolution, unseen-scheme, PACS cross-domain, adversarial PGD-10). Writes `results.json`, `results.md`, `roc.png` to `--out`. Implements `tpr_at_0p1pct_fpr` already (review item P, partially satisfied — see traceability matrix). |
| `train_with_neural.py` | Training entry point that mixes TrustMark and/or StegaStamp cache images into the classical generator via `rewm_mixing.MixedDataset`/`MultiMixedDataset`. Same CLI surface as `train.py` plus `--trustmark-dir`, `--trustmark-p`, `--stegastamp-dir`, `--stegastamp-p`. |
| `build_trustmark_cache.py` | Precomputes clean/single/re-watermarked TrustMark image triplets to disk (`--out data/trustmark_cache`), avoiding repeated TrustMark inference during training. |
| `build_stegastamp_cache.py` | Same, for StegaStamp (ONNX model). |
| `rewm_trustmark.py` | `TrustMarkCacheDataset` (reads the precomputed cache) + `MixedDataset` (probabilistically blends classical and TrustMark samples). Contains the seeded `_train_rng()` fix. |
| `rewm_stegastamp.py` | Wraps the ONNX-exported StegaStamp encoder/decoder (auto-downloads weights on first use from a public mirror of the original authors' checkpoints, per README). |
| `rewm_stegastamp_cache.py` | `StegaStampCacheDataset`, mirrors `rewm_trustmark.py`'s cache dataset. Contains the seeded `_train_rng()` fix. |
| `rewm_mixing.py` | `MultiMixedDataset`: generalizes `rewm_trustmark.MixedDataset` to blend an arbitrary number of sources (classical + TrustMark + StegaStamp) by configurable probability. |
| `test_trustmark.py` | Manual script (`__main__` guard): standalone TrustMark sanity check (PSNR, bit accuracy on N sample images). Not a pytest test. |
| `test_trustmark_detector.py` | Manual script: zero-shot detector evaluation against TrustMark-watermarked images, given a trained checkpoint. Not a pytest test. |
| `test_stegastamp.py` | Manual script: standalone StegaStamp sanity check, mirrors `test_trustmark.py`. |
| `test_stegastamp_detector.py` | Manual script: zero-shot detector evaluation against StegaStamp, mirrors `test_trustmark_detector.py`. |
| `test_realistic_attack.py` | Manual script: the one existing "combined/matched" robustness test — applies a random border crop + JPEG re-encode to both classes and reports AUC/TPR/FPR. This is the closest existing artifact to review items E/F (distortion-matched controls), but it is a single combined-benign-op test, not a systematic matched-control generator. |

## `rewm/` package

| File | Role |
|---|---|
| `__init__.py` | Empty/minimal package marker. |
| `watermarks.py` (17.5 KB — largest file in the repo) | All 7 scheme implementations (`dct_qim`, `dwt_qim`, `ss_spatial`, `fft_ring`, `nmp_freq`, `svd_qim`, `dct_svd`), `embed_random`, `psnr`, `SCHEMES` registry, `NBITS`. No bit-accuracy/outcome-classification helper exposed here (that logic is duplicated inline in `sanity_check.py` only). |
| `data.py` | `ReWMDataset` (on-the-fly classical watermark generator), `list_images`, `split_paths` (deterministic, source-image-level 60/10/30 split), `load_image`, `apply_benign` (JPEG/noise/blur/brightness), `BENIGN_TRAIN`. Contains the seeded `_train_rng()` fix (confirmed present in source). |
| `model.py` | `ForensicNet` (proposed detector, fixed `HighPass` front end + `ResBlock` residual backbone + global avg/max pooling), `SimpleClassifier` (plain-CNN baseline), `TVResNet18` (torchvision ResNet-18 wrapper, `weights=None`), `build_model(arch, width)` dispatcher supporting `forensic` / `forensic_nohp` / `simple` / `resnet18`. No SRNet/ZhuNet/SiaStegNet. |
| `engine.py` | `predict()` (batched inference loop) and `pgd_attack()` (white-box L∞ PGD, steps/eps/step_frac configurable, no random restarts). |
| `metrics.py` | `roc_auc`, `threshold_at_fpr`, `tpr_at_fpr`, `rates_at`, `roc_curve`, `summarize` (bundles AUC + TPR@1%FPR + **TPR@0.1%FPR**, already implemented), `breakdown` (per-watermark-combination detection rate). No bootstrap/confidence-interval function exists here. |

## Directories that do NOT exist in this clone or container

`data/` (COCO, PACS, caches), `runs/` (checkpoints), `results/` (evaluate.py output), any
`tests/` directory, any `.github/workflows/` CI config, any notebook (`.ipynb`) files. This is
expected and by design — see `RESOURCE_AUDIT.md` §Datasets and §Checkpoints.

## Documentation

- `README.md` — setup + scheme explanations + neural-watermarker usage (current, matches code).
- No `CHANGELOG.md`, `CONTRIBUTING.md`, or architecture-decision-record docs existed before this
  package.
- The manuscript (`report.tex`/`report.docx`) is **not** part of this GitHub repository (by the
  user's explicit standing instruction from prior sessions — only code goes to GitHub, the
  report is delivered as a file). It is therefore out of scope for this code audit and this
  handover package does not touch it, per rule 2.12 of the task instructions ("Do not modify the
  research manuscript, report, references, or presentation").

## External integration code

- TrustMark: official `trustmark` pip package (bundled pretrained weights), wrapped by
  `rewm_trustmark.py` + `build_trustmark_cache.py`.
- StegaStamp: no official pip package; `rewm_stegastamp.py` wraps a community ONNX export
  (ISPRAS WIBE benchmark, Apache-2.0) of the original Tancik et al. CVPR 2020 checkpoints,
  auto-downloaded on first use.
- No Neo4j or other graph/database component exists anywhere in this repository.
