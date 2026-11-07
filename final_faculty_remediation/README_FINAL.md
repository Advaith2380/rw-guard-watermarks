# RW-GUARD: FINAL FACULTY REVIEW SUBMISSION & REPRODUCIBILITY SUITE

**Project:** Forensic Detection of Re-Watermarking Attacks: A Deep Learning Approach to Identifying Ownership Forgery in Digital Images  
**Date of Final Packaging:** 2026-11-07 13:38:42  
**Compliance Verdict:** **FULLY VERIFIED — All 53 Mandatory Faculty Review Requirements Passed (0 Fail, 0 Blocked)**  
**Authoritative Primary Checkpoint:** `checkpoints/primary_checkpoint.pt`  
**Primary SHA-256:** `37680cdd2d4e5100cbb8aa1642e78b9bb3df373e79efd9f8512f89e15d0c0573`  
**Defended Checkpoint:** `checkpoints/defended_checkpoint_adv_eps1.pt`  
**Defended SHA-256:** `27954fd43360830d76fa107036567e9486844fa85d6a058c84d438b2e6caefed`  
**Trainable Parameters:** 2,466,099 parameters  

## Quick Verification
To run the automated verification suite:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_rwguard_final_verification.ps1 -Mode Full
```

To validate the acceptance matrix against this extracted package:
```powershell
python .\scripts\validate_acceptance_matrix.py --package-root .
```

To verify the multi-resolution empirical metrics:
```powershell
python .\scripts\verify_final_resolution_metrics.py
```

## Directory Structure
- `FINAL_ACCEPTANCE_MATRIX.csv`: Populated 53-row faculty acceptance matrix with package-internal evidence paths.
- `EVIDENCE_TRACEABILITY_AUDIT.csv`: Itemized evidence traceability audit for all 53 faculty requirements.
- `ACCEPTANCE_MATRIX_VALIDATION_REPORT.md`: Matrix validation audit confirming 10/10 checks PASS.
- `INTERNAL_PACKAGE_VERIFICATION.txt`: Internal component verification report.
- `manuscript/`: Final publication-ready manuscript document (`corrected_final_manuscript.docx`).
- `checkpoints/`: Frozen primary 7-scheme checkpoint (`primary_checkpoint.pt`) and defended adversarial checkpoint.
- `configs/`: Training and evaluation configurations.
- `manifests/`: Master source manifest (5,000 images), derived sample manifest (3,000 samples), and split integrity report.
- `predictions/`: Fresh model forward-pass predictions (3,000 rows, no cached NPZ reuse).
- `results/`: Comprehensive empirical result JSONs and CSVs across all primary and secondary conditions.
  * `results/final_primary/FINAL_RESOLUTION_METRICS_VERIFIED.csv`: Reconciled multi-resolution evaluation table.
  * `results/shortcut_controls/`: Distortion-matched single, nonlinear RF/LR baselines, matched noise.
  * `results/neural_generalization/`: TrustMark and StegaStamp zero-shot and adaptation evaluations.
  * `results/attack_outcomes/`: Collision outcomes, dual survival rates, per-attack recovery.
  * `results/statistics/`: Consolidated statistical bootstrap results and CIs.
- `tests/`: Automated regression test results (22/22 passing).
- `scripts/`: Verification PowerShell script and underlying evaluation scripts.
- `logs/`: Complete execution logs.
