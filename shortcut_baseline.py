"""Shortcut Learning Baselines: Residual-Energy & Spectral Features (Faculty Review Section B / REQ-G).

Investigates whether ForensicNet's detection performance is explainable by aggregate
residual-energy, roughness, or spectral frequency distribution statistics rather than
genuine re-watermarking forensic signatures.

Compares under identical train/val/test splits:
1. Logistic Regression (Linear aggregate baseline)
2. Random Forest (Nonlinear tree ensemble baseline)
3. RW-Guard Frozen Seven-Scheme Model (ForensicNet)

Implements:
- 10 residual & spectral features (HP mean/var/RGB energy, Laplacian energy/var, FFT high-freq ratio, local variance).
- Feature standardization (fit on train, applied to val and test).
- Validation-only hyperparameter tuning for Random Forest.
- Operating threshold calibrated on validation negatives targeting 1% nominal FPR.
- Grouped paired source-image bootstrap analysis (2,000 replicates).
- Paired differences (Delta AUC, Delta TPR@1%FPR) with 95% bootstrap confidence intervals.
"""

import argparse
import json
import os
import sys
sys.path.insert(0, os.path.abspath("."))
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from rewm.data import list_images, split_paths, ReWMDataset
from rewm.model import build_model
from rewm.engine import predict
from rewm.metrics import roc_auc, tpr_at_fpr, rates_at, threshold_at_fpr, summarize
from bootstrap_ci import compute_bootstrap_cis


# Fixed High-Pass filter kernel matching ForensicNet's 3x3 HP kernel
HP_KERNEL_2D = torch.tensor([
    [-1.0, -1.0, -1.0],
    [-1.0,  8.0, -1.0],
    [-1.0, -1.0, -1.0]
], dtype=torch.float32) / 8.0

LAPLACIAN_KERNEL_2D = torch.tensor([
    [0.0,  1.0, 0.0],
    [1.0, -4.0, 1.0],
    [0.0,  1.0, 0.0]
], dtype=torch.float32)


def extract_batch_features(x_tensor):
    """Extract 10 residual energy and frequency domain features from a batch of RGB tensors (B, 3, H, W)."""
    B, C, H, W = x_tensor.shape
    device = x_tensor.device
    
    # 1. Grayscale luminance
    weights = torch.tensor([0.2989, 0.5870, 0.1140], device=device).view(1, 3, 1, 1)
    gray = torch.sum(x_tensor * weights, dim=1, keepdim=True)
    
    # 2. High-pass residual features
    hp_k = HP_KERNEL_2D.view(1, 1, 3, 3).to(device)
    hp_gray = F.conv2d(gray, hp_k, padding=1)
    
    hp_k_rgb = HP_KERNEL_2D.view(1, 1, 3, 3).repeat(3, 1, 1, 1).to(device)
    hp_rgb = F.conv2d(x_tensor, hp_k_rgb, padding=1, groups=3)
    
    hp_mean_abs = torch.mean(torch.abs(hp_gray), dim=(1, 2, 3))
    hp_var = torch.var(hp_gray, dim=(1, 2, 3))
    hp_energy = torch.mean(hp_gray ** 2, dim=(1, 2, 3))
    hp_r_energy = torch.mean(hp_rgb[:, 0, :, :] ** 2, dim=(1, 2))
    hp_g_energy = torch.mean(hp_rgb[:, 1, :, :] ** 2, dim=(1, 2))
    hp_b_energy = torch.mean(hp_rgb[:, 2, :, :] ** 2, dim=(1, 2))
    
    # 3. Laplacian roughness energy
    lap_k = LAPLACIAN_KERNEL_2D.view(1, 1, 3, 3).to(device)
    lap = F.conv2d(gray, lap_k, padding=1)
    lap_energy = torch.mean(lap ** 2, dim=(1, 2, 3))
    lap_var = torch.var(lap, dim=(1, 2, 3))
    
    # 4. 2D FFT spectral high-frequency ratio
    fft2 = torch.fft.fft2(gray.squeeze(1))
    fft_shifted = torch.fft.fftshift(fft2, dim=(-2, -1))
    mag_sq = torch.abs(fft_shifted) ** 2
    
    cy, cx = H // 2, W // 2
    y_coords = torch.arange(H, device=device).view(-1, 1).repeat(1, W)
    x_coords = torch.arange(W, device=device).view(1, -1).repeat(H, 1)
    dist_sq = (y_coords - cy) ** 2 + (x_coords - cx) ** 2
    radius_cutoff_sq = (min(H, W) * 0.25) ** 2
    
    high_freq_mask = dist_sq > radius_cutoff_sq
    high_freq_energy = torch.sum(mag_sq * high_freq_mask.unsqueeze(0), dim=(-2, -1))
    total_fft_energy = torch.sum(mag_sq, dim=(-2, -1)) + 1e-10
    hf_fft_ratio = high_freq_energy / total_fft_energy
    
    # 5. Local variance contrast
    local_mean = F.avg_pool2d(gray, kernel_size=5, stride=1, padding=2)
    local_sq_mean = F.avg_pool2d(gray ** 2, kernel_size=5, stride=1, padding=2)
    local_var = torch.mean(torch.clamp(local_sq_mean - local_mean ** 2, min=0.0), dim=(1, 2, 3))
    
    features = torch.stack([
        hp_mean_abs,
        hp_var,
        hp_energy,
        hp_r_energy,
        hp_g_energy,
        hp_b_energy,
        lap_energy,
        lap_var,
        hf_fft_ratio,
        local_var
    ], dim=1)
    return features


def collect_features_from_dataset(dataset, batch_size=32, device="cuda"):
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    all_feats, all_labels = [], []
    with torch.no_grad():
        for batch in loader:
            x = batch["x"].to(device)
            y = batch["y"].to(device)
            feats = extract_batch_features(x)
            all_feats.append(feats.cpu())
            all_labels.append(y.cpu())
    X = torch.cat(all_feats, dim=0).numpy()
    Y = torch.cat(all_labels, dim=0).numpy()
    return X, Y


class TorchLogisticRegression(nn.Module):
    def __init__(self, in_features=10):
        super().__init__()
        self.linear = nn.Linear(in_features, 1)
        
    def forward(self, x):
        return self.linear(x).squeeze(1)
        
    def fit(self, X, y, lr=0.05, weight_decay=1e-3, epochs=400):
        X_t = torch.tensor(X, dtype=torch.float32)
        y_t = torch.tensor(y, dtype=torch.float32)
        optimizer = torch.optim.AdamW(self.parameters(), lr=lr, weight_decay=weight_decay)
        criterion = nn.BCEWithLogitsLoss()
        self.train()
        for _ in range(epochs):
            optimizer.zero_grad()
            logits = self(X_t)
            loss = criterion(logits, y_t)
            loss.backward()
            optimizer.step()
            
    def predict_logits(self, X):
        self.eval()
        with torch.no_grad():
            return self(torch.tensor(X, dtype=torch.float32)).numpy()


def run_shortcut_experiments(ckpt_path, data_dir, n_train=1000, n_val=300, n_test=500, device="cuda"):
    print("Loading data splits for shortcut-learning experiments...")
    paths = list_images(data_dir)
    tr_paths, va_paths, te_paths = split_paths(paths, seed=0)
    tr_paths = tr_paths[:n_train]
    va_paths = va_paths[:n_val]
    te_paths = te_paths[:n_test]

    seen = ["dct_qim", "dwt_qim", "ss_spatial", "fft_ring", "nmp_freq", "svd_qim", "dct_svd"]
    seen_kw = dict(victim_schemes=seen, attacker_schemes=seen, single_schemes=seen)

    print(f"Dataset sizes: Train {len(tr_paths)}, Val {len(va_paths)}, Test {len(te_paths)} source images.")
    ds_tr = ReWMDataset(tr_paths, train=False, seed=42, size=256, benign_p=0.5, **seen_kw)
    ds_va = ReWMDataset(va_paths, train=False, seed=777, size=256, benign_p=0.5, **seen_kw)
    ds_te = ReWMDataset(te_paths, train=False, seed=888, size=256, benign_p=0.5, **seen_kw)

    print("Extracting 10 residual & spectral features from train split...")
    X_tr, Y_tr = collect_features_from_dataset(ds_tr, batch_size=32, device=device)
    print("Extracting features from validation split...")
    X_va, Y_va = collect_features_from_dataset(ds_va, batch_size=32, device=device)
    print("Extracting features from test split...")
    X_te, Y_te = collect_features_from_dataset(ds_te, batch_size=32, device=device)

    # Standardize
    scaler = StandardScaler()
    X_tr_norm = scaler.fit_transform(X_tr)
    X_va_norm = scaler.transform(X_va)
    X_te_norm = scaler.transform(X_te)

    # 1. Logistic Regression
    print("\nTraining Logistic Regression baseline...")
    lr_model = TorchLogisticRegression(in_features=10)
    lr_model.fit(X_tr_norm, Y_tr)
    s_va_lr = lr_model.predict_logits(X_va_norm)
    thr_lr = float(threshold_at_fpr(s_va_lr[Y_va == 0], 0.01))
    s_te_lr = lr_model.predict_logits(X_te_norm)

    # 2. Random Forest (hyperparameter tuning on validation only)
    print("\nTuning Random Forest on validation split...")
    best_rf = None
    best_va_auc = -1.0
    best_params = {}
    for n_est in [100, 200]:
        for max_d in [4, 6, 8, None]:
            for min_split in [2, 5]:
                rf = RandomForestClassifier(
                    n_estimators=n_est, max_depth=max_d, min_samples_split=min_split,
                    random_state=42, n_jobs=-1
                )
                rf.fit(X_tr_norm, Y_tr)
                s_va = rf.predict_proba(X_va_norm)[:, 1]
                v_auc = roc_auc(Y_va, s_va)
                if v_auc > best_va_auc:
                    best_va_auc = v_auc
                    best_rf = rf
                    best_params = {"n_estimators": n_est, "max_depth": max_d, "min_samples_split": min_split}
    
    print(f"Best Random Forest: {best_params} (Val AUC: {best_va_auc:.4f})")
    s_va_rf = best_rf.predict_proba(X_va_norm)[:, 1]
    thr_rf = float(threshold_at_fpr(s_va_rf[Y_va == 0], 0.01))
    s_te_rf = best_rf.predict_proba(X_te_norm)[:, 1]

    # 3. RW-Guard Frozen Primary Model predictions on exact same test set
    print(f"\nEvaluating frozen RW-Guard model ({ckpt_path}) on exact same test set...")
    ck = torch.load(ckpt_path, map_location=device, weights_only=False)
    targs = ck["args"]
    rwg_model = build_model(targs["arch"], targs.get("width", 32)).to(device)
    rwg_model.load_state_dict(ck["model"])
    rwg_model.eval()

    dl_te = DataLoader(ds_te, batch_size=32, shuffle=False, num_workers=0)
    s_te_rwg, _, _ = predict(rwg_model, dl_te, device, desc="RW-Guard Test")
    
    # Frozen validation threshold
    dl_va = DataLoader(ds_va, batch_size=32, shuffle=False, num_workers=0)
    s_va_rwg, _, _ = predict(rwg_model, dl_va, device, desc="RW-Guard Val")
    thr_rwg = float(threshold_at_fpr(s_va_rwg[Y_va == 0], 0.01))

    # Evaluate all 3 models with grouped bootstrap (2,000 replicates)
    sids = np.array([i // 2 for i in range(len(Y_te))])
    
    ci_lr = compute_bootstrap_cis(Y_te, s_te_lr, thr=thr_lr, source_ids=sids, n_bootstraps=2000, seed=42)
    ci_rf = compute_bootstrap_cis(Y_te, s_te_rf, thr=thr_rf, source_ids=sids, n_bootstraps=2000, seed=42)
    ci_rwg = compute_bootstrap_cis(Y_te, s_te_rwg, thr=thr_rwg, source_ids=sids, n_bootstraps=2000, seed=42)

    # Paired Bootstrap Differences: RWG - LR and RWG - RF
    print("Computing paired bootstrap differences (2,000 replicates)...")
    from collections import defaultdict
    s_to_idx = defaultdict(list)
    for idx, sid in enumerate(sids):
        s_to_idx[sid].append(idx)
    u_sids = np.array(list(s_to_idx.keys()))
    n_s = len(u_sids)

    delta_auc_lr, delta_tpr_lr = [], []
    delta_auc_rf, delta_tpr_rf = [], []
    rng_p = np.random.default_rng(42)

    for _ in range(2000):
        sampled_u = rng_p.choice(u_sids, size=n_s, replace=True)
        b_idx = [idx for su in sampled_u for idx in s_to_idx[su]]
        yb = Y_te[b_idx]
        if len(np.unique(yb)) < 2:
            continue
        
        auc_rwg = roc_auc(yb, s_te_rwg[b_idx])
        auc_lr = roc_auc(yb, s_te_lr[b_idx])
        auc_rf = roc_auc(yb, s_te_rf[b_idx])

        tpr_rwg = tpr_at_fpr(yb, s_te_rwg[b_idx], 0.01)
        tpr_lr = tpr_at_fpr(yb, s_te_lr[b_idx], 0.01)
        tpr_rf = tpr_at_fpr(yb, s_te_rf[b_idx], 0.01)

        delta_auc_lr.append(auc_rwg - auc_lr)
        delta_tpr_lr.append(tpr_rwg - tpr_lr)
        delta_auc_rf.append(auc_rwg - auc_rf)
        delta_tpr_rf.append(tpr_rwg - tpr_rf)

    paired_stats = {
        "rwguard_minus_logistic_regression": {
            "delta_auc_mean": float(np.mean(delta_auc_lr)),
            "delta_auc_ci_95": [float(np.percentile(delta_auc_lr, 2.5)), float(np.percentile(delta_auc_lr, 97.5))],
            "delta_tpr_at_1pct_mean": float(np.mean(delta_tpr_lr)),
            "delta_tpr_at_1pct_ci_95": [float(np.percentile(delta_tpr_lr, 2.5)), float(np.percentile(delta_tpr_lr, 97.5))]
        },
        "rwguard_minus_random_forest": {
            "delta_auc_mean": float(np.mean(delta_auc_rf)),
            "delta_auc_ci_95": [float(np.percentile(delta_auc_rf, 2.5)), float(np.percentile(delta_auc_rf, 97.5))],
            "delta_tpr_at_1pct_mean": float(np.mean(delta_tpr_rf)),
            "delta_tpr_at_1pct_ci_95": [float(np.percentile(delta_tpr_rf, 2.5)), float(np.percentile(delta_tpr_rf, 97.5))]
        }
    }

    report = {
        "checkpoint": ckpt_path,
        "n_test_samples": len(Y_te),
        "n_source_images": len(te_paths),
        "features": [
            "hp_mean_abs", "hp_var", "hp_energy", "hp_r_energy", "hp_g_energy",
            "hp_b_energy", "lap_energy", "lap_var", "hf_fft_ratio", "local_var"
        ],
        "models": {
            "logistic_regression": {
                "val_threshold": thr_lr,
                "metrics": summarize(Y_te, s_te_lr, thr_lr),
                "confidence_intervals": ci_lr["metrics"]
            },
            "random_forest": {
                "best_hyperparameters": best_params,
                "val_threshold": thr_rf,
                "metrics": summarize(Y_te, s_te_rf, thr_rf),
                "confidence_intervals": ci_rf["metrics"]
            },
            "rwguard_frozen_7scheme": {
                "val_threshold": thr_rwg,
                "metrics": summarize(Y_te, s_te_rwg, thr_rwg),
                "confidence_intervals": ci_rwg["metrics"]
            }
        },
        "paired_statistical_comparison": paired_stats
    }
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ckpt", default="checkpoints/final/rwguard_final_7scheme.pt")
    parser.add_argument("--data", default="data/coco")
    parser.add_argument("--n-train", type=int, default=1000)
    parser.add_argument("--n-val", type=int, default=300)
    parser.add_argument("--n-test", type=int, default=500)
    parser.add_argument("--out", default="audit/shortcut_baseline_results.json")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Executing Shortcut-Learning Baseline Experiments on device: {device}...")
    report = run_shortcut_experiments(
        args.ckpt, args.data, n_train=args.n_train, n_val=args.n_val, n_test=args.n_test, device=device
    )

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(report, f, indent=2)

    print("\n=======================================================")
    print(" SHORTCUT LEARNING BASELINE COMPARISON SUMMARY")
    print(f" Test Samples: {report['n_test_samples']} ({report['n_source_images']} source images)")
    print("=======================================================")
    print(f"{'Model':<25} {'AUC (95% CI)':<26} {'TPR@1%FPR (95% CI)':<26} {'TPR @ tau':<10} {'FPR @ tau':<10}")
    print("-" * 100)
    for mname, mdata in report["models"].items():
        auc = mdata["metrics"]["auc"]
        auc_ci = mdata["confidence_intervals"]["auc"]["ci_95"]
        tpr1 = mdata["metrics"]["tpr_at_1pct_fpr"]
        tpr1_ci = mdata["confidence_intervals"]["tpr_at_1pct_fpr"]["ci_95"]
        tpr_f = mdata["metrics"]["tpr_fixed_thr"]
        fpr_f = mdata["metrics"]["fpr_fixed_thr"]
        auc_str = f"{auc:.4f} [{auc_ci[0]:.3f}, {auc_ci[1]:.3f}]"
        tpr1_str = f"{tpr1:.4f} [{tpr1_ci[0]:.3f}, {tpr1_ci[1]:.3f}]"
        print(f"{mname:<25} {auc_str:<26} {tpr1_str:<26} {tpr_f:<10.3f} {fpr_f:<10.3f}")
    print("-" * 100)
    paired = report["paired_statistical_comparison"]
    print("PAIRED DIFFERENCES (95% Bootstrap CI):")
    p_lr = paired["rwguard_minus_logistic_regression"]
    print(f"  RW-Guard - Logistic Reg: Delta AUC = +{p_lr['delta_auc_mean']:.4f} [{p_lr['delta_auc_ci_95'][0]:.4f}, {p_lr['delta_auc_ci_95'][1]:.4f}], Delta TPR@1% = +{p_lr['delta_tpr_at_1pct_mean']:.4f}")
    p_rf = paired["rwguard_minus_random_forest"]
    print(f"  RW-Guard - Random Forest: Delta AUC = +{p_rf['delta_auc_mean']:.4f} [{p_rf['delta_auc_ci_95'][0]:.4f}, {p_rf['delta_auc_ci_95'][1]:.4f}], Delta TPR@1% = +{p_rf['delta_tpr_at_1pct_mean']:.4f}")
    print(f"\nSaved results to {args.out}")


if __name__ == "__main__":
    main()
