import docx

doc = docx.Document("RWGuard_Final_Report_v3_Faculty_Approved.docx")
print("ABSTRACT (Paragraphs 0-6):")
for i in range(7):
    print(f"P[{i}]: {doc.paragraphs[i].text}\n")

print("=" * 80)
print("CONCLUSION (Paragraphs 170-185):")
for i in range(170, min(186, len(doc.paragraphs))):
    print(f"P[{i}]: {doc.paragraphs[i].text}\n")
