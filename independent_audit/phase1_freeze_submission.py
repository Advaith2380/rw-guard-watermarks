"""
Phase 1: Freeze and identify the submission
Calculates SHA-256, sizes, timestamps, and Git status for all primary submission artifacts.
Outputs to:
- independent_audit/submission_identification.json
- independent_audit/submission_frozen_manifest.txt
"""

import os
import sys
import hashlib
import json
import subprocess
from datetime import datetime

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def get_file_info(filepath):
    if not os.path.exists(filepath):
        return {"exists": False, "path": filepath}
    stat = os.stat(filepath)
    return {
        "exists": True,
        "path": os.path.abspath(filepath).replace("\\", "/"),
        "size_bytes": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 4),
        "mtime_utc": datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z",
        "sha256": compute_sha256(filepath)
    }

def main():
    print("=" * 80)
    print("PHASE 1: SUBMISSION FREEZE & IDENTIFICATION")
    print("=" * 80)

    # 1. Git metadata
    git_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
    git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    git_status = subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()

    # 2. Key submission artifacts
    artifacts = {
        "primary_checkpoint_repo": get_file_info("checkpoints/final/rwguard_final_7scheme.pt"),
        "primary_checkpoint_submission": get_file_info("final_faculty_remediation/checkpoints/primary_checkpoint.pt"),
        "config_repo": get_file_info("checkpoints/final/final_model_config.json"),
        "config_submission": get_file_info("final_faculty_remediation/configs/final_model_config.json"),
        "manuscript_repo": get_file_info("manuscript/corrected_final_manuscript.docx"),
        "manuscript_submission": get_file_info("final_faculty_remediation/manuscript/corrected_final_manuscript.docx"),
        "final_submission_zip": get_file_info("deliverables/RW_GUARD_FINAL_FACULTY_SUBMISSION.zip"),
        "final_submission_sha256_file": get_file_info("deliverables/RW_GUARD_FINAL_FACULTY_SUBMISSION.sha256")
    }

    # Verify matching hashes between repo and submission directory
    assert artifacts["primary_checkpoint_repo"]["sha256"] == artifacts["primary_checkpoint_submission"]["sha256"], "Primary checkpoint hash mismatch between repo and submission dir!"
    assert artifacts["config_repo"]["sha256"] == artifacts["config_submission"]["sha256"], "Config hash mismatch between repo and submission dir!"
    assert artifacts["manuscript_repo"]["sha256"] == artifacts["manuscript_submission"]["sha256"], "Manuscript hash mismatch between repo and submission dir!"

    # Read the sha256 file content to compare with actual zip sha256
    with open("deliverables/RW_GUARD_FINAL_FACULTY_SUBMISSION.sha256", "r") as f:
        recorded_zip_hash = f.read().split()[0].strip()

    assert recorded_zip_hash == artifacts["final_submission_zip"]["sha256"], f"Zip hash mismatch! Recorded: {recorded_zip_hash}, Actual: {artifacts['final_submission_zip']['sha256']}"

    summary = {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "repository_path": os.path.abspath(".").replace("\\", "/"),
        "submission_directory": os.path.abspath("final_faculty_remediation").replace("\\", "/"),
        "git_commit": git_commit,
        "git_branch": git_branch,
        "git_status_uncommitted_files_count": len([line for line in git_status.splitlines() if line.strip()]),
        "artifacts": artifacts
    }

    out_json = "independent_audit/submission_identification.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved: {out_json}")

    # Text report
    out_txt = "independent_audit/submission_frozen_manifest.txt"
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("RW-GUARD INDEPENDENT AUDIT: SUBMISSION IDENTIFICATION & FREEZE RECORD\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Audit Timestamp (UTC): {summary['timestamp_utc']}\n")
        f.write(f"Repository Root:       {summary['repository_path']}\n")
        f.write(f"Submission Directory:  {summary['submission_directory']}\n")
        f.write(f"Git Commit Hash:       {git_commit}\n")
        f.write(f"Git Branch:            {git_branch}\n\n")
        f.write("PRIMARY SUBMISSION ARTIFACTS:\n")
        f.write("-" * 80 + "\n")
        for k, v in artifacts.items():
            f.write(f"Artifact:   {k}\n")
            f.write(f"Path:       {v['path']}\n")
            f.write(f"Size:       {v['size_bytes']:,} bytes ({v['size_mb']} MB)\n")
            f.write(f"Timestamp:  {v['mtime_utc']}\n")
            f.write(f"SHA-256:    {v['sha256']}\n")
            f.write("-" * 80 + "\n")
    print(f"Saved: {out_txt}")

if __name__ == "__main__":
    main()
