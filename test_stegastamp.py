"""
Mirrors test_trustmark.py, but for StegaStamp: tests the real, pretrained
StegaStamp encoder/decoder on real images using the same methodology as
sanity_check.py's Table 1/2 -- PSNR for invisibility, bit accuracy for the
single-embed case, and victim/attacker bit accuracy for the re-watermarking case.

Usage:
    python test_stegastamp.py --data data/coco --n 10
"""
import argparse
import glob
import os
import random

import cv2
import numpy as np

from rewm_stegastamp import StegaStamp, bit_accuracy, msg_from_text


def psnr(a: np.ndarray, b: np.ndarray) -> float:
    a, b = a.astype(np.float64), b.astype(np.float64)
    mse = np.mean((a - b) ** 2)
    return 99.0 if mse == 0 else 10 * np.log10(255.0 ** 2 / mse)


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
    ap.add_argument("--msg", default="RWGuard1")
    ap.add_argument("--msg2", default="Attacker")
    ap.add_argument("--out", default="stegastamp_out")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    paths = find_images(args.data, args.n)
    print(f"testing on {len(paths)} images from {args.data}")

    print("loading StegaStamp (ONNX); first run downloads weights...")
    ss = StegaStamp()
    msg, msg2 = msg_from_text(args.msg), msg_from_text(args.msg2)

    # ---- Table A: single embedding (invisibility + message recovery) ----
    print("\n[Table A] single embedding")
    psnrs, accs = [], []
    for i, p in enumerate(paths):
        cover = cv2.imread(p)
        stego = ss.encode(cover, msg)
        pv = psnr(cover.astype(np.float64), stego.astype(np.float64)) if cover.shape == stego.shape else psnr(
            cv2.resize(cover, (stego.shape[1], stego.shape[0])), stego)
        decoded = ss.decode(stego)
        acc = bit_accuracy(decoded, msg)
        psnrs.append(pv)
        accs.append(acc)
        if i == 0:
            cv2.imwrite(os.path.join(args.out, "example_single.png"), stego)
        print(f"  {os.path.basename(p):30s} PSNR={pv:5.1f}dB  bit_acc={acc:.3f}")
    print(f"  MEAN  PSNR={np.mean(psnrs):.1f}dB  bit_acc={np.mean(accs):.3f}")

    # ---- Table B: re-watermarking (StegaStamp victim > StegaStamp attacker) ----
    print("\n[Table B] re-watermarking: StegaStamp > StegaStamp (same scheme, different message)")
    victim_acc, attacker_acc, psnrs2 = [], [], []
    for i, p in enumerate(paths):
        cover = cv2.imread(p)
        victim_img = ss.encode(cover, msg)
        reatt_img = ss.encode(victim_img, msg2)
        pv = psnr(victim_img, reatt_img) if victim_img.shape == reatt_img.shape else psnr(
            cv2.resize(victim_img, (reatt_img.shape[1], reatt_img.shape[0])), reatt_img)
        decoded = ss.decode(reatt_img)
        v_acc = bit_accuracy(decoded, msg)       # did the ORIGINAL (victim) message survive?
        a_acc = bit_accuracy(decoded, msg2)      # did the ATTACKER's message win instead?
        victim_acc.append(v_acc)
        attacker_acc.append(a_acc)
        psnrs2.append(pv)
        if i == 0:
            cv2.imwrite(os.path.join(args.out, "example_rewatermarked.png"), reatt_img)
        print(f"  {os.path.basename(p):30s} PSNR={pv:5.1f}dB  victim_bit_acc={v_acc:.3f}  attacker_bit_acc={a_acc:.3f}")
    print(f"  MEAN  PSNR={np.mean(psnrs2):.1f}dB  victim_bit_acc={np.mean(victim_acc):.3f}  "
          f"attacker_bit_acc={np.mean(attacker_acc):.3f}")
    print("  (near 0.5 = watermark destroyed/coin-flip, matching dct_qim/fft_ring in sanity_check.py; "
          "near 1.0 = still fully readable)")

    print(f"\nExample images saved to {args.out}/")


if __name__ == "__main__":
    main()
