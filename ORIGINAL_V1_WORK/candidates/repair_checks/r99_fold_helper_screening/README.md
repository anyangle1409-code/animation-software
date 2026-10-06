# r99 axillary fold-helper screening (in progress)

Prototypes are built from a copy of r98 with `scripts/r99/fold99.py`. They are weights-only and r98 is never written. The subset has 15 poses: 10 key overhead poses plus 5 low/mid poses with external rotation, adduction, or the arm behind the torso. Data is in `screening_subset_results.json`; kinematics are in `fold_kinematics_B_upperarm_targets.json`.

| Variant | Subset collisions | Max edge ratio |
|---|---:|---:|
| r98 | 346 | 4.33 |
| anterior only | 436 | 4.33 |
| posterior only | **196** | 5.19 |
| both | 362 | 5.19 |
| posterior, half-swing target | 226 | 5.62 |
| anterior (medial origin), half-swing target | 290 | 4.33 |
| both, half-swing targets | 238 | 5.62 |

Findings:
- **Kinematics:** both fold bones move smoothly through 0–170° with no flips. They over-stretch: the anterior bone reaches 2.3× its rest length and the posterior 1.8×.
- **Posterior fold:** strongly reduces low/mid collisions (60° flexion with external rotation 146 → 2, arm behind torso 56 → 6), but raises overhead maximum stretch.
- **Anterior fold:** increases overhead collisions.
