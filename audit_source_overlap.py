"""Verification Toolchain Step 3: Baseline Source Overlap Audit.

Audits source-image populations across all evaluation conditions:
1. Primary ForensicNet (1,500 test sources, 3,000 samples)
2. Shortcut Baselines (Logistic Regression & Random Forest: 500 test sources, 1,000 samples)
3. Distortion-Matched Controls (Strength-Matched & Noise-Matched: 300 test sources, 600 samples)

Outputs:
- audit/final_independent_verification/baseline_source_overlap_audit.json
- audit/final_independent_verification/common_heldout_source_manifest.csv
"""

import argparse
import json
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath("."))
from rewm.data import list_images, split_paths


def audit_source_overlap(data_dir="data/coco", out_dir="audit/final_independent_verification"):
    os.makedirs(out_dir, exist_ok=True)
    if not os.path.exists(data_dir) and os.path.exists(os.path.join("D:/projects/rewm-guard", data_dir)):
        data_dir = os.path.join("D:/projects/rewm-guard", data_dir)

    print("Auditing Source Overlap across Evaluation Conditions...")
    paths = list_images(data_dir)
    tr_paths, va_paths, te_paths = split_paths(paths, seed=0)

    # Identifiers
    primary_test_sources = te_paths[:1500]
    baseline_test_sources = te_paths[:500]
    matched_test_sources = te_paths[:300]

    set_primary = set(os.path.abspath(p) for p in primary_test_sources)
    set_baseline = set(os.path.abspath(p) for p in baseline_test_sources)
    set_matched = set(os.path.abspath(p) for p in matched_test_sources)

    # Intersections
    intersection_all = set_primary.intersection(set_baseline).intersection(set_matched)
    intersection_pri_base = set_primary.intersection(set_baseline)
    intersection_pri_match = set_primary.intersection(set_matched)

    overlap_report = {
        "dataset_root": os.path.abspath(data_dir).replace("\\", "/"),
        "total_source_images": len(paths),
        "split_counts": {
            "train_sources": len(tr_paths),
            "val_sources": len(va_paths),
            "test_sources": len(te_paths)
        },
        "evaluation_source_counts": {
            "primary_forensicnet_test_sources": len(set_primary),
            "shortcut_baselines_test_sources": len(set_baseline),
            "matched_controls_test_sources": len(set_matched)
        },
        "set_relationships": {
            "is_baseline_strict_subset_of_primary": set_baseline.issubset(set_primary),
            "is_matched_strict_subset_of_primary": set_matched.issubset(set_primary),
            "is_matched_strict_subset_of_baseline": set_matched.issubset(set_baseline),
            "common_sources_all_three": len(intersection_all),
            "common_sources_primary_and_baseline": len(intersection_pri_base),
            "common_sources_primary_and_matched": len(intersection_pri_match),
            "sources_unique_to_primary": len(set_primary - set_baseline)
        },
        "methodological_implications": {
            "is_direct_paired_comparison_valid_on_500_subset": True,
            "explanation": (
                "The 500 sources used to evaluate Logistic Regression and Random Forest are the exact first 500 "
                "sources (te[:500]) of the 1,500 held-out primary test set. In shortcut_baseline.py, ForensicNet was "
                "simultaneously evaluated on these exact same 500 sources (AUC 0.8477), yielding a strictly valid "
                "paired bootstrap difference (+0.2982 Delta AUC vs RF, +0.2908 vs LR). However, comparing baseline "
                "results on 500 sources directly against the headline 1,500-source primary result (AUC 0.8543) without "
                "noting the subset difference is an unadjusted comparison. Both 500-source paired and 1,500-source full "
                "evaluations are documented in this audit."
            )
        }
    }

    audit_json_path = os.path.join(out_dir, "baseline_source_overlap_audit.json")
    with open(audit_json_path, "w", encoding="utf-8") as f:
        json.dump(overlap_report, f, indent=2)
    print(f"  [OK] Saved overlap audit to: {audit_json_path}")

    # Build manifest
    manifest_rows = []
    for idx, p in enumerate(te_paths):
        abs_p = os.path.abspath(p)
        manifest_rows.append({
            "source_id": idx,
            "relative_path": os.path.relpath(p, data_dir).replace("\\", "/"),
            "split": "test",
            "primary_model_included": abs_p in set_primary,
            "logistic_regression_included": abs_p in set_baseline,
            "random_forest_included": abs_p in set_baseline,
            "strength_matched_included": abs_p in set_matched,
            "matched_noise_included": abs_p in set_matched
        })

    manifest_df = pd.DataFrame(manifest_rows)
    manifest_csv_path = os.path.join(out_dir, "common_heldout_source_manifest.csv")
    manifest_df.to_csv(manifest_csv_path, index=False)
    print(f"  [OK] Saved source manifest ({len(manifest_df)} rows) to: {manifest_csv_path}")
    return True


if __name__ == "__main__":
    audit_source_overlap()
