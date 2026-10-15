"""
Phase 3 item #16: a more realistic attacker than evaluate.py's section 2 (which only
applies ONE benign op at a time: jpeg OR noise OR blur OR bright). A real redistribution
pipeline typically does several things at once -- here: crop out an 5-15% border (hides
provenance / discards anything near the edges) AND re-save at a normal JPEG quality.
Applied equally to clean / single-watermarked / re-watermarked images, same as every
other section of evaluate.py, so the network can't use "was post-processed" as a shortcut.

Reuses the SAME fixed 1%-FPR operating threshold methodology as evaluate.py (recomputed
here on validation, in-distribution, seen schemes) -- a true no-recalibration test.

Usage:
    python test_realistic_attack.py --ckpt runs/baseline_e9/best.pt --data data/coco --n 300
"""
import argparse

import cv2
import numpy as np
import torch
from torch.utils.data import DataLoader

from rewm.data import ReWMDataset, apply_benign, list_images, split_paths
from rewm.engine import predict
from rewm.metrics import summarize, threshold_at_fpr
from rewm.model import build_model


def crop_and_resize(img, frac, rng):
    h, w = img.shape[:2]
    ch, cw = int(round(h * frac)), int(round(w * frac))
    t = int(rng.integers(0, h - ch + 1))
    l = int(rng.integers(0, w - cw + 1))
    cropped = img[t:t + ch, l:l + cw]
    return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_CUBIC)


def realistic_attack(img, rng):
    """crop out a random 5-15% border, then re-save as a typical-quality JPEG."""
    img = crop_and_resize(img, frac=float(rng.uniform(0.85, 0.95)), rng=rng)
    img = apply_benign(img, f"jpeg{int(rng.integers(75, 91))}", rng)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="runs/baseline_e9/best.pt")
    ap.add_argument("--data", default="data/coco")
    ap.add_argument("--n", type=int, default=0, help="0 = all test images")
    ap.add_argument("--bs", type=int, default=32)
    ap.add_argument("--workers", type=int, default=0)
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    ck = torch.load(args.ckpt, map_location=device, weights_only=False)
    targs, seen = ck["args"], ck["train_schemes"]
    model = build_model(targs["arch"], targs["width"]).to(device)
    model.load_state_dict(ck["model"])
    model.eval()
    print(f"loaded {args.ckpt} (epoch {ck['epoch']}, val AUC {ck['val_auc']:.4f})")

    paths = list_images(args.data)
    _, va, te = split_paths(paths)
    te = te[: args.n] if args.n else te
    va = va[: targs["n_val"]]
    seen_kw = dict(victim_schemes=seen, attacker_schemes=seen, single_schemes=seen)
    print(f"testing on {len(te)} test source images (never used in training)")

    def run(paths_, **kw):
        ds = ReWMDataset(paths_, train=False, seed=777, **kw)
        dl = DataLoader(ds, batch_size=args.bs, shuffle=False, num_workers=args.workers)
        return predict(model, dl, device)

    # same fixed operating point as evaluate.py: 1% FPR on validation, in-distribution
    sv, yv, _ = run(va, size=256, benign_p=0.5, **seen_kw)
    thr = threshold_at_fpr(sv[yv == 0], 0.01)
    print(f"fixed operating threshold (val, 1% FPR): logit > {thr:.3f}")

    # build the (clean / single / rewm) test set with NO single-op benign (benign_p=0) --
    # we apply our own combined crop+jpeg attack below, to every sample, both classes.
    ds = ReWMDataset(te, size=256, train=False, seed=999, benign_p=0.0, **seen_kw)
    rng_master = np.random.default_rng(999)

    scores, labels = [], []
    batch_x = []

    def flush():
        if not batch_x:
            return
        x = torch.stack(batch_x).to(device)
        with torch.no_grad():
            s = model(x).float().cpu().numpy()
        scores.extend(s.tolist())
        batch_x.clear()

    for i in range(len(ds)):
        item = ds[i]
        img = (item["x"].permute(1, 2, 0).numpy() * 255.0).round().astype(np.uint8)
        img = realistic_attack(img, rng_master)
        batch_x.append(torch.from_numpy(img).permute(2, 0, 1).float() / 255.0)
        labels.append(float(item["y"]))
        if len(batch_x) >= args.bs:
            flush()
        if (i + 1) % 200 == 0:
            print(f"  ...{i + 1}/{len(ds)}")
    flush()

    y, s = np.array(labels), np.array(scores)
    m = summarize(y, s, thr)
    print(f"\n[realistic attacker: crop 85-95% + JPEG q75-90, both classes] n={m['n']}  AUC={m['auc']:.3f}  "
          f"TPR@1%FPR={m['tpr_at_1pct_fpr']:.3f}  fixed-thr TPR={m['tpr_fixed_thr']:.3f} FPR={m['fpr_fixed_thr']:.3f}")
    print("(compare to evaluate.py section 1, no combo attack: AUC 0.859, fixed-thr TPR 0.295, FPR 0.035)")


if __name__ == "__main__":
    main()
