# Current source of truth

This file is the authoritative entry point for the high-detail mesh review workspace.

## Current status

The latest reviewed geometry baseline is **V6 knee seam**. The V6 asset itself was created at commit `b2203cfccd30d6835473ef2e1dee37965da22d02`. Later commits on this branch are preparation/automation only unless a newer review file explicitly says otherwise.

Current candidate assets:
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam_BARE.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.blend`

Use `CANDIDATE_BASELINE_MANIFEST.json` for exact hashes and machine-readable state.

## Instruction precedence

When instructions disagree, use this order:

1. `CURRENT_STATE.md`
2. `WORK_START_HERE.md`
3. `LAPTOP_CONTINUATION_HANDOFF.md`
4. `FINAL_RIG_INTAKE.md`
5. latest numbered review, currently `REVIEW_V6_KNEE_SEAM.md`
6. `PROGRESS.md`
7. older review/reproduction notes as historical evidence only

`CLAUDE_HANDOFF.md`, `DELIVERY.md`, `REVIEW.md`, and older V2/V3/V4/V5 notes describe earlier checkpoints. Do not treat an older statement such as "no bare candidate", "first candidate", or "pending guard" as current.

## Ready work

Work may continue autonomously on:
- true medial-knee retopology and anatomical knee shaping
- realistic hand/finger/thumb/palm/wrist geometry while preserving the floor-contact guard
- skin/material refinement
- candidate-only topology and geometry diagnostics
- review renders and validation

## Blocked work

Until the final canonical rig is confirmed:
- final shoulder/chest/back/armpit skin weighting
- final scapular deformation tuning
- production promotion

The canonical rig is being handled separately on `chatgpt/absolute-retarget-imports`. Do not merge this review branch into it merely to obtain rig changes.

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

Use `knee`, `hand`, or `material` for `<task>`. That command runs structural/runtime gates, the task-specific audit, the visual review pack, and candidate checkpointing.

## Do not

Do not overwrite V6, modify production assets, change exercise mechanics to accommodate a mesh, loosen guards to make a candidate pass, or finalise shoulder weights against the obsolete pre-scapula hierarchy.
