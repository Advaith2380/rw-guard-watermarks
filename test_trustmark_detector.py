"""
Phase 2 step 2 (plan item #11): test the already-trained epoch-9 detector
against TrustMark-watermarked images, WITH NO RETRAINING. Mirrors
evaluate.py's section 1 exactly (same preprocessing, same fixed threshold),
but swaps the classical watermark schemes for TrustMark.

label 0 -> clean image (50%) or TrustMark-single-watermarked (50%)
label 1 -> TrustMark victim embed, then TrustMark attacker embed (re-watermarked)

Usage:
    python test_trustmark_detector.py --ckpt runs/baseline_e9/best.pt --data data/coco --n 150
"""
import argparse
import os

import numpy as np
import torch
from PIL import Image
from trustmark import TrustMark

from rewm.data import list_images, split_paths, load_image
from rewm.metrics import summarize, threshold_at_fpr, roc_auc
from rewm.model import build_model


def to_tensor(img_uint8):
    return torch.from_numpy(np.array(img_uint8, dtype=np.uint8)).permute(2, 0, 1).float() / 255.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="runs/baseline_e9/best.pt")
    ap.add_argument("--data", default="data/coco")
    ap.add_argument("--n", type=int, default=150, help="number of test source images to use")
    ap.add_argument("--size", type=int, default=256)
    ap.add_argument("--thr", type=float, default=None,
                     help="fixed operating threshold; default: recompute at 1%% FPR on validation using classical schemes, same as evaluate.py")
    ap.add_argument("--model-type", default="Q")
    ap.add_argument("--bs", type=int, default=16)
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    ck = torch.load(args.ckpt, map_location=device, weights_only=False)
    targs = ck["args"]
    model = build_model(targs["arch"], targs["width"]).to(device)
    model.load_state_dict(ck["model"])
    model.eval()
    print(f"loaded {args.ckpt} (epoch {ck['epoch']}, val AUC {ck['val_auc']:.4f})")

    tm = TrustMark(verbose=False, model_type=args.model_type)

    paths = list_images(args.data)
    _, va, te = split_paths(paths)
    te = te[: args.n]
    print(f"testing on {len(te)} source images (never used in training)")

    if args.thr is None:
        # reuse the SAME fixed operating point evaluate.py established on classical schemes,
        # so this is a true no-recalibration generalisation test
        from rewm.data import ReWMDataset
        from torch.utils.data import DataLoader
        from rewm.engine import predict
        ds = ReWMDataset(va[: targs["n_val"]], train=False, seed=777, size=256, benign_p=0.5)
        dl = DataLoader(ds, batch_size=32, shuffle=False, num_workers=0)
        sv, yv, _ = predict(model, dl, device)
        args.thr = threshold_at_fpr(sv[yv == 0], 0.01)
    print(f"fixed operating threshold (reused from classical-scheme validation, 1% FPR): logit > {args.thr:.3f}")

    @torch.no_grad()
    def score_batch(imgs):
        x = torch.stack([to_tensor(im) for im in imgs]).to(device)
        return model(x).float().cpu().numpy()

    scores, labels = [], []
    batch_imgs, batch_labels = [], []

    def flush():
        nonlocal batch_imgs, batch_labels
        if not batch_imgs:
            return
        s = score_batch(batch_imgs)
        scores.extend(s.tolist())
        labels.extend(batch_labels)
        batch_imgs, batch_labels = [], []

    for i, p in enumerate(te):
        clean_arr = load_image(p, args.size, None)             # same preprocessing as rewm/data.py
        clean_pil = Image.fromarray(clean_arr)

        # label 0: clean or single TrustMark embed (alternate, matches ReWMDataset's 50/50 split)
        if i % 2 == 0:
            neg_img = np.array(clean_pil)
            kind0 = "clean"
        else:
            neg_img = np.array(tm.encode(clean_pil, "RWGuard1").resize((args.size, args.size)))
            kind0 = "single-trustmark"
        batch_imgs.append(neg_img); batch_labels.append(0)

        # label 1: TrustMark victim embed, then TrustMark attacker embed
        victim = tm.encode(clean_pil, "RWGuard1")
        rewm_img = np.array(tm.encode(victim, "Attacker").resize((args.size, args.size)))
        batch_imgs.append(rewm_img); batch_labels.append(1)

        if len(batch_imgs) >= args.bs:
            flush()
        if (i + 1) % 25 == 0:
            print(f"  ...{i + 1}/{len(te)} images processed")
    flush()

    y = np.array(labels)
    s = np.array(scores)
    m = summarize(y, s, args.thr)
    print(f"\n[TrustMark, no retraining] n={m['n']}  AUC={m['auc']:.3f}  "
          f"TPR@1%FPR={m['tpr_at_1pct_fpr']:.3f}  fixed-thr TPR={m['tpr_fixed_thr']:.3f} FPR={m['fpr_fixed_thr']:.3f}")
    print("(compare to in-distribution classical-scheme result: AUC 0.859, fixed-thr TPR 0.295, FPR 0.035)")


if __name__ == "__main__":
    main()
