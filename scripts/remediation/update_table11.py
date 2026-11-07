"""
Update Table 11 in manuscript/corrected_final_manuscript.docx:
Clarify standard deviation definitions (sample SD ddof=1 vs population SD ddof=0)
and note performance on the full 3,000-sample test split.
"""

import docx

doc = docx.Document("manuscript/corrected_final_manuscript.docx")
table = doc.tables[11]

# Row 4 is Multi-Seed Mean +/- Std
# Let's inspect cells in Row 4
r4_text = "Test AUC: 0.8528 +/- 0.0030 [s = 0.002955 (ddof=1), sigma = 0.002413 (ddof=0)] | Range: 0.0059 | Full Split (3,000): Mean = 0.8530 +/- 0.0024 (s = 0.002350)"
table.rows[4].cells[1].text = r4_text

doc.save("manuscript/corrected_final_manuscript.docx")
print("Table 11 updated successfully.")
