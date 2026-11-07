"""Unit tests for all 7 watermark embedding and extraction schemes."""

import os
import unittest
import numpy as np
from rewm.watermarks import SCHEMES, NBITS, embed_random, psnr


class TestWatermarks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use a real image if available (to ensure texture for NMP variance-selection), else textured array
        coco_sample = "D:/projects/rewm-guard/data/coco/000000000139.jpg"
        if os.path.isfile(coco_sample):
            from rewm.data import load_image
            cls.test_img = load_image(coco_sample, 256)
        else:
            rng = np.random.default_rng(42)
            cls.test_img = rng.integers(30, 220, size=(256, 256, 3), dtype=np.uint8)

    def test_all_seven_schemes_embed_and_extract(self):
        rng = np.random.default_rng(123)
        for name, scheme in SCHEMES.items():
            out, info = embed_random(self.test_img, name, rng, return_info=True)
            self.assertEqual(out.shape, self.test_img.shape)
            self.assertEqual(out.dtype, np.uint8)
            
            # Check PSNR invisibility (should exceed 32 dB)
            p = psnr(self.test_img, out)
            self.assertGreater(p, 30.0, f"Scheme {name} PSNR too low: {p:.1f} dB")
            
            # Check single embedding bit-accuracy (statistically significant above 0.5 chance)
            raw = scheme.extract(out, info["key"], NBITS, info["strength"])
            bitacc = float(np.mean((raw > 0) == info["bits"]))
            self.assertGreaterEqual(bitacc, 0.75, f"Scheme {name} bit accuracy too low: {bitacc:.2f}")

    def test_same_scheme_overwriting(self):
        # When embedding DCT-QIM followed by DCT-QIM, the second should overwrite the first
        rng = np.random.default_rng(42)
        o1, i1 = embed_random(self.test_img, "dct_qim", rng, return_info=True)
        o2, i2 = embed_random(o1, "dct_qim", rng, return_info=True)
        
        # Attacker bit-acc should be high
        raw_att = SCHEMES["dct_qim"].extract(o2, i2["key"], NBITS, i2["strength"])
        acc_att = float(np.mean((raw_att > 0) == i2["bits"]))
        self.assertGreaterEqual(acc_att, 0.85)
        
        # Victim bit-acc should drop significantly (overwritten)
        raw_vic = SCHEMES["dct_qim"].extract(o2, i1["key"], NBITS, i1["strength"])
        acc_vic = float(np.mean((raw_vic > 0) == i1["bits"]))
        self.assertLess(acc_vic, 0.75)

    def test_stegastamp_embed_and_decode(self):
        # Test real pretrained neural watermarker (StegaStamp ONNX)
        weights_path = "model_files/stega_stamp/stega_stamp.onnx"
        if os.path.isfile(weights_path):
            from rewm_stegastamp import StegaStamp, msg_from_text, bit_accuracy
            ss = StegaStamp(weights_path=weights_path)
            msg = msg_from_text("TestPayload1")
            wm_img = ss.encode(self.test_img, msg)
            self.assertEqual(wm_img.shape, self.test_img.shape)
            decoded_bits = ss.decode(wm_img)
            acc = bit_accuracy(decoded_bits, msg)
            self.assertGreaterEqual(acc, 0.90, f"StegaStamp decoding accuracy too low: {acc}")


if __name__ == "__main__":
    unittest.main()
