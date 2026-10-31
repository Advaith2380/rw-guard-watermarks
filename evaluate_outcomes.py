"""Evaluate detector performance stratified by attack outcome (REQ-C, REQ-D).

Distinguishes:
1. Successful overwrite (victim bit-acc < 0.75, attacker bit-acc >= 0.75)
2. Dual survival / ambiguity (both bit-acc >= 0.75)
3. Failed attack (attacker bit-acc < 0.75)
4. Singly-watermarked controls (single:<scheme>)
5. Clean unwatermarked controls (clean)
"""

import argparse
import json
import os
import numpy as np
import torch
from torch.utils.data import DataLoader

from rewm.data import list_images, split_paths, ReWMDataset
from rewm.model import build_model
from rewm.engine import predict_with_outcomes
from rewm.metrics import threshold_at_fpr, roc_auc, rates_at, tpr_at_fpr, summarize
from bootstrap_ci import compute_bootstrap_cis


def run_outcome_stratified_evaluation(ckpt_path, data_dir, n_test=300, n_val=150, bs=32, device="cuda"):
    ckpt = torch.load(ckpt_path, map_location=device)
    targs = ckpt["args"]
    model = build_model(targs["arch"], width=targs.get("width", 32)).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()

    seen = ckpt.get("train_schemes", ["dct_qim", "dwt_qim", "ss_spatial", "fft_ring"])
    paths = list_images(data_dir)
    _, va, te = split_paths(paths, seed=0)
    va = va[:n_val]
    if n_test:
        te = te[:n_test]

    seen_kw = dict(victim_schemes=seen, attacker_schemes=seen, single_schemes=seen)

    # 1. Validation split for threshold selection
    v_ds = ReWMDataset(va, train=False, seed=777, size=256, benign_p=0.5, **seen_kw)
    v_dl = DataLoader(v_ds, batch_size=bs, shuffle=False, num_workers=0)
    sv, yv, _, _ = predict_with_outcomes(model, v_dl, device, desc="val (thr)")
    thr = threshold_at_fpr(sv[yv == 0], 0.01)

    # 2. Test split with outcome tracking
    t_ds = ReWMDataset(te, train=False, seed=777, size=256, benign_p=0.5, track_outcomes=True, **seen_kw)
    t_dl = DataLoader(t_ds, batch_size=bs, shuffle=False, num_workers=0)
    st, yt, kinds, outcomes = predict_with_outcomes(model, t_dl, device, desc="test (outcomes)")

    # Overall in-distribution metrics
    overall_m = summarize(yt, st, thr)
    overall_ci = compute_bootstrap_cis(yt, st, thr=thr, n_bootstraps=500, seed=42)

    # Stratified breakdown by attack outcome
    unique_outcomes = sorted(list(set(outcomes)))
    outcome_stats = {}
    for oc in unique_outcomes:
        mask = (outcomes == oc)
        count = int(np.sum(mask))
        if count == 0:
            continue
        oc_scores = st[mask]
        flagged_rate = float(np.mean(oc_scores > thr))
        mean_score = float(np.mean(oc_scores))
        std_score = float(np.std(oc_scores))
        
        # If positive outcome, compute detection TPR
        outcome_stats[oc] = {
            "n": count,
            "flagged_rate": flagged_rate,
            "mean_score": mean_score,
            "std_score": std_score
        }

    # Stratified breakdown by sample kind (clean vs single:X vs A>B)
    unique_kinds = sorted(list(set(kinds)))
    kind_stats = {}
    for k in unique_kinds:
        mask = (kinds == k)
        count = int(np.sum(mask))
        if count == 0:
            continue
        k_scores = st[mask]
        flagged_rate = float(np.mean(k_scores > thr))
        kind_stats[k] = {
            "n": count,
            "flagged_rate": flagged_rate,
            "mean_score": float(np.mean(k_scores))
        }

    report = {
        "checkpoint": ckpt_path,
        "operating_threshold": float(thr),
        "overall_metrics": overall_m,
        "confidence_intervals": overall_ci["metrics"],
        "outcome_stratification": outcome_stats,
        "kind_stratification": kind_stats
    }
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ckpt", default="D:/projects/rewm-guard/runs/baseline_e9/best.pt")
    parser.add_argument("--data", default="D:/projects/rewm-guard/data/coco")
    parser.add_argument("--n-test", type=int, default=300)
    parser.add_argument("--n-val", type=int, default=150)
    parser.add_argument("--out", default="audit/outcome_stratification_results.json")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Running Outcome Stratification on {device} with {args.ckpt}...")
    report = run_outcome_stratified_evaluation(args.ckpt, args.data, n_test=args.n_test, n_val=args.n_val, device=device)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(report, f, indent=2)

    print("\n=======================================================")
    print(" ATTACK OUTCOME STRATIFICATION RESULTS")
    print(f" Operating Threshold (val 1% FPR): {report['operating_threshold']:.4f}")
    print("=======================================================")
    print(f"{'Outcome Category':24s} {'Count':>6s} {'Flagged Rate':>14s} {'Mean Score':>12s}")
    print("-" * 60)
    for oc, stats in report["outcome_stratification"].items():
        print(f"{oc:24s} {stats['n']:6d} {stats['flagged_rate']:13.3f} {stats['mean_score']:12.3f}")

    print("\nSaved report to", args.out)


if __name__ == "__main__":
    main()
