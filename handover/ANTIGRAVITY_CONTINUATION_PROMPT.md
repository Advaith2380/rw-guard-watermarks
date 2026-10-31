# Continuation prompt for the next agent (Google Antigravity or otherwise)

Paste this whole file as your first message to the next agent, in a session that has this
repository checked out (with the `handover/` directory present) on a machine with Python,
PyTorch, a GPU, and the COCO/PACS dataset downloadable.

---

You are continuing work on **RW-Guard**, a forensic-detection research project for sequential
image re-watermarking attacks. A previous Claude Code session completed a read-only audit and
left a handover package in this repository, at `handover/`. Do the following, in order, before
making any change:

1. Read `handover/README.md`.
2. Read `handover/CURRENT_STATE.md`.
3. Read `handover/REPOSITORY_INVENTORY.md`.
4. Read `handover/RESOURCE_AUDIT.md`.
5. Read `handover/REVIEW_TRACEABILITY.md`.
6. Read `handover/IMPLEMENTATION_PLAN.md`.
7. Read `handover/FILE_CHANGELOG.md`.
8. Read `handover/TEST_STATUS.md`.
9. Read `handover/EXPERIMENT_READINESS.md`.
10. Inspect `handover/state.json`.
11. Run `git status` and `git log -5` yourself, right now, in this actual repository. If what
    you see disagrees with what the handover files claim (a different commit, uncommitted
    changes, a different branch), **trust the live repository**, say so explicitly, and treat
    the handover files as possibly stale before doing anything else.
12. Verify that the files and commands the handover package names still exist as described
    (e.g. `ls rewm/`, check `train.py --help` actually has the flags `REPOSITORY_INVENTORY.md`
    claims). Do not assume; check.
13. Continue from the **last verified incomplete task** in `handover/IMPLEMENTATION_PLAN.md` —
    its recommended order (given limited time) is: Task 5 (bootstrap CIs) → Task 2 (shortcut
    baseline) → Task 3 (attack-outcome labelling) → Task 9 (StegaStamp full run) → Tasks 7/8
    (manifest capture, scheme-set versioning) → Task 6 (automated tests) → Tasks 4/10 (matched
    controls, multi-restart adversarial) → Task 12 (orchestration script) → Task 11
    (SRNet/ZhuNet/SiaStegNet, do last, flagged high-complexity).
14. **Do not redo anything already marked `TESTED_PASS` in `handover/REVIEW_TRACEABILITY.md`**
    unless your own verification in step 12 shows it's no longer true.
15. Before extending any modified component, run the smallest relevant test for it (a pytest
    file if one now exists from Task 6, or the manual smoke sequence in Task 1 otherwise).
16. After any further change, update: `handover/FILE_CHANGELOG.md`, `handover/TEST_STATUS.md`,
    `handover/CURRENT_STATE.md`, and `handover/state.json`. Keep them accurate — a stale
    handover file is worse than no handover file, because it will mislead the agent after you.
17. **Never delete or overwrite existing checkpoints, datasets, or result files** without
    explicit authorization from the user. New runs go in new, clearly-named subdirectories
    (e.g. `runs/shortcut_baseline_v1/`, not overwriting `runs/baseline/`).
18. **Never claim a result without having actually executed and inspected it.** If you reason
    from source code alone, say so explicitly and mark the corresponding
    `REVIEW_TRACEABILITY.md` row as `IMPLEMENTED_NOT_TESTED`, not `TESTED_PASS`.

## Exact next action

Start with `handover/IMPLEMENTATION_PLAN.md` **Task 1** (readiness smoke test): install
PyTorch, run `download_data.py --n-coco 200 --skip-pacs` for a small fast subset, then
`sanity_check.py`, a 1-epoch `train.py` smoke run, and `evaluate.py` on it. Confirm the pipeline
still works end-to-end on your machine before touching any production code. Then proceed to
Task 5 (bootstrap CIs — cheapest, highest-value, no GPU needed) as the first real implementation
task.

## Known blockers inherited from the prior session

- The prior session had **no PyTorch, no GPU, and no dataset**, so nothing beyond static code
  reading was verified there. Everything in `REVIEW_TRACEABILITY.md` marked `TESTED_PASS` is
  based on the **manuscript's reported results and prior-session logs**, not re-verified in that
  audit session — re-verify anything you're about to build on top of, if you have doubts.
- The prior session **could not push to GitHub** (proxy denied push access to this specific
  repository). If you also cannot push, package your changes as files for the user to apply
  manually, exactly as the prior session did, and say so plainly rather than claiming a push
  succeeded when it didn't.
- The manuscript (`report.tex`/`.docx`) is **out of scope** — do not modify it from this
  continuation; it lives outside this GitHub repository by the user's standing instruction.
