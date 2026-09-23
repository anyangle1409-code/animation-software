# Current source of truth

This file is the authoritative entry point for the high-detail mesh review workspace.

## Current status

The latest reviewed geometry baseline is **V6 knee seam**. The V6 asset itself was created at commit `b2203cfccd30d6835473ef2e1dee37965da22d02`. Later commits on this branch are preparation/automation only unless a newer review file explicitly says otherwise.

The canonical runtime skeleton is now the confirmed **55-bone structural baseline** at `c2372c16ad4b7a0763a4cfdf9a0da6a23c3524f2`. Read `RIG_55_BASELINE.md`.

Current candidate assets:
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam_BARE.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.blend`

Use `CANDIDATE_BASELINE_MANIFEST.json` for exact hashes and machine-readable state.

## Instruction precedence

When instructions disagree, use this order:

1. `CURRENT_STATE.md`
2. `RIG_55_BASELINE.md`
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

- final hand weights until the palm-arch/thumb-twist decision is settled
- scapular rhythm and reduced upper-arm elevation limits
- production promotion
- final scapula deform weighting until a candidate character asset explicitly contains/uses scapula deform influences and neutral equivalence is re-proven

The runtime rig is confirmed; the current production GLB itself was not changed by `c2372c16ad4b7a0763a4cfdf9a0da6a23c3524f2`, so V6 remains a valid geometry source and does not need an immediate rebind.

## Validation baseline

New candidates must be validated against the confirmed 55-bone source commit, not only the historical 53-bone validation snapshot. `RESUME_WORK.bat` prepares an isolated `validation_55` tree from `c2372c16ad4b7a0763a4cfdf9a0da6a23c3524f2` without merging source changes into this mesh-review branch.

## Fast path on the laptop

From `HIGH_DETAIL_MESH_WORK`:

```text
RESUME_WORK.bat
START_CANDIDATE.bat <version>
```

After editing the generated Blend file and exporting the dressed GLB:

```text
FINISH_CANDIDATE.bat <version> <task>
```

Use `knee`, `hand`, or `material` for `<task>`. That command runs structural/runtime gates against rig v2, the task-specific audit, the visual review pack, and candidate checkpointing.

## Do not

Do not overwrite V6, modify production assets, change exercise mechanics to accommodate a mesh, loosen guards to make a candidate pass, enable scapular rhythm during mesh-only work, or infer that unresolved hand/forearm architecture decisions were settled by the scapula commit.
