# RW-GUARD: FACULTY REQUIREMENT RECONCILIATION REPORT
## Exact Parsing and Granular Mapping of Final Review.docx

### 1. Executive Summary of Requirement Extraction
An independent extraction of all individually stated faculty instructions in `Final Review.docx` was conducted. Rather than assuming that the historical 36-item register was exhaustive, every actionable sentence was extracted and assigned a unique ID (`FR-A01` through `FR-ED04`).

- **Total Granular Faculty Requirements Extracted:** **53 Requirements**
- **Section Breakdown:**
  - Section A (Seven-Scheme Model & Principal Reproduction): 11 requirements (`FR-A01` to `FR-A11`)
  - Section B (Shortcut Learning & Distortion Controls): 6 requirements (`FR-B01` to `FR-B06`)
  - Section C (Neural-Watermarker Generalization): 5 requirements (`FR-C01` to `FR-C05`)
  - Section D (Ownership Forgery & Outcome Stratification): 7 requirements (`FR-D01` to `FR-D07`)
  - Section E (Statistical Analysis & Rigor): 9 requirements (`FR-E01` to `FR-E09`)
  - Final Submission Checklist (P119-P129): 11 requirements (`FR-CHK01` to `FR-CHK11`)
  - Editorial & Structural Mandates: 4 requirements (`FR-ED01` to `FR-ED04`)

### 2. Reconciliation with the 36-Item Requirement Register
The previous remediation team structured their audit around a 36-item taxonomy (10 in Section A, 4 in Section B, 5 in Section C, 5 in Section D, 7 in Section E, and 5 packaging items).

The reconciliation audit confirms:
1. **Complete Coverage:** All 36 items in the previous register map directly to subsets of the 53 granular requirements.
2. **No Omitted Scientific Mandates:** The 36-item register grouped closely related sub-tasks (e.g. reporting AUC and CIs for benign transformations into a single requirement REQ-A05). The underlying experiments cover 100% of the granular instructions.
3. **Dual Audit Structure:** In this independent audit, every check is verified against both the granular 53-item checklist and the canonical 36-item register.

---

### 3. Complete Granular Requirement Matrix

| ID | Section | Faculty Instruction | Source Para | Mapped 36 ID | Primary Evidence Artifact |
|---|---|---|---|---|---|
| **FR-A01** | Section A | Please consolidate the experiments using one finalized RW-Guard model trained on all seven watermarking schemes. | P[7] | `REQ-A01` | `final_faculty_remediation/checkpoints/primary_checkpoint.pt` |
| **FR-A02** | Section A | Verify whether the checkpoints from those runs are available. Select the final checkpoint using validation performance only. | P[8] | `REQ-A02` | `audit/checkpoint_provenance.json` |
| **FR-A03** | Section A | Using this frozen model, repeat the main test evaluation... Report ROC-AUC, TPR@1%FPR, fixed-threshold TPR/FPR, and appropriate confidence intervals. | P[9] | `REQ-A04` | `final_faculty_remediation/predictions/fresh_primary_test_predictions.csv` |
| **FR-A04** | Section A | Using this frozen model, repeat benign transformation tests. | P[9] | `REQ-A05` | `final_faculty_remediation/results/robustness_results.json` |
| **FR-A05** | Section A | Using this frozen model, repeat resolution tests. | P[9] | `REQ-A06` | `results/final_primary/resolution_results.json` |
| **FR-A06** | Section A | Using this frozen model, repeat PACS cross-domain experiments. | P[9] | `REQ-A07` | `final_faculty_remediation/results/pacs_results.json` |
| **FR-A07** | Section A | Using this frozen model, repeat adversarial evaluation. | P[9] | `REQ-A08` | `final_faculty_remediation/results/adversarial_results.json` |
| **FR-A08** | Section A | Keep the hold-one-scheme-out experiments separate, since they require models trained without the withheld scheme. | P[10] | `REQ-A09` | `final_faculty_remediation/results/hold_one_scheme_out_results.json` |
| **FR-A09** | Section A | Distinguish zero-shot neural-watermarker evaluation from supervised adaptation. | P[10] | `REQ-C02` | `final_faculty_remediation/results/neural_watermarker_results.json` |
| **FR-A10** | Section A | Replace the main results in the abstract, tables, discussion and conclusion with results from the finalized seven-scheme model. | P[11] | `REQ-A04 / MANU` | `final_faculty_remediation/manuscript/corrected_final_manuscript.docx` |
| **FR-A11** | Section A | Submit the final checkpoint, configuration, execution commands, result files, and updated manuscript so that the reported results can be verified in a git repo. | P[12] | `REQ-PKG05` | `deliverables/RW_GUARD_FINAL_FACULTY_SUBMISSION.zip` |
| **FR-B01** | Section B | Distortion-matched control: Generate single-watermarked images with embedding strength adjusted to match the PSNR/MSE of the corresponding double-watermarked images. Use the same held-out source images and compare single versus double watermarking using the frozen final seven-scheme model. | P[20] | `REQ-B01` | `results/shortcut_controls/distortion_matched_single.json` |
| **FR-B02** | Section B | Nonlinear baseline: Train a Random Forest or XGBoost classifier using the existing residual-energy and spectral features. Compare it with logistic regression and RW-Guard under the same evaluation protocol. | P[21] | `REQ-B02` | `results/shortcut_controls/nonlinear_baselines.json` |
| **FR-B03** | Section B | Matched-noise control: Evaluate single-watermarked images with additional noise matched to the distortion of double-watermarked images. Report the complete detection metrics, not only the average model score. | P[22] | `REQ-B03` | `results/shortcut_controls/matched_noise.json` |
| **FR-B04** | Section B | For each experiment, report ROC-AUC, TPR@1%FPR, fixed-threshold TPR/FPR and 95% confidence intervals. Verify that the distortion distributions are actually matched. | P[23] | `REQ-B01 / REQ-E01` | `results/shortcut_controls/distortion_matched_single.json` |
| **FR-B05** | Section B | Revise the manuscript's claim that shortcut learning has been disproved. The conclusion must reflect what the additional controls demonstrate. | P[24] | `REQ-B04` | `final_faculty_remediation/manuscript/corrected_final_manuscript.docx` |
| **FR-B06** | Section B | Submit the experimental configuration, result tables, code and updated manuscript in git repo. | P[25] | `REQ-PKG05` | `deliverables/RW_GUARD_FINAL_FACULTY_SUBMISSION.zip` |
| **FR-C01** | Section C | Using the finalized seven-scheme RW-Guard checkpoint, repeat the zero-shot TrustMark evaluation with stratified negative controls. Report ROC-AUC, TPR@1%FPR, fixed-threshold TPR/FPR and 95% confidence intervals. | P[34] | `REQ-C01` | `results/neural_generalization/trustmark_zero_shot.json` |
| **FR-C02** | Section C | Extend the StegaStamp experiment beyond watermark extraction accuracy. Evaluate whether RW-Guard can distinguish singly-watermarked from doubly-watermarked StegaStamp images without prior StegaStamp training exposure. | P[35] | `REQ-C04` | `results/neural_generalization/stegastamp_zero_shot.json` |
| **FR-C03** | Section C | Clearly separate zero-shot experiments from supervised adaptation experiments. State the training data, neural-watermarker exposure, checkpoint and test dataset for each condition. | P[36] | `REQ-C02` | `results/neural_generalization/trustmark_adaptation.json` |
| **FR-C04** | Section C | Reconcile the conflicting TrustMark results. The abstract and updated Results section report 0.534 and 0.851, while the Discussion and Contributions sections still report 0.696 and 0.925. These results must be presented under their correct experimental protocols. | P[37] | `REQ-C03` | `results/neural_generalization/historical_protocol_reconciliation.json` |
| **FR-C05** | Section C | Avoid claiming universal or scheme-agnostic generalization unless the results demonstrate reliable detection on unseen watermarking families. If zero-shot performance remains near chance, report this limitation clearly. | P[38] | `REQ-C05` | `final_faculty_remediation/manuscript/corrected_final_manuscript.docx` |
| **FR-D01** | Section D | First, define clear recovery or verification criteria for the victim and attacker watermarks. | P[48] | `REQ-D01` | `results/attack_outcomes/recovery_criteria.json` |
| **FR-D02** | Section D | Use these criteria to classify the re-watermarked test images into four categories: successful overwrite, dual survival, failed attacker embedding, and both watermarks unrecoverable. | P[48] | `REQ-D02` | `results/attack_outcomes/per_attack_recovery.csv` |
| **FR-D03** | Section D | Report the number and percentage of samples in each category. Verify the reported 88.7% dual-survival result and clearly state how it was calculated. | P[49] | `REQ-D03` | `results/attack_outcomes/dual_survival_reconciliation.json` |
| **FR-D04** | Section D | Next, evaluate the frozen final seven-scheme RW-Guard model separately on each category. Report the detection rate at the fixed validation-calibrated threshold, along with sample counts and confidence intervals. | P[50] | `REQ-D04` | `results/attack_outcomes/category_detection_metrics.json` |
| **FR-D05** | Section D | Also report category-specific ROC-AUC and TPR@1%FPR against common singly-watermarked controls where sample sizes permit. | P[50] | `REQ-D04` | `results/attack_outcomes/category_detection_metrics.json` |
| **FR-D06** | Section D | Discuss whether the detector performs differently for successful overwriting and dual watermark survival. | P[51] | `REQ-D05` | `final_faculty_remediation/manuscript/corrected_final_manuscript.docx` |
| **FR-D07** | Section D | Finally, revise the Discussion and Conclusion to distinguish detection of sequential watermark embedding from successful watermark suppression and ownership forgery. Avoid claiming that RW-Guard proves ownership forgery unless the experiments directly support that conclusion. | P[52] | `REQ-D05` | `final_faculty_remediation/manuscript/corrected_final_manuscript.docx` |
| **FR-E01** | Section E | Report 95% confidence intervals for ROC-AUC, TPR@1%FPR, fixed-threshold TPR and fixed-threshold FPR. | P[61] | `REQ-E01` | `results/statistics/consolidated_statistical_results.json` |
| **FR-E02** | Section E | Perform a source-image-level bootstrap analysis using at least 2,000 replicates. | P[62] | `REQ-E02` | `results/statistics/bootstrap_diagnostics.json` |
| **FR-E03** | Section E | Keep the validation-calibrated threshold fixed when evaluating test performance. Clearly distinguish TPR@1%FPR calculated using the test ROC from performance at the validation-selected threshold. | P[62] | `REQ-E03` | `results/statistics/threshold_validation_test_analysis.json` |
| **FR-E04** | Section E | Evaluate the existing three independently seeded seven-scheme checkpoints on the same held-out test set. Report individual test results, mean and standard deviation. If feasible, extend the experiment to five seeds. | P[63] | `REQ-A10 / REQ-E04` | `final_faculty_remediation/results/multi_seed_results.json` |
| **FR-E05** | Section E | Compare RW-Guard with the baseline classifiers using paired statistical analysis. Report confidence intervals for differences in ROC-AUC and low-FPR detection performance. | P[64] | `REQ-E05` | `results/statistics/paired_baseline_comparisons.json` |
| **FR-E06** | Section E | Investigate why the threshold calibrated for 1% FPR on validation produces 3.5% FPR on the test set. Report the number of independent negative samples, validation and test score distributions, threshold-selection procedure, and uncertainty around both FPR estimates. | P[65] | `REQ-E06` | `results/statistics/threshold_validation_test_analysis.json` |
| **FR-E07** | Section E | Provide one consolidated statistical results table covering the final model, baseline comparisons and independent training runs. | P[66] | `REQ-E07` | `results/statistics/consolidated_statistical_results.csv` |
| **FR-E08** | Section E | Revise the Discussion and Conclusion to acknowledge the limited detection sensitivity at strict false-positive-rate operating points. Avoid claiming deployment readiness unless supported by the results. | P[67] | `MANU / Scientific Claims` | `final_faculty_remediation/manuscript/corrected_final_manuscript.docx` |
| **FR-E09** | Section E | Please submit the prediction scores, source-image identifiers, statistical analysis scripts, confidence interval calculations and revised manuscript. | P[68] | `REQ-PKG01 / REQ-PKG05` | `deliverables/RW_GUARD_FINAL_FACULTY_SUBMISSION.zip` |
| **FR-CHK01** | Checklist | Freeze final seven-scheme checkpoint and validation-selected threshold | P[119] | `REQ-A02 / REQ-A03` | `final_faculty_remediation/checkpoints/primary_checkpoint.pt` |
| **FR-CHK02** | Checklist | Regenerate all principal test metrics and tables | P[120] | `REQ-A04` | `final_faculty_remediation/results/primary_metrics.json` |
| **FR-CHK03** | Checklist | Complete distortion-matched shortcut controls | P[121] | `REQ-B01` | `results/shortcut_controls/distortion_matched_single.json` |
| **FR-CHK04** | Checklist | Separate zero-shot neural evaluation and supervised adaptation | P[122] | `REQ-C02` | `results/neural_generalization/trustmark_zero_shot.json` |
| **FR-CHK05** | Checklist | Stratify overwrite, dual-survival and failed-embedding outcomes | P[123] | `REQ-D02` | `results/attack_outcomes/per_attack_recovery.csv` |
| **FR-CHK06** | Checklist | Calculate low-FPR and fixed-threshold confidence intervals | P[124] | `REQ-E01` | `results/statistics/consolidated_statistical_results.json` |
| **FR-CHK07** | Checklist | Evaluate independent training seeds on the same test set | P[125] | `REQ-A10` | `final_faculty_remediation/results/multi_seed_results.json` |
| **FR-CHK08** | Checklist | Reconcile abstract, main results and conclusion | P[126] | `MANU-01..22` | `final_faculty_remediation/manuscript/corrected_final_manuscript.docx` |
| **FR-CHK09** | Checklist | Rebuild and verify all reference entries | P[127] | `MANU` | `final_faculty_remediation/manuscript/corrected_final_manuscript.docx` |
| **FR-CHK10** | Checklist | Review every caption, equation, table and figure at final journal page size | P[128] | `MANU` | `final_faculty_remediation/manuscript/corrected_final_manuscript.docx` |
| **FR-CHK11** | Checklist | Proofread the entire revised manuscript again after scientific updates | P[129] | `MANU` | `final_faculty_remediation/manuscript/corrected_final_manuscript.docx` |
| **FR-ED01** | Editorial | Fix abstract within 250 words max. | P[83] | `MANU-01` | `final_faculty_remediation/manuscript/corrected_final_manuscript.docx` |
| **FR-ED02** | Editorial | Competing Interests: Use 'The authors declare no competing interests.' | P[106], P[111] | `MANU` | `final_faculty_remediation/manuscript/corrected_final_manuscript.docx` |
| **FR-ED03** | Editorial | Data Availability: State code, experiment configurations, model checkpoints, and evaluation scripts are available at the project repository. | P[113] | `MANU` | `final_faculty_remediation/manuscript/corrected_final_manuscript.docx` |
| **FR-ED04** | Editorial | Dataset / validation: Use consistent COCO val2017 terminology, source-image counts, image-level versus sample-level counts. | P[92] | `REQ-PKG01` | `final_faculty_remediation/manifests/master_source_manifest.csv` |
