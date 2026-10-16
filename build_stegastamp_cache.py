"""
Mirrors build_trustmark_cache.py, but for StegaStamp: precompute a cache of
StegaStamp-watermarked images so training doesn't have to run the (slow, neural)
StegaStamp ONNX model on every sample every epoch -- classical schemes are
near-instant numpy ops, StegaStamp is a full forward pass through a CNN
encoder/decoder at 400x400, so it has to be precomputed once and reused, the
same way a real deployment would cache a provider's watermark rather than
re-calling their API every time.

On a CUDA machine (recommended -- this is the step that benefits most from
better hardware): `pip install onnxruntime-gpu` instead of `onnxruntime` first.

Uses the SAME train/val source-image split as everything else (rewm.data.split_paths),
so there's no leakage: the StegaStamp images used in training are embedded in
training-split source photos only, never the ones evaluate.py / test_stegastamp_detector.py
use for testing.

Usage:
    python build_stegastamp_cache.py --data data/coco --out data/stegastamp_cache --n-train 500 --n-val 100
"""
import argparse
import os

import cv2

from rewm.data import list_images, load_image, split_paths
from rewm_stegastamp import StegaStamp, msg_from_text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/coco")
    ap.add_argument("--out", default="data/stegastamp_cache")
    ap.add_argument("--n-train", type=int, default=500)
    ap.add_argument("--n-val", type=int, default=100)
    ap.add_argument("--size", type=int, default=256)
    args = ap.parse_args()

    print("loading StegaStamp (ONNX); first run downloads weights...")
    ss = StegaStamp()
    msg, msg2 = msg_from_text("RWGuard1"), msg_from_text("Attacker")

    paths = list_images(args.data)
    tr, va, _ = split_paths(paths)   # same split as train.py/evaluate.py -- te is never touched here
    tr, va = tr[: args.n_train], va[: args.n_val]

    for split_name, split_paths_ in [("train", tr), ("val", va)]:
        for sub in ("clean", "single", "rewm"):
            os.makedirs(os.path.join(args.out, split_name, sub), exist_ok=True)
        print(f"\nbuilding {split_name}: {len(split_paths_)} source images -> "
              f"{len(split_paths_)} clean + {len(split_paths_)} single + {len(split_paths_)} rewm")
        for i, p in enumerate(split_paths_):
            arr_rgb = load_image(p, args.size, None)
            clean_bgr = cv2.cvtColor(arr_rgb, cv2.COLOR_RGB2BGR)
            single_bgr = cv2.resize(ss.encode(clean_bgr, msg), (args.size, args.size))
            victim_bgr = cv2.resize(ss.encode(clean_bgr, msg), (args.size, args.size))
            rewm_bgr = cv2.resize(ss.encode(victim_bgr, msg2), (args.size, args.size))

            name = f"{i:05d}.png"
            cv2.imwrite(os.path.join(args.out, split_name, "clean", name), clean_bgr)
            cv2.imwrite(os.path.join(args.out, split_name, "single", name), single_bgr)
            cv2.imwrite(os.path.join(args.out, split_name, "rewm", name), rewm_bgr)

            if (i + 1) % 50 == 0:
                print(f"  ...{i + 1}/{len(split_paths_)}")

    print(f"\ndone. cache written to {args.out}/")


if __name__ == "__main__":
    main()
