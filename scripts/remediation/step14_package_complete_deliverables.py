"""
Step 14: Complete Deliverables Archive Packaging & Verification
Packages the complete, self-contained faculty review remediation package into:
deliverables/RW_GUARD_COMPLETE_FACULTY_REMEDIATION_PACKAGE.zip

Performs:
1. Comprehensive archive creation including code, weights, results, manifests, and audit reports.
2. CRC32 archive integrity validation (zipfile.testzip).
3. SHA-256 cryptographic checksum calculation.
4. Clean extraction verification to ensure zero corruption and complete portability.
5. Synchronization to conversation artifacts directory.
"""

import os
import sys
import zipfile
import hashlib
import shutil
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.abspath("."))

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=" * 80)
    print("STEP 14: COMPLETE DELIVERABLES ARCHIVE PACKAGING & INTEGRITY VERIFICATION")
    print("=" * 80)

    os.makedirs("deliverables", exist_ok=True)
    zip_path = "deliverables/RW_GUARD_COMPLETE_FACULTY_REMEDIATION_PACKAGE.zip"
    sha_path = "deliverables/RW_GUARD_COMPLETE_FACULTY_REMEDIATION_PACKAGE.sha256"

    # Define files and directories to include
    include_paths = [
        # 1. Source code and orchestration scripts
        "rewm",
        "scripts/remediation",
        "tests",
        "bootstrap_ci.py",
        "run_test_suite_audit.py",
        "run_rwguard_final_verification.ps1",
        
        # 2. Frozen Primary Checkpoint and configurations
        "checkpoints/final",
        
        # 3. Fresh predictions and primary results
        "results/final_primary",
        "results/final_7scheme_primary",
        
        # 4. Secondary experiment results
        "results/shortcut_controls",
        "results/attack_outcomes",
        "results/neural_generalization",
        "results/statistics",
        
        # 5. Dataset manifests
        "data/manifests",
        
        # 6. Audit evidence and compliance reports
        "audit/final",
        "audit/json_reconciliation",
        "audit/scientific_claims",
        "audit/remediation",
        "audit/checkpoint_audit.json",
        "audit/checkpoint_integrity.json",
        "audit/checkpoint_provenance.json",
        "audit/fresh_inference_verification.json",
        "audit/source_split_leakage_audit.json",
        "audit/dataset_inventory.json",
        "audit/dataset_count_reconciliation.json",
        "audit/section_A_acceptance.json",
        "audit/section_B_claim_audit.json",
        "audit/section_C_claim_audit.json",
        "audit/section_D_claim_audit.json",
        "audit/section_E_acceptance.json"
    ]

    print(f"\n[1/5] Building deliverables ZIP package: {zip_path}...")
    file_count = 0
    total_bytes = 0

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for item in include_paths:
            if not os.path.exists(item):
                print(f"  [WARNING] Path does not exist (skipping): {item}")
                continue
            
            if os.path.isfile(item):
                arcname = item.replace("\\", "/")
                zipf.write(item, arcname)
                fsize = os.path.getsize(item)
                total_bytes += fsize
                file_count += 1
            elif os.path.isdir(item):
                for root, _, files in os.walk(item):
                    for file in files:
                        full_p = os.path.join(root, file)
                        # Skip pycache or temporary files
                        if "__pycache__" in full_p or file.endswith(".pyc"):
                            continue
                        arcname = os.path.relpath(full_p, ".").replace("\\", "/")
                        zipf.write(full_p, arcname)
                        fsize = os.path.getsize(full_p)
                        total_bytes += fsize
                        file_count += 1

    zip_size = os.path.getsize(zip_path)
    print(f"Packaged {file_count} files ({total_bytes / (1024*1024):.2f} MB uncompressed -> {zip_size / (1024*1024):.2f} MB compressed).")

    # 2. Test ZIP integrity
    print("\n[2/5] Testing archive CRC32 integrity via zipfile.testzip()...")
    with zipfile.ZipFile(zip_path, "r") as zipf:
        bad_file = zipf.testzip()
        if bad_file is not None:
            raise RuntimeError(f"Corrupted file detected in ZIP archive: {bad_file}")
    print("Archive integrity verified: ZERO corrupted CRC32 checksums.")

    # 3. Calculate SHA-256 Checksum
    print("\n[3/5] Computing SHA-256 cryptographic checksum...")
    zip_sha = compute_sha256(zip_path)
    with open(sha_path, "w", encoding="utf-8") as f:
        f.write(f"{zip_sha}  {os.path.basename(zip_path)}\n")
    print(f"SHA-256: {zip_sha}")
    print(f"Checksum written to: {sha_path}")

    # 4. Clean extraction test in temporary directory
    print("\n[4/5] Testing clean extraction in isolated temporary sandbox...")
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(zip_path, "r") as zipf:
            zipf.extractall(temp_dir)
        
        extracted_ckpt = os.path.join(temp_dir, "checkpoints", "final", "rwguard_final_7scheme.pt")
        if not os.path.exists(extracted_ckpt):
            raise FileNotFoundError("Extracted archive is missing primary model checkpoint!")
        
        extracted_hash = compute_sha256(extracted_ckpt)
        expected_ckpt_hash = "37680cdd2d4e5100cbb8aa1642e78b9bb3df373e79efd9f8512f89e15d0c0573"
        if extracted_hash != expected_ckpt_hash:
            raise ValueError(f"Extracted checkpoint hash mismatch! {extracted_hash} vs {expected_ckpt_hash}")
        
        print(f"Extraction test SUCCESS: Verified {os.path.basename(extracted_ckpt)} SHA-256 match.")

    # 5. Copy to conversation artifact directory
    print("\n[5/5] Synchronizing deliverables to conversation artifact directory...")
    artifact_dir = r"C:\Users\advai\.gemini\antigravity\brain\3607de8d-963e-49ed-ab52-992ed93ae4d1"
    if os.path.exists(artifact_dir):
        dst_zip = os.path.join(artifact_dir, "RW_GUARD_COMPLETE_FACULTY_REMEDIATION_PACKAGE.zip")
        dst_sha = os.path.join(artifact_dir, "RW_GUARD_COMPLETE_FACULTY_REMEDIATION_PACKAGE.sha256")
        shutil.copy2(zip_path, dst_zip)
        shutil.copy2(sha_path, dst_sha)
        
        # Copy key audit reports as well
        report_src = "audit/final/FINAL_TECHNICAL_AUDIT_REPORT.md"
        if os.path.exists(report_src):
            shutil.copy2(report_src, os.path.join(artifact_dir, "FINAL_TECHNICAL_AUDIT_REPORT.md"))
        
        matrix_src = "audit/final/FINAL_FACULTY_COMPLIANCE_MATRIX.json"
        if os.path.exists(matrix_src):
            shutil.copy2(matrix_src, os.path.join(artifact_dir, "FINAL_FACULTY_COMPLIANCE_MATRIX.json"))
        
        print(f"Artifacts successfully mirrored to: {artifact_dir}")
    else:
        print(f"Note: Artifact directory {artifact_dir} does not exist locally; skipped mirror.")

    print("\n" + "=" * 80)
    print("STEP 14 COMPLETE: COMPLETE FACULTY DELIVERABLES PACKAGE READY & VERIFIED")
    print("=" * 80)

if __name__ == "__main__":
    main()
