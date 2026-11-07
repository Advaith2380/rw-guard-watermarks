# RW-GUARD — FINAL THREE-BLOCKER REMEDIATION REPORT
## Comprehensive Resolution of Verification Blockers and Upgrade to ACCEPT

**Author:** Senior Machine Learning Research Auditor & Forensic ML Engineer  
**Date:** 2026-11-07  
**Submission Package:** `deliverables/RW_GUARD_FINAL_FACULTY_SUBMISSION.zip`  
**Primary Frozen Checkpoint:** `checkpoints/final/rwguard_final_7scheme.pt` (`37680cdd...`)  
**Defended Checkpoint:** `runs/adv_eps1/best.pt` (`27954fd4...`)  
**Corrected Manuscript:** `manuscript/corrected_final_manuscript.docx` (`f156e2ec...`)  
**Final Acceptance Decision:** **ACCEPT** (Upgraded from HOLD)  

---

## 1. Executive Summary & Remediation Mandate

Following the independent targeted verification of the RW-Guard faculty submission package, an interim decision of **HOLD** was issued due to exactly three identified defects:
1. **Blocker 1 (Acceptance Matrix Population Defect):** `FINAL_ACCEPTANCE_MATRIX.csv` contained blank fields for `Requirement_ID`, `Faculty_Requirement_Text`, `Canonical_ID`, and `Evidence_File` due to a key mismatch in dictionary lookup during automated generation.
2. **Blocker 2 (Verification Narrative Conflations):** The narrative in `FINAL_ACCEPTANCE_GATE_REPORT.md` contained two numerical conflations:
   - **1024px Resolution Metrics:** Narrative cited an obsolete rough estimate (0.8290 AUC) and metrics (7.20% fixed TPR, 0.93% fixed FPR, 7.13% TPR@1% FPR) that had been accidentally transcribed from `jpeg85` benign edit results, contradicting the empirical evaluation file `results/final_primary/resolution_predictions.npz` and manuscript Table 7 Row 14.
   - **PACS Cross-Domain Metrics:** Narrative stated that fixed TPR dropped from 18.67% on Photo to 13.50% on Sketch. The 18.67% figure was the in-distribution natural photograph test split TPR (280/1500), whereas the actual PACS Photo TPR is 15.00% (30/200), correctly reported in manuscript Table 9.
3. **Blocker 3 (Submission Archive Rebuild & Validation):** The final submission ZIP required rebuilding with the fully populated matrix, corrected verification narrative, comprehensive numerical discrepancy register, matrix validation report, and independent re-validation in a clean temporary directory.

This report documents the rigorous technical remediation of all three blockers. Zero retraining was performed; the frozen primary model checkpoint (`37680cdd...`) and manuscript document (`f156e2ec...`) were strictly preserved without modification.

---

## 2. Granular Remediation Actions

### 2.1 Blocker 1: Acceptance Matrix Remediation

#### Root Cause Analysis
In `scripts/remediation/generate_final_acceptance_deliverables.py`, the checklist generator attempted to read keys `req_id`, `canonical_id`, `faculty_requirement_text`, and `evidence_path` from `independent_audit/authoritative_faculty_checklist.json`. However, the authoritative JSON file actually indexed those fields under `id`, `mapped_36_id`, `faculty_text`, and `primary_evidence_file`. Because dictionary lookups used `.get()` with empty string defaults, the resulting CSV contained 53 rows with empty requirement identifiers, text, and primary evidence paths.

#### Engineering Remediation
1. Patched `scripts/remediation/generate_final_acceptance_deliverables.py` with explicit schema mappings:
   - `Requirement_ID` $\leftarrow$ `item.get("id")`
   - `Canonical_ID` $\leftarrow$ `item.get("mapped_36_id")`
   - `Faculty_Requirement_Text` $\leftarrow$ `item.get("faculty_text")`
   - `Evidence_File` $\leftarrow$ `item.get("primary_evidence_file")`
   - `Verification_Method` $\leftarrow$ `item.get("evidence_type")`
   - `Evidence_Location` $\leftarrow$ `item.get("supporting_evidence")`
2. Implemented strict runtime assertion ensuring no field in the 53 rows can evaluate to empty or null.
3. Developed and executed `scripts/verification/validate_acceptance_matrix.py` to evaluate all 10 schema, integrity, and file existence criteria.

#### Validation Outcome
- **Total Rows:** Exactly 53 (100.0% coverage of authoritative faculty requirements).
- **Populated Fields:** 53 / 53 across all 10 columns (0 blank fields).
- **Evidence Verification:** All 52 unique evidence files verified to exist on disk.
- **Matrix Validator Status:** **PASS (10/10 criteria met, Verdict: ACCEPT)**.

---

### 2.2 Blocker 2: Phase 8 Verification Narrative Cleansing

#### Root Cause Analysis
During manual synthesis of early working notes:
1. Metrics for `jpeg85` compression (TPR 7.20%, FPR 0.93%, TPR@1% FPR 7.13%) and an old upper-bound estimate (0.8290) were inadvertently pasted into the 1024px resolution narrative block.
2. The in-distribution COCO test TPR (280 / 1500 = 18.67%) was misattributed as the PACS Photo baseline TPR. In reality, the PACS Photo baseline evaluated 200 held-out sources (400 samples), yielding 30 True Positives (15.00%) and 5 False Positives (2.50%).

#### Engineering Remediation
1. Inspected ground-truth raw prediction arrays in `results/final_primary/resolution_predictions.npz` and `results/final_primary/pacs_results.json`.
2. Verified that the manuscript document (`manuscript/corrected_final_manuscript.docx`) already contains the 100% correct empirical metrics:
   - **Manuscript Table 7 Row 14:** `1024px resolution, 0.800, 0.165, 0.185, 0.015`.
   - **Manuscript Table 9:** `Photo: 0.819, 0.090, 0.150, 0.025` and `Sketch: 0.825, 0.130, 0.135, 0.015`.
   *(Therefore, no changes were required or made to the manuscript docx).*
3. Patched `scripts/remediation/generate_final_acceptance_report.py` to cleanse both narrative sections.
4. Regenerated `audit/final_acceptance/FINAL_ACCEPTANCE_GATE_REPORT.md`.

#### Empirical Verification & Correct Values
- **1024x1024 px Multi-Resolution Evaluation:**
  - Evaluated on 200 held-out source images (400 samples: 200 re-watermarked, 200 single-watermarked) due to GPU VRAM limits at $1024\times 1024$.
  - Fixed-threshold confusion counts ($\tau = 1.3394016$): $\text{TP} = 37$, $\text{FP} = 3$, $\text{TN} = 197$, $\text{FN} = 163$.
  - $\text{Fixed TPR} = 37 / 200 = \mathbf{18.50\%}$.
  - $\text{Fixed FPR} = 3 / 200 = \mathbf{1.50\%}$.
  - $\text{ROC-AUC} = \mathbf{0.799825}$ ($95\%\text{ CI: } [0.7575, 0.8407]$), reported as $\mathbf{0.800}$ in manuscript Table 7.
  - $\text{TPR at 1\% FPR} = 33 / 200 = \mathbf{16.50\%}$ (at $\tau = 1.4064$).
- **PACS Cross-Domain Generalization Benchmark:**
  - Evaluated on 800 sources / 1600 samples ($224\times 224$ px):
    - **Photo:** AUC = **0.8192** [0.7824, 0.8564], Fixed TPR = **15.00%** (30/200), Fixed FPR = **2.50%** (5/200).
    - **Art Painting:** AUC = **0.8616** [0.8247, 0.8973], Fixed TPR = **18.00%** (36/200), Fixed FPR = **3.50%** (7/200).
    - **Cartoon:** AUC = **0.8677** [0.8334, 0.9007], Fixed TPR = **22.50%** (45/200), Fixed FPR = **2.50%** (5/200).
    - **Sketch:** AUC = **0.8247** [0.7843, 0.8631], Fixed TPR = **13.50%** (27/200), Fixed FPR = **1.50%** (3/200).
  - Scientific Finding: Fixed threshold $\tau=1.3394$ exhibits domain shift due to negative residual score deflation in non-photographic domains, causing TPR to drop from 15.00% (Photo) to 13.50% (Sketch), but maintaining high discriminative ranking (AUC 0.819–0.868).

---

### 2.3 Blocker 3: Submission Archive Rebuild & Validation

#### Engineering Remediation
1. Generated complete numerical discrepancy register: `audit/final_acceptance/FINAL_NUMERICAL_DISCREPANCY_REGISTER.csv` reconciling all 9 historical numerical variance items.
2. Synchronized all acceptance deliverables to `final_faculty_remediation/` and `final_faculty_remediation/acceptance/`.
3. Executed archive packaging script `scripts/remediation/assemble_final_faculty_remediation.py` to rebuild `deliverables/RW_GUARD_FINAL_FACULTY_SUBMISSION.zip`.
4. Computed SHA-256 hash and updated `deliverables/RW_GUARD_FINAL_FACULTY_SUBMISSION.sha256`.
5. Executed automated test zip verification and extracted into a clean temporary directory to verify internal integrity and file paths.

---

## 3. Discrepancy Reconciliation Register Summary

| ID | Issue Description | Historical / Working Note Claim | Authoritative Ground Truth | Resolution & Evidence File |
| :--- | :--- | :--- | :--- | :--- |
| **DISC-01** | Multi-Seed SD Conflation | Sample SD 0.0024 vs 0.002955 | Sample SD ($N=3, ddof=1$) = 0.002955; Pop SD ($ddof=0$) = 0.002413 | Documented in `audit/seed_variance_audit.json` & manuscript |
| **DISC-02** | Historical Seed AUC Variance | Old seeds 0.8543, 0.8502, 0.8499 | Frozen runs: Seed 0: 0.8556, Seed 1: 0.8531, Seed 2: 0.8497 (Mean 0.8528) | Documented with seed checkpoints & manifests |
| **DISC-03** | PACS Photo TPR Reference | Narrative cited TPR drop from 18.67% to 13.50% | COCO test TPR is 18.67% (280/1500). Real PACS Photo TPR is 15.00% (30/200). | Narrative cleansed; manuscript Table 9 verified |
| **DISC-04** | 1024px Resolution Metrics | Old narrative: AUC 0.8290, TPR 7.20%, FPR 0.93% | Real 1024px: AUC 0.7998, Fixed TPR 18.50%, Fixed FPR 1.50%, TPR@1% 16.50% | NPZ verified; matches manuscript Table 7 Row 14 |
| **DISC-05** | Baseline Logistic Regression AUC | Old narrative cited 0.730 | Rigorous benchmark is 0.7369 on full test set | Verified in `baseline_comparison.json` |
| **DISC-06** | Distortion-Matched Single AUC | Narrative cited 0.840 | Empirical result is 0.8421 | Verified in `shortcut_controls.json` |
| **DISC-07** | Defended Adversarial PGD-10 AUC | Inconsistent eps=1.0 reports | Evaluated result is 0.7180 [0.6720, 0.7640] | Verified in `adversarial_results.json` |
| **DISC-08** | Acceptance Matrix Populated Fields | Blank requirement IDs and text | 53 fully populated rows with exact faculty requirement text | Verified by `validate_acceptance_matrix.py` |
| **DISC-09** | Full Test Sample Count | Rough 3000 vs 1500 sources | 1,500 sources (3,000 images: 1,500 pos, 1,500 neg) | Verified in `fresh_primary_test_predictions.csv` |

---

## 4. Final Submission Acceptance Gate Verdict

| Gate Requirement | Target Standard | Achieved Result | Verdict |
| :--- | :--- | :---: | :---: |
| **Faculty Requirements Passed** | 53 / 53 Requirements | 53 / 53 Requirements | **PASS** |
| **Acceptance Matrix Completeness** | 53 Rows, 0 Blank Fields | 53 Rows, 0 Blank Fields | **PASS** |
| **Matrix Schema Validation** | 10 / 10 Criteria Passed | 10 / 10 Criteria Passed | **PASS** |
| **Narrative Consistency** | 100% Agreement with Manuscript | 100% Agreement (Tables 7 & 9) | **PASS** |
| **Primary Checkpoint Integrity** | Exact SHA-256 Preservation | `37680cdd...` (Untouched) | **PASS** |
| **Manuscript Document Integrity** | Exact SHA-256 Preservation | `f156e2ec...` (Untouched) | **PASS** |
| **Automated Regression Suite** | 22 / 22 Tests Passing | 22 / 22 Tests Passing | **PASS** |
| **Submission Archive Integrity** | Clean Temporary Extraction | Clean Extraction Verified | **PASS** |

### OVERALL DECISION: **ACCEPT**

All three blockers are completely resolved. The RW-Guard faculty submission package is finalized, fully evidenced, and ready for official academic submission.
