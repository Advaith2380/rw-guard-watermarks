"""
Phase 2 step 3 (plan item #12, part 2 of 2): dataset classes that mix the existing
classical on-the-fly watermark generator with a precomputed TrustMark image cache
(built by build_trustmark_cache.py). Drop this file in the project root, next to
train.py -- it imports from the existing rewm package, nothing in rewm/ needs editing.
"""
import os

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset

from rewm.data import apply_benign, BENIGN_TRAIN


class TrustMarkCacheDataset(Dataset):
    """Reads precomputed clean / single / rewm TrustMark images from build_trustmark_cache.py's
    output folder. Same {"x","y","kind"} item shape as rewm.data.ReWMDataset, so it's a drop-in."""

    def __init__(self, cache_dir, split, crop=0, train=True, benign_p=0.5, seed=0):
        self.dir = os.path.join(cache_dir, split)
        clean_dir = os.path.join(self.dir, "clean")
        assert os.path.isdir(clean_dir), f"{clean_dir} not found -- run build_trustmark_cache.py first"
        self.names = sorted(os.listdir(clean_dir))
        assert self.names, f"no cached images in {clean_dir} -- run build_trustmark_cache.py first"
        self.crop, self.train, self.benign_p, self.seed = crop, train, benign_p, seed

    def __len__(self):
        return len(self.names) * 2  # one negative-slot + one positive-slot per cached source image

    def __getitem__(self, idx):
        name = self.names[(idx // 2) % len(self.names)]
        if self.train:
            rng = np.random.default_rng()
            label = int(rng.random() < 0.5)
        else:
            rng = np.random.default_rng([self.seed, idx])
            label = idx % 2

        if label == 1:
            img = Image.open(os.path.join(self.dir, "rewm", name)).convert("RGB")
            kind = "trustmark>trustmark"
        else:
            sub = "clean" if rng.random() < 0.5 else "single"
            img = Image.open(os.path.join(self.dir, sub, name)).convert("RGB")
            kind = "clean" if sub == "clean" else "single:trustmark"

        arr = np.array(img, dtype=np.uint8)
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


class MixedDataset(Dataset):
    """Wraps a classical ReWMDataset and a TrustMarkCacheDataset: each __getitem__ draws
    from the TrustMark cache with probability trustmark_p, otherwise from the classical
    generator. Keeps the classical dataset's length, so epoch size is unchanged -- this
    just changes what fraction of samples are TrustMark vs. classical schemes."""

    def __init__(self, classical_ds, trustmark_ds, trustmark_p=0.25):
        self.classical, self.trustmark, self.p = classical_ds, trustmark_ds, trustmark_p

    def __len__(self):
        return len(self.classical)

    def __getitem__(self, idx):
        if np.random.rand() < self.p:
            j = np.random.randint(len(self.trustmark))
            return self.trustmark[j]
        return self.classical[idx]
