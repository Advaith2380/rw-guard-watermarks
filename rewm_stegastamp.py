"""
StegaStamp integration (second neural watermarker, following report Section 7.4
future work: "extend the testbed to a second, heavier neural watermarker").

Unlike TrustMark (available as a pip package with bundled weights), StegaStamp
has no official pip package. This wraps a real, pretrained StegaStamp encoder/
decoder exported to ONNX by the ISPRAS WIBE open-source watermark benchmark
(https://github.com/ispras/wibe, Apache-2.0), itself built from the original
authors' released checkpoints (Tancik et al., CVPR 2020, arXiv:1904.05343,
https://github.com/tancik/StegaStamp). Weights auto-download on first use from
a public, unauthenticated host -- no TensorFlow, no HuggingFace token needed.

Requires: onnxruntime, opencv-python (both lightweight; add to requirements.txt).
On a CUDA machine, `pip install onnxruntime-gpu` instead of `onnxruntime` for a
large speedup on the (one-time) cache-building step -- see build_stegastamp_cache.py.

Usage (library):
    from rewm_stegastamp import StegaStamp, msg_from_text
    ss = StegaStamp()                                  # downloads weights on first call
    wm_img = ss.encode(clean_bgr_uint8, msg_from_text("RWGuard1"))
    bits = ss.decode(wm_img)                            # -> 0/1 array, length 100
"""
import hashlib
import os
import zipfile
from pathlib import Path

import numpy as np

try:
    import cv2
except ImportError as e:
    raise ImportError("StegaStamp needs opencv-python: pip install opencv-python") from e

try:
    import onnxruntime as ort
except ImportError as e:
    raise ImportError("StegaStamp needs onnxruntime (or onnxruntime-gpu on CUDA machines): "
                       "pip install onnxruntime") from e

try:
    import requests
except ImportError as e:
    raise ImportError("Weight auto-download needs requests: pip install requests") from e


_WEIGHTS_URL = "https://nextcloud.ispras.ru/index.php/s/K6wrA6KweXZ2DGL/download"
_DEFAULT_DIR = os.path.join("model_files", "stega_stamp")
_DEFAULT_WEIGHTS = os.path.join(_DEFAULT_DIR, "stega_stamp.onnx")
WM_LENGTH = 100  # bits; fixed by the released model


def msg_from_text(text: str, length: int = WM_LENGTH) -> np.ndarray:
    """Deterministic text -> fixed-length 0/1 bit array, so the same label (e.g. "RWGuard1",
    "Attacker") always produces the same watermark payload, mirroring how test_trustmark.py
    uses fixed string messages. Uses SHA-256 (not Python's hash(), which is per-process
    randomised) so results are reproducible across runs and machines."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    bits_needed = -(-length // 8)  # ceil
    raw = (digest * (bits_needed // len(digest) + 1))[:bits_needed]
    bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8))[:length]
    return bits.astype(np.int64)


def _ensure_weights(weights_path: str) -> str:
    weights_path = str(Path(weights_path).resolve())
    if os.path.isfile(weights_path):
        return weights_path
    os.makedirs(os.path.dirname(weights_path), exist_ok=True)
    zip_path = weights_path + ".download.zip"
    print(f"StegaStamp weights not found at {weights_path} -- downloading (~tens of MB, one-time)...")
    with requests.get(_WEIGHTS_URL, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 16):
                f.write(chunk)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(os.path.dirname(weights_path))
    os.remove(zip_path)
    if not os.path.isfile(weights_path):
        # the zip may nest the .onnx file one level down; find it and move it into place
        for root, _, files in os.walk(os.path.dirname(weights_path)):
            for f in files:
                if f == os.path.basename(weights_path):
                    os.replace(os.path.join(root, f), weights_path)
    assert os.path.isfile(weights_path), (
        f"download finished but {weights_path} is still missing -- check the extracted "
        f"archive contents and adjust the path, or download the Nextcloud share manually: "
        f"{_WEIGHTS_URL.rsplit('/download', 1)[0]}")
    print(f"StegaStamp weights ready at {weights_path}")
    return weights_path


class StegaStamp:
    """Real, pretrained StegaStamp encoder/decoder (ONNX). encode()/decode() mirror the
    `trustmark.TrustMark` API shape used elsewhere in this project (rewm_trustmark.py,
    test_trustmark.py), but operate on numpy BGR uint8 images and raw bit arrays rather
    than PIL images and ASCII strings -- use msg_from_text() to bridge the two."""

    def __init__(self, weights_path: str = _DEFAULT_WEIGHTS, wm_length: int = WM_LENGTH,
                 width: int = 400, height: int = 400, alpha: float = 1.0, providers=None):
        weights_path = _ensure_weights(weights_path)
        self._model = ort.InferenceSession(weights_path, providers=providers)
        self.wm_length, self.width, self.height, self.alpha = wm_length, width, height, alpha

    def encode(self, image_bgr: np.ndarray, message: np.ndarray) -> np.ndarray:
        """image_bgr: HxWx3 uint8 BGR (as from cv2.imread). message: length-`wm_length` 0/1 array.
        Returns an HxWx3 uint8 BGR image at the ORIGINAL resolution (encoder itself runs at
        400x400; the residual is upsampled back, same trick as the original StegaStamp code)."""
        orig_h, orig_w = image_bgr.shape[:2]
        img_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(img_rgb, (self.width, self.height), interpolation=cv2.INTER_LINEAR)
        float_img = np.divide(resized, 255, dtype=np.float32)[np.newaxis, ...]
        batched_msg = message[np.newaxis, ...].astype(np.float32)

        wm_img, _ = self._model.run(output_names=["stegastamp", "residual"],
                                     input_feed={"image": float_img, "secret": batched_msg})
        result = np.round(np.clip(wm_img[0], 0, 1) * 255).astype(np.int16)
        diff = np.round((result - resized) * self.alpha).astype(np.int16)
        min_val = diff.min()
        diff_resized = cv2.resize((diff - min_val).astype(np.uint8), (orig_w, orig_h),
                                   interpolation=cv2.INTER_LINEAR)
        marked_rgb = np.clip(img_rgb.astype(np.int16) + diff_resized.astype(np.int16) + min_val, 0, 255)
        return cv2.cvtColor(marked_rgb.astype(np.uint8), cv2.COLOR_RGB2BGR)

    def decode(self, image_bgr: np.ndarray) -> np.ndarray:
        """Returns a length-`wm_length` 0/1 int array."""
        img_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(img_rgb, (self.width, self.height), interpolation=cv2.INTER_LINEAR)
        float_img = np.divide(resized, 255, dtype=np.float32)[np.newaxis, ...]
        secret = self._model.run(output_names=["decoded"],
                                  input_feed={"image": float_img,
                                              "secret": np.zeros((1, self.wm_length), dtype=np.float32)})[0]
        return (secret[0] > 0.5).astype(int)


def bit_accuracy(a: np.ndarray, b: np.ndarray) -> float:
    return float((np.asarray(a) == np.asarray(b)).mean())


# Note: the training-time cache-mixing dataset class lives in rewm_stegastamp_cache.py,
# not here -- that keeps THIS file's actual dependencies (onnxruntime, opencv, requests)
# honest. The cache dataset needs torch, which test_stegastamp.py and build_stegastamp_cache.py
# have no reason to require just to import StegaStamp/msg_from_text/bit_accuracy above.
