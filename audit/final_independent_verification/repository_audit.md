# RW-GUARD REPOSITORY DISCOVERY AND BASELINE AUDIT
**Date/Time:** 2026-11-06 12:19:22Z  
**Platform:** Windows-11-10.0.26300-SP0  
**Python:** 3.13.7  
**PyTorch:** 2.14.0+cu126 (CUDA: True - NVIDIA GeForce GTX 1650)  
**Git Commit:** `238b3197fa532f40d9e2cfb3554b4f0f6205185d` (Branch: `main`)  

---
## 1. Key Component Inspection
- **Primary Model Checkpoint:** `checkpoints/final/rwguard_final_7scheme.pt`
- **Watermark Core Package:** `rewm/` (`model.py`, `watermarks.py`, `data.py`, `outcomes.py`, `metrics.py`)
- **Evaluation Entrypoints:** `evaluate.py`, `matched_controls.py`, `shortcut_baseline.py`, `evaluate_trustmark_cache.py`, `test_stegastamp_detector.py`, `pacs_calibration.py`
- **Statistical Engine:** `bootstrap_ci.py` (Source-image grouped bootstrap, B=2,000 replicates)
- **Regression Test Suite:** `run_tests.py` (22 unit & integration tests)

## 2. Inventory Summary
- Total tracked files cataloged: 250
- Relevant evaluation artifacts: 236
- Pre-verification baseline snapshot established in `audit/final_independent_verification/pre_verification_backup/`

## 3. Environment Readiness Status
All critical dependencies (PyTorch with CUDA GTX 1650, NumPy, scikit-learn, OpenCV) are verified and operational.
