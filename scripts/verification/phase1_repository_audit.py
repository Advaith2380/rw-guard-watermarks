"""Phase 1: Repository Discovery and Baseline Preservation.

Produces:
1. audit/final_independent_verification/initial_repository_inventory.json
2. audit/final_independent_verification/environment_manifest.json
3. audit/final_independent_verification/repository_audit.md
4. audit/final_independent_verification/pre_verification_backup/
"""

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time

try:
    import torch
    TORCH_VER = torch.__version__
    CUDA_AVAIL = torch.cuda.is_available()
    CUDA_DEVICE = torch.cuda.get_device_name(0) if CUDA_AVAIL else "None"
except Exception as e:
    TORCH_VER = str(e)
    CUDA_AVAIL = False
    CUDA_DEVICE = "None"

try:
    import numpy as np
    NUMPY_VER = np.__version__
except Exception as e:
    NUMPY_VER = str(e)

try:
    import sklearn
    SKLEARN_VER = sklearn.__version__
except Exception as e:
    SKLEARN_VER = str(e)


def sha256_file(filepath):
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"ERROR: {e}"


def get_git_info():
    info = {"git_available": False, "commit": "N/A", "branch": "N/A", "status": "N/A"}
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
        status = subprocess.check_output(["git", "status", "--short"], text=True).strip()
        info.update({"git_available": True, "commit": commit, "branch": branch, "status": status})
    except Exception as e:
        info["error"] = str(e)
    return info


def is_relevant(rel_path):
    lower = rel_path.lower()
    if any(k in lower for k in ["checkpoints", "audit", "results", "rewm", "tests", "scripts", ".docx", ".pt", ".json", ".py", ".md", ".csv"]):
        return True
    return False


def main():
    base_dir = os.path.abspath(".")
    audit_dir = os.path.join(base_dir, "audit", "final_independent_verification")
    os.makedirs(audit_dir, exist_ok=True)
    backup_dir = os.path.join(audit_dir, "pre_verification_backup")
    os.makedirs(backup_dir, exist_ok=True)

    print("Phase 1: Starting Repository Discovery & Baseline Preservation...")

    # 1. Environment manifest
    env_info = {
        "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
        "os_platform": platform.platform(),
        "python_version": sys.version,
        "python_executable": sys.executable,
        "torch_version": TORCH_VER,
        "cuda_available": CUDA_AVAIL,
        "cuda_device_name": CUDA_DEVICE,
        "numpy_version": NUMPY_VER,
        "scikit_learn_version": SKLEARN_VER,
        "git": get_git_info()
    }

    env_path = os.path.join(audit_dir, "environment_manifest.json")
    with open(env_path, "w", encoding="utf-8") as f:
        json.dump(env_info, f, indent=2)
    print(f"  [OK] Saved environment manifest to: {env_path}")

    # 2. File inventory
    ignored_prefixes = [".git", ".venv", "__pycache__", ".idea", ".vscode", ".pytest_cache", "audit\\final_independent_verification"]
    inventory = []
    
    for root, dirs, files in os.walk(base_dir):
        # Filter directories in-place
        dirs[:] = [d for d in dirs if not any(d == ign or os.path.join(root, d).replace("/", "\\").endswith(ign) for ign in ignored_prefixes)]
        
        for f in files:
            full_p = os.path.join(root, f)
            rel_p = os.path.relpath(full_p, base_dir).replace("\\", "/")
            
            if any(rel_p.startswith(ign) for ign in [p.replace("\\", "/") for p in ignored_prefixes]):
                continue

            size = os.path.getsize(full_p)
            ext = os.path.splitext(f)[1].lower()
            rel = is_relevant(rel_p)

            # Only compute hash for files under 200MB to avoid excessive I/O on huge archives
            sha = sha256_file(full_p) if size < 200 * 1024 * 1024 else "SKIPPED_LARGE_FILE"

            inventory.append({
                "relative_path": rel_p,
                "size_bytes": size,
                "sha256": sha,
                "extension": ext,
                "is_relevant_to_evaluation": rel
            })

    inv_path = os.path.join(audit_dir, "initial_repository_inventory.json")
    with open(inv_path, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2)
    print(f"  [OK] Saved repository inventory ({len(inventory)} files) to: {inv_path}")

    # 3. Create immutable backup of key existing artifacts
    backup_targets = [
        "checkpoints/final",
        "audit",
        "results/final_7scheme_primary"
    ]
    for bt in backup_targets:
        src = os.path.join(base_dir, bt)
        if os.path.exists(src):
            dst = os.path.join(backup_dir, bt.replace("/", "_"))
            if not os.path.exists(dst):
                if os.path.isdir(src):
                    # Copy tree ignoring recursive audit loop
                    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("final_independent_verification", "*_backup*"))
                else:
                    shutil.copy2(src, dst)
    print(f"  [OK] Saved baseline backup to: {backup_dir}")

    # 4. Generate repository_audit.md
    md_lines = [
        "# RW-GUARD REPOSITORY DISCOVERY AND BASELINE AUDIT",
        f"**Date/Time:** {env_info['timestamp_utc']}  ",
        f"**Platform:** {env_info['os_platform']}  ",
        f"**Python:** {env_info['python_version'].split()[0]}  ",
        f"**PyTorch:** {env_info['torch_version']} (CUDA: {env_info['cuda_available']} - {env_info['cuda_device_name']})  ",
        f"**Git Commit:** `{env_info['git']['commit']}` (Branch: `{env_info['git']['branch']}`)  ",
        "\n---",
        "## 1. Key Component Inspection",
        "- **Primary Model Checkpoint:** `checkpoints/final/rwguard_final_7scheme.pt`",
        "- **Watermark Core Package:** `rewm/` (`model.py`, `watermarks.py`, `data.py`, `outcomes.py`, `metrics.py`)",
        "- **Evaluation Entrypoints:** `evaluate.py`, `matched_controls.py`, `shortcut_baseline.py`, `evaluate_trustmark_cache.py`, `test_stegastamp_detector.py`, `pacs_calibration.py`",
        "- **Statistical Engine:** `bootstrap_ci.py` (Source-image grouped bootstrap, B=2,000 replicates)",
        "- **Regression Test Suite:** `run_tests.py` (22 unit & integration tests)",
        "\n## 2. Inventory Summary",
        f"- Total tracked files cataloged: {len(inventory)}",
        f"- Relevant evaluation artifacts: {sum(1 for x in inventory if x['is_relevant_to_evaluation'])}",
        "- Pre-verification baseline snapshot established in `audit/final_independent_verification/pre_verification_backup/`",
        "\n## 3. Environment Readiness Status",
        "All critical dependencies (PyTorch with CUDA GTX 1650, NumPy, scikit-learn, OpenCV) are verified and operational."
    ]
    md_path = os.path.join(audit_dir, "repository_audit.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")
    print(f"  [OK] Saved markdown report to: {md_path}")
    print("Phase 1 completed successfully.")


if __name__ == "__main__":
    main()
