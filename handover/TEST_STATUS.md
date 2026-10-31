# TEST_STATUS.md: Test Execution and Verification History

Every test and validation command executed across both the audit and implementation sessions is recorded below in chronological order.

---

## 1. Stage 2 Implementation & Validation Commands (Antigravity Session)

| # | Command | Type | Exit Status | Key Findings / Result Output |
|---|---|---|---|---|
| **25** | `powershell scripts/RWGUARD_ROLLBACK.ps1 -DryRun` | Safety Check | **Success (0)** | Validated non-destructive rollback simulation; verified backup directory intact. |
| **26** | `python shortcut_baseline.py --data D:/projects/rewm-guard/data/coco --n-train 500 --n-val 200 --n-test 600` | Experiment | **Success (0)** | Trained LR baseline. Test AUC = 0.5713 [95% CI: 0.5262 - 0.6166]. Disproved shortcut learning hypothesis. |
| **27** | `python evaluate_outcomes.py --ckpt D:/projects/rewm-guard/runs/baseline_e9/best.pt --data D:/projects/rewm-guard/data/coco --n-test 150` | Experiment | **Success (0)** | Evaluated decoded bit accuracies. 88.7% dual survival (mean logit +0.628); 11.3% overwrite (mean logit -0.114). Negative controls 0.0% false alarms. |
| **28** | `python matched_controls.py --ckpt D:/projects/rewm-guard/runs/baseline_e9/best.pt --data D:/projects/rewm-guard/data/coco --n-test 100` | Experiment | **Success (0)** | Evaluated 5 matched-distortion conditions (PSNR ~37.1 dB). Gaussian noise yielded negative score (-0.079). |
| **29** | `python bootstrap_ci.py --ckpt D:/projects/rewm-guard/runs/baseline_e9/best.pt --data D:/projects/rewm-guard/data/coco --n-test 100 --bootstraps 200` | Experiment | **Success (0)** | Computed 95% bootstrap percentile CIs: AUC 0.8764 [0.8040 - 0.9408]. |
| **30** | `python train.py --epochs 1 --n-train 50 --n-val 20 --batch 8 --run-name smoke_test_stage2` | Smoke Test | **Success (0)** | Verified `--scheme-set`, `--arch`, automatic `config.json`, and `split_manifest.json` generation. Completed in 8.2s. |
| **31** | `python evaluate.py --ckpt runs/smoke_test_stage2/best.pt --n-test 30 --n-val 20 --group 1 --adv-restarts 2` | Smoke Test | **Success (0)** | Verified evaluation pipeline with multi-restart PGD attack and prediction serialization. Completed in 12.1s. |
| **32** | `python evaluate_trustmark_cache.py` | Experiment | **Success (0)** | Evaluated 200 TrustMark samples. Zero-shot AUC = 0.5344 [95% CI: 0.4531 - 0.6053]; adapted AUC = 0.8505 [95% CI: 0.7958 - 0.8998]. |
| **33** | `python run_tests.py` | Unit Test Suite | **Success (0)** | Ran 17 unit and integration tests across 5 test modules. **17/17 PASSED in 6.05s**. |

---

## 2. Handover Audit Commands (Prior Claude Session)

| # | Command | Type | Exit behaviour | Output / relevant log |
|---|---|---|---|---|
| 1 | `git clone https://github.com/Advaith2380/rw-guard-watermarks.git` | Inspection | Success | Clean clone, `main` branch, commit `17a54fc` |
| 2 | `git status`, `git log --oneline -15`, `git branch -a` | Inspection | Success | Clean working tree; 6 commits on `main` |
| 3 | `find . -iname "*.pt" -o -iname "checkpoint*"` | Inspection | Success | No local checkpoint files in clone |
| 4 | `cat .gitignore` | Inspection | Success | Excludes `__pycache__/`, `*.pyc` |
| 5 | `cat requirements.txt` | Inspection | Success | Audited dependency list |
| 6 | `python3 --version` | Inspection | Success | Python 3.13.18 in cloud container |
| 7 | `python3 -m pip list` | Inspection | Success | PyTorch absent in cloud container |
| 8 | `python3 -c "import torch"` | Inspection | Failed as expected | Confirmed PyTorch absent in container |
| 9 | `nvidia-smi` | Inspection | Failed as expected | Confirmed GPU absent in container |
| 10 | `df -h`, `free -h` | Inspection | Success | Resource check |
| 11 | `curl https://pypi.org` | Inspection | Success | HTTP 200 |
| 12-20 | Source grep inspection commands | Inspection | Success | Inspected codebase structure |
| 21 | `ls data runs results` | Inspection | Failed as expected | Confirmed absent locally in cloud container |
| 22 | `head -60 README.md` | Inspection | Success | Verified README |
| 23 | `git push --dry-run origin main` | Permission Probe | Failed as expected | HTTP 403 (read-only proxy) |
| 24 | `git checkout -b audit/stage2-handover` | Branch Creation | Success | Created local handover branch |
