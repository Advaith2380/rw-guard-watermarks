"""TrustMark Neural-Watermarker Generalization Evaluation (Faculty Review Section C / REQ-I, REQ-J).

Evaluates:
1. Primary Frozen 7-Scheme Model (checkpoints/final/rwguard_final_7scheme.pt) - True Zero-Shot Generalization
   (Evaluated at both frozen validation threshold tau=1.3394 and domain-calibrated threshold).
2. Supervised Adapted Model (runs/trustmark_mix/best.pt) - Supervised Transfer Benchmark
   (Trained with 15% TrustMark cache exposure).
3. Historical Baseline (runs/baseline_e9/best.pt) - 4-Scheme Benchmark for Traceability.

Uses verified stratified TrustMark cache (singly-watermarked negatives, doubly-watermarked positives, clean controls).
Computes 95% bootstrap confidence intervals (2,000 replicates) with paired source-image grouping.
Reconciles all historical TrustMark results (0.534 stratified zero-shot vs 0.696 unstratified; 0.851 adapted vs 0.925).
"""

import argparse
import json
import os
import sys
sys.path.insert(0, os.path.abspath("."))
import numpy as np
import torch
from torch.utils.data import DataLoader

from rewm_trustmark import TrustMarkCacheDataset
from rewm.model import build_model
from rewm.engine import predict
from rewm.metrics import threshold_at_fpr, roc_auc, rates_at, tpr_at_fpr, summarize
from bootstrap_ci import compute_bootstrap_cis


def evaluate_trustmark_model(ckpt_path, cache_dir, frozen_thr=1.3394, split="val", device="cuda"):
    print(f"\nEvaluating TrustMark on {ckpt_path} (split={split})...")
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    targs = ckpt["args"]
    model = build_model(targs["arch"], width=targs.get("width", 32)).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()

    ds = TrustMarkCacheDataset(cache_dir, split=split, train=False, seed=42)
    dl = DataLoader(ds, batch_size=32, shuffle=False, num_workers=0)
    
    scores, labels, kinds = predict(model, dl, device, desc="TrustMark Eval")
    
    neg_scores = scores[labels == 0]
    pos_scores = scores[labels == 1]
    domain_thr = float(threshold_at_fpr(neg_scores, 0.01))
    
    # 1. Performance at frozen validation threshold (from classical COCO validation)
    m_frozen = summarize(labels, scores, frozen_thr)
    sids = np.array([i // 2 for i in range(len(labels))])
    ci_frozen = compute_bootstrap_cis(labels, scores, thr=frozen_thr, source_ids=sids, n_bootstraps=2000, seed=42)
    
    # 2. Performance at domain-recalibrated threshold (1% FPR on TrustMark negatives)
    m_recal = summarize(labels, scores, domain_thr)
    ci_recal = compute_bootstrap_cis(labels, scores, thr=domain_thr, source_ids=sids, n_bootstraps=2000, seed=42)

    # Stratified breakdown by kind
    kinds_arr = np.array(kinds)
    kind_stats = {}
    for k in sorted(set(kinds)):
        mask = (kinds_arr == k)
        k_scores = scores[mask]
        kind_stats[k] = {
            "n": int(np.sum(mask)),
            "flagged_rate_frozen_thr": float(np.mean(k_scores > frozen_thr)),
            "flagged_rate_recal_thr": float(np.mean(k_scores > domain_thr)),
            "mean_score": float(np.mean(k_scores)),
            "std_score": float(np.std(k_scores)),
            "median_score": float(np.median(k_scores))
        }

    return {
        "checkpoint": ckpt_path,
        "n_samples": len(labels),
        "n_positives": int(len(pos_scores)),
        "n_negatives": int(len(neg_scores)),
        "frozen_validation_threshold": float(frozen_thr),
        "domain_recalibrated_threshold": float(domain_thr),
        "metrics_at_frozen_threshold": m_frozen,
        "confidence_intervals_frozen_thr": ci_frozen["metrics"],
        "metrics_at_recalibrated_threshold": m_recal,
        "confidence_intervals_recal_thr": ci_recal["metrics"],
        "kind_breakdown": kind_stats
    }


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    cache_dir = "data/trustmark_cache"
    if not os.path.exists(cache_dir) and os.path.exists("D:/projects/rewm-guard/data/trustmark_cache"):
        cache_dir = "D:/projects/rewm-guard/data/trustmark_cache"
        
    results = {
        "protocol_documentation": {
            "evaluation_type": "Stratified TrustMark Evaluation (Bui et al. ICCV 2025)",
            "negative_controls": "50% clean original photographs, 50% single-watermarked TrustMark images",
            "positive_samples": "100% sequential double TrustMark embeddings",
            "historical_reconciliation": {
                "zero_shot_stratified_auc": 0.5344,
                "zero_shot_unstratified_auc": 0.6960,
                "supervised_adapted_auc_15pct": 0.8505,
                "supervised_adapted_auc_earlier": 0.9250,
                "explanation": "Unstratified test evaluated only clean vs double watermarks (ignoring single watermarks as negatives), artificially inflating AUC to 0.696. Stratified negative controls correctly include single watermarks, revealing true zero-shot AUC is 0.534 (near random ranking). Supervised adaptation with 15% TrustMark exposure restores AUC to 0.851."
            }
        },
        "experiments": {}
    }

    # 1. Primary Model (Frozen 7-Scheme) Zero-Shot
    primary_ckpt = "checkpoints/final/rwguard_final_7scheme.pt"
    if os.path.exists(primary_ckpt):
        print("\n=======================================================")
        print(" [PRIMARY] ZERO-SHOT TRUSTMARK GENERALIZATION (7-SCHEME)")
        print("=======================================================")
        results["experiments"]["primary_7scheme_zero_shot"] = evaluate_trustmark_model(
            primary_ckpt, cache_dir, frozen_thr=1.3394, split="val", device=device
        )

    # 2. Supervised Adapted Model
    adapted_ckpt = "runs/trustmark_mix/best.pt"
    if not os.path.exists(adapted_ckpt):
        adapted_ckpt = "D:/projects/rewm-guard/runs/trustmark_mix/best.pt"
    if os.path.exists(adapted_ckpt):
        print("\n=======================================================")
        print(" [ADAPTED] SUPERVISED ADAPTATION BENCHMARK (15% EXPOSURE)")
        print("=======================================================")
        results["experiments"]["supervised_adapted_15pct"] = evaluate_trustmark_model(
            adapted_ckpt, cache_dir, frozen_thr=1.3394, split="val", device=device
        )

    # 3. Historical 4-Scheme Baseline for Comparison
    hist_ckpt = "runs/baseline_e9/best.pt"
    if not os.path.exists(hist_ckpt):
        hist_ckpt = "D:/projects/rewm-guard/runs/baseline_e9/best.pt"
    if os.path.exists(hist_ckpt):
        print("\n=======================================================")
        print(" [HISTORICAL] 4-SCHEME BASELINE ZERO-SHOT (BASELINE_E9)")
        print("=======================================================")
        results["experiments"]["historical_4scheme_zero_shot"] = evaluate_trustmark_model(
            hist_ckpt, cache_dir, frozen_thr=1.1413, split="val", device=device
        )

    os.makedirs("audit", exist_ok=True)
    out_file = "audit/trustmark_evaluation_results.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print("\n=======================================================")
    print(" TRUSTMARK EVALUATION SUMMARY TABLE")
    print("=======================================================")
    print(f"{'Condition':<30} {'ROC-AUC (95% CI)':<26} {'TPR@1%FPR':<11} {'TPR @ tau':<11} {'FPR @ tau':<11}")
    print("-" * 90)
    for exp_name, exp_res in results["experiments"].items():
        m = exp_res["metrics_at_frozen_threshold"]
        ci = exp_res["confidence_intervals_frozen_thr"]["auc"]["ci_95"]
        ci_str = f"{m['auc']:.4f} [{ci[0]:.3f}, {ci[1]:.3f}]"
        print(f"{exp_name:<30} {ci_str:<26} {m['tpr_at_1pct_fpr']:<11.4f} {m['tpr_fixed_thr']:<11.4f} {m['fpr_fixed_thr']:<11.4f}")
    print("-" * 90)
    print(f"Results saved to {out_file}")


if __name__ == "__main__":
    main()
