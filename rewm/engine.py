import numpy as np
import torch
import torch.nn.functional as F
from tqdm import tqdm


@torch.no_grad()
def predict(model, loader, device, desc="predict"):
    model.eval()
    logits, ys, kinds = [], [], []
    for b in tqdm(loader, desc=desc, leave=False):
        logits.append(model(b["x"].to(device)).float().cpu())
        ys.append(b["y"])
        kinds += list(b["kind"])
    return torch.cat(logits).numpy(), torch.cat(ys).numpy().astype(int), np.array(kinds)


@torch.no_grad()
def predict_with_outcomes(model, loader, device, desc="predict"):
    model.eval()
    logits, ys, kinds, outcomes = [], [], [], []
    for b in tqdm(loader, desc=desc, leave=False):
        logits.append(model(b["x"].to(device)).float().cpu())
        ys.append(b["y"])
        kinds += list(b["kind"])
        outcomes += list(b.get("outcome", ["n/a"] * len(b["y"])))
    return (
        torch.cat(logits).numpy(),
        torch.cat(ys).numpy().astype(int),
        np.array(kinds),
        np.array(outcomes)
    )


def pgd_attack(model, x, y, eps, steps=10, step_frac=2.5, restarts=1):
    """White-box L-inf PGD that *maximises* the detector's loss (attacker's worst-case for defender).
    Supports multiple random restarts (restarts >= 1) to find worst-case adversarial perturbation.
    eps is in [0,1] pixel units (e.g. 2/255). The model must already be in eval() mode.
    """
    alpha = step_frac * eps / steps
    best_xa = x.clone()
    best_loss = torch.full((len(x),), -float("inf"), device=x.device)

    for _ in range(max(1, restarts)):
        xa = (x + torch.empty_like(x).uniform_(-eps, eps)).clamp(0, 1)
        for _ in range(steps):
            xa.requires_grad_(True)
            loss = F.binary_cross_entropy_with_logits(model(xa), y, reduction="sum")
            (g,) = torch.autograd.grad(loss, xa)
            xa = xa.detach() + alpha * g.sign()
            xa = torch.min(torch.max(xa, x - eps), x + eps).clamp(0, 1)

        with torch.no_grad():
            cur_loss = F.binary_cross_entropy_with_logits(model(xa), y, reduction="none")
            better_mask = cur_loss > best_loss
            best_loss = torch.where(better_mask, cur_loss, best_loss)
            best_xa = torch.where(better_mask.view(-1, 1, 1, 1), xa, best_xa)

    return best_xa.detach()
