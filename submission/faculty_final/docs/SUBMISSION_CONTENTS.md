# Faculty Submission Package Inventory

This document details the exact contents, directory layout, and file checksums comprising the authoritative RW-Guard Faculty Submission Package (`submission/faculty_final/` and `deliverables/RW_GUARD_FINAL_FACULTY_SUBMISSION.zip`).

---

## 1. Primary Deliverables

| Deliverable Item | Repository Path | File Size | Cryptographic SHA-256 | Description |
|:---|:---|:---:|:---|:---|
| **Final Manuscript (Word)** | `manuscript/corrected_final_manuscript.docx` | ~3.08 MB | Reconciled with all 53 review points | Complete formatted DOCX article with embedded tables, figures, algorithms, and references |
| **Final Manuscript (PDF)** | `manuscript/corrected_final_manuscript.pdf` | ~1.05 MB | Generated via Microsoft Word | Publication-ready PDF document |
| **Primary Model Checkpoint** | `checkpoints/final/rwguard_final_7scheme.pt` | 9,890,147 B | `37680cdd2d4e5100cbb8aa1642e78b9bb3df373e79efd9f8512f89e15d0c0573` | Frozen primary 7-scheme ForensicNet weights (2.47M parameters) |
| **Defended Checkpoint** | `runs/adv_eps1/best.pt` | 9,890,147 B | `27954fd43360830d76fa107036567e9486844fa85d6a058c84d438b2e6caefed` | Adversarially trained model checkpoint ($\epsilon=1/255$) |
| **Model Configuration** | `configs/final_model_config.json` | ~1.2 KB | Verified JSON structure | Complete hyperparameter, architecture, and scheme registry |
| **Submission Archive** | `deliverables/RW_GUARD_FINAL_FACULTY_SUBMISSION.zip` | ~12.6 MB | Bit-verified ZIP archive | Standalone faculty submission archive containing code, checkpoints, results, and docs |
| **ZIP Checksum File** | `deliverables/RW_GUARD_FINAL_FACULTY_SUBMISSION.sha256` | ~100 B | Plaintext hash | Cryptographic SHA-256 hash of the submission ZIP archive |

---

## 2. Comprehensive Documentation (`docs/`)

- `docs/PROJECT_OVERVIEW.md`: Research problem, threat model, contributions, and performance summary.
- `docs/ARCHITECTURE.md`: Detailed ForensicNet layer dimensions, fixed SRM high-pass filter bank, dual global pooling head, and Algorithm 2.
- `docs/DATASET_AND_SPLITS.md`: Dataset provenance (MS-COCO, PACS), source-level partitioning, seven watermarking schemes, and Algorithm 1.
- `docs/EXPERIMENT_PROTOCOLS.md`: Complete specifications for all eight experimental axes.
- `docs/STATISTICAL_METHODS.md`: Grouped bootstrapping ($B=2,000$), Wilson intervals, threshold calibration, and paired hypothesis tests.
- `docs/RESULTS_REFERENCE.md`: Direct mapping between every manuscript table/figure and its underlying raw result file.
- `docs/REPRODUCIBILITY.md`: Environment setup, pinned dependencies, checkpoint verification, and execution commands.
- `docs/RELEASE_NOTES.md`: Version notes, commit references, and remediation changelog.
- `docs/REFERENCE_VERIFICATION_REPORT.md`: Comprehensive audit of references [1] through [28].
- `docs/FACULTY_REQUIREMENT_TRACEABILITY.md`: Detailed compliance report across all 53 requirements.
- `docs/SUBMISSION_CONTENTS.md`: Complete submission manifest and inventory (this document).
- `docs/LIMITATIONS_AND_THREAT_MODEL.md`: Formal threat model, operational scope, and prohibited scientific claims.
- `docs/faculty_requirement_matrix.csv`: Fully populated CSV matrix with 12 required columns across all 53 review items.
- `docs/faculty_requirement_matrix.json`: Machine-readable JSON version of the faculty requirement matrix.

---

## 3. Authoritative Audit & Results Evidence

- `results/final_primary/FINAL_RESOLUTION_METRICS_VERIFIED.csv`: Audited metrics across all five resolutions (128, 256, 384, 512, 1024 px).
- `results/final_primary/resolution_predictions.npz`: Raw prediction arrays for all five resolutions.
- `audit/pacs_calibration_results.json`: Cross-domain PACS metrics, ECE, Brier score, and calibration data.
- `results/statistics/seed_statistics.json`: Multi-seed evaluation statistics for Protocol A (500 sources) and Protocol B (1,500 sources).
- `audit/trustmark_evaluation_results.json`: TrustMark zero-shot and supervised domain adaptation records.
- `audit/stegastamp_evaluation_results.json`: StegaStamp zero-shot evaluation records.
- `audit/outcome_stratification_results.json`: Attack-outcome classification records across all 500 collisions.
- `audit/shortcut_baseline_results.json`: Logistic Regression and Random Forest baseline results.
- `audit/matched_controls_results.json`: Distortion-matched and noise-matched single watermark control records.
- `audit/remediation/adversarial_evaluation_results.json`: PGD-10 adversarial robustness metrics.

---

## 4. Verification & Testing Infrastructure

- `scripts/verify_faculty_submission.py`: Master automated verification script auditing checkpoints, configs, tables, abstract, matrix, and ZIP.
- `scripts/verification/verify_final_resolution_metrics.py`: Independent resolution metrics verification script.
- `scripts/verification/validate_acceptance_matrix.py`: Acceptance matrix validation script.
- `tests/test_outcomes.py`: Regression tests for attack-outcome classification.
- `tests/test_integration_faculty.py`: Faculty compliance integration tests.
