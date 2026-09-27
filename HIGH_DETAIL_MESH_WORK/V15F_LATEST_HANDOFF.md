# V15f latest interruption handoff

Generated automatically from local artifacts.

## Repository
- branch: work/v15-deep-hand-rebuild-prep-20260925
- HEAD: 8b8b12843116aa78c8982fd25941e8e6f6fd5f9a
- working tree dirty: yes

## Candidate
- Blend: HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15f_deep_hand_rebuild.blend — present
- checkpoints: 5
- latest checkpoint: checkpoints\v15_manual\v15f_deep_hand_rebuild_checkpoint_005.blend

## Incremental gates
- ring_L proof: PASS
- ring_L visual: PASS — Route B upstream topology rebuild visibly cleans the middle/proximal ring_L shaft and reduces triangular banding in side and oblique views while retaining joint volume; no new pinch or razor crease.
- ring_L: missing
- ring_R: missing
- pinky_L: missing
- pinky_R: missing
- Stage A: missing
- Stage A visual: missing

## Stage B
- index_L: numeric missing; visual missing
- index_R: numeric missing; visual missing
- middle_L: numeric missing; visual missing
- middle_R: numeric missing; visual missing

## Latest Blender audit
- general invariant pass: True
- total >100° digit folds: 3 -> 3
- protected max move: 0.0 mm
- non-digit max move: 0.0 mm
- original digit weight rows changed: 0
- original source-vertex movement by digit:
  - index_L: max 0.000000 mm; moved 0
  - index_R: max 0.000000 mm; moved 0
  - middle_L: max 0.000000 mm; moved 0
  - middle_R: max 0.000000 mm; moved 0
  - pinky_L: max 0.000000 mm; moved 0
  - pinky_R: max 0.000000 mm; moved 0
  - ring_L: max 0.748885 mm; moved 173
  - ring_R: max 0.000000 mm; moved 0

## Shape-profile diagnostics
- pinky_L: jump_p90=0.2054; second_diff_p90=0.2247; Δjump vs V13e=+0.0000
- pinky_R: jump_p90=0.2054; second_diff_p90=0.2247; Δjump vs V13e=+0.0000
- ring_L: jump_p90=0.1593; second_diff_p90=0.0967; Δjump vs V13e=+0.0109
- ring_R: jump_p90=0.1484; second_diff_p90=0.0985; Δjump vs V13e=+0.0000
- middle_L: jump_p90=0.1254; second_diff_p90=0.1771; Δjump vs V13e=+0.0000
- middle_R: jump_p90=0.1254; second_diff_p90=0.1769; Δjump vs V13e=+0.0000
- index_R: jump_p90=0.1221; second_diff_p90=0.0631; Δjump vs V13e=+0.0000
- index_L: jump_p90=0.1217; second_diff_p90=0.0631; Δjump vs V13e=+0.0000
- advisory only: lower radius-profile jump/second-difference usually indicates smoother diameter continuity; final anatomy still needs visual review.

## Next action
Inspect/edit ring_R only, save/checkpoint, then run: AUDIT_V15F_DIGIT.bat ring_R

ring_R gate is missing.

## Resume references
- WORK_RESUME_AFTER_LIMIT.md
- V15F_LOCAL_PATCH_PLAN.md
- V15F_FAILURE_RECOVERY.md

Do not promote geometry or begin Phase C from this handoff alone.
