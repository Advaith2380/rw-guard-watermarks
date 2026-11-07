# RW-GUARD: FINAL SCIENTIFIC TECHNICAL VALIDATION DELIVERABLE

**Status:** All Faculty Corrections Implemented, Evaluated, and Frozen.
**Authoritative Primary Checkpoint:** `checkpoints/final/rwguard_final_7scheme.pt`
**Frozen Validation Operating Threshold:** $\tau = 1.3394016027450562$ (Nominal 1.0% Val FPR)

---
## Table 1: Master Technical Results Across All Experimental Axes

| Evaluation Axis / Condition | Tested Model | N (Sources) | ROC-AUC [95% CI] | TPR @ 1% FPR [95% CI] | Fixed-Thr TPR (tau) | Fixed-Thr FPR (tau) | Key Scientific Finding / Implication |
|---|---|---|---|---|---|---|---|
| Primary In-Distribution (COCO 256px) | Final 7-Scheme Frozen | 3,000 (1,500) | 0.8543 [0.841, 0.867] | 0.0787 [0.050, 0.106] | 0.1867 | 0.0333 | Headline 7-scheme detection benchmark on full held-out test split |
| Shortcut: Linear Baseline (10 Feats) | Logistic Regression | 1000 (500) | 0.5569 [0.543, 0.572] | 0.0100 [0.006, 0.020] | 0.0180 | 0.0160 | Linear aggregate energy/spectral stats fail to explain RW-Guard detection |
| Shortcut: Nonlinear Baseline (10 Feats) | Random Forest | 1000 (500) | 0.5500 [0.525, 0.575] | 0.0200 [0.008, 0.040] | 0.0060 | 0.0000 | Nonlinear tree ensemble shows ForensicNet learns spatial interaction signatures beyond aggregate statistics |
| Shortcut: Strength-Matched Control | Final 7-Scheme Frozen | 600 (300) | 0.5747 [0.554, 0.596] | 0.0500 [0.020, 0.073] | 0.2167 | 0.1400 | Single watermark matched to double watermark MSE (37.2 dB PSNR) |
| Shortcut: Matched-Noise Control | Final 7-Scheme Frozen | 600 (300) | 0.7296 [0.703, 0.757] | 0.0500 [0.017, 0.103] | 0.2167 | 0.0633 | Single watermark + additive Gaussian noise matching double watermark MSE |
| Outcome: successful_overwrite | Final 7-Scheme Frozen | 67 (67) | 0.6387 | 0.0299 | 0.1194 | - | 13.4% of attacks; mean score 0.378 |
| Outcome: dual_survival | Final 7-Scheme Frozen | 425 (425) | 0.7362 | 0.0659 | 0.2071 | - | 85.0% of attacks; mean score 0.742 |
| Outcome: failed_attacker_embedding | Final 7-Scheme Frozen | 8 (8) | 0.7847 | N/A | 0.1250 | - | 1.6% of attacks; mean score 0.859 |
| Neural: TrustMark Zero-Shot (Stratified) | Final 7-Scheme Frozen | 200 (100) | 0.6562 [0.615, 0.701] | 0.0300 | 0.0000 | 0.0100 | Zero-shot transfer to unseen deep neural watermarker without adaptation |
| Neural: TrustMark Supervised (15% Exposed) | trustmark_mix/best.pt | 200 (100) | 0.8505 [0.803, 0.894] | 0.2200 | 0.1800 | 0.0000 | Supervised domain transfer with 15% neural watermarker training exposure |
| Neural: StegaStamp Zero-Shot (Stratified) | Final 7-Scheme Frozen | 300 (150) | 0.9293 [0.902, 0.954] | 0.1667 | 0.0533 | 0.0067 | Zero-shot transfer on real ONNX StegaStamp encoder/decoder |
| Multi-Seed Reproducibility (3 Seeds) | Seed Ensemble Mean | 1000 (500) | 0.8528 [0.850, 0.856] | 0.0927 | 0.1820 | 0.0273 | Seed std: AUC +/- 0.0024, range: 0.0059 |
