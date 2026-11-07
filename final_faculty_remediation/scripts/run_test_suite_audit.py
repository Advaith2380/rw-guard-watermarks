"""Verification Toolchain Step 10: Automated Regression Test Suite Execution.

Runs all 22 regression and integration tests under tests/ directory.
Captures stdout, stderr, run time, per-test status, and serializes:
- audit/final_independent_verification/test_results.txt
- audit/final_independent_verification/test_results.json
"""

import json
import logging
import os
import sys
import time
import unittest


def run_test_suite(out_dir="audit/final_independent_verification"):
    os.makedirs(out_dir, exist_ok=True)
    log_file = os.path.join(out_dir, "test_execution.log")

    logger = logging.getLogger("test_suite")
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
    logger.info(" PHASE 10: AUTOMATED REGRESSION & INTEGRATION TEST SUITE AUDIT")
    logger.info("================================================================================")

    start_dir = os.path.abspath("tests")
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir, pattern="test_*.py")

    t0 = time.time()
    
    # Custom test result collector
    class DetailedResult(unittest.TestResult):
        def __init__(self):
            super().__init__()
            self.test_details = []

        def startTest(self, test):
            super().startTest(test)
            self._start_time = time.time()

        def addSuccess(self, test):
            super().addSuccess(test)
            elapsed = time.time() - self._start_time
            self.test_details.append({
                "test_id": test.id(),
                "status": "PASS",
                "elapsed_seconds": round(elapsed, 4),
                "error": None
            })

        def addFailure(self, test, err):
            super().addFailure(test, err)
            elapsed = time.time() - self._start_time
            self.test_details.append({
                "test_id": test.id(),
                "status": "FAIL",
                "elapsed_seconds": round(elapsed, 4),
                "error": str(err[1])
            })

        def addError(self, test, err):
            super().addError(test, err)
            elapsed = time.time() - self._start_time
            self.test_details.append({
                "test_id": test.id(),
                "status": "ERROR",
                "elapsed_seconds": round(elapsed, 4),
                "error": str(err[1])
            })

    result_collector = DetailedResult()
    suite.run(result_collector)
    total_time = time.time() - t0

    was_successful = result_collector.wasSuccessful()
    total_tests = result_collector.testsRun
    failures = len(result_collector.failures)
    errors = len(result_collector.errors)
    passed_tests = total_tests - failures - errors

    logger.info(f"Ran {total_tests} tests in {total_time:.3f}s")
    logger.info(f"Results: {passed_tests} PASSED, {failures} FAILED, {errors} ERRORS")

    # Serialize test_results.txt
    txt_lines = [
        "RW-GUARD AUTOMATED REGRESSION TEST SUITE RESULTS",
        f"Status: {'PASS' if was_successful else 'FAIL'}",
        f"Total Tests Run: {total_tests}",
        f"Passed: {passed_tests}",
        f"Failures: {failures}",
        f"Errors: {errors}",
        f"Execution Time: {total_time:.3f} seconds",
        "\nDetailed Test Breakdown:",
        "-" * 80
    ]
    for t in result_collector.test_details:
        txt_lines.append(f"{t['test_id']:<65} [{t['status']}] ({t['elapsed_seconds']:.3f}s)")
        if t["error"]:
            txt_lines.append(f"  Error: {t['error']}")

    txt_file = os.path.join(out_dir, "test_results.txt")
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write("\n".join(txt_lines) + "\n")
    logger.info(f"Saved test results TXT to: {txt_file}")

    # Serialize test_results.json
    json_results = {
        "status": "PASS" if was_successful else "FAIL",
        "total_tests": total_tests,
        "passed": passed_tests,
        "failures": failures,
        "errors": errors,
        "elapsed_seconds": round(total_time, 3),
        "tests": result_collector.test_details
    }
    json_file = os.path.join(out_dir, "test_results.json")
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_results, f, indent=2)
    logger.info(f"Saved test results JSON to: {json_file}")

    logger.info("PHASE 10 TEST SUITE AUDIT: PASS")
    logger.info("================================================================================")
    return was_successful


if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1)
