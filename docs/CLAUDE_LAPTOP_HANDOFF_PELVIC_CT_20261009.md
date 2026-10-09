# Claude laptop handoff — pelvic CT candidate evidence

Date: 2026-10-09

## Safe checkpoint

- Repository: `anyangle1409-code/animation-software`
- Draft PR: `#15`
- PR branch: `codex/independent-pelvis-stl-intake-20261009`
- Isolated recovery/development branch:
  `codex/pelvic-ct-identification-segmentation-20261009`
- Verified code checkpoint: `479f31c538a4bc1d2e02602a6c276c2397868b13`
- Claude source branch remains preserved at
  `claude/pelvis-ct-blender-review-20261009` (`9d57a01b`).

Both Codex branches pointed to `479f31c5` when this handoff was written. Fetch
and verify the live heads before starting; do not force-push or rewrite Claude,
Work, or PR history.

## What is implemented

The branch contains Claude's source-pin, display-geometry, Blender scene,
landmark-register, skeleton comparison, documentation, and CI work, plus:

1. source-bound candidate anatomical review packets;
2. bounded manually authored sparse-mask validation for one physical 3 mm
   triplet at a time;
3. 6-neighbour component counts and scanner-RAS sample-centre bounds;
4. mask-supported ASIS, pubic-region, S1/endplate, acetabular, and
   femoral-head candidate landmark validation;
5. an end-to-end privacy-safe CLI and offline CI coverage;
6. Windows path/UTF-8/symlink portability fixes.

No canonical geometry changed. Source skeleton geometry still governs. The
current six frames do not provide a complete pelvic volume, verified HU, a
verified bone surface, a scanner-to-Home-Gym-PT transform, or independently
verified anatomical landmarks.

## Verified state

- 102/102 focused NLM CT workflow tests pass locally.
- All 21 `review-intake` suites pass locally (329 tests).
- Blender 5.2.1 LTS executed the real scene script headlessly with `--skip-ct`:
  pre-existing objects unchanged, skeleton geometry unmodified, no world
  transform, and no canonical promotion.
- Isolated-branch full workflow run `37950922333`: success.
- PR #15 runs `37951159582`, `37951159624`, and `37951159663`: success.
  These include the live NLM pin jobs for all six original PNG/header pairs.

## Start on the laptop

```text
git fetch origin --prune
git switch codex/independent-pelvis-stl-intake-20261009
git pull --ff-only
git rev-parse HEAD
python -m unittest discover -s scripts -p "test_nlm_*ct*.py" -v
python -m unittest discover -s scripts -p "test_ct_*.py" -v
```

Expected HEAD before later commits: `479f31c5`. The focused suites should pass;
the Windows symlink test may skip if the account lacks symlink privilege.

Read first:

- `docs/NLM_PELVIC_CT_IDENTIFICATION_SEGMENTATION_WORKFLOW_20261009.md`
- `docs/CLAUDE_PELVIS_CT_BLENDER_REVIEW_20261009.md`
- `ORIGINAL_V1_WORK/anatomy/audit/claude_pelvis_ct_review_20261009/README.md`

## Useful Blender work now

The useful Blender task is evidence review, not mesh sculpting. Keep the six
original PNG files and scanner headers in a private directory outside the Git
checkout. Validate them against the committed pins and build private windowed
display copies. Then run the Blender review scene with the private CT and cache
directories, a new privacy-safe JSON report, and optionally a new private
`.blend` file. Never pack CT images into the `.blend`.

Use the scene to:

- confirm image laterality from an unambiguous source cue before assigning
  left/right;
- record exact source ID, row, column, candidate structure, confidence,
  reviewer ID, and independent HTTPS anatomical citation;
- inspect disagreement between the source-governing skeleton and CT evidence;
- author sparse mask runs manually only where the candidate structure is
  actually visible.

Do not use Blender display axes as Home Gym PT world coordinates. Do not create
or promote a canonical pelvis mesh from the two short windows.

## Next evidence sequence

1. Perform the actual private six-frame visual review; all current repository
   landmarks remain unverified until that happens.
2. Create a source-bound review packet and validate it with
   `nlm_ct_anatomical_review.py`.
3. For a single reviewed triplet and a single reviewed structure, create manual
   sparse runs and validate them with `nlm_ct_candidate_segmentation.py`.
4. Add only mask-supported candidate landmarks through
   `nlm_ct_landmark_validation.py`.
5. Run `nlm_ct_pelvis_workflow.py` to generate an exclusive-create sanitized
   report. Confirm `status` is `CANDIDATE_EVIDENCE_ONLY` and promotions are zero.
6. Acquire and independently pin additional contiguous original CT coverage.
   The current 9 mm windows and 39 mm gap cannot validate a complete pelvis,
   both hip centres, S1 endplate, pubic region, and bilateral ASIS/acetabula.
7. Obtain independent anatomical and surface validation before drafting any
   separate canonical-change proposal.

Claude/Codex agreement is review evidence only. It is not independent
anatomical evidence and must never be treated as canonical approval.
