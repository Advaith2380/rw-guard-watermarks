"""
Verify the real MS-COCO dataset at D:/projects/rewm-guard/data/coco:
1. Verify 5,000 source image files exist and decode cleanly.
2. Check dimensions and channels.
3. Compute SHA-256 for all 5,000 images.
4. Verify split_paths partition: 3,000 train, 500 val (300 calibration subset), 1,500 test.
5. Verify 0 split leakage.
6. Generate master_source_manifest.csv with required fields.
"""

import os
import sys
import hashlib
import csv
import json
from PIL import Image
import numpy as np

sys.path.insert(0, os.path.abspath("."))
from rewm.data import list_images, split_paths

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def simple_dhash(image, hash_size=8):
    """Compute difference hash (dHash) for perceptual similarity check."""
    img = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = list(img.getdata())
    diff = []
    for row in range(hash_size):
        for col in range(hash_size):
            pixel_left = pixels[row * (hash_size + 1) + col]
            pixel_right = pixels[row * (hash_size + 1) + col + 1]
            diff.append(pixel_left > pixel_right)
    decimal_value = 0
    hex_string = []
    for index, value in enumerate(diff):
        if value:
            decimal_value += 2 ** (index % 8)
        if (index % 8) == 7:
            hex_string.append(hex(decimal_value)[2:].rjust(2, '0'))
            decimal_value = 0
    return "".join(hex_string)

def main():
    print("=" * 80)
    print("VERIFYING MS-COCO DATASET & GENERATING AUTHORITATIVE MANIFEST")
    print("=" * 80)

    coco_dir = "D:/projects/rewm-guard/data/coco"
    if not os.path.exists(coco_dir):
        raise FileNotFoundError(f"MS-COCO dataset directory not found at {coco_dir}")

    image_paths = list_images(coco_dir)
    print(f"Discovered {len(image_paths)} images in {coco_dir}.")
    assert len(image_paths) == 5000, f"Expected 5,000 images, found {len(image_paths)}"

    # 1. Split computation
    tr_paths, va_paths, te_paths = split_paths(image_paths, seed=0, fractions=(0.6, 0.1, 0.3))
    print(f"Partition counts: Train={len(tr_paths)}, Val={len(va_paths)}, Test={len(te_paths)}")
    assert len(tr_paths) == 3000
    assert len(va_paths) == 500
    assert len(te_paths) == 1500

    tr_set = set(tr_paths)
    va_set = set(va_paths)
    te_set = set(te_paths)

    assert len(tr_set.intersection(va_set)) == 0, "Train-Val overlap detected!"
    assert len(tr_set.intersection(te_set)) == 0, "Train-Test overlap detected!"
    assert len(va_set.intersection(te_set)) == 0, "Val-Test overlap detected!"
    print("Partition isolation verified: ZERO source image leakage across splits.")

    # 300 validation threshold calibration subset
    va_calib_set = set(va_paths[:300])

    # 2. Decode verification, hashes, and manifest creation
    manifest_rows = []
    sha_set = set()
    dhash_map = {}
    corrupted_count = 0

    print("Verifying image decoding and computing cryptographic & perceptual hashes...")
    for idx, p in enumerate(image_paths):
        fname = os.path.basename(p)
        fsize = os.path.getsize(p)
        
        # Check split
        if p in tr_set:
            split_name = "train"
            source_group = "training"
        elif p in va_calib_set:
            split_name = "val_calibration"
            source_group = "validation_calibration_300"
        elif p in va_set:
            split_name = "val_holdout"
            source_group = "validation_extra_200"
        else:
            split_name = "test"
            source_group = "held_out_test_1500"

        # Decode image
        try:
            with Image.open(p) as img:
                w, h = img.size
                mode = img.mode
                dhash = simple_dhash(img)
                file_ok = True
        except Exception as e:
            w, h, mode, dhash = 0, 0, "ERROR", "ERROR"
            file_ok = False
            corrupted_count += 1

        file_sha = compute_sha256(p)
        sha_set.add(file_sha)

        manifest_rows.append({
            "source_id": f"COCO_{idx:05d}",
            "image_id": fname,
            "absolute_path": os.path.abspath(p),
            "relative_path": f"data/coco/{fname}",
            "dataset_split": split_name,
            "file_exists": file_ok,
            "image_width": w,
            "image_height": h,
            "sha256": file_sha,
            "perceptual_hash": dhash,
            "source_group": source_group
        })

        if (idx + 1) % 1000 == 0:
            print(f"  Processed {idx + 1} / {len(image_paths)} images...")

    print(f"Image verification completed. Corrupted files: {corrupted_count}")
    assert corrupted_count == 0, f"Found {corrupted_count} corrupted images!"
    assert len(sha_set) == 5000, f"Found duplicate SHA-256 hashes! Unique: {len(sha_set)}"
    print(f"All 5,000 images are unique (5,000 distinct SHA-256 signatures).")

    # Save manifest
    os.makedirs("data/manifests", exist_ok=True)
    manifest_csv = "data/manifests/master_source_manifest.csv"
    with open(manifest_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "source_id", "image_id", "absolute_path", "relative_path", "dataset_split",
            "file_exists", "image_width", "image_height", "sha256", "perceptual_hash", "source_group"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)
    print(f"Saved master source manifest: {manifest_csv}")

    # Generate split integrity report JSON
    split_report = {
        "dataset_name": "MS-COCO val2017 Source Collection",
        "dataset_path": os.path.abspath(coco_dir),
        "total_source_images": len(image_paths),
        "corrupted_images": corrupted_count,
        "unique_sha256_hashes": len(sha_set),
        "split_policy": "split_paths(paths, seed=0, fractions=(0.6, 0.1, 0.3))",
        "splits": {
            "training_sources": len(tr_paths),
            "validation_sources_total": len(va_paths),
            "validation_sources_calibration_subset": len(va_calib_set),
            "validation_sources_uncalibrated": len(va_paths) - len(va_calib_set),
            "held_out_test_sources": len(te_paths)
        },
        "leakage_audit": {
            "train_val_overlap": len(tr_set.intersection(va_set)),
            "train_test_overlap": len(tr_set.intersection(te_set)),
            "val_test_overlap": len(va_set.intersection(te_set)),
            "zero_leakage_verified": True
        },
        "derived_samples_accounting": {
            "test_sources": len(te_paths),
            "derived_negative_samples": len(te_paths),
            "derived_positive_samples": len(te_paths),
            "total_test_evaluation_samples": len(te_paths) * 2
        },
        "reconciliation_notes": (
            "The historical report referenced 3,200 training sources by naive subtraction (5000 - 300 - 1500 = 3200). "
            "The actual code implementation in rewm/data.py:split_paths partitions 5,000 sources as 60% train (3,000), "
            "10% val (500), and 30% test (1,500). train.py uses all 3,000 training sources and validates on the first "
            "300 validation sources (n_val=300). The held-out test split of 1,500 sources generates exactly 3,000 balanced "
            "evaluation samples (1 negative and 1 positive per source)."
        )
    }

    report_path = "data/manifests/split_integrity_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(split_report, f, indent=2)
    print(f"Saved split integrity report: {report_path}")

    # Also update derived sample manifest
    derived_csv = "data/manifests/derived_sample_manifest.csv"
    with open(derived_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["sample_index", "source_image_id", "dataset_split", "label", "sample_type"])
        sample_idx = 0
        for p in te_paths:
            img_id = os.path.basename(p)
            writer.writerow([sample_idx, img_id, "test", 0, "unattacked_negative"])
            sample_idx += 1
            writer.writerow([sample_idx, img_id, "test", 1, "re_watermarked_positive"])
            sample_idx += 1
    print(f"Saved derived sample manifest (3,000 rows): {derived_csv}")

    print("\n" + "=" * 80)
    print("PART 2 VERIFICATION COMPLETE: ALL 5,000 MS-COCO SOURCES VERIFIED AND RECONCILED")
    print("=" * 80)

if __name__ == "__main__":
    main()
