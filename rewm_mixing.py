"""
Generalises rewm_trustmark.MixedDataset (one classical + one neural source) to any
number of neural-watermarker caches at once, so a single training run can mix
classical schemes + TrustMark + StegaStamp together -- useful once you have both
caches built and want one detector trained against the broadest possible mix.
"""
import numpy as np
from torch.utils.data import Dataset


class MultiMixedDataset(Dataset):
    """Wraps a classical ReWMDataset plus any number of named (dataset, probability) neural
    sources. Each __getitem__ draws from one of the neural sources with its given probability,
    otherwise falls back to the classical generator. Probabilities should sum to <= 1.0; the
    remainder is the classical-scheme share. Keeps the classical dataset's length, so epoch
    size is unchanged -- this only changes what fraction of samples are classical vs. neural."""

    def __init__(self, classical_ds, sources):
        """sources: list of (name: str, dataset: Dataset, probability: float)."""
        self.classical = classical_ds
        self.sources = list(sources)
        total_p = sum(p for _, _, p in self.sources)
        assert total_p <= 1.0 + 1e-6, f"neural-source probabilities sum to {total_p:.3f} > 1.0"

    def __len__(self):
        return len(self.classical)

    def __getitem__(self, idx):
        r = np.random.rand()
        acc = 0.0
        for _, ds, p in self.sources:
            acc += p
            if r < acc:
                j = np.random.randint(len(ds))
                return ds[j]
        return self.classical[idx]
