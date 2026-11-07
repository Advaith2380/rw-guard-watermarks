"""
Update Manuscript Multi-Seed text in Paragraph 107:
Clarify Protocol A (1000 samples) vs Protocol B (3000 samples) and sample SD (ddof=1) vs population SD (ddof=0).
"""

import docx

doc = docx.Document("manuscript/corrected_final_manuscript.docx")

target_text = (
    "Multi-Seed Reproducibility Analysis: Evaluating all three independent seven-scheme runs on the exact same 1,000-sample test split demonstrates remarkable stability: "
    "Seed 0 achieves test AUC 0.8556 [95% CI: 0.831, 0.878], Seed 1 achieves 0.8531 [0.829, 0.876], and Seed 2 achieves 0.8497 [0.826, 0.872]. "
    "Across the three seeds, mean test AUC is 0.8528 +/- 0.0024 (range: 0.0059), mean TPR@1%FPR is 0.0927 +/- 0.0242, and mean fixed-threshold TPR is 0.1820 +/- 0.0129. "
    "This confirms that ForensicNet converges to consistent representations regardless of stochastic initialization."
)

replacement_text = (
    "Multi-Seed Reproducibility Analysis: Evaluating all three independent seven-scheme runs demonstrates high training stability. "
    "On the standardized 1,000-sample test split (500 sources), Seed 0 achieves test AUC 0.8556 [95% CI: 0.831, 0.878], "
    "Seed 1 achieves 0.8531 [0.829, 0.876], and Seed 2 achieves 0.8497 [0.826, 0.872], yielding a mean test AUC of 0.8528 with sample standard deviation s = 0.002955 (ddof = 1; population standard deviation sigma = 0.002413, range = 0.0059). "
    "When evaluated on the full 3,000-sample test split (1,500 sources), the seeds achieve AUCs of 0.8543 (Seed 0, Primary), 0.8545 (Seed 1), and 0.8503 (Seed 2), yielding mean AUC = 0.8530 with sample standard deviation s = 0.002350 (ddof = 1; sigma = 0.001918). "
    "This confirms that ForensicNet converges to consistent representations across random weight initializations regardless of evaluation partition size."
)

found = False
for i, p in enumerate(doc.paragraphs):
    if "Multi-Seed Reproducibility Analysis:" in p.text:
        print(f"Found paragraph {i}: {p.text[:60]}...")
        p.text = replacement_text
        found = True
        break

assert found, "Target paragraph not found!"

doc.save("manuscript/corrected_final_manuscript.docx")
print("Successfully updated manuscript/corrected_final_manuscript.docx")
