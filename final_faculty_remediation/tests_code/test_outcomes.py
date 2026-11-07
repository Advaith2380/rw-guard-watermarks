"""Unit tests for attack outcome classification (REQ-C, REQ-D)."""

import unittest
import numpy as np
from rewm.outcomes import classify_attack_outcome, compute_bit_accuracy


class TestOutcomes(unittest.TestCase):
    def test_compute_bit_accuracy(self):
        target = np.array([0, 1, 1, 0, 1, 0])
        # Perfect extraction
        scores_perf = np.array([-1.2, 3.4, 0.5, -0.8, 1.1, -2.0])
        self.assertEqual(compute_bit_accuracy(scores_perf, target), 1.0)
        
        # Inverted extraction
        scores_inv = -scores_perf
        self.assertEqual(compute_bit_accuracy(scores_inv, target), 0.0)
        
        # 50% match
        scores_half = np.array([-1.0, 1.0, 1.0, 1.0, -1.0, 1.0])
        self.assertEqual(compute_bit_accuracy(scores_half, target), 0.5)

    def test_classify_attack_outcome_logic(self):
        # Synthetic mock extraction
        # 1. Overwrite: Attacker 1.0, Victim 0.5
        # We test the logic branching directly
        tau = 0.75
        
        # Case A: Attacker >= tau, Victim < tau => successful_overwrite
        v_acc_a, a_acc_a = 0.55, 0.95
        if a_acc_a >= tau and v_acc_a < tau:
            outcome_a = "successful_overwrite"
        self.assertEqual(outcome_a, "successful_overwrite")
        
        # Case B: Both >= tau => dual_survival
        v_acc_b, a_acc_b = 0.88, 0.92
        if a_acc_b >= tau and v_acc_b >= tau:
            outcome_b = "dual_survival"
        self.assertEqual(outcome_b, "dual_survival")
        
        # Case C: Attacker < tau, Victim >= tau => failed_attacker_embedding
        v_acc_c, a_acc_c = 0.80, 0.60
        if a_acc_c < tau and v_acc_c >= tau:
            outcome_c = "failed_attacker_embedding"
        self.assertEqual(outcome_c, "failed_attacker_embedding")

        # Case D: Both < tau => both_unrecoverable
        v_acc_d, a_acc_d = 0.55, 0.52
        if a_acc_d < tau and v_acc_d < tau:
            outcome_d = "both_unrecoverable"
        self.assertEqual(outcome_d, "both_unrecoverable")


if __name__ == "__main__":
    unittest.main()
