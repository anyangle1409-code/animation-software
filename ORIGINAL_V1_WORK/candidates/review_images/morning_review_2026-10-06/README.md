# Morning review: 2026-10-06

**Branch:** `codex/whole-body-deformation-recovery-20261004`. The pack sits on top of HEAD `36d6b036cf1129ca011e8f4407d93c29eeaea6fc`. Model work was stopped at that commit, and no model, weight, rig, READY or validation file was changed afterwards.

## Current strongest model: r98 (unchanged)

| | |
|---|---|
| Candidate | `ORIGINAL_V1_WORK/candidates/r98/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r98.blend` |
| SHA-256 | `89e98cc74cc7dfd17f6d5a0991a9f0f6954e8de4d99ea3d3b30be2ec617b2ce0` |
| Candidate commit | `61f48118e834f4fc188ec715269a646feffd663a` |
| Status | GPT validation: **FAIL / not production-approved**. Weights-only, no correctives. |
| Details | `ORIGINAL_V1_WORK/candidates/r98/README.md` |

Every image in this pack is a weights-only render of that exact r98 file, copied from its committed evidence. Nothing was re-rendered.

### What is strongest about r98

- **Collisions:** 56-pose matrix collisions are 708, against 1536 for r97 and 1931 for r95.
- **Repository pose test:** no self-intersection regression against r95 or r97:
  - press_top 58 → 0;
  - squat 82 → 76;
  - pull-up hang 0 → 0;
  - pull-up top 92 → 92.
- **Shoulder mechanics** (from r97): the scapula pivots at the AC joint, so the shoulder joint no longer slides 9.3 cm, and half-swing helpers remove the linear-blend chord collapse.
- **Rest armpit:** the slit is opened and its apex rounded, which is invisible at rest and removes most low/mid-elevation armpit collisions.
- **Weights:** non-declared weights are identical to r95, symmetry is within 0.3 mm, and every vertex has at most 4 influences.

### What remains visibly wrong

See `sheets/03_r98_issues_to_review_tomorrow.jpg`.

- **SH-V02:** overhead (flexion and abduction 150–170°, press top, pull-up hang), a flat membrane spans armpit to chest, with a crease line.
- **SH-V01:** the rear deltoid dents or thins overhead.
- **SH-V05:** back creases beside the scapula at 150° and above.
- **SH-M03:** collisions are not zero (708). The heaviest are around 146 pairs at 60° flexion with external rotation, then posterior armpit and the top of the shoulder overhead.
- **SH-M09 / SH-V09:**
  - overhead stretched-edge counts are above r95 (press_top 853 / 1104 / 1134 for r95 / r97 / r98);
  - the maximum edge ratio is 4.33 (flexion 170 with internal rotation).

## Sheets

| Sheet | Contents |
|---|---|
| [`sheets/01_r98_current_strongest_pose_overview.jpg`](sheets/01_r98_current_strongest_pose_overview.jpg) | Clean front three-quarter overview: rest, abduction 90/150/170, flexion 90/150/170, horizontal adduction, press bottom/top, pull-up hang/top, squat bottom |
| [`sheets/02_r98_overhead_all_views.jpg`](sheets/02_r98_overhead_all_views.jpg) | Flexion 170, abduction 150, press top and pull-up hang, each in all eight views: front, side, rear, front 3/4, rear 3/4, close front, close axilla, close rear |
| [`sheets/03_r98_issues_to_review_tomorrow.jpg`](sheets/03_r98_issues_to_review_tomorrow.jpg) | Labelled close-ups of each open defect, with gate IDs |
| [`sheets/04_progression_r98_vs_rejected_r99_r100_r101.jpg`](sheets/04_progression_r98_vs_rejected_r99_r100_r101.jpg) | r98 against the rejected r99-P, r100-Am and r101-Acap, in close front, axilla and rear views at flexion 170, abduction 150 and press top |

## Individual renders

**`renders/r98_matrix/`** holds 107 JPEGs named `<pose>__<view>.jpg`.
- **Poses:**
  - `abduction_000_neutral` (rest);
  - `abduction_090/150/170_neutral`;
  - `flexion_090/150/170_neutral`;
  - `flexion_170_internal` (close views only);
  - `press_bottom_like`, `press_top_like`;
  - `pullup_hang_like`, `pullup_top_like`;
  - `horizontal_adduction_90`;
  - `flexion_060_external`.
- **Views:** `front`, `side`, `rear`, `front_three_quarter`, `rear_three_quarter`, `close_front`, `close_axilla`, `close_rear`.

**`renders/r98_repo_poses/`** holds the 15-pose repository test renders for squat_bottom, press_bottom, press_top, press_top_rhythm, pullup_hang, pullup_top and neutral.

**The full 56-pose r98 matrix** (448 images plus `matrix_report.json`) is in `ORIGINAL_V1_WORK/candidates/review_images/r98_axillary_weights_only_matrix/`. All 15 repository-pose renders and the comparison table are in `ORIGINAL_V1_WORK/candidates/repair_checks/r98_pose_test_weights_only/`.

## r99–r102: rejected diagnostic experiments, NOT candidates

None of these produced a candidate or a READY record. Each was declared before editing and built from a copy of r98, and r98 was never modified.

| Revision | Idea | Why it was rejected | Evidence |
|---|---|---|---|
| r99 | Straight-line stretch-bone fold helpers | Worse squat/press/pull-up collisions, a new chest crease, more overhead stretch | `ORIGINAL_V1_WORK/candidates/repair_checks/r99_fold_helper_screening/` |
| r100 | 3–6 mm rest fold ridges | The ridge is kept under pose (96–99%) but is negligible against the ~10 cm membrane; collisions rose | `ORIGINAL_V1_WORK/candidates/repair_checks/r100_fold_ridge_screening/` |
| r101 | Elevation-driven fold-volume helpers, half-helper weight only | Visually inert at 30 mm; at the 40 mm cap a sharper ridge or flap and more collisions. Measured cause: about two-thirds of the membrane's weight is torso and humerus | `ORIGINAL_V1_WORK/candidates/repair_checks/r101_fold_volume_screening/` |
| r102 | Same helper, taking torso and humerus weight too | Base motion drags the chest even at a 0.25 share (10 mm at 30° abduction, 16 mm with the arm rotating at the side, 43 mm in horizontal adduction). Rejected on that measurement, **before any rendering; there is no r102 image** | `ORIGINAL_V1_WORK/candidates/repair_checks/r102_fold_weight_source_screening/` |

**Proposed next step** (from the r102 blocker; needs a new declaration): per-source offset twins. Each would be a driven offset bone parented to its own weight source, so that base motion stays exactly r98's while the fold band gets outward volume overhead.
