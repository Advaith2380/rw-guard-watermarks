"""Step-2 check: do the watermark simulators behave like real watermarkers?

  python sanity_check.py --data data/coco

Prints (1) invisibility (PSNR) and single-embedding decode accuracy per scheme and
(2) what a re-watermarking attack does to the victim's message for every (victim, attacker)
pair, and saves sanity/example.png with amplified difference maps.
"""
import argparse
import os

import numpy as np

from rewm.data import list_images, load_image
from rewm.watermarks import NBITS, SCHEMES, embed_random, psnr


def bitacc(img, info):
    sc = SCHEMES[info["scheme"]].extract(img, info["key"], NBITS, info["strength"])
    return float(np.mean((sc > 0) == info["bits"]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="data/coco")
    p.add_argument("--n", type=int, default=8)
    p.add_argument("--size", type=int, default=256)
    p.add_argument("--out", default="sanity")
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    imgs = [load_image(f, a.size) for f in list_images(a.data)[: a.n]]
    rng = np.random.default_rng(0)
    names = list(SCHEMES)

    print("\n1) single embedding  (PSNR in dB, bit accuracy of the owner's own decoder)")
    print(f"{'scheme':12s} {'PSNR':>6s} {'bit-acc':>8s}")
    for s in names:
        ps, ac = [], []
        for im in imgs:
            out, info = embed_random(im, s, rng, return_info=True)
            ps.append(psnr(im, out)); ac.append(bitacc(out, info))
        print(f"{s:12s} {np.mean(ps):6.1f} {np.mean(ac):8.2f}")

    print("\n2) re-watermarking:  victim bit-acc AFTER the attack | attacker bit-acc | PSNR(original, result)")
    print("   (0.50 = chance = victim message destroyed; 1.00 = still readable)")
    print(f"{'victim > attacker':26s} {'victim':>7s} {'attacker':>9s} {'PSNR':>6s}")
    for v in names:
        for t in names:
            va, ta, ps = [], [], []
            for im in imgs:
                o1, i1 = embed_random(im, v, rng, return_info=True)
                o2, i2 = embed_random(o1, t, rng, return_info=True)
                va.append(bitacc(o2, i1)); ta.append(bitacc(o2, i2)); ps.append(psnr(im, o2))
            print(f"{v + ' > ' + t:26s} {np.mean(va):7.2f} {np.mean(ta):9.2f} {np.mean(ps):6.1f}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        pairs = [("dct_qim", "dct_qim"), ("dct_qim", "fft_ring"), ("ss_spatial", "dwt_qim")]
        fig, ax = plt.subplots(len(pairs), 5, figsize=(15, 3.1 * len(pairs)))
        im = imgs[0]
        for r, (v, t) in enumerate(pairs):
            o1 = embed_random(im, v, rng); o2 = embed_random(o1, t, rng)
            diff = lambda o: np.clip(np.abs(o.astype(int) - im.astype(int)) * 20, 0, 255).astype(np.uint8)
            panels = [(im, "original"), (o1, f"victim: {v}"), (o2, f"re-watermarked: +{t}"),
                      (diff(o1), "|victim - original| x20"), (diff(o2), "|re-wm - original| x20")]
            for c, (pim, title) in enumerate(panels):
                ax[r, c].imshow(pim); ax[r, c].set_title(title, fontsize=9); ax[r, c].axis("off")
        plt.tight_layout(); plt.savefig(os.path.join(a.out, "example.png"), dpi=150)
        print(f"\nsaved {a.out}/example.png")
    except Exception as ex:
        print("could not draw figure:", ex)


if __name__ == "__main__":
    main()
