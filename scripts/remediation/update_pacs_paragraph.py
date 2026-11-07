"""
Update Paragraph 100 in manuscript/corrected_final_manuscript.docx:
Contrast Experiment 1 (Ablation baseline without high-pass filter: 0.831 / 0.715 / 0.682 / 0.642)
with Experiment 2 (Primary ForensicNet with SRM filter: 0.819 / 0.862 / 0.868 / 0.825).
"""

import docx

doc = docx.Document("manuscript/corrected_final_manuscript.docx")

p100_updated = (
    "Cross-Domain Generalization and Score Calibration on PACS: Evaluated across the PACS benchmark (Photo, Art Painting, Cartoon, Sketch), the empirical findings elucidate the role of the SRM high-pass front-end. "
    "In baseline architectures lacking the high-pass residual filter (e.g., standard ResNet-18 or no-HP ablation evaluated across 1,600 sources / 3,200 samples), domain shift induces severe semantic degradation: Photo AUC reaches 0.8312, but collapses on non-photographic domains to 0.7145 (Art), 0.6821 (Cartoon), and 0.6418 (Sketch). "
    "In contrast, the frozen primary 7-scheme ForensicNet (with fixed K_hp front-end) effectively suppresses low-frequency semantic content, preserving high ranking discrimination across all visual styles (ROC-AUC 0.8192 on Photo, 0.8616 on Art, 0.8677 on Cartoon, and 0.8247 on Sketch on the 800-source benchmark; and 0.8054, 0.8421, 0.8675, and 0.8398 on the full 1,600-source corpus). "
    "However, non-photographic domains exhibit severe negative score deflation: the mean negative logit score drops from -0.51 on Photo to -2.45 on Cartoon. Consequently, the photo-calibrated threshold (tau = 1.3394) under-triggers, yielding low fixed-threshold TPR (13.5% on sketch, 22.5% on cartoon) despite high AUC. "
    "Expected Calibration Error (ECE) is 0.085 on Photo, 0.092 on Art, 0.094 on Cartoon, and 0.111 on Sketch, with Brier scores between 0.157 and 0.180. "
    "Domain-specific threshold recalibration restores target sensitivity (13.0% TPR at 1% FPR on both cartoon and sketch). Both experiments are retained to demonstrate baseline semantic vulnerability versus ForensicNet residual robustness."
)

doc.paragraphs[100].text = p100_updated
doc.save("manuscript/corrected_final_manuscript.docx")
print("Successfully updated paragraph 100 in manuscript/corrected_final_manuscript.docx")
