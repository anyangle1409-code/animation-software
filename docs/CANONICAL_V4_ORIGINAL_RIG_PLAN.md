# Canonical v4 ORIGINAL rig plan

## Goal

Create a clean numerical rest-pose/proportion definition for the final original Home Gym PT character while retaining the project-authored rig architecture.

New identity:

`hgpt_canonical_v4_original`

## Retain

The following project concepts may carry forward:
- bone names;
- 63-bone hierarchy structure;
- parent/child semantics;
- left/right mirroring architecture;
- joint-axis conventions;
- joint-limit data where independently defensible as anatomical specification;
- IK chain definitions;
- contact semantics;
- equipment attachment semantics;
- pose data model.

## Re-author

Do not copy the current v3 rest coordinates wholesale.

Re-author numerical rest geometry for:
- pelvis width/height reference;
- spine segment lengths;
- neck/head placement;
- clavicle length/angle;
- scapula pivots;
- humerus length;
- forearm length;
- hand length/width;
- metacarpals;
- finger segment lengths;
- hip width;
- femur length;
- tibia length;
- foot/toe dimensions.

The new values must be documented as project-authored target dimensions and must not be fitted to legacy V8/V13e/V15f vertices or imported source bones.

## Authoring method

1. Define a neutral target adult figure height.
2. Define each segment as:
   - an explicit project target dimension; or
   - a dimensionless fraction of body height/hand length.
3. Record the source rationale as generic anatomical design intent, not a legacy mesh measurement.
4. Generate left-side world rest coordinates from those specifications.
5. Mirror right side algorithmically.
6. Derive local frames through the existing project skeleton logic.
7. Verify the rig without loading any legacy character asset.

## Independence guard

Create a test that can construct and validate v4 with the legacy character files absent.

The test must prove:
- all 63 bones exist;
- hierarchy is valid;
- no NaN/zero-length structural bones;
- symmetry where expected;
- intended joint limits;
- hand/finger chain completeness;
- IK chains build;
- all exercise definitions can resolve against the skeleton structurally.

## Migration

Do not immediately delete v3.

During transition:
- v3 remains the historical comparison skeleton;
- v4 becomes the clean-room character target;
- exercise definitions should be checked for hidden assumptions tied to v3 dimensions;
- dimension-specific contacts/equipment sockets should become derived/parameterised where possible.

## Acceptance

v4 may replace v3 for the standalone production line only after:
- ORIGINAL v1 neutral bind fits naturally;
- movement-envelope tests pass;
- all equipment/contact calibrations are re-established;
- no legacy rest-transform data is required at runtime.
