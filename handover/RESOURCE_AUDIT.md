# RESOURCE_AUDIT.md

All findings below are from direct inspection of this audit session's container
(`/home/claude/rw-guard-watermarks`), 2026-10-31. Nothing here is assumed from prior sessions
unless explicitly marked "per prior session / report".

## 1. Runtime environment (this audit container)

| Item | Value |
|---|---|
| OS | Linux (container), kernel 6.18.44 |
| Python | 3.13.18, at `/usr/local/bin/python3` |
| Virtual environment | None identifiable (system-level `pip` packages) |
| Dependency manager | pip (no `poetry.lock`/`Pipfile`/`conda env` in repo) |
| PyTorch | **Not installed.** `import torch` fails with `ModuleNotFoundError`. |
| torchvision | Not checked directly (depends on torch; not installed). |
| NumPy | 2.5.3 installed |
| CUDA | Not applicable — no GPU, no `nvidia-smi` binary |
| GPU | **None** in this container |
| System RAM | 7.8 GiB total, ~7.2 GiB free at audit time |
| Disk | 252 GB filesystem, ~30 GiB available |
| Internet | Reachable — `curl https://pypi.org` returned HTTP 200 through the session's proxy |
| Can execute existing training code? | **No** — `train.py`/`evaluate.py`/`train_with_neural.py` all `import torch` at module load; none can run until PyTorch is installed, and even then there is no GPU and no dataset here. |

This audit did **not** install, upgrade, or remove any package (rule 3.2 compliance).

## 2. Dependency audit (`requirements.txt` vs. installed)

| Dependency | Declared | Installed here | Status |
|---|---|---|---|
| `numpy>=1.24` | yes | 2.5.3 | Installed and importable |
| `opencv-python-headless>=4.8` | yes | 5.0.0.93 (+ `opencv-python`, `opencv-contrib-python` also present) | Installed and importable |
| `Pillow>=10.0` | yes | 12.3.0 | Installed and importable |
| `tqdm>=4.66` | yes | not checked individually (not in filtered list) | Unverified — not treated as a risk, ubiquitous package |
| `matplotlib>=3.7` | yes | 3.11.2 | Installed and importable |
| `datasets>=2.19` | yes (for `download_data.py` only) | not in filtered `pip list` output | **Declared but not installed** here |
| `trustmark>=0.5.0` | optional | not in filtered `pip list` output | **Declared but not installed** here |
| `onnxruntime>=1.17` | optional | 1.29.0 | Installed and importable |
| `requests>=2.31` | optional | 2.34.2 | Installed and importable |
| `torch` / `torchvision` | required (install separately, per README) | **not installed** | **Missing — blocks every entry point** |
| `scikit-learn`, `scipy`, `scikit-image` | not declared in requirements.txt | 1.9.1 / 1.18.1 / 0.26.0 installed | Undeclared but present; available if a shortcut-baseline script wants `sklearn.linear_model.LogisticRegression` instead of a hand-rolled one |

**Conclusion:** this specific audit container cannot run any entry point as-is. Installing
`torch` (CPU-only build) plus `datasets` and `trustmark` would make the *code paths* importable,
but without a GPU, real training runs (15–20 epochs over thousands of images) would be
impractically slow here, matching this project's established practice of training exclusively
on the user's/professor's Windows+GPU laptops.

## 3. Dataset inventory

| Dataset | Configured location | Exists here? | Notes |
|---|---|---|---|
| MS-COCO val2017 subset | `data/coco` (via `download_data.py --n-coco 5000`) | **No** | Downloaded via HuggingFace `datasets`; not committed to git; must be re-downloaded on any new machine. Deterministic 60/10/30 train/val/test split **by source image** (`rewm.data.split_paths`, seeded). |
| PACS (4 domains) | `data/pacs` (via `download_data.py --n-pacs 400`) | **No** | Same download script; used only as out-of-distribution test data, never for training. |
| TrustMark cache | `data/trustmark_cache` (via `build_trustmark_cache.py`, default 500 train / 100 val source images) | **No** | Derived cache, regenerable from COCO + the `trustmark` pip package; not committed. |
| StegaStamp cache | `data/stegastamp_cache` (via `build_stegastamp_cache.py`) | **No** | Same pattern, derived from COCO + ONNX StegaStamp weights. |

No dataset access, license, or storage constraint is documented in the repo beyond "run
`download_data.py`"; COCO and PACS are both public and openly licensed for research use, so no
authentication is required. All dataset paths above are `EXTERNAL_RESOURCE_REQUIRED` in this
container specifically because the download has never been run here — not because of any
license/access barrier.

## 4. Model and checkpoint inventory

**No checkpoint files (`.pt`) exist anywhere in this repository clone or container.** This is by
design: `runs/` is never committed (not even `.gitignore`d explicitly — it has simply never been
created here). Per the project's established workflow (confirmed across prior sessions), trained
checkpoints (`baseline_e9/best.pt`, `holdout_dct/best.pt`, `holdout_fft/best.pt`, three
reproducibility-seed runs, two adversarial-training runs, TrustMark-mixed runs at
`p∈{0.15,0.25}`) exist only on the user's and the professor's own Windows laptops, never
committed to GitHub and never present in a Claude cloud session.

Consequently:
- Checkpoint **provenance** (exact training command, data split, seed) is only as good as what
  each checkpoint's own embedded `args=vars(args)` dict records (confirmed present in
  `train.py`/`train_with_neural.py` save logic) — this audit could not inspect any actual
  checkpoint's embedded args, because none exist here.
- No checkpoint can be loaded or architecture-verified in this environment (no PyTorch, no
  checkpoint files).
- This is recorded as a reproducibility limitation per rule 3.5, not assumed fixed.

## 5. Entry-point inventory (inspected from source, NOT executed)

| Entry point | Verified by | Key arguments |
|---|---|---|
| `python download_data.py [--n-coco N] [--n-pacs N] [--skip-coco] [--skip-pacs]` | source inspection only | downloads to `data/coco`, `data/pacs` |
| `python sanity_check.py --data data/coco` | source inspection only | prints PSNR/bit-accuracy tables, saves `example.png` |
| `python train.py --data data/coco --out runs/<name> [--arch forensic\|forensic_nohp\|simple\|resnet18] [--holdout <scheme>...] [--adv-eps E] [--seed N] ...` | source inspection only | saves `last.pt`, `best.pt`, `history.json` |
| `python evaluate.py --ckpt runs/<name>/best.pt --data data/coco --pacs data/pacs --out results/<name>` | source inspection only | saves `results.json`, `results.md`, `roc.png` |
| `python train_with_neural.py ... --trustmark-dir data/trustmark_cache --trustmark-p 0.25` | source inspection only | same outputs as `train.py` |
| `python build_trustmark_cache.py --data data/coco --out data/trustmark_cache` | source inspection only | requires `trustmark` pip package |
| `python build_stegastamp_cache.py --data data/coco --out data/stegastamp_cache` | source inspection only | requires `onnxruntime` + internet (first-use weight download) |
| `python test_trustmark.py` / `test_trustmark_detector.py` / `test_stegastamp.py` / `test_stegastamp_detector.py` | source inspection only | manual `__main__` scripts, not pytest |
| `python test_realistic_attack.py` | source inspection only | the one existing combined-attack robustness test |

**None of the above have been executed in this session.** All prior successful executions (per
the project report and earlier session history) were run on the user's or professor's own
machines, not reproduced or re-verified here.

## 6. Compute classification per experiment (Phase 3 requirement)

| Experiment | Classification | Why |
|---|---|---|
| Static code audit / grep inventory | `CPU_ONLY` | Already done, this session. |
| A lightweight readiness/smoke check (imports, path existence) | `CPU_ONLY` | No GPU needed; blocked here only by missing `torch`/`datasets` packages, which pip can install without a GPU. |
| `sanity_check.py` | `CPU_ONLY`, potentially slow for all 49 scheme pairs but feasible | No PyTorch dependency at all (pure NumPy/OpenCV/PIL) — this is the cheapest possible real-code smoke test and should be the first thing run on a resumed machine. |
| Unit tests for `rewm/metrics.py`, `rewm/watermarks.py` (if written) | `CPU_ONLY` | Pure NumPy, no GPU, no dataset needed beyond a couple of sample images. |
| Residual-energy / frequency-statistics shortcut baseline (review item G) | `CPU_ONLY` or `GPU_RECOMMENDED` | A `sklearn.linear_model.LogisticRegression` on hand-crafted features needs no GPU; only needs the dataset (COCO) to generate features from, which is `EXTERNAL_RESOURCE_REQUIRED` here specifically because it hasn't been downloaded in this container. |
| Bootstrap confidence intervals from existing `results.json` files | `CPU_ONLY` | Needs only the already-computed JSON result files (which exist on the user's/professor's machines from prior runs, not in this container) — no GPU, no retraining. Flagged as a quick win in prior sessions; still not implemented as a script. |
| Full `train.py` run (15–20 epochs, thousands of images) | `GPU_REQUIRED_OR_PRACTICALLY_NECESSARY` | Matches this project's established practice; a CPU-only run would be impractically slow for the epoch counts used throughout the reported results. |
| `evaluate.py` full six-axis pass | `GPU_RECOMMENDED` | Mostly inference (fast even on CPU) except the PGD-10 adversarial block, which needs gradients through the model repeatedly — feasible on CPU for the existing 100-image sample but slow. |
| TrustMark/StegaStamp cache building + mixed training | `EXTERNAL_RESOURCE_REQUIRED` here | Needs COCO data + the respective package (`trustmark`, `onnxruntime`) + (for training) GPU. |
| SRNet / ZhuNet / SiaStegNet baselines | `EXTERNAL_RESOURCE_REQUIRED` + `GPU_RECOMMENDED` | None of these exist in the repo; would need new implementation (not just a config change) plus GPU training. Scope and timeline risk flagged in `IMPLEMENTATION_PLAN.md`. |
| Adversarial-training re-attempt with a tuned schedule (future work item from the report) | `GPU_REQUIRED_OR_PRACTICALLY_NECESSARY` | Same reasoning as full training. |

## 7. External dependencies and constraints

- **TrustMark**: public pip package with bundled weights, no authentication required, Apache/MIT-family license per package metadata (not independently re-verified here).
- **StegaStamp (ONNX)**: auto-downloaded from a public GitHub-hosted mirror (ISPRAS WIBE
  benchmark, Apache-2.0) on first use — requires outbound internet at run time, no credentials.
- **MS-COCO / PACS**: both public research datasets, fetched via HuggingFace `datasets`; no
  authentication required for the specific subsets this project uses, per the existing
  `download_data.py` implementation.
- **No secrets, API keys, or private URLs were found anywhere in the repository** during this
  audit (`grep`-level check of all tracked files for common credential patterns found nothing;
  this is not a substitute for a dedicated secret-scanning tool, but no obvious leak exists).
- No license file (`LICENSE`) was found in the repo root — not a blocker for this audit, but
  worth the user's attention before any public release.

## 8. Summary: what can run right now, anywhere

| Can run today, CPU-only, no dataset | Needs dataset download, still CPU-feasible | Needs GPU (per established practice) |
|---|---|---|
| A new pytest suite for `rewm/metrics.py`/`rewm/watermarks.py` using synthetic/small sample images | `sanity_check.py`, a shortcut-energy baseline, bootstrap CIs from existing results | `train.py`, `train_with_neural.py`, any full `evaluate.py` run, SRNet/ZhuNet/SiaStegNet training |
