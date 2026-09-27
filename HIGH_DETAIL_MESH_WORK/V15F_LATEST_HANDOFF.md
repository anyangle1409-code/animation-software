# V15f latest interruption handoff

Generated automatically from local artifacts.

## Repository
- branch: work/v15-deep-hand-rebuild-prep-20260925
- HEAD: aaed0df109fcf4ccbf3162f4719f5fb5465d0bf5
- working tree dirty: yes

## Candidate
- Blend: HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15f_deep_hand_rebuild.blend — present
- checkpoints: 12
- latest checkpoint: checkpoints\v15_manual\v15f_deep_hand_rebuild_checkpoint_012.blend

## Incremental gates
- ring_L proof: PASS
- ring_L visual: PASS — Route B upstream topology rebuild visibly cleans the middle/proximal ring_L shaft and reduces triangular banding in side and oblique views while retaining joint volume; no new pinch or razor crease.
- ring_L: missing
- ring_R: PASS
- pinky_L: PASS
- pinky_R: PASS
- Stage A: PASS
- Stage A visual: PASS — Matched ring and pinky views show cleaner continuous shafts, reduced triangular banding and removal of severe pinky folds. Bilateral volume and silhouettes remain consistent with no new pinching or razor creases.

## Stage B
- index_L: numeric PASS; visual PASS — Matched four-view review shows a modest but consistent reduction in shaft segmentation without new pinching, crease, or volume loss; accepted as the left-index Stage-B increment.
- index_R: numeric PASS; visual PASS — Matched four-view review shows the same modest bilateral shaft cleanup as index-left, with no new pinching, razor crease, asymmetrical volume change, or regression to accepted digits.
- middle_L: numeric PASS; visual PASS — Matched views show a clear reduction in middle-finger shaft banding and a smoother longitudinal silhouette, with joint volume retained and no new pinch or crease.
- middle_R: numeric PASS; visual missing

## Latest Blender audit
- general invariant pass: True
- total >100° digit folds: 3 -> 0
- protected max move: 0.0 mm
- non-digit max move: 0.0 mm
- original digit weight rows changed: 0
- original source-vertex movement by digit:
  - index_L: max 0.697419 mm; moved 184
  - index_R: max 0.697419 mm; moved 184
  - middle_L: max 0.678787 mm; moved 216
  - middle_R: max 0.678739 mm; moved 216
  - pinky_L: max 0.763573 mm; moved 188
  - pinky_R: max 0.763574 mm; moved 188
  - ring_L: max 0.748885 mm; moved 173
  - ring_R: max 0.653267 mm; moved 173

## Shape-profile diagnostics
- pinky_L: jump_p90=0.2022; second_diff_p90=0.2335; Δjump vs V13e=-0.0032
- pinky_R: jump_p90=0.2022; second_diff_p90=0.2335; Δjump vs V13e=-0.0032
- ring_L: jump_p90=0.1593; second_diff_p90=0.0967; Δjump vs V13e=+0.0109
- ring_R: jump_p90=0.1527; second_diff_p90=0.0971; Δjump vs V13e=+0.0043
- middle_L: jump_p90=0.1224; second_diff_p90=0.1745; Δjump vs V13e=-0.0030
- middle_R: jump_p90=0.1224; second_diff_p90=0.1741; Δjump vs V13e=-0.0030
- index_R: jump_p90=0.1210; second_diff_p90=0.0616; Δjump vs V13e=-0.0011
- index_L: jump_p90=0.1206; second_diff_p90=0.0616; Δjump vs V13e=-0.0011
- advisory only: lower radius-profile jump/second-difference usually indicates smoother diameter continuity; final anatomy still needs visual review.

## Next action
GENERATE_V15F_STAGE_B_VISUAL.bat middle_R

Stage-B middle_R numeric gate passes; visual board is missing.

## Resume references
- WORK_RESUME_AFTER_LIMIT.md
- V15F_LOCAL_PATCH_PLAN.md
- V15F_FAILURE_RECOVERY.md

Do not promote geometry or begin Phase C from this handoff alone.
