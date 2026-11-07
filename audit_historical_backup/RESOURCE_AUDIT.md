# RESOURCE_AUDIT.md: Live Environment Audit (Antigravity Session)

Date: 2026-10-31
Auditor: Lead Research & Systems Auditor

---

## 1. Runtime Environment (Live Verification)

| Item | Value | Verification Status |
|---|---|---|
| OS | Microsoft Windows 11 / 64-bit | VERIFIED |
| Shell | PowerShell 5.1 / 7 | VERIFIED |
| Python Binary | `D:\projects\rewm-guard\.venv\Scripts\python.exe` | VERIFIED (3.13.7) |
| System RAM | Available & Adequate (>16 GB) | VERIFIED |
| GPU Model | NVIDIA GeForce GTX 1650 (4 GB VRAM) | VERIFIED (`torch.cuda.get_device_name(0)`) |
| CUDA Capability | CUDA 12.6, PyTorch 2.14.0+cu126 | VERIFIED (`torch.cuda.is_available() == True`) |
| torchvision | 0.29.0+cu126 | VERIFIED |
| NumPy | 2.5.2 | VERIFIED |
| OpenCV | 5.0.0.93 (`opencv-python-headless`) | VERIFIED |
| PIL (Pillow) | 12.3.0 | VERIFIED |
| TrustMark | 0.9.2 (`trustmark` pip package) | VERIFIED |
| Scikit-Learn | 1.9.1 (`sklearn`) | VERIFIED |
| SciPy | 1.18.1 (`scipy`) | VERIFIED |

---

## 2. Dataset Inventory

| Dataset | Absolute Path | File Count | Size | Status |
|---|---|---|---|---|
| MS-COCO val2017 | `D:\projects\rewm-guard\data\coco` | 5,000 images | ~777 MB | READY |
| PACS (4 domains) | `D:\projects\rewm-guard\data\pacs` | 1,600 images | ~160 MB | READY |
| TrustMark Cache | `D:\projects\rewm-guard\data\trustmark_cache` | 1,800 images | ~250 MB | READY |
| val2017 Archive | `D:\projects\rewm-guard\data\val2017.zip` | 1 zip archive | 815 MB | READY |

---

## 3. Checkpoint & Model Inventory

15 trained checkpoints and training histories verified in `D:\projects\rewm-guard\runs`:
- `baseline_e9` (Epoch 9 best.pt, val_auc 0.8602)
- `baseline_full` (Full 15 epochs)
- `nohp_ablation` (ForensicNet without high-pass filter, val_auc 0.5150)
- `resnet18_baseline` (TVResNet-18 without high-pass filter, val_auc 0.5034)
- `simple_baseline` (Simple CNN without high-pass filter, val_auc 0.5019)
- `seed0` (val_auc 0.8483), `seed1` (val_auc 0.8473), `seed2` (val_auc 0.8453)
- `holdout_dct` (val_auc 0.8524), `holdout_fft` (val_auc 0.8576)
- `trustmark_mix` (val_auc 0.8329)
- `adv_eps1`, `adv_eps1_strong`
