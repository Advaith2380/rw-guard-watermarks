"""Master Technical Orchestration Script for Faculty Review Implementation.

Coordinates execution across all five core faculty requirements (A - E):
1. Step 1: Main Primary 7-Scheme Model Evaluation (`evaluate.py`)
2. Step 2: Attack-Outcome Stratified Evaluation (`evaluate_outcomes.py`)
3. Step 3: Distortion-Matched Controls Evaluation (`matched_controls.py`)
4. Step 4: Nonlinear Residual & Spectral Baselines (`shortcut_baseline.py`)
5. Step 5: TrustMark Generalization Evaluation (`evaluate_trustmark_cache.py`)
6. Step 6: StegaStamp Zero-Shot Detection Evaluation (`test_stegastamp_detector.py`)
7. Step 7: PACS Cross-Domain Calibration & Score Shift (`pacs_calibration.py`)
8. Step 8: Multi-Seed Reproducibility Analysis (`scripts/evaluate_three_seeds.py`)
9. Step 9: Validation vs Test FPR Discrepancy Investigation (`scripts/investigate_fpr_discrepancy.py`)
10. Step 10: Master Results Consolidation (`scripts/consolidate_final_results.py`)
11. Step 11: Final Regression Testing Suite (`run_tests.py`)
"""

import argparse
import os
import subprocess
import sys
import time


PYTHON_EXE = "D:/projects/rewm-guard/.venv/Scripts/python.exe"
if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = sys.executable


def run_step(step_num, step_name, cmd_args, check_output_file=None):
    print("\n" + "=" * 80)
    print(f" STEP {step_num}: {step_name.upper()}")
    print("=" * 80)
    print(f"Command: {PYTHON_EXE} {' '.join(cmd_args)}")
    
    if check_output_file and os.path.exists(check_output_file):
        print(f"  [CACHE] Output file already exists: {check_output_file}")
        print("  Skipping re-execution to preserve resources.")
        return True

    t0 = time.time()
    result = subprocess.run([PYTHON_EXE] + cmd_args, cwd=os.path.abspath("."))
    elapsed = time.time() - t0
    
    if result.returncode != 0:
        print(f"  [FAILED] Step {step_num} exited with code {result.returncode} after {elapsed:.1f}s!")
        return False
        
    print(f"  [SUCCESS] Step {step_num} completed successfully in {elapsed:.1f}s.")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-eval", action="store_true", help="Skip Step 1 if evaluate.py already ran/running")
    parser.add_argument("--start-at", type=int, default=2, help="Start at step number (default 2)")
    args = parser.parse_args()

    steps = [
        (1, "Main Primary Model Full Evaluation",
         ["evaluate.py", "--ckpt", "checkpoints/final/rwguard_final_7scheme.pt", "--data", "data/coco", "--pacs", "data/pacs", "--thr", "1.3394", "--out", "results/final_7scheme_primary"],
         "results/final_7scheme_primary/results.json"),
        (2, "Attack-Outcome Stratification (4 Categories)",
         ["evaluate_outcomes.py", "--ckpt", "checkpoints/final/rwguard_final_7scheme.pt", "--data", "data/coco", "--n-test", "500", "--thr", "1.3394", "--out", "audit/outcome_stratification_results.json"],
         "audit/outcome_stratification_results.json"),
        (3, "Distortion-Matched Single & Matched-Noise Controls",
         ["matched_controls.py", "--ckpt", "checkpoints/final/rwguard_final_7scheme.pt", "--data", "data/coco", "--n-test", "300", "--thr", "1.3394", "--out", "audit/matched_controls_results.json"],
         "audit/matched_controls_results.json"),
        (4, "Nonlinear Residual Baselines (Logistic Reg vs Random Forest)",
         ["shortcut_baseline.py", "--ckpt", "checkpoints/final/rwguard_final_7scheme.pt", "--data", "data/coco", "--n-train", "1000", "--n-val", "300", "--n-test", "500", "--out", "audit/shortcut_baseline_results.json"],
         "audit/shortcut_baseline_results.json"),
        (5, "TrustMark Zero-Shot and Supervised Adaptation Evaluation",
         ["evaluate_trustmark_cache.py"],
         "audit/trustmark_evaluation_results.json"),
        (6, "StegaStamp Zero-Shot Detection Evaluation",
         ["test_stegastamp_detector.py", "--ckpt", "checkpoints/final/rwguard_final_7scheme.pt", "--data", "data/coco", "--n", "150", "--thr", "1.3394", "--out", "audit/stegastamp_evaluation_results.json"],
         "audit/stegastamp_evaluation_results.json"),
        (7, "PACS Cross-Domain Calibration & Score Shift Analysis",
         ["pacs_calibration.py", "--ckpt", "checkpoints/final/rwguard_final_7scheme.pt", "--pacs", "data/pacs", "--thr", "1.3394", "--n-samples", "200", "--out", "audit/pacs_calibration_results.json"],
         "audit/pacs_calibration_results.json"),
        (8, "Multi-Seed Reproducibility Analysis (3 Seeds)",
         ["scripts/evaluate_three_seeds.py", "--data", "data/coco", "--n-test", "500", "--out", "audit/seed_evaluation_results.json"],
         "audit/seed_evaluation_results.json"),
        (9, "Validation vs Test FPR Discrepancy Investigation",
         ["scripts/investigate_fpr_discrepancy.py"],
         "audit/fpr_discrepancy_investigation.json"),
        (10, "Consolidate Master Final Results",
         ["scripts/consolidate_final_results.py"],
         "audit/final_consolidated_results.json"),
        (11, "Final Unit & Regression Test Suite",
         ["run_tests.py"],
         None)
    ]

    print("================================================================================")
    print(" RW-GUARD MASTER TECHNICAL EXECUTION ORCHESTRATOR")
    print(f" Environment Python: {PYTHON_EXE}")
    print("================================================================================")

    for num, name, cmd_args, out_file in steps:
        if num < args.start_at:
            continue
        if num == 1 and args.skip_eval:
            print(f"Skipping Step 1 per --skip-eval flag.")
            continue
        success = run_step(num, name, cmd_args, check_output_file=None)
        if not success:
            print(f"\nExecution halted due to failure in Step {num}: {name}")
            sys.exit(1)

    print("\n" + "=" * 80)
    print(" ALL 11 SCIENTIFIC AND REGRESSION STAGES COMPLETED SUCCESSFULLY!")
    print("================================================================================")


if __name__ == "__main__":
    main()
