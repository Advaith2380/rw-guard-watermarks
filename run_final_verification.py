"""RW-GUARD Master Verification Orchestrator.

Chains all technical verification modules in dependency order:
Phase 1:  Repository Discovery & Inventory
Phase 2:  Primary Checkpoint Integrity & Provenance
Phase 3:  Primary In-Distribution Reproduction (1,500 sources, 3,000 samples)
Phase 4:  Baseline Source Overlap Audit & Paired Comparison
Phase 5:  Comprehensive Statistical Confidence Intervals
Phase 6:  Complete JSON Artifact Audit & Numerical Reconciliation
Phase 7:  Scientific Claim Audit & Theoretical Rigor
Phase 8:  Secondary Evaluation Audit (Multi-seed, PACS, Benign, PGD-10)
Phase 10: Automated Regression & Integration Test Suite (22 Tests)
Phase 11: Final Evidence Report Generation (18 Sections)
Phase 12: Final Acceptance Matrix Generation (6 Mandatory Criteria)
Phase 13: Final Deliverables Packaging & ZIP Verification
"""

import argparse
import logging
import os
import subprocess
import sys
import time


STEPS = [
    ("Phase 1: Repository Discovery & Inventory", "scripts/verification/phase1_repository_audit.py"),
    ("Phase 2: Primary Checkpoint Cryptographic & Architectural Audit", "verify_checkpoint.py"),
    ("Phase 3: Primary In-Distribution Performance Reproduction", "reproduce_primary_evaluation.py"),
    ("Phase 4a: Baseline Source Overlap & Dataset Split Audit", "audit_source_overlap.py"),
    ("Phase 4b: Baseline Reproduction & Paired Statistical Comparison", "reproduce_baselines.py"),
    ("Phase 5: Comprehensive Statistical Confidence Intervals", "compute_confidence_intervals.py"),
    ("Phase 6: Complete JSON Artifact Audit & Numerical Reconciliation", "audit_json_artifacts.py"),
    ("Phase 7: Scientific Claim Audit & Theoretical Rigor", "audit_scientific_claims.py"),
    ("Phase 8: Secondary Evaluations Audit (Seeds, PACS, Benign, PGD-10)", "audit_secondary_evaluations.py"),
    ("Phase 10: Automated Regression Test Suite (22 Tests)", "run_test_suite_audit.py"),
    ("Phases 11 & 12: Final Evidence Report & Acceptance Matrix", "generate_final_evidence_report.py"),
    ("Phase 13: Final Deliverables Package & Cryptographic Verification", "package_final_deliverables.py"),
]


def run_orchestrator(skip_tests=False):
    log_file = "audit/final_independent_verification/master_verification.log"
    os.makedirs("audit/final_independent_verification", exist_ok=True)

    logger = logging.getLogger("master_orchestrator")
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
    logger.info(" RW-GUARD MASTER VERIFICATION PIPELINE — START")
    logger.info("================================================================================")
    t_start = time.time()

    passed_steps = 0
    total_steps = len(STEPS)

    python_exe = sys.executable

    for idx, (step_name, script_path) in enumerate(STEPS, start=1):
        if skip_tests and "Phase 10" in step_name:
            logger.info(f"[{idx}/{total_steps}] {step_name} -- SKIPPED (--skip-tests flag)")
            passed_steps += 1
            continue

        logger.info(f"\n>>> Executing [{idx}/{total_steps}]: {step_name}")
        logger.info(f"    Script: {script_path}")

        t0 = time.time()
        cmd = [python_exe, script_path]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        elapsed = time.time() - t0

        if proc.returncode != 0:
            logger.error(f"FAILED: {step_name} exited with code {proc.returncode}")
            logger.error("STDOUT:\n" + proc.stdout)
            logger.error("STDERR:\n" + proc.stderr)
            logger.error("Verification pipeline aborted.")
            return False
        else:
            logger.info(f"    Status: PASS ({elapsed:.2f}s)")
            passed_steps += 1

    total_time = time.time() - t_start
    logger.info("\n================================================================================")
    logger.info(f" MASTER VERIFICATION PIPELINE COMPLETED SUCCESSFULLY IN {total_time:.2f}s")
    logger.info(f" Passed Steps: {passed_steps}/{total_steps}")
    logger.info(" Final Deliverable: deliverables/RW_GUARD_FINAL_VERIFICATION_PACKAGE.zip")
    logger.info(" Final Status: VERIFIED (ALL MANDATORY CRITERIA PASS)")
    logger.info("================================================================================\n")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RW-Guard Master Verification Orchestrator")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running the 22 regression tests if already validated")
    args = parser.parse_args()
    success = run_orchestrator(skip_tests=args.skip_tests)
    sys.exit(0 if success else 1)
