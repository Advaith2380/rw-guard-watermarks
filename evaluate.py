"""Full evaluation of a trained detector.

  python evaluate.py --ckpt runs/baseline/best.pt --data data/coco --pacs data/pacs --out results/baseline

Sections (each one targets a limitation from the literature review):
  1 in-distribution          seen watermark schemes, 256 px
  2 benign post-processing   JPEG / noise / blur / brightness (benign vs malicious edits)
  3 resolution               128 / 256 / 384 px (train crops were 128 px)
  4 unseen watermark scheme  only if the model was trained with --holdout
  5 cross-domain             PACS: photo / art_painting / cartoon / sketch
  6 adaptive adversary       white-box PGD against the detector (use --adv-eps-list)
"""
import argparse
import json
import os

import numpy as np
import torch
from torch.utils.data import DataLoader

from rewm.data import ReWMDataset, list_images, split_paths
from rewm.engine import pgd_attack, predict
from rewm.metrics import breakdown, roc_curve, summarize, threshold_at_fpr
from rewm.model import build_model
from rewm.watermarks import SCHEMES


def get_args():
    p = argparse.ArgumentParser()
    p.add_argument("--ckpt", required=True)
    p.add_argument("--data", default="data/coco")
    p.add_argument("--pacs", default="data/pacs")
    p.add_argument("--out", default="results/baseline")
    p.add_argument("--n-test", type=int, default=0, help="limit test source images (0 = all)")
    p.add_argument("--sizes", type=int, nargs="*", default=[128, 256, 384])
    p.add_argument("--benign", nargs="*", default=["none", "jpeg95", "jpeg85", "jpeg75", "noise1", "noise2", "blur0.5", "bright"])
    p.add_argument("--adv-eps-list", type=float, nargs="*", default=[0.5, 1.0, 2.0], help="PGD eps in /255 units")
    p.add_argument("--adv-n", type=int, default=100, help="positives attacked per eps")
    p.add_argument("--adv-size", type=int, default=128)
    p.add_argument("--bs", type=int, default=32)
    p.add_argument("--workers", type=int, default=4)
    return p.parse_args()


def fmt(name, m):
    g = lambda k: f"{m[k]:.3f}" if k in m else "-"
    return f"| {name} | {m['n']} | {g('auc')} | {g('tpr_at_1pct_fpr')} | {g('tpr_at_0p1pct_fpr')} | {g('tpr_fixed_thr')} | {g('fpr_fixed_thr')} |"


HEADER = ("| condition | n | AUC | TPR@1%FPR | TPR@0.1%FPR | TPR @fixed thr | FPR @fixed thr |\n"
          "|---|---|---|---|---|---|---|")


def main():
    a = get_args()
    os.makedirs(a.out, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    ck = torch.load(a.ckpt, map_location=device, weights_only=False)
    targs, seen = ck["args"], ck["train_schemes"]
    unseen = [s for s in SCHEMES if s not in seen]
    model = build_model(targs["arch"], targs["width"]).to(device)
    model.load_state_dict(ck["model"])
    model.eval()
    print(f"loaded {a.ckpt} (epoch {ck['epoch']}, val AUC {ck['val_auc']:.4f}); seen={seen} unseen={unseen}")

    paths = list_images(a.data)
    _, va, te = split_paths(paths)
    te = te[: a.n_test] if a.n_test else te
    va = va[: targs["n_val"]]

    def run(paths_, **kw):
        ds = ReWMDataset(paths_, train=False, seed=777, **kw)
        dl = DataLoader(ds, batch_size=a.bs, shuffle=False, num_workers=a.workers)
        return predict(model, dl, device)

    seen_kw = dict(victim_schemes=seen, attacker_schemes=seen, single_schemes=seen)

    # operating point: threshold that gives 1 % FPR on the *validation* negatives (in-distribution, 256 px)
    sv, yv, _ = run(va, size=256, benign_p=0.5, **seen_kw)
    thr = threshold_at_fpr(sv[yv == 0], 0.01)
    print(f"fixed operating threshold (val, 1% FPR): logit > {thr:.3f}")

    results, rows, curves, kinds_out = {"threshold": thr}, [], {}, {}

    def record(section, name, s, y, kinds):
        m = summarize(y, s, thr)
        results.setdefault(section, {})[name] = m
        rows.append((section, fmt(name, m)))
        curves[f"{section}/{name}"] = roc_curve(y, s)
        print(f"[{section}] {name:24s} AUC {m['auc']:.3f}  TPR@1%FPR {m['tpr_at_1pct_fpr']:.3f}  "
              f"fixed-thr TPR {m['tpr_fixed_thr']:.3f} FPR {m['fpr_fixed_thr']:.3f}")
        return kinds

    # 1 in-distribution
    s, y, k = run(te, size=256, benign_p=0.5, **seen_kw)
    record("1 in-distribution", "COCO 256px (seen schemes)", s, y, k)
    kinds_out["in-distribution"] = breakdown(y, s, k, thr)

    # 2 benign post-processing
    for b in a.benign:
        s, y, k = run(te, size=256, benign=b, **seen_kw)
        record("2 benign post-processing", b, s, y, k)

    # 3 resolution
    for sz in a.sizes:
        s, y, k = run(te, size=sz, benign_p=0.5, **seen_kw)
        record("3 resolution", f"{sz}px", s, y, k)

    # 4 unseen schemes
    if unseen:
        s, y, k = run(te, size=256, benign_p=0.5, victim_schemes=seen, attacker_schemes=unseen,
                      single_schemes=seen + unseen)
        record("4 unseen scheme", f"unseen attacker {unseen}", s, y, k)
        kinds_out["unseen attacker"] = breakdown(y, s, k, thr)
        s, y, k = run(te, size=256, benign_p=0.5, victim_schemes=unseen, attacker_schemes=unseen,
                      single_schemes=seen + unseen)
        record("4 unseen scheme", f"unseen victim+attacker {unseen}", s, y, k)
        kinds_out["unseen both"] = breakdown(y, s, k, thr)

    # 5 cross-domain
    if a.pacs and os.path.isdir(a.pacs):
        for dom in sorted(d for d in os.listdir(a.pacs) if os.path.isdir(os.path.join(a.pacs, d))):
            dp = list_images(os.path.join(a.pacs, dom))
            if not dp:
                continue
            s, y, k = run(dp, size=224, benign_p=0.5, **seen_kw)
            record("5 cross-domain (PACS)", dom, s, y, k)
    else:
        print("PACS folder not found - skipping cross-domain section")

    # 6 adaptive adversary (white-box PGD, positives only)
    if a.adv_eps_list:
        ds = ReWMDataset(te[: a.adv_n], size=a.adv_size, train=False, seed=888, benign_p=0.0, **seen_kw)
        pos = [ds[i] for i in range(1, len(ds), 2)]                  # odd idx = positives
        x = torch.stack([p["x"] for p in pos]).to(device)
        y = torch.ones(len(pos), device=device)
        with torch.no_grad():
            base = model(x).cpu().numpy()
        results["6 adversarial"] = {"clean positives detected": float((base > thr).mean())}
        print(f"[6 adversarial] no attack: {(base > thr).mean():.3f} of {len(pos)} positives flagged")
        for e in a.adv_eps_list:
            adv = []
            for i in range(0, len(x), 16):
                xa = pgd_attack(model, x[i:i + 16], y[i:i + 16], e / 255.0, steps=10)
                with torch.no_grad():
                    adv.append(model(xa).cpu().numpy())
            adv = np.concatenate(adv)
            results["6 adversarial"][f"PGD-10 eps={e}/255"] = float((adv > thr).mean())
            print(f"[6 adversarial] PGD-10 eps={e}/255: {(adv > thr).mean():.3f} of positives still flagged")

    with open(os.path.join(a.out, "results.json"), "w") as f:
        json.dump(dict(results=results, breakdown=kinds_out), f, indent=2)

    md = [f"# Results for `{a.ckpt}`\n", f"Seen schemes: {seen} - unseen: {unseen or 'none'}\n",
          f"Fixed operating point: logit > {thr:.3f} (1% FPR on validation)\n"]
    for sec in sorted({r[0] for r in rows}):
        md += [f"\n## {sec}\n", HEADER] + [r[1] for r in rows if r[0] == sec]
    if "6 adversarial" in results:
        md += ["\n## 6 adversarial (fraction of re-watermarked images still flagged)\n", "| attack | detected |", "|---|---|"]
        md += [f"| {k} | {v:.3f} |" for k, v in results["6 adversarial"].items()]
    md += ["\n## Per watermark-combination (in-distribution, fraction flagged as re-watermarked)\n", "| combo | label | n | flagged |", "|---|---|---|---|"]
    md += [f"| {k} | {v['label']} | {v['n']} | {v['flagged']:.3f} |" for k, v in kinds_out["in-distribution"].items()]
    with open(os.path.join(a.out, "results.md"), "w") as f:
        f.write("\n".join(md))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.figure(figsize=(6, 5))
        for name, (fpr, tpr) in curves.items():
            if name.startswith(("1 ", "4 ", "5 ")):
                plt.plot(fpr, tpr, label=name.split("/", 1)[1])
        plt.xscale("log"); plt.xlim(1e-3, 1); plt.ylim(0, 1.02)
        plt.xlabel("False-positive rate"); plt.ylabel("True-positive rate"); plt.grid(alpha=.3); plt.legend(fontsize=7)
        plt.title("ROC - re-watermark detector"); plt.tight_layout()
        plt.savefig(os.path.join(a.out, "roc.png"), dpi=200)
    except Exception as ex:                       # plotting is optional
        print("could not plot ROC:", ex)
    print(f"\nwrote {a.out}/results.md, results.json, roc.png")


if __name__ == "__main__":
    main()
