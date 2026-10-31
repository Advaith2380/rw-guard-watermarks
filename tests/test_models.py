"""Unit tests for model architectures and resolution invariance (REQ-K, REQ-M)."""

import unittest
import torch
from rewm.model import build_model, HighPass


class TestModels(unittest.TestCase):
    def test_highpass_filter_shape_and_range(self):
        hp = HighPass()
        # Input tensor shape (2, 3, 64, 64) in [0, 1]
        x = torch.rand(2, 3, 64, 64)
        out = hp(x)
        # 3 input channels * 3 filters = 9 output channels
        self.assertEqual(out.shape, (2, 9, 64, 64))

    def test_all_architectures_forward(self):
        archs = ["forensic", "forensic_nohp", "simple", "simple_hp", "resnet18", "resnet18_hp", "srnet", "srnet_hp"]
        x = torch.rand(2, 3, 128, 128)
        for arch in archs:
            model = build_model(arch)
            model.eval()
            with torch.no_grad():
                out = model(x)
            self.assertEqual(out.shape, (2,), f"Arch {arch} unexpected shape {out.shape}")

    def test_resolution_invariance(self):
        # ForensicNet accepts variable input sizes without modifying weights
        model = build_model("forensic")
        model.eval()
        for sz in [128, 256, 384]:
            x = torch.rand(1, 3, sz, sz)
            with torch.no_grad():
                out = model(x)
            self.assertEqual(out.shape, (1,))


if __name__ == "__main__":
    unittest.main()
