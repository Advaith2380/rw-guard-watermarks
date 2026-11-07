"""Verification Toolchain Step 1: Checkpoint Integrity and Provenance Verification.

Validates:
1. Exact file existence and cryptographic SHA-256 hash against expected:
   37680cdd2d4e5100cbb8aa1642e78b9bb3df373e79efd9f8512f89e15d0c0573
2. Parameter count matches exactly 2,466,099.
3. State dictionary tensor shapes, dtypes, and absence of NaN/Inf values.
4. Provenance comparison against runs/seed0/best.pt.
5. Saves all audit artifacts to audit/final_independent_verification/.
"""

import argparse
import hashlib
import json
import logging
import os
import sys
import torch

sys.path.insert(0, os.path.abspath("."))
from rewm.model import build_model


EXPECTED_SHA256 = "37680cdd2d4e5100cbb8aa1642e78b9bb3df373e79efd9f8512f89e15d0c0573"
EXPECTED_PARAMS = 2466099
DEFAULT_CKPT = "checkpoints/final/rwguard_final_7scheme.pt"
SEED0_CKPT = "runs/seed0/best.pt"


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_checkpoint(ckpt_path=DEFAULT_CKPT, out_dir="audit/final_independent_verification"):
    os.makedirs(out_dir, exist_ok=True)
    log_file = os.path.join(out_dir, "checkpoint_verification.log")
    
    # Configure logger
    logger = logging.getLogger("verify_checkpoint")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fh = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    sh = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    fh.setFormatter(formatter)
    sh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(sh)

    logger.info("================================================================================")
    logger.info(" PHASE 2: CHECKPOINT INTEGRITY AND PROVENANCE VERIFICATION")
    logger.info("================================================================================")
    logger.info(f"Target checkpoint: {ckpt_path}")

    if not os.path.exists(ckpt_path):
        logger.error(f"CRITICAL: Checkpoint does not exist at {ckpt_path}!")
        return False

    # 1. SHA-256 Verification
    actual_size = os.path.getsize(ckpt_path)
    actual_hash = sha256_file(ckpt_path)
    hash_match = (actual_hash.lower() == EXPECTED_SHA256.lower())
    logger.info(f"Actual SHA-256:   {actual_hash}")
    logger.info(f"Expected SHA-256: {EXPECTED_SHA256}")
    logger.info(f"Hash match status: {'PASS' if hash_match else 'FAIL'}")
    logger.info(f"File size:        {actual_size} bytes")

    integrity_report = {
        "checkpoint_path": os.path.abspath(ckpt_path).replace("\\", "/"),
        "file_size_bytes": actual_size,
        "actual_sha256": actual_hash,
        "expected_sha256": EXPECTED_SHA256,
        "hash_verified": hash_match,
        "status": "PASS" if hash_match else "FAIL"
    }
    with open(os.path.join(out_dir, "checkpoint_integrity.json"), "w", encoding="utf-8") as f:
        json.dump(integrity_report, f, indent=2)

    # 2. Architecture & State Dictionary Inspection
    logger.info("Loading checkpoint PyTorch state dictionary...")
    state = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    
    targs = state.get("args", {})
    arch = targs.get("arch", "forensic")
    width = targs.get("width", 32)
    logger.info(f"Reported architecture in args: {arch} (width={width})")

    model = build_model(arch, width=width)
    weights = state["model"] if "model" in state else state
    load_res = model.load_state_dict(weights, strict=True)
    logger.info(f"State dict strict load: missing_keys={load_res.missing_keys}, unexpected_keys={load_res.unexpected_keys}")

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"Total parameter count:     {total_params}")
    logger.info(f"Trainable parameter count: {trainable_params} (Expected: {EXPECTED_PARAMS})")
    params_match = (total_params == EXPECTED_PARAMS)

    # Tensor value validation (NaN / Inf check)
    nan_tensors, inf_tensors = [], []
    for name, param in model.named_parameters():
        if torch.isnan(param).any():
            nan_tensors.append(name)
        if torch.isinf(param).any():
            inf_tensors.append(name)

    logger.info(f"NaN check: {len(nan_tensors)} tensors with NaN")
    logger.info(f"Inf check: {len(inf_tensors)} tensors with Inf")
    values_finite = (len(nan_tensors) == 0 and len(inf_tensors) == 0)

    # Preprocessing / High-Pass verification
    has_hp = hasattr(model, "hp")
    hp_channels = model.hp.weight.shape if has_hp else None
    logger.info(f"High-pass front end present: {has_hp} (weight shape: {hp_channels})")

    arch_report = {
        "architecture_name": arch,
        "width": width,
        "total_parameters": total_params,
        "trainable_parameters": trainable_params,
        "expected_parameters": EXPECTED_PARAMS,
        "parameter_count_verified": params_match,
        "high_pass_filter_present": has_hp,
        "high_pass_filter_shape": list(hp_channels) if hp_channels else None,
        "strict_load_missing_keys": load_res.missing_keys,
        "strict_load_unexpected_keys": load_res.unexpected_keys,
        "all_parameters_finite": values_finite,
        "nan_tensors": nan_tensors,
        "inf_tensors": inf_tensors,
        "status": "PASS" if (params_match and values_finite) else "FAIL"
    }
    with open(os.path.join(out_dir, "checkpoint_architecture_verification.json"), "w", encoding="utf-8") as f:
        json.dump(arch_report, f, indent=2)

    # 3. Provenance Verification against seed0/best.pt
    seed0_path = SEED0_CKPT
    if not os.path.exists(seed0_path) and os.path.exists("D:/projects/rewm-guard/runs/seed0/best.pt"):
        seed0_path = "D:/projects/rewm-guard/runs/seed0/best.pt"
    
    provenance_match = False
    seed0_hash = "N/A"
    weights_identical = False
    
    if os.path.exists(seed0_path):
        seed0_hash = sha256_file(seed0_path)
        logger.info(f"Seed0 source checkpoint: {seed0_path} (SHA-256: {seed0_hash})")
        
        # Check byte equality
        byte_identical = (actual_hash == seed0_hash)
        logger.info(f"Byte-level identity with seed0/best.pt: {byte_identical}")

        # Check state_dict equality
        state_seed0 = torch.load(seed0_path, map_location="cpu", weights_only=False)
        w_seed0 = state_seed0["model"] if "model" in state_seed0 else state_seed0
        weights_identical = True
        for k in weights:
            if k not in w_seed0 or not torch.equal(weights[k], w_seed0[k]):
                weights_identical = False
                break
        logger.info(f"Tensor-level weight equality with seed0/best.pt: {weights_identical}")
        provenance_match = byte_identical or weights_identical
    else:
        logger.warning(f"Seed0 checkpoint not found at {seed0_path}")

    # Metadata extraction
    meta_epoch = state.get("epoch", None)
    meta_val_auc = float(state.get("val_auc", 0.0))
    meta_schemes = state.get("train_schemes", [])
    logger.info(f"Checkpoint Metadata: epoch={meta_epoch}, val_auc={meta_val_auc:.4f}, schemes={meta_schemes}")

    provenance_report = {
        "primary_checkpoint": os.path.abspath(ckpt_path).replace("\\", "/"),
        "seed0_checkpoint_path": os.path.abspath(seed0_path).replace("\\", "/") if os.path.exists(seed0_path) else None,
        "seed0_sha256": seed0_hash,
        "byte_identical_to_seed0": actual_hash == seed0_hash,
        "weights_identical_to_seed0": weights_identical,
        "metadata": {
            "epoch": meta_epoch,
            "validation_auc": meta_val_auc,
            "training_schemes": meta_schemes,
            "training_args": {k: str(v) for k, v in targs.items()}
        },
        "provenance_verified": provenance_match,
        "status": "PASS" if provenance_match else "FAIL"
    }
    with open(os.path.join(out_dir, "checkpoint_provenance.json"), "w", encoding="utf-8") as f:
        json.dump(provenance_report, f, indent=2)

    # Save sha256 text file
    with open(os.path.join(out_dir, "checkpoint_sha256.txt"), "w", encoding="utf-8") as f:
        f.write(f"{actual_hash}  {os.path.basename(ckpt_path)}\n")

    overall_success = hash_match and params_match and values_finite and provenance_match
    logger.info("--------------------------------------------------------------------------------")
    logger.info(f"CHECKPOINT VERIFICATION OVERALL: {'PASS' if overall_success else 'FAIL'}")
    logger.info("================================================================================\n")
    return overall_success


def main():
    parser = argparse.ArgumentParser(description="Verify checkpoint integrity and provenance.")
    parser.add_argument("--ckpt", default=DEFAULT_CKPT, help="Path to final checkpoint")
    parser.add_argument("--out", default="audit/final_independent_verification", help="Output directory")
    args = parser.parse_args()

    success = verify_checkpoint(args.ckpt, args.out)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
