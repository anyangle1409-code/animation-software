# Current source of truth

This file is the authoritative entry point for the high-detail mesh review workspace.

## Current status

The latest reviewed geometry baseline is **V6 knee seam**. The V6 asset itself was created at commit `b2203cfccd30d6835473ef2e1dee37965da22d02`.

The canonical runtime skeleton is now the frozen **63-bone canonical skeleton** at `19ca602ca2f2a821237dcf5b1b50c7906d86b0fe` (`hgpt_canonical_v3`). Read `RIG_63_FREEZE.md`.

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

New candidates must be validated against the frozen 63-bone source commit. `RESUME_WORK.bat` prepares an isolated `validation_63` tree from `19ca602` without merging source changes into this mesh-review branch.

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

Do not overwrite V6, modify production assets, change exercise mechanics to accommodate a mesh, loosen guards to make a candidate pass, enable scapular rhythm during mesh-only work, or change the frozen canonical hierarchy. Remaining hand-roll, palm-export and mannequin-hand issues belong outside the skeleton.
