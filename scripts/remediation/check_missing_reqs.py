import json
import os

with open("audit/remediation/faculty_requirement_register.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for r in data["requirements"]:
    out_files = [f.strip() for f in r.get("output_files", "").split(",") if f.strip()]
    missing = [f for f in out_files if not os.path.exists(f)]
    if missing:
        print(f"Req: {r['req_id']} | Title: {r['title']}")
        print(f"   Missing: {missing}")
