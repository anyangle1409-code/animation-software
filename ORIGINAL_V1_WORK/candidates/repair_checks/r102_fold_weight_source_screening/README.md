# r102 fold-helper weight sources: BLOCKED (no candidate, no READY)

Declaration: `repair_preparation/r102_fold_helper_weight_sources_declared` (commit 68c4f4c1, before any edit). Prototypes are built from fresh copies of r98 with `scripts/r102/vol102.py`. Only the weight source changed from r101: the elevation drive, fixed normal, 40 mm cap and helper structure (child of `glenohumeral_half`, same rest frame) are kept.

## What was tested

The test covered the anterior fold only, at two shares of the declared source weight (`spine_02`, `spine_03`, clavicle, scapula, upperarm, `glenohumeral_half`), taken proportionally from each source:
- conservative: 0.25;
- moderate: 0.45.

Each share was built twice, with the 40 mm offset and with the offset forced to 0. The zero-offset build isolates the base-motion cost.

In every receipt:
- out-of-band and undeclared weights are unchanged exactly;
- at most 4 influences;
- mirror-exact;
- per-source changes are recorded.

## Base-motion cost

Displacement in mm against r98 with the offset at 0 (`base_motion_cost_*.json`):

| Pose | Share 0.25, band max | Share 0.25, band p90 | Share 0.45, band max | Outside band |
|---|---:|---:|---:|---:|
| rest | 0 | 0 | 0 | 0 |
| curl top | 6.0 | 4.2 | 10.1 | 0 |
| **abduction 30** | **10.4** | 7.4 | **17.5** | 0 |
| **arm at side, ±40° axial** | **15.8** | 11.2 | **26.4** | 0 |
| **horizontal adduction 90** | **43.2** | 30.8 | **73.1** | 0 |
| **press bottom** | **59.7** | 41.8 | **101.3** | 0 |
| pull-up top | 30.8 | 21.2 | 52.5 | 0 |
| flexion 170 | 66.0 | 46.5 | 115.1 | 0 |
| abduction 150 | 60.6 | 41.9 | 105.4 | 0 |

Even the conservative share drags the anterior fold band:
- about 1 cm at 30° abduction;
- 1.6 cm when the arm only rotates at the side;
- 4–6 cm in horizontal adduction and press bottom.

This is the low-elevation drift and chest drag the declaration rejects. Both shares are rejected before any visual review, and the moderate share was not run further.

On the subset, the conservative share has 286 collisions against r98's 346, but horizontal adduction regresses from 2 to 18 (`screening_subset_results.json`).

## Measured blocker

The fold-volume helper is a child of `glenohumeral_half`, which carries half the humeral swing and the **full axial twist**. Torso/girdle weight re-sourced onto it stops following the torso and follows the arm instead. Even arm rotation at the side moves chest skin. The base motion of re-sourced weight is no longer the base motion of its source.

Base motion is preserved only when the helper's parent matches the source of the weight. r101 met that condition for half-helper weight, but that weight was too small a share of the membrane to matter.

## Next causal requirement

This needs a new declaration. The fold-volume offset should be carried by **per-source offset twins**: one driven offset bone per source bone, each a child of that source with the same rest frame and the same elevation-driven outward offset. Fold weight then moves from each source to its own twin. Base motion stays exactly r98's at any share, as it did in r101 for the half helper, and the fold band can still be reached by the torso- and humerus-weighted membrane.

The twins would be:
- `axvol_ant_spine03_<s>`, a child of spine_03;
- `axvol_ant_scap_<s>`, a child of the scapula;
- `axvol_ant_ua_<s>`, a child of the upperarm;
- the existing half twin.

The offset normal is expressed per parent. Posed-normal following stays a later, separate refinement.

r98–r101 are unchanged. No READY record is published.
