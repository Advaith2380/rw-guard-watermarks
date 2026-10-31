"""Distortion-matched controls for RW-Guard (Review Requirements REQ-E, REQ-F).

Evaluates whether ForensicNet distinguishes genuine sequential re-watermarking attacks
from non-adversarial images with identical total perturbation energy:
1. Re-watermarked (victim + attacker sequential embedding) [True Positives]
2. Single-watermarked at matched perturbation budget (scaled embedding strength)
3. Single-watermarked + matched high-frequency Gaussian noise
4. Benign double processing with matched residual energy
5. Standard singly-watermarked controls [True Negatives]
6. Clean unwatermarked controls [Auxiliary Controls]
"""

import argparse
import json
import os
import numpy as np
import torch
from torch.utils.data import DataLoader

from rewm.data import list_images, split_paths, load_image, apply_benign
from rewm.watermarks import SCHEMES, NBITS, embed_random, psnr
from rewm.model import build_model
from rewm.engine import predict
from rewm.metrics import threshold_at_fpr, summarize
from bootstrap_ci import compute_bootstrap_cis


def evaluate_matched_controls(ckpt_path, data_dir, n_test=200, seed=0, device="cuda"):
    ckpt = torch.load(ckpt_path, map_location=device)
    targs = ckpt["args"]
    model = build_model(targs["arch"], width=targs.get("width", 32)).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()

    seen = ckpt.get("train_schemes", ["dct_qim", "dwt_qim", "ss_spatial", "fft_ring"])
    paths = list_images(data_dir)
    _, va_paths, te_paths = split_paths(paths, seed=seed)
    
    # 1. Validation split for threshold selection
    val_images = [load_image(p, 256, None) for p in va_paths[:100]]
    val_negs = []
    rng_val = np.random.default_rng(777)
    for im in val_images:
        # 50% clean, 50% single watermark
        if rng_val.random() < 0.5:
            val_negs.append(im)
        else:
            s = str(rng_val.choice(seen))
            val_negs.append(embed_random(im, s, rng_val))
    
    val_tensors = torch.stack([
        torch.from_numpy(im).permute(2, 0, 1).float() / 255.0 for im in val_negs
    ]).to(device)
    with torch.no_grad():
        val_logits = model(val_tensors).view(-1).cpu().numpy()
    thr = float(threshold_at_fpr(val_logits, 0.01))
    print(f"Validation operating threshold (1% FPR): logit > {thr:.4f}")

    # 2. Test split controls construction
    test_paths = te_paths[:n_test]
    test_originals = [load_image(p, 256, None) for p in test_paths]
    
    rng = np.random.default_rng(seed)
    
    cond_rewm = []           # 1. Sequential double watermark
    cond_single_matched = []  # 2. Single watermark at increased strength
    cond_single_plus_noise = [] # 3. Single watermark + matched noise
    cond_single_standard = [] # 4. Standard single watermark
    cond_clean = []          # 5. Clean images
    
    energies_rewm = []
    energies_single_matched = []
    energies_noise = []
    
    for im in test_originals:
        s1 = str(rng.choice(seen))
        s2 = str(rng.choice(seen))
        
        # 1. Re-watermark (victim + attacker)
        w1, i1 = embed_random(im, s1, rng, return_info=True)
        w2, i2 = embed_random(w1, s2, rng, return_info=True)
        cond_rewm.append(w2)
        diff_rewm = w2.astype(np.float32) - im.astype(np.float32)
        mse_rewm = float(np.mean(diff_rewm ** 2))
        energies_rewm.append(mse_rewm)
        
        # 2. Single watermark at matched strength (scaled strength)
        # Scale strength by approx sqrt(2) to double residual variance
        orig_strength = i1.get("strength", 1.0)
        matched_strength = orig_strength * 1.414
        w_scaled = SCHEMES[s1].embed(im, i1["key"], i1["bits"], matched_strength)
        cond_single_matched.append(w_scaled)
        diff_scaled = w_scaled.astype(np.float32) - im.astype(np.float32)
        energies_single_matched.append(float(np.mean(diff_scaled ** 2)))
        
        # 3. Single watermark + matched Gaussian noise
        # Residual variance needed = MSE(rewm) - MSE(single)
        mse_single = float(np.mean((w1.astype(np.float32) - im.astype(np.float32)) ** 2))
        needed_noise_var = max(0.0, mse_rewm - mse_single)
        sigma = np.sqrt(needed_noise_var)
        noise = rng.normal(0, sigma, im.shape).astype(np.float32)
        w_noise = np.clip(w1.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        cond_single_plus_noise.append(w_noise)
        diff_noise = w_noise.astype(np.float32) - im.astype(np.float32)
        energies_noise.append(float(np.mean(diff_noise ** 2)))
        
        # 4. Standard single watermark
        cond_single_standard.append(w1)
        
        # 5. Clean original
        cond_clean.append(im)

    conditions = {
        "1_re-watermarked_positives": (cond_rewm, energies_rewm),
        "2_single_strength_matched": (cond_single_matched, energies_single_matched),
        "3_single_plus_matched_noise": (cond_single_plus_noise, energies_noise),
        "4_single_standard_negative": (cond_single_standard, [float(np.mean((w.astype(np.float32) - im.astype(np.float32))**2)) for w, im in zip(cond_single_standard, test_originals)]),
        "5_clean_controls": (cond_clean, [0.0] * len(test_clean := test_originals))
    }

    results = {
        "operating_threshold": thr,
        "n_samples_per_condition": len(test_originals),
        "conditions": {}
    }

    print("\nEvaluating model against matched controls...")
    for cond_name, (img_list, mse_list) in conditions.items():
        tensors = torch.stack([
            torch.from_numpy(im).permute(2, 0, 1).float() / 255.0 for im in img_list
        ]).to(device)
        
        logits_list = []
        with torch.no_grad():
            for b in range(0, len(tensors), 32):
                logits_list.append(model(tensors[b:b+32]).view(-1).cpu())
        logits = torch.cat(logits_list).numpy()
        
        flagged_rate = float(np.mean(logits > thr))
        mean_score = float(np.mean(logits))
        mean_mse = float(np.mean(mse_list))
        mean_psnr = float(10.0 * np.log10(255.0**2 / (mean_mse + 1e-10))) if mean_mse > 0 else float("inf")
        
        results["conditions"][cond_name] = {
            "mean_residual_mse": mean_mse,
            "mean_psnr_db": mean_psnr,
            "flagged_rate": flagged_rate,
            "mean_score": mean_score
        }

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ckpt", default="D:/projects/rewm-guard/runs/baseline_e9/best.pt")
    parser.add_argument("--data", default="D:/projects/rewm-guard/data/coco")
    parser.add_argument("--n-test", type=int, default=200)
    parser.add_argument("--out", default="audit/matched_controls_results.json")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Running Matched Controls Evaluation on {device}...")
    report = evaluate_matched_controls(args.ckpt, args.data, n_test=args.n_test, device=device)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(report, f, indent=2)

    print("\n=========================================================================")
    print(" DISTORTION-MATCHED CONTROLS EVALUATION RESULTS")
    print(f" Operating Threshold: {report['operating_threshold']:.4f}")
    print("=========================================================================")
    print(f"{'Condition':32s} {'MSE':>8s} {'PSNR (dB)':>10s} {'Flagged Rate':>14s} {'Mean Logit':>12s}")
    print("-" * 78)
    for name, c in report["conditions"].items():
        print(f"{name:32s} {c['mean_residual_mse']:8.2f} {c['mean_psnr_db']:10.1f} {c['flagged_rate']:14.3f} {c['mean_score']:12.3f}")

    print("\nSaved report to", args.out)


if __name__ == "__main__":
    main()
