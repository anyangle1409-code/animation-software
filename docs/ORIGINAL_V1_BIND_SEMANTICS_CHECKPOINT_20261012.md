# Work task continued remotely: shoulder bind semantics — 12 October 2026

Actual Blender 5.2.1 proof completed without the laptop. Based on live PR81
`d04100995ca496fd4e095c748179e08b730bcd6e`, preserving Work PR80 and shared
master-plan PR48. Separate diagnostic branch; no native source files edited.

## What this resolves

The six c004-authored clavicle/scapula/humerus controls and r95 full-body runtime
have different rest frames. The earlier native audit found bilateral origin
separations of 12.091 mm, 74.946 mm and 54.789 mm. The source pilot scapula control
starts at AC; its origin is not automatically the GH joint. Bare name matching
or calling all control origins anatomical joint centres is incorrect.

An explicit rest-preserving mathematical adapter is now tested:
`offset = inverse(sourceWorldRest) * targetWorldRest`;
`diagnosticTargetWorld = sourceWorldPose * offset`.
It preserves the current target rest frame without changing source coordinates.
However, it also rotates and retains the existing origin gap. It **does not**
bring the old body's shoulder joints onto the anatomical source joints. A proper
matrix transform is not a deformation/anatomical correction.

## Actual verification

- 7 new diagnostic unit tests PASS after missing-function and nonfinite-distance
  RED results; proper handedness, invalid affine/scale/shear/NaN frames, global
  frame invariance, coincident/different origins and source immutability covered.
- Existing pure body-bridge tests: 4 PASS. Existing native Blender bridge: 4 PASS.
- Actual newer curved-blade pilot built only in a separate temporary scene.
  Original full-body scene preserved; no body driver or retarget installed.
- 6 actual source controls × source REST / authored 0 / 90 / 160 = **24 native
  matrix comparisons** against independent Blender mathutils oracle.
- Maximum matrix-element error: `2.95967509056e-07`.
  Maximum retained-origin-gap drift: `1.44151731246e-08 m`.
- Exact original scene fingerprint before/after matches: vertices, weights,
  active modifiers, both skeleton rest frames and all original pose bases.
  Native file SHA256 stays
  `670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56`.
- Native report SHA256: `db0a09a6c5243e3b8edbdc3f52fe77c66dadee5c97eef8c78decdf09eb6a87e4`.
  Report: `docs/reviews/ORIGINAL_V1_NATIVE_BIND_SEMANTICS_20261012.json`.
- Pure diagnostic CI workflow added; actual new CI result must be checked at
  the published commit. Native proof above was run here, not claimed as CI.
- Inherited full-suite failures remain open; unchanged broad red suite was not
  repeated for this isolated diagnostic. No all-suite-green claim.

## Exact next Work action

Explicitly specify SC/AC/GH joint/contact origins separately from the scapula
control origin. For the next separate provisional functional candidate, derive
runtime joint frames from the source authority, then refit original body/weights
around those frames and prove rest/posed attachment. Do not move the anatomical
source skeleton to preserve the old skin. The rest-offset diagnostic is a
comparison tool, not permission to install a production retarget.

Clinical/anatomical, coupled motion, contact, realistic deformation and
production approvals stay false. Historical regional readiness is unchanged.
