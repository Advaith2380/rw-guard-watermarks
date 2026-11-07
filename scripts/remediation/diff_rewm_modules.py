"""Diff rewm modules between rewm-guard and rwg-push"""
import difflib

for fname in ["data.py", "engine.py", "model.py", "metrics.py"]:
    p1 = f"D:/projects/rewm-guard/rewm/{fname}"
    p2 = f"D:/projects/rwg-push/rewm/{fname}"
    c1 = open(p1, "r", encoding="utf-8").readlines()
    c2 = open(p2, "r", encoding="utf-8").readlines()
    diff = list(difflib.unified_diff(c1, c2, fromfile=f"rewm-guard/{fname}", tofile=f"rwg-push/{fname}"))
    print("=" * 80)
    print(f"DIFF FOR {fname} (lines: {len(diff)})")
    print("=" * 80)
    if diff:
        print("".join(diff[:30]))
    else:
        print("Identical (ignoring line endings)")
