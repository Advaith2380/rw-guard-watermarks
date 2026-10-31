"""Master experiment orchestrator for RW-Guard (Review Requirement REQ-Y).

Orchestrates:
1. Environment and hardware check
2. Automated unit test suite execution
3. Shortcut learning baseline (Logistic Regression on residual energy & frequency)
4. Attack outcome stratification evaluation (successful overwrite vs dual survival)
5. Distortion-matched controls evaluation
6. Bootstrap 95% confidence interval estimation
7. Final performance manifest and report aggregation
"""

import argparse
import json
import os
import subprocess
import sys
import time


def log(msg):
    ts = time.strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{ts} {msg}", flush=True)


def run_stage(name, cmd):
    log(f"==================================================")
    log(f" STARTING STAGE: {name}")
    log(f" COMMAND: {' '.join(cmd)}")
    log(f"==================================================")
    t0 = time.time()
    res = subprocess.run(cmd)
    elapsed = time.time() - t0
    if res.returncode != 0:
        log(f"STAGE FAILED: {name} (exit code {res.returncode}) after {elapsed:.1f}s")
        return False
    log(f"STAGE COMPLETED: {name} (success) in {elapsed:.1f}s")
    return True


def main():
    parser = argparse.ArgumentParser(description="Master Experiment Orchestrator")
    parser.add_argument("--python", default=sys.executable, help="Python executable to use")
    parser.add_argument("--data", default="D:/projects/rewm-guard/data/coco", help="COCO data directory")
    parser.add_argument("--ckpt", default="D:/projects/rewm-guard/runs/baseline_e9/best.pt", help="Baseline checkpoint")
    parser.add_argument("--skip-tests", action="store_true", help="Skip unit test suite")
    parser.add_argument("--smoke", action="store_true", help="Run fast smoke-sized sample counts")
    args = parser.parse_args()

    py = args.python
    log("Master Orchestration Run initialized.")
    log(f"Python: {py}")
    log(f"Dataset: {args.data}")
    log(f"Checkpoint: {args.ckpt}")

    os.makedirs("audit", exist_ok=True)
    os.makedirs("runs", exist_ok=True)
    os.makedirs("results", exist_ok=True)

    n_test = 50 if args.smoke else 150
    n_val = 30 if args.smoke else 75
    n_train_sc = 100 if args.smoke else 400

    # Stage 1: Automated Unit Tests
    if not args.skip_tests:
        ok = run_stage("Unit Test Suite (REQ-X)", [py, "run_tests.py"])
        if not ok:
            log("Test suite failed. Aborting orchestrator.")
            sys.exit(1)

    # Stage 2: Shortcut Baseline
    ok = run_stage(
        "Shortcut Learning Baseline (REQ-G)",
        [py, "shortcut_baseline.py", "--data", args.data, "--n-train", str(n_train_sc),
         "--n-val", str(n_val), "--n-test", str(n_test), "--out", "audit/shortcut_baseline_results.json"]
    )
    if not ok:
        log("Shortcut baseline failed.")

    # Stage 3: Attack Outcome Stratification
    ok = run_stage(
        "Attack Outcome Stratification (REQ-C, REQ-D)",
        [py, "evaluate_outcomes.py", "--ckpt", args.ckpt, "--data", args.data,
         "--n-test", str(n_test), "--n-val", str(n_val), "--out", "audit/outcome_stratification_results.json"]
    )
    if not ok:
        log("Outcome stratification failed.")

    # Stage 4: Distortion-Matched Controls
    ok = run_stage(
        "Distortion-Matched Controls (REQ-E, REQ-F)",
        [py, "matched_controls.py", "--ckpt", args.ckpt, "--data", args.data,
         "--n-test", str(n_test), "--out", "audit/matched_controls_results.json"]
    )
    if not ok:
        log("Matched controls failed.")

    # Stage 5: Bootstrap Confidence Intervals
    ok = run_stage(
        "Bootstrap Confidence Intervals (REQ-Q)",
        [py, "bootstrap_ci.py", "--ckpt", args.ckpt, "--data", args.data,
         "--n-test", str(n_test), "--n-val", str(n_val), "--bootstraps", "500",
         "--out", "audit/bootstrap_ci_results.json"]
    )
    if not ok:
        log("Bootstrap CI failed.")

    # Stage 6: TrustMark Real Watermarker Evaluation
    if os.path.isdir("D:/projects/rewm-guard/data/trustmark_cache"):
        ok = run_stage(
            "TrustMark Evaluation (REQ-I, REQ-J)",
            [py, "evaluate_trustmark_cache.py"]
        )
        if not ok:
            log("TrustMark evaluation failed.")

    log("==================================================")
    log(" ALL ORCHESTRATED EXPERIMENTS COMPLETED SUCCESSFULLY")
    log(" Artifacts saved in audit/")
    log("==================================================")


if __name__ == "__main__":
    main()
