"""On-the-fly dataset: every sample is a fresh random watermark configuration.

label 0  ->  clean image (50 %)  or  singly watermarked image (50 %)
label 1  ->  re-watermarked: victim scheme A  then  attacker scheme B (independent
             keys / messages / strengths; A and B may be the same or different schemes)
Then, with probability benign_p, ONE benign operation (JPEG, noise, blur, brightness)
is applied to every class equally, so the network cannot use "was post-processed" as a shortcut.
"""
import os
import cv2
import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset

from .watermarks import SCHEMES, embed_random

cv2.setNumThreads(0)
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
BENIGN_TRAIN = ["jpeg", "noise", "blur", "bright"]


def list_images(folder):
    out = []
    for root, _, files in os.walk(folder):
        for f in files:
            if os.path.splitext(f)[1].lower() in IMG_EXT:
                out.append(os.path.join(root, f))
    return sorted(out)


def split_paths(paths, seed=0, fractions=(0.6, 0.1, 0.3)):
    """Deterministic train / val / test split of *source images* (no image appears in two splits)."""
    idx = np.random.default_rng(seed).permutation(len(paths))
    n_tr, n_va = int(fractions[0] * len(paths)), int(fractions[1] * len(paths))
    pick = lambda ii: [paths[i] for i in ii]
    return pick(idx[:n_tr]), pick(idx[n_tr:n_tr + n_va]), pick(idx[n_tr + n_va:])


def load_image(path, size, rng=None):
    """Resize the short side to `size` (this also removes the source JPEG 8x8 grid), then crop.
    rng given -> random crop offset + random flip (training); None -> centre crop (evaluation)."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    s = size / min(w, h)
    nw, nh = max(size, round(w * s)), max(size, round(h * s))
    im = im.resize((nw, nh), Image.BICUBIC)
    if rng is None:
        left, top = (nw - size) // 2, (nh - size) // 2
    else:
        left, top = int(rng.integers(0, nw - size + 1)), int(rng.integers(0, nh - size + 1))
    arr = np.array(im.crop((left, top, left + size, top + size)), dtype=np.uint8)
    if rng is not None and rng.random() < 0.5:
        arr = arr[:, ::-1]
    return np.ascontiguousarray(arr)


def apply_benign(img, name, rng):
    """name: none | jpeg | jpeg85 | noise | noise2 | blur | blur0.6 | bright"""
    if name == "none":
        return img
    if name.startswith("jpeg"):
        q = int(name[4:]) if len(name) > 4 else int(rng.integers(70, 96))
        ok, buf = cv2.imencode(".jpg", img[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, q])
        return cv2.imdecode(buf, cv2.IMREAD_COLOR)[..., ::-1].copy()
    if name.startswith("noise"):
        sigma = float(name[5:]) if len(name) > 5 else float(rng.uniform(0.5, 2.5))
        out = img.astype(np.float32) + rng.normal(0, sigma, img.shape).astype(np.float32)
        return np.clip(np.rint(out), 0, 255).astype(np.uint8)
    if name.startswith("blur"):
        sigma = float(name[4:]) if len(name) > 4 else float(rng.uniform(0.4, 0.9))
        return cv2.GaussianBlur(img, (0, 0), sigma)
    if name == "bright":
        gain, off = float(rng.uniform(0.9, 1.1)), float(rng.uniform(-8, 8))
        return np.clip(np.rint(img.astype(np.float32) * gain + off), 0, 255).astype(np.uint8)
    raise ValueError(f"unknown benign op: {name}")


class ReWMDataset(Dataset):
    def __init__(self, paths, size=256, crop=0, train=False, seed=0, repeat=None,
                 victim_schemes=None, attacker_schemes=None, single_schemes=None,
                 benign=None, benign_p=0.5):
        self.paths, self.size, self.crop, self.train, self.seed = list(paths), size, crop, train, seed
        allowed = list(SCHEMES)
        self.victim = list(victim_schemes or allowed)
        self.attacker = list(attacker_schemes or allowed)
        self.single = list(single_schemes or allowed)
        self.benign, self.benign_p = benign, benign_p
        self.repeat = repeat if repeat is not None else (1 if train else 2)

    def __len__(self):
        return len(self.paths) * self.repeat

    def __getitem__(self, idx):
        if self.train:
            rng = np.random.default_rng()
            img = load_image(self.paths[idx % len(self.paths)], self.size, rng)
            label = int(rng.random() < 0.5)
        else:  # deterministic: every source image appears once as negative and once as positive
            rng = np.random.default_rng([self.seed, idx])
            img = load_image(self.paths[idx // 2], self.size, None)
            label = idx % 2

        if label == 1:
            a, b = str(rng.choice(self.victim)), str(rng.choice(self.attacker))
            img = embed_random(embed_random(img, a, rng), b, rng)
            kind = f"{a}>{b}"
        elif rng.random() < 0.5:
            kind = "clean"
        else:
            s = str(rng.choice(self.single))
            img = embed_random(img, s, rng)
            kind = f"single:{s}"

        if self.benign is not None:
            img = apply_benign(img, self.benign, rng)
        elif rng.random() < self.benign_p:
            img = apply_benign(img, str(rng.choice(BENIGN_TRAIN)), rng)

        if self.crop and self.crop < min(img.shape[:2]):   # arbitrary offset: grid-shift invariance
            t = int(rng.integers(0, img.shape[0] - self.crop + 1))
            l = int(rng.integers(0, img.shape[1] - self.crop + 1))
            img = img[t:t + self.crop, l:l + self.crop]

        x = torch.from_numpy(np.array(img, dtype=np.uint8)).permute(2, 0, 1).float() / 255.0
        return {"x": x, "y": torch.tensor(float(label)), "kind": kind}
