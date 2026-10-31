"""Shortcut learning baseline: Residual-energy and Frequency-statistics Logistic Regression.

Investigates whether ForensicNet's detection performance is explainable by simple
perturbation magnitude / residual energy accumulation rather than genuine
re-watermarking forensic signatures (Review Requirement REQ-G).

Implemented using PyTorch/NumPy primitives (zero external dependencies like sklearn/scipy).
"""

import argparse
import json
import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from rewm.data import list_images, split_paths, ReWMDataset
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
    """Extract residual energy and frequency domain features from a batch of RGB tensors.
    
    Args:
        x_tensor: torch.Tensor of shape (B, 3, H, W) in range [0, 1].
        
    Returns:
        torch.Tensor of shape (B, 10) isolating perturbation magnitude & frequency statistics.
    """
    B, C, H, W = x_tensor.shape
    device = x_tensor.device
    
    # 1. Grayscale luminance
    # Y = 0.2989 R + 0.5870 G + 0.1140 B
    weights = torch.tensor([0.2989, 0.5870, 0.1140], device=device).view(1, 3, 1, 1)
    gray = torch.sum(x_tensor * weights, dim=1, keepdim=True)  # (B, 1, H, W)
    
    # 2. High-pass residual features (ForensicNet-matched kernel)
    hp_k = HP_KERNEL_2D.view(1, 1, 3, 3).to(device)
    hp_gray = F.conv2d(gray, hp_k, padding=1)  # (B, 1, H, W)
    
    hp_k_rgb = HP_KERNEL_2D.view(1, 1, 3, 3).repeat(3, 1, 1, 1).to(device)
    hp_rgb = F.conv2d(x_tensor, hp_k_rgb, padding=1, groups=3)  # (B, 3, H, W)
    
    hp_mean_abs = torch.mean(torch.abs(hp_gray), dim=(1, 2, 3))
    hp_var = torch.var(hp_gray, dim=(1, 2, 3))
    hp_energy = torch.mean(hp_gray ** 2, dim=(1, 2, 3))
    hp_r_energy = torch.mean(hp_rgb[:, 0, :, :] ** 2, dim=(1, 2))
    hp_g_energy = torch.mean(hp_rgb[:, 1, :, :] ** 2, dim=(1, 2))
    hp_b_energy = torch.mean(hp_rgb[:, 2, :, :] ** 2, dim=(1, 2))
    
    # 3. Laplacian edge / roughness energy
    lap_k = LAPLACIAN_KERNEL_2D.view(1, 1, 3, 3).to(device)
    lap = F.conv2d(gray, lap_k, padding=1)
    lap_energy = torch.mean(lap ** 2, dim=(1, 2, 3))
    lap_var = torch.var(lap, dim=(1, 2, 3))
    
    # 4. 2D FFT spectral energy distribution
    # High frequency ratio = power outside low-frequency center / total power
    fft_spec = torch.fft.fftshift(torch.fft.fft2(gray.squeeze(1)), dim=(-2, -1))
    mag_sq = torch.abs(fft_spec) ** 2
    
    cy, cx = H // 2, W // 2
    y_coords, x_coords = torch.meshgrid(torch.arange(H, device=device), torch.arange(W, device=device), indexing='ij')
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
    
    # Stack 10 features: (B, 10)
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


def collect_features_from_dataset(dataset, batch_size=32, device="cpu"):
    """Extract features and labels in batches."""
    loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    all_feats = []
    all_labels = []
    all_kinds = []
    
    with torch.no_grad():
        for batch in loader:
            x = batch['x'].to(device)
            y = batch['y'].to(device)
            feats = extract_batch_features(x)
            all_feats.append(feats.cpu())
            all_labels.append(y.cpu())
            all_kinds.extend(batch.get('kind', []))
            
    X = torch.cat(all_feats, dim=0).numpy()
    Y = torch.cat(all_labels, dim=0).numpy()
    return X, Y, all_kinds


class TorchLogisticRegression(nn.Module):
    """L2-regularized logistic regression solver using PyTorch."""
    def __init__(self, in_features):
        super().__init__()
        self.linear = nn.Linear(in_features, 1)
        
    def forward(self, x):
        return self.linear(x).squeeze(1)
        
    def fit(self, X, y, lr=0.05, weight_decay=1e-3, epochs=300):
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
            X_t = torch.tensor(X, dtype=torch.float32)
            return self(X_t).numpy()


def run_shortcut_baseline(data_dir, n_train=3000, n_val=300, n_test=1500, seed=0, device="cpu"):
    paths = list_images(data_dir)
    tr_paths, va_paths, te_paths = split_paths(paths, seed=seed)
    
    if n_train > 0:
        tr_paths = tr_paths[:n_train]
    if n_val > 0:
        va_paths = va_paths[:n_val]
    if n_test > 0:
        te_paths = te_paths[:n_test]
        
    seen = ["dct_qim", "dwt_qim", "ss_spatial", "fft_ring"]
    seen_kw = dict(victim_schemes=seen, attacker_schemes=seen, single_schemes=seen)
    
    print(f"Dataset split: train={len(tr_paths)}, val={len(va_paths)}, test={len(te_paths)} source images...")
    ds_train = ReWMDataset(tr_paths, train=True, seed=seed, size=256, benign_p=0.5, **seen_kw)
    ds_val = ReWMDataset(va_paths, train=False, seed=777, size=256, benign_p=0.5, **seen_kw)
    ds_test = ReWMDataset(te_paths, train=False, seed=777, size=256, benign_p=0.5, **seen_kw)
    
    print(f"Extracting features: train ({len(ds_train)}), val ({len(ds_val)}), test ({len(ds_test)})...")
    X_train, y_train, _ = collect_features_from_dataset(ds_train, device=device)
    X_val, y_val, _ = collect_features_from_dataset(ds_val, device=device)
    X_test, y_test, test_kinds = collect_features_from_dataset(ds_test, device=device)
    
    # Feature Standardization (StandardScaler equivalent)
    mean = np.mean(X_train, axis=0, keepdims=True)
    std = np.std(X_train, axis=0, keepdims=True) + 1e-7
    
    X_train_norm = (X_train - mean) / std
    X_val_norm = (X_val - mean) / std
    X_test_norm = (X_test - mean) / std
    
    print("Fitting Logistic Regression model...")
    clf = TorchLogisticRegression(in_features=X_train.shape[1])
    clf.fit(X_train_norm, y_train)
    
    # Calibrate threshold on validation negatives targeting 1% FPR
    val_logits = clf.predict_logits(X_val_norm)
    val_neg_scores = val_logits[y_val == 0]
    thr = threshold_at_fpr(val_neg_scores, 0.01)
    print(f"Validation 1% FPR threshold: logit > {thr:.4f}")
    
    # Evaluate on test set
    test_logits = clf.predict_logits(X_test_norm)
    test_metrics = summarize(y_test, test_logits, thr)
    
    # Compute 95% Bootstrap Confidence Intervals
    cis = compute_bootstrap_cis(y_test, test_logits, thr=thr, n_bootstraps=1000, seed=seed)
    
    feature_names = [
        "hp_mean_abs", "hp_var", "hp_energy", "hp_r_energy", "hp_g_energy",
        "hp_b_energy", "lap_energy", "lap_var", "hf_fft_ratio", "local_var"
    ]
    weights = clf.linear.weight.detach().squeeze(0).numpy()
    coef_dict = {name: float(w) for name, w in zip(feature_names, weights)}
    
    report = {
        "baseline_name": "Residual-Energy & Frequency-Statistics Logistic Regression",
        "n_train_samples": int(len(y_train)),
        "n_val_samples": int(len(y_val)),
        "n_test_samples": int(len(y_test)),
        "operating_threshold_val_1pct": float(thr),
        "metrics": test_metrics,
        "confidence_intervals": cis["metrics"],
        "coefficients": coef_dict,
        "intercept": float(clf.linear.bias.detach().item())
    }
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="D:/projects/rewm-guard/data/coco")
    parser.add_argument("--n-train", type=int, default=1000)
    parser.add_argument("--n-val", type=int, default=200)
    parser.add_argument("--n-test", type=int, default=500)
    parser.add_argument("--out", default="audit/shortcut_baseline_results.json")
    args = parser.parse_args()
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Executing Shortcut Baseline on device: {device}...")
    report = run_shortcut_baseline(args.data, n_train=args.n_train, n_val=args.n_val, n_test=args.n_test, device=device)
    
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(report, f, indent=2)
        
    print("\n=======================================================")
    print(" SHORTCUT LEARNING BASELINE (LOGISTIC REGRESSION) RESULTS")
    print("=======================================================")
    m = report["metrics"]
    ci = report["confidence_intervals"]
    print(f"  Test ROC-AUC:        {m['auc']:.4f}  [95% CI: {ci['auc']['ci_95'][0]:.4f} - {ci['auc']['ci_95'][1]:.4f}]")
    print(f"  TPR @ 1% FPR:        {m['tpr_at_1pct_fpr']:.4f}  [95% CI: {ci['tpr_at_1pct_fpr']['ci_95'][0]:.4f} - {ci['tpr_at_1pct_fpr']['ci_95'][1]:.4f}]")
    print(f"  TPR @ 0.1% FPR:      {m['tpr_at_0p1pct_fpr']:.4f}")
    print(f"  TPR @ Fixed Thr:     {m['tpr_fixed_thr']:.4f}")
    print(f"  FPR @ Fixed Thr:     {m['fpr_fixed_thr']:.4f}")
    print("\nLearned Weights:")
    for name, c in report["coefficients"].items():
        print(f"  {name:16s}: {c:+.4f}")
    print(f"\nSaved report to {args.out}")


if __name__ == "__main__":
    main()
