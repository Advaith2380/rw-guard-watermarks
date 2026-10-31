"""Seed Ensemble Experiment (Review 1 Reconciliation §4.8).

Evaluates individual seed checkpoints (seed0, seed1, seed2) versus a 3-model
ensemble on the COCO test split. Measures:
- Single model ROC-AUC, TPR@1% FPR, fixed-threshold TPR & FPR, latency
- Ensemble ROC-AUC, TPR@1% FPR, fixed-threshold TPR & FPR, latency
"""

import json
import os
import time
import numpy as np
import torch
from torch.utils.data import DataLoader

from rewm.data import ReWMDataset, list_images, split_paths
from rewm.metrics import summarize, roc_auc, threshold_at_fpr
from rewm.model import build_model


def eval_model(model, loader, device):
    model.eval()
    scores, labels = [], []
    t0 = time.time()
    with torch.no_grad():
        for batch in loader:
            x = batch["x"].to(device)
            y = batch["y"].numpy()
            logits = model(x).cpu().numpy()
            scores.extend(logits)
            labels.extend(y)
    elapsed = time.time() - t0
    return np.array(scores), np.array(labels), elapsed


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Running Seed Ensemble Experiment on device: {device}")

    data_dir = "D:/projects/rewm-guard/data/coco"
    paths = list_images(data_dir)
    _, val_paths, test_paths = split_paths(paths, seed=0)

    val_paths = val_paths[:100]
    test_paths = test_paths[:300]

    val_ds = ReWMDataset(val_paths, train=False, seed=0)
    test_ds = ReWMDataset(test_paths, train=False, seed=0)

    val_loader = DataLoader(val_ds, batch_size=32, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=32, shuffle=False)

    ckpt_paths = [
        "D:/projects/rewm-guard/runs/seed0/best.pt",
        "D:/projects/rewm-guard/runs/seed1/best.pt",
        "D:/projects/rewm-guard/runs/seed2/best.pt",
    ]

    models = []
    val_scores_list = []
    test_scores_list = []
    single_metrics = []

    for idx, cp in enumerate(ckpt_paths):
        print(f"Loading checkpoint {idx}: {cp}")
        state = torch.load(cp, map_location="cpu")
        weights = state["model"] if "model" in state else state
        m = build_model("forensic")
        m.load_state_dict(weights)
        m.to(device)
        models.append(m)

        # Val evaluation for threshold calibration
        v_scores, v_labels, _ = eval_model(m, val_loader, device)
        val_scores_list.append(v_scores)
        thr = threshold_at_fpr(v_scores[v_labels == 0], 0.01)

        # Test evaluation
        t_scores, t_labels, elapsed = eval_model(m, test_loader, device)
        test_scores_list.append(t_scores)

        rates = summarize(t_labels, t_scores, thr_fixed=thr)

        single_metrics.append({
            "seed": idx,
            "checkpoint": cp,
            "val_threshold_1pct": float(thr),
            "test_auc": float(rates["auc"]),
            "tpr_at_1pct_fpr": float(rates["tpr_at_1pct_fpr"]),
            "tpr_at_0p1pct_fpr": float(rates["tpr_at_0p1pct_fpr"]),
            "tpr_fixed_thr": float(rates["tpr_fixed_thr"]),
            "fpr_fixed_thr": float(rates["fpr_fixed_thr"]),
            "inference_time_sec": float(elapsed),
        })

    # Ensemble: Average logits
    val_ens_scores = np.mean(val_scores_list, axis=0)
    test_ens_scores = np.mean(test_scores_list, axis=0)

    ens_thr = threshold_at_fpr(val_ens_scores[v_labels == 0], 0.01)
    ens_rates = summarize(t_labels, test_ens_scores, thr_fixed=ens_thr)

    total_ens_time = sum(m["inference_time_sec"] for m in single_metrics)

    ensemble_metrics = {
        "ensemble_type": "Logit Mean of 3 Independently Trained Seeds",
        "val_threshold_1pct": float(ens_thr),
        "test_auc": float(ens_rates["auc"]),
        "tpr_at_1pct_fpr": float(ens_rates["tpr_at_1pct_fpr"]),
        "tpr_at_0p1pct_fpr": float(ens_rates["tpr_at_0p1pct_fpr"]),
        "tpr_fixed_thr": float(ens_rates["tpr_fixed_thr"]),
        "fpr_fixed_thr": float(ens_rates["fpr_fixed_thr"]),
        "inference_time_sec": float(total_ens_time),
        "latency_overhead_multiplier": 3.0,
    }

    report = {
        "n_test_samples": len(test_scores_list[0]),
        "single_models": single_metrics,
        "ensemble": ensemble_metrics,
        "comparison": {
            "mean_single_auc": float(np.mean([m["test_auc"] for m in single_metrics])),
            "ensemble_auc": float(ens_rates["auc"]),
            "auc_delta": float(ens_rates["auc"] - np.mean([m["test_auc"] for m in single_metrics])),
            "mean_single_tpr_at_1pct": float(np.mean([m["tpr_at_1pct_fpr"] for m in single_metrics])),
            "ensemble_tpr_at_1pct": float(ens_rates["tpr_at_1pct_fpr"]),
            "tpr_delta": float(ens_rates["tpr_at_1pct_fpr"] - np.mean([m["tpr_at_1pct_fpr"] for m in single_metrics])),
        }
    }

    print("\n=======================================================")
    print(" SEED ENSEMBLE EXPERIMENT RESULTS")
    print("=======================================================")
    for m in single_metrics:
        print(f"Seed {m['seed']}: AUC={m['test_auc']:.4f}, TPR@1%FPR={m['tpr_at_1pct_fpr']:.4f}, Fixed TPR={m['tpr_fixed_thr']:.4f}")
    print("-------------------------------------------------------")
    print(f"Ensemble (3 seeds): AUC={ens_rates['auc']:.4f}, TPR@1%FPR={ens_rates['tpr_at_1pct_fpr']:.4f}, Fixed TPR={ens_rates['tpr_fixed_thr']:.4f}")
    print(f"AUC Gain: {report['comparison']['auc_delta']:+.4f}, TPR@1% Gain: {report['comparison']['tpr_delta']:+.4f}")
    print(f"Inference Overhead: 3.0x")

    out_file = "audit/seed_ensemble_results.json"
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Saved results to {out_file}")


if __name__ == "__main__":
    main()
