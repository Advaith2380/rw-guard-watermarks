"""Attack outcome classification and stratification for RW-Guard.

Distinguishes between four explicit categories (Section 7.2 of Faculty Review):
1. 'successful_overwrite': Attacker watermark passes verification (bit-acc >= tau),
   victim watermark fails verification (bit-acc < tau). True ownership forgery.
2. 'dual_survival': Both victim and attacker watermarks pass verification
   (both bit-acc >= tau). Forensic ownership ambiguity / conflict.
3. 'failed_attacker_embedding': Victim watermark passes verification (bit-acc >= tau),
   attacker watermark fails verification (bit-acc < tau).
4. 'both_unrecoverable': Both victim and attacker watermarks fail verification
   (both bit-acc < tau). Severe destruction / collision.

Review Requirements: REQ-C, REQ-D.
"""

import numpy as np
from rewm.watermarks import SCHEMES, NBITS


DEFAULT_BITACC_THRESHOLD = 0.75


def compute_bit_accuracy(extracted_scores, target_bits):
    """Compute empirical bit accuracy between continuous detector output and binary target."""
    extracted_binary = (np.asarray(extracted_scores) > 0).astype(int)
    target_binary = np.asarray(target_bits).astype(int)
    return float(np.mean(extracted_binary == target_binary))


def extract_and_measure_accuracy(img_uint8, info):
    """Extract watermark bits from image using info metadata and compute bit accuracy."""
    scheme_name = info["scheme"]
    if scheme_name not in SCHEMES:
        return 0.5  # Unknown scheme default to chance
        
    scheme = SCHEMES[scheme_name]
    key = info["key"]
    strength = info.get("strength", 1.0)
    bits = info["bits"]
    
    extracted_scores = scheme.extract(img_uint8, key, NBITS, strength)
    return compute_bit_accuracy(extracted_scores, bits)


def classify_attack_outcome(img_uint8, victim_info, attacker_info, threshold=DEFAULT_BITACC_THRESHOLD):
    """Classify the forensic outcome of a sequential re-watermarking attack.
    
    Args:
        img_uint8: uint8 image after victim + attacker embedding (H, W, 3).
        victim_info: dict containing victim scheme, key, bits, strength.
        attacker_info: dict containing attacker scheme, key, bits, strength.
        threshold: bit accuracy threshold for reliable recovery (default 0.75; 0.5 is chance).
        
    Returns:
        dict containing:
            'outcome': 'successful_overwrite' | 'dual_survival' | 'failed_attack'
            'victim_acc': float
            'attacker_acc': float
            'threshold': float
    """
    v_acc = extract_and_measure_accuracy(img_uint8, victim_info)
    a_acc = extract_and_measure_accuracy(img_uint8, attacker_info)
    
    if a_acc >= threshold and v_acc < threshold:
        outcome = "successful_overwrite"
    elif a_acc >= threshold and v_acc >= threshold:
        outcome = "dual_survival"
    elif a_acc < threshold and v_acc >= threshold:
        outcome = "failed_attacker_embedding"
    else:
        outcome = "both_unrecoverable"
        
    return {
        "outcome": outcome,
        "victim_bitacc": v_acc,
        "attacker_bitacc": a_acc,
        "threshold": threshold,
        "category_id": {
            "successful_overwrite": 1,
            "dual_survival": 2,
            "failed_attacker_embedding": 3,
            "both_unrecoverable": 4
        }[outcome]
    }
