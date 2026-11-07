"""Read and inspect paragraphs in manuscript docx"""
import docx

doc = docx.Document("RWGuard_Final_Report_v3_Faculty_Approved.docx")
print(f"Total paragraphs: {len(doc.paragraphs)}")
print(f"Total tables: {len(doc.tables)}")

keywords = ["dual-survival", "88.7", "85.0", "0.854", "0.859", "3,200", "3,000", "TrustMark", "StegaStamp", "Kolmogorov"]

found = []
for idx, p in enumerate(doc.paragraphs):
    for kw in keywords:
        if kw.lower() in p.text.lower():
            found.append((idx, kw, p.text[:120]))
            break

print(f"\nFound {len(found)} paragraphs matching keywords:")
for idx, kw, snippet in found[:25]:
    print(f"P[{idx:03d}] ({kw}): {snippet}...")
