"""
Training-time mixing dataset for a precomputed StegaStamp cache (build_stegastamp_cache.py's
output). Split out from rewm_stegastamp.py so that module stays torch-free (it's needed by
test_stegastamp.py and build_stegastamp_cache.py, neither of which touches PyTorch); this file
is the one that needs torch, and only train_with_neural.py imports it.
"""
import os

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset

from rewm.data import BENIGN_TRAIN, apply_benign


class StegaStampCacheDataset(Dataset):
    """Mirrors rewm_trustmark.TrustMarkCacheDataset exactly, reading precomputed clean/single/rewm
    StegaStamp images instead. Same {"x","y","kind"} item shape as rewm.data.ReWMDataset, so it's
    a drop-in for MixedDataset / MultiMixedDataset (see rewm_mixing.py)."""

    def __init__(self, cache_dir, split, crop=0, train=True, benign_p=0.5, seed=0):
        self.dir = os.path.join(cache_dir, split)
        clean_dir = os.path.join(self.dir, "clean")
        assert os.path.isdir(clean_dir), f"{clean_dir} not found -- run build_stegastamp_cache.py first"
        self.names = sorted(os.listdir(clean_dir))
        assert self.names, f"no cached images in {clean_dir} -- run build_stegastamp_cache.py first"
        self.crop, self.train, self.benign_p, self.seed = crop, train, benign_p, seed

    def __len__(self):
        return len(self.names) * 2  # one negative-slot + one positive-slot per cached source image

    def __getitem__(self, idx):
        name = self.names[(idx // 2) % len(self.names)]
        rng = np.random.default_rng() if self.train else np.random.default_rng([self.seed, idx])
        label = int(rng.random() < 0.5) if self.train else idx % 2

        if label == 1:
            img_bgr = cv2.imread(os.path.join(self.dir, "rewm", name))
            kind = "stegastamp>stegastamp"
        else:
            sub = "clean" if rng.random() < 0.5 else "single"
            img_bgr = cv2.imread(os.path.join(self.dir, sub, name))
            kind = "clean" if sub == "clean" else "single:stegastamp"
        arr = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

        if self.train and rng.random() < 0.5:
            arr = arr[:, ::-1].copy()
        if self.crop and self.crop < min(arr.shape[:2]):
            if self.train:
                t = int(rng.integers(0, arr.shape[0] - self.crop + 1))
                l = int(rng.integers(0, arr.shape[1] - self.crop + 1))
            else:
                t, l = (arr.shape[0] - self.crop) // 2, (arr.shape[1] - self.crop) // 2
            arr = arr[t:t + self.crop, l:l + self.crop]
        if rng.random() < self.benign_p:
            arr = apply_benign(arr, str(rng.choice(BENIGN_TRAIN)), rng)

        x = torch.from_numpy(np.ascontiguousarray(arr, dtype=np.uint8)).permute(2, 0, 1).float() / 255.0
        return {"x": x, "y": torch.tensor(float(label)), "kind": kind}
