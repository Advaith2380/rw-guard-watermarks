"""Clean up typographic glitches and formatting in manuscript docx"""
import os
import docx

os.makedirs("manuscript", exist_ok=True)
doc = docx.Document("RWGuard_Final_Report_v3_Faculty_Approved.docx")

replacements = [
    (",.", "."),
    (",;", ";"),
    ("?,", "?"),
    ("from, seed,", "from the primary seed,"),
    ("in the store;", "in the repository;"),
    ("No competing interests are, in practice, declared", "No competing interests are declared")
]

modified = 0
for idx, p in enumerate(doc.paragraphs):
    orig = p.text
    new_text = orig
    for r1, r2 in replacements:
        if r1 in new_text:
            new_text = new_text.replace(r1, r2)
    if new_text != orig:
        p.text = new_text
        modified += 1

print(f"Cleaned {modified} paragraphs.")
out_path = "manuscript/corrected_final_manuscript.docx"
doc.save(out_path)
print(f"Saved cleaned manuscript: {out_path}")
