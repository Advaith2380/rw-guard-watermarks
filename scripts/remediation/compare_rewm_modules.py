"""Compare rewm modules across directories"""
import os
import hashlib

dirs = [
    r"D:\projects\rewm-guard",
    r"D:\projects\rw-guard-watermarks",
    r"D:\projects\rwg-push"
]

files = ["data.py", "engine.py", "metrics.py", "model.py", "watermarks.py", "__init__.py"]

print("=" * 80)
print(f"{'File':<15} | {'rewm-guard':<20} | {'rw-guard-watermarks':<20} | {'rwg-push':<20}")
print("=" * 80)

for f in files:
    hashes = []
    normalized_hashes = []
    for d in dirs:
        p = os.path.join(d, "rewm", f)
        if os.path.exists(p):
            raw = open(p, "rb").read()
            h = hashlib.sha256(raw).hexdigest()[:8]
            norm_raw = raw.replace(b"\r\n", b"\n")
            nh = hashlib.sha256(norm_raw).hexdigest()[:8]
            hashes.append(h)
            normalized_hashes.append(nh)
        else:
            hashes.append("MISSING")
            normalized_hashes.append("MISSING")
    
    same_norm = (normalized_hashes[0] == normalized_hashes[1] == normalized_hashes[2])
    print(f"{f:<15} | {hashes[0]:<20} | {hashes[1]:<20} | {hashes[2]:<20} (Content Match: {same_norm})")

