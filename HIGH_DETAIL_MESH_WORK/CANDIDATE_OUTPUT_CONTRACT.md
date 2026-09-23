# Candidate output contract

Use one version suffix consistently, for example `v7_knee_retopology`.

## Start

```text
START_CANDIDATE.bat v7_knee_retopology
```

This creates:

`HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v7_knee_retopology.blend`

from reviewed V6 without overwriting V6.

## Before finishing

Save the edited Blender file under the same version and export the dressed GLB as:

`HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v7_knee_retopology.glb`

The finish workflow will create the corresponding bare GLB automatically if it is missing.

## Finish

```text
FINISH_CANDIDATE.bat v7_knee_retopology knee
```

Task must be one of:
- `knee`
- `hand`
- `material`

The finish workflow:
1. creates the bare GLB if needed
2. runs the fast structural check
3. runs the focused runtime guards
4. runs the sampled five-exercise comparison
5. runs the task-specific hand/knee audit when applicable
6. renders the visual review pack
7. writes hashes/checkpoint metadata and a review-note scaffold

A successful finish is still **review-only**, not production approval.
