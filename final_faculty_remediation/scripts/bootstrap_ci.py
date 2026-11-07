"""Bootstrap confidence interval estimation for RW-Guard evaluation metrics.

Supports:
- ROC-AUC 95% percentile bootstrap CI
- TPR @ 1% FPR 95% CI
- TPR @ 0.1% FPR 95% CI
- Fixed-threshold TPR & FPR 95% CI
- Stratified source-aware or i.i.d. test resampling
"""

import argparse
import json
import os
import numpy as np
import torch

from rewm.metrics import roc_auc, tpr_at_fpr, rates_at, threshold_at_fpr, summarize
from rewm.data import list_images, split_paths, ReWMDataset
from rewm.model import build_model
from rewm.engine import predict
from torch.utils.data import DataLoader


def compute_bootstrap_cis(y_true, scores, thr=None, source_ids=None, n_bootstraps=2000, seed=42, alpha=0.05):
    """Compute empirical percentile bootstrap confidence intervals with source-image grouping.
    
    Args:
        y_true: 1D array of ground truth binary labels (0 or 1).
        scores: 1D array of continuous classifier logits/scores.
        thr: Operating threshold (fixed validation-calibrated threshold).
        source_ids: 1D array of source image IDs for grouped resampling (preserves paired dependencies).
        n_bootstraps: Number of bootstrap iterations (>= 2000 per faculty requirement).
        seed: Random seed for bootstrap generation.
        alpha: Significance level (default 0.05 for 95% CI).
        
    Returns:
        dict of metrics with point estimate, mean, std, and (lower, upper) CI bounds.
    """
    y_true = np.asarray(y_true)
    scores = np.asarray(scores)
    n = len(y_true)
    assert n == len(scores), f"Length mismatch: {n} vs {len(scores)}"

    if source_ids is None:
        # Default pairing assumption: sequential evaluation pairs even/odd indices to same source
        source_ids = np.array([i // 2 for i in range(n)])
    else:
        source_ids = np.asarray(source_ids)

    if thr is None:
        neg_scores = scores[y_true == 0]
        thr = threshold_at_fpr(neg_scores, 0.01)

    point_metrics = summarize(y_true, scores, thr)
    
    rng = np.random.default_rng(seed)
    boot_stats = {
        "auc": [],
        "tpr_at_1pct_fpr": [],      # Metric A: Test ROC-based TPR@1%FPR
        "tpr_at_0p1pct_fpr": [],    # Metric A: Test ROC-based TPR@0.1%FPR
        "tpr_fixed_thr": [],        # Metric B: Fixed validation threshold TPR
        "fpr_fixed_thr": []         # Metric B: Fixed validation threshold FPR
    }

    # Group sample indices by unique source image ID
    from collections import defaultdict
    source_to_indices = defaultdict(list)
    for idx, sid in enumerate(source_ids):
        source_to_indices[sid].append(idx)
    unique_sources = np.array(list(source_to_indices.keys()))
    n_sources = len(unique_sources)
    
    invalid_replicates = 0
    for _ in range(n_bootstraps):
        # Source-image-level resampling with replacement
        sampled_sources = rng.choice(unique_sources, size=n_sources, replace=True)
        b_idx = []
        for s in sampled_sources:
            b_idx.extend(source_to_indices[s])
        b_idx = np.array(b_idx, dtype=int)
        
        yb = y_true[b_idx]
        sb = scores[b_idx]
        
        # Check for single-class degeneracy
        if len(np.unique(yb)) < 2:
            invalid_replicates += 1
            continue
            
        try:
            auc = roc_auc(yb, sb)
        except Exception:
            auc = np.nan
            invalid_replicates += 1
            continue

        tpr1 = tpr_at_fpr(yb, sb, 0.01)
        tpr01 = tpr_at_fpr(yb, sb, 0.001)
        tpr_f, fpr_f = rates_at(yb, sb, thr)
        
        boot_stats["auc"].append(auc)
        boot_stats["tpr_at_1pct_fpr"].append(tpr1)
        boot_stats["tpr_at_0p1pct_fpr"].append(tpr01)
        boot_stats["tpr_fixed_thr"].append(tpr_f)
        boot_stats["fpr_fixed_thr"].append(fpr_f)
        
    lower_pct = 100.0 * (alpha / 2.0)
    upper_pct = 100.0 * (1.0 - alpha / 2.0)
    
    ci_results = {
        "threshold": float(thr),
        "n_samples": int(n),
        "n_unique_sources": int(n_sources),
        "n_bootstraps_requested": int(n_bootstraps),
        "n_bootstraps_valid": int(len(boot_stats["auc"])),
        "n_bootstraps_invalid": int(invalid_replicates),
        "metrics": {}
    }
    
    for metric_name, values in boot_stats.items():
        vals = np.array(values)
        vals = vals[~np.isnan(vals)]
        p_est = point_metrics.get(metric_name, float(np.mean(vals)))
        ci_low = float(np.percentile(vals, lower_pct))
        ci_high = float(np.percentile(vals, upper_pct))
        ci_results["metrics"][metric_name] = {
            "point_estimate": float(p_est),
            "bootstrap_mean": float(np.mean(vals)),
            "bootstrap_std": float(np.std(vals)),
            "ci_95": [ci_low, ci_high]
        }
        
    return ci_results


def evaluate_and_bootstrap(ckpt_path, data_dir, n_test=0, n_val=300, bs=32, n_bootstraps=1000, seed=42, device=None):
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
    ckpt = torch.load(ckpt_path, map_location=device)
    targs = ckpt["args"]
    model = build_model(targs["arch"], width=targs.get("width", 32)).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()
    
    seen = ckpt.get("train_schemes", ["dct_qim", "dwt_qim", "ss_spatial", "fft_ring"])
    paths = list_images(data_dir)
    _, va, te = split_paths(paths)
    va = va[:n_val]
    if n_test:
        te = te[:n_test]
        
    seen_kw = dict(victim_schemes=seen, attacker_schemes=seen, single_schemes=seen)
    
    # 1. Validation split for threshold selection
    v_ds = ReWMDataset(va, train=False, seed=777, size=256, benign_p=0.5, **seen_kw)
    v_dl = DataLoader(v_ds, batch_size=bs, shuffle=False, num_workers=0)
    sv, yv, _ = predict(model, v_dl, device)
    thr = threshold_at_fpr(sv[yv == 0], 0.01)
    
    # 2. Test split evaluation
    t_ds = ReWMDataset(te, train=False, seed=777, size=256, benign_p=0.5, **seen_kw)
    t_dl = DataLoader(t_ds, batch_size=bs, shuffle=False, num_workers=0)
    st, yt, _ = predict(model, t_dl, device)
    
    cis = compute_bootstrap_cis(yt, st, thr=thr, n_bootstraps=n_bootstraps, seed=seed)
    return cis, (yt, st, thr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ckpt", default="D:/projects/rewm-guard/runs/baseline_e9/best.pt")
    parser.add_argument("--data", default="D:/projects/rewm-guard/data/coco")
    parser.add_argument("--n-test", type=int, default=200, help="Number of test images to evaluate (0 for full)")
    parser.add_argument("--n-val", type=int, default=100)
    parser.add_argument("--bootstraps", type=int, default=1000)
    parser.add_argument("--out", default="audit/bootstrap_ci_results.json")
    args = parser.parse_args()
    
    print(f"Loading checkpoint {args.ckpt}...")
    cis, (yt, st, thr) = evaluate_and_bootstrap(
        args.ckpt, args.data, n_test=args.n_test, n_val=args.n_val, n_bootstraps=args.bootstraps
    )
    
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(cis, f, indent=2)
        
    print(f"\n=======================================================")
    print(f" Bootstrap 95% Confidence Intervals (N_boot={args.bootstraps})")
    print(f" Threshold (val 1% FPR): {cis['threshold']:.4f}")
    print(f"=======================================================")
    for m, vals in cis["metrics"].items():
        pe = vals["point_estimate"]
        ci = vals["ci_95"]
        print(f"  {m:20s}: {pe:.4f}  [95% CI: {ci[0]:.4f} - {ci[1]:.4f}]")
    print(f"Saved results to {args.out}")


if __name__ == "__main__":
    main()
