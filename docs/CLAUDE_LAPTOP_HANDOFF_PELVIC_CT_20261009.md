# Claude laptop handoff — pelvic CT candidate evidence

Date: 2026-10-09

## Updated continuation checkpoint — 2026-10-10

This section supersedes the older six-frame checkpoint below. Fetch both live
branches before starting. The verified development and PR head is
`73197ca9f715c83d5f4eca3b9f8728d4f1bb0848`; 362 intake tests passed locally
and all 15 GitHub checks succeeded. Claude's branch remains at `9d57a01b`.

The source bundle now contains 72 slices in two acquisition groups. All
18,874,368 PNG samples matched their official decompressed GE source samples
exactly. All 72 scanner headers report the same -1024 addend. Read
`nlm_pelvic_ct_full_series_hu_calibration_20261009.json` in the anatomy audit
directory: `HU = PNG_stored_value - 1024` is verified for this bundle. The
stored threshold 1200 corresponds to 176 HU, but its anatomical suitability
has not been established. The private Blender occupancy scene has 8 and 3
components by group; no component was automatically removed.

Other preserved Work branches contain additional evidence. Review their live
heads and checks before integrating; they have not been merged into this head:

- Orientation: `codex/ct-72-frame-orientation-preflight-20261009`,
  last inspected `bf02226b`.
- Threshold sensitivity: `codex/ct-stored-scalar-threshold-sensitivity-20261009`,
  last inspected `20c3b2bd`.
- Landmark coverage: `codex/ct-anatomical-landmark-coverage-audit-20261009`,
  last inspected `3614dd9f`.

These branches already audit scanner row/column orientation, threshold
sensitivity, and the distinction between ten provisional region observations
and seven required physical landmarks. Their earlier calibration questions
are answered by the newer direct GE-to-PNG comparison above. Keep their
pixel-centre convention and anatomical-identity limitations in force.

Claude's useful next Blender task is independent source review of bilateral
bony ASIS, bilateral pubic tubercles, S1 superior endplate centre, and bilateral
femoral-head articular centres. Review multiple source planes, retain exact
source hashes and pixel support, record reviewer identity and uncertainty, and
leave unsupported features absent. Region labels alone do not establish these
landmarks. Preserve acquisition boundaries and the unmodified source skeleton.

Private CT and GE bytes and existing Blender outputs are on the desktop,
outside Git; a laptop checkout does not contain them. Obtain source files from
the recorded official NLM URLs and validate their pins before building a
laptop scene. Never commit source bytes or pack the CT images into Blender.
Independent anatomy review, verified surfaces, scanner-to-HGPT registration,
and evidence beyond this single donor remain outstanding promotion gates.

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

## Boundary-extension checkpoint — 2026-10-10

The CT development branch is `codex/pelvic-ct-identification-segmentation-20261009`, based at `cb2a68b8a0c24d0ea1ff7a30a69c75d9bb4ed054` before this checkpoint. The draft intake PR is #15 and still has no anatomical approval. Ten additional official NLM PNG/header pairs were downloaded into the private laptop source cache (outside Git): six superior slices `cvm1716f` through `cvm1731f` at S=-324 through -339 mm, plus four inferior slices `cvm1948f` through `cvm1957f` at S=-556 through -565 mm. All are 512x512, 3 mm apart, with parsed scanner headers declaring 0.898438 mm XY spacing, 3 mm thickness, +Z normal, and HU addend -1024.

The new candidate bundle `ORIGINAL_V1_WORK/anatomy/audit/nlm_pelvic_ct_boundary_extension_candidate_bundle_20261010.json` retains both original acquisition groups and their 2 mm slab overlap; it has 82 source rows total (43 + 39), not a flattened uniform volume. The old 72-slice calibration packet and base bundle remain byte-for-byte unchanged. Official NLM raw `.Z` counterparts for all ten additions were acquired privately, decompressed with GNU gzip 1.14, and compared sample-by-sample against their pinned PNGs: 2,621,440/2,621,440 identical, zero differences, maximum difference zero. All 10 paired scanner headers independently declare -1024. The combined 82-slice calibrated count is 21,495,808 samples under `HU = PNG_stored_value - 1024`; extension packet SHA-256 is `497a0349b579e193ff0dcc65dfa2c3e2696a3d60a233c894ccdf89a33b340dad`. Raw `.Z` files and all image/header bytes remain outside Git. This establishes numeric calibration only—not anatomy, segmentation, landmarks, or canonical geometry.

Focused validation: `python -B -m unittest scripts.test_pelvic_ct_series_manifest -v` — 20 tests passed, including the new per-frame PNG/header/raw hash binding and combined sample count. The indiscriminate `unittest discover -s scripts -p 'test_*.py'` command is not a valid branch gate here: it ran 1,215 cross-project tests and failed 27 / errored 382 due to unrelated frozen-evidence CRLF/autocrlf assumptions and missing reconstruction fixtures. Do not summarize that result as a CT regression. For the prior candidate commit `cfbcf771fe801fb9772fa979ff46b35f9b551b27`, PR #15 CI runs 38078716914 (pelvis review/test), 38078716953 (mesh intake), and 38078716938 (trunk source comparisons) all completed successfully. This newer raw-calibration checkpoint must receive fresh CI. The pelvis workflow is a stdlib evidence/test gate, not a native-Blender review of the ten added frames.

**Next executable action:** create an isolated, source-pinned Blender visual review for the ten new boundary frames, building header/orientation tests first. It must preserve the two source groups, avoid skeleton registration and laterality guesses, keep display assets and any `.blend` outside Git, and label the output as diagnostic—not segmentation. Then inspect image coverage before deciding whether the next evidence should be more source images, candidate masks, or independent review. Never infer anatomy or source-to-rig fit from calibration or slice count alone.
