#!/usr/bin/env python3
"""Update Table 7 in manuscript/corrected_final_manuscript.docx with all 5 resolutions."""

import docx
import json
import os

DOCX_PATH = "manuscript/corrected_final_manuscript.docx"
RES_JSON = "results/final_primary/resolution_results.json"


def update_table7():
    if not os.path.exists(RES_JSON):
        print("Waiting for resolution_results.json...")
        return

    with open(RES_JSON, "r") as f:
        res_data = json.load(f)["resolutions"]

    doc = docx.Document(DOCX_PATH)
    t7 = None
    for t_idx, table in enumerate(doc.tables):
        header = " ".join([c.text.strip() for c in table.rows[0].cells]).lower()
        if "auc" in header and "tpr@1%fpr" in header and "tpr@fixed" in header:
            # Check if it has 128px
            for row in table.rows:
                if "128px resolution" in row.cells[0].text.lower():
                    t7 = table
                    break
        if t7:
            break

    assert t7 is not None, "Could not find Table 7!"
    print("Found Table 7. Inspecting rows...")

    # Check existing resolution rows
    has_512 = any("512px" in r.cells[0].text for r in t7.rows)
    has_1024 = any("1024px" in r.cells[0].text for r in t7.rows)

    if not has_512 and "512px" in res_data:
        r512 = res_data["512px"]
        row = t7.add_row()
        row.cells[0].text = "512px resolution"
        row.cells[1].text = f"{r512['roc_auc']:.3f}"
        row.cells[2].text = f"{r512['tpr_at_1pct_fpr']:.3f}"
        row.cells[3].text = f"{r512['tpr_fixed_thr']:.3f}"
        row.cells[4].text = f"{r512['fpr_fixed_thr']:.3f}"
        print("Added 512px row to Table 7.")

    if not has_1024 and "1024px" in res_data:
        r1024 = res_data["1024px"]
        row = t7.add_row()
        row.cells[0].text = "1024px resolution"
        row.cells[1].text = f"{r1024['roc_auc']:.3f}"
        row.cells[2].text = f"{r1024['tpr_at_1pct_fpr']:.3f}"
        row.cells[3].text = f"{r1024['tpr_fixed_thr']:.3f}"
        row.cells[4].text = f"{r1024['fpr_fixed_thr']:.3f}"
        print("Added 1024px row to Table 7.")

    doc.save(DOCX_PATH)
    print("Saved Table 7 updates to manuscript.")


if __name__ == "__main__":
    update_table7()
