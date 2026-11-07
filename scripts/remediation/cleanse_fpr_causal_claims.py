#!/usr/bin/env python3
"""Cleanse all unsupported causal FPR claims across all markdown, CSV, and JSON audit files.

Mandatory faculty wording:
"The frozen validation threshold yielded an empirical validation FPR of 1.00% and a held-out test FPR of 3.33%. The two-sample KS test did not detect a statistically significant difference between the negative-score distributions (D = 0.0500, p = 0.5485). However, this does not establish distributional equivalence or identify the cause of the observed operating-point difference."
"""

import os
import glob
import re

MANDATORY_PHRASING = (
    "The frozen validation threshold yielded an empirical validation FPR of 1.00% and a held-out test FPR of 3.33%. "
    "The two-sample KS test did not detect a statistically significant difference between the negative-score distributions "
    "(D = 0.0500, p = 0.5485). However, this does not establish distributional equivalence or identify the cause of the "
    "observed operating-point difference."
)

FILES_TO_CHECK = [
    "audit/final/FINAL_INDEPENDENT_VERIFICATION_REPORT.md",
    "final_faculty_remediation/FINAL_INDEPENDENT_VERIFICATION_REPORT.md",
    "audit/final_independent_verification/FINAL_INDEPENDENT_VERIFICATION_REPORT.md",
    "audit/final_independent_verification/scientific_claim_audit.md",
    "audit/scientific_claims/scientific_claim_audit.md",
    "audit/json_reconciliation/discrepancy_register.md",
    "deliverables/FINAL_DISCREPANCY_RESOLUTION_REGISTER.md",
    "final_faculty_remediation/FINAL_DISCREPANCY_RESOLUTION_REGISTER.md",
    "deliverables/FINAL_TECHNICAL_AND_FACULTY_REPORT.md",
    "final_faculty_remediation/FINAL_TECHNICAL_AND_FACULTY_REPORT.md",
    "audit/final/FINAL_PREVIOUS_VS_NEW_VS_FACULTY_COMPARISON.csv",
    "final_faculty_remediation/FINAL_PREVIOUS_VS_NEW_VS_FACULTY_COMPARISON.csv",
    "independent_audit/independent_metrics_report.md",
    "independent_audit/independent_audit_verdict.md"
]


def cleanse_file(path):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    original = content

    # Replace auditor interpretation that attributes to extreme tail sensitivity
    content = re.sub(
        r"reflects extreme tail sensitivity where small finite-sample shifts produce noticeable percentage changes\.?",
        "does not establish distributional equivalence or identify the cause of the observed operating-point difference.",
        content
    )
    content = re.sub(
        r"due to finite-sample extreme tail variance, not distribution shift\.?",
        "characterized by validation FPR of 1.00% and test FPR of 3.33% with non-significant KS test (p = 0.5485).",
        content
    )
    content = re.sub(
        r"Statistical tests conclusively demonstrate that underlying negative score distributions are identical \(p = 0\.55\), but high tail density renders fixed score thresholds sensitive to sample quantization\.?",
        MANDATORY_PHRASING,
        content
    )
    content = re.sub(
        r"proving that negative score distributions are statistically identical between validation and test sets\.?",
        "failing to detect a statistically significant difference between negative-score distributions (D = 0.0500, p = 0.5485). However, this does not establish distributional equivalence or identify the cause of the observed operating-point difference.",
        content
    )
    content = re.sub(
        r"Validation vs\. Test FPR Discrepancy & Extreme Tail Quantization",
        "Validation vs. Test Operating Point Analysis (1.00% vs. 3.33% FPR)",
        content
    )

    if content != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Cleaned {path}")
    else:
        print(f"No causal FPR claims found in {path}")


def main():
    print("Cleansing unsupported causal FPR claims...")
    for p in FILES_TO_CHECK:
        cleanse_file(p)
    print("Cleansing complete.")


if __name__ == "__main__":
    main()
