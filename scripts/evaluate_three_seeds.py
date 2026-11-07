"""Independent Seven-Scheme Training Runs Evaluation (Faculty Review Section E / REQ-R).

Evaluates all three independently seeded 15-epoch seven-scheme training runs:
- Seed 0: runs/seed0/best.pt (Selected Primary Model)
- Seed 1: runs/seed1/best.pt
- Seed 2: runs/seed2/best.pt

Evaluates on the exact same held-out MS-COCO test split.
For each seed:
- Calibrates operating threshold tau on validation negatives targeting 1% nominal FPR.
- Evaluates test ROC-AUC, TPR@1%FPR, fixed-threshold TPR, and fixed-threshold FPR.
- Computes 95% bootstrap confidence intervals (2,000 source-grouped replicates).
- Computes multi-seed statistical summary: Mean, Standard Deviation, Range.
- Saves audit output to audit/seed_evaluation_results.json.
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
from rewm.engine import predict
from rewm.metrics import threshold_at_fpr, roc_auc, rates_at, tpr_at_fpr, summarize
from bootstrap_ci import compute_bootstrap_cis


def evaluate_seed_checkpoint(ckpt_path, seed_idx, te_paths, va_paths, seen_schemes, bs=32, device="cuda"):
    print(f"\n--- Evaluating Seed {seed_idx}: {ckpt_path} ---")
    ck = torch.load(ckpt_path, map_location=device, weights_only=False)
    targs = ck["args"]
    model = build_model(targs["arch"], targs.get("width", 32)).to(device)
    model.load_state_dict(ck["model"])
    model.eval()

    seen_kw = dict(victim_schemes=seen_schemes, attacker_schemes=seen_schemes, single_schemes=seen_schemes)

    # 1. Validation calibration
    v_ds = ReWMDataset(va_paths, train=False, seed=777, size=256, benign_p=0.5, **seen_kw)
    v_dl = DataLoader(v_ds, batch_size=bs, shuffle=False, num_workers=0)
    sv, yv, _ = predict(model, v_dl, device, desc=f"Seed {seed_idx} Val")
    thr = float(threshold_at_fpr(sv[yv == 0], 0.01))
    v_auc = float(roc_auc(yv, sv))
    print(f"  Val ROC-AUC: {v_auc:.4f}, Calibrated Threshold (1% FPR): {thr:.4f}")

    # 2. Test evaluation
    t_ds = ReWMDataset(te_paths, train=False, seed=777, size=256, benign_p=0.5, **seen_kw)
    t_dl = DataLoader(t_ds, batch_size=bs, shuffle=False, num_workers=0)
    st, yt, _ = predict(model, t_dl, device, desc=f"Seed {seed_idx} Test")

    m = summarize(yt, st, thr)
    sids = np.array([i // 2 for i in range(len(yt))])
    cis = compute_bootstrap_cis(yt, st, thr=thr, source_ids=sids, n_bootstraps=2000, seed=42)

    auc = m["auc"]
    tpr1 = m["tpr_at_1pct_fpr"]
    tpr_f = m["tpr_fixed_thr"]
    fpr_f = m["fpr_fixed_thr"]
    print(f"  Test ROC-AUC: {auc:.4f}, TPR@1%FPR: {tpr1:.4f}, Fixed-Thr TPR: {tpr_f:.4f}, FPR: {fpr_f:.4f}")

    return {
        "seed_index": seed_idx,
        "checkpoint_path": ckpt_path,
        "validation_auc": v_auc,
        "validation_threshold": thr,
        "test_metrics": m,
        "confidence_intervals": cis["metrics"],
        "scores": st,
        "labels": yt
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/coco")
    parser.add_argument("--n-test", type=int, default=500, help="Test source images (1000 derived samples)")
    parser.add_argument("--n-val", type=int, default=300)
    parser.add_argument("--out", default="audit/seed_evaluation_results.json")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Executing Multi-Seed Reproducibility Analysis on device: {device}...")

    paths = list_images(args.data)
    _, va, te = split_paths(paths, seed=0)
    va = va[: args.n_val]
    te = te[: args.n_test]

    ckpt_configs = [
        ("Seed 0 (Primary)", "runs/seed0/best.pt", 0),
        ("Seed 1", "runs/seed1/best.pt", 1),
        ("Seed 2", "runs/seed2/best.pt", 2)
    ]

    seen_schemes = ["dct_qim", "dwt_qim", "ss_spatial", "fft_ring", "nmp_freq", "svd_qim", "dct_svd"]

    seed_results = {}
    aucs, tpr1s, tpr_fixed_list, fpr_fixed_list = [], [], [], []

    for label, ckpt_p, s_idx in ckpt_configs:
        if not os.path.exists(ckpt_p):
            alt_p = os.path.join("D:/projects/rewm-guard", ckpt_p)
            if os.path.exists(alt_p):
                ckpt_p = alt_p
        res = evaluate_seed_checkpoint(ckpt_p, s_idx, te, va, seen_schemes, bs=32, device=device)
        # Exclude raw arrays from JSON dump
        res_to_save = {k: v for k, v in res.items() if k not in ("scores", "labels")}
        seed_results[label] = res_to_save
        
        aucs.append(res["test_metrics"]["auc"])
        tpr1s.append(res["test_metrics"]["tpr_at_1pct_fpr"])
        tpr_fixed_list.append(res["test_metrics"]["tpr_fixed_thr"])
        fpr_fixed_list.append(res["test_metrics"]["fpr_fixed_thr"])

    summary = {
        "n_seeds": len(ckpt_configs),
        "test_source_images": len(te),
        "test_sample_count": len(te) * 2,
        "metrics_summary": {
            "roc_auc": {
                "individual": [float(x) for x in aucs],
                "mean": float(np.mean(aucs)),
                "std": float(np.std(aucs)),
                "min": float(np.min(aucs)),
                "max": float(np.max(aucs)),
                "range": float(np.max(aucs) - np.min(aucs))
            },
            "tpr_at_1pct_fpr": {
                "individual": [float(x) for x in tpr1s],
                "mean": float(np.mean(tpr1s)),
                "std": float(np.std(tpr1s)),
                "range": float(np.max(tpr1s) - np.min(tpr1s))
            },
            "fixed_threshold_tpr": {
                "individual": [float(x) for x in tpr_fixed_list],
                "mean": float(np.mean(tpr_fixed_list)),
                "std": float(np.std(tpr_fixed_list)),
                "range": float(np.max(tpr_fixed_list) - np.min(tpr_fixed_list))
            },
            "fixed_threshold_fpr": {
                "individual": [float(x) for x in fpr_fixed_list],
                "mean": float(np.mean(fpr_fixed_list)),
                "std": float(np.std(fpr_fixed_list)),
                "range": float(np.max(fpr_fixed_list) - np.min(fpr_fixed_list))
            }
        },
        "individual_runs": seed_results
    }

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n=======================================================")
    print(" THREE INDEPENDENT SEEDS REPRODUCIBILITY SUMMARY")
    print(f" Test Set: {len(te)} source images ({len(te)*2} samples)")
    print("=======================================================")
    print(f"{'Seed':<20} {'ROC-AUC (95% CI)':<26} {'TPR@1%FPR (95% CI)':<26} {'TPR @ tau':<10} {'FPR @ tau':<10}")
    print("-" * 95)
    for label, res in seed_results.items():
        m = res["test_metrics"]
        ci_a = res["confidence_intervals"]["auc"]["ci_95"]
        ci_t = res["confidence_intervals"]["tpr_at_1pct_fpr"]["ci_95"]
        a_str = f"{m['auc']:.4f} [{ci_a[0]:.3f}, {ci_a[1]:.3f}]"
        t_str = f"{m['tpr_at_1pct_fpr']:.4f} [{ci_t[0]:.3f}, {ci_t[1]:.3f}]"
        print(f"{label:<20} {a_str:<26} {t_str:<26} {m['tpr_fixed_thr']:<10.3f} {m['fpr_fixed_thr']:<10.3f}")
    print("-" * 95)
    s_auc = summary["metrics_summary"]["roc_auc"]
    s_tpr = summary["metrics_summary"]["tpr_at_1pct_fpr"]
    print(f"Seed Mean +/- Std:  AUC = {s_auc['mean']:.4f} +/- {s_auc['std']:.4f} (range: {s_auc['range']:.4f})")
    print(f"                    TPR@1%FPR = {s_tpr['mean']:.4f} +/- {s_tpr['std']:.4f} (range: {s_tpr['range']:.4f})")
    print(f"Saved results to {args.out}")


if __name__ == "__main__":
    main()
