"""Unit tests for rewm.metrics and bootstrap CI calculations."""

import unittest
import numpy as np
from rewm.metrics import roc_auc, tpr_at_fpr, rates_at, threshold_at_fpr, summarize
from bootstrap_ci import compute_bootstrap_cis


class TestMetrics(unittest.TestCase):
    def test_roc_auc_perfect(self):
        y = np.array([0, 0, 0, 1, 1, 1])
        scores = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
        self.assertAlmostEqual(roc_auc(y, scores), 1.0)

    def test_roc_auc_inverted(self):
        y = np.array([0, 0, 0, 1, 1, 1])
        scores = np.array([0.9, 0.8, 0.7, 0.3, 0.2, 0.1])
        self.assertAlmostEqual(roc_auc(y, scores), 0.0)

    def test_roc_auc_chance(self):
        # Interleaved scores
        y = np.array([0, 1, 0, 1, 0, 1])
        scores = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
        auc = roc_auc(y, scores)
        self.assertTrue(0.4 <= auc <= 0.8)

    def test_threshold_at_fpr(self):
        # 100 negative scores uniformly spaced [0, 99]
        neg_scores = np.arange(100, dtype=float)
        # At 1% FPR, threshold should be around the 99th percentile (98.01)
        thr = threshold_at_fpr(neg_scores, 0.01)
        self.assertGreaterEqual(thr, 98.0)
        # At 5% FPR, threshold should be around the 95th percentile (94.05)
        thr5 = threshold_at_fpr(neg_scores, 0.05)
        self.assertGreaterEqual(thr5, 94.0)

    def test_rates_at(self):
        y = np.array([0, 0, 1, 1])
        scores = np.array([0.2, 0.8, 0.6, 0.9])
        # Threshold at 0.5:
        # Negatives > 0.5: score 0.8 (1 of 2 => FPR = 0.5)
        # Positives > 0.5: scores 0.6, 0.9 (2 of 2 => TPR = 1.0)
        tpr, fpr = rates_at(y, scores, 0.5)
        self.assertEqual(tpr, 1.0)
        self.assertEqual(fpr, 0.5)

    def test_summarize_format(self):
        y = np.array([0, 0, 1, 1])
        scores = np.array([0.1, 0.2, 0.8, 0.9])
        res = summarize(y, scores, 0.5)
        self.assertIn("n", res)
        self.assertIn("auc", res)
        self.assertIn("tpr_at_1pct_fpr", res)
        self.assertIn("tpr_at_0p1pct_fpr", res)
        self.assertIn("tpr_fixed_thr", res)
        self.assertIn("fpr_fixed_thr", res)
        self.assertEqual(res["auc"], 1.0)

    def test_bootstrap_ci(self):
        rng = np.random.default_rng(42)
        y = np.concatenate([np.zeros(100), np.ones(100)])
        scores = np.concatenate([rng.normal(0, 1, 100), rng.normal(2, 1, 100)])
        cis = compute_bootstrap_cis(y, scores, n_bootstraps=200, seed=42)
        
        auc_pe = cis["metrics"]["auc"]["point_estimate"]
        ci_low, ci_high = cis["metrics"]["auc"]["ci_95"]
        
        self.assertTrue(0.80 <= auc_pe <= 0.98)
        self.assertLessEqual(ci_low, auc_pe)
        self.assertGreaterEqual(ci_high, auc_pe)


if __name__ == "__main__":
    unittest.main()
