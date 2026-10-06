# r100 axillary fold-ridge rest volume: BLOCKED (no candidate published)

Declaration: `repair_preparation/r100_axillary_ridge_volume_declared` (commit 0868bcfc, before any edit). Every prototype was built from a fresh copy of r98 (`scripts/r100/ridge100.py`); r98 and the r99 prototypes were not used as a base or modified.

## What was tested

These are geometry-only screens: weights are unchanged and no topology was added.

- **Ridge shape:** a mirror-exact, rounded cosine cross-section, 3.5 cm in radius. It runs along each fold line as projected onto the outward-facing skin; the curves are in each receipt's `ridge_curves`.
- **Surfaces moved:** only outward-facing fold surfaces, so the r98 slit opening is preserved. Each shape key receives the same delta.
- **Variants:** anterior-only, posterior-only and both, each at 3 mm (conservative) and 6 mm (moderate). Each moves 404–866 vertices, with a maximum displacement of 2.9–6.0 mm against the 8 mm cap.

## Results

15-pose subset, same set as the r98 and r99 screens (`screening_subset_results.json`):

| Variant | Collisions | Max edge ratio |
|---|---:|---:|
| r98 | 346 | 4.33 |
| r99 best (P, rejected) | 196 | 5.19 |
| anterior 3 mm | 348 | 4.33 |
| anterior 6 mm | 414 | 4.33 |
| posterior 3 mm | 388 | 4.37 |
| posterior 6 mm | 498 | 4.42 |
| both 3 mm | 452 | 4.37 |
| both 6 mm | 546 | 4.42 |

Added rest volume increases collisions roughly in proportion to amplitude; the extra tissue meets in the tight junction during horizontal adduction and 30° flexion with external rotation. No variant reduces them. Because none was promising, the repository 15-pose test and the 56-pose matrix were not run.

## Visual check

`images/r98_r99P_r100Am_r100Bm_closeups.jpg` shows r98 / r99-P / r100-Am / r100-Bm for each pose, in front, armpit, rear and three-quarter views.
- **Rest:** the silhouette is unchanged and plausible, with no shelf, cuff or crease.
- **Overhead (flexion 170°, abduction 150°, press top):** indistinguishable from r98. The membrane, rear-deltoid dent and back creases are unchanged.

## Why: ridge retention

`ridge_retention_under_pose.txt` measures the median fraction of the rest ridge offset that is still present in each pose.

| Variant | 90° | 60° flexion, external rotation | 150° abduction | 170° flexion |
|---|---:|---:|---:|---:|
| anterior 6 mm | 0.99 | 0.97 | 0.97 | 0.96 |
| posterior 6 mm | 0.97 | 0.99 | 1.00 | 0.99 |

The existing topology carries the ridge: about 1.4 cm edges represent the 3.5 cm cosine ridge, and the ridge is not destroyed by the blend. It is simply negligible next to the overhead membrane, which spans about 10 cm and is shaped by where the blend places the whole band. A rest ridge large enough to matter overhead would create the permanent shelf or cuff at rest that the declaration forbids.

## Verdict and next causal requirement

- The hypothesis that the folds lack bind-pose cross-sectional volume is **falsified** as the cause of the overhead defect.
- **Minimal local topology is not the next requirement:** the ridge is carried and retained.
- **The next causal requirement is a declared rotation-driven volume mechanism**: something that changes fold geometry as a function of glenohumeral elevation and axial rotation. For example, fold-volume helper bones driven by the half-swing helper's elevation that displace the fold band along its surface normal, kept distinct from the rejected straight-line stretch bones.

  This is outside the current authorisation, which forbids elevation-driven bulge drivers, so it needs an explicit decision and a new declaration.
- An alternative outside the shoulder-only scope is a less-adducted bind pose for the arm.

r98 remains the strongest model. No r100 candidate or READY record is published.
