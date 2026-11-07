# Scientific Reproducibility Guide

This guide details the environment setup, dependency management, automated test execution, and end-to-end reproduction commands for the RW-Guard research project.

---

## 1. Environment & Hardware Prerequisites

- **Operating System:** Linux (Ubuntu 20.04/22.04), Windows 10/11, or macOS (x86_64 / Apple Silicon).
- **Python Version:** Python 3.10, 3.11, 3.12, or 3.13.
- **Hardware Requirements:**
  - *Minimum:* Single 4GB GPU (e.g., NVIDIA GeForce GTX 1650) or modern multi-core CPU.
  - *RAM:* 8GB minimum (16GB recommended for full test evaluations).
  - *Disk Space:* 5GB for code, checkpoints, and cached predictions; 25GB if downloading raw MS-COCO and PACS image corpora.

---

## 2. Dependency Installation

Clone the repository and install the verified pinned dependencies:

```bash
git clone https://github.com/Advaith2380/rw-guard-watermarks.git
cd rw-guard-watermarks

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Core Dependency List
```text
torch>=2.0.0
torchvision>=0.15.0
numpy>=1.24.0
scipy>=1.10.0
scikit-learn>=1.2.0
pandas>=2.0.0
pytest>=7.0.0
onnxruntime>=1.15.0
python-docx>=0.8.11
tqdm>=4.65.0
```

---

## 3. Immediate Integrity & Checkpoint Verification

Before running experiments, verify that the frozen primary checkpoint is bit-identical to the audited release:

```bash
# Verify primary checkpoint SHA-256
python -c "
import hashlib
with open('checkpoints/final/rwguard_final_7scheme.pt', 'rb') as f:
    h = hashlib.sha256(f.read()).hexdigest()
assert h == '37680cdd2d4e5100cbb8aa1642e78b9bb3df373e79efd9f8512f89e15d0c0573', f'Hash mismatch: {h}'
print('SUCCESS: Primary checkpoint SHA-256 verified.')
"
```

---

## 4. Master Automated Verification Script

To execute the authoritative verification suite covering checkpoints, model configurations, numerical consistency across all tables, abstract word counts, reference mapping, and package integrity:

```bash
python scripts/verify_faculty_submission.py
```

Expected output:
```text
[PASS] Checkpoint Integrity: 37680cdd...
[PASS] Model Architecture & Seven Schemes
[PASS] Table 8 Resolution Metrics (128, 256, 384, 512, 1024 px)
[PASS] Table 10 PACS Cross-Domain Metrics
[PASS] Table 12 Multi-Seed Statistics (Protocol A & B)
[PASS] Table 14 Deep Neural Watermarkers (TrustMark & StegaStamp)
[PASS] Table 16 Attack Outcome Accounting (500/500 sum)
[PASS] Table 17 Shortcut-Learning Baselines & Controls
[PASS] Abstract Word Count (<= 250 words)
[PASS] Reference Format ([1]-[28] sequential, no stray citations)
[PASS] Faculty Acceptance Matrix Completeness (53/53 PASS)
OVERALL VERDICT: ALL AUDIT GATES PASSED
```

---

## 5. Automated Regression Test Suite

Run the full automated pytest suite:

```bash
pytest tests/
```
Expected result: **22/22 passed**.

---

## 6. End-to-End Reproduction Commands

### 6.1 In-Distribution Test Evaluation
```bash
python evaluate.py --checkpoint checkpoints/final/rwguard_final_7scheme.pt --data-split test --batch-size 32
```

### 6.2 Multi-Resolution Evaluation
```bash
python scripts/verification/verify_final_resolution_metrics.py
```

### 6.3 PACS Cross-Domain Calibration
```bash
python pacs_calibration.py --checkpoint checkpoints/final/rwguard_final_7scheme.pt
```

### 6.4 Shortcut-Learning Controls & Baselines
```bash
python shortcut_baseline.py
python matched_controls.py
```

### 6.5 Deep Neural Watermarker Evaluation
```bash
# StegaStamp ONNX inference
python test_stegastamp_detector.py

# TrustMark zero-shot & supervised adaptation
python evaluate_trustmark_cache.py
```

### 6.6 Attack-Outcome Stratification
```bash
python evaluate_outcomes.py
```

### 6.7 Source-Grouped Bootstrap Confidence Intervals
```bash
python compute_confidence_intervals.py --bootstrap-replicates 2000
```

---

## 7. External Dataset Setup (Optional for Fresh Image Synthesis)

If regenerating raw watermarked images from scratch rather than evaluating against the audited prediction arrays:
1. **MS-COCO val2017:** Download `val2017.zip` (1GB) from [COCO Consortium](http://images.cocodataset.org/zips/val2017.zip) and extract into `data/coco/val2017/`.
2. **PACS Benchmark:** Download the PACS image dataset from the official repository and place under `data/pacs/`.
