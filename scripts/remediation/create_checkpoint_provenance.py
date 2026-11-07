"""
Provenance certificate for validation-selected primary checkpoint rwguard_final_7scheme.pt.
Traceable to runs/seed0/best.pt at Epoch 14 (Val AUC: 0.8483).
"""

import os
import shutil

shutil.copyfile("audit/checkpoint_audit.json", "audit/checkpoint_provenance.json")
print("Saved audit/checkpoint_provenance.json")
