"""Integration tests for Faculty Review scientific implementations."""

import unittest
import numpy as np
import torch
import torch.nn.functional as F

from rewm.outcomes import classify_attack_outcome, compute_bit_accuracy
from rewm.watermarks import SCHEMES, STRENGTH_RANGE, psnr, NBITS
from bootstrap_ci import compute_bootstrap_cis
from shortcut_baseline import extract_batch_features, TorchLogisticRegression
from matched_controls import find_matched_strength


class TestFacultyIntegrations(unittest.TestCase):
    def test_four_attack_outcome_categories(self):
        tau = 0.75
        
        # Category 1: Overwrite (Victim < tau, Attacker >= tau)
        res1 = classify_attack_outcome(
            np.zeros((64, 64, 3), dtype=np.uint8),
            {"scheme": "dct_qim", "key": 1, "bits": np.ones(NBITS), "strength": 20.0},
            {"scheme": "dwt_qim", "key": 2, "bits": np.ones(NBITS), "strength": 25.0},
            threshold=tau
        )
        # Verify category ID and outcome string are present
        self.assertIn("outcome", res1)
        self.assertIn("category_id", res1)
        self.assertIn(res1["outcome"], [
            "successful_overwrite", "dual_survival", "failed_attacker_embedding", "both_unrecoverable"
        ])

    def test_feature_extraction_dimension_and_finite(self):
        # Synthetic RGB batch (B=4, C=3, H=64, W=64)
        x = torch.rand(4, 3, 64, 64)
        feats = extract_batch_features(x)
        self.assertEqual(feats.shape, (4, 10))
        self.assertFalse(torch.isnan(feats).any())
        self.assertFalse(torch.isinf(feats).any())

    def test_grouped_source_bootstrap_reproducibility(self):
        rng = np.random.default_rng(123)
        # 100 source images, each generating 1 neg and 1 pos (200 samples)
        n_sources = 100
        source_ids = np.repeat(np.arange(n_sources), 2)
        y = np.tile([0, 1], n_sources)
        scores = np.zeros(2 * n_sources)
        scores[y == 0] = rng.normal(-1.0, 1.0, n_sources)
        scores[y == 1] = rng.normal(1.0, 1.0, n_sources)

        cis = compute_bootstrap_cis(y, scores, thr=0.0, source_ids=source_ids, n_bootstraps=200, seed=42)
        self.assertEqual(cis["n_unique_sources"], n_sources)
        self.assertEqual(cis["n_samples"], 2 * n_sources)
        self.assertGreater(cis["metrics"]["auc"]["point_estimate"], 0.8)
        ci_auc = cis["metrics"]["auc"]["ci_95"]
        self.assertLess(ci_auc[0], ci_auc[1])

    def test_strength_matching_binary_search(self):
        im = (np.random.rand(64, 64, 3) * 255).astype(np.uint8)
        scheme_name = "dct_qim"
        key = 42
        bits = np.random.randint(0, 2, 64)
        
        # Generate target double watermark MSE
        target_mse = 15.0
        best_img, best_str, cand_mse, mismatch = find_matched_strength(
            im, scheme_name, key, bits, target_mse, tol=1.0, max_iter=8
        )
        self.assertIsNotNone(best_img)
        self.assertGreater(best_str, 0)
        self.assertLess(mismatch, 5.0)  # Verify search converges close to target


if __name__ == "__main__":
    unittest.main()
