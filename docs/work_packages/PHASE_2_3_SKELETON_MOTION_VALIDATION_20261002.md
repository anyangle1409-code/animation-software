# Phase 2/3 skeleton-motion validation — pre-freeze package

Status: PREPARED; requires Blender execution  
Effective: 2026-10-02  
Purpose: prove whether a visible defect comes from the skeleton/pose/constraint layer or from skinning/topology before Phase 4 freeze.

## Why this exists

Phase 2 froze the canonical-v4 63-bone hierarchy/rest structure, while Phase 3 repairs deformation around that rig.

Owner review of r38 showed defects that could plausibly originate in either layer:
- distal fingertips appear to bend backwards in flexed grips;
- push-up palm/wrist support is incorrect;
- push-up toe/forefoot support is incorrect;
- overhead shoulder/axilla behaviour may be a pose/rig problem or a skinning/topology problem.

Do not assume these are skinning problems merely because Phase 2 is marked complete.

A frozen structure can be reopened locally only when evidence proves that the frozen structure itself is wrong. Any reopening must be minimal, documented, regression-tested and must preserve the 63-bone hierarchy/name contract unless a separate explicit owner decision authorises a structural change.

## Required diagnostic order

For each flagged issue use this order:

1. **Skeleton only**
   - hide body/shorts;
   - inspect bone head/tail directions and joint chain movement;
   - inspect the full relevant motion, not only the endpoint.
2. **Pose / constraint construction**
   - inspect the code/logic that aims or rotates the bones;
   - verify rotation axis/sign and range.
3. **Skin visible**
   - if bones are correct, identify weights/topology/deformation as the cause.
4. **External human reference**
   - follow `docs/EXTERNAL_HUMAN_MOVEMENT_REFERENCE_POLICY.md`;
   - compare normal human joint direction/contact/motion envelope;
   - record source/timecode plus generic observations only.
5. Fix the smallest general first-party cause.
6. Re-run skeleton-only evidence, deformation evidence and all existing regressions.

## Prepared read-only tool

Run on the current candidate:

```bat
blender --background --factory-startup <candidate.blend> ^
  --python scripts/audit_original_v1_skeleton_motion_blender.py -- ^
  ORIGINAL_V1_WORK\candidates\repair_checks\<revision>_skeleton_motion.json
```

Or restrict to the immediate poses:

```bat
blender --background --factory-startup <candidate.blend> ^
  --python scripts/audit_original_v1_skeleton_motion_blender.py -- ^
  ORIGINAL_V1_WORK\candidates\repair_checks\<revision>_skeleton_motion_focus.json ^
  curl_peak,curl_handle,pullup_bar,pushup_bottom,press_top,press_top_rhythm,pullup_hang_rhythm
```

The script:
- never saves the Blend file;
- reuses the exact Phase 3 pose constructors;
- records bone directions and relevant joint-chain angles;
- records palm, wrist/hand, foot/toe and shoulder relationships;
- flags a suspicious finger chain when the distal bend reverses sign relative to the preceding flexion bend;
- hashes both the candidate and pose-definition script.

A flag is diagnostic, not a final anatomical verdict. External human reference and visual inspection remain required.

## Finger decision tree

For each index/middle/ring/pinky chain in curl/grip/pull-up:

### If the distal bone itself bends the wrong direction
Investigate in this order:
1. pose-construction rotation axis/sign;
2. joint/local-axis orientation;
3. generic joint-limit policy;
4. only then canonical-v4 rest orientation if evidence proves it incorrect.

If the rest/local axis is genuinely wrong, create an isolated documented rig-correction candidate. Do not preserve a known wrong rig simply because Phase 2 was frozen.

### If the bones bend correctly but the fingertip mesh bends backwards
Keep the rig frozen and fix:
- skin weights;
- joint-support topology;
- local geometry;
- or another deformation-layer cause.

Do not sculpt over a wrong bone pose.

## Push-up hand/wrist decision tree

With mesh hidden, inspect:
- palm normal relative to floor;
- forearm direction;
- hand direction;
- wrist extension;
- left/right symmetry through top -> descent -> bottom -> ascent.

If the palm plane and hand/forearm bones are wrong, repair pose/constraint logic before weights.

If the bones form a plausible loaded support chain but the visible hand rolls onto its side, repair deformation/contact geometry.

The final skinned pose must show:
- palm/metacarpal support planted;
- plausible loaded wrist extension;
- fingers naturally directed/splayed;
- no side-edge loading as the primary support.

## Push-up foot/toe decision tree

With mesh hidden, inspect:
- ankle/foot direction;
- toe bone direction;
- toe dorsiflexion through push-up support;
- left/right symmetry.

If bone directions are wrong, repair pose/constraint behaviour.
If bones are plausible but the mesh/contact patch is wrong, repair deformation/contact geometry.

Shoes remain a later first-party clothing task and are not evidence of a corrected barefoot support chain.

## Shoulder decision tree

Use:
- press_bottom;
- press_top;
- press_top_rhythm;
- pullup_hang;
- pullup_hang_rhythm;
- pullup_top.

Inspect skeleton-only:
- humeral elevation/rotation;
- clavicle contribution;
- scapular contribution;
- upper-arm/forearm relationship;
- continuity through the movement.

Then inspect the skin.

Classify the current axilla/webbing defect as:
- pose/rig/constraint;
- weighting/deformation;
- topology/support;
- or coarse surface anatomy.

Only the final category may be deferred to Phase 5B.

## Continuous-motion requirement

Endpoint poses are insufficient.

For every currently flagged support/joint problem, inspect intermediate motion samples. At minimum use:
- 0%;
- 25%;
- 50%;
- 75%;
- 100%.

The objective is to catch:
- sign flips;
- sudden joint reversals;
- contact popping;
- wrist/hand roll;
- toe inversion;
- shoulder collapse between accepted endpoints.

If no existing interpolation runner covers the required path, create a read-only diagnostic first. Do not modify exercise definitions merely to produce pretty evidence.

## Evidence required before Phase 4

Commit:
- skeleton-motion JSON report(s);
- skeleton-only screenshots/captures for the flagged regions;
- external reference observation record(s);
- diagnosis per issue: rig/pose vs deformation vs surface anatomy;
- correction candidate evidence;
- full existing deformation/comparison reports.

Phase 4 must not freeze a known mechanical joint-direction or loaded-contact defect merely because aggregate deformation metrics are green.
