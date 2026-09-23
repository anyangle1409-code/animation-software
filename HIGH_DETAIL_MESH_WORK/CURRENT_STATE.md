# Current source of truth

This file is the authoritative entry point for the high-detail mesh review workspace.

## Current status

The latest accepted knee **topology** is V7. V6 remains the preserved earlier geometry baseline; its asset was created at commit `b2203cfccd30d6835473ef2e1dee37965da22d02`.

V8 knee anatomy is a new, validated **review candidate** built from V7. Read `REVIEW_V8_KNEE_ANATOMY.md` and the matched-camera V7/V8 deepest-squat knee comparison. Stop for this review before Phase B hand geometry.

The canonical hierarchy is frozen at **63 bones** at `19ca602ca2f2a821237dcf5b1b50c7906d86b0fe` (`hgpt_canonical_v3`). The current validated runtime/retarget source is `614033b256d869230ea273522620467401b0bc71`, which fixes mirrored-character hand roll without changing the frozen hierarchy. Read `RIG_63_FREEZE.md`.

Current candidate assets:
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam_BARE.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.blend`

Use `CANDIDATE_BASELINE_MANIFEST.json` for exact hashes and machine-readable state.

## Instruction precedence

1. `CURRENT_STATE.md`
2. `RIG_63_FREEZE.md`
3. `WORK_START_HERE.md`
4. `LAPTOP_CONTINUATION_HANDOFF.md`
5. `FINAL_RIG_INTAKE.md`
6. latest numbered review, currently `REVIEW_V6_KNEE_SEAM.md`
7. `PROGRESS.md`
8. older review/reproduction notes as historical evidence only

## Ready work

Work may continue autonomously on:
- true medial-knee retopology and anatomical knee shaping
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
