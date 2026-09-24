# Current source of truth

This file is the authoritative entry point for the high-detail mesh review workspace.

## Current status

The accepted knee **geometry baseline** is V8, built on the accepted V7 connected topology. V6 and V7 remain preserved historical candidates.

The user accepted V8 after reviewing the matched V7/V8 deepest-squat knee comparison. It is the geometry source for Phase B hand anatomy, not a production asset. V9 is preserved as a rejected experimental hand candidate. V10 is superseded. V11 closes the hand seams and caps the fingertips. **V12c palm volume** is the current hand review candidate built directly from V11. It adds a restrained, seam-aware palm interior sculpt and passes the same guards; visual acceptance is pending. Grip refit has not started. See `REVIEW_V12C_HAND_PALM.md`.

The canonical hierarchy is frozen at **63 bones** at `19ca602ca2f2a821237dcf5b1b50c7906d86b0fe` (`hgpt_canonical_v3`). The current validated runtime/retarget source is `614033b256d869230ea273522620467401b0bc71`, which fixes mirrored-character hand roll without changing the frozen hierarchy. Read `RIG_63_FREEZE.md`.

Current candidate assets:
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy_BARE.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.blend`

Separate, unaccepted hand review assets:
- HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v9_hand_geometry_review.glb
- HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v9_hand_geometry_review_BARE.glb
- HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v9_hand_geometry_review.blend

V10 hand anatomy review assets (not accepted):
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v10_hand_retopology.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v10_hand_retopology_BARE.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v10_hand_retopology.blend`

V11 hand cleanup review assets (preserved, not accepted):
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v11_hand_cleanup.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v11_hand_cleanup_BARE.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v11_hand_cleanup.blend`

V12c hand palm review assets (current hand candidate, not accepted):
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v12c_palm_volume.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v12c_palm_volume_BARE.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v12c_palm_volume.blend`

Use `CANDIDATE_BASELINE_MANIFEST.json` for exact hashes and machine-readable state.

## Instruction precedence

1. `CURRENT_STATE.md`
2. `RIG_63_FREEZE.md`
3. `WORK_START_HERE.md`
4. `LAPTOP_CONTINUATION_HANDOFF.md`
5. `FINAL_RIG_INTAKE.md`
6. latest accepted geometry review, currently `REVIEW_V8_KNEE_ANATOMY.md`, followed by V9 rejection, superseded V10, and unaccepted V11/V12c hand reviews
7. `PROGRESS.md`
8. older review/reproduction notes as historical evidence only

## Ready work

Work may continue autonomously on:
- Phase B realistic hand/finger/thumb/palm/wrist **geometry** using V8 as source
- realistic hand/finger/thumb/palm/wrist **geometry** while preserving the floor-contact guard
- skin/material refinement
- shoulder/back/chest/armpit topology and geometry planning against the confirmed scapula structure
- candidate-only topology/geometry diagnostics and review renders

## Still held

- scapular rhythm and reduced upper-arm elevation limits
- production promotion
- final scapula deform weighting until a candidate character asset explicitly contains/uses scapula deform influences and neutral equivalence is re-proven

The canonical hierarchy is now frozen. The production GLB itself was not changed by the freeze commit, so V6 remains a valid geometry source and does not need an immediate rebind.

## Validation baseline

New candidates must be validated against the current v3 runtime source `614033b256d869230ea273522620467401b0bc71`, while the structural freeze remains `19ca602ca2f2a821237dcf5b1b50c7906d86b0fe`. `RESUME_WORK.bat` prepares an isolated `validation_63` tree from the runtime source without merging it into this mesh-review branch.

## Fast path on the laptop

```text
RESUME_WORK.bat
START_CANDIDATE.bat <version>
```

After editing the generated Blend file and exporting the dressed GLB:

```text
FINISH_CANDIDATE.bat <version> <task>
```

Use `knee`, `hand`, `material`, or `shoulder`. The finish workflow runs the frozen v3 structural/runtime gates, task-specific audit where available, visual review pack, and checkpointing.

## Do not

Do not overwrite V6, modify production assets, change exercise mechanics to accommodate a mesh, loosen guards to make a candidate pass, enable scapular rhythm during mesh-only work, or change the frozen canonical hierarchy. The mirrored hand-roll issue is fixed. Remaining grip refit, palm-export and mannequin-hand issues belong outside the skeleton.
