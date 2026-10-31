# TEST_RESULTS.md: Automated Verification and Test Execution Log

**Project:** Forensic Detection of Re-Watermarking Attacks (RW-Guard)  
**Date:** 2026-10-31  
**Environment:** Windows 11, Python 3.13.7 (`D:\projects\rewm-guard\.venv`), PyTorch 2.14.0+cu126, NVIDIA GeForce GTX 1650  
**Test Suite:** `run_tests.py` / `unittest` discovering `tests/test_*.py`  

---

## 1. Summary of Execution

| Category | Test File | Test Method | Execution Status | Runtime |
|---|---|---|---|---|
| **Determinism & Isolation** | `tests/test_determinism.py` | `test_split_paths_deterministic` | **PASS** | <0.1s |
| | `tests/test_determinism.py` | `test_split_paths_isolation` | **PASS** | <0.1s |
| | `tests/test_determinism.py` | `test_eval_dataset_sample_reproducibility` | **PASS** | 0.8s |
| **Forensic Metrics** | `tests/test_metrics.py` | `test_roc_auc_perfect` | **PASS** | <0.1s |
| | `tests/test_metrics.py` | `test_roc_auc_chance` | **PASS** | <0.1s |
| | `tests/test_metrics.py` | `test_roc_auc_inverted` | **PASS** | <0.1s |
| | `tests/test_metrics.py` | `test_threshold_at_fpr` | **PASS** | <0.1s |
| | `tests/test_metrics.py` | `test_rates_at` | **PASS** | <0.1s |
| | `tests/test_metrics.py` | `test_summarize_format` | **PASS** | <0.1s |
| | `tests/test_metrics.py` | `test_bootstrap_ci` | **PASS** | 0.5s |
| **Architectures & Steganalysis** | `tests/test_models.py` | `test_highpass_filter_shape_and_range` | **PASS** | <0.1s |
| | `tests/test_models.py` | `test_all_architectures_forward` (8 models incl. SRNet) | **PASS** | 0.6s |
| | `tests/test_models.py` | `test_resolution_invariance` | **PASS** | 0.2s |
| **Outcome Stratification** | `tests/test_outcomes.py` | `test_compute_bit_accuracy` | **PASS** | <0.1s |
| | `tests/test_outcomes.py` | `test_classify_attack_outcome_logic` | **PASS** | <0.1s |
| **Watermarking Schemes & Neural** | `tests/test_watermarks.py` | `test_all_seven_schemes_embed_and_extract` | **PASS** | 2.1s |
| | `tests/test_watermarks.py` | `test_same_scheme_overwriting` | **PASS** | 1.6s |
| | `tests/test_watermarks.py` | `test_stegastamp_embed_and_decode` (ONNX) | **PASS** | 2.4s |

**Total:** 18 passed, 0 failed, 0 skipped, 0 errors. Total run duration: 9.691s.

---

## 2. Neural Watermarker & Steganalysis Verification

### 2.1 StegaStamp Live Embed and Decode Validation
- **Engine:** `onnxruntime` executing official `stega_stamp.onnx` (219 MB) in `model_files/stega_stamp/stega_stamp.onnx`.
- **Single Embedding:** Mean PSNR = 29.4 dB, bit extraction accuracy = 1.000 (100% extraction).
- **Re-Watermarking Overwrite:** Mean PSNR = 29.2 dB, victim bit accuracy = 0.516 (51.6% near coin-flip, destroyed), attacker bit accuracy = 0.994 (99.4% readable).

### 2.2 SRNet (Steganalysis Residual Network) Architecture
- **Source:** [`rewm/srnet.py`](file:///D:/projects/rwg-push/rewm/srnet.py) (9.63M parameters) implementing the 12-layer unpooled/residual/pooling architecture from Boroumand et al. (IEEE TIFS 2019).
- **Training Smoke Run:** Trained on CUDA for 1 epoch (`runs/smoke_srnet/best.pt`) in 16.0s.

---

## 3. Integration Smoke Tests

| Script / Pipeline | Command | Outcome | Runtime | Key Verified Artifacts |
|---|---|---|---|---|
| **Training Pipeline (ForensicNet)** | `python train.py --epochs 1 --n-train 50 --n-val 20 --bs 8 --out runs/smoke_test_stage2` | **SUCCESS** | 8.2s | `runs/smoke_test_stage2/best.pt`, `config.json`, `split_manifest.json` |
| **Training Pipeline (SRNet)** | `python train.py --data D:/projects/rewm-guard/data/coco --arch srnet --epochs 1 --n-train 20 --n-val 10 --bs 4 --out runs/smoke_srnet` | **SUCCESS** | 16.0s | `runs/smoke_srnet/best.pt` (9.63M parameters) |
| **StegaStamp Pipeline** | `python test_stegastamp.py --data D:/projects/rewm-guard/data/coco --n 5` | **SUCCESS** | 10.8s | Verified 100% single bit accuracy and 51.6% overwrite |
| **Evaluation Pipeline** | `python evaluate.py --ckpt runs/smoke_test_stage2/best.pt --n-test 30 --n-val 20 --group 1 --adv-restarts 2` | **SUCCESS** | 12.1s | `results/smoke_test_stage2/results.json`, `predictions.npz` |
| **Rollback Verification** | `powershell scripts/RWGUARD_ROLLBACK.ps1 -DryRun` | **SUCCESS** | 1.1s | Dry run passed without mutation. |

---

## 4. Verification Conclusion
All 18 unit tests and 5 smoke pipelines pass with 100% success rate. Both StegaStamp (neural watermarker) and SRNet (specialized steganalysis baseline) are implemented, verified, and operational.
