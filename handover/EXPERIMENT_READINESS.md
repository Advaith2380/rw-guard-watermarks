# EXPERIMENT_READINESS.md

Readiness is assessed **for this audit container**. On a resumed machine (the user's or
professor's Windows laptop, with PyTorch + GPU + downloaded COCO/PACS), re-run the lightweight
check in `IMPLEMENTATION_PLAN.md` Task 1 and update this file with that machine's actual status
— do not assume this container's "waiting for X" carries over unchanged.

| Experiment | Status here | Exact blocker (if any) | Command (once unblocked) |
|---|---|---|---|
| Unit tests (`rewm/metrics.py`, `rewm/watermarks.py`) | **Waiting for dependencies** | No pytest suite exists yet (Task 6, review item X) — write it first | `pytest tests/` (once written) |
| Smoke test (`sanity_check.py`) | **Ready after code changes: none needed** — ready to run as-is, but **waiting for compute/data**: no PyTorch issue (pure NumPy), just needs COCO data | `data/coco` does not exist in this container | `python sanity_check.py --data data/coco` |
| Primary model training (`train.py`) | **Waiting for dependencies + compute + dataset** | PyTorch not installed; no GPU; no COCO data | `python train.py --data data/coco --out runs/baseline` |
| Primary model evaluation (`evaluate.py`) | **Waiting for a checkpoint + dataset** | No checkpoint exists here; no COCO/PACS data | `python evaluate.py --ckpt runs/baseline/best.pt --data data/coco --pacs data/pacs` |
| Matched-control generation (review items E/F) | **Blocked — not yet implemented** | `matched_controls.py` does not exist (Task 4) | N/A until written |
| Shortcut baselines (review item G) | **Blocked — not yet implemented**, but **cheapest to unblock**: needs only COCO data, no GPU, no PyTorch | `shortcut_baseline.py` does not exist (Task 2); once written, only needs `data/coco` | `python shortcut_baseline.py --data data/coco` (once written) |
| Deep-learning baselines (simple CNN, ResNet-18) | **Implemented, waiting for compute + dataset** — code already exists and was previously run successfully (per report) | PyTorch, GPU, COCO data all absent here | `python train.py --arch simple ...` / `--arch resnet18` |
| Architecture ablations (no-high-pass) | **Implemented, waiting for compute + dataset** | Same as above | `python train.py --arch forensic_nohp ...` |
| Multi-seed experiments | **Implemented, waiting for compute + dataset** | Same as above | `python train.py --seed 0/1/2 ...` |
| TrustMark experiments | **Implemented and previously completed** (per report); **waiting for dependencies + compute + dataset** to re-run here | `trustmark` package not installed; no GPU; no COCO data | `python build_trustmark_cache.py ...` → `python train_with_neural.py --trustmark-dir ...` |
| StegaStamp experiments | **Implemented, not yet run to completion anywhere** (review item I, second half) | Needs `onnxruntime` (present), internet (present), GPU + COCO data (absent here) | `python build_stegastamp_cache.py ...` → `python train_with_neural.py --stegastamp-dir ...` |
| External natural-image evaluation (review item N) | **Ambiguous scope — not blocked by this container specifically** | Depends on whether review wants a dataset beyond COCO/PACS; needs a decision, then a dataset | N/A pending scope decision |
| Robustness tests (benign post-processing) | **Implemented, waiting for compute + dataset** | Same as training | `python evaluate.py --benign ...` |
| Resolution tests | **Implemented, waiting for compute + dataset** | Same as training | `python evaluate.py --sizes 128 256 384` |
| Adversarial tests (PGD) | **Implemented, waiting for compute + dataset**; multi-restart variant **blocked — not yet implemented** (review item W) | PGD-10 single-restart exists; restarts flag doesn't | `python evaluate.py --adv-eps-list 0.5 1.0 2.0` |
| Statistical analysis (bootstrap CIs) | **Blocked — not yet implemented**, but **cheapest to unblock**: needs only an existing `results.json`, no GPU, no new dataset | `bootstrap_ci.py` does not exist (Task 5); once written, needs a `results.json` from a prior run | `python bootstrap_ci.py --results results/baseline/results.json` (once written) |
| SRNet / ZhuNet / SiaStegNet baselines | **Blocked — not implemented at all** | No architecture code exists; would need new implementation (Task 11, flagged high-complexity) | N/A until written |
| Automated readiness check script (Phase 8) | **Not yet implemented** | See note below | N/A until written |

## Phase 8 readiness-check script

The task instructions ask for a lightweight, non-training readiness command. **This was not
implemented as a standalone script in this session** (time/priority went to the audit and
traceability matrix first, per the task's own priority order: "handover over broad
implementation"). It is listed as a candidate in `IMPLEMENTATION_PLAN.md` implicitly via Task 6
(tests) and Task 1 (the manual smoke-test sequence, which a script could wrap). A minimal version
would check: `python3 -c "import torch"` exit code, `python3 -c "import numpy, cv2, PIL"` exit
code, existence of `data/coco`, `data/pacs`, existence of a writable `runs/`/`results/` parent
directory, and `nvidia-smi` exit code (optional — mark GPU as "unavailable," not a failure, if
absent, since CPU-only smoke tests are still possible). No PowerShell-specific syntax issue is
expected since this would be a plain `python3 readiness_check.py` invocation, identical on
Windows PowerShell and Linux/macOS shells — not yet written, flagged for a future task.
