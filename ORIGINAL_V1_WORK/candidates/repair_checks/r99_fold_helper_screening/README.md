# r99 axillary fold soft-tissue helpers: BLOCKED (no candidate published)

Declaration: `repair_preparation/r99_axillary_fold_helpers_declared` (commit d2683b76, before any edit). Prototypes are built from a copy of r98 by `scripts/r99/fold99.py`; r98 is unchanged. Everything here is weights-only, with correctives at 0.

## What was built

Each side gets two deforming fold bones:
- **`axfold_ant_<s>`:** pectoral fold, parented to spine_03.
- **`axfold_post_<s>`:** latissimus/teres fold, parented to the scapula.

Each bone STRETCH_TOs a non-deforming insertion target that is a child of the humerus, or of the half-swing helper in some variants. Each also gets a local, mirror-exact band weight transfer, taken only from declared bones, with at most 4 influences.

## Kinematics

`fold_kinematics_B_upperarm_targets.json` covers 0–170° of abduction and flexion with internal, neutral and external rotation. Both bones move smoothly and monotonically, with no flips or double transforms. Both over-stretch: the anterior bone reaches 2.3× its rest length and the posterior 1.8× at 170°.

## Subset matrix

15 poses: 10 key overhead poses plus 5 low/mid poses (`screening_subset_results.json`).

| Variant | Collisions | Max edge ratio |
|---|---:|---:|
| r98 | 346 | 4.33 |
| anterior only | 436 | 4.33 |
| posterior only (P) | **196** | 5.19 |
| both | 362 | 5.19 |
| posterior, half-swing target | 226 | 5.62 |
| anterior (medial origin), half-swing target | 290 | 4.33 |
| both, half-swing targets | 238 | 5.62 |
| P with diffused band (P3) | 188 | 5.64 |
| P light (P4, effective peak 0.21) | 282 | 4.33 |
| P wide (P5) | 200 | 5.70 |

## Repository pose test against r98

Self-intersection pairs, r98 → prototype (`pose_test_vs_r98.json`):

| Pose | r98 | P | P4 |
|---|---:|---:|---:|
| press_top | 0 | 16 | 4 |
| press_top_rhythm | 0 | 19 | 4 |
| squat_bottom | 76 | **114** | **94** |
| pullup_hang | 0 | 11 | 4 |
| pullup_hang_rhythm | 0 | 10 | 4 |
| pullup_top | 92 | 92 | 92 |
| press_bottom | 80 | 80 | 80 |

## Visual check

`images/r98_vs_P_vs_P4_overhead_and_flexion60_closeups.jpg` shows each pose as an r98 / P / P4 triplet.
- The overhead membrane (SH-V02), rear-deltoid dent (SH-V01) and back creases (SH-V05) are **not visibly improved**.
- P adds a new vertical crease line on the lateral chest wall in the overhead armpit views, at the posterior band edge. P4 shows a weaker version.

## Verdict

No prototype meets the r99 criteria:
- it must not regress against r98 in press, squat or pull-up collisions;
- it must substantially reduce matrix collisions without worsening overhead stretch;
- it must visibly improve the folds.

The posterior fold removes many low/mid collisions, but it does so by moving the band with a stretching bone. That produces overhead stretch peaks and a new crease, and it regresses squat. r98 remains the strongest model; no r99 candidate or READY record is published.

## Cause and next step

- The fold band is still a linear blend. A stretch-bone helper moves the band vertices along a chord between trunk and arm, which is the same mechanism that produces the membrane. It only moves where the chord lies.
- The visible defects need **volume**, not repositioning: overhead, the folds must bulge outward as rounded bands, and the rear deltoid must keep its mass.
- Two directions are left:
  1. A rotation-driven fold-volume mechanism, for example fold bones with a declared scale or offset driven by elevation, so the fold bulges along its normal instead of following a chord.
  2. Declared rest-geometry support for the fold ridges, such as building the ridge into the rest shape so that the blend has volume to preserve.

  Both need a new declaration. Correctives remain unauthorised until the foundation passes.
