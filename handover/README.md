# RW-Guard Stage 2 Handover Package

## Project

**RW-Guard**: forensic detection of re-watermarking attacks (sequential invisible-watermark
embedding) in digital images. Team 12 (Advaith Rajesh, Asrar, Riz Eapen), VIT. Code:
https://github.com/Advaith2380/rw-guard-watermarks

## Purpose of this package

This project's peer review (a *Scientific Reports* Major-Revision review, see
`REVIEW_TRACEABILITY.md`) requested a number of implementation-level corrections beyond what
was already applied to the manuscript text. This package is a read-only audit of the current
repository plus a requirement-traceability matrix, so that implementation work can resume —
from this session, or from a different coding agent (e.g. Google Antigravity) on a different
machine — without re-deriving the project's history from scratch.

**No training, evaluation, or destructive change was run in this session.** The audit session
had no GPU, no PyTorch installed, and no dataset present (see `RESOURCE_AUDIT.md`) — nearly
everything beyond static code reading is `EXTERNAL_RESOURCE_REQUIRED` here and must run on the
user's or professor's Windows/GPU machine, exactly as it always has for this project.

## Read this first, in order

1. `CURRENT_STATE.md` — what's done, in progress, not started, and the exact next action.
2. `REPOSITORY_INVENTORY.md` — what every file in the repo does.
3. `RESOURCE_AUDIT.md` — what this (or any) environment needs to actually run each experiment.
4. `REVIEW_TRACEABILITY.md` — every review requirement mapped to code and a status.
5. `IMPLEMENTATION_PLAN.md` — ordered, independently-executable tasks to close the gaps.
6. `FILE_CHANGELOG.md` — every file this session touched (currently: only files inside
   `handover/`; no production code was modified).
7. `TEST_STATUS.md` — every command actually executed this session, and its real outcome.
8. `EXPERIMENT_READINESS.md` — per-experiment readiness classification.
9. `ANTIGRAVITY_CONTINUATION_PROMPT.md` — paste this into the next agent/session.
10. `state.json` — machine-readable version of the above.

## Current stage

Stage 2, Phase 1–4 complete (audit + handover package). Phase 5 (implementing corrections) has
**not** started — see `CURRENT_STATE.md` for why, and `IMPLEMENTATION_PLAN.md` for the ordered
task list to execute next, on a machine with Python + PyTorch + GPU + the COCO/PACS data
(normally the user's laptop or the professor's laptop, per this project's established workflow).

## Important project paths

- Repo root (this session's clone): `/home/claude/rw-guard-watermarks` (cloned fresh from
  `origin/main`, commit `17a54fc`, read-only remote access — this session cannot push).
- Classical testbed: `rewm/` (`data.py`, `watermarks.py`, `model.py`, `engine.py`, `metrics.py`).
- Neural-watermarker integration: `rewm_trustmark.py`, `rewm_stegastamp.py`,
  `rewm_stegastamp_cache.py`, `rewm_mixing.py`, `build_trustmark_cache.py`,
  `build_stegastamp_cache.py`, `train_with_neural.py`.
- Entry points: `train.py`, `evaluate.py`, `sanity_check.py`, `download_data.py`.
- No `data/`, `runs/`, or `results/` directories exist in this clone or on this machine —
  datasets and checkpoints have never been committed to this repo (by design; see
  `.gitignore` and `RESOURCE_AUDIT.md`).

## How to resume safely

1. Clone/copy the repo (or open the existing checkout) on a machine with Python, PyTorch, a
   GPU, and the COCO/PACS data already downloaded (via `download_data.py`).
2. Read the files above, in order.
3. Run `git status` and `git log -3` yourself and compare against what `CURRENT_STATE.md`
   claims — if they disagree, trust the live repository, not this document, and say so before
   continuing.
4. Pick up the first `NOT_STARTED` or `IMPLEMENTATION_IN_PROGRESS` task in
   `IMPLEMENTATION_PLAN.md` whose dependencies are satisfied.
5. Work in small, independently-testable commits; update `FILE_CHANGELOG.md`, `TEST_STATUS.md`,
   `CURRENT_STATE.md`, and `state.json` after each one.

## Most important unresolved issues

- **Attack-outcome labelling (review items C/D)** is not wired into the training/eval pipeline:
  `sanity_check.py` computes bit-accuracy outcomes (successful overwrite vs. dual-survival) as a
  one-off diagnostic, but training labels are structural ("two embeddings happened"), not
  outcome-verified. This is the review's most scientifically important open item.
- **No shortcut baseline exists** (review item G): no residual-energy or frequency-statistics
  logistic-regression classifier is implemented anywhere in the repo.
- **No distortion-matched controls** (review item E/F) beyond the single combined crop+JPEG test
  in `test_realistic_attack.py`.
- **SRNet / ZhuNet / SiaStegNet baselines** (review item L) do not exist in any form.
- **No automated tests** (review item X): the `test_*.py` files are manual integration scripts
  (each has a `__main__` block you run by hand), not a pytest suite; there is no CI.
- **No PowerShell-compatible orchestration script** (review item Y) — the README documents
  commands to run by hand, one at a time.
- **This session cannot push to GitHub** (`git push` is denied by the session's proxy: the repo
  is not in this session's authorized push set). The `audit/stage2-handover` branch and its
  commits exist only in this container and must be transferred out manually (see
  `FILE_CHANGELOG.md` and the final chat message for how).
