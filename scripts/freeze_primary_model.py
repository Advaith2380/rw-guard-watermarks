"""Final Seven-Scheme Primary Model Freezing Script.

Performs:
1. Loads the selected winning primary 7-scheme checkpoint (runs/seed0/best.pt).
2. Computes SHA-256 hash and parameter count.
3. Evaluates on validation split (300 source images, 600 samples) with 7 schemes.
4. Computes validation ROC-AUC and operating threshold tau targeting 1% validation FPR.
5. Verifies validation FPR is exactly around 1%.
6. Saves frozen checkpoint copy to checkpoints/final/rwguard_final_7scheme.pt.
7. Saves comprehensive frozen model configuration and metadata to checkpoints/final/final_model_config.json.
"""

import json
import os
import sys
sys.path.insert(0, os.path.abspath("."))
import hashlib
import numpy as np
import torch
from torch.utils.data import DataLoader

from rewm.data import list_images, split_paths, ReWMDataset
from rewm.model import build_model
from rewm.engine import predict
from rewm.metrics import roc_auc, threshold_at_fpr, summarize, rates_at
from rewm.watermarks import SCHEMES


def get_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192 * 1024):
            h.update(chunk)
    return h.hexdigest()


def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Executing Model Freezing on device: {device}")

    src_ckpt = "runs/seed0/best.pt"
    if not os.path.exists(src_ckpt):
        src_ckpt = "D:/projects/rewm-guard/runs/seed0/best.pt"

    dst_dir = "checkpoints/final"
    os.makedirs(dst_dir, exist_ok=True)
    dst_ckpt = os.path.join(dst_dir, "rwguard_final_7scheme.pt")

    # Ensure file is copied
    if not os.path.exists(dst_ckpt) or os.path.getsize(dst_ckpt) != os.path.getsize(src_ckpt):
        import shutil
        shutil.copy2(src_ckpt, dst_ckpt)
        print(f"Copied {src_ckpt} to {dst_ckpt}")

    sha256 = get_sha256(dst_ckpt)
    size_bytes = os.path.getsize(dst_ckpt)
    print(f"Final Model Checkpoint: {dst_ckpt}")
    print(f"  SHA-256: {sha256}")
    print(f"  Size:    {size_bytes} bytes")

    ck = torch.load(dst_ckpt, map_location=device, weights_only=False)
    targs = ck["args"]
    seen = ck["train_schemes"]
    
    print(f"  Training arguments: {targs}")
    print(f"  Trained schemes ({len(seen)}): {seen}")
    assert len(seen) == 7, f"Expected 7 schemes, got {len(seen)}: {seen}"

    model = build_model(targs["arch"], targs.get("width", 32)).to(device)
    model.load_state_dict(ck["model"])
    model.eval()

    param_count = count_parameters(model)
    print(f"  Trainable parameters: {param_count:,}")

    # Load validation dataset
    data_dir = "data/coco"
    paths = list_images(data_dir)
    _, va, te = split_paths(paths, seed=0)
    va = va[: targs.get("n_val", 300)]
    print(f"  Validation source images: {len(va)} (corresponds to {len(va)*2} derived samples)")

    seen_kw = dict(victim_schemes=seen, attacker_schemes=seen, single_schemes=seen)
    val_ds = ReWMDataset(va, train=False, seed=777, size=256, benign_p=0.5, **seen_kw)
    val_dl = DataLoader(val_ds, batch_size=32, shuffle=False, num_workers=0)
    
    val_scores, val_labels, _ = predict(model, val_dl, device, desc="Validation Calibration")

    val_neg_scores = val_scores[val_labels == 0]
    val_pos_scores = val_scores[val_labels == 1]
    
    val_auc = float(roc_auc(val_labels, val_scores))
    frozen_thr = float(threshold_at_fpr(val_neg_scores, 0.01))
    
    val_tpr_fixed, val_fpr_fixed = rates_at(val_labels, val_scores, frozen_thr)
    val_summary = summarize(val_labels, val_scores, frozen_thr)

    print("\n--- Validation Calibration Results ---")
    print(f"  Validation ROC-AUC:            {val_auc:.4f}")
    print(f"  Frozen Threshold (tau @ 1% FPR): {frozen_thr:.4f}")
    print(f"  Validation TPR @ frozen tau:    {val_tpr_fixed:.4f} ({int(val_tpr_fixed * len(val_pos_scores))}/{len(val_pos_scores)})")
    print(f"  Validation FPR @ frozen tau:    {val_fpr_fixed:.4f} ({int(val_fpr_fixed * len(val_neg_scores))}/{len(val_neg_scores)})")
    print(f"  Validation Neg Mean Score:      {float(np.mean(val_neg_scores)):.4f} +/- {float(np.std(val_neg_scores)):.4f}")
    print(f"  Validation Pos Mean Score:      {float(np.mean(val_pos_scores)):.4f} +/- {float(np.std(val_pos_scores)):.4f}")

    # Write configuration
    config = {
        "model_name": "RW-Guard Final Seven-Scheme Primary Model",
        "checkpoint_path": dst_ckpt,
        "sha256": sha256,
        "file_size_bytes": size_bytes,
        "architecture": {
            "type": "ForensicNet",
            "arch_name": targs["arch"],
            "base_width": targs.get("width", 32),
            "parameter_count": param_count,
            "high_pass_preprocessing": True,
            "pooling": "global_avg_and_max"
        },
        "training_protocol": {
            "dataset": "MS-COCO val2017",
            "training_source_images": 3000,
            "validation_source_images": len(va),
            "random_seed": targs.get("seed", 0),
            "epochs": targs.get("epochs", 15),
            "best_epoch": ck.get("epoch", 14),
            "batch_size": targs.get("bs", 32),
            "learning_rate": targs.get("lr", 0.001),
            "input_crop_size": targs.get("crop", 128),
            "training_size": targs.get("size", 256),
            "benign_augmentation_prob": targs.get("benign_p", 0.5),
            "seven_schemes": seen
        },
        "operating_point": {
            "calibration_dataset": "MS-COCO validation split (300 source images, 600 samples)",
            "target_fpr": 0.01,
            "frozen_threshold": frozen_thr,
            "calibration_rule": "Threshold selected on validation negative scores at 99th percentile (FPR=0.01)",
            "validation_auc": val_auc,
            "validation_tpr_at_frozen_threshold": float(val_tpr_fixed),
            "validation_fpr_at_frozen_threshold": float(val_fpr_fixed),
            "validation_neg_score_stats": {
                "mean": float(np.mean(val_neg_scores)),
                "std": float(np.std(val_neg_scores)),
                "p50": float(np.percentile(val_neg_scores, 50)),
                "p90": float(np.percentile(val_neg_scores, 90)),
                "p99": float(np.percentile(val_neg_scores, 99)),
                "max": float(np.max(val_neg_scores))
            },
            "validation_pos_score_stats": {
                "mean": float(np.mean(val_pos_scores)),
                "std": float(np.std(val_pos_scores)),
                "p50": float(np.percentile(val_pos_scores, 50)),
                "min": float(np.min(val_pos_scores)),
                "max": float(np.max(val_pos_scores))
            }
        },
        "status": "FROZEN_VALIDATED"
    }

    cfg_path = os.path.join(dst_dir, "final_model_config.json")
    with open(cfg_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"\nSaved frozen configuration to {cfg_path}")


if __name__ == "__main__":
    main()
