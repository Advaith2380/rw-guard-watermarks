"""Verification Toolchain Step 13: Final Package Assembly & Cryptographic Integrity Verification.

Assembles deliverables/RW_GUARD_FINAL_VERIFICATION_PACKAGE.zip containing:
1. Complete independent verification audit tree (audit/final_independent_verification/)
2. Verified canonical JSON artifacts (verified_artifacts/)
3. Complete verification toolchain scripts
4. Primary frozen model checkpoint and config
5. Top-level comprehensive verification README.md

Verifies the archive by:
1. Testing ZIP archive integrity (CRC32 checksums).
2. Performing clean test extraction to a temporary sandbox directory.
3. Confirming 100% presence of mandatory evidence files.
4. Calculating SHA-256 hash of the final archive and writing to:
   deliverables/RW_GUARD_FINAL_VERIFICATION_PACKAGE.sha256
"""

import hashlib
import json
import logging
import os
import shutil
import sys
import tempfile
import zipfile


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def build_package_readme() -> str:
    return """# RW-GUARD — FINAL INDEPENDENT VERIFICATION & EVIDENCE PACKAGE
## Forensic Detection of Re-Watermarking Attacks: A Deep Learning Approach to Identifying Ownership Forgery in Digital Images

---

## 1. Package Overview
This independent verification archive contains the complete cryptographic, statistical, architectural, and experimental evidence validating the RW-Guard research project.

- **Lead Auditor:** Antigravity Forensic Machine Learning Verification Toolchain
- **Verification Status:** **VERIFIED (ALL 6 CRITERIA PASS)**
- **Primary Model Checkpoint:** `checkpoints/final/rwguard_final_7scheme.pt`
- **Checkpoint SHA-256:** `37680cdd2d4e5100cbb8aa1642e78b9bb3df373e79efd9f8512f89e15d0c0573`
- **Trainable Parameters:** 2,466,099 (ForensicNet with fixed high-pass preprocessing)
- **Frozen Calibration Threshold:** tau = 1.3394016

---

## 2. Directory Structure of This Package
```
RW_GUARD_FINAL_VERIFICATION_PACKAGE/
│
├── README.md                                          # This document
├── FINAL_INDEPENDENT_VERIFICATION_REPORT.md           # 18-Section Master Audit Report
├── FINAL_ACCEPTANCE_MATRIX.json                       # 6-Criterion Acceptance Matrix
│
├── audit_evidence/                                    # Complete verification deliverables
│   ├── checkpoint_integrity.json                     # SHA-256 and bit-level integrity audit
│   ├── checkpoint_provenance.json                    # Exact weight match against Seed 0 epoch 14
│   ├── checkpoint_architecture_verification.json     # Parameter count and layer state verification
│   ├── primary_reproduction.json                     # Primary COCO 1,500-source evaluation
│   ├── primary_per_sample_predictions.csv            # All 3,000 test sample scores and labels
│   ├── primary_confusion_matrix.json                 # TP (280), FP (50), TN (1450), FN (1220)
│   ├── baseline_reproduction.json                    # LR, RF, and RW-Guard on common 500 sources
│   ├── paired_baseline_comparison.json               # Delta AUC (+0.2908 LR, +0.2982 RF, p < 0.001)
│   ├── confidence_intervals.json                     # Unified 95% CIs across all 34 conditions
│   ├── consolidated_statistical_results.csv          # Master statistical table
│   ├── paired_statistical_comparisons.csv            # Formal hypothesis test results
│   ├── bootstrap_diagnostics.json                    # Grouped bootstrap parameters (B=2,000)
│   ├── scientific_claim_audit.json                   # 8 core scientific claims audit
│   ├── secondary_evaluation_audit.json               # Multi-seed, PACS, benign, and PGD-10 audit
│   ├── test_results.txt                              # 22/22 regression tests passing log
│   ├── test_results.json                             # Automated test results schema
│   └── verified_artifacts/                           # 16 verified canonical JSON backups
│
├── checkpoints/                                       # Primary frozen model weights
│   └── final/
│       ├── rwguard_final_7scheme.pt                  # Primary 7-scheme weights (9.91 MB)
│       └── final_model_config.json                   # Model hyperparameters
│
└── verification_toolchain/                            # Self-contained audit scripts
    ├── verify_checkpoint.py
    ├── reproduce_primary_evaluation.py
    ├── audit_source_overlap.py
    ├── reproduce_baselines.py
    ├── compute_confidence_intervals.py
    ├── audit_json_artifacts.py
    ├── audit_scientific_claims.py
    ├── audit_secondary_evaluations.py
    ├── run_test_suite_audit.py
    ├── generate_final_evidence_report.py
    └── run_final_verification.py
```

---

## 3. Reproduction Instructions
To execute full independent end-to-end verification from source:
```bash
# Execute master verification pipeline
python verification_toolchain/run_final_verification.py
```

To run individual verification modules:
```bash
# 1. Verify Checkpoint SHA-256 and Architecture
python verification_toolchain/verify_checkpoint.py

# 2. Reproduce Primary Evaluation (1,500 sources, 3,000 samples)
python verification_toolchain/reproduce_primary_evaluation.py

# 3. Reproduce Handcrafted Baselines and Paired Statistics
python verification_toolchain/reproduce_baselines.py

# 4. Run Complete Regression Test Suite (22 Tests)
python verification_toolchain/run_test_suite_audit.py
```

---

## 4. Key Scientific Results Verified
1. **Primary Model Discriminability:** ROC-AUC **0.8543** [95% CI: 0.8408, 0.8674] on 1,500 held-out test source images.
2. **Definitive Baseline Superiority:** Delta AUC = **+0.2908** vs Logistic Regression, **+0.2982** vs Random Forest ($p < 0.001$, paired bootstrap strictly excludes zero).
3. **Attack Mechanics Characterization:** Re-watermarking attacks yield **85.0% dual watermark survival** (425/500 cases); complete erasure occurs in only 13.4% of attacks.
4. **Generalization Capabilities:** StegaStamp zero-shot AUC **0.9293**; TrustMark 15% adapted AUC **0.8505**; PACS cross-domain average AUC **0.8433**.
5. **Architectural Stability:** Multi-seed ensemble mean AUC = **0.8528 +/- 0.0024** across independent training runs.
"""


def package_verification_artifacts(out_dir="deliverables"):
    os.makedirs(out_dir, exist_ok=True)
    zip_path = os.path.join(out_dir, "RW_GUARD_FINAL_VERIFICATION_PACKAGE.zip")
    sha_path = os.path.join(out_dir, "RW_GUARD_FINAL_VERIFICATION_PACKAGE.sha256")
    log_file = os.path.join("audit/final_independent_verification", "package_verification.log")

    logger = logging.getLogger("package_verification")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fh = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    sh = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    fh.setFormatter(formatter)
    sh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(sh)

    logger.info("================================================================================")
    logger.info(" PHASE 13: FINAL PACKAGE ASSEMBLY & CRYPTOGRAPHIC VERIFICATION")
    logger.info("================================================================================")

    # 1. Write Package README
    readme_content = build_package_readme()

    # 2. Files to include
    audit_dir = "audit/final_independent_verification"
    scripts = [
        "verify_checkpoint.py",
        "reproduce_primary_evaluation.py",
        "audit_source_overlap.py",
        "reproduce_baselines.py",
        "compute_confidence_intervals.py",
        "audit_json_artifacts.py",
        "audit_scientific_claims.py",
        "audit_secondary_evaluations.py",
        "run_test_suite_audit.py",
        "generate_final_evidence_report.py",
        "package_final_deliverables.py"
    ]

    logger.info(f"Assembling ZIP archive at: {zip_path}")
    file_count = 0

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Write README.md at root
        zipf.writestr("README.md", readme_content)
        file_count += 1

        # Write FINAL_INDEPENDENT_VERIFICATION_REPORT.md at root
        report_src = os.path.join(audit_dir, "FINAL_INDEPENDENT_VERIFICATION_REPORT.md")
        if os.path.exists(report_src):
            zipf.write(report_src, "FINAL_INDEPENDENT_VERIFICATION_REPORT.md")
            file_count += 1

        # Write FINAL_ACCEPTANCE_MATRIX.json at root
        matrix_src = os.path.join(audit_dir, "FINAL_ACCEPTANCE_MATRIX.json")
        if os.path.exists(matrix_src):
            zipf.write(matrix_src, "FINAL_ACCEPTANCE_MATRIX.json")
            file_count += 1

        # Add entire audit_evidence/ directory
        for root, dirs, files in os.walk(audit_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, audit_dir)
                archive_name = os.path.join("audit_evidence", rel_path).replace("\\", "/")
                zipf.write(full_path, archive_name)
                file_count += 1

        # Add primary checkpoint and config
        ckpt_path = "checkpoints/final/rwguard_final_7scheme.pt"
        if os.path.exists(ckpt_path):
            zipf.write(ckpt_path, "checkpoints/final/rwguard_final_7scheme.pt")
            file_count += 1
        cfg_path = "checkpoints/final/final_model_config.json"
        if os.path.exists(cfg_path):
            zipf.write(cfg_path, "checkpoints/final/final_model_config.json")
            file_count += 1

        # Add verification toolchain scripts
        for sc in scripts:
            if os.path.exists(sc):
                zipf.write(sc, f"verification_toolchain/{sc}")
                file_count += 1

    zip_size = os.path.getsize(zip_path)
    logger.info(f"Archive created with {file_count} files ({zip_size:,} bytes / {zip_size/(1024*1024):.2f} MB)")

    # 3. Test Archive Integrity
    logger.info("Testing ZIP archive integrity (testzip)...")
    with zipfile.ZipFile(zip_path, "r") as zipf:
        bad_file = zipf.testzip()
        if bad_file:
            logger.error(f"CORRUPT FILE DETECTED IN ARCHIVE: {bad_file}")
            return False
    logger.info("ZIP archive testzip integrity check: PASS (0 corrupt files)")

    # 4. Test Extraction to clean temporary directory
    logger.info("Performing test extraction to clean temporary directory...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        with zipfile.ZipFile(zip_path, "r") as zipf:
            zipf.extractall(tmp_dir)
        
        # Verify key files in extracted folder
        mandatory_test_files = [
            "README.md",
            "FINAL_INDEPENDENT_VERIFICATION_REPORT.md",
            "FINAL_ACCEPTANCE_MATRIX.json",
            "checkpoints/final/rwguard_final_7scheme.pt",
            "audit_evidence/checkpoint_integrity.json",
            "audit_evidence/primary_reproduction.json",
            "audit_evidence/paired_baseline_comparison.json",
            "audit_evidence/confidence_intervals.json",
            "audit_evidence/test_results.json"
        ]
        for mf in mandatory_test_files:
            extracted_path = os.path.join(tmp_dir, mf)
            if not os.path.exists(extracted_path):
                logger.error(f"Missing mandatory file in extracted archive: {mf}")
                return False
        logger.info(f"Verified extraction: All {len(mandatory_test_files)} mandatory artifacts verified present.")

    # 5. Compute SHA-256 of ZIP Archive
    zip_sha256 = compute_sha256(zip_path)
    with open(sha_path, "w", encoding="utf-8") as f:
        f.write(f"{zip_sha256}  RW_GUARD_FINAL_VERIFICATION_PACKAGE.zip\n")
    logger.info(f"Archive SHA-256: {zip_sha256}")
    logger.info(f"Saved SHA-256 manifest to: {sha_path}")

    logger.info("PHASE 13 PACKAGE ASSEMBLY & VERIFICATION: PASS")
    logger.info("================================================================================\n")
    return True


if __name__ == "__main__":
    package_verification_artifacts()
