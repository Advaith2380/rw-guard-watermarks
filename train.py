"""Train the re-watermarking detector.

Examples
  python train.py --data data/coco --out runs/baseline
  python train.py --data data/coco --out runs/holdout_fft --holdout fft_ring      # unseen-scheme test
  python train.py --data data/coco --out runs/adv --adv-eps 1.0                   # adversarial training
"""
import argparse
import json
import os
import time

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from tqdm import tqdm

from rewm.data import ReWMDataset, list_images, split_paths
from rewm.engine import pgd_attack, predict
from rewm.metrics import roc_auc, tpr_at_fpr
from rewm.model import build_model
from rewm.watermarks import SCHEMES


def get_args():
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="data/coco")
    p.add_argument("--out", default="runs/baseline")
    p.add_argument("--arch", default="forensic", choices=["forensic", "forensic_nohp", "simple", "resnet18"])
    p.add_argument("--width", type=int, default=32)
    p.add_argument("--size", type=int, default=256, help="images are resized/cropped to this before watermarking")
    p.add_argument("--crop", type=int, default=128, help="random crop fed to the network (0 = no crop)")
    p.add_argument("--epochs", type=int, default=15)
    p.add_argument("--bs", type=int, default=32)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--n-train", type=int, default=0, help="limit number of training source images (0 = all)")
    p.add_argument("--n-val", type=int, default=300)
    p.add_argument("--repeat", type=int, default=4,
                   help="samples per source image per epoch (each one gets a fresh random watermark)")
    p.add_argument("--holdout", nargs="*", default=[], help="scheme(s) never shown during training")
    p.add_argument("--benign-p", type=float, default=0.5)
    p.add_argument("--adv-eps", type=float, default=0.0, help="PGD eps in /255 units; 0 = off")
    p.add_argument("--adv-steps", type=int, default=3)
    p.add_argument("--adv-start", type=int, default=2, help="epochs of clean warm-up before adversarial training")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--init", default="", help="checkpoint (.pt) whose weights to start from, to continue training")
    p.add_argument("--seed", type=int, default=0)
    return p.parse_args()


def main():
    args = get_args()
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    os.makedirs(args.out, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"device: {device}")

    paths = list_images(args.data)
    assert paths, f"no images found in {args.data} - run download_data.py first"
    tr, va, _ = split_paths(paths)
    if args.n_train:
        tr = tr[: args.n_train]
    va = va[: args.n_val]
    schemes = [s for s in SCHEMES if s not in args.holdout]
    print(f"train images: {len(tr)}  val images: {len(va)}  schemes seen in training: {schemes}")

    common = dict(victim_schemes=schemes, attacker_schemes=schemes, single_schemes=schemes)
    ds_tr = ReWMDataset(tr, size=args.size, crop=args.crop, train=True, repeat=args.repeat,
                        benign_p=args.benign_p, **common)
    ds_va = ReWMDataset(va, size=args.size, crop=0, train=False, seed=123, benign_p=0.5, **common)
    dl_tr = DataLoader(ds_tr, batch_size=args.bs, shuffle=True, num_workers=args.workers,
                       drop_last=True, persistent_workers=args.workers > 0)
    dl_va = DataLoader(ds_va, batch_size=32, shuffle=False, num_workers=args.workers)

    model = build_model(args.arch, args.width).to(device)
    if args.init:
        model.load_state_dict(torch.load(args.init, map_location=device, weights_only=False)["model"])
        print(f"initialised weights from {args.init}")
    print(f"parameters: {sum(p.numel() for p in model.parameters()) / 1e6:.2f} M")
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=args.lr, total_steps=args.epochs * len(dl_tr))

    history, best = [], -1.0
    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        model.train()
        run_loss, run_acc, n = 0.0, 0.0, 0
        use_adv = args.adv_eps > 0 and epoch > args.adv_start
        for b in tqdm(dl_tr, desc=f"epoch {epoch}/{args.epochs}", leave=False):
            x, y = b["x"].to(device), b["y"].to(device)
            if use_adv:                                    # half of every batch becomes adversarial
                model.eval()
                xa = pgd_attack(model, x, y, args.adv_eps / 255.0, steps=args.adv_steps)
                model.train()
                mask = (torch.rand(len(x), device=device) < 0.5)[:, None, None, None]
                x = torch.where(mask, xa, x)
            logit = model(x)
            loss = F.binary_cross_entropy_with_logits(logit, y)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            sched.step()
            run_loss += loss.item() * len(y)
            run_acc += ((logit > 0).float() == y).float().sum().item()
            n += len(y)

        s, yv, _ = predict(model, dl_va, device, desc="validate")
        auc, tpr1 = roc_auc(yv, s), tpr_at_fpr(yv, s, 0.01)
        rec = dict(epoch=epoch, train_loss=run_loss / n, train_acc=run_acc / n, val_auc=auc,
                   val_tpr_at_1pct_fpr=tpr1, seconds=time.time() - t0, adversarial=use_adv)
        history.append(rec)
        print(f"epoch {epoch:2d} | loss {rec['train_loss']:.4f} | train acc {rec['train_acc']:.3f} | "
              f"val AUC {auc:.4f} | val TPR@1%FPR {tpr1:.3f} | {rec['seconds']:.0f}s" + (" | adv" if use_adv else ""))

        ckpt = dict(model=model.state_dict(), args=vars(args), train_schemes=schemes, epoch=epoch, val_auc=auc)
        torch.save(ckpt, os.path.join(args.out, "last.pt"))
        if auc >= best:
            best = auc
            torch.save(ckpt, os.path.join(args.out, "best.pt"))
        with open(os.path.join(args.out, "history.json"), "w") as f:
            json.dump(history, f, indent=2)
    print(f"done. best val AUC {best:.4f}  ->  {os.path.join(args.out, 'best.pt')}")


if __name__ == "__main__":
    main()
