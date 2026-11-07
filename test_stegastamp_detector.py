"""StegaStamp Neural-Watermarker Generalization Evaluation (Faculty Review Section C / REQ-I, REQ-J).

Tests the frozen primary seven-scheme RW-Guard detector (checkpoints/final/rwguard_final_7scheme.pt)
against real StegaStamp-watermarked images without retraining (zero-shot transfer):
- label 0: clean original photographs (50%) or single-watermarked StegaStamp images (50%)
- label 1: sequential double StegaStamp embeddings (re-watermarking)

Computes:
- ROC-AUC
- TPR @ 1% FPR (test ROC empirical)
- Fixed-threshold TPR and FPR (using frozen threshold tau=1.3394)
- 95% bootstrap confidence intervals (2,000 replicates) with paired source-image grouping
- Output saved to audit/stegastamp_evaluation_results.json
"""

import argparse
import json
import os
import sys
sys.path.insert(0, os.path.abspath("."))
import cv2
import numpy as np
import torch

from rewm.data import list_images, load_image, split_paths
from rewm.metrics import summarize, threshold_at_fpr
from rewm.model import build_model
from rewm_stegastamp import StegaStamp, msg_from_text
from bootstrap_ci import compute_bootstrap_cis


def to_tensor(img_bgr_uint8):
    img_rgb = cv2.cvtColor(img_bgr_uint8, cv2.COLOR_BGR2RGB)
    return torch.from_numpy(np.ascontiguousarray(img_rgb, dtype=np.uint8)).permute(2, 0, 1).float() / 255.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="checkpoints/final/rwguard_final_7scheme.pt")
    ap.add_argument("--data", default="data/coco")
    ap.add_argument("--n", type=int, default=150, help="number of test source images to use (300 samples)")
    ap.add_argument("--size", type=int, default=256)
    ap.add_argument("--thr", type=float, default=1.3394, help="frozen operating threshold (default: 1.3394)")
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--out", default="audit/stegastamp_evaluation_results.json")
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading detector checkpoint: {args.ckpt}...")
    ck = torch.load(args.ckpt, map_location=device, weights_only=False)
    targs = ck["args"]
    model = build_model(targs["arch"], targs.get("width", 32)).to(device)
    model.load_state_dict(ck["model"])
    model.eval()
    print(f"Loaded {args.ckpt} (epoch {ck.get('epoch', 'N/A')}, val AUC {ck.get('val_auc', 0.0):.4f})")

    print("Loading StegaStamp ONNX encoder/decoder...")
    ss = StegaStamp()
    msg, msg2 = msg_from_text("RWGuard1"), msg_from_text("Attacker")

    paths = list_images(args.data)
    _, _, te = split_paths(paths, seed=0)
    te = te[: args.n]
    print(f"Testing on {len(te)} source images ({len(te)*2} derived samples, never used in training)...")

    thr = args.thr
    print(f"Frozen operating threshold: logit > {thr:.4f}")

    @torch.no_grad()
    def score_batch(imgs_bgr):
        x = torch.stack([to_tensor(im) for im in imgs_bgr]).to(device)
        return model(x).view(-1).float().cpu().numpy()

    scores, labels, kinds = [], [], []
    batch_imgs, batch_labels, batch_kinds = [], [], []

    def flush():
        nonlocal batch_imgs, batch_labels, batch_kinds
        if not batch_imgs:
            return
        s = score_batch(batch_imgs)
        scores.extend(s.tolist())
        labels.extend(batch_labels)
        kinds.extend(batch_kinds)
        batch_imgs, batch_labels, batch_kinds = [], [], []

    for i, p in enumerate(te):
        clean_rgb = load_image(p, args.size, None)
        clean_bgr = cv2.cvtColor(clean_rgb, cv2.COLOR_RGB2BGR)

        # Label 0: clean or single StegaStamp embed (50/50 alternating)
        if i % 2 == 0:
            neg_img = clean_bgr
            kind0 = "clean"
        else:
            neg_img = cv2.resize(ss.encode(clean_bgr, msg), (args.size, args.size))
            kind0 = "single_stegastamp"
        batch_imgs.append(neg_img)
        batch_labels.append(0)
        batch_kinds.append(kind0)

        # Label 1: StegaStamp victim embed then StegaStamp attacker embed (re-watermarking)
        victim = ss.encode(clean_bgr, msg)
        rewm_img = cv2.resize(ss.encode(victim, msg2), (args.size, args.size))
        batch_imgs.append(rewm_img)
        batch_labels.append(1)
        batch_kinds.append("stegastamp>stegastamp")

        if len(batch_imgs) >= args.bs:
            flush()
        if (i + 1) % 25 == 0:
            print(f"  ...processed {i + 1}/{len(te)} images")
    flush()

    y, s = np.array(labels), np.array(scores)
    m = summarize(y, s, thr)
    
    # 2,000 source-grouped bootstrap replicates
    sids = np.array([i // 2 for i in range(len(y))])
    cis = compute_bootstrap_cis(y, s, thr=thr, source_ids=sids, n_bootstraps=2000, seed=42)

    # Breakdown by kind
    kinds_arr = np.array(kinds)
    kind_stats = {}
    for k in sorted(set(kinds)):
        mask = (kinds_arr == k)
        k_scores = s[mask]
        kind_stats[k] = {
            "n": int(np.sum(mask)),
            "flagged_rate_at_tau": float(np.mean(k_scores > thr)),
            "mean_score": float(np.mean(k_scores)),
            "std_score": float(np.std(k_scores)),
            "median_score": float(np.median(k_scores))
        }

    report = {
        "checkpoint": args.ckpt,
        "operating_threshold": float(thr),
        "n_samples": len(y),
        "n_source_images": len(te),
        "metrics": m,
        "confidence_intervals": cis["metrics"],
        "kind_breakdown": kind_stats
    }

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(report, f, indent=2)

    auc_ci = cis["metrics"]["auc"]["ci_95"]
    print("\n=======================================================")
    print(" STEGASTAMP GENERALIZATION EVALUATION SUMMARY")
    print(f" Checkpoint: {args.ckpt}")
    print(f" Frozen Operating Threshold: {thr:.4f}")
    print("=======================================================")
    print(f"  Sample Count:        {m['n']} ({len(te)} source images)")
    print(f"  ROC-AUC:             {m['auc']:.4f} [95% CI: {auc_ci[0]:.4f} - {auc_ci[1]:.4f}]")
    print(f"  TPR @ 1% FPR:        {m['tpr_at_1pct_fpr']:.4f}")
    print(f"  Fixed-Threshold TPR: {m['tpr_fixed_thr']:.4f}")
    print(f"  Fixed-Threshold FPR: {m['fpr_fixed_thr']:.4f}")
    print("\n  Kind Breakdown:")
    for k, v in kind_stats.items():
        print(f"    {k:<24}: n={v['n']:<4} mean={v['mean_score']:<7.3f} flagged@tau={v['flagged_rate_at_tau']:<6.3f}")
    print(f"\nSaved results to {args.out}")


if __name__ == "__main__":
    main()
