"""
Simulated invisible-watermark schemes used to build the training / test data.

Every scheme exposes
    embed(img_u8, key, bits, strength)          -> img_u8   (H x W x 3, uint8)
    extract(img_u8, key, nbits, strength)       -> soft score per bit (>0 means bit=1)

All schemes only touch the luminance (Y) channel: the change is added equally to
R, G and B so that chroma is untouched.  Results are clipped and rounded to uint8,
exactly like a real image that was saved to disk.

Why simulate instead of using StegaStamp / Stable Signature / Tree-Ring directly?
  * those need multi-GB pretrained models and a GPU, which makes the pipeline fragile;
  * here every layer of the data is reproducible from a seed and costs milliseconds.
The four schemes cover four different *artefact families*:
  dct_qim     block-DCT quantisation (QIM)     -> "overwriting" behaviour like post-hoc encoders
  dwt_qim     Haar-DWT quantisation (QIM)      -> wavelet-domain, different spatial signature
  ss_spatial  additive spread spectrum         -> content-agnostic pattern (Ba et al., Yang et al.)
  fft_ring    Fourier-magnitude rings          -> Tree-Ring-like frequency-domain signature
Neural watermarkers (StegaStamp, Video Seal, ...) are the natural Phase-2 extension.
"""
import numpy as np

NBITS = 32
_LUMA = np.array([0.299, 0.587, 0.114], dtype=np.float32)


# --------------------------------------------------------------------------- helpers
def _rng(key, salt=0):
    return np.random.default_rng([int(key) & 0x7FFFFFFF, int(salt)])


def _luma(img):
    return img.astype(np.float32) @ _LUMA


def _apply_luma(img, new_y):
    """Write a modified luminance plane back into the RGB image (chroma unchanged)."""
    dy = new_y - _luma(img)
    out = img.astype(np.float32) + dy[..., None]
    return np.clip(np.rint(out), 0, 255).astype(np.uint8)


def _region(img, mult):
    h, w = img.shape[:2]
    return (h // mult) * mult, (w // mult) * mult


def _dct_matrix(n=8):
    k = np.arange(n)[:, None]
    i = np.arange(n)[None, :]
    m = np.sqrt(2.0 / n) * np.cos(np.pi * (2 * i + 1) * k / (2 * n))
    m[0, :] = np.sqrt(1.0 / n)
    return m.astype(np.float32)


_D = _dct_matrix(8)


def _block_dct(y):
    h, w = y.shape
    b = y.reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3)
    return _D @ b @ _D.T


def _block_idct(c):
    b = _D.T @ c @ _D
    hb, wb = b.shape[:2]
    return b.transpose(0, 2, 1, 3).reshape(hb * 8, wb * 8)


def _haar2d(x):
    a, b, c, d = x[0::2, 0::2], x[0::2, 1::2], x[1::2, 0::2], x[1::2, 1::2]
    return (a + b + c + d) / 2, (a + b - c - d) / 2, (a - b + c - d) / 2, (a - b - c + d) / 2


def _ihaar2d(ll, lh, hl, hh):
    out = np.empty((ll.shape[0] * 2, ll.shape[1] * 2), dtype=ll.dtype)
    out[0::2, 0::2] = (ll + lh + hl + hh) / 2
    out[0::2, 1::2] = (ll + lh - hl - hh) / 2
    out[1::2, 0::2] = (ll - lh + hl - hh) / 2
    out[1::2, 1::2] = (ll - lh - hl + hh) / 2
    return out


def _qim_embed(c, bit, delta, dither):
    off = dither + bit * delta / 2.0
    return delta * np.round((c - off) / delta) + off


def _qim_score(c, delta, dither):
    """Positive when the coefficient sits closer to the bit-1 lattice than to the bit-0 lattice."""
    r0 = (c - dither) / delta
    r1 = (c - dither - delta / 2.0) / delta
    return np.abs(r0 - np.round(r0)) - np.abs(r1 - np.round(r1))


def _gauss_blur(x, sigma):
    if sigma <= 0:
        return x
    import cv2
    return cv2.GaussianBlur(x, (0, 0), sigma)


# --------------------------------------------------------------------------- schemes
class DctQim:
    """8x8 block-DCT, QIM on a public set of mid-frequency coefficients.
    The key controls the block->bit assignment and a secret dither, so a second
    embedding with another key *re-quantises* the same coefficients (true overwriting)."""
    name = "dct_qim"
    POS = [(1, 2), (2, 1), (2, 2), (1, 3), (3, 1), (3, 2)]

    def _layout(self, key, nblocks, nbits):
        rng = _rng(key, 1)
        assign = rng.permutation(nblocks) % nbits
        dither = rng.uniform(0, 1, size=(nblocks, len(self.POS)))
        return assign, dither

    def embed(self, img, key, bits, strength):
        h, w = _region(img, 8)
        y = _luma(img)
        c = _block_dct(y[:h, :w])
        hb, wb = c.shape[:2]
        flat = c.reshape(hb * wb, 8, 8)
        assign, dither = self._layout(key, hb * wb, len(bits))
        b = np.asarray(bits)[assign]
        for j, (u, v) in enumerate(self.POS):
            flat[:, u, v] = _qim_embed(flat[:, u, v], b, strength, dither[:, j] * strength)
        y2 = y.copy()
        y2[:h, :w] = _block_idct(flat.reshape(hb, wb, 8, 8))
        return _apply_luma(img, y2)

    def extract(self, img, key, nbits, strength):
        h, w = _region(img, 8)
        c = _block_dct(_luma(img)[:h, :w])
        hb, wb = c.shape[:2]
        flat = c.reshape(hb * wb, 8, 8)
        assign, dither = self._layout(key, hb * wb, nbits)
        s = np.mean([_qim_score(flat[:, u, v], strength, dither[:, j] * strength)
                     for j, (u, v) in enumerate(self.POS)], axis=0)
        return np.bincount(assign, weights=s, minlength=nbits) / np.maximum(np.bincount(assign, minlength=nbits), 1)


class DwtQim:
    """Two-level Haar DWT, QIM on the level-2 LH and HL sub-bands."""
    name = "dwt_qim"

    def _split(self, y):
        ll1, lh1, hl1, hh1 = _haar2d(y)
        ll2, lh2, hl2, hh2 = _haar2d(ll1)
        return (ll1, lh1, hl1, hh1), (ll2, lh2, hl2, hh2)

    def _layout(self, key, n, nbits):
        rng = _rng(key, 2)
        return rng.permutation(n) % nbits, rng.uniform(0, 1, size=n)

    def embed(self, img, key, bits, strength):
        h, w = _region(img, 4)
        y = _luma(img)
        lvl1, (ll2, lh2, hl2, hh2) = self._split(y[:h, :w])
        coefs = np.concatenate([lh2.ravel(), hl2.ravel()])
        assign, dither = self._layout(key, coefs.size, len(bits))
        coefs = _qim_embed(coefs, np.asarray(bits)[assign], strength, dither * strength)
        n = lh2.size
        lh2n, hl2n = coefs[:n].reshape(lh2.shape), coefs[n:].reshape(hl2.shape)
        ll1n = _ihaar2d(ll2, lh2n, hl2n, hh2)
        y2 = y.copy()
        y2[:h, :w] = _ihaar2d(ll1n, lvl1[1], lvl1[2], lvl1[3])
        return _apply_luma(img, y2)

    def extract(self, img, key, nbits, strength):
        h, w = _region(img, 4)
        _, (_, lh2, hl2, _) = self._split(_luma(img)[:h, :w])
        coefs = np.concatenate([lh2.ravel(), hl2.ravel()])
        assign, dither = self._layout(key, coefs.size, nbits)
        s = _qim_score(coefs, strength, dither * strength)
        return np.bincount(assign, weights=s, minlength=nbits) / np.maximum(np.bincount(assign, minlength=nbits), 1)


class SpreadSpectrum:
    """Additive multi-bit spread spectrum in the pixel domain (content-agnostic)."""
    name = "ss_spatial"

    def _patterns(self, key, shape, nbits):
        rng = _rng(key, 3)
        sigma = float(rng.choice([0.0, 0.8, 1.5]))
        w = rng.choice(np.array([-1.0, 1.0], dtype=np.float32), size=(nbits,) + tuple(shape))
        return w, sigma

    def embed(self, img, key, bits, strength):
        y = _luma(img)
        w, sigma = self._patterns(key, y.shape, len(bits))
        pat = np.tensordot((2 * np.asarray(bits) - 1).astype(np.float32), w, axes=1) / np.sqrt(len(bits))
        pat = _gauss_blur(pat.astype(np.float32), sigma)
        pat /= pat.std() + 1e-8
        return _apply_luma(img, y + strength * pat)

    def extract(self, img, key, nbits, strength):
        y = _luma(img)
        w, _ = self._patterns(key, y.shape, nbits)
        hp = y - _gauss_blur(y, 2.0)
        return np.array([float((hp * w[i]).mean()) for i in range(nbits)])


class FftRing:
    """Fourier-magnitude rings (Tree-Ring-like, but post-hoc): each ring's mean magnitude is *set* to
    (1 +/- strength) x the level of its neighbouring gaps.  Because the level is set (not multiplied),
    a second embedding on the same rings overwrites the first."""
    name = "fft_ring"
    R0, R1, WIDTH_FRAC = 0.10, 0.46, 0.4
    _cache = {}

    def _masks(self, shape, nbits):
        k = (shape, nbits)
        if k not in self._cache:
            fy = np.fft.fftfreq(shape[0])[:, None]
            fx = np.fft.fftfreq(shape[1])[None, :]
            r = np.sqrt(fx ** 2 + fy ** 2).ravel()
            centres = np.linspace(self.R0, self.R1, nbits)
            spacing = centres[1] - centres[0]
            half = self.WIDTH_FRAC * spacing / 2
            idx = lambda c: np.flatnonzero(np.abs(r - c) <= half)
            self._cache[k] = [(idx(c), idx(c - spacing / 2), idx(c + spacing / 2)) for c in centres]
            if len(self._cache) > 6:
                self._cache.pop(next(iter(self._cache)))
        return self._cache[k]

    def embed(self, img, key, bits, strength):
        y = _luma(img)
        mag = np.abs(np.fft.fft2(y)).ravel()
        order = _rng(key, 4).permutation(len(bits))          # key: which bit sits on which ring
        gain = np.ones(mag.size, dtype=np.float32)
        for ring, (ridx, lo, hi) in enumerate(self._masks(y.shape, len(bits))):
            ref = 0.5 * (mag[lo].mean() + mag[hi].mean())
            gain[ridx] = (1.0 + strength * (2 * bits[order[ring]] - 1)) * ref / max(mag[ridx].mean(), 1e-6)
        y2 = np.fft.ifft2(np.fft.fft2(y) * gain.reshape(y.shape)).real.astype(np.float32)
        return _apply_luma(img, y2)

    def extract(self, img, key, nbits, strength):
        mag = np.abs(np.fft.fft2(_luma(img))).ravel()
        order = _rng(key, 4).permutation(nbits)
        scores = np.zeros(nbits)
        for ring, (ridx, lo, hi) in enumerate(self._masks(img.shape[:2], nbits)):
            ref = 0.5 * (mag[lo].mean() + mag[hi].mean())
            scores[order[ring]] = np.log(mag[ridx].mean() + 1e-6) - np.log(ref + 1e-6)
        return scores


class NmpFreq:
    """2026-style scheme, inspired by PECCAVI (CVPR 2026): embeds only in semantically *stable*
    regions ("Non-Melting Points"), instead of everywhere. Stable = locally textured, not flat and
    not a hard edge - the parts of a photo least disturbed by heavy edits or AI re-generation.
    We approximate NMP selection with a local-variance mask, then run block-DCT QIM (as in DctQim)
    restricted to that mask, plus faint camouflage noise elsewhere so the mask itself isn't obvious."""
    name = "nmp_freq"
    POS = [(2, 2), (1, 3), (3, 1), (2, 3), (3, 2)]

    def _nmp_mask(self, y):
        h, w = _region(y.shape[0], 8), _region(y.shape[1], 8)  # placeholder, fixed below
        return None

    def _stability_mask(self, y):
        """Per 8x8 block: keep blocks with mid-range local variance (textured, not flat, not a
        hard edge) - a cheap stand-in for PECCAVI's learned Non-Melting-Point detector."""
        h, w = (y.shape[0] // 8) * 8, (y.shape[1] // 8) * 8
        blocks = y[:h, :w].reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3)
        var = blocks.reshape(blocks.shape[0], blocks.shape[1], -1).var(axis=2)
        lo, hi = np.percentile(var, 35), np.percentile(var, 90)
        return (var >= lo) & (var <= hi), h, w

    def embed(self, img, key, bits, strength):
        y = _luma(img)
        mask, h, w = self._stability_mask(y)
        c = _block_dct(y[:h, :w])
        hb, wb = c.shape[:2]
        flat = c.reshape(hb * wb, 8, 8)
        rng = _rng(key, 5)
        m = mask.ravel()
        idx = np.flatnonzero(m)
        if idx.size == 0:                              # pathological (near-flat) image: fall back to all blocks
            idx = np.arange(hb * wb)
        assign = rng.integers(0, len(bits), size=idx.size)
        dither = rng.uniform(0, 1, size=(idx.size, len(self.POS)))
        b = np.asarray(bits)[assign]
        for j, (u, v) in enumerate(self.POS):
            flat[idx, u, v] = _qim_embed(flat[idx, u, v], b, strength, dither[:, j] * strength)
        # camouflage: tiny noise on a random subset of the *non*-NMP blocks, so the stable-region
        # mask cannot be found just by looking for "which blocks changed"
        rest = np.flatnonzero(~m)
        if rest.size:
            deco = rng.choice(rest, size=max(1, rest.size // 4), replace=False)
            flat[deco] += rng.normal(0, strength * 0.15, size=flat[deco].shape)
        y2 = y.copy()
        y2[:h, :w] = _block_idct(flat.reshape(hb, wb, 8, 8))
        return _apply_luma(img, y2)

    def extract(self, img, key, nbits, strength):
        y = _luma(img)
        mask, h, w = self._stability_mask(y)
        c = _block_dct(y[:h, :w])
        hb, wb = c.shape[:2]
        flat = c.reshape(hb * wb, 8, 8)
        rng = _rng(key, 5)
        m = mask.ravel()
        idx = np.flatnonzero(m)
        if idx.size == 0:
            idx = np.arange(hb * wb)
        assign = rng.integers(0, nbits, size=idx.size)
        dither = rng.uniform(0, 1, size=(idx.size, len(self.POS)))
        s = np.mean([_qim_score(flat[idx, u, v], strength, dither[:, j] * strength)
                     for j, (u, v) in enumerate(self.POS)], axis=0)
        return np.bincount(assign, weights=s, minlength=nbits) / np.maximum(np.bincount(assign, minlength=nbits), 1)


class SvdQim:
    """Classical SVD watermarking. Every 8x8 luma block is factored as U . diag(S) . V^T (Singular
    Value Decomposition - it rewrites a block as a rotation, a stretch along a few principal axes,
    and another rotation). The block's overall energy sits almost entirely in its largest singular
    value S[0], so QIM-rounding S[0] survives compression and small edits far better than rounding
    a single pixel would, at the cost of a slightly larger visible change."""
    name = "svd_qim"

    def _layout(self, key, nblocks, nbits):
        rng = _rng(key, 6)
        return rng.permutation(nblocks) % nbits, rng.uniform(0, 1, size=nblocks)

    def embed(self, img, key, bits, strength):
        h, w = _region(img, 8)
        y = _luma(img)
        blocks = y[:h, :w].reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3).reshape(-1, 8, 8)
        U, S, Vt = np.linalg.svd(blocks, full_matrices=False)
        assign, dither = self._layout(key, len(blocks), len(bits))
        S[:, 0] = _qim_embed(S[:, 0], np.asarray(bits)[assign], strength, dither * strength)
        blocks2 = U @ (S[:, :, None] * Vt)
        hb, wb = h // 8, w // 8
        y2 = y.copy()
        y2[:h, :w] = blocks2.reshape(hb, wb, 8, 8).transpose(0, 2, 1, 3).reshape(h, w)
        return _apply_luma(img, y2)

    def extract(self, img, key, nbits, strength):
        h, w = _region(img, 8)
        y = _luma(img)
        blocks = y[:h, :w].reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3).reshape(-1, 8, 8)
        S = np.linalg.svd(blocks, full_matrices=False, compute_uv=False)
        assign, dither = self._layout(key, len(blocks), nbits)
        s = _qim_score(S[:, 0], strength, dither * strength)
        return np.bincount(assign, weights=s, minlength=nbits) / np.maximum(np.bincount(assign, minlength=nbits), 1)


class DctSvd:
    """Hybrid: block-DCT first (concentrates energy into a few frequency coefficients), THEN SVD on
    the resulting 8x8 DCT-coefficient block, QIM on its largest singular value. Combines DCT's
    "watch for JPEG-like compression" property with SVD's noise/rounding robustness."""
    name = "dct_svd"

    def _layout(self, key, nblocks, nbits):
        rng = _rng(key, 7)
        return rng.permutation(nblocks) % nbits, rng.uniform(0, 1, size=nblocks)

    def embed(self, img, key, bits, strength):
        h, w = _region(img, 8)
        y = _luma(img)
        c = _block_dct(y[:h, :w])
        hb, wb = c.shape[:2]
        blocks = c.reshape(hb * wb, 8, 8)
        U, S, Vt = np.linalg.svd(blocks, full_matrices=False)
        assign, dither = self._layout(key, hb * wb, len(bits))
        S[:, 0] = _qim_embed(S[:, 0], np.asarray(bits)[assign], strength, dither * strength)
        blocks2 = U @ (S[:, :, None] * Vt)
        y2 = y.copy()
        y2[:h, :w] = _block_idct(blocks2.reshape(hb, wb, 8, 8))
        return _apply_luma(img, y2)

    def extract(self, img, key, nbits, strength):
        h, w = _region(img, 8)
        c = _block_dct(_luma(img)[:h, :w])
        hb, wb = c.shape[:2]
        blocks = c.reshape(hb * wb, 8, 8)
        S = np.linalg.svd(blocks, full_matrices=False, compute_uv=False)
        assign, dither = self._layout(key, hb * wb, nbits)
        s = _qim_score(S[:, 0], strength, dither * strength)
        return np.bincount(assign, weights=s, minlength=nbits) / np.maximum(np.bincount(assign, minlength=nbits), 1)


SCHEMES = {s.name: s for s in (DctQim(), DwtQim(), SpreadSpectrum(), FftRing(), NmpFreq(), SvdQim(), DctSvd())}
# (min, max) strength used when sampling; chosen so PSNR stays roughly in the 36-46 dB range
STRENGTH_RANGE = {"dct_qim": (18.0, 40.0), "dwt_qim": (14.0, 34.0),
                  "ss_spatial": (1.5, 4.0), "fft_ring": (0.05, 0.20), "nmp_freq": (14.0, 22.0), "svd_qim": (20.0, 70.0), "dct_svd": (20.0, 70.0)}


def embed_random(img, scheme, rng, return_info=False):
    """Embed a random message with a random key and random strength."""
    key = int(rng.integers(0, 2 ** 31 - 1))
    bits = rng.integers(0, 2, size=NBITS)
    lo, hi = STRENGTH_RANGE[scheme]
    strength = float(rng.uniform(lo, hi))
    out = SCHEMES[scheme].embed(img, key, bits, strength)
    if return_info:
        return out, dict(scheme=scheme, key=key, bits=bits, strength=strength)
    return out


def psnr(a, b):
    mse = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    return 99.0 if mse == 0 else 10 * np.log10(255.0 ** 2 / mse)
