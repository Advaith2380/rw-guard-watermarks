"""
Phase 2 step 3 (plan item #12, part 1 of 2): precompute a cache of TrustMark-
watermarked images so training doesn't have to run the (slow, neural) TrustMark
encoder on every sample every epoch -- classical schemes are near-instant numpy
ops, TrustMark is a full forward pass through a ResNet encoder, so it has to be
precomputed once and reused, the same way a real deployment would cache a
provider's watermark rather than re-calling their API every time.

Uses the SAME train/val source-image split as everything else (rewm.data.split_paths),
so there's no leakage: the TrustMark images used in training are embedded in
training-split source photos only, never the ones evaluate.py / test_trustmark_detector.py
use for testing.

Usage:
    python build_trustmark_cache.py --data data/coco --out data/trustmark_cache --n-train 500 --n-val 100
"""
import argparse
import os

import numpy as np
from PIL import Image
from trustmark import TrustMark

from rewm.data import list_images, split_paths, load_image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/coco")
    ap.add_argument("--out", default="data/trustmark_cache")
    ap.add_argument("--n-train", type=int, default=500)
    ap.add_argument("--n-val", type=int, default=100)
    ap.add_argument("--size", type=int, default=256)
    ap.add_argument("--model-type", default="Q")
    args = ap.parse_args()

    tm = TrustMark(verbose=False, model_type=args.model_type)

    paths = list_images(args.data)
    tr, va, _ = split_paths(paths)   # same split as train.py/evaluate.py -- te is never touched here
    tr, va = tr[: args.n_train], va[: args.n_val]

    for split_name, split_paths_ in [("train", tr), ("val", va)]:
        for sub in ("clean", "single", "rewm"):
            os.makedirs(os.path.join(args.out, split_name, sub), exist_ok=True)
        print(f"\nbuilding {split_name}: {len(split_paths_)} source images -> "
              f"{len(split_paths_)} clean + {len(split_paths_)} single + {len(split_paths_)} rewm")
        for i, p in enumerate(split_paths_):
            arr = load_image(p, args.size, None)
            clean = Image.fromarray(arr)
            single = tm.encode(clean, "RWGuard1")
            victim = tm.encode(clean, "RWGuard1")
            rewm = tm.encode(victim, "Attacker")

            name = f"{i:05d}.png"
            clean.save(os.path.join(args.out, split_name, "clean", name))
            single.save(os.path.join(args.out, split_name, "single", name))
            rewm.save(os.path.join(args.out, split_name, "rewm", name))

            if (i + 1) % 50 == 0:
                print(f"  ...{i + 1}/{len(split_paths_)}")

    print(f"\ndone. cache written to {args.out}/")


if __name__ == "__main__":
    main()
