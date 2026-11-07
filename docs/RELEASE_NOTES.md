# Release Notes: RW-Guard Faculty Submission Edition

**Release Tag:** `v2.0-faculty-final`  
**Date:** November 2026  
**Repository Remote:** `https://github.com/Advaith2380/rw-guard-watermarks.git`  
**Target Branch:** `main`

---

## 1. Frozen Cryptographic Identities

- **Primary Checkpoint Path:** `checkpoints/final/rwguard_final_7scheme.pt`
- **Primary Checkpoint SHA-256:** `37680cdd2d4e5100cbb8aa1642e78b9bb3df373e79efd9f8512f89e15d0c0573`
- **Primary Parameters:** 2,466,099 weights (7 schemes: `dct_qim`, `dwt_qim`, `ss_spatial`, `fft_ring`, `nmp_freq`, `svd_qim`, `dct_svd`)
- **Frozen Operating Threshold:** $\tau = 1.3394016$ (calibrated at 1.00% validation FPR)
- **Defended Checkpoint Path:** `runs/adv_eps1/best.pt`
- **Defended Checkpoint SHA-256:** `27954fd43360830d76fa107036567e9486844fa85d6a058c84d438b2e6caefed`
- **Submission Archive:** `deliverables/RW_GUARD_FINAL_FACULTY_SUBMISSION.zip`

---

## 2. Summary of Scientific & Manuscript Remediation

### 2.1 Resolution Discrepancy Reconciliation (REQ-A06 / Table 8)
- Reconciled Table 8 with authoritative raw prediction arrays (`results/final_primary/FINAL_RESOLUTION_METRICS_VERIFIED.csv`):
  - **128 px:** Updated TPR@1% FPR from erroneous preliminary value 0.106 to exact verified **0.069** (6.93%).
  - **384 px:** Updated TPR@1% FPR from erroneous preliminary value 0.119 to exact verified **0.083** (8.33%).
  - Verified all five resolutions (128, 256, 384, 512, 1024 px) in both manuscript tables and narrative paragraphs.

### 2.2 Multi-Seed Protocol Disambiguation (Table 12)
- Clearly separated Protocol A (500-source test subset, Seed 0: 0.8556, Seed 1: 0.8531, Seed 2: 0.8497; Mean 0.8528, Sample SD $s=0.0030$, Population SD $\sigma=0.0024$) from Protocol B (1,500-source full held-out test split; Mean 0.8530, Sample SD 0.0024).
- Confirmed test FPR stability ($2.73\% \pm 0.68\%$) across all seeds.

### 2.3 Algorithm & Methodology Repair
- Replaced fragmented placeholder text with complete, numbered, professional pseudocode:
  - **Algorithm 1:** Full experimental pipeline for dataset generation, source-level partitioning, random scheme pairing, and verification.
  - **Algorithm 2:** ForensicNet forward inference pipeline detailing SRM filtering, stem layers, residual stages, dual global spatial pooling, and threshold decision.

### 2.4 Abstract and Text Revision
- Abstract rewritten to exactly 250 words (complying with $\le 250$ word guidelines).
- Outdated TrustMark preliminary claims (0.696 and 0.925) removed from Contributions; replaced with verified 7-scheme figures (0.6562 zero-shot, 0.8505 supervised adaptation) and StegaStamp ONNX benchmark (0.9293 zero-shot).
- Qualifications on sequential embedding detection versus legal ownership forgery applied consistently throughout text.

### 2.5 Bibliographic & Citation Audit
- Verified sequential bracketed citations [1] through [28].
- Updated TrustMark to official published conference version: **ICCV 2025** (Bui et al.).
- Updated PECCVAI to official conference publication: **CVPR 2026** (Dixit et al.).
- Confirmed exact statutory citations for EU AI Act (Regulation (EU) 2024/1689 & 2026/1744) and California SB 942.
- Verified zero stray citations (e.g. "[99]" completely removed).

### 2.6 Full Test Suite & Matrix Validation
- **Pytest Suite:** 22/22 tests passing.
- **Faculty Requirement Matrix:** 53/53 requirements independently audited as **PASS** with zero remaining failures or unverified claims.
