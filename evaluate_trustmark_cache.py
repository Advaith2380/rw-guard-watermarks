"""Evaluate zero-shot and supervised adapted detection performance on real TrustMark watermarks.

Uses the verified precomputed TrustMark cache (REQ-I, REQ-J).
"""

import json
import os
import numpy as np
import torch
from torch.utils.data import DataLoader

from rewm_trustmark import TrustMarkCacheDataset
from rewm.model import build_model
from rewm.engine import predict
from rewm.metrics import threshold_at_fpr, roc_auc, rates_at, tpr_at_fpr, summarize
from bootstrap_ci import compute_bootstrap_cis


def evaluate_trustmark(ckpt_path, cache_dir, device="cuda"):
    ckpt = torch.load(ckpt_path, map_location=device)
    targs = ckpt["args"]
    model = build_model(targs["arch"], width=targs.get("width", 32)).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()

    # Val cache: 100 images => 200 samples (100 pos, 100 neg)
    ds_val = TrustMarkCacheDataset(cache_dir, split="val", train=False, seed=42)
    dl_val = DataLoader(ds_val, batch_size=32, shuffle=False)
    
    scores, labels, kinds = predict(model, dl_val, device, desc="TrustMark eval")
    
    # Validation threshold targeting 1% nominal FPR on negative cache
    neg_scores = scores[labels == 0]
    thr = float(threshold_at_fpr(neg_scores, 0.01))
    
    m = summarize(labels, scores, thr)
    cis = compute_bootstrap_cis(labels, scores, thr=thr, n_bootstraps=500, seed=42)
    
    # Breakdown by kind
    kinds_arr = np.array(kinds)
    kind_breakdown = {}
    for k in sorted(set(kinds)):
        mask = (kinds_arr == k)
        k_scores = scores[mask]
        kind_breakdown[k] = {
            "n": int(np.sum(mask)),
            "flagged_rate": float(np.mean(k_scores > thr)),
            "mean_score": float(np.mean(k_scores))
        }
        
    return {
        "checkpoint": ckpt_path,
        "n_samples": len(labels),
        "threshold_1pct_val": thr,
        "metrics": m,
        "confidence_intervals": cis["metrics"],
        "breakdown": kind_breakdown
    }


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    cache_dir = "D:/projects/rewm-guard/data/trustmark_cache"
    
    results = {}
    
    # 1. Zero-shot evaluation with baseline_e9 (never saw TrustMark in training)
    baseline_ckpt = "D:/projects/rewm-guard/runs/baseline_e9/best.pt"
    if os.path.exists(baseline_ckpt):
        print("\n--- Evaluating Zero-Shot TrustMark Detection (baseline_e9) ---")
        results["zero_shot_baseline_e9"] = evaluate_trustmark(baseline_ckpt, cache_dir, device=device)
        m0 = results["zero_shot_baseline_e9"]["metrics"]
        ci0 = results["zero_shot_baseline_e9"]["confidence_intervals"]["auc"]["ci_95"]
        print(f"Zero-Shot TrustMark ROC-AUC: {m0['auc']:.4f} [95% CI: {ci0[0]:.4f} - {ci0[1]:.4f}]")
        print(f"Zero-Shot TPR @ 1% FPR:      {m0['tpr_at_1pct_fpr']:.4f}")
        
    # 2. Supervised adapted evaluation with trustmark_mix (trained with TrustMark examples)
    mix_ckpt = "D:/projects/rewm-guard/runs/trustmark_mix/best.pt"
    if os.path.exists(mix_ckpt):
        print("\n--- Evaluating Supervised-Adapted TrustMark Detection (trustmark_mix) ---")
        results["supervised_adapted_trustmark_mix"] = evaluate_trustmark(mix_ckpt, cache_dir, device=device)
        m1 = results["supervised_adapted_trustmark_mix"]["metrics"]
        ci1 = results["supervised_adapted_trustmark_mix"]["confidence_intervals"]["auc"]["ci_95"]
        print(f"Supervised Adapted TrustMark ROC-AUC: {m1['auc']:.4f} [95% CI: {ci1[0]:.4f} - {ci1[1]:.4f}]")
        print(f"Supervised Adapted TPR @ 1% FPR:      {m1['tpr_at_1pct_fpr']:.4f}")

    os.makedirs("audit", exist_ok=True)
    out_file = "audit/trustmark_evaluation_results.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved TrustMark evaluation results to {out_file}")


if __name__ == "__main__":
    main()
