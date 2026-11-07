"""
Audit and compare the three project directories:
1. D:/projects/rewm-guard
2. D:/projects/rw-guard-watermarks
3. D:/projects/rwg-push
"""

import os
import sys
import subprocess
import glob
import json
import hashlib

def run_git(cmd, cwd):
    try:
        res = subprocess.run(["git"] + cmd, cwd=cwd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def inspect_dir(path):
    print("=" * 80)
    print(f"INSPECTING DIRECTORY: {path}")
    print("=" * 80)
    if not os.path.exists(path):
        print(f"Path does not exist: {path}")
        return None

    info = {
        "path": path,
        "is_git": os.path.exists(os.path.join(path, ".git")),
        "git_info": {},
        "top_level_items": [],
        "python_modules": [],
        "checkpoints": [],
        "manuscripts": [],
        "datasets": [],
        "manifests": [],
        "watermark_files": []
    }

    if info["is_git"]:
        info["git_info"]["branch"] = run_git(["rev-parse", "--abbrev-ref", "HEAD"], path)
        info["git_info"]["commit"] = run_git(["rev-parse", "--short", "HEAD"], path)
        info["git_info"]["remotes"] = run_git(["remote", "-v"], path)
        status = run_git(["status", "--short"], path)
        info["git_info"]["status_lines_count"] = len(status.splitlines()) if status else 0
        print(f"Git Branch: {info['git_info']['branch']} | Commit: {info['git_info']['commit']}")
        print(f"Git Remotes:\n{info['git_info']['remotes']}")
        print(f"Git Uncommitted Changes Count: {info['git_info']['status_lines_count']}")
    else:
        print("Not a git repository.")

    # Top-level items
    for item in os.listdir(path):
        ip = os.path.join(path, item)
        is_dir = os.path.isdir(ip)
        sz = os.path.getsize(ip) if not is_dir else 0
        info["top_level_items"].append({"name": item, "is_dir": is_dir, "size_bytes": sz})

    print(f"\nTop-level items ({len(info['top_level_items'])}):")
    for item in sorted(info["top_level_items"], key=lambda x: (not x["is_dir"], x["name"])):
        dtype = "DIR " if item["is_dir"] else "FILE"
        print(f"  [{dtype}] {item['name']:<35} {item['size_bytes']:>12,} bytes" if not item["is_dir"] else f"  [{dtype}] {item['name']:<35}")

    # Recursive search for checkpoints
    for ext in [".pt", ".pth", ".ckpt"]:
        for root, _, files in os.walk(path):
            for f in files:
                if f.endswith(ext):
                    fp = os.path.join(root, f)
                    rel = os.path.relpath(fp, path)
                    sz = os.path.getsize(fp)
                    info["checkpoints"].append({"rel_path": rel, "size_bytes": sz})

    print(f"\nCheckpoints found ({len(info['checkpoints'])}):")
    for c in info["checkpoints"]:
        print(f"  {c['rel_path']} ({c['size_bytes']:,} bytes)")

    # Recursive search for manuscripts (.docx, .tex, .pdf, .md)
    for ext in [".docx", ".pdf", ".tex"]:
        for root, _, files in os.walk(path):
            for f in files:
                if f.endswith(ext):
                    fp = os.path.join(root, f)
                    rel = os.path.relpath(fp, path)
                    sz = os.path.getsize(fp)
                    info["manuscripts"].append({"rel_path": rel, "size_bytes": sz})

    print(f"\nManuscripts (.docx, .pdf, .tex) found ({len(info['manuscripts'])}):")
    for m in info["manuscripts"]:
        print(f"  {m['rel_path']} ({m['size_bytes']:,} bytes)")

    # Check for datasets (coco, pacs, etc.)
    data_candidates = ["data", "datasets", "coco", "pacs"]
    for dc in data_candidates:
        dp = os.path.join(path, dc)
        if os.path.exists(dp):
            info["datasets"].append(dc)
            print(f"\nDataset directory found: {dp}")
            for sub in os.listdir(dp):
                subp = os.path.join(dp, sub)
                if os.path.isdir(subp):
                    count = len(os.listdir(subp))
                    print(f"  Subdirectory: {sub} ({count} items)")
                else:
                    sz = os.path.getsize(subp)
                    print(f"  File: {sub} ({sz:,} bytes)")

    # Watermark files
    for root, _, files in os.walk(path):
        for f in files:
            if "watermark" in f.lower() or f in ["watermarks.py", "schemes.py"]:
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, path)
                info["watermark_files"].append(rel)

    print(f"\nWatermark files found ({len(info['watermark_files'])}):")
    for w in info["watermark_files"][:15]:
        print(f"  {w}")

    return info

def main():
    dirs = [
        r"D:\projects\rewm-guard",
        r"D:\projects\rw-guard-watermarks",
        r"D:\projects\rwg-push"
    ]
    results = {}
    for d in dirs:
        results[d] = inspect_dir(d)

    # Save summary
    os.makedirs("audit/remediation", exist_ok=True)
    with open("audit/remediation/three_directories_inspection.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("\nSaved three_directories_inspection.json successfully.")

if __name__ == "__main__":
    main()
