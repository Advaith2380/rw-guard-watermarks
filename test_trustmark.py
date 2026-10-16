"""
Phase 2 step 1: test TrustMark (a real, pretrained neural watermarker) on
real images using the same methodology as sanity_check.py's Table 1/2 --
PSNR for invisibility, message recovery for the single-embed case, and
victim/attacker recovery for the re-watermarking case.

Usage:
    python test_trustmark.py --data data/coco --n 10
"""
import argparse
import glob
import os
import random

import numpy as np
from PIL import Image

from trustmark import TrustMark


def psnr(a: np.ndarray, b: np.ndarray) -> float:
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    mse = np.mean((a - b) ** 2)
    if mse == 0:
        return 99.0
    return 10 * np.log10(255.0 ** 2 / mse)


def find_images(data_dir: str, n: int, seed: int = 0):
    exts = ("*.jpg", "*.jpeg", "*.png")
    paths = []
    for ext in exts:
        paths.extend(glob.glob(os.path.join(data_dir, "**", ext), recursive=True))
    paths = sorted(paths)
    random.Random(seed).shuffle(paths)
    if not paths:
        raise SystemExit(f"No images found under {data_dir}")
    return paths[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/coco")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--msg", default="RWGuard1")  # 8 ASCII chars = 56 bits, fits TrustMark's 100-bit payload
    ap.add_argument("--msg2", default="Attacker")  # second (attacker) message for the re-watermark test
    ap.add_argument("--model-type", default="Q", choices=["Q", "P", "C"])
    ap.add_argument("--out", default="trustmark_out")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    paths = find_images(args.data, args.n)
    print(f"testing on {len(paths)} images from {args.data}")

    print(f"loading TrustMark (model_type={args.model_type}); first run downloads weights...")
    tm = TrustMark(verbose=False, model_type=args.model_type)

    # ---- Table A: single embedding (invisibility + message recovery) ----
    print("\n[Table A] single embedding")
    psnrs, oks = [], []
    for i, p in enumerate(paths):
        cover = Image.open(p).convert("RGB")
        stego = tm.encode(cover, args.msg)
        a = np.array(cover.resize(stego.size))
        b = np.array(stego)
        pv = psnr(a, b)
        secret, present, schema = tm.decode(stego)
        ok = present and secret == args.msg
        psnrs.append(pv)
        oks.append(ok)
        if i == 0:
            stego.save(os.path.join(args.out, "example_single.png"))
        print(f"  {os.path.basename(p):30s} PSNR={pv:5.1f}dB  decoded_ok={ok}  got={secret!r}")
    print(f"  MEAN  PSNR={np.mean(psnrs):.1f}dB  recovery_rate={np.mean(oks):.3f}")

    # ---- Table B: re-watermarking (TrustMark victim > TrustMark attacker) ----
    print("\n[Table B] re-watermarking: TrustMark > TrustMark (same scheme, different message)")
    victim_ok, attacker_ok, psnrs2 = [], [], []
    for i, p in enumerate(paths):
        cover = Image.open(p).convert("RGB")
        victim_img = tm.encode(cover, args.msg)
        reatt_img = tm.encode(victim_img, args.msg2)
        a = np.array(victim_img.resize(reatt_img.size))
        b = np.array(reatt_img)
        pv = psnr(a, b)
        secret, present, schema = tm.decode(reatt_img)
        v_ok = present and secret == args.msg       # did the ORIGINAL (victim) message survive?
        a_ok = present and secret == args.msg2       # did the ATTACKER's message win instead?
        victim_ok.append(v_ok)
        attacker_ok.append(a_ok)
        psnrs2.append(pv)
        if i == 0:
            reatt_img.save(os.path.join(args.out, "example_rewatermarked.png"))
        print(f"  {os.path.basename(p):30s} PSNR={pv:5.1f}dB  decoded={secret!r}  victim_survived={v_ok}  attacker_won={a_ok}")
    print(f"  MEAN  PSNR={np.mean(psnrs2):.1f}dB  victim_survival_rate={np.mean(victim_ok):.3f}  attacker_success_rate={np.mean(attacker_ok):.3f}")

    print(f"\nExample images saved to {args.out}/")


if __name__ == "__main__":
    main()
