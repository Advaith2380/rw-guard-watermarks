"""Attack Outcome-Stratified Evaluation for RW-Guard (Faculty Review Section D / REQ-C, REQ-D).

Implements four explicit outcome categories (Section 7.2 of Master Prompt):
1. 'successful_overwrite': Attacker message passes verification (bit-acc >= tau),
   victim message fails verification (bit-acc < tau). True ownership forgery.
2. 'dual_survival': Both victim and attacker messages pass verification
   (both bit-acc >= tau). Forensic ownership ambiguity / conflict.
3. 'failed_attacker_embedding': Victim message passes verification (bit-acc >= tau),
   attacker message fails verification (bit-acc < tau).
4. 'both_unrecoverable': Both victim and attacker messages fail verification
   (both bit-acc < tau).

Computes:
- Total valid double-watermarked samples and percentage in each category.
- Exact recalculation and verification of the dual-survival percentage.
- Category-specific detector evaluation using the frozen 7-scheme model and frozen threshold.
- Detection rate at fixed threshold with 95% bootstrap confidence intervals.
- Category-specific ROC-AUC and TPR@1%FPR against common singly-watermarked controls.
"""

import argparse
import json
import os
import sys
sys.path.insert(0, os.path.abspath("."))
import numpy as np
import torch
from torch.utils.data import DataLoader

from rewm.data import list_images, split_paths, ReWMDataset
from rewm.model import build_model
from rewm.engine import predict_with_outcomes
from rewm.metrics import threshold_at_fpr, roc_auc, rates_at, tpr_at_fpr, summarize
from bootstrap_ci import compute_bootstrap_cis


def run_outcome_stratified_evaluation(ckpt_path, data_dir, n_test=500, n_val=300, thr_fixed=1.3394, bs=32, device="cuda"):
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    targs = ckpt["args"]
    model = build_model(targs["arch"], width=targs.get("width", 32)).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()

    seen = ckpt.get("train_schemes", ["dct_qim", "dwt_qim", "ss_spatial", "fft_ring", "nmp_freq", "svd_qim", "dct_svd"])
    paths = list_images(data_dir)
    _, va, te = split_paths(paths, seed=0)
    va = va[:n_val]
    if n_test:
        te = te[:n_test]

    seen_kw = dict(victim_schemes=seen, attacker_schemes=seen, single_schemes=seen)

    # Operating threshold: if provided, use frozen; otherwise compute on validation negatives
    if thr_fixed is not None:
        thr = float(thr_fixed)
        print(f"Using fixed operating threshold: logit > {thr:.4f}")
    else:
        v_ds = ReWMDataset(va, train=False, seed=777, size=256, benign_p=0.5, **seen_kw)
        v_dl = DataLoader(v_ds, batch_size=bs, shuffle=False, num_workers=0)
        sv, yv, _, _ = predict_with_outcomes(model, v_dl, device, desc="Validation Calibration")
        thr = float(threshold_at_fpr(sv[yv == 0], 0.01))
        print(f"Validation operating threshold (1% FPR): logit > {thr:.4f}")

    # Test split with full outcome tracking
    print(f"Evaluating {len(te)} source images ({len(te)*2} derived test samples) with outcome tracking...")
    t_ds = ReWMDataset(te, train=False, seed=777, size=256, benign_p=0.5, track_outcomes=True, **seen_kw)
    t_dl = DataLoader(t_ds, batch_size=bs, shuffle=False, num_workers=0)
    st, yt, kinds, outcomes = predict_with_outcomes(model, t_dl, device, desc="Test Outcome Tracking")

    # Overall in-distribution metrics on test set
    sids = np.array([i // 2 for i in range(len(yt))])
    overall_m = summarize(yt, st, thr)
    overall_ci = compute_bootstrap_cis(yt, st, thr=thr, source_ids=sids, n_bootstraps=2000, seed=42)

    # Separate negatives (clean and single-watermarked controls)
    neg_mask = (yt == 0)
    pos_mask = (yt == 1)
    
    st_neg = st[neg_mask]
    kinds_neg = np.array(kinds)[neg_mask]
    
    single_mask = np.array([k.startswith("single:") for k in kinds_neg])
    st_single = st_neg[single_mask]  # Common singly-watermarked controls

    total_double = int(np.sum(pos_mask))
    print(f"\nTotal double-watermarked test samples: {total_double}")

    categories = [
        "successful_overwrite",
        "dual_survival",
        "failed_attacker_embedding",
        "both_unrecoverable"
    ]

    outcomes_arr = np.array(outcomes)
    category_results = {}
    
    for cat in categories:
        mask = (outcomes_arr == cat)
        cat_count = int(np.sum(mask))
        cat_pct = (cat_count / total_double * 100.0) if total_double > 0 else 0.0
        
        if cat_count > 0:
            cat_scores = st[mask]
            cat_flagged = int(np.sum(cat_scores > thr))
            cat_tpr = cat_flagged / cat_count
            
            # Grouped bootstrap CI for category detection rate
            cat_sids = sids[mask]
            cat_cis_stats = []
            rng_boot = np.random.default_rng(42)
            u_sids = np.unique(cat_sids)
            for _ in range(2000):
                sampled_u = rng_boot.choice(u_sids, size=len(u_sids), replace=True)
                sample_scores = []
                for su in sampled_u:
                    sample_scores.extend(cat_scores[cat_sids == su])
                sample_scores = np.array(sample_scores)
                cat_cis_stats.append(float(np.mean(sample_scores > thr)))
            ci_low = float(np.percentile(cat_cis_stats, 2.5))
            ci_high = float(np.percentile(cat_cis_stats, 97.5))
            
            # Compute ROC-AUC and TPR@1%FPR against common singly-watermarked controls
            if len(st_single) > 0:
                y_eval = np.concatenate([np.zeros(len(st_single)), np.ones(cat_count)])
                s_eval = np.concatenate([st_single, cat_scores])
                try:
                    cat_auc = float(roc_auc(y_eval, s_eval))
                    cat_tpr1 = float(tpr_at_fpr(y_eval, s_eval, 0.01))
                except Exception:
                    cat_auc, cat_tpr1 = None, None
            else:
                cat_auc, cat_tpr1 = None, None

            category_results[cat] = {
                "category_name": cat,
                "n_samples": cat_count,
                "percentage_of_attacks": float(cat_pct),
                "n_independent_sources": len(u_sids),
                "detection_count": cat_flagged,
                "detection_rate_fixed_thr": float(cat_tpr),
                "detection_rate_95_ci": [ci_low, ci_high],
                "mean_detector_score": float(np.mean(cat_scores)),
                "std_detector_score": float(np.std(cat_scores)),
                "median_detector_score": float(np.median(cat_scores)),
                "auc_vs_single_controls": cat_auc,
                "tpr_at_1pct_fpr_vs_single_controls": cat_tpr1
            }
        else:
            category_results[cat] = {
                "category_name": cat,
                "n_samples": 0,
                "percentage_of_attacks": 0.0,
                "detection_rate_fixed_thr": 0.0
            }

    # Recalculate dual-survival rate
    dual_count = category_results["dual_survival"]["n_samples"]
    dual_rate_pct = (dual_count / total_double * 100.0) if total_double > 0 else 0.0
    print(f"Recalculated Dual-Survival Rate: {dual_rate_pct:.2f}% ({dual_count}/{total_double})")

    # Negative controls breakdown
    neg_results = {
        "all_negatives": {
            "n": int(len(st_neg)),
            "fpr_fixed_thr": float(np.mean(st_neg > thr)),
            "mean_score": float(np.mean(st_neg)),
            "std_score": float(np.std(st_neg))
        },
        "single_watermark_controls": {
            "n": int(len(st_single)),
            "fpr_fixed_thr": float(np.mean(st_single > thr)),
            "mean_score": float(np.mean(st_single)),
            "std_score": float(np.std(st_single))
        },
        "clean_controls": {
            "n": int(np.sum(kinds_neg == "clean")),
            "fpr_fixed_thr": float(np.mean(st_neg[kinds_neg == "clean"] > thr)),
            "mean_score": float(np.mean(st_neg[kinds_neg == "clean"])),
            "std_score": float(np.std(st_neg[kinds_neg == "clean"]))
        }
    }

    report = {
        "checkpoint": ckpt_path,
        "operating_threshold": float(thr),
        "total_test_samples": len(yt),
        "total_source_images": len(te),
        "overall_in_distribution": overall_m,
        "overall_confidence_intervals_95": overall_ci["metrics"],
        "dual_survival_rate_verified": {
            "dual_survival_count": dual_count,
            "total_double_watermarked": total_double,
            "dual_survival_percentage": float(dual_rate_pct),
            "verification_formula": "dual_survival_count / total_valid_double_watermarked * 100"
        },
        "four_outcome_categories": category_results,
        "negative_controls": neg_results
    }
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ckpt", default="checkpoints/final/rwguard_final_7scheme.pt")
    parser.add_argument("--data", default="data/coco")
    parser.add_argument("--n-test", type=int, default=500, help="Number of test source images (1000 derived samples)")
    parser.add_argument("--n-val", type=int, default=300)
    parser.add_argument("--thr", type=float, default=1.3394)
    parser.add_argument("--out", default="audit/outcome_stratification_results.json")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Running Attack-Outcome Stratified Evaluation on {args.ckpt}...")
    report = run_outcome_stratified_evaluation(
        args.ckpt, args.data, n_test=args.n_test, n_val=args.n_val, thr_fixed=args.thr, device=device
    )

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(report, f, indent=2)

    print("\n=======================================================")
    print(" ATTACK-OUTCOME STRATIFIED EVALUATION SUMMARY")
    print(f" Checkpoint: {report['checkpoint']}")
    print(f" Frozen Operating Threshold: {report['operating_threshold']:.4f}")
    print("=======================================================")
    print(f"{'Category':<28} {'Count':<7} {'% of Pos':<10} {'TPR @ tau':<12} {'95% CI':<20} {'Mean Score':<10} {'AUC vs Single':<12}")
    print("-" * 105)
    for cat, res in report["four_outcome_categories"].items():
        if res["n_samples"] > 0:
            ci_str = f"[{res['detection_rate_95_ci'][0]:.3f}, {res['detection_rate_95_ci'][1]:.3f}]"
            auc_str = f"{res['auc_vs_single_controls']:.3f}" if res['auc_vs_single_controls'] is not None else "N/A"
            print(f"{cat:<28} {res['n_samples']:<7} {res['percentage_of_attacks']:<10.1f} {res['detection_rate_fixed_thr']:<12.3f} {ci_str:<20} {res['mean_detector_score']:<10.3f} {auc_str:<12}")
    print("-" * 105)
    print(f"Recalculated Dual-Survival Rate: {report['dual_survival_rate_verified']['dual_survival_percentage']:.1f}%")
    print(f"Results saved to {args.out}")


if __name__ == "__main__":
    main()
