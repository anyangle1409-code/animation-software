# Reference body match — two-stage decision and next steps

**Branch:** `chatgpt/absolute-retarget-imports`  
**Do not merge or promote.**

This document records the decision after the completed rig-proportion investigation in `docs/REFERENCE_BODY_RIG_PROPOSAL.md`.

## Decision

The remaining mismatch is two different problems and must be handled in two controlled stages.

### Stage 1 — correct the forearm proportion first

This is a real defect, not a style preference.

Measured as percentage of figure height:

| Measure | Canonical rig | Character | Reference |
|---|---:|---:|---:|
| Shoulder lateral offset | 9.71% | 9.68% | 10.64% |
| Upper arm length | 17.14% | 16.98% | ~17.2% |
| Forearm length | 14.86% | 10.93% | ~14.7% |

The forearm is short relative to both the canonical rig and the reference by about 4% of figure height. Correcting it therefore moves the character toward both its own animation rig and the target physique.

Retain the investigated forearm correction target:

- forearm lengthening: about **3.92% of figure height**;
- about **79.2 mm model-space / 68.7 mm studio-space**;
- upper arm remains effectively unchanged;
- preserve existing accepted motion intent rather than editing exercises to hide the new proportions.

### Stage 2 — widen the shoulder system deliberately

This is not a defect relative to the current canonical rig. The character and canonical rig already agree on shoulder offset to within about 0.03% of height.

The supplied reference is wider. Therefore matching it requires a deliberate physique/proportion change to the canonical rig and source character together, not fake deltoid inflation.

Investigated target per side:

- lateral arm-chain shift: about **1.83% of figure height**;
- about **37.0 mm model-space / 32.1 mm studio-space**;
- projected shoulder span reaches the reference;
- projected shoulder-line residual is about **2.1°**;
- no further shoulder-yoke sculpt should be needed purely to chase slope.

Treat this as a planned canonical-rig proportion upgrade, not as a mesh workaround.

## Required sequence

Do **not** combine both changes immediately.

1. Implement and validate the forearm correction alone.
2. Re-derive all hand contacts from their own rules.
3. Validate deformation/contact/motion across the exercise set.
4. Only when Stage 1 is clean, use that new state as the baseline for Stage 2.
5. Then widen the canonical shoulder chain and source character together, followed by a fresh full contact/deformation pass.

This ordering is mandatory so any regression can be attributed to one change.

## Stage 1 guardrails

During the forearm correction:

- keep upper-arm length unchanged unless new measurement proves otherwise;
- keep accepted curl timing and motion intent unchanged;
- keep global grip closure at **85%**;
- keep elbow corrective at **0%**;
- keep the current reference-fit torso/waist/lat/yoke geometry;
- preserve topology;
- preserve skin weights unless the existing v5→v6 hand/wrist handover repair objectively fails after the stretch;
- do not manually nudge equipment or locks simply to make poses look like they did before;
- re-derive contacts from the actual rules and updated joint positions;
- do not weaken validation thresholds.

The surface must move with the bones. The investigation already showed that after the proposed skeletal change, the current surface no longer encloses the proposed joint positions naturally. Refit/regenerate the arm surface around the corrected bone locations. Recompute inverse binds as required by the retained skeleton change.

## Stage 1 validation that must be re-measured

At minimum re-measure and inspect:

### Curl
- hand/dumbbell world positions;
- bilateral symmetry;
- rigid equipment attachment;
- the documented ~6 mm dumbbell/thigh overlap at the bottom;
- wrist/hand deformation around the v5→v6 repaired weight-transition region;
- accepted curl motion itself must not be rewritten to compensate.

### Shoulder press
- rack position;
- overhead lockout height;
- hand/dumbbell placement;
- wrist and elbow appearance;
- contact/attachment stability.

### Push-up
- hand-floor contacts;
- true wrist extension at top and bottom;
- the documented shoulder-ahead-of-hand / hand-placement issue must be re-measured after the proportion change rather than assumed unchanged;
- do not treat the skeletal correction as the push-up solution unless the new measurement actually proves it.

### Pull-up
- grip width;
- bilateral hand sockets;
- bar contact;
- wrist/forearm behaviour;
- shoulder/armpit deformation.

Also run deepest squat to confirm the body/garment path did not regress indirectly.

## Stage 2 guardrails

When Stage 1 is validated, widen the shoulder system by updating the **canonical rig and source character together**.

Do not:

- shift only the GLB skeleton while leaving the canonical animation rig narrow;
- fake width with more deltoid mass;
- rewrite exercise motion to hide the changed proportions;
- change grip closure from 85%;
- change elbow corrective from 0%;
- overwrite v7, v6, or proven v5 fallbacks.

The goal is:

**reference-fit torso + corrected forearm proportions + widened canonical shoulder chain + re-derived contacts**

After widening, revalidate all five exercise families because shoulder position affects press, push-up, pull-up, hand spacing, equipment contact and retargeting relationships.

## Current interpretation of the reference

The front reference supports the shoulder-width decision and the forearm-length correction.

Do not invent unsupported side/rear depth from it. Chest depth, scapular shape, glute projection, lumbar curve, calf depth and side-view deltoid profile still require side/rear references for a stronger 3D match.

## Stop points

### Immediate next task

Proceed with **Stage 1 only**: implement the forearm correction as a separate candidate and validate it fully.

Do not start shoulder widening in the same implementation pass.

### After Stage 1

Report:

- exact skeletal/bind changes retained;
- candidate asset filename + SHA-256;
- whether skin weights remained unchanged;
- inverse-bind update details;
- contact deltas for curl/press/push-up/pull-up;
- updated push-up true wrist angles;
- updated curl dumbbell/thigh overlap;
- hand/wrist deformation comparison against v7;
- strain/diagnostic results;
- typecheck/test/build result;
- any regression that would block Stage 2.

Only then proceed to the separate shoulder-width stage.

**Do not merge or promote.**
