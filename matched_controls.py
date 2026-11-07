"""Distortion-Matched Controls for RW-Guard (Faculty Review Section B / REQ-E, REQ-F).

Evaluates whether ForensicNet distinguishes genuine sequential re-watermarking attacks
from non-adversarial images with identical total perturbation energy (PSNR / MSE):

1. Re-watermarked (victim + attacker sequential embedding) [True Positives]
2. Single-watermarked at matched perturbation budget (controlled strength-search matching MSE)
3. Single-watermarked + matched additive Gaussian noise matching target MSE
4. Standard singly-watermarked controls [True Negatives]
5. Clean unwatermarked controls [Reference Controls]

Implements:
- Controlled binary strength-search procedure for matching single-watermark distortion.
- Rigorous per-sample distortion matching verification (PSNR / MSE mean, median, std, max mismatch).
- Paired source-image level evaluation on frozen 7-scheme model and frozen threshold (1.3394).
- ROC-AUC, TPR@1%FPR, fixed-threshold TPR/FPR, and 95% bootstrap confidence intervals.
"""

import argparse
import json
import os
import sys
sys.path.insert(0, os.path.abspath("."))
import numpy as np
import torch
from torch.utils.data import DataLoader

from rewm.data import list_images, split_paths, load_image
from rewm.watermarks import SCHEMES, STRENGTH_RANGE, embed_random, psnr
from rewm.model import build_model
from rewm.metrics import threshold_at_fpr, roc_auc, rates_at, tpr_at_fpr, summarize
from bootstrap_ci import compute_bootstrap_cis


def mse_to_psnr(mse_val):
    """Convert MSE to PSNR in dB."""
    return 99.0 if mse_val <= 0 else float(10.0 * np.log10(255.0 ** 2 / max(1e-10, mse_val)))


def find_matched_strength(im, scheme_name, key, bits, target_mse, tol=0.1, max_iter=10):
    """Controlled binary strength-search to match single-watermark MSE to target double-watermark MSE."""
    scheme = SCHEMES[scheme_name]
    s_min, s_max = STRENGTH_RANGE.get(scheme_name, (5.0, 50.0))
    low, high = max(0.1, s_min * 0.2), s_max * 4.0
    
    best_str = (s_min + s_max) / 2.0
    best_diff = float("inf")
    best_img = None
    best_mse = 0.0

    im_f = im.astype(np.float32)

    for _ in range(max_iter):
        mid = (low + high) / 2.0
        candidate = scheme.embed(im, key, bits, mid)
        cand_mse = float(np.mean((candidate.astype(np.float32) - im_f) ** 2))
        diff = abs(cand_mse - target_mse)

        if diff < best_diff:
            best_diff = diff
            best_str = mid
            best_img = candidate
            best_mse = cand_mse

        if cand_mse < target_mse:
            low = mid
        else:
            high = mid

        if diff <= tol:
            break

    return best_img, best_str, best_mse, best_diff


def evaluate_matched_controls(ckpt_path, data_dir, n_test=300, seed=42, thr_fixed=1.3394, device="cuda"):
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    targs = ckpt["args"]
    model = build_model(targs["arch"], width=targs.get("width", 32)).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()

    seen = ckpt.get("train_schemes", ["dct_qim", "dwt_qim", "ss_spatial", "fft_ring", "nmp_freq", "svd_qim", "dct_svd"])
    paths = list_images(data_dir)
    _, _, te_paths = split_paths(paths, seed=0)
    test_paths = te_paths[:n_test]
    print(f"Constructing distortion-matched controls for {len(test_paths)} test source images...")

    rng = np.random.default_rng(seed)

    cond_rewm = []
    cond_single_matched = []
    cond_single_noise = []
    cond_single_std = []
    cond_clean = []

    mse_rewm = []
    mse_single_matched = []
    mse_single_noise = []
    mse_single_std = []

    mismatch_strength_list = []
    mismatch_noise_list = []

    for idx, p in enumerate(test_paths):
        im = load_image(p, 256, None)
        im_f = im.astype(np.float32)

        s1 = str(rng.choice(seen))
        s2 = str(rng.choice(seen))

        # 1. Double watermark (victim + attacker)
        w1, info1 = embed_random(im, s1, rng, return_info=True)
        w2, info2 = embed_random(w1, s2, rng, return_info=True)
        t_mse = float(np.mean((w2.astype(np.float32) - im_f) ** 2))

        cond_rewm.append(w2)
        mse_rewm.append(t_mse)

        # 2. Single watermark with strength-matched search
        w_matched, matched_s, cand_mse, mismatch = find_matched_strength(
            im, s1, info1["key"], info1["bits"], target_mse=t_mse
        )
        cond_single_matched.append(w_matched)
        mse_single_matched.append(cand_mse)
        mismatch_strength_list.append(mismatch)

        # 3. Single watermark + matched additive Gaussian noise
        std_mse = float(np.mean((w1.astype(np.float32) - im_f) ** 2))
        needed_var = max(0.0, t_mse - std_mse)
        noise = rng.normal(0, np.sqrt(needed_var), im.shape).astype(np.float32)
        w_noise = np.clip(np.rint(w1.astype(np.float32) + noise), 0, 255).astype(np.uint8)
        n_mse = float(np.mean((w_noise.astype(np.float32) - im_f) ** 2))
        
        cond_single_noise.append(w_noise)
        mse_single_noise.append(n_mse)
        mismatch_noise_list.append(abs(n_mse - t_mse))

        # 4. Standard single watermark negative
        cond_single_std.append(w1)
        mse_single_std.append(std_mse)

        # 5. Clean control
        cond_clean.append(im)

    print(f"Distortion matching completed:")
    print(f"  Target Double Watermark MSE: {np.mean(mse_rewm):.3f} +/- {np.std(mse_rewm):.3f} (PSNR {mse_to_psnr(np.mean(mse_rewm)):.2f} dB)")
    print(f"  Single Strength-Matched MSE: {np.mean(mse_single_matched):.3f} +/- {np.std(mse_single_matched):.3f} (PSNR {mse_to_psnr(np.mean(mse_single_matched)):.2f} dB)")
    print(f"  Single + Noise Matched  MSE: {np.mean(mse_single_noise):.3f} +/- {np.std(mse_single_noise):.3f} (PSNR {mse_to_psnr(np.mean(mse_single_noise)):.2f} dB)")
    print(f"  Mean Per-Sample Strength Mismatch: {np.mean(mismatch_strength_list):.4f} MSE")
    print(f"  Mean Per-Sample Noise Mismatch:    {np.mean(mismatch_noise_list):.4f} MSE")

    # Score conditions with frozen model
    @torch.no_grad()
    def score_images(imgs):
        tensors = torch.stack([
            torch.from_numpy(im).permute(2, 0, 1).float() / 255.0 for im in imgs
        ]).to(device)
        dl = DataLoader(tensors, batch_size=32, shuffle=False)
        out = []
        for batch in dl:
            out.append(model(batch).view(-1).cpu().numpy())
        return np.concatenate(out)

    print("Scoring all conditions with frozen primary model...")
    s_rewm = score_images(cond_rewm)
    s_single_matched = score_images(cond_single_matched)
    s_single_noise = score_images(cond_single_noise)
    s_single_std = score_images(cond_single_std)
    s_clean = score_images(cond_clean)

    sids = np.arange(len(test_paths))

    def evaluate_binary(s_pos, s_neg, name):
        y = np.concatenate([np.ones(len(s_pos)), np.zeros(len(s_neg))])
        s = np.concatenate([s_pos, s_neg])
        paired_sids = np.concatenate([sids, sids])
        
        m = summarize(y, s, thr_fixed)
        ci = compute_bootstrap_cis(y, s, thr=thr_fixed, source_ids=paired_sids, n_bootstraps=2000, seed=42)
        return {
            "comparison": name,
            "metrics": m,
            "confidence_intervals": ci["metrics"]
        }

    comp_strength = evaluate_binary(s_rewm, s_single_matched, "Double vs Single (Strength-Matched)")
    comp_noise = evaluate_binary(s_rewm, s_single_noise, "Double vs Single (Noise-Matched)")
    comp_std = evaluate_binary(s_rewm, s_single_std, "Double vs Single (Standard)")
    comp_clean = evaluate_binary(s_rewm, s_clean, "Double vs Clean Controls")

    report = {
        "checkpoint": ckpt_path,
        "operating_threshold": float(thr_fixed),
        "n_source_images": len(test_paths),
        "distortion_verification": {
            "target_double_mse": {
                "mean": float(np.mean(mse_rewm)),
                "std": float(np.std(mse_rewm)),
                "median": float(np.median(mse_rewm)),
                "mean_psnr_db": float(mse_to_psnr(np.mean(mse_rewm)))
            },
            "single_strength_matched_mse": {
                "mean": float(np.mean(mse_single_matched)),
                "std": float(np.std(mse_single_matched)),
                "median": float(np.median(mse_single_matched)),
                "mean_psnr_db": float(mse_to_psnr(np.mean(mse_single_matched))),
                "mean_absolute_mismatch": float(np.mean(mismatch_strength_list)),
                "max_absolute_mismatch": float(np.max(mismatch_strength_list))
            },
            "single_noise_matched_mse": {
                "mean": float(np.mean(mse_single_noise)),
                "std": float(np.std(mse_single_noise)),
                "median": float(np.median(mse_single_noise)),
                "mean_psnr_db": float(mse_to_psnr(np.mean(mse_single_noise))),
                "mean_absolute_mismatch": float(np.mean(mismatch_noise_list)),
                "max_absolute_mismatch": float(np.max(mismatch_noise_list))
            },
            "single_standard_mse": {
                "mean": float(np.mean(mse_single_std)),
                "std": float(np.std(mse_single_std)),
                "mean_psnr_db": float(mse_to_psnr(np.mean(mse_single_std)))
            }
        },
        "condition_scores": {
            "1_rewm_double": {
                "mean": float(np.mean(s_rewm)),
                "std": float(np.std(s_rewm)),
                "flagged_rate_at_tau": float(np.mean(s_rewm > thr_fixed))
            },
            "2_single_strength_matched": {
                "mean": float(np.mean(s_single_matched)),
                "std": float(np.std(s_single_matched)),
                "flagged_rate_at_tau": float(np.mean(s_single_matched > thr_fixed))
            },
            "3_single_noise_matched": {
                "mean": float(np.mean(s_single_noise)),
                "std": float(np.std(s_single_noise)),
                "flagged_rate_at_tau": float(np.mean(s_single_noise > thr_fixed))
            },
            "4_single_standard": {
                "mean": float(np.mean(s_single_std)),
                "std": float(np.std(s_single_std)),
                "flagged_rate_at_tau": float(np.mean(s_single_std > thr_fixed))
            },
            "5_clean": {
                "mean": float(np.mean(s_clean)),
                "std": float(np.std(s_clean)),
                "flagged_rate_at_tau": float(np.mean(s_clean > thr_fixed))
            }
        },
        "pairwise_evaluations": {
            "double_vs_strength_matched": comp_strength,
            "double_vs_noise_matched": comp_noise,
            "double_vs_standard_single": comp_std,
            "double_vs_clean": comp_clean
        }
    }
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ckpt", default="checkpoints/final/rwguard_final_7scheme.pt")
    parser.add_argument("--data", default="data/coco")
    parser.add_argument("--n-test", type=int, default=300)
    parser.add_argument("--thr", type=float, default=1.3394)
    parser.add_argument("--out", default="audit/matched_controls_results.json")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Evaluating Distortion-Matched Controls on {args.ckpt}...")
    report = evaluate_matched_controls(
        args.ckpt, args.data, n_test=args.n_test, thr_fixed=args.thr, device=device
    )

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(report, f, indent=2)

    print("\n=======================================================")
    print(" DISTORTION-MATCHED CONTROLS EVALUATION SUMMARY")
    print(f" Checkpoint: {report['checkpoint']}")
    print(f" Frozen Operating Threshold: {report['operating_threshold']:.4f}")
    print("=======================================================")
    print(f"{'Condition':<32} {'Mean MSE':<10} {'PSNR (dB)':<11} {'Mean Score':<12} {'Flagged @ tau':<14}")
    print("-" * 85)
    for cname, stats in report["condition_scores"].items():
        mse_val = report["distortion_verification"].get(f"{cname.split('_', 1)[1]}_mse", {}).get("mean", 0.0)
        psnr_val = report["distortion_verification"].get(f"{cname.split('_', 1)[1]}_mse", {}).get("mean_psnr_db", float("inf"))
        print(f"{cname:<32} {mse_val:<10.3f} {psnr_val:<11.2f} {stats['mean']:<12.3f} {stats['flagged_rate_at_tau']:<14.3f}")
    print("-" * 85)
    for comp_key, comp in report["pairwise_evaluations"].items():
        m = comp["metrics"]
        ci = comp["confidence_intervals"]["auc"]["ci_95"]
        print(f"  {comp['comparison']}: ROC-AUC {m['auc']:.4f} [95% CI: {ci[0]:.4f} - {ci[1]:.4f}], TPR@1%FPR {m['tpr_at_1pct_fpr']:.4f}")
    print(f"\nSaved results to {args.out}")


if __name__ == "__main__":
    main()
