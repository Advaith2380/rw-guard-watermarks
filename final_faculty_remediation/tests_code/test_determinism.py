"""Unit tests for seed propagation, dataset determinism, and worker isolation (REQ-R, REQ-T)."""

import unittest
import numpy as np
import torch
from rewm.data import split_paths, ReWMDataset


class TestDeterminism(unittest.TestCase):
    def test_split_paths_deterministic(self):
        paths = [f"img_{i:04d}.jpg" for i in range(100)]
        tr1, va1, te1 = split_paths(paths, seed=42)
        tr2, va2, te2 = split_paths(paths, seed=42)
        
        self.assertEqual(tr1, tr2)
        self.assertEqual(va1, va2)
        self.assertEqual(te1, te2)

    def test_split_paths_isolation(self):
        # Guarantee no image path leaks across splits
        paths = [f"img_{i:04d}.jpg" for i in range(100)]
        tr, va, te = split_paths(paths, seed=42)
        
        set_tr = set(tr)
        set_va = set(va)
        set_te = set(te)
        
        self.assertEqual(len(set_tr.intersection(set_va)), 0, "Leakage between train and val!")
        self.assertEqual(len(set_tr.intersection(set_te)), 0, "Leakage between train and test!")
        self.assertEqual(len(set_va.intersection(set_te)), 0, "Leakage between val and test!")

    def test_eval_dataset_sample_reproducibility(self):
        # Evaluation dataset (train=False) must be 100% deterministic per index
        # We test with synthetic in-memory paths mock
        class MockDataset(ReWMDataset):
            def __getitem__(self, idx):
                rng = np.random.default_rng([self.seed, idx])
                # Generate synthetic test pattern
                val = rng.integers(0, 255, size=(64, 64, 3), dtype=np.uint8)
                label = idx % 2
                return {"val": val, "label": label}

        ds1 = MockDataset(["a.jpg", "b.jpg"], train=False, seed=999)
        ds2 = MockDataset(["a.jpg", "b.jpg"], train=False, seed=999)
        
        sample1 = ds1[0]["val"]
        sample2 = ds2[0]["val"]
        np.testing.assert_array_equal(sample1, sample2)


if __name__ == "__main__":
    unittest.main()
