"""
Phase 3: Collect Raw Evidence and Generate Cryptographic Evidence Manifest
Crawls all raw evidence files across categories, verifies existence on disk,
computes SHA-256 checksums, and outputs independent_audit/evidence_manifest_sha256.csv.
"""

import os
import sys
import hashlib
import csv
from datetime import datetime, timezone

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def get_file_metadata(category, filepath, description):
    abs_path = os.path.abspath(filepath).replace("\\", "/")
    if os.path.exists(filepath):
        stat = os.stat(filepath)
        sha256 = compute_sha256(filepath)
        return {
            "category": category,
            "description": description,
            "relative_path": filepath.replace("\\", "/"),
            "absolute_path": abs_path,
            "status": "EXISTS",
            "size_bytes": stat.st_size,
            "size_kb": round(stat.st_size / 1024, 2),
            "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            "sha256": sha256
        }
    else:
        return {
            "category": category,
            "description": description,
            "relative_path": filepath.replace("\\", "/"),
            "absolute_path": abs_path,
            "status": "MISSING",
            "size_bytes": 0,
            "size_kb": 0.0,
            "mtime_utc": "N/A",
            "sha256": "N/A"
        }

def collect_evidence():
    evidence_items = [
        # 1. Dataset manifests & source identifiers
        ("Dataset Manifests", "data/manifests/master_source_manifest.csv", "Master source manifest (5,000 COCO source images with hashes)"),
        ("Dataset Manifests", "data/manifests/derived_sample_manifest.csv", "Derived test sample manifest (3,000 samples mapped to source IDs)"),
        ("Dataset Manifests", "data/manifests/split_integrity_report.json", "Source split partition and zero-leakage report"),
        ("Dataset Manifests", "final_faculty_remediation/manifests/master_source_manifest.csv", "Submission copy of master source manifest"),
        ("Dataset Manifests", "final_faculty_remediation/manifests/derived_sample_manifest.csv", "Submission copy of derived sample manifest"),
        ("Dataset Manifests", "final_faculty_remediation/manifests/split_integrity_report.json", "Submission copy of split integrity report"),

        # 2. Checkpoints & model configs
        ("Checkpoints & Configs", "checkpoints/final/rwguard_final_7scheme.pt", "Authoritative frozen primary 7-scheme checkpoint"),
        ("Checkpoints & Configs", "checkpoints/final/final_model_config.json", "Authoritative frozen primary model config with threshold"),
        ("Checkpoints & Configs", "final_faculty_remediation/checkpoints/primary_checkpoint.pt", "Submission package primary checkpoint"),
        ("Checkpoints & Configs", "final_faculty_remediation/checkpoints/checkpoint_metadata.json", "Submission package checkpoint metadata"),
        ("Checkpoints & Configs", "final_faculty_remediation/configs/final_model_config.json", "Submission package model config"),
        ("Checkpoints & Configs", "scheme_sets.json", "Definition of 7 watermarking schemes"),
        ("Checkpoints & Configs", "D:/projects/rewm-guard/runs/seed0/best.pt", "Provenance training checkpoint (Seed 0, epoch 14)"),
        ("Checkpoints & Configs", "D:/projects/rewm-guard/runs/adv_eps1/best.pt", "Isolated adversarially-trained checkpoint"),

        # 3. Raw test predictions, labels & source IDs
        ("Raw Predictions", "results/final_primary/fresh_predictions.csv", "Fresh GPU forward-pass test predictions (3,000 rows with source IDs)"),
        ("Raw Predictions", "results/final_primary/fresh_predictions.npz", "Fresh GPU test prediction arrays (scores, labels, source_ids)"),
        ("Raw Predictions", "final_faculty_remediation/predictions/fresh_primary_test_predictions.csv", "Submission copy of fresh predictions CSV"),
        ("Raw Predictions", "final_faculty_remediation/predictions/fresh_primary_test_predictions.npz", "Submission copy of fresh predictions NPZ"),

        # 4. Validation predictions & threshold calibration
        ("Threshold & Calibration", "results/statistics/threshold_validation_test_analysis.json", "Validation vs test score distributions, KS test, and tail analysis"),
        ("Threshold & Calibration", "audit/fpr_discrepancy_investigation.json", "Detailed tail density and FPR discrepancy investigation"),

        # 5. Ownership recovery records
        ("Ownership Attacks", "results/attack_outcomes/per_attack_recovery.csv", "Row-level recovery records for 500 double-watermark attacks"),
        ("Ownership Attacks", "results/attack_outcomes/recovery_criteria.json", "Codified bit-accuracy recovery threshold criteria (>0.75)"),
        ("Ownership Attacks", "results/attack_outcomes/category_counts.json", "Category counts and percentages for 4 outcome categories"),
        ("Ownership Attacks", "results/attack_outcomes/dual_survival_reconciliation.json", "Reconciliation of 88.7% prototype vs 85.0% verified"),
        ("Ownership Attacks", "results/attack_outcomes/category_detection_metrics.json", "Category-specific detection rates, AUCs, and scores"),
        ("Ownership Attacks", "final_faculty_remediation/results/ownership_attack_results.json", "Submission copy of ownership attack results"),

        # 6. Neural watermarker records
        ("Neural Watermarkers", "results/neural_generalization/trustmark_zero_shot.json", "TrustMark zero-shot evaluation under stratified controls"),
        ("results/neural_generalization/trustmark_adaptation.json", "results/neural_generalization/trustmark_adaptation.json", "TrustMark supervised adaptation with 15% data"),
        ("Neural Watermarkers", "results/neural_generalization/stegastamp_zero_shot.json", "StegaStamp single vs double zero-shot detection results"),
        ("Neural Watermarkers", "results/neural_generalization/historical_protocol_reconciliation.json", "Historical TrustMark protocol reconciliation"),
        ("Neural Watermarkers", "final_faculty_remediation/results/neural_watermarker_results.json", "Submission copy of neural generalization results"),

        # 7. Shortcut controls & feature data
        ("Shortcut Controls", "results/shortcut_controls/distortion_matched_single.json", "Distortion-matched single-watermark control evaluation"),
        ("Shortcut Controls", "results/shortcut_controls/nonlinear_baselines.json", "Logistic Regression & Random Forest baseline results"),
        ("Shortcut Controls", "results/shortcut_controls/matched_noise.json", "MSE-matched Gaussian noise control evaluation"),
        ("Shortcut Controls", "results/shortcut_controls/paired_comparisons.json", "Paired bootstrap difference testing vs shallow baselines"),
        ("Shortcut Controls", "final_faculty_remediation/results/shortcut_controls.json", "Submission copy of shortcut controls results"),

        # 8. PACS, resolution, benign & adversarial results
        ("Secondary Evaluations", "results/final_primary/benign_transformations.json", "11 benign post-processing operations evaluation"),
        ("Secondary Evaluations", "results/final_primary/resolution_results.json", "Multi-resolution evaluation (128px to 1024px)"),
        ("Secondary Evaluations", "results/final_primary/pacs_results.json", "PACS 4-domain cross-domain evaluation"),
        ("Secondary Evaluations", "results/final_primary/adversarial_results.json", "White-box PGD-10 and FGSM adversarial evaluation"),
        ("Secondary Evaluations", "results/final_primary/hold_one_scheme_out.json", "Hold-one-scheme-out generalization results"),
        ("Secondary Evaluations", "results/final_primary/multi_seed_results.json", "Multi-seed training stability evaluation (Seeds 0, 1, 2)"),
        ("Secondary Evaluations", "final_faculty_remediation/results/robustness_results.json", "Submission copy of benign robustness results"),
        ("Secondary Evaluations", "final_faculty_remediation/results/pacs_results.json", "Submission copy of PACS results"),
        ("Secondary Evaluations", "final_faculty_remediation/results/adversarial_results.json", "Submission copy of adversarial results"),
        ("Secondary Evaluations", "final_faculty_remediation/results/hold_one_scheme_out_results.json", "Submission copy of hold-one-out results"),
        ("Secondary Evaluations", "final_faculty_remediation/results/multi_seed_results.json", "Submission copy of multi-seed results"),

        # 9. Statistical validation & bootstrap data
        ("Statistical Validation", "results/statistics/consolidated_statistical_results.json", "Consolidated 34-condition statistical table with 95% CIs"),
        ("Statistical Validation", "results/statistics/consolidated_statistical_results.csv", "CSV master table of all evaluated conditions"),
        ("Statistical Validation", "results/statistics/bootstrap_diagnostics.json", "Bootstrap resampling diagnostics (B=2,000, source-grouped)"),
        ("Statistical Validation", "results/statistics/seed_statistics.json", "Multi-seed variance and degrees-of-freedom documentation"),
        ("Statistical Validation", "results/statistics/paired_baseline_comparisons.json", "Paired bootstrap comparisons against baselines"),
        ("Statistical Validation", "audit/final/FINAL_STATISTICAL_CORRECTION_RESULTS.json", "Audited statistical correction records"),
        ("Statistical Validation", "final_faculty_remediation/FINAL_STATISTICAL_CORRECTION_RESULTS.json", "Submission copy of statistical corrections"),
        ("Statistical Validation", "final_faculty_remediation/results/consolidated_statistical_results.json", "Submission copy of consolidated statistical results"),

        # 10. Test suite & verification logs
        ("Test Suite & Logs", "audit/final/test_results.txt", "Automated regression test suite raw console output (22 tests)"),
        ("Test Suite & Logs", "audit/final/test_results.json", "Automated regression test suite JSON output"),
        ("Test Suite & Logs", "audit/final/FINAL_EXECUTION_LOG.txt", "Execution log of 12-stage verification suite"),
        ("Test Suite & Logs", "audit/final/FINAL_EXECUTION_SUMMARY.json", "Execution summary of 12-stage verification suite"),
        ("Test Suite & Logs", "final_faculty_remediation/tests/final_regression_test_results.txt", "Submission copy of test results TXT"),
        ("Test Suite & Logs", "final_faculty_remediation/tests/final_regression_test_results.json", "Submission copy of test results JSON"),
        ("Test Suite & Logs", "final_faculty_remediation/logs/FINAL_EXECUTION_LOG.txt", "Submission copy of execution log"),
        ("Test Suite & Logs", "final_faculty_remediation/logs/FINAL_EXECUTION_SUMMARY.json", "Submission copy of execution summary"),

        # 11. Manuscript & documentation
        ("Manuscript & Reports", "manuscript/corrected_final_manuscript.docx", "Authoritative corrected manuscript Word document"),
        ("Manuscript & Reports", "final_faculty_remediation/manuscript/corrected_final_manuscript.docx", "Submission copy of corrected manuscript"),
        ("Manuscript & Reports", "final_faculty_remediation/FINAL_TECHNICAL_AND_FACULTY_REPORT.md", "Comprehensive technical audit and remediation report"),
        ("Manuscript & Reports", "final_faculty_remediation/FINAL_PREVIOUS_VS_NEW_VS_FACULTY_COMPARISON.csv", "41-metric comparison register"),
        ("Manuscript & Reports", "final_faculty_remediation/FINAL_FACULTY_COMPLIANCE_MATRIX.csv", "36-requirement compliance matrix CSV"),
        ("Manuscript & Reports", "final_faculty_remediation/FINAL_FACULTY_COMPLIANCE_MATRIX.json", "36-requirement compliance matrix JSON"),
        ("Manuscript & Reports", "final_faculty_remediation/FINAL_DISCREPANCY_RESOLUTION_REGISTER.md", "10 discrepancy resolution register"),
        ("Manuscript & Reports", "final_faculty_remediation/FINAL_SCIENTIFIC_CLAIM_AUDIT.md", "Scientific claim audit markdown"),
        ("Manuscript & Reports", "final_faculty_remediation/FINAL_INDEPENDENT_VERIFICATION_REPORT.md", "Independent verification synthesis report"),
        ("Manuscript & Reports", "final_faculty_remediation/FINAL_MANUSCRIPT_VERIFICATION.md", "22-point manuscript verification report"),
        ("Manuscript & Reports", "final_faculty_remediation/FINAL_PACKAGE_INTEGRITY_REPORT.txt", "Submission archive integrity report"),
        ("Manuscript & Reports", "final_faculty_remediation/README_FINAL.md", "Top-level submission instructions"),

        # 12. Deliverables & ZIP
        ("Submission Deliverables", "deliverables/RW_GUARD_FINAL_FACULTY_SUBMISSION.zip", "Final portable faculty submission ZIP archive"),
        ("Submission Deliverables", "deliverables/RW_GUARD_FINAL_FACULTY_SUBMISSION.sha256", "Cryptographic SHA-256 hash manifest file for submission ZIP")
    ]

    records = []
    missing_count = 0
    exists_count = 0

    for cat, path, desc in evidence_items:
        meta = get_file_metadata(cat, path, desc)
        records.append(meta)
        if meta["status"] == "EXISTS":
            exists_count += 1
        else:
            missing_count += 1
            print(f"[MISSING] {path} ({desc})")

    print(f"\nEvidence collection complete: {exists_count} files verified present on disk, {missing_count} missing.")

    # Write CSV
    out_csv = "independent_audit/evidence_manifest_sha256.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "category", "description", "relative_path", "status", "size_bytes", "size_kb", "mtime_utc", "sha256", "absolute_path"
        ])
        writer.writeheader()
        writer.writerows(records)
    print(f"Evidence manifest written to: {out_csv}")

if __name__ == "__main__":
    collect_evidence()
