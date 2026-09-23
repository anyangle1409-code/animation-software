# Candidate output contract

Use one version suffix consistently, for example `v7_knee_retopology`.

## Start

```text
START_CANDIDATE.bat v7_knee_retopology
```

This creates a fresh editable Blend from reviewed V6 without overwriting V6.

## Before finishing

Save the edited Blender file under the same version and export the dressed GLB as:

`HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_<version>.glb`

The finish workflow creates the matching bare GLB if it is missing.

## Finish

```text
FINISH_CANDIDATE.bat <version> <task>
```

Task:
- `knee`
- `hand`
- `material`
- `shoulder`

The finish workflow:
1. creates the bare GLB if needed
2. runs the fast structural check
3. validates against exact rig source c2372c1 / hgpt_canonical_v2
4. runs the focused runtime guards
5. runs the current all-exercise comparison
6. runs the task-specific hand/knee audit when applicable
7. renders the visual review pack; shoulder runs include overhead detail views
8. writes hashes/checkpoint metadata and a review-note scaffold

A successful finish is still **review-only**, not production approval.
