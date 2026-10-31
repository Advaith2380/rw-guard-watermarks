# IMPLEMENTATION_PLAN.md

Ordered, independently-executable tasks. Each is scoped so a different agent/session could pick
it up alone, given only this handover package and the repository. Sequencing follows the task
instructions' Phase 6 order, adapted to this project's actual gaps (see `REVIEW_TRACEABILITY.md`
for full per-item detail — this file is the execution plan, that file is the evidence).

**Do not start multi-hour training during tasks 1–5.** Tasks 1, 2, 3, 6 are CPU-only and need no
GPU. Task 4 needs the dataset but not a GPU. Tasks 5, 7+ need a GPU, per established project
practice (user's or professor's Windows laptop).

---

## Task 0 (done, this session): Repository and resource audit

Status: `TESTED_PASS` (the audit itself — see `TEST_STATUS.md` for exact commands run).

## Task 1: Readiness smoke test on a real training machine

- **Objective:** confirm the existing pipeline still runs end-to-end before touching any code.
- **Files:** none modified; run existing `sanity_check.py`, then a tiny `train.py` smoke run.
- **Dependencies:** PyTorch installed, COCO data downloaded (`download_data.py`).
- **Proposed steps:**
  1. `pip install -r requirements.txt` then install PyTorch per pytorch.org for your platform.
  2. `python download_data.py --n-coco 200 --skip-pacs` (small subset, fast).
  3. `python sanity_check.py --data data/coco`
  4. `python train.py --data data/coco --out runs/smoke --n-train 50 --epochs 1`
  5. `python evaluate.py --ckpt runs/smoke/best.pt --data data/coco --n-test 20`
- **Tests:** the commands themselves; expect no exceptions, `results.json` written.
- **Acceptance criteria:** all 5 commands exit 0.
- **Risk of regression:** none — no production files touched.
- **Estimated complexity:** Trivial.
- **Status:** `NOT_STARTED` (blocked on GPU/dataset machine; cannot run in a cloud audit
  container — see `RESOURCE_AUDIT.md`).

## Task 2: Residual-energy / frequency-statistics shortcut baseline (review item G)

- **Objective:** produce a cheap, non-deep baseline to test whether ForensicNet's signal is
  specific to "overwriting" or explainable by simple perturbation-energy statistics.
- **Files:** new `shortcut_baseline.py` at repo root.
- **Dependencies:** COCO data (same split as `ReWMDataset`, via `rewm.data.split_paths`); no
  PyTorch needed — use `rewm.watermarks` directly for generation and `sklearn` for the classifier.
- **Proposed steps:**
  1. Reuse `rewm.data.list_images` + `split_paths` for an identical train/val/test split.
  2. For each sample, generate via the same `embed_random`/double-embed logic as
     `ReWMDataset.__getitem__` (import and call directly — don't duplicate the embedding code).
  3. Feature vector: high-pass residual variance/energy (apply a fixed high-pass kernel, e.g.
     reuse `rewm.model.HighPass`'s kernel definition translated to NumPy, or a simple Laplacian),
     plus a handful of DCT/FFT band-energy ratios.
  4. Fit `sklearn.linear_model.LogisticRegression` on train, select threshold on val (mirroring
     `evaluate.py`'s methodology exactly), report AUC/TPR@1%FPR/TPR@fixed/FPR@fixed on test using
     `rewm.metrics` functions directly, for an apples-to-apples comparison.
- **Tests:** feature extractor sanity-checked on 2–3 known clean vs. re-watermarked images.
- **Acceptance criteria:** a results table directly comparable to ForensicNet's Table 8.
- **Risk of regression:** none (new file only).
- **Estimated complexity:** Low–Medium.
- **Estimated compute:** `CPU_ONLY`.
- **Status:** `NOT_STARTED`.

## Task 3: Attack-outcome labelling (review items C/D)

- **Objective:** classify each re-watermarking sample as successful-overwrite / dual-survival /
  failed-attack, based on decoded bit accuracy, not just "two embeddings happened."
- **Files:** new `rewm/outcomes.py`; edits to `rewm/data.py` (`ReWMDataset.__getitem__`, add an
  `outcome` field alongside `kind` — additive, does not change the existing `kind`/`label`
  contract, so it's a low-regression-risk change); edits to `evaluate.py`'s `breakdown()` call
  site to also group by outcome.
- **Dependencies:** `rewm.watermarks.SCHEMES[...].extract` (already exists, already proven
  correct via `sanity_check.py`).
- **Proposed steps:**
  1. Extract the bit-accuracy comparison logic already in `sanity_check.py`'s pair-loop into
     `rewm/outcomes.py::classify_outcome(victim_bits, attacker_bits, decoded_victim,
     decoded_attacker, thresh=0.75) -> str`.
  2. In `ReWMDataset.__getitem__`, after a double-embed (label==1), decode both watermarks from
     the final image and call `classify_outcome`; attach as a new `outcome` key in the returned
     dict (keep existing `kind`/`label`/`x`/`y` unchanged for backward compatibility with
     `rewm/engine.py::predict`, which only reads `x`/`y`/`kind` today — confirm before merging
     that `predict()` tolerates an extra dict key, or that callers use `.get()`).
  3. In `evaluate.py`, collect `outcome` alongside `kinds` in the eval loop and add an
     outcome-stratified breakdown table.
- **Tests:** unit test comparing `classify_outcome` against `sanity_check.py`'s printed numbers
  for the known same-scheme pairs (expect `"overwritten"` for dct_qim>dct_qim, dwt_qim>dwt_qim,
  fft_ring>fft_ring; `"dual_survival"` for ss_spatial>ss_spatial and most cross-scheme pairs).
- **Acceptance criteria:** `evaluate.py --out results/outcome_check` produces an
  outcome-stratified detection-rate table.
- **Risk of regression:** Low-Medium — touches the hot path of `ReWMDataset.__getitem__`; must
  not change existing `label`/`kind` semantics, only add a field. Run the existing `sanity_check.py`
  and a short training smoke test (Task 1) afterward to confirm nothing broke.
- **Estimated complexity:** Medium.
- **Estimated compute:** `CPU_ONLY` for the labelling logic itself; needs a GPU training re-run
  only if you also want a detector trained/evaluated with outcome-awareness, not just outcome-
  labelled data statistics.
- **Status:** `NOT_STARTED`. **Highest scientific priority** per `REVIEW_TRACEABILITY.md`.

## Task 4: Distortion-matched controls (review items E/F)

- **Objective:** generate negatives with perturbation energy matched to re-watermarked
  positives, isolating "overwriting-specific" signal from "more perturbation in general."
- **Files:** new `matched_controls.py`, building on Task 3's outcome/energy primitives.
- **Dependencies:** Task 3 (for a shared notion of "residual energy" to match against) is a soft
  dependency — this task can start with a simpler PSNR-based matching if Task 3 isn't done yet.
- **Status:** `NOT_STARTED`. See `REVIEW_TRACEABILITY.md` items E/F for full detail.
- **Estimated compute:** `CPU_ONLY` generation, `GPU_RECOMMENDED` for a follow-up evaluation run.

## Task 5: Bootstrap confidence intervals (review item Q)

- **Objective:** report percentile CIs for AUC/TPR@1%FPR/fixed-threshold TPR,FPR from
  already-saved `results.json` files, no retraining.
- **Files:** new `bootstrap_ci.py`.
- **Dependencies:** an existing `results.json` (produced by a prior `evaluate.py` run — exists
  on the user's/professor's machine from earlier sessions, not in this container).
- **Proposed steps:** resample per-image scores+labels with replacement (N=1000+ resamples),
  recompute `rewm.metrics.roc_auc`/`tpr_at_fpr`/`rates_at` per resample, report 2.5th/97.5th
  percentiles.
- **Tests:** validate against a synthetic dataset with known true AUC (e.g. scores drawn from two
  separated Gaussians).
- **Acceptance criteria:** CIs addable to any existing results table without retraining.
- **Risk of regression:** none (new file, reads existing JSON only).
- **Estimated complexity:** Low.
- **Estimated compute:** `CPU_ONLY`.
- **Status:** `NOT_STARTED`. Cheapest available win — can run on the user's laptop immediately,
  no GPU, no dataset download even needed (just the existing `results.json` files).

## Task 6: Automated tests (review item X)

- **Objective:** a real, CPU-only pytest suite.
- **Files:** new `tests/test_metrics.py`, `tests/test_watermarks.py`, `tests/test_rng.py`;
  `pytest` added to `requirements.txt` (dev-only, clearly marked).
- **Dependencies:** none beyond `pytest`.
- **Status:** `NOT_STARTED`. See `REVIEW_TRACEABILITY.md` item X.
- **Estimated compute:** `CPU_ONLY`.

## Task 7: Config/environment manifest capture (review item U)

- **Objective:** write `config.json` + `split_manifest.json` alongside every `train.py`/
  `train_with_neural.py` run, capturing git commit, package versions, and resolved file lists,
  not just the args embedded in the `.pt` checkpoint.
- **Files:** edits to `train.py`, `train_with_neural.py` (additive — write two new JSON files at
  run start, don't change existing checkpoint-saving logic).
- **Status:** `NOT_STARTED`. Low risk, low complexity, `CPU_ONLY`.

## Task 8: Protocol-consistency scheme-set versioning (review item H)

- **Objective:** a named, versioned scheme-set config so every run is traceable to an explicit
  protocol version instead of "whichever schemes existed in the repo at the time."
- **Files:** new `scheme_sets.json`; `train.py`/`train_with_neural.py` gain a `--scheme-set`
  flag.
- **Status:** `NOT_STARTED`. Low risk, low complexity, `CPU_ONLY`.

## Task 9: StegaStamp full training + evaluation (review item I, second half)

- **Objective:** complete what TrustMark already has — full mixed-training + six-axis evaluation.
- **Files:** none new — run the existing pipeline (`build_stegastamp_cache.py` →
  `train_with_neural.py --stegastamp-dir ...` → `evaluate.py` / `test_stegastamp_detector.py`).
- **Status:** `NOT_STARTED`. `GPU_REQUIRED_OR_PRACTICALLY_NECESSARY`. This is "run it," not
  "build it" — infrastructure cost already paid.

## Task 10: Multi-restart adversarial evaluation (review item W)

- **Objective:** report worst-case-over-restarts PGD detection, not single-restart.
- **Files:** `rewm/engine.py::pgd_attack` (add a restarts loop), `evaluate.py` (expose
  `--adv-steps`/`--adv-restarts` CLI flags, currently hardcoded).
- **Status:** `NOT_STARTED`. `GPU_RECOMMENDED`.

## Task 11: SRNet / ZhuNet / SiaStegNet baselines (review item L)

- **Objective:** three additional architecture baselines, "where feasible."
- **Status:** `NOT_STARTED`. **Explicitly flagged as high-complexity/stretch-goal** — new
  architecture implementation, not configuration, `GPU_REQUIRED_OR_PRACTICALLY_NECESSARY`. Do
  this last, and only if time permits after tasks 2, 3, 5 (the cheap, high-value items) are done.

## Task 12: PowerShell-compatible orchestration script (review item Y)

- **Objective:** a thin `orchestrate.py` wrapper so the user doesn't hand-run each command.
- **Status:** `NOT_STARTED`. Low priority — most valuable once tasks 2–9 exist and there's a
  longer real sequence worth automating; building it first would just wrap commands that don't
  exist yet.

---

## Recommended execution order given limited remaining time

1. **Task 5** (bootstrap CIs) — cheapest, CPU-only, immediate statistical-rigor win.
2. **Task 2** (shortcut baseline) — CPU-only, directly answers the review's central question.
3. **Task 3** (attack-outcome labelling) — highest scientific priority, needs the most care.
4. **Task 9** (StegaStamp run) — GPU time already justified by existing infrastructure.
5. **Task 7, Task 8** (manifest capture, scheme-set versioning) — cheap rigor wins, can run
   alongside tasks 2–4 since they touch different files.
6. **Task 6** (automated tests) — formalizes what tasks 2/3/5 already validate ad hoc.
7. **Task 4, Task 10** (matched controls, multi-restart adversarial) — medium cost, medium value.
8. **Task 12** (orchestration script) — convenience, do once there's a real sequence to wrap.
9. **Task 11** (SRNet/ZhuNet/SiaStegNet) — highest cost, do last, only if time remains.
